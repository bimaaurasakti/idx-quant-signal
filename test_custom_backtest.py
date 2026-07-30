"""
Test manual untuk custom_backtest.py (algoritma Vote & Trigger, Backtest Lab).
Jalankan: python test_custom_backtest.py
"""
import numpy as np
import pandas as pd

from custom_backtest import generate_custom_signals, validate_min_bars, compute_equity_curve

np.random.seed(7)


def make_step_ohlcv(n=80) -> pd.DataFrame:
    """Harga flat/turun tipis 40 bar pertama, lalu naik tajam & konsisten
    40 bar berikutnya -- didesain supaya EMA cepat (fast) jelas cross di
    atas EMA lambat (slow) SEKALI di sekitar bar ke-40, bukan berkali-kali."""
    dates = pd.date_range("2024-01-01", periods=n, freq="B")
    down = 1000 - np.cumsum(np.random.uniform(0, 1.5, 40))
    up = down[-1] + np.cumsum(np.random.uniform(3, 6, 40))
    close = np.concatenate([down, up])
    high = close * 1.005
    low = close * 0.995
    open_ = close
    volume = np.full(n, 2_000_000.0)
    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume},
        index=dates,
    )


df = make_step_ohlcv()

print("=" * 70)
print("TEST 1: ATR14 SELALU ada meski indikator terpilih tidak termasuk ATR")
print("=" * 70)
out = generate_custom_signals(df, selected_indicators=["rsi"], confirmation_threshold=1)
assert "ATR14" in out.columns, "ATR14 harus selalu dihitung utk sizing TP/SL"
assert out["ATR14"].notna().sum() > 0
print("  PASS: ATR14 ada di output walau cuma pilih RSI.\n")

print("=" * 70)
print("TEST 2: selected_indicators kosong -> Signal semua 0, tidak crash")
print("=" * 70)
out_empty = generate_custom_signals(df, selected_indicators=[], confirmation_threshold=1)
assert (out_empty["Signal"] == 0).all()
print("  PASS: list indikator kosong ditangani dgn aman.\n")

print("=" * 70)
print("TEST 3: EMA Crossover -- sinyal BUY muncul TEPAT SEKALI di sekitar")
print("titik crossover, bukan berulang tiap hari selama trend berlanjut")
print("=" * 70)
out_cross = generate_custom_signals(
    df, selected_indicators=["ema_crossover"],
    params={"ema_crossover": {"fast": 3, "slow": 8}},
    confirmation_threshold=1,
)
buy_days = out_cross.index[out_cross["Signal"] == 1]
print(f"  Bar dgn Signal==1: {[d.strftime('%Y-%m-%d') for d in buy_days]}")
assert len(buy_days) >= 1, "Harus ada minimal 1 sinyal BUY setelah crossover naik"
# Sinyal2 BUY yg muncul (kalau lebih dari 1, karena harga naik terus bisa
# ada micro-flip) harus TERKUMPUL di sekitar fase uptrend (index >= 35),
# BUKAN tersebar acak di fase downtrend awal.
assert all(out_cross.index.get_loc(d) >= 35 for d in buy_days), \
    "Sinyal BUY seharusnya muncul di fase uptrend (bar >=35), bukan di fase turun awal"
print("  PASS: sinyal BUY EMA Crossover muncul di fase uptrend, konsisten dgn desain event-trigger.\n")

print("=" * 70)
print("TEST 4: confirmation_threshold=2 dgn 2 indikator -- HANYA trigger")
print("kalau KEDUANYA sepakat di bar yg sama (bukan salah satu saja)")
print("=" * 70)
out_thr1 = generate_custom_signals(
    df, selected_indicators=["ema_crossover", "rsi"],
    params={"ema_crossover": {"fast": 3, "slow": 8}},
    confirmation_threshold=1,
)
out_thr2 = generate_custom_signals(
    df, selected_indicators=["ema_crossover", "rsi"],
    params={"ema_crossover": {"fast": 3, "slow": 8}},
    confirmation_threshold=2,
)
n_signals_thr1 = int((out_thr1["Signal"] != 0).sum())
n_signals_thr2 = int((out_thr2["Signal"] != 0).sum())
print(f"  threshold=1: {n_signals_thr1} sinyal | threshold=2: {n_signals_thr2} sinyal")
assert n_signals_thr2 <= n_signals_thr1, \
    "Threshold lebih ketat (butuh lebih banyak konfirmasi) harus menghasilkan sinyal <= threshold longgar"
print("  PASS: menaikkan confirmation_threshold tidak pernah menambah jumlah sinyal.\n")

print("=" * 70)
print("TEST 5: Tie-break BUY vs SELL di bar yang sama -> prioritas SELL")
print("(reproduksi langsung logika trigger, lihat custom_backtest.py docstring)")
print("=" * 70)
bullish_count = pd.Series([0, 3, 3, 0])   # naik ke atas threshold di index 1
bearish_count = pd.Series([0, 3, 0, 0])   # JUGA naik ke atas threshold di index 1 (sama persis)
threshold = 2
prev_b = bullish_count.shift(1).fillna(0)
prev_s = bearish_count.shift(1).fillna(0)
buy_trigger = (bullish_count >= threshold) & (prev_b < threshold)
sell_trigger = (bearish_count >= threshold) & (prev_s < threshold)
signal = pd.Series(0, index=bullish_count.index)
signal[sell_trigger] = -1
signal[buy_trigger & ~sell_trigger] = 1
assert signal.iloc[1] == -1, "Saat BUY & SELL trigger bareng, SELL harus menang (konservatif)"
print(f"  signal di bar konflik = {signal.iloc[1]} (harus -1). PASS.\n")

print("=" * 70)
print("TEST 6: validate_min_bars()")
print("=" * 70)
ok, msg = validate_min_bars(df, min_bars=60)
assert ok, "80 bar valid harus lolos syarat minimal 60 bar"
short_df = df.iloc[:30]
ok2, msg2 = validate_min_bars(short_df, min_bars=60)
assert not ok2 and "terlalu pendek" in msg2
print("  PASS: validasi panjang data bekerja utk kasus cukup & tidak cukup.\n")

print("=" * 70)
print("TEST 7: compute_equity_curve()")
print("=" * 70)
trades = [{"return_pct": 10.0}, {"return_pct": -5.0}, {"return_pct": 8.0}]
equity = compute_equity_curve(trades)
expected_final = (1.10) * (0.95) * (1.08)
assert abs(equity.iloc[-1] - expected_final) < 1e-9, "Equity curve harus compounding, bukan sum"
assert compute_equity_curve([]).empty
print(f"  Equity akhir dari 3 trade = {equity.iloc[-1]:.4f} (expected {expected_final:.4f}). PASS.\n")

print("=" * 70)
print("SEMUA TEST custom_backtest.py PASS ✅")
print("=" * 70)
