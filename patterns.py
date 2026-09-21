# patterns.py

import pandas as pd
import numpy as np


class CandlePatternDetector:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.patterns = []

    def detect_all(self):
        for i in range(-5, 0):
            self._doji(i)
            self._hammer(i)
            self._shooting_star(i)
            self._engulfing(i)
            self._morning_star(i)
            self._evening_star(i)
        return self.patterns

    def _body(self, i):
        return abs(self.df["close"].iloc[i] - self.df["open"].iloc[i])

    def _range(self, i):
        return self.df["high"].iloc[i] - self.df["low"].iloc[i]

    def _upper_wick(self, i):
        return self.df["high"].iloc[i] - max(self.df["close"].iloc[i], self.df["open"].iloc[i])

    def _lower_wick(self, i):
        return min(self.df["close"].iloc[i], self.df["open"].iloc[i]) - self.df["low"].iloc[i]

    def _is_bullish(self, i):
        return self.df["close"].iloc[i] > self.df["open"].iloc[i]

    def _is_bearish(self, i):
        return self.df["close"].iloc[i] < self.df["open"].iloc[i]

    def _doji(self, i):
        if self._range(i) == 0:
            return
        if self._body(i) / self._range(i) < 0.1:
            self.patterns.append({"index": i, "name": "Doji", "type": "INDECISION", "score": 0, "price": self.df["close"].iloc[i]})

    def _hammer(self, i):
        if self._range(i) == 0:
            return
        if (self._lower_wick(i) > 2 * self._body(i)
                and self._upper_wick(i) < self._body(i) * 0.5
                and self._body(i) / self._range(i) < 0.4):
            self.patterns.append({"index": i, "name": "Marteau", "type": "HAUSSIER", "score": +2, "price": self.df["close"].iloc[i]})

    def _shooting_star(self, i):
        if self._range(i) == 0:
            return
        if (self._upper_wick(i) > 2 * self._body(i)
                and self._lower_wick(i) < self._body(i) * 0.5
                and self._body(i) / self._range(i) < 0.4):
            self.patterns.append({"index": i, "name": "Etoile Filante", "type": "BAISSIER", "score": -2, "price": self.df["close"].iloc[i]})

    def _engulfing(self, i):
        if i == -len(self.df) or self._body(i - 1) == 0:
            return
        curr_body = self._body(i)
        prev_body = self._body(i - 1)
        if (self._is_bullish(i) and self._is_bearish(i - 1)
                and self.df["close"].iloc[i] > self.df["open"].iloc[i - 1]
                and self.df["open"].iloc[i] < self.df["close"].iloc[i - 1]
                and curr_body > prev_body):
            self.patterns.append({"index": i, "name": "Englobante Haussiere", "type": "HAUSSIER", "score": +2, "price": self.df["close"].iloc[i]})
        if (self._is_bearish(i) and self._is_bullish(i - 1)
                and self.df["close"].iloc[i] < self.df["open"].iloc[i - 1]
                and self.df["open"].iloc[i] > self.df["close"].iloc[i - 1]
                and curr_body > prev_body):
            self.patterns.append({"index": i, "name": "Englobante Baissiere", "type": "BAISSIER", "score": -2, "price": self.df["close"].iloc[i]})

    def _morning_star(self, i):
        if i < 2:
            return
        if (self._is_bearish(i - 2)
                and self._body(i - 1) < self._body(i - 2) * 0.3
                and self._is_bullish(i)
                and self.df["close"].iloc[i] > (self.df["open"].iloc[i - 2] + self.df["close"].iloc[i - 2]) / 2):
            self.patterns.append({"index": i, "name": "Etoile du Matin", "type": "HAUSSIER", "score": +3, "price": self.df["close"].iloc[i]})

    def _evening_star(self, i):
        if i < 2:
            return
        if (self._is_bullish(i - 2)
                and self._body(i - 1) < self._body(i - 2) * 0.3
                and self._is_bearish(i)
                and self.df["close"].iloc[i] < (self.df["open"].iloc[i - 2] + self.df["close"].iloc[i - 2]) / 2):
            self.patterns.append({"index": i, "name": "Etoile du Soir", "type": "BAISSIER", "score": -3, "price": self.df["close"].iloc[i]})


class SupportResistanceDetector:
    def __init__(self, df: pd.DataFrame, window=5):
        self.df = df.copy()
        self.window = window
        self.supports = []
        self.resistances = []

    def detect(self):
        highs = self.df["high"].values
        lows = self.df["low"].values
        for i in range(self.window, len(self.df) - self.window):
            if highs[i] == max(highs[i - self.window:i + self.window + 1]):
                self.resistances.append(highs[i])
            if lows[i] == min(lows[i - self.window:i + self.window + 1]):
                self.supports.append(lows[i])
        self.supports = self._cluster(self.supports)
        self.resistances = self._cluster(self.resistances)
        return {
            "supports": sorted(self.supports, reverse=True)[:5],
            "resistances": sorted(self.resistances)[:5],
        }

    def _cluster(self, levels, tolerance=0.01):
        if not levels:
            return []
        levels = sorted(levels)
        clusters = [levels[0]]
        for lvl in levels[1:]:
            if abs(lvl - clusters[-1]) / clusters[-1] < tolerance:
                clusters[-1] = (clusters[-1] + lvl) / 2
            else:
                clusters.append(lvl)
        return clusters
