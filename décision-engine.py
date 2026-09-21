# decision_engine.py

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TradeSignal:
    symbol: str
    price: float
    trend: str
    confidence: str
    tech_score: int = 0
    fund_score: int = 0
    pattern_score: int = 0
    total_score: int = 0
    entry: Optional[float] = None
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None
    tp_pct: Optional[float] = None
    sl_pct: Optional[float] = None
    risk_reward: Optional[float] = None
    invest_100_tp: Optional[float] = None
    invest_100_sl: Optional[float] = None
    reasons: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


class DecisionEngine:
    def decide(self, symbol, df, indicators_summary, patterns, levels,
               fundamental_summary, atr_value, current_price):
        signal = TradeSignal(symbol=symbol, price=current_price, trend="NEUTRE", confidence="DANGEREUX")
        signal.tech_score = indicators_summary.get("total_score", 0)
        signal.fund_score = fundamental_summary.get("total_score", 0)
        signal.pattern_score = sum(p["score"] for p in patterns)
        signal.total_score = signal.tech_score + signal.fund_score + signal.pattern_score

        for name, data in indicators_summary.get("indicators", {}).items():
            if data["score"] != 0:
                signal.reasons.append(f"{name} : {data['signal']}")
        for p in patterns:
            signal.reasons.append(f"Figure {p['name']} ({p['type']})")
        fg = fundamental_summary.get("fear_greed", {})
        if fg.get("score", 0) != 0:
            signal.reasons.append(f"Fear & Greed : {fg['signal']}")

        score = signal.total_score
        if score >= 7:
            signal.trend = "ACHAT FORT"
            signal.confidence = "FIABLE"
        elif score >= 4:
            signal.trend = "ACHAT MODERE"
            signal.confidence = "MOYEN"
        elif score >= -3:
            signal.trend = "NEUTRE"
            signal.confidence = "DANGEREUX"
        elif score >= -6:
            signal.trend = "VENTE MODEREE"
            signal.confidence = "MOYEN"
        else:
            signal.trend = "VENTE FORTE"
            signal.confidence = "FIABLE"

        if signal.trend == "NEUTRE":
            signal.warnings.append("Marche sans direction claire. Ne pas trader.")
            return signal

        supports = levels.get("supports", [])
        resistances = levels.get("resistances", [])

        if not supports or not resistances:
            signal.warnings.append("Supports/resistances insuffisants. Trade annule.")
            signal.trend = "NEUTRE"
            signal.confidence = "DANGEREUX"
            return signal

        if signal.trend in ["ACHAT FORT", "ACHAT MODERE"]:
            self._calc_buy(signal, current_price, atr_value, resistances, supports)
        else:
            self._calc_sell(signal, current_price, atr_value, resistances, supports)

        if signal.risk_reward is not None and signal.risk_reward < 1.5:
            signal.warnings.append(f"Ratio R/R trop faible ({signal.risk_reward:.2f}:1 < 1.5:1). Trade annule.")
            signal.trend = "NEUTRE"
            signal.confidence = "DANGEREUX"

        return signal

    def _calc_buy(self, signal, price, atr, resistances, supports):
        signal.entry = price
        nearest_support = max([s for s in supports if s < price], default=price * 0.97)
        sl_atr = price - (1.5 * atr)
        signal.stop_loss = min(nearest_support * 0.998, sl_atr)
        above = [r for r in resistances if r > price]
        if above:
            signal.take_profit = min(above)
        else:
            signal.take_profit = price + (3 * atr)
        signal.tp_pct = ((signal.take_profit - signal.entry) / signal.entry) * 100
        signal.sl_pct = ((signal.stop_loss - signal.entry) / signal.entry) * 100
        risk = signal.entry - signal.stop_loss
        reward = signal.take_profit - signal.entry
        signal.risk_reward = reward / risk if risk > 0 else 0
        signal.invest_100_tp = 100 * (signal.tp_pct / 100)
        signal.invest_100_sl = 100 * (signal.sl_pct / 100)

    def _calc_sell(self, signal, price, atr, resistances, supports):
        signal.entry = price
        nearest_resistance = min([r for r in resistances if r > price], default=price * 1.03)
        sl_atr = price + (1.5 * atr)
        signal.stop_loss = max(nearest_resistance * 1.002, sl_atr)
        below = [s for s in supports if s < price]
        if below:
            signal.take_profit = max(below)
        else:
            signal.take_profit = price - (3 * atr)
        signal.tp_pct = ((signal.take_profit - signal.entry) / signal.entry) * 100
        signal.sl_pct = ((signal.stop_loss - signal.entry) / signal.entry) * 100
        risk = signal.stop_loss - signal.entry
        reward = signal.entry - signal.take_profit
        signal.risk_reward = reward / risk if risk > 0 else 0
        signal.invest_100_tp = 100 * (signal.tp_pct / 100)
        signal.invest_100_sl = 100 * (signal.sl_pct / 100)
