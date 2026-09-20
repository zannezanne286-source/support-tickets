# config.py

EXCHANGES = {
    "binance": {"enabled": True, "sandbox": False},
    "bitget": {"enabled": True, "sandbox": True},
}

TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d"]
HISTORY_LIMIT = 500

SYMBOLS = [
    "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT",
    "ADA/USDT", "DOGE/USDT", "AVAX/USDT", "DOT/USDT", "MATIC/USDT",
    "LINK/USDT", "TON/USDT", "SHIB/USDT", "LTC/USDT", "BCH/USDT",
]

API_KEYS = {
    "binance": {"apiKey": "", "secret": ""},
    "bitget": {"apiKey": "", "secret": "", "password": ""},
}

DEMO_MODE = True

TRADING_CONFIG = {
    "max_risk_per_trade": 0.01,
    "max_daily_loss": 0.03,
    "max_open_positions": 5,
    "default_investment": 100,
}
