"""
views/screener.py
==================
Isi tab "Screener" dari app.py versi lama, dipindah apa adanya. Filter
sektor & minimal-trade sebelumnya widget langsung di st.sidebar; sekarang
datang dari panel Pengaturan kanan (lihat render_page_settings() di bawah,
dipanggil oleh ui_layout.render_right_settings() HANYA saat halaman aktif
adalah "screener" -- lihat app.py & IMPLEMENTATION_PLAN §2.3).

TIDAK ADA perubahan logika filter/ranking dari versi sebelumnya.
"""
from __future__ import annotations
import pandas as pd
import streamlit as st

import data_loaders
from tickers_idx import IDX_TICKERS


def render_page_settings() -> dict:
    """Dipanggil dari panel kanan (ui_layout) saat current_page=='screener'.
    Return dict {"sector_filter": [...], "min_trades_filter": int}."""
    sector_filter = st.multiselect(
        "Filter sektor", options=list(IDX_TICKERS.keys()), default=[],
        help="Kosongkan untuk menampilkan semua sektor.",
    )
    min_trades_filter = st.slider(
        "Minimal jumlah trade historis (filter reliabilitas)", 3, 30, 8,
        help="Saham dengan trade historis terlalu sedikit statistiknya tidak reliabel — sembunyikan dari screener.",
    )
    return {"sector_filter": sector_filter, "min_trades_filter": min_trades_filter}


def render(ctx) -> None:
    client = ctx.client
    sector_filter = ctx.settings.get("sector_filter", [])
    min_trades_filter = ctx.settings.get("min_trades_filter", 8)

    screener_df = data_loaders.load_screener(client)

    if screener_df.empty:
        st.warning(
            "Belum ada data di database. Worker mungkin belum pernah dijalankan. "
            "Trigger manual lewat tab **Actions** di GitHub repo → workflow "
            "\"Update Sinyal IDX Setelah Tutup Bursa\" → **Run workflow**."
        )
        return

    if sector_filter:
        allowed = set()
        for s in sector_filter:
            allowed.update(IDX_TICKERS[s])
        screener_df = screener_df[screener_df["ticker"].isin(allowed)]

    # ================= PRIORITAS 1: Sinyal BUY Besok =================
    pending = data_loaders.load_positions(client, ("PENDING_ENTRY",))
    if not pending.empty:
        pending = pending.merge(
            screener_df[["ticker", "sektor", "winrate", "expectancy_pct", "profit_factor", "last_close"]],
            on="ticker", how="left",
        )
        pending["planned_entry_date"] = pd.to_datetime(pending["planned_entry_date"])
        main_date = pending["planned_entry_date"].mode()[0]
        st.markdown(f"## 🎯 Sinyal BUY Besok ({main_date.strftime('%d/%m/%Y')})")
        st.caption(
            "Sinyal baru muncul pada penutupan sesi terakhir. Rencana entry di harga "
            "**Open** pada tanggal bursa berikutnya (lihat kolom Tanggal Entry — bisa "
            "berbeda antar saham bila ada gangguan data)."
        )
        disp = pending.copy()
        disp["Tanggal Entry"] = disp["planned_entry_date"].dt.strftime("%d/%m/%Y")
        disp = disp.rename(columns={
            "ticker": "Ticker", "sektor": "Sektor", "last_close": "Harga Terakhir",
            "winrate": "Winrate (%)", "expectancy_pct": "Expectancy (%)",
            "profit_factor": "Profit Factor",
        })
        cols_show = ["Ticker", "Sektor", "Tanggal Entry", "Harga Terakhir",
                     "Winrate (%)", "Expectancy (%)", "Profit Factor"]
        st.dataframe(
            disp[cols_show].sort_values("Expectancy (%)", ascending=False),
            use_container_width=True, hide_index=True,
        )
    else:
        st.markdown("## 🎯 Sinyal BUY Besok")
        st.info("Tidak ada sinyal BUY baru untuk sesi bursa berikutnya saat ini.")

    st.divider()

    # ================= PRIORITAS 2: Ongoing Position =================
    st.markdown("## 📌 Ongoing Position")
    open_pos = data_loaders.load_positions(client, ("OPEN",))
    if not open_pos.empty:
        open_pos = open_pos.merge(
            screener_df[["ticker", "sektor", "last_close", "last_date"]],
            on="ticker", how="left",
        )
        open_pos["entry_date"] = pd.to_datetime(open_pos["entry_date"])
        open_pos["last_date"] = pd.to_datetime(open_pos["last_date"])
        open_pos["Return Saat Ini (%)"] = (
            (open_pos["last_close"] - open_pos["entry_price"]) / open_pos["entry_price"] * 100
        ).round(2)
        open_pos["Hari ke-"] = (open_pos["last_date"] - open_pos["entry_date"]).dt.days
        open_pos["Tanggal Entry"] = open_pos["entry_date"].dt.strftime("%d/%m/%Y")
        disp2 = open_pos.rename(columns={
            "ticker": "Ticker", "sektor": "Sektor", "entry_price": "Harga Entry",
            "tp_price": "Take Profit", "sl_price": "Stop Loss", "last_close": "Harga Terakhir",
        })
        cols_show2 = ["Ticker", "Sektor", "Tanggal Entry", "Harga Entry", "Harga Terakhir",
                      "Take Profit", "Stop Loss", "Return Saat Ini (%)", "Hari ke-"]
        st.dataframe(
            disp2[cols_show2].sort_values("Return Saat Ini (%)", ascending=False),
            use_container_width=True, hide_index=True,
        )
        st.caption(
            "Posisi otomatis hilang dari tabel ini begitu kena Take Profit atau Stop Loss "
            "— riwayatnya tetap tersimpan dan bisa dilihat di tab **Detail Saham → Riwayat Trade**."
        )
    else:
        st.info("Tidak ada posisi yang sedang berjalan (open) saat ini.")

    st.divider()

    # ================= PRIORITAS 3: Ranking lengkap =================
    st.markdown("## 🏆 Ranking Semua Saham (berdasarkan Expectancy)")
    st.caption(
        "Expectancy = (winrate × rata-rata profit) − (lossrate × rata-rata loss) — metrik "
        "yang lebih jujur dibanding winrate mentah, karena winrate tinggi bisa tetap rugi "
        "kalau rata-rata loss jauh lebih besar dari rata-rata profit."
    )
    filtered = screener_df[screener_df["n_trades"].fillna(0) >= min_trades_filter].copy()
    ranked = filtered.sort_values("expectancy_pct", ascending=False)
    ranked["idx30_badge"] = (
        ranked["is_idx30"].map({True: "🏅 IDX30", False: ""}).fillna("")
        if "is_idx30" in ranked.columns else ""
    )
    display_cols = {
        "ticker": "Ticker", "idx30_badge": "Indeks", "sektor": "Sektor",
        "last_close": "Harga Terakhir",
        "signal_today": "Sinyal Terkini", "trend": "Trend", "rsi": "RSI(14)",
        "winrate": "Winrate (%)", "expectancy_pct": "Expectancy (%)",
        "profit_factor": "Profit Factor", "max_drawdown_pct": "Max Drawdown (%)",
        "n_trades": "Jml Trade Historis", "sharpe_rough": "Sharpe (kasar)",
    }
    ranked_disp = ranked.rename(columns=display_cols)[list(display_cols.values())]
    st.dataframe(
        ranked_disp.style.format({
            "Harga Terakhir": "{:,.0f}", "RSI(14)": "{:.1f}",
            "Winrate (%)": "{:.1f}%", "Expectancy (%)": "{:.2f}%",
            "Max Drawdown (%)": "{:.2f}%", "Sharpe (kasar)": "{:.2f}",
        }, na_rep="-"),
        use_container_width=True, height=450,
    )

    csv = ranked_disp.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download hasil sebagai CSV", csv, "idx_screener_result.csv", "text/csv")
