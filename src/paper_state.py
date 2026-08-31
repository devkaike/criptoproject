"""Paper-trading account persistence.

Same JSON-on-disk approach as src/state.py, kept in its own file
(paper_state.json) so it never collides with the live SMA/RSI trader's
state. load_account/save_account are the seam to swap in a real database
later without touching src/paper_trader.py.
"""
import json
import os
from dataclasses import asdict, dataclass, field
from typing import Optional

PAPER_STATE_FILE = "paper_state.json"


@dataclass
class PaperPosition:
    open: bool = False
    entry_price: float = 0.0
    quantity: float = 0.0
    cost_basis: float = 0.0
    buy_fee: float = 0.0
    opened_at: str = ""


@dataclass
class PaperTrade:
    side: str
    price: float
    quantity: float
    quote_amount: float
    fee_quote: float
    timestamp: str
    profit_quote: Optional[float] = None
    profit_percent: Optional[float] = None


@dataclass
class PaperAccount:
    balance: float
    realized_profit: float = 0.0
    position: PaperPosition = field(default_factory=PaperPosition)
    history: list = field(default_factory=list)


def new_account(initial_capital: float) -> PaperAccount:
    return PaperAccount(balance=initial_capital)


def load_account(initial_capital: float) -> PaperAccount:
    if not os.path.exists(PAPER_STATE_FILE):
        return new_account(initial_capital)
    with open(PAPER_STATE_FILE, "r") as f:
        data = json.load(f)
    position = PaperPosition(**data.get("position", {}))
    history = [PaperTrade(**trade) for trade in data.get("history", [])]
    return PaperAccount(
        balance=data["balance"],
        realized_profit=data.get("realized_profit", 0.0),
        position=position,
        history=history,
    )


def save_account(account: PaperAccount) -> None:
    with open(PAPER_STATE_FILE, "w") as f:
        json.dump(asdict(account), f, indent=2)
