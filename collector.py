# collector.py

import ccxt
import pandas as pd
import time
from config import EXCHANGES, TIMEFRAMES, HISTORY_LIMIT, SYMBOLS


class DataCollector:
    def __init__(self):
        self.exchanges = {}
        self._init_exchanges()

    def _init_exchanges(self):
        for name, cfg in EXCHANGES.items():
            if not cfg["enabled"]:
                continue
            try:
                exchange_class = getattr(ccxt, name)
                exchange = exchange_class({
                    "enableRateLimit": True,
                    "options": {"defaultType": "spot"},
                })
                if cfg["sandbox"]:
                    exchange.set_sandbox_mode(True)
                self.exchanges[name] = exchange
                print(f"Connecte a {name}")
            except Exception as e:
                print(f"Erreur connexion {name} : {e}")

    def fetch_ohlcv(self, exchange_name, symbol, timeframe, limit=HISTORY_LIMIT):
        if exchange_name not in self.exchanges:
            return None
        exchange = self.exchanges[exchange_name]
        try:
            data = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(
                data,
                columns=["timestamp", "open", "high", "low", "close", "volume"]
            )
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df.set_index("timestamp", inplace=True)
            return df
        except Exception as e:
            print(f"Erreur {exchange_name} {symbol} {timeframe} : {e}")
            return None

    def fetch_ticker(self, exchange_name, symbol):
        if exchange_name not in self.exchanges:
            return None
        try:
            return self.exchanges[exchange_name].fetch_ticker(symbol)
        except Exception as e:
            print(f"Erreur ticker {symbol} : {e}")
            return None

    def fetch_orderbook(self, exchange_name, symbol, limit=20):
        if exchange_name not in self.exchanges:
            return None
        try:
            return self.exchanges[exchange_name].fetch_order_book(symbol, limit=limit)
        except Exception as e:
            print(f"Erreur orderbook {symbol} : {e}")
            return None

    def fetch_all_ohlcv(self, exchange_name="binance", timeframe="1h"):
        results = {}
        for symbol in SYMBOLS:
            df = self.fetch_ohlcv(exchange_name, symbol, timeframe)
            if df is not None and len(df) > 0:
                results[symbol] = df
            time.sleep(0.1)
        return results

    def fetch_multi_timeframe(self, exchange_name, symbol):
        results = {}
        for tf in TIMEFRAMES:
            df = self.fetch_ohlcv(exchange_name, symbol, tf)
            if df is not None:
                results[tf] = df
            time.sleep(0.05)
        return results
