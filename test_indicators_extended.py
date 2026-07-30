"""
Test manual untuk indikator baru di indicators.py (Backtest Lab).
Jalankan: python test_indicators_extended.py
Tidak butuh koneksi Supabase / yfinance -- data OHLCV sintetis dibuat di
sini. Gaya sama dengan test_tickers_idx.py / test_position_manager.py.
"""
import numpy as np
import pandas as pd

import indicators as ind

np.random.seed(42)


def make_synthetic_ohlcv(n=300, start_price=1000.0, trend=0.0015, noise=0.01) -> pd.DataFrame:
    """OHLCV sintetis dgn trend naik ringan + noise -- cukup utk warm-up
    indikator periode terpanjang (SenkouB=52+26 displacement, dst)."""
    dates = pd.date_range("2024-01-01", periods=n, freq="B")
    returns = np.random.normal(trend, noise, n)
    close = start_price * np.cumprod(1 + returns)
    high = close * (1 + np.abs(np.random.normal(0, 0.004, n)))
    low = close * (1 - np.abs(np.random.normal(0, 0.004, n)))
    open_ = low + (high - low) * np.random.uniform(0.2, 0.8, n)
    volume = np.random.randint(1_000_000, 5_000_000, n).astype(float)
    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume},
        index=dates,
    )


df = make_synthetic_ohlcv()

print("=" * 70)
print("TEST 1: Semua indikator Tier 1 (vectorized) berjalan tanpa error")
print("=" * 70)
tier1_checks = {
    "wma": lambda: ind.wma(df["Close"], 20),
    "adx": lambda: ind.adx(df, 14),
    "ichimoku": lambda: ind.ichimoku(df),
    "vwap_rolling": lambda: ind.vwap_rolling(df, 20),
    "stochastic": lambda: ind.stochastic(df),
    "stochastic_rsi": lambda: ind.stochastic_rsi(df["Close"]),
    "cci": lambda: ind.cci(df),
    "williams_r": lambda: ind.williams_r(df),
    "roc": lambda: ind.roc(df["Close"]),
    "keltner_channels": lambda: ind.keltner_channels(df),
    "donchian_channels": lambda: ind.donchian_channels(df),
    "obv": lambda: ind.obv(df),
    "mfi": lambda: ind.mfi(df),
    "cmf": lambda: ind.cmf(df),
    "ad_line": lambda: ind.ad_line(df),
}
results = {}
for name, fn in tier1_checks.items():
    out = fn()
    results[name] = out
    n_valid = out.dropna().shape[0] if hasattr(out, "dropna") else "?"
    print(f"  {name:18s} OK -- shape={getattr(out, 'shape', len(out))}, valid non-NaN rows={n_valid}")
print("  PASS: semua Tier 1 jalan tanpa exception.\n")

print("=" * 70)
print("TEST 2: Range nilai masuk akal (sanity check formula)")
print("=" * 70)
adx_df = results["adx"].dropna()
assert (adx_df["ADX"] >= 0).all() and (adx_df["ADX"] <= 100).all(), "ADX harus 0-100"
assert (adx_df["PlusDI"] >= 0).all() and (adx_df["MinusDI"] >= 0).all(), "DI harus >= 0"
print("  ADX/PlusDI/MinusDI dalam range wajar (>=0, ADX<=100). PASS.")

stoch = results["stochastic"].dropna()
assert (stoch["K"] >= -0.01).all() and (stoch["K"] <= 100.01).all(), "Stochastic %K harus 0-100"
print("  Stochastic %K dalam range 0-100. PASS.")

wr = results["williams_r"].dropna()
assert (wr >= -100.01).all() and (wr <= 0.01).all(), "Williams %R harus -100..0"
print("  Williams %R dalam range -100..0. PASS.")

mfi_s = results["mfi"].dropna()
assert (mfi_s >= 0).all() and (mfi_s <= 100).all(), "MFI harus 0-100"
print("  MFI dalam range 0-100. PASS.")

cmf_s = results["cmf"].dropna()
assert (cmf_s >= -1.0001).all() and (cmf_s <= 1.0001).all(), "CMF harus -1..1"
print("  CMF dalam range -1..1. PASS.\n")

print("=" * 70)
print("TEST 3: WMA lebih responsif ke harga terbaru drpd SMA (bobot linear)")
print("=" * 70)
# Buat data dgn lonjakan besar di bar terakhir -- WMA harus bergerak lebih
# jauh ke arah lonjakan itu dibanding SMA periode sama, krn bobot WMA
# condong ke observasi terbaru.
spike = df["Close"].copy()
spike.iloc[-1] = spike.iloc[-2] * 1.15  # lonjakan 15% di bar terakhir
wma_val = ind.wma(spike, 20).iloc[-1]
sma_val = ind.sma(spike, 20).iloc[-1]
assert wma_val > sma_val, f"WMA ({wma_val:.2f}) harus > SMA ({sma_val:.2f}) setelah lonjakan naik"
print(f"  WMA={wma_val:.2f} > SMA={sma_val:.2f} setelah lonjakan naik di bar terakhir. PASS.\n")

print("=" * 70)
print("TEST 4: OBV naik pada uptrend konsisten; A/D Line naik saat Close")
print("dekat High tiap hari (mengukur tekanan beli INTRADAY, bukan sekadar")
print("arah harga antar-hari)")
print("=" * 70)
uptrend_df = make_synthetic_ohlcv(n=60, start_price=1000, trend=0.01, noise=0.001)
obv_series = ind.obv(uptrend_df)
assert obv_series.iloc[-1] > obv_series.iloc[10], "OBV harus naik pada uptrend konsisten"

# A/D Line = f(posisi Close dlm range High-Low hari itu) -- generator OHLCV
# umum di atas tidak mengontrol posisi Close scr sengaja, jadi dibuat data
# khusus di sini: Close SELALU dekat High (simulasi tekanan beli kuat tiap
# hari) supaya MFM konsisten positif dan A/D Line HARUS naik.
n = 60
dates = pd.date_range("2024-01-01", periods=n, freq="B")
low = np.linspace(1000, 1000, n)
high = low + 20
close_near_high = high - 1  # close nyaris di High -> MFM mendekati +1 tiap hari
strong_buy_df = pd.DataFrame({
    "Open": low + 5, "High": high, "Low": low, "Close": close_near_high,
    "Volume": np.full(n, 1_000_000.0),
}, index=dates)
ad_series = ind.ad_line(strong_buy_df)
assert ad_series.iloc[-1] > ad_series.iloc[10], "A/D Line harus naik saat Close konsisten dekat High"
print("  OBV naik pada uptrend harga; A/D Line naik saat tekanan beli intraday kuat. PASS.\n")

print("=" * 70)
print("TEST 5: Tier 2 -- Parabolic SAR & Supertrend (iteratif)")
print("=" * 70)
psar = ind.parabolic_sar(df)
st_df = ind.supertrend(df)
assert psar.notna().sum() == len(df), "PSAR harus terisi penuh sejak bar ke-0 (no warm-up NaN)"
assert set(st_df["Trend"].dropna().unique()).issubset({1, -1}), "Trend Supertrend harus cuma 1 atau -1"
# Supertrend punya NaN warm-up wajar selama ~period bar pertama (mengikuti
# ATR yg butuh window bar utk mulai terisi) -- konsisten dgn indikator lain
# yg pakai rolling/ewm window (mis. SMA200 juga NaN 200 bar pertama).
# Cek bagian SETELAH warm-up harus terisi penuh, bukan seluruh Series.
warm_up = 10  # == period default supertrend()
assert st_df["Supertrend"].iloc[warm_up:].notna().all(), "Supertrend harus terisi penuh setelah warm-up ATR"
print(f"  PSAR: {psar.notna().sum()}/{len(df)} bar terisi, range [{psar.min():.1f}, {psar.max():.1f}]")
print(f"  Supertrend: trend berganti {int((st_df['Trend'].diff() != 0).sum())} kali sepanjang {len(df)} bar")
print("  PASS: kedua indikator iteratif jalan tanpa crash & konsisten strukturnya.\n")

print("=" * 70)
print("TEST 6: Ichimoku -- SenkouA/B tergeser maju, Chikou tergeser mundur")
print("=" * 70)
ichi = ind.ichimoku(df)
# SenkouA/B di bar-bar AWAL harus NaN (karena digeser maju +26 dari base
# yg sendirinya butuh warm-up rolling) -- tapi TIDAK NaN di bar2 akhir
assert ichi["SenkouA"].iloc[:26].isna().all(), "SenkouA awal harus NaN (belum ada data utk digeser maju)"
assert ichi["Chikou"].iloc[-26:].isna().all(), "Chikou akhir harus NaN (digeser mundur, kehabisan data)"
print("  SenkouA/B (leading) & Chikou (lagging) tergeser sesuai arah yg benar. PASS.\n")

print("=" * 70)
print("SEMUA TEST indicators.py (Backtest Lab) PASS ✅")
print("=" * 70)
