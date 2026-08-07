"""
theme.py
========
Design system tunggal ("single source of truth") untuk redesign UI IDX
Quant Signal Dashboard -- token warna, tipografi, spacing, CSS global, dan
tema Plotly. TIDAK ada dependency baru: murni Python + CSS string, di atas
Streamlit native (config.toml + st.markdown unsafe_allow_html).

Warna semantik (bullish/bearish/neutral/info) SENGAJA memperluas, bukan
mengganti, palet yang sudah dipakai shared_ui.EXIT_REASON_CHART_COLORS --
supaya makna warna konsisten di seluruh app (chart exit-reason lama & UI
baru sama-sama merujuk sumber yang sama, lihat shared_ui.py).

TIDAK ADA logika bisnis/data di sini -- murni presentasional.

Lihat IMPLEMENTATION_PLAN_UI_REDESIGN_STOCKBIT.md §3 & §6 untuk rationale.
"""
from __future__ import annotations

COLORS = {
    "bg_base": "#0B0F17",
    "bg_surface": "#121826",
    "bg_surface_2": "#182131",
    "border": "#232B3D",
    "border_strong": "#2E3850",

    "text_primary": "#F1F5F9",
    "text_secondary": "#94A3B8",
    "text_muted": "#64748B",

    "brand": "#6366F1",
    "brand_hover": "#4F46E5",

    "bullish": "#22C55E",
    "bullish_bg": "rgba(34,197,94,0.14)",
    "bearish": "#EF4444",
    "bearish_bg": "rgba(239,68,68,0.14)",
    "neutral": "#EAB308",
    "neutral_bg": "rgba(234,179,8,0.14)",
    "info": "#3B82F6",
    "info_bg": "rgba(59,130,246,0.14)",
}

FONT_SANS = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
FONT_MONO = "'JetBrains Mono', ui-monospace, 'SFMono-Regular', Menlo, Consolas, monospace"

RADIUS = {"sm": "6px", "md": "10px", "lg": "14px", "pill": "999px"}
SPACING = {"xs": "4px", "sm": "8px", "md": "16px", "lg": "24px", "xl": "32px"}


def signal_colors(signal: str | None) -> dict:
    """Map 'BUY'/'SELL'/'HOLD' (atau None/'NO_DATA'/lainnya) ke token warna
    semantik + label tampilan. Dipusatkan di sini supaya components.py &
    views/*.py tidak masing-masing menulis if/elif warna sendiri-sendiri
    (sumber drift kalau tidak dipusatkan)."""
    s = (signal or "").upper()
    if s == "BUY":
        return {"fg": COLORS["bullish"], "bg": COLORS["bullish_bg"], "label": "Buy"}
    if s == "SELL":
        return {"fg": COLORS["bearish"], "bg": COLORS["bearish_bg"], "label": "Sell"}
    if s == "HOLD":
        return {"fg": COLORS["neutral"], "bg": COLORS["neutral_bg"], "label": "Hold"}
    return {"fg": COLORS["text_muted"], "bg": "rgba(148,163,184,0.12)", "label": "–"}


def direction_from_signal(signal: str | None) -> str:
    """'BUY' -> 'bullish', 'SELL' -> 'bearish', selain itu -> 'neutral'.
    Dipakai buat mewarnai Meteran Konfirmasi (lihat components.py)."""
    s = (signal or "").upper()
    if s == "BUY":
        return "bullish"
    if s == "SELL":
        return "bearish"
    return "neutral"


def get_global_css() -> str:
    """CSS global tunggal -- dipanggil SEKALI dari ui_layout.inject_css().
    Berisi HANYA hal yang tidak bisa diatur lewat .streamlit/config.toml:
    utility class untuk komponen custom (.iqs-*), dan sedikit polish pada
    elemen native Streamlit yang stabil ditarget (radius tombol) -- BUKAN
    data-testid internal yang rapuh lintas versi Streamlit (lihat
    IMPLEMENTATION_PLAN §4.4)."""
    c = COLORS
    return f"""<style>
:root {{
    --iqs-bg-base: {c['bg_base']};
    --iqs-bg-surface: {c['bg_surface']};
    --iqs-bg-surface-2: {c['bg_surface_2']};
    --iqs-border: {c['border']};
    --iqs-border-strong: {c['border_strong']};
    --iqs-text-primary: {c['text_primary']};
    --iqs-text-secondary: {c['text_secondary']};
    --iqs-text-muted: {c['text_muted']};
    --iqs-brand: {c['brand']};
    --iqs-font-sans: {FONT_SANS};
    --iqs-font-mono: {FONT_MONO};
}}

@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');

.iqs-card {{
    background: var(--iqs-bg-surface);
    border: 1px solid var(--iqs-border);
    border-radius: {RADIUS['lg']};
    padding: 16px 18px;
}}

.iqs-badge {{
    display: inline-flex; align-items: center; gap: 4px;
    font-family: var(--iqs-font-sans);
    font-size: 11.5px; font-weight: 600;
    padding: 3px 10px; border-radius: {RADIUS['pill']};
    line-height: 1.6;
}}

.iqs-mono {{ font-family: var(--iqs-font-mono); font-variant-numeric: tabular-nums; }}

.iqs-meter-bar {{
    display: inline-block; width: 5px; height: 15px; border-radius: 2px; margin-right: 3px;
}}

hr.topbar-divider {{
    margin: 0.2rem 0 0.9rem 0;
    border: none;
    border-top: 1px solid var(--iqs-border);
}}

div[data-testid="stButton"] > button {{ border-radius: {RADIUS['md']}; }}
</style>"""


def apply_chart_theme(fig, height: int | None = None):
    """Terapkan tema visual seragam ke SEMUA Plotly figure di app ini.
    Panggil di akhir setiap fungsi pembangun chart (chart_builder.py,
    views/detail.py, views/portfolio.py, views/backtest.py). Selalu
    dipanggil PALING TERAKHIR (setelah update_layout lain milik pemanggil)
    supaya token tema ini yang menang. Lihat IMPLEMENTATION_PLAN §8."""
    c = COLORS
    fig.update_layout(
        paper_bgcolor=c["bg_surface"],
        plot_bgcolor=c["bg_surface"],
        font=dict(family=FONT_SANS, color=c["text_secondary"], size=12),
        title_font=dict(family=FONT_SANS, color=c["text_primary"], size=14),
        legend=dict(font=dict(color=c["text_secondary"], size=11)),
        hoverlabel=dict(
            bgcolor=c["bg_surface_2"], bordercolor=c["border_strong"],
            font=dict(family=FONT_MONO, color=c["text_primary"], size=12),
        ),
    )
    if height:
        fig.update_layout(height=height)
    fig.update_xaxes(gridcolor=c["border"], zerolinecolor=c["border_strong"], showline=False)
    fig.update_yaxes(gridcolor=c["border"], zerolinecolor=c["border_strong"], showline=False)
    return fig


CANDLESTICK_COLORS = dict(
    increasing_line_color=COLORS["bullish"], increasing_fillcolor=COLORS["bullish"],
    decreasing_line_color=COLORS["bearish"], decreasing_fillcolor=COLORS["bearish"],
)


def format_idr(value: float | None, decimals: int = 0) -> str:
    """Format angka gaya Indonesia ('.' pemisah ribuan, ',' desimal).
    Contoh: format_idr(1234567.8, 2) -> 'Rp 1.234.567,80'.
    format_idr(None) -> '–'."""
    if value is None:
        return "–"
    try:
        s = f"{float(value):,.{decimals}f}"
    except (TypeError, ValueError):
        return "–"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"Rp {s}"


def format_pct_id(value: float | None, decimals: int = 2, show_sign: bool = True) -> str:
    """Format persentase gaya Indonesia, opsional tanda +. format_pct_id(None) -> '–'."""
    if value is None:
        return "–"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "–"
    sign = "+" if (show_sign and v > 0) else ""
    s = f"{v:.{decimals}f}".replace(".", ",")
    return f"{sign}{s}%"


def format_number_id(value: float | None, decimals: int = 0) -> str:
    """Sama seperti format_idr tapi tanpa prefix 'Rp' -- untuk angka umum
    (jumlah lembar saham, volume, dst)."""
    if value is None:
        return "–"
    try:
        s = f"{float(value):,.{decimals}f}"
    except (TypeError, ValueError):
        return "–"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")
