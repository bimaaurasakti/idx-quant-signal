"""
views/portfolio.py
===================
Isi tab "Portfolio" dari app.py versi lama, dipindah apa adanya.
"""
from __future__ import annotations
import pandas as pd
import plotly.express as px
import streamlit as st

import data_loaders
from shared_ui import TOOLTIP, EXIT_REASON_CHART_COLORS, style_exit_reason_row
from tickers_idx import get_sector_of


def _prepare_portfolio_df(df: pd.DataFrame) -> pd.DataFrame:
    """Siapkan closed_positions mentah dari Supabase: parse tanggal, hitung
    hold_days, lookup sektor, kasih label yang enak dibaca."""
    if df.empty:
        return df
    d = df.copy()
    d["entry_date"] = pd.to_datetime(d["entry_date"])
    d["exit_date"] = pd.to_datetime(d["exit_date"])
    d["signal_date"] = pd.to_datetime(d["signal_date"])
    d["hold_days"] = (d["exit_date"] - d["entry_date"]).dt.days
    d["sektor"] = d["ticker"].apply(get_sector_of)

    label_map = {
        "CLOSED_TP": "Take Profit", "CLOSED_SL": "Stop Loss",
        "CLOSED_SIGNAL": "Sinyal SELL", "CLOSED_TIME": "Batas Waktu",
    }
    d["exit_label"] = d["status"].map(label_map).fillna(d["status"])
    d["is_win"] = d["return_pct"] > 0
    return d.sort_values("exit_date", ascending=False)


def _portfolio_metrics(d: pd.DataFrame) -> dict:
    """Formula IDENTIK dengan backtester.py._compute_metrics."""
    n = len(d)
    if n == 0:
        return {"n_closed": 0}
    wins = d[d["return_pct"] > 0]
    losses = d[d["return_pct"] <= 0]
    winrate = len(wins) / n * 100
    avg_win = wins["return_pct"].mean() if not wins.empty else 0.0
    avg_loss = abs(losses["return_pct"].mean()) if not losses.empty else 0.0
    lossrate = 100 - winrate
    expectancy = (winrate / 100 * avg_win) - (lossrate / 100 * avg_loss)
    total_profit = wins["return_pct"].sum() if not wins.empty else 0.0
    total_loss = abs(losses["return_pct"].sum()) if not losses.empty else 0.0
    profit_factor = (total_profit / total_loss) if total_loss > 0 else None
    return {
        "n_closed": n, "winrate": winrate, "expectancy": expectancy,
        "profit_factor": profit_factor, "total_return": d["return_pct"].sum(),
        "avg_hold_days": d["hold_days"].mean(),
    }


def render(ctx) -> None:
    client = ctx.client
    st.markdown("## 💼 Portfolio — Riwayat Posisi Closed")
    st.caption(
        "Beda dengan halaman **Detail Saham → Riwayat Trade** (hasil *backtest* yang "
        "dihitung ULANG dari seluruh histori data setiap worker jalan): data di "
        "sini adalah jejak sinyal **LIVE** — posisi yang benar-benar dibuka & "
        "ditutup hari demi hari, tanpa lookahead, tidak pernah direvisi ke belakang."
    )

    raw_closed = data_loaders.load_closed_positions(client)
    closed_df = _prepare_portfolio_df(raw_closed)

    if closed_df.empty:
        st.info(
            "📭 Belum ada posisi yang closed. Data akan mulai muncul setelah "
            "sebuah posisi live mencapai Take Profit, Stop Loss, sinyal SELL, "
            "atau batas waktu holding (20 hari bursa)."
        )
        return

    fc1, fc2, fc3 = st.columns([1.3, 1.4, 1.3])
    with fc1:
        sektor_opts = sorted(closed_df["sektor"].unique().tolist())
        sektor_pick = st.multiselect(
            "Sektor", options=sektor_opts, default=[], key="portfolio_sektor_filter",
            help="Kosongkan untuk menampilkan semua sektor.",
        )
    with fc2:
        min_d, max_d = closed_df["exit_date"].min(), closed_df["exit_date"].max()
        date_pick = st.date_input(
            "Rentang Tanggal Exit", value=(min_d, max_d),
            min_value=min_d, max_value=max_d, key="portfolio_date_filter",
        )
    with fc3:
        ticker_search = st.text_input(
            "Cari Ticker", placeholder="mis. BBCA", key="portfolio_ticker_search",
        )

    f = closed_df.copy()
    if sektor_pick:
        f = f[f["sektor"].isin(sektor_pick)]
    if isinstance(date_pick, tuple) and len(date_pick) == 2:
        start_d, end_d = pd.Timestamp(date_pick[0]), pd.Timestamp(date_pick[1])
        f = f[(f["exit_date"] >= start_d) & (f["exit_date"] <= end_d)]
    if ticker_search:
        f = f[f["ticker"].str.contains(ticker_search.strip().upper(), regex=False)]

    if f.empty:
        st.warning("Tidak ada posisi closed yang cocok dengan filter di atas.")
        return

    metrics = _portfolio_metrics(f)
    if metrics["n_closed"] < 20:
        st.warning(
            f"⚠️ Sample masih kecil (n={metrics['n_closed']} posisi closed). "
            "Hati-hati menarik kesimpulan statistik dari jumlah trade sekecil ini."
        )

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Total Closed", f"{metrics['n_closed']}")
    m2.metric("Winrate", f"{metrics['winrate']:.1f}%", help=TOOLTIP["winrate"])
    m3.metric("Expectancy", f"{metrics['expectancy']:.2f}%", help=TOOLTIP["expectancy"])
    pf = metrics["profit_factor"]
    pf_disp = f"{pf:.2f}" if pf is not None else "∞"
    m4.metric("Profit Factor", pf_disp, help=TOOLTIP["profit_factor"])
    m5.metric("Total Return (Sum)", f"{metrics['total_return']:.2f}%", help=TOOLTIP["total_return"])
    m6.metric("Avg Hold", f"{metrics['avg_hold_days']:.1f} hari")
    if pf is None:
        st.caption("∞ = belum ada trade rugi sama sekali dalam sample/filter saat ini.")

    st.divider()

    cc1, cc2 = st.columns(2)
    with cc1:
        exit_counts = f["exit_label"].value_counts().reset_index()
        exit_counts.columns = ["Alasan Exit", "Jumlah"]
        fig_exit = px.bar(
            exit_counts, x="Alasan Exit", y="Jumlah", color="Alasan Exit",
            color_discrete_map=EXIT_REASON_CHART_COLORS,
            text="Jumlah", title="Breakdown Alasan Exit",
        )
        fig_exit.update_layout(showlegend=False)
        st.plotly_chart(fig_exit, use_container_width=True)
    with cc2:
        sektor_stats = (
            f.groupby("sektor")
            .agg(Jumlah=("ticker", "count"), AvgReturn=("return_pct", "mean"))
            .reset_index().sort_values("AvgReturn", ascending=False)
        )
        fig_sektor = px.bar(
            sektor_stats, x="sektor", y="AvgReturn", color="AvgReturn",
            color_continuous_scale=["red", "lightgray", "green"],
            title="Rata-rata Return per Sektor (%)",
        )
        st.plotly_chart(fig_sektor, use_container_width=True)

    timeline = f.sort_values("exit_date").copy()
    timeline["cum_return"] = timeline["return_pct"].cumsum()
    fig_cum = px.line(
        timeline, x="exit_date", y="cum_return", markers=True,
        title="Return Kumulatif dari Waktu ke Waktu (Non-Kompound, Sum)",
    )
    st.plotly_chart(fig_cum, use_container_width=True)
    st.caption(
        "Grafik ini adalah **penjumlahan** (bukan compounding) return_pct tiap trade "
        "closed, asumsi ukuran posisi sama rata — bukan equity curve portfolio riil."
    )

    st.divider()
    st.markdown("### 📋 Detail Posisi Closed")
    disp = f.rename(columns={
        "ticker": "Ticker", "sektor": "Sektor",
        "signal_date": "Tanggal Sinyal", "entry_date": "Tanggal Entry",
        "entry_price": "Harga Entry", "exit_date": "Tanggal Exit",
        "exit_price": "Harga Exit", "exit_label": "Alasan Exit",
        "return_pct": "Return (%)", "hold_days": "Lama Hold (hari)",
    })
    cols_show = ["Ticker", "Sektor", "Tanggal Sinyal", "Tanggal Entry",
                 "Harga Entry", "Tanggal Exit", "Harga Exit", "Alasan Exit",
                 "Return (%)", "Lama Hold (hari)"]
    st.caption("🟢 Take Profit  🔴 Stop Loss  🔵 Sinyal SELL  🟡 Batas Waktu")
    st.dataframe(
        disp[cols_show].style
            .apply(style_exit_reason_row, axis=1)
            .format({
                "Harga Entry": "{:,.0f}", "Harga Exit": "{:,.0f}",
                "Return (%)": "{:+.2f}%",
            }, na_rep="-"),
        use_container_width=True, hide_index=True, height=400,
    )

    csv = disp[cols_show].to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download riwayat portfolio sebagai CSV", csv,
        "idx_portfolio_closed_positions.csv", "text/csv",
    )

    with st.expander("📋 Ringkasan untuk Analisis AI (copy teks di bawah)"):
        ai_summary = f"""Ringkasan Portfolio Live — IDX Quant Signal Dashboard
Per tanggal: {pd.Timestamp.now().strftime('%d/%m/%Y')}
Filter aktif: sektor={sektor_pick or 'semua'} — semua alasan exit (TP/SL/SIGNAL/TIME) selalu ditampilkan, tidak difilter

METRIK UTAMA
- Total posisi closed: {metrics['n_closed']}
- Winrate: {metrics['winrate']:.1f}%
- Expectancy: {metrics['expectancy']:.2f}% per trade
- Profit Factor: {pf_disp}
- Total Return (sum, non-kompound): {metrics['total_return']:.2f}%
- Rata-rata lama hold: {metrics['avg_hold_days']:.1f} hari bursa

BREAKDOWN ALASAN EXIT
{exit_counts.to_string(index=False)}

BREAKDOWN PERFORMA PER SEKTOR (rata-rata return %)
{sektor_stats.to_string(index=False)}

Catatan: metrik non-kompound, asumsi ukuran posisi sama rata per trade.
Ini jejak sinyal LIVE (bukan hasil backtest simulasi ulang)."""
        st.code(ai_summary, language=None)
