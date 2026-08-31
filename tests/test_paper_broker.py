import pytest

from src.paper_broker import can_sell, compute_buy, compute_sell, min_sell_price, unrealized_pnl
from src.paper_state import new_account


def test_compute_buy_applies_trade_percent_and_fee():
    execution = compute_buy(balance=3000.0, trade_percent=30, price=100_000, buy_fee_percent=0.1)

    assert execution.quote_spent == pytest.approx(900.0)
    assert execution.fee_quote == pytest.approx(0.9)
    assert execution.quantity == pytest.approx((900.0 - 0.9) / 100_000)
    assert execution.cost_basis == pytest.approx(900.0)


def test_min_sell_price_covers_fees_and_min_profit():
    buy = compute_buy(balance=3000.0, trade_percent=30, price=100_000, buy_fee_percent=0.1)
    price = min_sell_price(buy.cost_basis, buy.quantity, min_profit_percent=0.5, sell_fee_percent=0.1)

    sale = compute_sell(buy.cost_basis, buy.quantity, price, sell_fee_percent=0.1)
    assert sale.profit_percent == pytest.approx(0.5, rel=1e-6)


def test_cannot_sell_below_min_profit():
    buy = compute_buy(balance=3000.0, trade_percent=30, price=100_000, buy_fee_percent=0.1)
    required = min_sell_price(buy.cost_basis, buy.quantity, min_profit_percent=0.5, sell_fee_percent=0.1)

    assert not can_sell(buy.cost_basis, buy.quantity, required - 1, min_profit_percent=0.5, sell_fee_percent=0.1)
    # price above the raw entry price, but still below the min-profit threshold, must still refuse
    assert not can_sell(buy.cost_basis, buy.quantity, 100_050, min_profit_percent=0.5, sell_fee_percent=0.1)


def test_sell_allowed_once_min_profit_reached():
    buy = compute_buy(balance=3000.0, trade_percent=30, price=100_000, buy_fee_percent=0.1)
    required = min_sell_price(buy.cost_basis, buy.quantity, min_profit_percent=0.5, sell_fee_percent=0.1)

    assert can_sell(buy.cost_basis, buy.quantity, required, min_profit_percent=0.5, sell_fee_percent=0.1)
    assert can_sell(buy.cost_basis, buy.quantity, required * 1.01, min_profit_percent=0.5, sell_fee_percent=0.1)


def test_balance_updates_correctly_after_full_buy_sell_cycle():
    account = new_account(3000.0)

    buy = compute_buy(balance=account.balance, trade_percent=30, price=100_000, buy_fee_percent=0.1)
    account.balance -= buy.quote_spent
    assert account.balance == pytest.approx(2100.0)

    sell_price = min_sell_price(buy.cost_basis, buy.quantity, min_profit_percent=0.5, sell_fee_percent=0.1)
    sale = compute_sell(buy.cost_basis, buy.quantity, sell_price, sell_fee_percent=0.1)
    account.balance += sale.net_proceeds
    account.realized_profit += sale.profit_quote

    assert account.balance == pytest.approx(2100.0 + 900.0 * 1.005, rel=1e-6)
    assert account.realized_profit == pytest.approx(900.0 * 0.005, rel=1e-6)


def test_unrealized_pnl_reflects_sell_fee():
    buy = compute_buy(balance=3000.0, trade_percent=30, price=100_000, buy_fee_percent=0.1)

    pnl_quote, pnl_percent = unrealized_pnl(buy.cost_basis, buy.quantity, price=100_000, sell_fee_percent=0.1)

    # selling right back at the entry price still loses to both the buy and sell fee (~0.2%)
    assert pnl_quote < 0
    assert pnl_percent == pytest.approx(-0.2, abs=0.01)
