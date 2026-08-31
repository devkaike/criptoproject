"""Pure summary-building for the paper trading report (no I/O)."""
from dataclasses import dataclass

from src.paper_broker import min_sell_price, unrealized_pnl
from src.paper_state import PaperAccount


@dataclass(frozen=True)
class ReportSummary:
    balance: float
    position_open: bool
    entry_price: float
    quantity: float
    min_sell_price: float
    unrealized_pnl_quote: float
    unrealized_pnl_percent: float
    equity: float
    realized_profit: float
    total_trades: int
    wins: int
    losses: int
    win_rate_percent: float


def build_summary(
    account: PaperAccount, current_price: float, min_profit_percent: float, sell_fee_percent: float
) -> ReportSummary:
    pos = account.position
    required_price = 0.0
    pnl_quote = 0.0
    pnl_percent = 0.0
    position_value = 0.0

    if pos.open:
        required_price = min_sell_price(pos.cost_basis, pos.quantity, min_profit_percent, sell_fee_percent)
        pnl_quote, pnl_percent = unrealized_pnl(pos.cost_basis, pos.quantity, current_price, sell_fee_percent)
        position_value = pos.quantity * current_price

    sells = [trade for trade in account.history if trade.side == "sell"]
    wins = sum(1 for trade in sells if (trade.profit_quote or 0) > 0)
    total = len(sells)
    losses = total - wins
    win_rate = (wins / total * 100) if total else 0.0

    return ReportSummary(
        balance=account.balance,
        position_open=pos.open,
        entry_price=pos.entry_price,
        quantity=pos.quantity,
        min_sell_price=required_price,
        unrealized_pnl_quote=pnl_quote,
        unrealized_pnl_percent=pnl_percent,
        equity=account.balance + position_value,
        realized_profit=account.realized_profit,
        total_trades=total,
        wins=wins,
        losses=losses,
        win_rate_percent=win_rate,
    )
