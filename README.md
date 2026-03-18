# Binance Futures Testnet Trading Bot

A clean, structured Python CLI application to place orders on **Binance Futures Testnet (USDT-M)**.

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance REST API client (no SDK — pure requests)
│   ├── orders.py          # Order placement logic + formatted output
│   ├── validators.py      # Input validation with clear error messages
│   └── logging_config.py  # Dual-sink logger (file + console)
├── cli.py                 # argparse CLI entry point
├── logs/                  # Auto-created; one log file per day
├── .env.example           # Template for credentials
├── requirements.txt
└── README.md
```

---

## Setup

### 1 — Get Testnet Credentials

1. Visit [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Log in (GitHub OAuth works).
3. Go to **API Management** → generate a key pair.
4. Copy your **API Key** and **Secret Key**.

### 2 — Install Dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3 — Configure Credentials

```bash
cp .env.example .env
# Edit .env and paste your API key and secret
```

`.env` file format:
```
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here
```

---

## How to Run

### Place a Market Order

```bash
# Market BUY 0.01 BTC
python cli.py place-order --symbol BTCUSDT --side BUY --type MARKET --qty 0.01

# Market SELL 0.01 BTC
python cli.py place-order --symbol BTCUSDT --side SELL --type MARKET --qty 0.01
```

### Place a Limit Order

```bash
# Limit SELL at $88,000
python cli.py place-order --symbol BTCUSDT --side SELL --type LIMIT --qty 0.01 --price 88000

# Limit BUY at $78,000
python cli.py place-order --symbol BTCUSDT --side BUY --type LIMIT --qty 0.01 --price 78000
```

### Place a Stop-Market Order *(bonus order type)*

```bash
# Stop-Market BUY triggered at $80,000
python cli.py place-order --symbol BTCUSDT --side BUY --type STOP_MARKET --qty 0.01 --stop-price 80000
```

### Other Commands

```bash
# Check USDT balance
python cli.py balance

# List open orders (all symbols)
python cli.py open-orders

# List open orders for a specific symbol
python cli.py open-orders --symbol BTCUSDT
```

---

## Example Output

```
┌─ Order Request ─────────────────────────
│  Symbol     : BTCUSDT
│  Side       : BUY
│  Type       : MARKET
│  Quantity   : 0.01
└─────────────────────────────────────────
┌─ Order Response ────────────────────────
│  Order ID   : 3842910
│  Symbol     : BTCUSDT
│  Status     : FILLED
│  Side       : BUY
│  Type       : MARKET
│  Orig Qty   : 0.01
│  Executed   : 0.01
│  Avg Price  : 83241.50
└─────────────────────────────────────────
✅  Order placed successfully!
```

---

## Logging

Logs are written to `logs/trading_bot_YYYYMMDD.log`.

- **File log**: `DEBUG` level — full request/response details, timestamps, errors.
- **Console log**: `INFO` level — clean, human-readable summaries.

Log files from test runs are included in the `logs/` directory.

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Missing API credentials | Exits with clear message before any network call |
| Invalid `--side` / `--type` | Caught by argparse choices validation |
| Invalid quantity / price | Caught by `validators.py` with descriptive message |
| Binance API error (e.g. insufficient margin) | `BinanceClientError` raised, code + message printed |
| Network timeout / unreachable host | `ConnectionError` / `TimeoutError` caught and reported |

---

## Assumptions

- Only **USDT-M Futures** (linear) on testnet are targeted.
- `STOP_MARKET` is included as the bonus third order type.
- No third-party Binance SDK is used; all API calls are raw `requests` for transparency and portability.
- Credentials are loaded from a `.env` file (via `python-dotenv`) or from environment variables directly — no hardcoding.
- Quantity and price precision are passed as-is; for production you would clamp them to the symbol's `LOT_SIZE` / `PRICE_FILTER` from `/fapi/v1/exchangeInfo`.

---

## Requirements

```
requests>=2.31.0
python-dotenv>=1.0.0
```

Python 3.8+ required.
