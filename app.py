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
ARSITEKTUR LAYOUT -- FASE 1 REDESIGN (lihat
IMPLEMENTATION_PLAN_UI_REDESIGN_STOCKBIT.md §4.2-4.3 & §9.1 utk alasan
desain lengkap; §1.2 IMPLEMENTATION_PLAN_UI_BACKTEST_LAB.md utk sejarah
kenapa arsitektur lama dulu dipilih):
  - Navigasi SEKARANG memakai st.navigation()/st.Page() NATIVE, posisi di
    atas ("position=top"). Ini API PROGRAMATIK (dipanggil langsung di sini,
    BUKAN folder "pages/" auto-detect) -- jadi TETAP tidak bentrok dgn
    alasan penamaan folder "views/" (bukan "pages/") yg sudah didokumentasikan
    di README & IMPLEMENTATION_PLAN_UI_BACKTEST_LAB.md.
  - Panel "Pengaturan" sekarang st.popover() native, bukan kolom kanan
    custom -- tidak lagi "mencuri" lebar dari konten utama.
  - Isi tiap halaman tetap modul terpisah di folder views/ (TIDAK berubah
    dari arsitektur sebelumnya) -- yang berubah HANYA cara routing ke sana.
  - AppContext (client + settings) tidak bisa dioper langsung sbg argumen
    ke st.Page() (Streamlit memanggil fungsi halaman tanpa argumen), jadi
    tiap page_xxx() di bawah membangun ulang ctx-nya sendiri lewat
    _current_ctx() yang membaca dari st.session_state (diisi sekali di
    main() sebelum st.navigation() dipanggil).
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


# Callback pengaturan khusus per halaman -- HANYA halaman yg didaftarkan di
# sini yg dapat kontrol tambahan di panel Pengaturan (lihat
# ui_layout.render_settings_content). Key HARUS sama persis dgn title
# st.Page() masing-masing di _build_pages().
PAGE_SPECIFIC_SETTINGS = {
    "Screener": screener.render_page_settings,
}


@st.cache_resource(show_spinner=False)
def _get_client():
    return get_client(use_service_role=False)


def _current_ctx() -> AppContext:
    """Dipanggil dari dalam tiap page_xxx() -- st.Page() memanggil fungsi
    halamannya TANPA argumen, jadi ctx dibangun ulang di sini dari
    st.session_state (diisi main() sebelum st.navigation() dipanggil,
    lihat bawah)."""
    return AppContext(
        client=st.session_state["_iqs_client"],
        settings=st.session_state.get("_iqs_settings", {}),
    )


def page_screener() -> None:
    screener.render(_current_ctx())


def page_backtest() -> None:
    backtest.render(_current_ctx())


def page_detail() -> None:
    detail.render(_current_ctx())


def page_portfolio() -> None:
    portfolio.render(_current_ctx())


def page_risk() -> None:
    risk.render(_current_ctx())


def page_about() -> None:
    about.render(_current_ctx())


def _build_pages() -> list[st.Page]:
    """Daftar halaman utk st.navigation() -- title di sini JUGA jadi key di
    PAGE_SPECIFIC_SETTINGS di atas. Urutan = urutan tab yg tampil."""
    return [
        st.Page(page_screener, title="Screener", icon=":material/search:", default=True, url_path="screener"),
        st.Page(page_backtest, title="Backtest Lab", icon=":material/science:", url_path="backtest"),
        st.Page(page_detail, title="Detail Saham", icon=":material/query_stats:", url_path="detail"),
        st.Page(page_portfolio, title="Portfolio", icon=":material/pie_chart:", url_path="portfolio"),
        st.Page(page_risk, title="Risk Calculator", icon=":material/calculate:", url_path="risk"),
        st.Page(page_about, title="Tentang", icon=":material/info:", url_path="about"),
    ]


def main() -> None:
    ui_layout.inject_css()
    ui_layout.render_brand_header()

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

    st.session_state["_iqs_client"] = client

    pg = st.navigation(_build_pages(), position="top")

    last_update = data_loaders.load_last_update(client)
    page_cb = PAGE_SPECIFIC_SETTINGS.get(pg.title)

    _u1, _u2 = st.columns([6, 1])
    with _u1:
        pass  # ruang kosong kiri -- tombol Pengaturan sengaja rata kanan (lihat _u2)
    with _u2:
        with st.popover("Pengaturan", icon=":material/tune:", width="stretch"):
            settings = ui_layout.render_settings_content(last_update, page_cb)
    st.session_state["_iqs_settings"] = settings

    pg.run()


if __name__ == "__main__":
    main()
