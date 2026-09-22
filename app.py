# app.py

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import time

from collector import DataCollector
from indicators import IndicatorEngine
from patterns import CandlePatternDetector, SupportResistanceDetector
from fundamental import FundamentalAnalyzer
from decision_engine import DecisionEngine
from config import SYMBOLS, TIMEFRAMES

st.set_page_config(page_title="Crypto Predictor", page_icon="📊", layout="wide")


@st.cache_resource
def get_services():
    return {
        "collector": DataCollector(),
        "fundamental": FundamentalAnalyzer(),
        "decision": DecisionEngine(),
    }


def analyze_crypto(services, symbol, exchange="binance", timeframe="1h"):
    collector = services["collector"]
    fundamental = services["fundamental"]
    decision_engine = services["decision"]
    df = collector.fetch_ohlcv(exchange, symbol, timeframe, limit=200)
    if df is None or len(df) < 50:
        return None, None
    engine = IndicatorEngine(df)
    engine.compute_all()
    ind_summary = engine.get_summary()
    detector = CandlePatternDetector(df)
    patterns = detector.detect_all()
    sr = SupportResistanceDetector(df, window=5)
    levels = sr.detect()
    base = symbol.split("/")[0]
    fund_summary = fundamental.analyze(base)
    current_price = df["close"].iloc[-1]
    atr_value = df["atr"].iloc[-1]
    signal = decision_engine.decide(
        symbol=symbol, df=df, indicators_summary=ind_summary,
        patterns=patterns, levels=levels, fundamental_summary=fund_summary,
        atr_value=atr_value, current_price=current_price,
    )
    return signal, df


def build_chart(df, symbol, levels=None):
    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=(f"{symbol} - Bougies", "RSI", "MACD"),
    )
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["open"], high=df["high"],
        low=df["low"], close=df["close"], name="Prix",
        increasing_line_color="#26a69a", decreasing_line_color="#ef5350",
    ), row=1, col=1)
    if "ema50" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["ema50"], name="EMA 50",
                                 line=dict(color="#ff9800", width=1.2)), row=1, col=1)
    if "ema200" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["ema200"], name="EMA 200",
                                 line=dict(color="#2196f3", width=1.2)), row=1, col=1)
    if "bb_upper" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["bb_upper"], name="BB Sup",
                                 line=dict(color="rgba(150,150,150,0.5)", width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["bb_lower"], name="BB Inf",
                                 line=dict(color="rgba(150,150,150,0.5)", width=1),
                                 fill="tonexty", fillcolor="rgba(150,150,150,0.1)"), row=1, col=1)
    if levels:
        for r in levels.get("resistances", [])[:3]:
            fig.add_hline(y=r, line_dash="dash", line_color="red", opacity=0.5, row=1, col=1)
        for s in levels.get("supports", [])[:3]:
            fig.add_hline(y=s, line_dash="dash", line_color="green", opacity=0.5, row=1, col=1)
    if "rsi" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["rsi"], name="RSI",
                                 line=dict(color="#9c27b0", width=1.5)), row=2, col=1)
        fig.add_hline(y=70, line_dash="dot", line_color="red", opacity=0.5, row=2, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="green", opacity=0.5, row=2, col=1)
        fig.update_yaxes(range=[0, 100], row=2, col=1)
    if "macd" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["macd"], name="MACD",
                                 line=dict(color="#2196f3", width=1.2)), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["macd_signal"], name="Signal",
                                 line=dict(color="#ff9800", width=1.2)), row=3, col=1)
        colors = ["#26a69a" if v >= 0 else "#ef5350" for v in df["macd_hist"].fillna(0)]
        fig.add_trace(go.Bar(x=df.index, y=df["macd_hist"], name="Histogramme",
                             marker_color=colors, opacity=0.5), row=3, col=1)
    fig.update_layout(height=800, showlegend=True, xaxis_rangeslider_visible=False,
                      margin=dict(l=20, r=20, t=40, b=20))
    return fig


def render_signal_card(signal):
    color_map = {
        "ACHAT FORT": "#00c853", "ACHAT MODERE": "#64dd17",
        "NEUTRE": "#9e9e9e", "VENTE MODEREE": "#ff6d00", "VENTE FORTE": "#d50000",
    }
    color = color_map.get(signal.trend, "#9e9e9e")
    st.markdown(
        f"""<div style="background-color:{color}; padding:15px; border-radius:10px; color:white;">
        <h2 style="margin:0;">{signal.symbol} — {signal.trend}</h2>
        <p style="margin:5px 0 0 0;">Confiance : <b>{signal.confidence}</b> | Score total : <b>{signal.total_score:+d}</b></p>
        </div>""", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Prix actuel", f"{signal.price:.4f}$")
    col2.metric("Entrée", f"{signal.entry:.4f}$" if signal.entry else "—")
    col3.metric("Take Profit", f"{signal.take_profit:.4f}$ ({signal.tp_pct:+.2f}%)" if signal.take_profit else "—")
    col4.metric("Stop Loss", f"{signal.stop_loss:.4f}$ ({signal.sl_pct:+.2f}%)" if signal.stop_loss else "—")
    if signal.risk_reward is not None:
        c1, c2, c3 = st.columns(3)
        c1.metric("Ratio R/R", f"{signal.risk_reward:.2f}:1")
        c2.metric("100 EUR → TP", f"{signal.invest_100_tp:+.2f} EUR" if signal.invest_100_tp else "—")
        c3.metric("100 EUR → SL", f"{signal.invest_100_sl:+.2f} EUR" if signal.invest_100_sl else "—")
    c1, c2, c3 = st.columns(3)
    c1.metric("Score Technique", f"{signal.tech_score:+d}")
    c2.metric("Score Fondamental", f"{signal.fund_score:+d}")
    c3.metric("Score Figures", f"{signal.pattern_score:+d}")
    if signal.reasons:
        with st.expander("📋 Raisons du signal", expanded=True):
            for r in signal.reasons:
                st.write(f"• {r}")
    if signal.warnings:
        for w in signal.warnings:
            st.warning(w)


def main():
    st.title("📊 Crypto Predictor — Aide à la décision")
    st.caption("Analyse technique + fondamentale. Décision finale : VOUS.")
    services = get_services()

    with st.sidebar:
        st.header("⚙️ Configuration")
        exchange = st.selectbox("Exchange", ["binance", "bitget"], index=0)
        timeframe = st.selectbox("Timeframe", TIMEFRAMES, index=3)
        st.divider()
        st.header("📋 Cryptos à analyser")
        default = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
        selected = st.multiselect("Sélection", options=SYMBOLS, default=default)
        st.divider()
        if st.button("🔄 Rafraîchir", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        st.caption("⚠️ Outil d'aide à la décision. Aucun gain garanti.")

    tab1, tab2 = st.tabs(["📈 Analyse individuelle", "📊 Vue d'ensemble"])

    with tab1:
        if not selected:
            st.info("Sélectionnez au moins une crypto dans la sidebar.")
            return
        symbol = st.selectbox("Choisir une crypto", selected)
        with st.spinner(f"Analyse de {symbol}..."):
            signal, df = analyze_crypto(services, symbol, exchange, timeframe)
        if signal is None:
            st.error(f"Impossible d'analyser {symbol}.")
            return
        render_signal_card(signal)
        st.divider()
        st.subheader("📈 Graphique")
        sr = SupportResistanceDetector(df, window=5)
        levels = sr.detect()
        fig = build_chart(df, symbol, levels)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        if not selected:
            st.info("Sélectionnez au moins une crypto.")
            return
        st.subheader(f"Analyse de {len(selected)} cryptos en {timeframe}")
        if st.button("🚀 Lancer l'analyse globale", use_container_width=True):
            progress = st.progress(0)
            results = []
            for i, sym in enumerate(selected):
                progress.progress((i + 1) / len(selected), text=f"Analyse {sym}...")
                try:
                    sig, _ = analyze_crypto(services, sym, exchange, timeframe)
                    if sig:
                        results.append(sig)
                except Exception as e:
                    st.warning(f"Erreur sur {sym} : {e}")
                time.sleep(0.2)
            progress.empty()
            if results:
                rows = []
                for s in results:
                    rows.append({
                        "Crypto": s.symbol,
                        "Prix": f"{s.price:.4f}",
                        "Tendance": s.trend,
                        "Confiance": s.confidence,
                        "Score": s.total_score,
                        "Entrée": f"{s.entry:.4f}" if s.entry else "—",
                        "TP": f"{s.take_profit:.4f}" if s.take_profit else "—",
                        "SL": f"{s.stop_loss:.4f}" if s.stop_loss else "—",
                        "R/R": f"{s.risk_reward:.2f}:1" if s.risk_reward else "—",
                    })
                df_results = pd.DataFrame(rows)
                st.dataframe(df_results, use_container_width=True, hide_index=True)
                st.divider()
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Total analysés", len(results))
                c2.metric("Achats", len([s for s in results if "ACHAT" in s.trend]))
                c3.metric("Neutres", len([s for s in results if s.trend == "NEUTRE"]))
                c4.metric("Ventes", len([s for s in results if "VENTE" in s.trend]))


if __name__ == "__main__":
    main()
