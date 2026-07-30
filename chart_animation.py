"""
chart_animation.py
===================
Wrapper animasi replay backtest: sliding window ukuran tetap yang bergeser
maju sepanjang waktu (BUKAN cumulative-growing-window -- lebih enak
ditonton & payload per-frame konstan berapa pun panjang histori). Lihat
IMPLEMENTATION_PLAN_UI_BACKTEST_LAB.md §3.7 utk alasan desain lengkap.

GOTCHA PLOTLY: semua trace harus konsisten jumlah & urutannya di tiap
frame -- ditangani di sisi chart_builder.build_chart_figure() (trace
Entry/Exit SELALU ditambahkan, walau array kosong).
"""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go

from chart_builder import build_chart_figure


def build_animated_backtest_chart(
    df: pd.DataFrame,
    selected_indicators: list[str],
    trades: list[dict],
    window_size: int = 90,
    target_frames: int = 150,
) -> go.Figure:
    """
    df: OHLCV + kolom indikator lengkap (SUDAH melewati warm-up NaN --
        caller wajib drop baris awal yg masih NaN sebelum manggil ini,
        lihat views/backtest.py).
    window_size: jumlah bar yg terlihat sekaligus di tiap frame (viewport).
    target_frames: target jumlah frame total -- frame_step dihitung
        adaptif dari ini supaya animasi tetap ringan berapa pun panjang df
        (5 tahun ataupun 1 tahun, jumlah frame tetap ~target_frames).
    """
    n = len(df)
    if n <= window_size:
        # Histori lebih pendek dari 1 window -- tampilkan statis saja,
        # tidak ada yg bisa dianimasikan.
        return build_chart_figure(df, selected_indicators, trades)

    frame_step = max(1, (n - window_size) // target_frames)
    frame_end_indices = list(range(window_size, n, frame_step))
    if frame_end_indices[-1] != n - 1:
        frame_end_indices.append(n - 1)

    # Frame awal (state pertama yg dirender) = window pertama.
    initial_end = frame_end_indices[0]
    initial_window = df.iloc[max(0, initial_end - window_size + 1): initial_end + 1]
    fig = build_chart_figure(
        initial_window, selected_indicators, trades, window_end=df.index[initial_end],
    )

    frames = []
    for end_idx in frame_end_indices:
        window = df.iloc[max(0, end_idx - window_size + 1): end_idx + 1]
        snap = build_chart_figure(
            window, selected_indicators, trades, window_end=df.index[end_idx],
        )
        # snap.data HARUS sama jumlah & urutan trace dgn fig.data awal --
        # dijamin oleh build_chart_figure() krn selected_indicators & window
        # size (jumlah bar tervisualisasi) konsisten tiap panggilan.
        frames.append(go.Frame(data=snap.data, name=str(end_idx), layout=snap.layout))

    fig.frames = frames
    fig.update_layout(
        updatemenus=[{
            "type": "buttons", "showactive": False,
            "x": 0.0, "y": 1.12, "xanchor": "left",
            "buttons": [
                {
                    "label": "▶️ Play", "method": "animate",
                    "args": [None, {"frame": {"duration": 180, "redraw": True},
                                     "fromcurrent": True, "transition": {"duration": 0}}],
                },
                {
                    "label": "⏸️ Pause", "method": "animate",
                    "args": [[None], {"frame": {"duration": 0}, "mode": "immediate"}],
                },
            ],
        }],
        sliders=[{
            "active": 0,
            "x": 0.08, "y": -0.02, "len": 0.9,
            "steps": [
                {
                    "args": [[str(idx)], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}],
                    "label": pd.Timestamp(df.index[idx]).strftime("%d/%m/%y"),
                    "method": "animate",
                }
                for idx in frame_end_indices
            ],
        }],
    )
    return fig


def estimate_frame_count(n_bars: int, window_size: int = 90, target_frames: int = 150) -> int:
    """Helper utk UI -- kasih tahu user perkiraan jumlah frame SEBELUM
    tombol 'Putar Animasi' diklik (animasi dibangun lazy, lihat §3.6)."""
    if n_bars <= window_size:
        return 0
    frame_step = max(1, (n_bars - window_size) // target_frames)
    return len(range(window_size, n_bars, frame_step)) + 1
