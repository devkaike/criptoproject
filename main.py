from src.config import load_config
from src.trader import Trader

if __name__ == "__main__":
    config = load_config()
    trader = Trader(config)
    trader.run_forever()
