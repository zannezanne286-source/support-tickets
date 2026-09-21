# indicators.py

import pandas as pd
import numpy as np
import pandas_ta as ta


class IndicatorEngine:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.results = {}

    def compute_all(self):
        self._rsi()
        self._macd()
        self._bollinger()
        self._ema()
        self._atr()
        self._stochastic()
        self._ichimoku()
        self._volume_ma()
        return self.df

    def _rsi(self, length=14):
        self.df["rsi"] = ta.rsi(self.df["close"], length=length)
        last = self.df["rsi"].iloc[-1]
        if last > 70:
            self.results["RSI"] = {"value": round(last, 2), "signal": "SURACHAT", "score": -2}
        elif last < 30:
            self.results["RSI"] = {"value": round(last, 2), "signal": "SURVENTE", "score": +2}
        else:
            self.results["RSI"] = {"value": round(last, 2), "signal": "NEUTRE", "score": 0}

    def _macd(self, fast=12, slow=26, signal=9):
        macd = ta.macd(self.df["close"], fast=fast, slow=slow, signal=signal)
        self.df["macd"] = macd[f"MACD_{fast}_{slow}_{signal}"]
        self.df["macd_signal"] = macd[f"MACDs_{fast}_{slow}_{signal}"]
        self.df["macd_hist"] = macd[f"MACDh_{fast}_{slow}_{signal}"]
        prev_diff = self.df["macd"].iloc[-2] - self.df["macd_signal"].iloc[-2]
        curr_diff = self.df["macd"].iloc[-1] - self.df["macd_signal"].iloc[-1]
        if prev_diff < 0 and curr_diff > 0:
            self.results["MACD"] = {"value": round(curr_diff, 4), "signal": "CROISEMENT HAUSSIER", "score": +2}
        elif prev_diff > 0 and curr_diff < 0:
            self.results["MACD"] = {"value": round(curr_diff, 4), "signal": "CROISEMENT BAISSIER", "score": -2}
        else:
            direction = "HAUSSIER" if curr_diff > 0 else "BAISSIER"
            self.results["MACD"] = {"value": round(curr_diff, 4), "signal": f"TENDANCE {direction}", "score": 0}

    def _bollinger(self, length=20, std=2):
        bb = ta.bbands(self.df["close"], length=length, std=std)
        self.df["bb_lower"] = bb[f"BBL_{length}_{std}.0"]
        self.df["bb_mid"] = bb[f"BBM_{length}_{std}.0"]
        self.df["bb_upper"] = bb[f"BBU_{length}_{std}.0"]
        price = self.df["close"].iloc[-1]
        upper = self.df["bb_upper"].iloc[-1]
        lower = self.df["bb_lower"].iloc[-1]
        width = (upper - lower) / self.df["bb_mid"].iloc[-1]
        if price <= lower:
            self.results["Bollinger"] = {"value": round(price, 2), "signal": "PRIX SOUS BANDE INF.", "score": +2}
        elif price >= upper:
            self.results["Bollinger"] = {"value": round(price, 2), "signal": "PRIX SUR BANDE SUP.", "score": -2}
        elif width < 0.02:
            self.results["Bollinger"] = {"value": round(width, 4), "signal": "BANDES RESSERREES", "score": 0}
        else:
            self.results["Bollinger"] = {"value": round(width, 4), "signal": "NEUTRE", "score": 0}

    def _ema(self, periods=(50, 200)):
        self.df["ema50"] = ta.ema(self.df["close"], length=periods[0])
        self.df["ema200"] = ta.ema(self.df["close"], length=periods[1])
        price = self.df["close"].iloc[-1]
        ema50 = self.df["ema50"].iloc[-1]
        ema200 = self.df["ema200"].iloc[-1]
        if price > ema50 > ema200:
            self.results["EMA"] = {"value": round(ema50, 2), "signal": "TENDANCE HAUSSIERE FORTE", "score": +2}
        elif price < ema50 < ema200:
            self.results["EMA"] = {"value": round(ema50, 2), "signal": "TENDANCE BAISSIERE FORTE", "score": -2}
        else:
            self.results["EMA"] = {"value": round(ema50, 2), "signal": "TENDANCE MIXTE", "score": 0}

    def _atr(self, length=14):
        self.df["atr"] = ta.atr(self.df["high"], self.df["low"], self.df["close"], length=length)
        self.results["ATR"] = {"value": round(self.df["atr"].iloc[-1], 4), "signal": "VOLATILITE", "score": 0}

    def _stochastic(self, k=14, d=3, smooth=3):
        stoch = ta.stoch(self.df["high"], self.df["low"], self.df["close"], k=k, d=d, smooth_k=smooth)
        self.df["stoch_k"] = stoch[f"STOCHk_{k}_{d}_{smooth}"]
        self.df["stoch_d"] = stoch[f"STOCHd_{k}_{d}_{smooth}"]
        last = self.df["stoch_k"].iloc[-1]
        if last > 80:
            self.results["Stochastique"] = {"value": round(last, 2), "signal": "SURACHAT", "score": -1}
        elif last < 20:
            self.results["Stochastique"] = {"value": round(last, 2), "signal": "SURVENTE", "score": +1}
        else:
            self.results["Stochastique"] = {"value": round(last, 2), "signal": "NEUTRE", "score": 0}

    def _ichimoku(self):
        ich = ta.ichimoku(self.df["high"], self.df["low"], self.df["close"])
        if ich and len(ich) > 0:
            df_ich = ich[0]
            self.df["ichi_tenkan"] = df_ich.iloc[:, 0]
            self.df["ichi_kijun"] = df_ich.iloc[:, 1]
            self.df["ichi_spanA"] = df_ich.iloc[:, 2]
            self.df["ichi_spanB"] = df_ich.iloc[:, 3]
            price = self.df["close"].iloc[-1]
            spanA = self.df["ichi_spanA"].iloc[-1]
            spanB = self.df["ichi_spanB"].iloc[-1]
            cloud_top = max(spanA, spanB)
            cloud_bottom = min(spanA, spanB)
            if price > cloud_top:
                self.results["Ichimoku"] = {"value": round(price, 2), "signal": "PRIX AU-DESSUS DU NUAGE", "score": +2}
            elif price < cloud_bottom:
                self.results["Ichimoku"] = {"value": round(price, 2), "signal": "PRIX SOUS LE NUAGE", "score": -2}
            else:
                self.results["Ichimoku"] = {"value": round(price, 2), "signal": "PRIX DANS LE NUAGE", "score": 0}

    def _volume_ma(self, length=20):
        self.df["volume_ma"] = self.df["volume"].rolling(length).mean()
        last_vol = self.df["volume"].iloc[-1]
        avg_vol = self.df["volume_ma"].iloc[-1]
        ratio = last_vol / avg_vol if avg_vol > 0 else 1
        if ratio > 1.5:
            self.results["Volume"] = {"value": round(ratio, 2), "signal": f"VOLUME FORT ({ratio:.1f}x)", "score": +1}
        elif ratio < 0.5:
            self.results["Volume"] = {"value": round(ratio, 2), "signal": f"VOLUME FAIBLE ({ratio:.1f}x)", "score": -1}
        else:
            self.results["Volume"] = {"value": round(ratio, 2), "signal": "VOLUME NORMAL", "score": 0}

    def get_summary(self):
        total_score = sum(v["score"] for v in self.results.values())
        return {
            "indicators": self.results,
            "total_score": total_score,
            "df": self.df,
          }
