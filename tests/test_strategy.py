import pandas as pd

from src.config import Config
from src.strategy import add_indicators, generate_signal

TEST_CONFIG = Config(
    exchange_id="binance",
    api_key="",
    api_secret="",
    use_testnet=True,
    dry_run=True,
    symbol="BTC/USDT",
    timeframe="15m",
    trade_amount_quote=50.0,
    sma_short=3,
    sma_long=5,
    rsi_period=5,
    rsi_overbought=70.0,
    rsi_buy_max=60.0,
    stop_loss_pct=0.03,
    take_profit_pct=0.05,
    poll_interval_seconds=60,
    telegram_bot_token="",
    telegram_chat_id="",
    paper_trading=True,
    initial_capital=3000.0,
    trade_percent=30.0,
    min_profit_percent=0.5,
    buy_fee_percent=0.1,
    sell_fee_percent=0.1,
)


def make_df(closes):
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=len(closes), freq="15min"),
            "open": closes,
            "high": closes,
            "low": closes,
            "close": closes,
        }
    )


def test_golden_cross_with_low_rsi_triggers_buy():
    # A downtrend followed by a sharp recovery should flip SMA short above
    # SMA long while RSI is still below the buy threshold.
    closes = [100, 95, 90, 85, 80, 78, 90, 95]
    df = make_df(closes)
    df = add_indicators(df, TEST_CONFIG)
    assert generate_signal(df, TEST_CONFIG) == "buy"


def test_death_cross_triggers_sell():
    closes = [80, 85, 90, 95, 100, 102, 90, 85]
    df = make_df(closes)
    df = add_indicators(df, TEST_CONFIG)
    assert generate_signal(df, TEST_CONFIG) == "sell"


def test_not_enough_data_holds():
    df = make_df([100, 101, 102])
    df = add_indicators(df, TEST_CONFIG)
    assert generate_signal(df, TEST_CONFIG) == "hold"


def test_flat_market_holds():
    closes = [100] * 10
    df = make_df(closes)
    df = add_indicators(df, TEST_CONFIG)
    assert generate_signal(df, TEST_CONFIG) == "hold"
