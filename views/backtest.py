"""
views/backtest.py
==================
Placeholder halaman Backtest Lab. Implementasi penuh (indicator registry,
custom signal engine, animated chart) ada di Fase 2-6 dari
IMPLEMENTATION_PLAN_UI_BACKTEST_LAB.md §3 -- BELUM dikerjakan di putaran
eksekusi ini (yang fokus ke Goal 1 & 2: dual sidebar).

Placeholder ini SENGAJA sudah didaftarkan di ui_layout.NAV_ITEMS dan routing
app.py supaya struktur navigasi final sudah bisa diuji end-to-end sekarang,
tanpa menunggu Backtest Lab selesai dibangun.
"""
from __future__ import annotations
import streamlit as st


def render(ctx) -> None:
    st.markdown("## 🧪 Backtest Lab")
    st.info(
        "🚧 **Segera hadir.** Halaman ini akan memungkinkan Anda memilih kombinasi "
        "indikator sendiri (SMA/EMA Crossover, MACD, ADX, RSI, Stochastic, Bollinger, "
        "Ichimoku, Supertrend, dan lainnya — total ~24 indikator profesional), "
        "menjalankan backtest atas kombinasi tersebut, dan menonton replay animasi "
        "chart harga + indikator + posisi entry/exit.\n\n"
        "Detail teknis lengkap ada di §3 dokumen `IMPLEMENTATION_PLAN_UI_BACKTEST_LAB.md` "
        "(Fase 2–6 dari roadmap implementasi)."
    )
    st.caption(
        "Halaman ini sudah terhubung ke sistem navigasi baru — begitu Fase 2-6 selesai "
        "dikerjakan, konten di sini tinggal diganti tanpa perlu ubah routing di app.py."
    )
