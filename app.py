"""
IDX Quant Signal Dashboard
===========================
Dashboard sinyal trading kuantitatif untuk saham Indonesia (IDX), berbasis
data yfinance. Menampilkan sinyal multi-konfirmasi + backtest historis
transparan (winrate, expectancy, profit factor, max drawdown) — bukan klaim,
tapi angka yang benar-benar dihitung dari data historis tiap saham.

Jalankan dengan:
    streamlit run app.py

PENTING: Ini adalah alat riset kuantitatif, BUKAN nasihat keuangan.
Semua keputusan trading adalah tanggung jawab Anda sendiri.
"""
from __future__ import annotations
import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from tickers_idx import IDX_TICKERS, get_all_tickers, get_sector_of
from data_fetcher import fetch_history, fetch_many
from signals import generate_signals, latest_signal_summary
from backtester import backtest_signals

st.set_page_config(
    page_title="IDX Quant Signal Dashboard",
    page_icon="📈",
    layout="wide",
)

# ----------------------------------------------------------------------
# Sidebar — konfigurasi global
# ----------------------------------------------------------------------
st.sidebar.title("⚙️ Pengaturan")

period = st.sidebar.selectbox(
    "Periode data historis", ["1y", "2y", "5y"], index=1,
    help="Semakin panjang periode, semakin banyak data untuk backtest — tapi fetch lebih lama.",
)
min_trades_filter = st.sidebar.slider(
    "Minimal jumlah trade historis (filter reliabilitas)", 3, 30, 8,
    help="Saham dengan trade historis terlalu sedikit statistiknya tidak reliabel — sembunyikan dari screener.",
)
sector_filter = st.sidebar.multiselect(
    "Filter sektor", options=list(IDX_TICKERS.keys()), default=[],
    help="Kosongkan untuk menampilkan semua sektor.",
)
use_cache = st.sidebar.checkbox("Gunakan cache lokal (lebih cepat)", value=True)

st.sidebar.markdown("---")
st.sidebar.caption(
    "⚠️ **Disclaimer**: Dashboard ini adalah alat riset kuantitatif berbasis "
    "data historis (yfinance). Winrate & expectancy dihitung dari backtest "
    "masa lalu — **tidak menjamin hasil masa depan**. Bukan nasihat keuangan. "
    "Selalu lakukan riset & risk management sendiri."
)

# ----------------------------------------------------------------------
# Data loading (cached in Streamlit session)
# ----------------------------------------------------------------------
@st.cache_data(show_spinner=False, ttl=3600)
def load_and_analyze(tickers: tuple[str, ...], period: str, use_cache: bool):
    rows = []
    detail_store = {}
    progress = st.progress(0.0, text="Mengambil & menganalisis data...")
    total = len(tickers)
    for i, ticker in enumerate(tickers, start=1):
        raw = fetch_history(ticker, period=period, use_cache=use_cache)
        if raw is None or raw.empty:
            progress.progress(i / total, text=f"({i}/{total}) {ticker} — tidak ada data")
            continue
        d = generate_signals(raw)
        summary = latest_signal_summary(d)
        bt = backtest_signals(d)

        ticker_clean = ticker.replace(".JK", "")
        rows.append({
            "Ticker": ticker_clean,
            "Sektor": get_sector_of(ticker_clean),
            "Harga Terakhir": summary["last_close"],
            "Sinyal Terkini": summary["signal"],
            "Kekuatan Sinyal": summary["strength"],
            "Trend": summary["trend"],
            "RSI(14)": summary["rsi"],
            "Winrate (%)": bt["winrate"],
            "Expectancy (%)": bt["expectancy_pct"],
            "Profit Factor": bt["profit_factor"],
            "Max Drawdown (%)": bt["max_drawdown_pct"],
            "Jml Trade Historis": bt["n_trades"],
            "Sharpe (kasar)": bt["sharpe_rough"],
        })
        detail_store[ticker_clean] = {"df": d, "backtest": bt}
        progress.progress(i / total, text=f"({i}/{total}) {ticker} selesai")

    progress.empty()
    return pd.DataFrame(rows), detail_store


# ----------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------
st.title("📈 IDX Quant Signal Dashboard")
st.caption(
    "Multi-confirmation trend signal system • Backtest transparan • Data via yfinance"
)

tab_screener, tab_detail, tab_risk, tab_about = st.tabs(
    ["🔍 Screener", "📊 Detail Saham", "🧮 Risk Calculator", "ℹ️ Tentang Metodologi"]
)

# ----------------------------------------------------------------------
# TAB 1: Screener
# ----------------------------------------------------------------------
with tab_screener:
    st.subheader("Screener Sinyal — Semua Saham IDX")

    all_tickers = get_all_tickers(with_suffix=True)
    if sector_filter:
        allowed = set()
        for s in sector_filter:
            allowed.update(IDX_TICKERS[s])
        all_tickers = [t for t in all_tickers if t.replace(".JK", "") in allowed]

    st.caption(f"Menganalisis **{len(all_tickers)} saham**. Klik tombol di bawah untuk mulai (bisa memakan waktu beberapa menit untuk saham dalam jumlah besar, terutama saat pertama kali / cache kosong).")

    if st.button("🚀 Jalankan Analisis", type="primary"):
        result_df, detail_store = load_and_analyze(tuple(all_tickers), period, use_cache)
        st.session_state["result_df"] = result_df
        st.session_state["detail_store"] = detail_store

    if "result_df" in st.session_state:
        result_df = st.session_state["result_df"]
        filtered = result_df[result_df["Jml Trade Historis"] >= min_trades_filter].copy()

        st.markdown("### 🏆 Ranking berdasarkan Expectancy (kualitas sinyal, bukan sekadar winrate)")
        st.caption(
            "Expectancy = (winrate × rata-rata profit) − (lossrate × rata-rata loss). "
            "Ini metrik yang lebih jujur dibanding winrate mentah, karena winrate tinggi bisa "
            "tetap rugi kalau rata-rata loss jauh lebih besar dari rata-rata profit."
        )
        ranked = filtered.sort_values("Expectancy (%)", ascending=False)
        st.dataframe(
            ranked.style.format({
                "Harga Terakhir": "{:,.0f}",
                "RSI(14)": "{:.1f}",
                "Winrate (%)": "{:.1f}%",
                "Expectancy (%)": "{:.2f}%",
                "Max Drawdown (%)": "{:.2f}%",
                "Sharpe (kasar)": "{:.2f}",
            }, na_rep="-"),
            use_container_width=True,
            height=450,
        )

        st.markdown("### 🎯 Sinyal BUY Aktif Saat Ini")
        active_buys = filtered[filtered["Sinyal Terkini"] == "BUY"].sort_values(
            "Expectancy (%)", ascending=False
        )
        if active_buys.empty:
            st.info("Tidak ada sinyal BUY aktif dalam beberapa hari terakhir untuk saham yang lolos filter.")
        else:
            st.dataframe(active_buys, use_container_width=True)

        csv = ranked.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download hasil sebagai CSV", csv, "idx_screener_result.csv", "text/csv")
    else:
        st.info("Klik **Jalankan Analisis** untuk memulai screening.")

# ----------------------------------------------------------------------
# TAB 2: Detail Saham
# ----------------------------------------------------------------------
with tab_detail:
    st.subheader("Analisis Mendalam per Saham")

    if "detail_store" not in st.session_state:
        st.warning("Jalankan analisis di tab Screener terlebih dahulu.")
    else:
        detail_store = st.session_state["detail_store"]
        ticker_choice = st.selectbox("Pilih saham", sorted(detail_store.keys()))

        if ticker_choice:
            d = detail_store[ticker_choice]["df"]
            bt = detail_store[ticker_choice]["backtest"]

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Winrate Historis", f"{bt['winrate']}%" if bt["winrate"] is not None else "N/A")
            col2.metric("Expectancy", f"{bt['expectancy_pct']}%" if bt["expectancy_pct"] is not None else "N/A")
            col3.metric("Profit Factor", f"{bt['profit_factor']}" if bt["profit_factor"] is not None else "N/A")
            col4.metric("Max Drawdown", f"{bt['max_drawdown_pct']}%" if bt["max_drawdown_pct"] is not None else "N/A")

            # Candlestick + indicators chart
            fig = make_subplots(
                rows=3, cols=1, shared_xaxes=True,
                row_heights=[0.55, 0.20, 0.25], vertical_spacing=0.03,
                subplot_titles=("Harga & Sinyal", "RSI(14)", "MACD"),
            )
            fig.add_trace(go.Candlestick(
                x=d.index, open=d["Open"], high=d["High"], low=d["Low"], close=d["Close"],
                name="Harga",
            ), row=1, col=1)
            fig.add_trace(go.Scatter(x=d.index, y=d["SMA50"], line=dict(width=1), name="SMA50"), row=1, col=1)
            fig.add_trace(go.Scatter(x=d.index, y=d["SMA200"], line=dict(width=1), name="SMA200"), row=1, col=1)

            buys = d[d["Signal"] == 1]
            sells = d[d["Signal"] == -1]
            fig.add_trace(go.Scatter(
                x=buys.index, y=buys["Low"] * 0.98, mode="markers",
                marker=dict(symbol="triangle-up", size=10, color="green"), name="BUY",
            ), row=1, col=1)
            fig.add_trace(go.Scatter(
                x=sells.index, y=sells["High"] * 1.02, mode="markers",
                marker=dict(symbol="triangle-down", size=10, color="red"), name="SELL",
            ), row=1, col=1)

            fig.add_trace(go.Scatter(x=d.index, y=d["RSI14"], name="RSI14", line=dict(color="purple")), row=2, col=1)
            fig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dot", line_color="green", row=2, col=1)

            fig.add_trace(go.Bar(x=d.index, y=d["MACD_Hist"], name="MACD Hist"), row=3, col=1)
            fig.add_trace(go.Scatter(x=d.index, y=d["MACD"], name="MACD", line=dict(color="blue")), row=3, col=1)
            fig.add_trace(go.Scatter(x=d.index, y=d["MACD_Signal"], name="Signal", line=dict(color="orange")), row=3, col=1)

            fig.update_layout(height=800, xaxis_rangeslider_visible=False, hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("#### 📋 Riwayat Trade dari Backtest")
            if bt["trades"]:
                trades_df = pd.DataFrame(bt["trades"])
                st.dataframe(trades_df, use_container_width=True)
            else:
                st.info("Belum ada trade historis yang tercatat untuk saham ini pada periode data yang dipilih.")

# ----------------------------------------------------------------------
# TAB 3: Risk Calculator
# ----------------------------------------------------------------------
with tab_risk:
    st.subheader("🧮 Kalkulator Position Sizing & Risk Management")
    st.caption(
        "Sinyal bagus tidak ada gunanya tanpa position sizing yang benar. "
        "Hedge fund sungguhan selalu menentukan ukuran posisi berdasarkan risiko, bukan 'feeling'."
    )

    c1, c2 = st.columns(2)
    with c1:
        capital = st.number_input("Modal total (Rp)", min_value=1_000_000, value=50_000_000, step=1_000_000)
        risk_pct = st.slider("Risiko per trade (% dari modal)", 0.5, 5.0, 1.0, step=0.5)
        entry_price = st.number_input("Harga entry (Rp)", min_value=1.0, value=5000.0, step=50.0)
    with c2:
        atr_value = st.number_input("ATR(14) saham ini (Rp)", min_value=1.0, value=100.0, step=10.0)
        sl_mult = st.slider("Stop loss = X × ATR", 0.5, 3.0, 1.0, step=0.5)
        tp_mult = st.slider("Take profit = X × ATR", 1.0, 5.0, 2.0, step=0.5)

    risk_rupiah = capital * (risk_pct / 100)
    sl_price = entry_price - (sl_mult * atr_value)
    tp_price = entry_price + (tp_mult * atr_value)
    risk_per_share = entry_price - sl_price
    shares = int(risk_rupiah / risk_per_share) if risk_per_share > 0 else 0
    shares = (shares // 100) * 100  # bulatkan ke lot (100 lembar)
    position_value = shares * entry_price
    reward_risk_ratio = (tp_price - entry_price) / risk_per_share if risk_per_share > 0 else 0

    st.markdown("### Hasil Perhitungan")
    r1, r2, r3 = st.columns(3)
    r1.metric("Jumlah Saham (dibulatkan ke lot)", f"{shares:,}")
    r2.metric("Nilai Posisi", f"Rp {position_value:,.0f}")
    r3.metric("Risk : Reward Ratio", f"1 : {reward_risk_ratio:.2f}")

    r4, r5, r6 = st.columns(3)
    r4.metric("Stop Loss", f"Rp {sl_price:,.0f}")
    r5.metric("Take Profit", f"Rp {tp_price:,.0f}")
    r6.metric("Max Risiko (Rp)", f"Rp {risk_rupiah:,.0f}")

    if position_value > capital:
        st.error(
            "⚠️ Nilai posisi melebihi modal Anda! Stop loss terlalu ketat relatif ke ATR, "
            "atau risk % per trade terlalu besar untuk modal ini. Perbesar jarak SL atau kurangi risk %."
        )

# ----------------------------------------------------------------------
# TAB 4: Tentang Metodologi
# ----------------------------------------------------------------------
with tab_about:
    st.subheader("ℹ️ Metodologi & Batasan Jujur")
    st.markdown("""
### Bagaimana sinyal dihasilkan?

Sistem ini memakai **multi-confirmation signal**: sinyal BUY/SELL hanya
muncul kalau minimal 2 dari 3 kondisi berikut searah:

1. **Trend** — harga di atas SMA50, dan SMA50 di atas SMA200 (uptrend struktural)
2. **Momentum** — MACD baru cross naik, dan RSI berada di zona sehat (40–70, bukan overbought)
3. **Volume** — volume hari sinyal minimal 20% di atas rata-rata 20 hari (konfirmasi partisipasi pasar)

Pendekatan ini mengurangi false signal dibanding indikator tunggal, dengan
trade-off sinyal lebih jarang muncul.

### Bagaimana backtest dihitung?

- Entry di **hari setelah** sinyal muncul (bukan di harga penutupan hari sinyal itu sendiri) — menghindari lookahead bias.
- Exit di salah satu dari: take profit (2× ATR), stop loss (1× ATR), sinyal SELL, atau batas waktu 20 hari.
- Semua trade historis dicatat, lalu dihitung winrate, expectancy, profit factor, dan max drawdown per saham.

### Kenapa ini BUKAN "kelas Renaissance Technologies"

Untuk jujur soal ekspektasi:

- **Data**: yfinance = data harian/delayed dari Yahoo Finance. RenTech pakai data tick-by-tick,
  order book, dan data alternatif eksklusif selama puluhan tahun.
- **Eksekusi**: dashboard ini tidak terhubung ke broker — sinyal harus dieksekusi manual,
  dengan slippage dan delay yang tidak terhindarkan.
- **Riset**: strategi di sini adalah trend-following klasik yang sudah dikenal luas (crowded
  strategy). Alpha yang tersisa dari strategi semacam ini jauh lebih kecil dibanding strategi
  proprietary yang belum diketahui pasar.
- **Skala**: sistem ini cocok untuk trading personal skala kecil-menengah di saham likuid,
  bukan untuk mengelola miliaran dolar dengan risk-adjusted return luar biasa.

Yang dashboard ini **bisa** berikan: kerangka kerja disiplin, berbasis data, dengan
risk management eksplisit dan metrik yang jujur — jauh lebih baik daripada trading
berdasarkan feeling atau rumor, tapi tetap bukan "mesin uang" ala hedge fund kuantitatif kelas dunia.

### Keterbatasan data yfinance untuk saham Indonesia

- Beberapa saham IDX punya data kosong/tidak lengkap di Yahoo Finance (terutama saham dengan
  likuiditas rendah).
- Data fundamental (`ticker.info`) untuk saham IDX seringkali tidak selengkap saham AS.
- Selalu cross-check sinyal dengan sumber data lain sebelum eksekusi nyata.
    """)
