"""Order placement logic — sits between the CLI and the raw client."""

from typing import Optional

from .client import BinanceClient, BinanceClientError
from .logging_config import setup_logger
from .validators import ValidationError, validate_all

logger = setup_logger("trading_bot.orders")


def _fmt_order_summary(params: dict) -> str:
    lines = [
        "┌─ Order Request ─────────────────────────",
        f"│  Symbol     : {params['symbol']}",
        f"│  Side       : {params['side']}",
        f"│  Type       : {params['order_type']}",
        f"│  Quantity   : {params['quantity']}",
    ]
    if params.get("price"):
        lines.append(f"│  Price      : {params['price']}")
    if params.get("stop_price"):
        lines.append(f"│  Stop Price : {params['stop_price']}")
    lines.append("└─────────────────────────────────────────")
    return "\n".join(lines)


def _fmt_order_response(resp: dict) -> str:
    lines = [
        "┌─ Order Response ────────────────────────",
        f"│  Order ID   : {resp.get('orderId', 'N/A')}",
        f"│  Symbol     : {resp.get('symbol', 'N/A')}",
        f"│  Status     : {resp.get('status', 'N/A')}",
        f"│  Side       : {resp.get('side', 'N/A')}",
        f"│  Type       : {resp.get('type', 'N/A')}",
        f"│  Orig Qty   : {resp.get('origQty', 'N/A')}",
        f"│  Executed   : {resp.get('executedQty', 'N/A')}",
        f"│  Avg Price  : {resp.get('avgPrice', resp.get('price', 'N/A'))}",
        "└─────────────────────────────────────────",
    ]
    return "\n".join(lines)


def place_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
    stop_price: Optional[float] = None,
) -> dict:
    """Validate inputs, place the order, and return the response dict."""

    # --- Validation ---
    try:
        params = validate_all(symbol, side, order_type, quantity, price, stop_price)
    except ValidationError as exc:
        logger.error("Validation failed: %s", exc)
        raise

    print(_fmt_order_summary(params))
    logger.info("Order summary: %s", params)

    # --- API call ---
    try:
        response = client.place_order(
            symbol=params["symbol"],
            side=params["side"],
            order_type=params["order_type"],
            quantity=params["quantity"],
            price=params["price"],
            stop_price=params["stop_price"],
        )
    except BinanceClientError as exc:
        logger.error("Order placement failed: %s", exc)
        raise
    except (ConnectionError, TimeoutError) as exc:
        logger.error("Network error during order placement: %s", exc)
        raise

    print(_fmt_order_response(response))
    logger.info("Order placed successfully: orderId=%s status=%s", response.get("orderId"), response.get("status"))
    print("✅  Order placed successfully!\n")

    return response
