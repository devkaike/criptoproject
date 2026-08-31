import pytest

from src.paper_broker import compute_buy, compute_sell, min_sell_price
from src.paper_report import build_summary
from src.paper_state import PaperTrade, new_account


def test_summary_with_no_position_and_no_history():
    account = new_account(3000.0)

    summary = build_summary(account, current_price=100_000, min_profit_percent=0.5, sell_fee_percent=0.1)

    assert summary.position_open is False
    assert summary.balance == pytest.approx(3000.0)
    assert summary.equity == pytest.approx(3000.0)
    assert summary.total_trades == 0
    assert summary.win_rate_percent == 0.0


def test_summary_with_open_position_reports_unrealized_pnl_and_equity():
    account = new_account(3000.0)
    buy = compute_buy(balance=account.balance, trade_percent=30, price=100_000, buy_fee_percent=0.1)
    account.balance -= buy.quote_spent
    account.position.open = True
    account.position.entry_price = 100_000
    account.position.quantity = buy.quantity
    account.position.cost_basis = buy.cost_basis

    current_price = 101_000
    summary = build_summary(account, current_price, min_profit_percent=0.5, sell_fee_percent=0.1)

    assert summary.position_open is True
    expected_min_sell = min_sell_price(buy.cost_basis, buy.quantity, 0.5, 0.1)
    assert summary.min_sell_price == pytest.approx(expected_min_sell)
    assert summary.equity == pytest.approx(account.balance + buy.quantity * current_price)


def test_summary_win_rate_counts_only_closed_sells():
    account = new_account(3000.0)
    account.history = [
        PaperTrade(side="buy", price=100_000, quantity=0.01, quote_amount=1000, fee_quote=1, timestamp="t1"),
        PaperTrade(
            side="sell", price=101_000, quantity=0.01, quote_amount=1010, fee_quote=1,
            timestamp="t2", profit_quote=5.0, profit_percent=0.5,
        ),
        PaperTrade(side="buy", price=101_000, quantity=0.01, quote_amount=1010, fee_quote=1, timestamp="t3"),
        PaperTrade(
            side="sell", price=100_500, quantity=0.01, quote_amount=1005, fee_quote=1,
            timestamp="t4", profit_quote=-3.0, profit_percent=-0.3,
        ),
    ]

    summary = build_summary(account, current_price=100_500, min_profit_percent=0.5, sell_fee_percent=0.1)

    assert summary.total_trades == 2
    assert summary.wins == 1
    assert summary.losses == 1
    assert summary.win_rate_percent == pytest.approx(50.0)
