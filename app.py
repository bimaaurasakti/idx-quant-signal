"""
IDX Quant Signal Dashboard — PUBLIC EDITION
=============================================
Dashboard publik, READ-ONLY. Semua data (sinyal, backtest, ongoing position)
sudah dihitung sebelumnya oleh worker_fetch_and_update.py (GitHub Actions,
terjadwal tiap akhir sesi bursa IDX) dan disimpan di Supabase. Dashboard ini
TIDAK melakukan fetch yfinance sendiri.

Jalankan dengan:
    streamlit run app.py

Butuh secrets (lihat .streamlit/secrets.toml.example / README.md):
    SUPABASE_URL, SUPABASE_ANON_KEY

PENTING: Ini adalah alat riset kuantitatif, BUKAN nasihat keuangan.

--------------------------------------------------------------------------
ARSITEKTUR LAYOUT (lihat IMPLEMENTATION_PLAN_UI_BACKTEST_LAB.md §2 utk
alasan desain lengkap):
  - app.py ini SEKARANG orkestrator tipis: init state layout, top bar,
    kolom dinamis (nav kiri + settings kanan, keduanya collapsible), lalu
    routing ke modul views/*.py sesuai halaman aktif.
  - st.sidebar bawaan Streamlit TIDAK dipakai sama sekali -- diganti
    ui_layout.py yang membangun 2 panel independen dari st.columns() +
    st.session_state (lihat ui_layout.py).
  - Isi tiap halaman (dulu st.tabs()) sekarang berupa modul terpisah di
    folder views/ (SENGAJA bukan "pages/" -- Streamlit auto-detect nama
    folder itu sbg multi-page-app native & akan bentrok dgn nav custom kita).
--------------------------------------------------------------------------
"""
from __future__ import annotations
import warnings
warnings.filterwarnings("ignore")

from dataclasses import dataclass, field
from typing import Any

import streamlit as st

import ui_layout
import data_loaders
from supabase_client import get_client
from views import screener, backtest, detail, portfolio, risk, about

st.set_page_config(page_title="IDX Quant Signal Dashboard", page_icon="📈", layout="wide")


@dataclass
class AppContext:
    """Bundel resource bersama yg dioper ke tiap view.render(ctx) -- dipakai
    supaya view module tidak perlu import balik dari app.py (hindari
    circular import)."""
    client: Any
    settings: dict = field(default_factory=dict)


ROUTES = {
    "screener": screener.render,
    "backtest": backtest.render,
    "detail": detail.render,
    "portfolio": portfolio.render,
    "risk": risk.render,
    "about": about.render,
}

# Callback pengaturan khusus per halaman -- HANYA halaman yg didaftarkan di
# sini yg dapat kontrol tambahan di panel kanan (lihat ui_layout.render_right_settings).
PAGE_SPECIFIC_SETTINGS = {
    "screener": screener.render_page_settings,
}


@st.cache_resource(show_spinner=False)
def _get_client():
    return get_client(use_service_role=False)


def main() -> None:
    ui_layout.init_layout_state()
    ui_layout.inject_css()
    ui_layout.render_topbar()

    try:
        client = _get_client()
    except Exception as e:
        st.error(
            "⚠️ **Koneksi ke Supabase belum berhasil.**\n\n"
            f"Detail: `{e}`\n\n"
            "Pastikan `SUPABASE_URL` dan `SUPABASE_ANON_KEY` sudah diset di "
            "`.streamlit/secrets.toml` (lokal) atau di Settings → Secrets "
            "(Streamlit Community Cloud). Lihat **README.md → Setup Supabase**."
        )
        st.stop()
        return

    last_update = data_loaders.load_last_update(client)

    col_nav, col_main, col_settings = ui_layout.get_layout_columns()

    settings: dict = {}
    if col_settings is not None:
        with col_settings:
            page_cb = PAGE_SPECIFIC_SETTINGS.get(st.session_state.current_page)
            settings = ui_layout.render_right_settings(last_update, page_cb)

    if col_nav is not None:
        with col_nav:
            ui_layout.render_left_nav()

    ctx = AppContext(client=client, settings=settings)

    with col_main:
        st.caption(
            "Multi-confirmation trend signal system • Universe: IDX30 & LQ45 • "
            "Data bersama via Supabase • Sumber harga: yfinance"
        )
        current_page = st.session_state.current_page
        if current_page not in ui_layout.VALID_PAGES:
            current_page = st.session_state.current_page = "screener"
        ROUTES[current_page](ctx)


if __name__ == "__main__":
    main()
