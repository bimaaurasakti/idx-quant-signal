"""
Indikator teknikal — implementasi manual pakai pandas/numpy saja
(tidak butuh TA-Lib yang sering susah di-install).
"""
from __future__ import annotations
import numpy as np
import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=window).mean()


def ema(series: pd.Series, window: int) -> pd.Series:
    return series.ewm(span=window, adjust=False, min_periods=window).mean()


def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    out = 100 - (100 / (1 + rs))
    return out.fillna(50)


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False, min_periods=signal).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def _true_range(df: pd.DataFrame) -> pd.Series:
    """True Range mentah (belum di-smooth) -- dipakai atr() dan adx()."""
    high, low, close = df["High"], df["Low"], df["Close"]
    prev_close = close.shift(1)
    return pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)


def atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    tr = _true_range(df)
    return tr.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()


def bollinger_bands(series: pd.Series, window: int = 20, num_std: float = 2.0):
    mid = sma(series, window)
    std = series.rolling(window=window, min_periods=window).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    return upper, mid, lower


def volume_ratio(volume: pd.Series, window: int = 20) -> pd.Series:
    """Volume hari ini dibagi rata-rata volume N hari (deteksi lonjakan volume)."""
    avg_vol = volume.rolling(window=window, min_periods=window).mean()
    return volume / avg_vol.replace(0, np.nan)


# ============================================================================
# INDIKATOR TAMBAHAN — Backtest Lab (lihat IMPLEMENTATION_PLAN_UI_BACKTEST_LAB.md §3.2)
# Semua manual pakai pandas/numpy, konsisten dgn filosofi file ini (no TA-Lib).
# ============================================================================

# ---- Tier 1: vectorized (rolling/ewm), tidak butuh loop eksplisit --------

def wma(series: pd.Series, window: int) -> pd.Series:
    """Weighted Moving Average (bobot linear 1..window, terbaru paling berat)."""
    weights = np.arange(1, window + 1)
    return series.rolling(window=window, min_periods=window).apply(
        lambda x: np.dot(x, weights) / weights.sum(), raw=True
    )


def adx(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    """Average Directional Index (Wilder). Kolom: ADX, PlusDI, MinusDI.
    ADX mengukur KEKUATAN trend (bukan arah); arah dari PlusDI vs MinusDI."""
    high, low = df["High"], df["Low"]
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = pd.Series(
        np.where((up_move > down_move) & (up_move > 0), up_move, 0.0), index=df.index
    )
    minus_dm = pd.Series(
        np.where((down_move > up_move) & (down_move > 0), down_move, 0.0), index=df.index
    )
    tr = _true_range(df)
    atr_smooth = tr.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    plus_dm_smooth = plus_dm.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    minus_dm_smooth = minus_dm.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()

    plus_di = 100 * (plus_dm_smooth / atr_smooth.replace(0, np.nan))
    minus_di = 100 * (minus_dm_smooth / atr_smooth.replace(0, np.nan))
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx_val = dx.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    return pd.DataFrame({"ADX": adx_val, "PlusDI": plus_di, "MinusDI": minus_di})


def ichimoku(df: pd.DataFrame, tenkan: int = 9, kijun: int = 26,
             senkou_b_period: int = 52, displacement: int = 26) -> pd.DataFrame:
    """Ichimoku Kinko Hyo. Kolom: Tenkan, Kijun, SenkouA, SenkouB, Chikou.
    SenkouA/B digeser maju `displacement` bar (leading), Chikou digeser
    mundur (lagging) -- perilaku standar."""
    high, low, close = df["High"], df["Low"], df["Close"]
    tenkan_sen = (high.rolling(tenkan).max() + low.rolling(tenkan).min()) / 2
    kijun_sen = (high.rolling(kijun).max() + low.rolling(kijun).min()) / 2
    senkou_a = ((tenkan_sen + kijun_sen) / 2).shift(displacement)
    senkou_b = ((high.rolling(senkou_b_period).max() + low.rolling(senkou_b_period).min()) / 2).shift(displacement)
    chikou = close.shift(-displacement)
    return pd.DataFrame({
        "Tenkan": tenkan_sen, "Kijun": kijun_sen,
        "SenkouA": senkou_a, "SenkouB": senkou_b, "Chikou": chikou,
    })


def vwap_rolling(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """VWAP N-hari berjalan -- ADAPTASI dari VWAP intraday asli (yang reset
    tiap sesi) karena sistem ini pakai bar harian. Beri label di UI sbg
    'VWAP (Rolling N-hari)' supaya tidak menyesatkan."""
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    pv = tp * df["Volume"]
    return (pv.rolling(window, min_periods=window).sum() /
            df["Volume"].rolling(window, min_periods=window).sum())


def stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
    """Stochastic Oscillator. Kolom: K, D."""
    low_min = df["Low"].rolling(k_period, min_periods=k_period).min()
    high_max = df["High"].rolling(k_period, min_periods=k_period).max()
    percent_k = 100 * (df["Close"] - low_min) / (high_max - low_min).replace(0, np.nan)
    percent_d = percent_k.rolling(d_period, min_periods=d_period).mean()
    return pd.DataFrame({"K": percent_k, "D": percent_d})


def stochastic_rsi(series: pd.Series, rsi_period: int = 14,
                    stoch_period: int = 14, d_period: int = 3) -> pd.DataFrame:
    """Stochastic RSI -- formula Stochastic diterapkan ke SERIES RSI (bukan
    ke harga langsung). Kolom: K, D."""
    rsi_series = rsi(series, rsi_period)
    low_min = rsi_series.rolling(stoch_period, min_periods=stoch_period).min()
    high_max = rsi_series.rolling(stoch_period, min_periods=stoch_period).max()
    percent_k = 100 * (rsi_series - low_min) / (high_max - low_min).replace(0, np.nan)
    percent_d = percent_k.rolling(d_period, min_periods=d_period).mean()
    return pd.DataFrame({"K": percent_k, "D": percent_d})


def cci(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """Commodity Channel Index."""
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    sma_tp = tp.rolling(window, min_periods=window).mean()
    mean_abs_dev = tp.rolling(window, min_periods=window).apply(
        lambda x: np.abs(x - x.mean()).mean(), raw=True
    )
    return (tp - sma_tp) / (0.015 * mean_abs_dev.replace(0, np.nan))


def williams_r(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """Williams %R (range -100..0, mirip Stochastic terbalik)."""
    high_max = df["High"].rolling(window, min_periods=window).max()
    low_min = df["Low"].rolling(window, min_periods=window).min()
    return -100 * (high_max - df["Close"]) / (high_max - low_min).replace(0, np.nan)


def roc(series: pd.Series, window: int = 12) -> pd.Series:
    """Rate of Change (%)."""
    shifted = series.shift(window)
    return (series - shifted) / shifted.replace(0, np.nan) * 100


def keltner_channels(df: pd.DataFrame, ema_window: int = 20,
                      atr_window: int = 10, mult: float = 2.0) -> pd.DataFrame:
    """Keltner Channels. Kolom: Upper, Middle, Lower."""
    middle = ema(df["Close"], ema_window)
    band = mult * atr(df, atr_window)
    return pd.DataFrame({"Upper": middle + band, "Middle": middle, "Lower": middle - band})


def donchian_channels(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """Donchian Channels (breakout N-hari, gaya Turtle Trading). Kolom: Upper, Middle, Lower."""
    upper = df["High"].rolling(window, min_periods=window).max()
    lower = df["Low"].rolling(window, min_periods=window).min()
    return pd.DataFrame({"Upper": upper, "Middle": (upper + lower) / 2, "Lower": lower})


def obv(df: pd.DataFrame) -> pd.Series:
    """On-Balance Volume."""
    direction = np.sign(df["Close"].diff()).fillna(0)
    return (direction * df["Volume"]).cumsum()


def mfi(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """Money Flow Index ("RSI dengan volume")."""
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    raw_flow = tp * df["Volume"]
    tp_diff = tp.diff()
    pos_flow = raw_flow.where(tp_diff > 0, 0.0)
    neg_flow = raw_flow.where(tp_diff < 0, 0.0)
    pos_sum = pos_flow.rolling(window, min_periods=window).sum()
    neg_sum = neg_flow.rolling(window, min_periods=window).sum()
    money_ratio = pos_sum / neg_sum.replace(0, np.nan)
    return 100 - (100 / (1 + money_ratio))


def cmf(df: pd.DataFrame, window: int = 20) -> pd.Series:
    """Chaikin Money Flow."""
    mfm = ((df["Close"] - df["Low"]) - (df["High"] - df["Close"])) / (df["High"] - df["Low"]).replace(0, np.nan)
    mfv = mfm * df["Volume"]
    return mfv.rolling(window, min_periods=window).sum() / df["Volume"].rolling(window, min_periods=window).sum()


def ad_line(df: pd.DataFrame) -> pd.Series:
    """Accumulation/Distribution Line (kumulatif)."""
    mfm = ((df["Close"] - df["Low"]) - (df["High"] - df["Close"])) / (df["High"] - df["Low"]).replace(0, np.nan)
    mfv = (mfm * df["Volume"]).fillna(0)
    return mfv.cumsum()


# ---- Tier 2: butuh loop iteratif eksplisit (state machine antar-bar) -----

def parabolic_sar(df: pd.DataFrame, step: float = 0.02, max_step: float = 0.2) -> pd.Series:
    """Parabolic SAR (Wilder). Iteratif -- nilai bar-t bergantung apakah
    trend 'flip' di bar t-1, sulit divectorize. ~1250 bar (5 tahun) tetap
    sub-detik dgn loop Python murni."""
    high, low, close = df["High"].to_numpy(), df["Low"].to_numpy(), df["Close"].to_numpy()
    n = len(df)
    sar = np.full(n, np.nan)
    if n < 2:
        return pd.Series(sar, index=df.index)

    uptrend = close[1] >= close[0]
    sar[0] = low[0] if uptrend else high[0]
    ep = high[0] if uptrend else low[0]
    af = step

    for i in range(1, n):
        sar[i] = sar[i - 1] + af * (ep - sar[i - 1])

        if uptrend:
            prev_low = low[i - 2] if i >= 2 else low[i - 1]
            sar[i] = min(sar[i], low[i - 1], prev_low)
            if low[i] < sar[i]:
                uptrend, sar[i], ep, af = False, ep, low[i], step
            elif high[i] > ep:
                ep, af = high[i], min(af + step, max_step)
        else:
            prev_high = high[i - 2] if i >= 2 else high[i - 1]
            sar[i] = max(sar[i], high[i - 1], prev_high)
            if high[i] > sar[i]:
                uptrend, sar[i], ep, af = True, ep, high[i], step
            elif low[i] < ep:
                ep, af = low[i], min(af + step, max_step)

    return pd.Series(sar, index=df.index)


def supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.DataFrame:
    """Supertrend. Kolom: Supertrend (garis), Trend (1=uptrend/-1=downtrend).
    Iteratif -- band final bergantung nilai band final bar sebelumnya."""
    atr_val = atr(df, period)
    hl2 = (df["High"] + df["Low"]) / 2
    basic_upper = (hl2 + multiplier * atr_val).to_numpy()
    basic_lower = (hl2 - multiplier * atr_val).to_numpy()
    close = df["Close"].to_numpy()
    n = len(df)

    final_upper = np.full(n, np.nan)
    final_lower = np.full(n, np.nan)
    line = np.full(n, np.nan)

    for i in range(n):
        if i == 0 or np.isnan(basic_upper[i]) or np.isnan(basic_lower[i]) or np.isnan(final_upper[i - 1]):
            final_upper[i] = basic_upper[i]
            final_lower[i] = basic_lower[i]
            line[i] = basic_upper[i]
            continue

        final_upper[i] = (
            basic_upper[i] if (basic_upper[i] < final_upper[i - 1] or close[i - 1] > final_upper[i - 1])
            else final_upper[i - 1]
        )
        final_lower[i] = (
            basic_lower[i] if (basic_lower[i] > final_lower[i - 1] or close[i - 1] < final_lower[i - 1])
            else final_lower[i - 1]
        )
        if line[i - 1] == final_upper[i - 1]:
            line[i] = final_upper[i] if close[i] <= final_upper[i] else final_lower[i]
        else:
            line[i] = final_lower[i] if close[i] >= final_lower[i] else final_upper[i]

    trend = np.where(line == final_upper, -1, 1)
    return pd.DataFrame({"Supertrend": line, "Trend": trend}, index=df.index)


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Tambahkan semua indikator ke DataFrame OHLCV. Return copy baru."""
    out = df.copy()
    out["SMA20"] = sma(out["Close"], 20)
    out["SMA50"] = sma(out["Close"], 50)
    out["SMA200"] = sma(out["Close"], 200)
    out["EMA12"] = ema(out["Close"], 12)
    out["EMA26"] = ema(out["Close"], 26)
    out["RSI14"] = rsi(out["Close"], 14)
    macd_line, signal_line, hist = macd(out["Close"])
    out["MACD"] = macd_line
    out["MACD_Signal"] = signal_line
    out["MACD_Hist"] = hist
    out["ATR14"] = atr(out, 14)
    bb_up, bb_mid, bb_low = bollinger_bands(out["Close"], 20, 2.0)
    out["BB_Upper"] = bb_up
    out["BB_Mid"] = bb_mid
    out["BB_Lower"] = bb_low
    out["VolRatio20"] = volume_ratio(out["Volume"], 20)
    return out
