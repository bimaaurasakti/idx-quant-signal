"""
Test manual untuk chart_builder.py & chart_animation.py setelah chart
theming (Fase 2, lihat IMPLEMENTATION_PLAN_UI_REDESIGN_STOCKBIT.md §8).
Jalankan: python test_chart_theming.py
Tidak butuh Supabase -- data OHLCV sintetis, gaya sama dengan
test_indicators_extended.py / test_custom_backtest.py.

FOKUS PENGUJIAN: (1) tema (warna/font/latar) benar2 ke-apply, (2) GOTCHA
PALING PENTING dari chart_animation.py TETAP terjaga: semua frame animasi
harus punya jumlah & urutan trace yang identik persis -- apply_chart_theme()
hanya boleh menyentuh layout, TIDAK PERNAH menambah/menghapus trace.
"""
import numpy as np
import pandas as pd

from custom_backtest import generate_custom_signals
from backtester import backtest_signals
from chart_builder import build_chart_figure
from chart_animation import build_animated_backtest_chart, estimate_frame_count
import theme

np.random.seed(11)


def make_ohlcv(n=260) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=n, freq="B")
    returns = np.random.normal(0.001, 0.012, n)
    close = 1000.0 * np.cumprod(1 + returns)
    high = close * (1 + np.abs(np.random.normal(0, 0.004, n)))
    low = close * (1 - np.abs(np.random.normal(0, 0.004, n)))
    open_ = low + (high - low) * np.random.uniform(0.2, 0.8, n)
    volume = np.random.randint(1_000_000, 5_000_000, n).astype(float)
    return pd.DataFrame({"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume}, index=dates)


df = make_ohlcv()
selected = ["ema_crossover", "rsi", "macd"]  # 1 overlay + 2 subplot -- kombinasi representatif
d = generate_custom_signals(df, selected, confirmation_threshold=1)
bt = backtest_signals(d)
print(f"Data sintetis siap: {len(d)} bar, {bt['n_trades']} trade dari kombinasi {selected}")

errors = []


def check(label, cond):
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {label}")
    if not cond:
        errors.append(label)


print("\n=== Chart statis (build_chart_figure) ===")
fig = build_chart_figure(d, selected, bt["trades"])

check("paper_bgcolor sesuai token theme.py", fig.layout.paper_bgcolor == theme.COLORS["bg_surface"])
check("plot_bgcolor sesuai token theme.py", fig.layout.plot_bgcolor == theme.COLORS["bg_surface"])
check("font family Inter ter-set", fig.layout.font.family == theme.FONT_SANS)

candle = [t for t in fig.data if t.type == "candlestick"][0]
check("candlestick increasing = bullish token", candle.increasing.line.color == theme.COLORS["bullish"])
check("candlestick decreasing = bearish token", candle.decreasing.line.color == theme.COLORS["bearish"])

entry_trace = [t for t in fig.data if t.name == "Entry"][0]
check("marker Entry pakai warna bullish token (bukan lagi hardcode)", entry_trace.marker.color == theme.COLORS["bullish"])

vol_trace = [t for t in fig.data if t.name == "Volume"][0]
check("volume bar warna per-bar (list, bukan 1 warna flat)", isinstance(vol_trace.marker.color, (list, tuple)) and len(vol_trace.marker.color) == len(d))

trace_names = [t.name for t in fig.data]
print(f"  Trace pada chart statis ({len(trace_names)}): {trace_names}")
check("trace Entry & Exit SELALU ada (kontrak lama chart_animation.py tetap terjaga)",
      "Entry" in trace_names and "Exit" in trace_names)

print("\n=== GOTCHA UTAMA: konsistensi trace antar-frame animasi ===")
n_frames_est = estimate_frame_count(len(d))
print(f"  Estimasi jumlah frame: {n_frames_est}")
fig_anim = build_animated_backtest_chart(d, selected, bt["trades"], window_size=60, target_frames=20)

base_trace_count = len(fig_anim.data)
base_trace_names = [t.name for t in fig_anim.data]
print(f"  Trace di frame AWAL: {base_trace_count} -> {base_trace_names}")
check("jumlah frame animasi dibuat (> 1)", len(fig_anim.frames) > 1)

mismatches = [
    i for i, fr in enumerate(fig_anim.frames)
    if len(fr.data) != base_trace_count or [t.name for t in fr.data] != base_trace_names
]
check(f"SEMUA {len(fig_anim.frames)} frame animasi py jumlah & urutan trace IDENTIK dgn frame awal "
      f"(gotcha chart_animation.py -- kalau ini FAIL, Plotly animate tidak akan update dgn benar)",
      len(mismatches) == 0)
if mismatches:
    print(f"    Frame index yang beda: {mismatches[:10]}")

first_frame_candle = [t for t in fig_anim.frames[0].data if t.type == "candlestick"][0]
check("tema warna candlestick JUGA konsisten di dalam frame (bukan cuma figure awal)",
      first_frame_candle.increasing.line.color == theme.COLORS["bullish"])

print("\n=== Histori pendek (<= window_size) -- jalur fallback statis di chart_animation.py ===")
short_d = d.iloc[:50]
fig_short = build_animated_backtest_chart(short_d, selected, bt["trades"], window_size=90)
check("histori pendek fallback ke chart statis (tanpa frames) TANPA error",
      not hasattr(fig_short, "frames") or len(fig_short.frames) == 0)
check("chart statis fallback tetap dapat tema (bg_surface)", fig_short.layout.paper_bgcolor == theme.COLORS["bg_surface"])

print(f"\n{'='*70}")
if errors:
    print(f"GAGAL: {len(errors)} pengecekan tidak lolos -> {errors}")
    raise SystemExit(1)
print("SEMUA TEST chart theming (Fase 2) PASS ✅")
print(f"{'='*70}")
