import pandas as pd

from src.config import Config


def add_sma(df: pd.DataFrame, period: int, column: str) -> pd.DataFrame:
    df[column] = df["close"].rolling(window=period).mean()
    return df


def add_rsi(df: pd.DataFrame, period: int, column: str = "rsi") -> pd.DataFrame:
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, float("nan"))
    df[column] = 100 - (100 / (1 + rs))
    df[column] = df[column].fillna(50)
    return df


def add_indicators(df: pd.DataFrame, config: Config) -> pd.DataFrame:
    df = add_sma(df, config.sma_short, "sma_short")
    df = add_sma(df, config.sma_long, "sma_long")
    df = add_rsi(df, config.rsi_period)
    return df


def generate_signal(df: pd.DataFrame, config: Config) -> str:
    """Returns 'buy', 'sell' or 'hold' based on the last two closed candles.

    Buy: SMA short crosses above SMA long (golden cross) while RSI is not
    already overheated (avoids buying right before a reversal).

    Sell: SMA short crosses below SMA long (death cross) or RSI signals the
    asset is overbought.
    """
    if len(df) < max(config.sma_long, config.rsi_period) + 2:
        return "hold"

    prev = df.iloc[-2]
    last = df.iloc[-1]

    golden_cross = prev["sma_short"] <= prev["sma_long"] and last["sma_short"] > last["sma_long"]
    death_cross = prev["sma_short"] >= prev["sma_long"] and last["sma_short"] < last["sma_long"]

    if golden_cross and last["rsi"] < config.rsi_buy_max:
        return "buy"

    if death_cross or last["rsi"] > config.rsi_overbought:
        return "sell"

    return "hold"
