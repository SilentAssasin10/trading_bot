"""Binance Futures Testnet API client (pure REST, no third-party SDK required)."""

import hashlib
import hmac
import time
from typing import Any, Optional
from urllib.parse import urlencode

import requests

from .logging_config import setup_logger

BASE_URL = "https://testnet.binancefuture.com"
logger = setup_logger("trading_bot.client")


class BinanceClientError(Exception):
    """Raised for Binance API-level errors."""
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"Binance API Error {code}: {message}")


class BinanceClient:
    def __init__(self, api_key: str, api_secret: str, base_url: str = BASE_URL):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "X-MBX-APIKEY": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded",
        })
        logger.debug("BinanceClient initialised. base_url=%s", self.base_url)

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #

    def _sign(self, params: dict) -> dict:
        params["timestamp"] = int(time.time() * 1000)
        query = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    def _request(
        self,
        method: str,
        endpoint: str,
        signed: bool = False,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
    ) -> Any:
        params = params or {}
        data = data or {}

        if signed:
            # Merge params + data for signing, then split back
            combined = {**params, **data}
            combined = self._sign(combined)
            # For POST we send as body; GET as query string
            if method.upper() == "GET":
                params = combined
                data = {}
            else:
                data = combined
                params = {}

        url = f"{self.base_url}{endpoint}"
        logger.debug("REQUEST  %s %s | params=%s | data=%s", method.upper(), url, params, data)

        try:
            response = self.session.request(
                method,
                url,
                params=params if params else None,
                data=data if data else None,
                timeout=10,
            )
        except requests.exceptions.ConnectionError as exc:
            logger.error("Network error reaching %s: %s", url, exc)
            raise ConnectionError(f"Cannot connect to Binance API: {exc}") from exc
        except requests.exceptions.Timeout:
            logger.error("Request timed out: %s", url)
            raise TimeoutError("Binance API request timed out.")

        logger.debug("RESPONSE %s %s | status=%s | body=%s", method.upper(), url, response.status_code, response.text[:500])

        try:
            payload = response.json()
        except ValueError:
            logger.error("Non-JSON response from %s: %s", url, response.text[:200])
            raise ValueError(f"Unexpected non-JSON response (HTTP {response.status_code})")

        if isinstance(payload, dict) and "code" in payload and payload["code"] != 200:
            # Binance error envelope
            logger.error("API error | code=%s | msg=%s", payload.get("code"), payload.get("msg"))
            raise BinanceClientError(payload["code"], payload.get("msg", "Unknown error"))

        return payload

    # ------------------------------------------------------------------ #
    # Public API methods
    # ------------------------------------------------------------------ #

    def get_server_time(self) -> dict:
        return self._request("GET", "/fapi/v1/time")

    def get_exchange_info(self) -> dict:
        return self._request("GET", "/fapi/v1/exchangeInfo")

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: str = "GTC",
        reduce_only: bool = False,
    ) -> dict:
        data: dict = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": str(quantity),
        }

        if order_type == "LIMIT":
            data["price"] = str(price)
            data["timeInForce"] = time_in_force

        if order_type == "STOP_MARKET":
            data["stopPrice"] = str(stop_price)

        if reduce_only:
            data["reduceOnly"] = "true"

        logger.info("Placing order | %s", data)
        return self._request("POST", "/fapi/v1/order", signed=True, data=data)

    def get_order(self, symbol: str, order_id: int) -> dict:
        params = {"symbol": symbol, "orderId": order_id}
        return self._request("GET", "/fapi/v1/order", signed=True, params=params)

    def get_open_orders(self, symbol: Optional[str] = None) -> list:
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._request("GET", "/fapi/v1/openOrders", signed=True, params=params)

    def get_account_balance(self) -> list:
        return self._request("GET", "/fapi/v2/balance", signed=True)
