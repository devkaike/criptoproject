from src.config import load_config
from src.paper_trader import PaperTrader

if __name__ == "__main__":
    config = load_config()
    if not config.paper_trading:
        raise SystemExit(
            "PAPER_TRADING=false: paper_main.py só executa em modo simulado. "
            "Defina PAPER_TRADING=true no .env para rodar este bot."
        )
    trader = PaperTrader(config)
    trader.run_forever()
