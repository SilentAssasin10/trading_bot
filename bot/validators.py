"""Input validation for order parameters."""

from typing import Optional

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}
MIN_QUANTITY = 0.001


class ValidationError(ValueError):
    pass


def validate_symbol(symbol: str) -> str:
    s = symbol.strip().upper()
    if not s or len(s) < 3:
        raise ValidationError(f"Invalid symbol: '{symbol}'. Example: BTCUSDT")
    return s


def validate_side(side: str) -> str:
    s = side.strip().upper()
    if s not in VALID_SIDES:
        raise ValidationError(f"Invalid side '{side}'. Must be one of: {', '.join(VALID_SIDES)}")
    return s


def validate_order_type(order_type: str) -> str:
    t = order_type.strip().upper()
    if t not in VALID_ORDER_TYPES:
        raise ValidationError(f"Invalid order type '{order_type}'. Must be one of: {', '.join(VALID_ORDER_TYPES)}")
    return t


def validate_quantity(quantity: float) -> float:
    if quantity <= 0:
        raise ValidationError(f"Quantity must be positive. Got: {quantity}")
    if quantity < MIN_QUANTITY:
        raise ValidationError(f"Quantity {quantity} is below minimum {MIN_QUANTITY}")
    return quantity


def validate_price(price: Optional[float], order_type: str) -> Optional[float]:
    if order_type in ("LIMIT", "STOP_MARKET") and (price is None or price <= 0):
        raise ValidationError(f"Price is required and must be positive for {order_type} orders.")
    if price is not None and price <= 0:
        raise ValidationError(f"Price must be positive. Got: {price}")
    return price


def validate_stop_price(stop_price: Optional[float], order_type: str) -> Optional[float]:
    if order_type == "STOP_MARKET" and (stop_price is None or stop_price <= 0):
        raise ValidationError("stopPrice is required and must be positive for STOP_MARKET orders.")
    return stop_price


def validate_all(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
    stop_price: Optional[float] = None,
) -> dict:
    return {
        "symbol": validate_symbol(symbol),
        "side": validate_side(side),
        "order_type": validate_order_type(order_type),
        "quantity": validate_quantity(quantity),
        "price": validate_price(price, order_type.upper()),
        "stop_price": validate_stop_price(stop_price, order_type.upper()),
    }
