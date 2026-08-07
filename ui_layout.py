"""
ui_layout.py
============
Layer chrome UI: header brand & isi panel Pengaturan (popover). Sejak Fase 1
redesign (lihat IMPLEMENTATION_PLAN_UI_REDESIGN_STOCKBIT.md §4.2-4.3 & §9.1),
modul ini JAUH lebih tipis dari versi sebelumnya.

RIWAYAT ARSITEKTUR (penting utk konteks): versi lama modul ini SENGAJA tidak
memakai st.sidebar/multi-page native karena API Streamlit versi lama tidak
mendukung itu dgn baik (sidebar tunggal, tidak bisa diduplikasi/dipindah) --
makanya dibangun 2 kolom custom (nav kiri + settings kanan) dari st.columns()
+ st.session_state, dipoles CSS manual yg menarget elemen internal Streamlit
(rapuh lintas versi -- risiko yg SUDAH diakui sendiri di versi lama modul
ini).

Streamlit sekarang (>=1.48, lihat requirements.txt) punya st.navigation()
programatik (BUKAN folder "pages/" auto-detect -- jadi tetap tidak bentrok
dgn alasan penamaan folder "views/" yg sudah ada) + st.popover() native.
app.py sekarang yg langsung memanggil keduanya (lihat app.py::main()) --
modul ini tinggal menyediakan 2 potongan konten: header brand & isi popover
Pengaturan. Fungsi routing lama (init_layout_state, get_layout_columns,
render_left_nav, NAV_ITEMS, VALID_PAGES) SUDAH DIHAPUS -- digantikan native
oleh st.navigation()/st.Page() di app.py.
"""
from __future__ import annotations
import pandas as pd
import streamlit as st


def inject_css() -> None:
    """
    CSS global app ini -- dipusatkan lewat theme.get_global_css() (design
    system tunggal, lihat theme.py & IMPLEMENTATION_PLAN_UI_REDESIGN_
    STOCKBIT.md §4.4/§6). ui_layout.py tidak menyimpan CSS literal sendiri
    supaya tidak ada 2 sumber kebenaran warna/style yang bisa drift.

    CATATAN VERIFIKASI (tetap berlaku): selector CSS di theme.py sengaja
    memakai kelas custom (.iqs-*) yang kita suntik sendiri, bukan menargetkan
    data-testid internal Streamlit, supaya lebih tahan terhadap perubahan
    struktur DOM Streamlit antar versi. Tetap disarankan cek visual di
    browser nyata setelah deploy.
    """
    import theme
    st.markdown(theme.get_global_css(), unsafe_allow_html=True)


def render_brand_header(title: str = "IDX Quant Signal") -> None:
    """Baris brand paling atas -- dipanggil SEBELUM st.navigation() di
    app.py::main(), supaya tampil di atas nav. Menggantikan render_topbar()
    versi lama yang punya tombol hamburger/gear manual: toggle nav/settings
    sekarang ditangani native oleh st.navigation()/st.popover(), jadi tidak
    perlu tombol custom lagi di sini.

    Tagline di bawah judul (dulu st.caption() yang dipanggil terpisah di
    app.py sebelum routing) dipindah ke sini supaya konsisten tampil di
    semua halaman apa pun cara navigasinya."""
    import theme
    st.markdown(
        f"""<div style="padding:2px 0 6px;">
<div style="display:flex;align-items:center;gap:8px;">
<span style="font-size:21px;line-height:1;">📈</span>
<span class="iqs-mono" style="font-size:18px;font-weight:700;color:{theme.COLORS['text_primary']};">{title}</span>
</div>
<div style="font-size:12.5px;color:{theme.COLORS['text_secondary']};margin-top:2px;">
Multi-confirmation trend signal system &bull; Universe: IDX30 &amp; LQ45 &bull; Data bersama via Supabase &bull; Sumber harga: yfinance
</div>
</div>""",
        unsafe_allow_html=True,
    )


def render_settings_content(last_update: dict | None, render_page_specific=None) -> dict:
    """
    Isi panel Pengaturan -- dipanggil dari DALAM `with st.popover(...):` di
    app.py::main() (lihat IMPLEMENTATION_PLAN §4.3). Logika & isi konten
    IDENTIK dengan render_right_settings() versi lama (status update
    terakhir, kontrol khusus halaman aktif, disclaimer) -- HANYA pembungkus
    st.container(border=True) yang dihapus, karena st.popover() sendiri
    sudah jadi wadah kontainer; container bersarang di dalamnya jadi kotak
    di dalam kotak yang redundan.

    `render_page_specific`, kalau diberikan, adalah callable yang dipanggil
    untuk menyisipkan kontrol khusus halaman aktif (mis. filter sektor &
    minimal trade, HANYA relevan saat halaman aktif == Screener -- lihat
    views/screener.py) dan harus mengembalikan dict.

    Return dict gabungan hasil dari render_page_specific (kosong kalau
    tidak ada).
    """
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
