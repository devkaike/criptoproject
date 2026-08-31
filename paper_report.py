"""Prints a snapshot of the paper trading account: current position, unrealized
P&L, equity, and closed-trade stats. Read-only - fetches the live price but
touches no order endpoints. Usage: python paper_report.py
"""
from src.config import load_config
from src.exchange_client import ExchangeClient
from src.paper_report import build_summary
from src.paper_state import load_account


def main() -> None:
    config = load_config()
    account = load_account(config.initial_capital)
    client = ExchangeClient(config)
    price = client.fetch_last_price()
    summary = build_summary(account, price, config.min_profit_percent, config.sell_fee_percent)
    quote = config.symbol.split("/")[1]

    print(f"=== Paper trading — {config.symbol} ===")
    print(f"Preço atual: {price:.2f} {quote}")
    print(f"Saldo (caixa): {summary.balance:.2f} {quote}")

    if summary.position_open:
        print(f"Posição aberta: entrada={summary.entry_price:.2f} qtd={summary.quantity:.8f} BTC")
        print(f"Preço mínimo para vender: {summary.min_sell_price:.2f} {quote}")
        print(
            f"Lucro/prejuízo não realizado: {summary.unrealized_pnl_quote:.2f} {quote} "
            f"({summary.unrealized_pnl_percent:.2f}%)"
        )
    else:
        print("Sem posição aberta.")

    print(f"Patrimônio total (saldo + posição): {summary.equity:.2f} {quote}")
    print(f"Lucro realizado acumulado: {summary.realized_profit:.2f} {quote}")
    print(
        f"Trades fechados: {summary.total_trades} "
        f"(vitórias={summary.wins} derrotas={summary.losses} taxa_acerto={summary.win_rate_percent:.1f}%)"
    )


if __name__ == "__main__":
    main()
