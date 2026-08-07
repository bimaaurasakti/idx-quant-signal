"""
components.py
==============
Komponen UI reusable, murni presentasional -- dibangun di atas token
theme.py. Semua fungsi MENERIMA data yang sudah dihitung modul lain
(screener_df, price_history, hasil backtest, dst); TIDAK ADA fetch,
kalkulasi bisnis, atau akses Supabase/yfinance di sini.

Fungsi *_html() mengembalikan string HTML (untuk disisipkan ke dalam
markup lain sebelum satu kali st.markdown). Fungsi render_*() langsung
memanggil st.markdown/unsafe_allow_html sendiri (dipakai berdiri sendiri
dalam st.columns()).

Lihat IMPLEMENTATION_PLAN_UI_REDESIGN_STOCKBIT.md §7.
"""
from __future__ import annotations
import html as _html_lib

import streamlit as st

from theme import COLORS, RADIUS, signal_colors, format_idr, format_pct_id


def _esc(value) -> str:
    """Escape teks yang berasal dari data (ticker, sektor, dst) sebelum
    disisipkan ke HTML mentah -- pencegahan dasar terhadap karakter yang
    bisa merusak markup kalau data punya karakter tak terduga."""
    return _html_lib.escape(str(value)) if value is not None else ""


def confirmation_meter_html(filled: int, total: int, direction: str) -> str:
    """Meteran Konfirmasi -- elemen signature dashboard ini (lihat
    IMPLEMENTATION_PLAN §3.4). direction: 'bullish' | 'bearish' | 'neutral'.

    filled/total HARUS berasal dari data yang SUDAH ada, tidak pernah
    dihitung ulang di sini:
      - Screener / Detail Saham (strategi produksi): filled=row['signal_strength'], total=3
      - Backtest Lab (indikator custom): filled=BullishCount/BearishCount pada
        bar trigger, total=len(selected_indicators)
    """
    total = max(int(total), 1)
    filled = max(0, min(int(filled), total))
    fill_color = {
        "bullish": COLORS["bullish"], "bearish": COLORS["bearish"],
    }.get(direction, COLORS["neutral"])
    bars = "".join(
        f'<span class="iqs-meter-bar" style="background:{fill_color if i < filled else COLORS["border_strong"]};"></span>'
        for i in range(total)
    )
    return f'<span title="Konfirmasi {filled} dari {total}">{bars}</span>'


def signal_badge_html(signal: str | None) -> str:
    sc = signal_colors(signal)
    return (
        f'<span class="iqs-badge" style="background:{sc["bg"]};color:{sc["fg"]};">'
        f'{sc["label"]}</span>'
    )


def render_status_card(html_content: str, tone: str = "info") -> None:
    """Kartu status dengan aksen border kiri berwarna -- pengganti
    st.info()/st.success() bawaan Streamlit utk pesan yang perlu terasa
    konsisten dgn design system (bukan kotak biru/hijau default Streamlit
    yang temanya beda sendiri). tone: 'info'|'bullish'|'bearish'|'neutral'.

    html_content adalah HTML MENTAH (bukan markdown ** dkk) -- pemanggil
    bertanggung jawab escape data dinamis sendiri (pakai _esc() di modul
    ini kalau nilainya berasal dari input bebas, BUKAN dari pilihan
    ticker/sektor yang sudah dikontrol lewat selectbox/database)."""
    color = {
        "bullish": COLORS["bullish"], "bearish": COLORS["bearish"], "neutral": COLORS["neutral"],
    }.get(tone, COLORS["info"])
    st.markdown(
        f"""<div style="background:{COLORS['bg_surface']};border:1px solid {COLORS['border']};
border-left:4px solid {color};border-radius:{RADIUS['lg']};padding:12px 16px;
font-size:13.5px;color:{COLORS['text_primary']};">{html_content}</div>""",
        unsafe_allow_html=True,
    )


def render_metric_card(label: str, value: str, tone: str = "neutral", help_text: str | None = None) -> None:
    """Pengganti st.metric() polos -- kartu dengan label di atas, angka
    besar mono di bawah, warna opsional sesuai tone
    ('bullish'/'bearish'/'neutral'). Dipakai persis seperti st.metric di
    dalam st.columns(...)."""
    color = {"bullish": COLORS["bullish"], "bearish": COLORS["bearish"]}.get(tone, COLORS["text_primary"])
    help_icon = (
        f'<span title="{_esc(help_text)}" style="cursor:help;color:{COLORS["text_muted"]};font-size:11px;"> ⓘ</span>'
        if help_text else ""
    )
    st.markdown(
        f"""<div style="background:{COLORS['bg_surface_2']};border-radius:{RADIUS['md']};padding:12px 14px;">
<div style="font-size:12.5px;color:{COLORS['text_secondary']};">{_esc(label)}{help_icon}</div>
<div class="iqs-mono" style="font-size:20px;font-weight:600;color:{color};margin-top:2px;">{_esc(value)}</div>
</div>""",
        unsafe_allow_html=True,
    )


def render_price_header(ticker: str, sektor: str, price: float | None, change: float | None,
                          change_pct: float | None, signal: str | None, filled: int, total: int) -> None:
    """Header 'ala stock profile' untuk halaman Detail Saham -- ticker,
    sektor, harga besar (mono), badge perubahan harian, badge sinyal +
    meteran konfirmasi. change/change_pct diturunkan di views/detail.py
    dari price_history yang SUDAH dimuat (lihat IMPLEMENTATION_PLAN §9.3)
    -- fungsi ini TIDAK menghitung apa pun, murni render."""
    from theme import direction_from_signal
    direction = direction_from_signal(signal)

    chg_html = ""
    if change is not None and change_pct is not None:
        chg_color = COLORS["bullish"] if change >= 0 else COLORS["bearish"]
        chg_bg = COLORS["bullish_bg"] if change >= 0 else COLORS["bearish_bg"]
        chg_html = (
            f'<span class="iqs-badge iqs-mono" style="background:{chg_bg};color:{chg_color};">'
            f'{format_idr(change)} ({format_pct_id(change_pct)})</span>'
        )

    st.markdown(
        f"""<div class="iqs-card" style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">
<div>
<div style="font-size:12.5px;color:{COLORS['text_secondary']};">{_esc(sektor)}</div>
<div class="iqs-mono" style="font-size:22px;font-weight:700;color:{COLORS['text_primary']};">{_esc(ticker)}</div>
<div class="iqs-mono" style="font-size:32px;font-weight:700;color:{COLORS['text_primary']};margin-top:4px;">{format_idr(price)}</div>
<div style="margin-top:4px;">{chg_html}</div>
</div>
<div style="text-align:right;">
<div style="margin-bottom:6px;">{signal_badge_html(signal)}</div>
<div>{confirmation_meter_html(filled, total, direction)}</div>
</div>
</div>""",
        unsafe_allow_html=True,
    )


def render_position_card(ticker: str, sektor: str, entry_price: float | None, return_pct: float | None,
                           tp_price: float | None, sl_price: float | None, entry_date_label: str) -> None:
    """Kartu status posisi OPEN -- dipakai di grid 'Ongoing Position' Screener
    (lihat IMPLEMENTATION_PLAN §9.2). SENGAJA tidak pakai signal_badge_html/
    confirmation_meter_html seperti render_signal_card: posisi yang sudah
    terbuka tidak relevan ditampilkan dengan sinyal/meteran konfirmasi HARI
    INI (signal_strength saat ini bisa berbeda dari saat posisi ini dibuka
    -- akan menyesatkan kalau ditampilkan seolah itu kekuatan sinyal saat
    entry). Kartu ini fokus ke status posisi berjalan: return saat ini, TP,
    SL -- data yang memang relevan untuk posisi yang SUDAH terbuka."""
    ret_color = COLORS["bullish"] if (return_pct or 0) >= 0 else COLORS["bearish"]
    st.markdown(
        f"""<div class="iqs-card" style="padding:12px 14px;">
<div style="display:flex;justify-content:space-between;align-items:flex-start;">
<div>
<div class="iqs-mono" style="font-size:15px;font-weight:600;color:{COLORS['text_primary']};">{_esc(ticker)}</div>
<div style="font-size:11.5px;color:{COLORS['text_muted']};">{_esc(sektor)} &bull; entry {_esc(entry_date_label)}</div>
</div>
<span class="iqs-mono" style="font-size:15px;font-weight:600;color:{ret_color};">{format_pct_id(return_pct)}</span>
</div>
<div style="margin-top:10px;border-top:1px solid {COLORS['border']};padding-top:8px;
            display:flex;justify-content:space-between;font-size:11.5px;color:{COLORS['text_secondary']};">
<span>Entry<br><span class="iqs-mono" style="color:{COLORS['text_primary']};">{format_idr(entry_price)}</span></span>
<span>TP<br><span class="iqs-mono" style="color:{COLORS['bullish']};">{format_idr(tp_price)}</span></span>
<span>SL<br><span class="iqs-mono" style="color:{COLORS['bearish']};">{format_idr(sl_price)}</span></span>
</div>
</div>""",
        unsafe_allow_html=True,
    )
def render_signal_card(ticker: str, sektor: str, signal: str, filled: int, total: int,
                         footer_label: str, footer_value: str) -> None:
    """Kartu sinyal ringkas -- dipakai di grid Screener (section 'Sinyal BUY
    Besok' & 'Ongoing Position'), pengganti st.dataframe polos untuk data
    prioritas tinggi yang jumlah barisnya sedikit (lihat IMPLEMENTATION_PLAN
    §9.2 untuk aturan kapan pakai kartu vs tabel)."""
    from theme import direction_from_signal
    direction = direction_from_signal(signal)
    st.markdown(
        f"""<div class="iqs-card" style="padding:12px 14px;">
<div style="display:flex;justify-content:space-between;align-items:flex-start;">
<div>
<div class="iqs-mono" style="font-size:15px;font-weight:600;color:{COLORS['text_primary']};">{_esc(ticker)}</div>
<div style="font-size:11.5px;color:{COLORS['text_muted']};">{_esc(sektor)}</div>
</div>
{signal_badge_html(signal)}
</div>
<div style="margin-top:8px;">{confirmation_meter_html(filled, total, direction)}</div>
<div style="margin-top:8px;border-top:1px solid {COLORS['border']};padding-top:8px;
            display:flex;justify-content:space-between;">
<span style="font-size:12px;color:{COLORS['text_secondary']};">{_esc(footer_label)}</span>
<span class="iqs-mono" style="font-size:12.5px;color:{COLORS['text_primary']};">{_esc(footer_value)}</span>
</div>
</div>""",
        unsafe_allow_html=True,
    )
