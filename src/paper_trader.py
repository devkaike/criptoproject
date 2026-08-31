"""Paper-trading loop: real market prices, fully simulated execution.

Entries reuse the existing SMA/RSI golden-cross buy signal from
src/strategy.py (already implemented and tested). Exits ignore that
strategy's sell signal entirely - a position only closes once the net
profit (after both buy and sell fees) reaches config.min_profit_percent.
No stop-loss, no forced exit: a losing position is simply held.
"""
import time
from datetime import datetime, timezone

from src.config import Config
from src.exchange_client import ExchangeClient
from src.logger import get_logger
from src.paper_broker import can_sell, compute_buy, compute_sell, min_sell_price, unrealized_pnl
from src.paper_state import PaperPosition, PaperTrade, load_account, save_account
from src.strategy import add_indicators, generate_signal

logger = get_logger(__name__)


class PaperTrader:
    def __init__(self, config: Config):
        self.config = config
        self.client = ExchangeClient(config)
        self.account = load_account(config.initial_capital)

    def _quote_currency(self) -> str:
        return self.config.symbol.split("/")[1]

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _buy(self, price: float) -> None:
        execution = compute_buy(
            balance=self.account.balance,
            trade_percent=self.config.trade_percent,
            price=price,
            buy_fee_percent=self.config.buy_fee_percent,
        )
        opened_at = self._timestamp()
        self.account.balance -= execution.quote_spent
        self.account.position = PaperPosition(
            open=True,
            entry_price=price,
            quantity=execution.quantity,
            cost_basis=execution.cost_basis,
            buy_fee=execution.fee_quote,
            opened_at=opened_at,
        )
        self.account.history.append(
            PaperTrade(
                side="buy",
                price=price,
                quantity=execution.quantity,
                quote_amount=execution.quote_spent,
                fee_quote=execution.fee_quote,
                timestamp=opened_at,
            )
        )
        save_account(self.account)

        required_price = min_sell_price(
            execution.cost_basis,
            execution.quantity,
            self.config.min_profit_percent,
            self.config.sell_fee_percent,
        )
        quote = self._quote_currency()
        logger.info("COMPRA realizada @ %.2f", price)
        logger.info("  Quantidade: %.8f BTC", execution.quantity)
        logger.info("  Valor investido: %.2f %s", execution.quote_spent, quote)
        logger.info("  Taxa de compra: %.2f %s", execution.fee_quote, quote)
        logger.info("  Preço mínimo para venda: %.2f", required_price)
        logger.info("  Saldo restante: %.2f %s", self.account.balance, quote)

    def _sell(self, price: float) -> None:
        pos = self.account.position
        execution = compute_sell(
            cost_basis=pos.cost_basis,
            quantity=pos.quantity,
            price=price,
            sell_fee_percent=self.config.sell_fee_percent,
        )
        self.account.balance += execution.net_proceeds
        self.account.realized_profit += execution.profit_quote
        self.account.history.append(
            PaperTrade(
                side="sell",
                price=price,
                quantity=execution.quantity,
                quote_amount=execution.gross_proceeds,
                fee_quote=execution.fee_quote,
                timestamp=self._timestamp(),
                profit_quote=execution.profit_quote,
                profit_percent=execution.profit_percent,
            )
        )
        self.account.position = PaperPosition()
        save_account(self.account)

        quote = self._quote_currency()
        gross_profit = execution.gross_proceeds - pos.cost_basis
        total_fees = pos.buy_fee + execution.fee_quote
        logger.info("VENDA realizada @ %.2f", price)
        logger.info("  Lucro bruto: %.2f %s", gross_profit, quote)
        logger.info("  Taxas (compra + venda): %.2f %s", total_fees, quote)
        logger.info(
            "  Lucro líquido: %.2f %s (%.2f%%)", execution.profit_quote, quote, execution.profit_percent
        )
        logger.info("  Saldo atual: %.2f %s", self.account.balance, quote)

    def run_once(self) -> None:
        price = self.client.fetch_last_price()
        quote = self._quote_currency()
        logger.info("Preço BTC: %.2f | Saldo: %.2f %s", price, self.account.balance, quote)

        pos = self.account.position
        if pos.open:
            required_price = min_sell_price(
                pos.cost_basis, pos.quantity, self.config.min_profit_percent, self.config.sell_fee_percent
            )
            pnl_quote, pnl_percent = unrealized_pnl(
                pos.cost_basis, pos.quantity, price, self.config.sell_fee_percent
            )
            logger.info(
                "Posição aberta: entrada=%.2f qtd=%.8f preço_min_venda=%.2f "
                "lucro_não_realizado=%.2f %s (%.2f%%)",
                pos.entry_price,
                pos.quantity,
                required_price,
                pnl_quote,
                quote,
                pnl_percent,
            )
            if can_sell(
                pos.cost_basis, pos.quantity, price, self.config.min_profit_percent, self.config.sell_fee_percent
            ):
                self._sell(price)
            else:
                logger.info("Lucro mínimo ainda não atingido. Mantém posição aberta.")
            return

        df = self.client.fetch_ohlcv_df(self.config.timeframe)
        df = add_indicators(df, self.config)
        signal = generate_signal(df, self.config)
        if signal == "buy":
            self._buy(price)
        else:
            logger.info("Sem sinal de compra (signal=%s). Aguardando.", signal)

    def run_forever(self) -> None:
        logger.info(
            "Iniciando paper trader: symbol=%s capital_inicial=%.2f trade_percent=%.2f%% "
            "min_profit=%.2f%% buy_fee=%.2f%% sell_fee=%.2f%%",
            self.config.symbol,
            self.config.initial_capital,
            self.config.trade_percent,
            self.config.min_profit_percent,
            self.config.buy_fee_percent,
            self.config.sell_fee_percent,
        )
        while True:
            try:
                self.run_once()
            except Exception as exc:
                logger.exception("Erro no loop do paper trader: %s", exc)
            time.sleep(self.config.poll_interval_seconds)
