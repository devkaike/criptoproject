import time

from src.config import Config
from src.exchange_client import ExchangeClient
from src.logger import get_logger
from src.notifier import Notifier
from src.state import Position, load_position, save_position
from src.strategy import add_indicators, generate_signal

logger = get_logger(__name__)


class Trader:
    def __init__(self, config: Config):
        self.config = config
        self.client = ExchangeClient(config)
        self.notifier = Notifier(config)
        self.position = load_position()

    def _quote_currency(self) -> str:
        return self.config.symbol.split("/")[1]

    def _check_risk_exit(self, price: float) -> bool:
        """Force-sells the open position if stop-loss or take-profit is hit."""
        if not self.position.in_position:
            return False

        change = (price - self.position.entry_price) / self.position.entry_price
        if change <= -self.config.stop_loss_pct:
            logger.info("Stop-loss hit (%.2f%%). Selling.", change * 100)
            self._sell(price, reason="stop-loss")
            return True
        if change >= self.config.take_profit_pct:
            logger.info("Take-profit hit (%.2f%%). Selling.", change * 100)
            self._sell(price, reason="take-profit")
            return True
        return False

    def _buy(self, price: float) -> None:
        balance = self.client.fetch_quote_balance(self._quote_currency())
        if balance < self.config.trade_amount_quote:
            logger.warning(
                "Insufficient %s balance (%.2f) to buy %.2f.",
                self._quote_currency(),
                balance,
                self.config.trade_amount_quote,
            )
            return

        order = self.client.create_market_buy(self.config.trade_amount_quote, price)
        self.position = Position(
            in_position=True, entry_price=price, amount=order["amount"]
        )
        save_position(self.position)
        msg = f"BUY {self.config.symbol} @ {price:.2f} (amount={order['amount']:.6f})"
        logger.info(msg)
        self.notifier.send(msg)

    def _sell(self, price: float, reason: str = "signal") -> None:
        order = self.client.create_market_sell(self.position.amount, price)
        pnl_pct = (price - self.position.entry_price) / self.position.entry_price * 100
        msg = (
            f"SELL {self.config.symbol} @ {price:.2f} "
            f"(reason={reason}, pnl={pnl_pct:.2f}%)"
        )
        logger.info(msg)
        self.notifier.send(msg)
        self.position = Position()
        save_position(self.position)

    def run_once(self) -> None:
        df = self.client.fetch_ohlcv_df(self.config.timeframe)
        df = add_indicators(df, self.config)
        price = self.client.fetch_last_price()

        if self._check_risk_exit(price):
            return

        signal = generate_signal(df, self.config)

        if signal == "buy" and not self.position.in_position:
            self._buy(price)
        elif signal == "sell" and self.position.in_position:
            self._sell(price, reason="signal")
        else:
            logger.info(
                "No action. signal=%s in_position=%s price=%.2f",
                signal,
                self.position.in_position,
                price,
            )

    def run_forever(self) -> None:
        logger.info(
            "Starting trader: symbol=%s timeframe=%s dry_run=%s testnet=%s",
            self.config.symbol,
            self.config.timeframe,
            self.config.dry_run,
            self.config.use_testnet,
        )
        while True:
            try:
                self.run_once()
            except Exception as exc:
                logger.exception("Error in trading loop: %s", exc)
            time.sleep(self.config.poll_interval_seconds)
