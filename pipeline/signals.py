"""
Signal engine: Dual-Horizon IHSG Adaptive Momentum & Flexible Multi-Confirmation System.
"""
from __future__ import annotations
import pandas as pd
import numpy as np

from indicators import add_all_indicators


def check_ihsg_regime(ihsg_df: pd.DataFrame | None) -> dict:
    """
    Evaluasi Dual-Horizon Macro & Micro Market Regime dari IHSG (^JKSE):
    - Macro Horizon: IHSG Close >= SMA200 (Bullish vs Bearish Macro).
    - Micro Horizon: Daily Candle Hijau (Close >= Open atau Close >= Close[t-1])
      DAN akselerasi momentum (MACD Histogram membesar / berbalik naik atau Close >= EMA10).

    Returns:
        dict dengan struktur:
        {
            "tier": "HIGH_ALPHA" | "TACTICAL_SWING" | "DEFENSIVE",
            "macro_bull": bool,
            "momentum_green": bool,
            "sizing": float (1.0 | 0.5 | 0.0),
            "max_pos": int (7 | 3 | 0),
            "last_close": float | None,
            "sma200": float | None,
            "dist_sma200_pct": float | None,
            "description": str,
        }
    """
    default_regime = {
        "tier": "HIGH_ALPHA",
        "macro_bull": True,
        "momentum_green": True,
        "sizing": 1.0,
        "max_pos": 7,
        "last_close": None,
        "sma200": None,
        "dist_sma200_pct": None,
        "description": "Data IHSG tidak tersedia, fallback ke default High Alpha.",
    }

    if ihsg_df is None or ihsg_df.empty or len(ihsg_df) < 20:
        return default_regime

    close = ihsg_df["Close"]
    last_close = float(close.iloc[-1])
    n = len(ihsg_df)

    # 1. Macro Horizon (SMA200)
    if n >= 200:
        sma200_series = close.rolling(200, min_periods=200).mean()
        last_sma200 = float(sma200_series.iloc[-1]) if not pd.isna(sma200_series.iloc[-1]) else None
    else:
        last_sma200 = None

    if last_sma200 is not None:
        macro_bull = bool(last_close >= last_sma200)
        dist_sma200_pct = round(((last_close - last_sma200) / last_sma200) * 100, 2)
    else:
        macro_bull = True
        dist_sma200_pct = 0.0

    # 2. Micro Momentum Horizon
    open_series = ihsg_df["Open"] if "Open" in ihsg_df.columns else close
    last_open = float(open_series.iloc[-1])
    prev_close = float(close.iloc[-2]) if n >= 2 else last_close

    # Candle hijau jika close hari ini >= open hari ini ATAU close hari ini >= close kemarin
    candle_green = bool(last_close >= last_open or last_close >= prev_close)

    # Momentum Acceleration via MACD Histogram
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    hist = macd_line - signal_line

    if len(hist) >= 2:
        hist_now = float(hist.iloc[-1])
        hist_prev = float(hist.iloc[-2])
        hist_accel = bool(hist_now > hist_prev or hist_now > 0)
    else:
        hist_accel = True

    # EMA10 Short-term Trend
    ema10_series = close.ewm(span=10, adjust=False).mean()
    above_ema10 = bool(last_close >= float(ema10_series.iloc[-1]))

    # Micro momentum dianggap HIJAU jika candle hijau DAN (histogram naik ATAU harga di atas EMA10)
    momentum_green = bool(candle_green and (hist_accel or above_ema10))

    # 3. Klasifikasi Rezim Pasar & Pembobotan
    if macro_bull and momentum_green:
        tier = "HIGH_ALPHA"
        sizing = 1.0
        max_pos = 7
        desc = "Macro Bullish + Momentum Hijau. Full deployment 100% sizing."
    elif (not macro_bull) and momentum_green:
        tier = "TACTICAL_SWING"
        sizing = 0.5
        max_pos = 3
        desc = "Macro Bearish tapi Rebound Hijau. Tactical swing 50% sizing, maks 3 posisi."
    else:
        tier = "DEFENSIVE"
        sizing = 0.0
        max_pos = 0
        desc = "Market Risk-Off / Momentum Merah. Entry ditahan (0% sizing) untuk menjaga modal."

    return {
        "tier": tier,
        "macro_bull": macro_bull,
        "momentum_green": momentum_green,
        "sizing": sizing,
        "max_pos": max_pos,
        "last_close": round(last_close, 2),
        "sma200": round(last_sma200, 2) if last_sma200 is not None else None,
        "dist_sma200_pct": dist_sma200_pct,
        "description": desc,
    }


def generate_signals(
    df: pd.DataFrame,
    market_bullish: bool | dict = True,
    market_regime: dict | None = None,
) -> pd.DataFrame:
    """
    Input: DataFrame OHLCV mentah.
    Output: DataFrame dengan indikator + kolom 'Signal' (1=BUY, -1=SELL, 0=HOLD)
    dan kolom 'SignalStrength' (0-3, jumlah konfirmasi yang terpenuhi).

    Fitur Baru:
    - 3-Day Lookback Window untuk MACD Golden Cross & Volume Accumulation.
    - Resolusi Bug Data: Tidak pernah menghapus histori sinyal DataFrame untuk backtest.
    - Live Gate: Hanya memfilter candle live EOD (bar terakhir) berdasarkan rezim pasar.
    """
    d = add_all_indicators(df)

    # Ekstrak rezim pasar
    regime = market_regime
    if regime is None:
        if isinstance(market_bullish, dict):
            regime = market_bullish
        elif isinstance(market_bullish, bool):
            regime = {
                "tier": "HIGH_ALPHA" if market_bullish else "DEFENSIVE",
                "sizing": 1.0 if market_bullish else 0.0,
                "macro_bull": market_bullish,
                "momentum_green": market_bullish,
            }
        else:
            regime = {"tier": "HIGH_ALPHA", "sizing": 1.0, "macro_bull": True, "momentum_green": True}

    # --- 1. Kondisi TREND (Hard Gate) ---
    uptrend = (d["Close"] > d["SMA50"]) & (d["SMA50"] > d["SMA200"])
    downtrend = (d["Close"] < d["SMA50"]) & (d["SMA50"] < d["SMA200"])

    # --- 2. Kondisi MOMENTUM (Flexible 3-Day Lookback) ---
    macd_cross_up = (d["MACD"] > d["MACD_Signal"]) & (
        d["MACD"].shift(1) <= d["MACD_Signal"].shift(1)
    )
    macd_cross_down = (d["MACD"] < d["MACD_Signal"]) & (
        d["MACD"].shift(1) >= d["MACD_Signal"].shift(1)
    )

    # 3-Day rolling lookback: Cross terjadi dalam 3 bar terakhir (t, t-1, t-2)
    # DAN garis MACD saat ini masih berada di atas Signal Line
    macd_cross_3d = (
        (macd_cross_up.rolling(3, min_periods=1).max() == 1)
        & (d["MACD"] > d["MACD_Signal"])
    )

    # Anti-overbought / Healthy Bull zone: RSI 40-68
    rsi_healthy_bull = (d["RSI14"] >= 40) & (d["RSI14"] <= 68)
    rsi_healthy_bear = (d["RSI14"] <= 60) & (d["RSI14"] >= 30)

    # --- 3. Kondisi VOLUME (Flexible 3-Day Lookback) ---
    # Lonjakan volume >= 1.2x dalam 3 hari terakhir ATAU volume bar saat ini >= 1.1x rata-rata 20 hari
    vol_spike_3d = d["VolRatio20"].rolling(3, min_periods=1).max() >= 1.2
    vol_confirmed = (d["VolRatio20"] >= 1.1) | vol_spike_3d

    # --- 4. Kondisi LOW-RISK ENTRY (Anti-FOMO Buffer) ---
    close_near_sma20 = d["Close"] <= (d["SMA20"] * 1.05)

    # --- 5. Skor Konfirmasi (0-3) ---
    buy_score = (
        uptrend.astype(int)
        + (macd_cross_3d & rsi_healthy_bull).astype(int)
        + vol_confirmed.astype(int)
    )
    sell_score = (
        downtrend.astype(int)
        + (macd_cross_down & rsi_healthy_bear).astype(int)
        + (d["VolRatio20"] >= 1.2).astype(int)
    )

    d["BuyScore"] = buy_score
    d["SellScore"] = sell_score

    signal = pd.Series(0, index=d.index)

    # Syarat BUY Teknis (5 Pilar Terpenuhi dengan Lookback Window 3 Hari)
    buy_valid = uptrend & macd_cross_3d & rsi_healthy_bull & vol_confirmed & close_near_sma20
    signal[buy_valid] = 1

    # Syarat SELL Teknis
    sell_valid = (sell_score >= 2) & (macd_cross_down)
    signal[sell_valid] = -1

    # --- 6. Live Market Regime Gate (HANYA pada bar terakhir, tidak menghapus histori 5 tahun) ---
    tier = regime.get("tier", "HIGH_ALPHA")
    if len(signal) > 0:
        last_sig = signal.iloc[-1]
        if last_sig == 1:
            if tier == "DEFENSIVE":
                # Market sedang dump / momentum merah -> tahan entry baru hari ini
                signal.iloc[-1] = 0
            elif tier == "TACTICAL_SWING":
                # Rezim Tactical Swing (IHSG Bearish tapi Rebound Hijau)
                # Hanya izinkan jika skor konfirmasi maksimal (BuyScore >= 3)
                if buy_score.iloc[-1] < 3:
                    signal.iloc[-1] = 0

    d["Signal"] = signal
    d["SignalStrength"] = np.where(signal == 1, buy_score, np.where(signal == -1, sell_score, 0))

    return d


def latest_signal_summary(d: pd.DataFrame, lookback_days: int = 5) -> dict:
    if d is None or d.empty or len(d) < 60:
        return {
            "last_close": None, "signal": "NO_DATA", "strength": 0,
            "signal_date": None, "rsi": None, "trend": "N/A", "atr": None,
        }

    recent = d.tail(lookback_days)
    last_row = d.iloc[-1]

    active = recent[recent["Signal"] != 0]
    if not active.empty:
        sig_row = active.iloc[-1]
        sig_label = "BUY" if sig_row["Signal"] == 1 else "SELL"
        sig_strength = int(sig_row["SignalStrength"])
        sig_date = sig_row.name
    else:
        sig_label = "HOLD"
        sig_strength = 0
        sig_date = None

    if last_row["Close"] > last_row["SMA50"] > last_row["SMA200"]:
        trend = "Uptrend"
    elif last_row["Close"] < last_row["SMA50"] < last_row["SMA200"]:
        trend = "Downtrend"
    else:
        trend = "Sideways/Mixed"

    return {
        "last_close": round(float(last_row["Close"]), 2),
        "signal": sig_label,
        "strength": sig_strength,
        "signal_date": sig_date,
        "rsi": round(float(last_row["RSI14"]), 1),
        "trend": trend,
        "atr": round(float(last_row["ATR14"]), 2) if not pd.isna(last_row["ATR14"]) else None,
    }
