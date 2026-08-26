"""Simple backtest: replays historical candles through the same strategy
used live, to sanity-check the SMA+RSI rules before running the bot for real.

Usage: python backtest.py
"""
import ccxt

from src.config import load_config
from src.strategy import add_indicators, generate_signal


def fetch_history(config, limit=1000):
    exchange_class = getattr(ccxt, config.exchange_id)
    exchange = exchange_class({"enableRateLimit": True})
    raw = exchange.fetch_ohlcv(config.symbol, timeframe=config.timeframe, limit=limit)
    import pandas as pd

    df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df


def run_backtest():
    config = load_config()
    df = fetch_history(config)
    df = add_indicators(df, config)

    balance_quote = 1000.0
    balance_base = 0.0
    in_position = False
    entry_price = 0.0
    trades = []

    min_len = max(config.sma_long, config.rsi_period) + 2
    for i in range(min_len, len(df)):
        window = df.iloc[: i + 1]
        signal = generate_signal(window, config)
        price = df.iloc[i]["close"]

        if in_position:
            change = (price - entry_price) / entry_price
            if change <= -config.stop_loss_pct or change >= config.take_profit_pct:
                signal = "sell"

        if signal == "buy" and not in_position:
            balance_base = balance_quote / price
            balance_quote = 0.0
            entry_price = price
            in_position = True
            trades.append(("buy", df.iloc[i]["timestamp"], price))
        elif signal == "sell" and in_position:
            balance_quote = balance_base * price
            balance_base = 0.0
            in_position = False
            trades.append(("sell", df.iloc[i]["timestamp"], price))

    final_price = df.iloc[-1]["close"]
    final_value = balance_quote + balance_base * final_price
    print(f"Trades executed: {len(trades)}")
    for side, ts, price in trades:
        print(f"  {ts} {side.upper():4} @ {price:.2f}")
    print(f"Final portfolio value: {final_value:.2f} (started with 1000.00)")
    print(f"Return: {(final_value / 1000.0 - 1) * 100:.2f}%")


if __name__ == "__main__":
    run_backtest()
