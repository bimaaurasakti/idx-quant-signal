"""
chart_builder.py
=================
Builder chart Plotly generik untuk Backtest Lab -- dipakai baik utk chart
STATIS (sekali render, full history) maupun sebagai builder tiap FRAME
animasi (lihat chart_animation.py). Memisahkan logic ini dari
views/backtest.py supaya tidak duplikasi antara mode statis & animasi
(lihat IMPLEMENTATION_PLAN_UI_BACKTEST_LAB.md §3.7).

ATURAN OVERLAY vs SUBPLOT: indikator dgn spec["overlay"]==True digambar di
row harga (row 1); selain itu dapat row subplot sendiri. Kolom yg digambar
diambil generik dari semua kolom df berprefix "{indicator_key}_" (hasil
custom_backtest._attach_chart_columns()) -- tidak perlu config per-indikator
tambahan.

GOTCHA PENTING UTK ANIMASI (lihat §3.7): SEMUA frame animasi harus punya
jumlah & urutan trace yg identik persis, atau Plotly tidak akan meng-update
frame dgan benar. Karena itu trace "Entry"/"Exit" DI SINI SELALU ditambahkan
(pakai array kosong kalau belum ada trade terlihat di window ini), TIDAK
pernah conditional -- supaya build_chart_figure() aman dipanggil berkali2
dgn window berbeda-beda tanpa mengubah struktur trace.
"""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from indicator_registry import INDICATOR_SPECS
from shared_ui import EXIT_REASON_CHART_COLORS
from theme import apply_chart_theme, CANDLESTICK_COLORS, COLORS

_EXIT_REASON_LABEL = {
    "TP": "Take Profit", "SL": "Stop Loss",
    "SELL_SIGNAL": "Sinyal SELL", "TIME_EXIT": "Batas Waktu",
}


def _split_indicator_columns(df: pd.DataFrame, selected_indicators: list[str]):
    """Return (overlay_groups, subplot_groups) -- masing2 list of
    (label, [nama_kolom, ...])."""
    overlay_groups, subplot_groups = [], []
    for key in selected_indicators:
        spec = INDICATOR_SPECS.get(key)
        if spec is None:
            continue
        cols = [c for c in df.columns if c.startswith(f"{key}_")]
        if not cols:
            continue
        target = overlay_groups if spec["overlay"] else subplot_groups
        target.append((spec["label"], cols))
    return overlay_groups, subplot_groups


def build_chart_figure(
    df: pd.DataFrame,
    selected_indicators: list[str],
    trades: list[dict] | None = None,
    window_end: pd.Timestamp | None = None,
) -> go.Figure:
    """
    df: slice OHLCV + kolom indikator (hasil custom_backtest.generate_custom_signals()).
        Untuk chart statis: seluruh histori. Untuk 1 frame animasi: window
        bergeser (lihat chart_animation.py).
    trades: SELURUH list trade dari backtester.backtest_signals()['trades']
        (tidak usah difilter manual -- fungsi ini yg menyaring ke trade yg
        relevan dgn window df & window_end).
    window_end: batas waktu "sekarang" utk animasi (trade dgn exit_date >
        window_end dianggap "masih terbuka" & entry-nya tetap ditampilkan
        tapi exit-nya belum). None = pakai df.index[-1] (mode statis: semua
        trade yg overlap window ditampilkan penuh).
    """
    trades = trades or []
    window_end = window_end if window_end is not None else (df.index[-1] if len(df) else None)
    window_start = df.index[0] if len(df) else None

    overlay_groups, subplot_groups = _split_indicator_columns(df, selected_indicators)
    n_extra = len(subplot_groups)
    n_rows = 1 + n_extra + 1  # price + subplot indikator terpilih + volume
    row_heights = [3.0] + [1.4] * n_extra + [1.0]
    titles = ["Harga & Posisi"] + [label for label, _ in subplot_groups] + ["Volume"]

    fig = make_subplots(
        rows=n_rows, cols=1, shared_xaxes=True, vertical_spacing=0.035,
        row_heights=row_heights, subplot_titles=titles,
    )

    # --- Row 1: candlestick + overlay indikator ---
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name="Harga",
        **CANDLESTICK_COLORS,
    ), row=1, col=1)
    for label, cols in overlay_groups:
        for c in cols:
            suffix = c.split("_", 1)[1] if "_" in c else c
            fig.add_trace(go.Scatter(
                x=df.index, y=df[c], name=f"{label} ({suffix})", line=dict(width=1.2), mode="lines",
            ), row=1, col=1)

    # --- Entry/Exit markers -- SELALU ditambahkan (array kosong kalau tidak
    # ada yg relevan di window ini) supaya jumlah trace konsisten antar-frame ---
    relevant = [
        t for t in trades
        if window_start is not None and window_end is not None
        and pd.Timestamp(t["entry_date"]) <= window_end
        and pd.Timestamp(t["entry_date"]) >= window_start
    ]
    entry_x = [pd.Timestamp(t["entry_date"]) for t in relevant]
    entry_y = [t["entry_price"] for t in relevant]
    fig.add_trace(go.Scatter(
        x=entry_x, y=entry_y, mode="markers", name="Entry",
        marker=dict(symbol="triangle-up", size=11, color=COLORS["bullish"], line=dict(width=1, color="white")),
    ), row=1, col=1)

    exited = [t for t in relevant if pd.Timestamp(t["exit_date"]) <= window_end]
    exit_x = [pd.Timestamp(t["exit_date"]) for t in exited]
    exit_y = [t["exit_price"] for t in exited]
    exit_colors = [
        EXIT_REASON_CHART_COLORS.get(_EXIT_REASON_LABEL.get(t["reason"], ""), "#999999") for t in exited
    ]
    fig.add_trace(go.Scatter(
        x=exit_x, y=exit_y, mode="markers", name="Exit",
        marker=dict(symbol="triangle-down", size=11, color=exit_colors or "#999999", line=dict(width=1, color="white")),
    ), row=1, col=1)

    # --- Subplot indikator non-overlay ---
    for row_i, (label, cols) in enumerate(subplot_groups, start=2):
        for c in cols:
            suffix = c.split("_", 1)[1] if "_" in c else c
            fig.add_trace(go.Scatter(
                x=df.index, y=df[c], name=f"{label} ({suffix})", line=dict(width=1), mode="lines",
            ), row=row_i, col=1)

    # --- Volume (row terakhir, selalu ada) -- diwarnai per-bar sesuai arah
    # candle (naik/turun) supaya konsisten dgn konvensi warna sinyal app ini,
    # bukan satu warna flat spt sebelumnya (lihat IMPLEMENTATION_PLAN §8.1). ---
    vol_colors = [
        "rgba(34,197,94,0.45)" if c >= o else "rgba(239,68,68,0.45)"
        for o, c in zip(df["Open"], df["Close"])
    ]
    fig.add_trace(go.Bar(
        x=df.index, y=df["Volume"], name="Volume", marker_color=vol_colors,
    ), row=n_rows, col=1)

    fig.update_layout(
        height=min(230 * n_rows + 120, 1100),
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return apply_chart_theme(fig)
