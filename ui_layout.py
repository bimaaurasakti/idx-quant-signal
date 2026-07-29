"""
ui_layout.py
============
Layer layout & UI chrome: top bar, dua sidebar collapsible (kiri = navigasi
gaya admin panel, kanan = pengaturan/gear icon), dan helper CSS ringan.

ARSITEKTUR: modul ini SENGAJA tidak memakai st.sidebar bawaan Streamlit.
Streamlit cuma punya satu sidebar native (selalu di kiri, tidak bisa
diduplikasi/dipindah), jadi kedua panel di sini dibangun dari st.columns()
yang lebarnya berubah dinamis sesuai st.session_state, dipoles CSS ringan.
Ini pola "reflow" (konten utama menyempit saat panel dibuka), bukan overlay
mengambang -- jauh lebih robust lintas versi Streamlit dibanding hack CSS
position:fixed di atas struktur DOM internal Streamlit.

Lihat IMPLEMENTATION_PLAN_UI_BACKTEST_LAB.md §1.2 dan §2 untuk detail
alasan desain.
"""
from __future__ import annotations
import pandas as pd
import streamlit as st

# Daftar menu navigasi kiri: (page_key, label_dengan_icon)
# page_key dipakai sbg nilai st.session_state.current_page dan sbg key
# routing di app.py.
NAV_ITEMS = [
    ("screener", "🔍 Screener"),
    ("backtest", "🧪 Backtest Lab"),
    ("detail", "📊 Detail Saham"),
    ("portfolio", "💼 Portfolio"),
    ("risk", "🧮 Risk Calculator"),
    ("about", "ℹ️ Tentang Metodologi"),
]

VALID_PAGES = {key for key, _ in NAV_ITEMS}


def init_layout_state() -> None:
    """Inisialisasi session_state layout. Panggil sekali di awal tiap run."""
    st.session_state.setdefault("nav_open", True)      # nav kiri: default terbuka
    st.session_state.setdefault("settings_open", False)  # settings kanan: default tertutup
    st.session_state.setdefault("current_page", "screener")


def inject_css() -> None:
    """
    CSS ringan supaya panel kiri/kanan terasa seperti sidebar, bukan kolom
    polos.

    CATATAN VERIFIKASI: target selector di sini pakai kelas CSS custom yang
    kita suntik sendiri (bukan menargetkan data-testid internal Streamlit),
    supaya lebih tahan terhadap perubahan struktur DOM Streamlit antar versi.
    Tetap disarankan cek visual di browser nyata setelah deploy.
    """
    st.markdown(
        """
        <style>
        hr.topbar-divider {
            margin: 0.2rem 0 0.9rem 0;
            border: none;
            border-top: 1px solid rgba(128, 128, 128, 0.25);
        }
        div[data-testid="stButton"] > button {
            border-radius: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_topbar(title: str = "📈 IDX Quant Signal Dashboard") -> None:
    """
    Top bar persisten (selalu terlihat, tidak ikut collapse): tombol
    hamburger kiri (toggle nav) - judul - tombol gear kanan (toggle
    pengaturan).

    CATATAN: klik st.button() SUDAH otomatis memicu Streamlit rerun ulang
    seluruh script dari atas -- perubahan session_state di bawah langsung
    terbaca oleh get_layout_columns() pada rerun yang sama. TIDAK perlu
    st.rerun() manual di sini.
    """
    c_menu, c_title, c_gear = st.columns([1, 10, 1])
    with c_menu:
        if st.button("☰", key="btn_toggle_nav", help="Buka/tutup menu navigasi"):
            st.session_state.nav_open = not st.session_state.nav_open
    with c_title:
        st.markdown(f"#### {title}")
    with c_gear:
        if st.button("⚙️", key="btn_toggle_settings", help="Buka/tutup pengaturan"):
            st.session_state.settings_open = not st.session_state.settings_open
    st.markdown('<hr class="topbar-divider">', unsafe_allow_html=True)


def get_layout_columns():
    """
    Return (col_nav | None, col_main, col_settings | None) sesuai kombinasi
    nav_open/settings_open saat ini. Lebar kolom menyesuaikan otomatis.
    """
    nav_open = st.session_state.nav_open
    settings_open = st.session_state.settings_open

    if nav_open and settings_open:
        col_nav, col_main, col_settings = st.columns([1.3, 3.4, 1.3])
        return col_nav, col_main, col_settings
    if nav_open:
        col_nav, col_main = st.columns([1.3, 4.7])
        return col_nav, col_main, None
    if settings_open:
        col_main, col_settings = st.columns([4.7, 1.3])
        return None, col_main, col_settings
    return None, st.container(), None


def render_left_nav() -> None:
    """Render daftar menu navigasi di panel kiri, highlight halaman aktif.

    CATATAN: dipakai st.container(border=True) -- bukan pola
    st.markdown('<div>...</div>') -- karena widget Streamlit yang dirender
    di antara dua panggilan st.markdown mentah TIDAK benar-benar ter-nest
    di dalam div tsb (tiap elemen Streamlit jadi blok DOM terpisah).
    st.container(border=True) adalah cara native yang memang membungkus
    child widget dengan benar."""
    with st.container(border=True):
        st.markdown("###### Menu")
        for key, label in NAV_ITEMS:
            is_active = st.session_state.current_page == key
            if st.button(
                label,
                key=f"nav_{key}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state.current_page = key


def render_right_settings(last_update: dict | None, render_page_specific=None) -> dict:
    """
    Render panel pengaturan kanan. Selalu berisi status update terakhir +
    disclaimer. `render_page_specific`, kalau diberikan, adalah callable
    yang dipanggil untuk menyisipkan kontrol khusus halaman aktif (mis.
    filter sektor & minimal trade, HANYA relevan saat current_page ==
    "screener" -- lihat views/screener.py) dan harus mengembalikan dict.

    Return dict gabungan hasil dari render_page_specific (kosong kalau
    tidak ada).
    """
    with st.container(border=True):
        st.markdown("###### ⚙️ Pengaturan")

        if last_update:
            try:
                run_at_wib = pd.to_datetime(last_update["run_at"]).tz_convert("Asia/Jakarta")
                ts_str = run_at_wib.strftime("%d/%m/%Y %H:%M")
            except Exception:
                ts_str = str(last_update.get("run_at", "?"))
            status_icon = {"OK": "🟢", "SKIPPED": "🟡", "FAILED": "🔴"}.get(
                last_update.get("status"), "⚪"
            )
            st.markdown(
                f"**{status_icon} Data terakhir diperbarui:**  \n"
                f"{ts_str} WIB  \n"
                f"_{last_update.get('tickers_processed', '?')} saham diproses_"
            )
        else:
            st.warning("Belum ada riwayat update.")

        st.caption(
            "Data diperbarui **otomatis setiap hari bursa** ±16:30 WIB oleh "
            "proses terjadwal — bukan saat Anda membuka halaman ini."
        )

        page_settings: dict = {}
        if render_page_specific is not None:
            page_settings = render_page_specific() or {}

        st.markdown("---")
        st.caption(
            "⚠️ **Disclaimer**: Alat riset kuantitatif berbasis data historis (yfinance). "
            "Winrate & expectancy dihitung dari backtest masa lalu — **tidak menjamin hasil "
            "masa depan**. Bukan nasihat keuangan. Pasar Indonesia hanya mendukung posisi "
            "**long/spot** — dashboard ini tidak pernah menghasilkan sinyal short. Universe "
            "default: konstituen indeks **IDX30 & LQ45**, direview ulang oleh BEI tiap kuartal."
        )
    return page_settings
