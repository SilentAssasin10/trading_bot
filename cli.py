#!/usr/bin/env python3
"""
CLI entry point for the Binance Futures Testnet trading bot.

Usage examples
--------------
# Market BUY
python cli.py place-order --symbol BTCUSDT --side BUY --type MARKET --qty 0.01

# Limit SELL
python cli.py place-order --symbol BTCUSDT --side SELL --type LIMIT --qty 0.01 --price 70000

# Stop-Market BUY (bonus order type)
python cli.py place-order --symbol BTCUSDT --side BUY --type STOP_MARKET --qty 0.01 --stop-price 65000

# Show account USDT balance
python cli.py balance

# Show open orders
python cli.py open-orders --symbol BTCUSDT
"""

import os
import sys
import argparse

from dotenv import load_dotenv

from bot.client import BinanceClient, BinanceClientError
from bot.logging_config import setup_logger
from bot.orders import place_order
from bot.validators import ValidationError

load_dotenv()
logger = setup_logger("trading_bot.cli")


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #

def get_client() -> BinanceClient:
    api_key = os.getenv("BINANCE_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_API_SECRET", "").strip()

    if not api_key or not api_secret:
        print("❌  Error: BINANCE_API_KEY and BINANCE_API_SECRET must be set in your .env file or environment.")
        logger.error("Missing API credentials.")
        sys.exit(1)

    return BinanceClient(api_key=api_key, api_secret=api_secret)


# ------------------------------------------------------------------ #
# Sub-command handlers
# ------------------------------------------------------------------ #

def cmd_place_order(args: argparse.Namespace) -> None:
    client = get_client()
    try:
        place_order(
            client=client,
            symbol=args.symbol,
            side=args.side.upper(),
            order_type=args.type.upper(),
            quantity=args.qty,
            price=args.price,
            stop_price=args.stop_price,
        )
    except ValidationError as exc:
        print(f"❌  Validation error: {exc}")
        sys.exit(1)
    except BinanceClientError as exc:
        print(f"❌  Binance API error [{exc.code}]: {exc.message}")
        sys.exit(1)
    except (ConnectionError, TimeoutError) as exc:
        print(f"❌  Network error: {exc}")
        sys.exit(1)


def cmd_balance(args: argparse.Namespace) -> None:
    client = get_client()
    try:
        balances = client.get_account_balance()
        usdt = next((b for b in balances if b["asset"] == "USDT"), None)
        if usdt:
            print(f"\n💰  USDT Balance")
            print(f"    Available : {usdt.get('availableBalance', 'N/A')}")
            print(f"    Wallet    : {usdt.get('balance', 'N/A')}\n")
        else:
            print("No USDT balance found.")
    except BinanceClientError as exc:
        print(f"❌  Binance API error [{exc.code}]: {exc.message}")
        sys.exit(1)


def cmd_open_orders(args: argparse.Namespace) -> None:
    client = get_client()
    try:
        orders = client.get_open_orders(symbol=args.symbol)
        if not orders:
            print("No open orders found.")
            return
        print(f"\n📋  Open Orders ({len(orders)} total)")
        for o in orders:
            print(
                f"  ID={o['orderId']} | {o['symbol']} | {o['side']} {o['type']} "
                f"| qty={o['origQty']} | price={o.get('price','N/A')} | status={o['status']}"
            )
        print()
    except BinanceClientError as exc:
        print(f"❌  Binance API error [{exc.code}]: {exc.message}")
        sys.exit(1)


# ------------------------------------------------------------------ #
# Argument parser
# ------------------------------------------------------------------ #

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Binance Futures Testnet Trading Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- place-order ---
    po = subparsers.add_parser("place-order", help="Place a new futures order")
    po.add_argument("--symbol",     required=True,              help="Trading pair, e.g. BTCUSDT")
    po.add_argument("--side",       required=True,              choices=["BUY", "SELL", "buy", "sell"], help="BUY or SELL")
    po.add_argument("--type",       required=True,              choices=["MARKET", "LIMIT", "STOP_MARKET",
                                                                          "market", "limit", "stop_market"],
                                                                help="Order type")
    po.add_argument("--qty",        required=True, type=float,  help="Order quantity")
    po.add_argument("--price",      required=False, type=float, default=None, help="Limit price (required for LIMIT)")
    po.add_argument("--stop-price", dest="stop_price", required=False, type=float, default=None,
                    help="Stop price (required for STOP_MARKET)")
    po.set_defaults(func=cmd_place_order)

    # --- balance ---
    bal = subparsers.add_parser("balance", help="Show USDT futures balance")
    bal.set_defaults(func=cmd_balance)

    # --- open-orders ---
    oo = subparsers.add_parser("open-orders", help="List open orders")
    oo.add_argument("--symbol", default=None, help="Filter by symbol")
    oo.set_defaults(func=cmd_open_orders)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    logger.info("Command invoked: %s | args=%s", args.command, vars(args))
    args.func(args)


if __name__ == "__main__":
    main()
