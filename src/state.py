import json
import os
from dataclasses import asdict, dataclass
from typing import Optional

STATE_FILE = "state.json"


@dataclass
class Position:
    in_position: bool = False
    entry_price: float = 0.0
    amount: float = 0.0


def load_position() -> Position:
    if not os.path.exists(STATE_FILE):
        return Position()
    with open(STATE_FILE, "r") as f:
        data = json.load(f)
    return Position(**data)


def save_position(position: Position) -> None:
    with open(STATE_FILE, "w") as f:
        json.dump(asdict(position), f)
