import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _float(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value else default


def _int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value else default


@dataclass(frozen=True)
class Config:
    exchange_id: str
    api_key: str
    api_secret: str
    use_testnet: bool
    dry_run: bool

    symbol: str
    timeframe: str
    trade_amount_quote: float

    sma_short: int
    sma_long: int
    rsi_period: int
    rsi_overbought: float
    rsi_buy_max: float

    stop_loss_pct: float
    take_profit_pct: float

    poll_interval_seconds: int

    telegram_bot_token: str
    telegram_chat_id: str


def load_config() -> Config:
    return Config(
        exchange_id=os.getenv("EXCHANGE_ID", "binance"),
        api_key=os.getenv("API_KEY", ""),
        api_secret=os.getenv("API_SECRET", ""),
        use_testnet=_bool("USE_TESTNET", True),
        dry_run=_bool("DRY_RUN", True),
        symbol=os.getenv("SYMBOL", "BTC/USDT"),
        timeframe=os.getenv("TIMEFRAME", "15m"),
        trade_amount_quote=_float("TRADE_AMOUNT_QUOTE", 50.0),
        sma_short=_int("SMA_SHORT", 9),
        sma_long=_int("SMA_LONG", 21),
        rsi_period=_int("RSI_PERIOD", 14),
        rsi_overbought=_float("RSI_OVERBOUGHT", 70.0),
        rsi_buy_max=_float("RSI_BUY_MAX", 60.0),
        stop_loss_pct=_float("STOP_LOSS_PCT", 0.03),
        take_profit_pct=_float("TAKE_PROFIT_PCT", 0.05),
        poll_interval_seconds=_int("POLL_INTERVAL_SECONDS", 60),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
    )
