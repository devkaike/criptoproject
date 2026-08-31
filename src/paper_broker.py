"""Pure paper-trading math: no I/O, no exchange calls, no state.

Given a wallet balance and the configured percentages, computes what a buy
or sell would do, and the minimum price at which a sell clears the
configured minimum net profit after both buy and sell fees.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class BuyExecution:
    quantity: float
    quote_spent: float
    fee_quote: float
    cost_basis: float


@dataclass(frozen=True)
class SellExecution:
    quantity: float
    gross_proceeds: float
    fee_quote: float
    net_proceeds: float
    profit_quote: float
    profit_percent: float


def compute_buy(
    balance: float, trade_percent: float, price: float, buy_fee_percent: float
) -> BuyExecution:
    quote_spent = balance * (trade_percent / 100)
    fee_quote = quote_spent * (buy_fee_percent / 100)
    quantity = (quote_spent - fee_quote) / price
    return BuyExecution(
        quantity=quantity,
        quote_spent=quote_spent,
        fee_quote=fee_quote,
        cost_basis=quote_spent,
    )


def min_sell_price(
    cost_basis: float, quantity: float, min_profit_percent: float, sell_fee_percent: float
) -> float:
    """Lowest sell price at which net profit (after the sell fee) reaches
    min_profit_percent over cost_basis (which already reflects the buy fee)."""
    required_net_proceeds = cost_basis * (1 + min_profit_percent / 100)
    required_gross_proceeds = required_net_proceeds / (1 - sell_fee_percent / 100)
    return required_gross_proceeds / quantity


def can_sell(
    cost_basis: float,
    quantity: float,
    price: float,
    min_profit_percent: float,
    sell_fee_percent: float,
) -> bool:
    if quantity <= 0 or cost_basis <= 0:
        return False
    return price >= min_sell_price(cost_basis, quantity, min_profit_percent, sell_fee_percent)


def compute_sell(
    cost_basis: float, quantity: float, price: float, sell_fee_percent: float
) -> SellExecution:
    gross_proceeds = quantity * price
    fee_quote = gross_proceeds * (sell_fee_percent / 100)
    net_proceeds = gross_proceeds - fee_quote
    profit_quote = net_proceeds - cost_basis
    profit_percent = (profit_quote / cost_basis) * 100
    return SellExecution(
        quantity=quantity,
        gross_proceeds=gross_proceeds,
        fee_quote=fee_quote,
        net_proceeds=net_proceeds,
        profit_quote=profit_quote,
        profit_percent=profit_percent,
    )


def unrealized_pnl(
    cost_basis: float, quantity: float, price: float, sell_fee_percent: float
) -> tuple[float, float]:
    """PnL (quote, percent) if the position were closed at `price` right now,
    net of the sell fee it would incur."""
    if quantity <= 0 or cost_basis <= 0:
        return 0.0, 0.0
    gross = quantity * price
    net = gross - gross * (sell_fee_percent / 100)
    pnl_quote = net - cost_basis
    pnl_percent = (pnl_quote / cost_basis) * 100
    return pnl_quote, pnl_percent
