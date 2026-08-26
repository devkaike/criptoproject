import ccxt
import pandas as pd

from src.config import Config


class ExchangeClient:
    def __init__(self, config: Config):
        exchange_class = getattr(ccxt, config.exchange_id)
        self.exchange = exchange_class(
            {
                "apiKey": config.api_key,
                "secret": config.api_secret,
                "enableRateLimit": True,
            }
        )
        if config.use_testnet:
            self.exchange.set_sandbox_mode(True)

        self.symbol = config.symbol
        self.dry_run = config.dry_run

    def fetch_ohlcv_df(self, timeframe: str, limit: int = 200) -> pd.DataFrame:
        raw = self.exchange.fetch_ohlcv(self.symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(
            raw, columns=["timestamp", "open", "high", "low", "close", "volume"]
        )
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df

    def fetch_last_price(self) -> float:
        ticker = self.exchange.fetch_ticker(self.symbol)
        return float(ticker["last"])

    def fetch_quote_balance(self, quote_currency: str) -> float:
        if self.dry_run:
            return float("inf")
        balance = self.exchange.fetch_balance()
        return float(balance.get(quote_currency, {}).get("free", 0.0))

    def create_market_buy(self, quote_amount: float, price: float) -> dict:
        base_amount = quote_amount / price
        if self.dry_run:
            return {
                "id": "dry-run-buy",
                "side": "buy",
                "amount": base_amount,
                "price": price,
                "dry_run": True,
            }
        return self.exchange.create_market_buy_order(self.symbol, base_amount)

    def create_market_sell(self, base_amount: float, price: float) -> dict:
        if self.dry_run:
            return {
                "id": "dry-run-sell",
                "side": "sell",
                "amount": base_amount,
                "price": price,
                "dry_run": True,
            }
        return self.exchange.create_market_sell_order(self.symbol, base_amount)
