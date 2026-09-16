"""
Signal engine: multi-confirmation trend-following system.

Filosofi: alih-alih satu indikator tunggal (yang gampang false-signal),
sinyal BUY/SELL hanya muncul kalau BEBERAPA konfirmasi independen searah:

  1. TREND      -> harga di atas SMA50 & SMA50 di atas SMA200 (uptrend struktural)
  2. MOMENTUM   -> MACD histogram positif & baru cross naik, RSI di zona sehat (40-70)
  3. VOLUME     -> volume hari sinyal di atas rata-rata (konfirmasi partisipasi pasar)

Pendekatan ini secara empiris cenderung menghasilkan winrate lebih stabil
karena mengurangi false signal, dengan trade-off: sinyal lebih jarang muncul
(lebih sedikit trade) dibanding sinyal indikator tunggal.

TIDAK ADA jaminan profit. Semua angka winrate/expectancy di dashboard ini
dihitung dari backtest historis pada data yfinance — performa masa lalu
tidak menjamin hasil masa depan.
"""
from __future__ import annotations
import pandas as pd
import numpy as np

from indicators import add_all_indicators


def check_ihsg_regime(ihsg_df: pd.DataFrame | None) -> bool:
    """
    Evaluasi Macro Market Regime dari IHSG (^JKSE):
    True jika IHSG berada di atas SMA200 (Risk-On / Bull Market).
    False jika IHSG berada di bawah SMA200 (Risk-Off / Defensive).
    Jika data tidak tersedia (None/empty), return True agar tidak hard-block.
    """
    if ihsg_df is None or ihsg_df.empty or len(ihsg_df) < 200:
        return True
    close = ihsg_df["Close"]
    sma200 = close.rolling(200, min_periods=200).mean()
    last_close = close.iloc[-1]
    last_sma200 = sma200.iloc[-1]
    if pd.isna(last_sma200):
        return True
    return bool(last_close >= last_sma200)


def generate_signals(df: pd.DataFrame, market_bullish: bool = True) -> pd.DataFrame:
    """
    Input: DataFrame OHLCV mentah.
    Output: DataFrame dengan indikator + kolom 'Signal' (1=BUY, -1=SELL, 0=HOLD)
    dan kolom 'SignalStrength' (0-3, jumlah konfirmasi yang terpenuhi).

    Syarat BUY diperketat (Hard Gate):
      1. HARD GATE TREND: Wajib Close > SMA50 dan SMA50 > SMA200 (anti falling-knife).
      2. MOMENTUM: MACD Bullish Crossover & RSI sehat non-overbought (40-65).
      3. VOLUME: Volume hari sinyal >= 1.2x rata-rata 20 hari.
      4. ANTI-FOMO: Close <= SMA20 * 1.05 (tidak membeli saham yang sudah terbang jauh).
      5. MARKET REGIME: IHSG harus Risk-On (market_bullish == True).
    """
    d = add_all_indicators(df)

    # --- Kondisi TREND (Hard Gate) ---
    uptrend = (d["Close"] > d["SMA50"]) & (d["SMA50"] > d["SMA200"])
    downtrend = (d["Close"] < d["SMA50"]) & (d["SMA50"] < d["SMA200"])

    # --- Kondisi MOMENTUM ---
    macd_cross_up = (d["MACD"] > d["MACD_Signal"]) & (
        d["MACD"].shift(1) <= d["MACD_Signal"].shift(1)
    )
    macd_cross_down = (d["MACD"] < d["MACD_Signal"]) & (
        d["MACD"].shift(1) >= d["MACD_Signal"].shift(1)
    )
    # Anti-overbought: RSI 40-65 (tidak boleh mengejar saham overbought > 65)
    rsi_healthy_bull = (d["RSI14"] >= 40) & (d["RSI14"] <= 65)
    rsi_healthy_bear = (d["RSI14"] <= 60) & (d["RSI14"] >= 30)

    # --- Kondisi VOLUME ---
    volume_confirmed = d["VolRatio20"] >= 1.2  # 20% di atas rata-rata 20 hari

    # --- Kondisi LOW-RISK ENTRY (Anti-FOMO) ---
    close_near_sma20 = d["Close"] <= (d["SMA20"] * 1.05)

    # --- Skor konfirmasi (0-3) ---
    buy_score = (
        uptrend.astype(int)
        + (macd_cross_up & rsi_healthy_bull).astype(int)
        + volume_confirmed.astype(int)
    )
    sell_score = (
        downtrend.astype(int)
        + (macd_cross_down & rsi_healthy_bear).astype(int)
        + volume_confirmed.astype(int)
    )

    d["BuyScore"] = buy_score
    d["SellScore"] = sell_score

    signal = pd.Series(0, index=d.index)
    # BUY hanya jika SEMUA syarat terpenuhi (Hard Gate Uptrend & Anti-FOMO)
    buy_valid = uptrend & macd_cross_up & rsi_healthy_bull & volume_confirmed & close_near_sma20
    if not market_bullish:
        buy_valid = pd.Series(False, index=d.index)

    signal[buy_valid] = 1
    signal[(sell_score >= 2) & (macd_cross_down)] = -1
    d["Signal"] = signal
    d["SignalStrength"] = np.where(signal == 1, buy_score, np.where(signal == -1, sell_score, 0))

    return d


def latest_signal_summary(d: pd.DataFrame, lookback_days: int = 5) -> dict:
    """
    Ringkasan sinyal terbaru untuk ditampilkan di tabel screener.
    Cari sinyal BUY/SELL dalam `lookback_days` hari terakhir (bukan cuma hari ini),
    supaya sinyal yang baru muncul kemarin tetap kelihatan.
    """
    if d is None or d.empty or len(d) < 60:
        return {
            "last_close": None, "signal": "NO_DATA", "strength": 0,
            "signal_date": None, "rsi": None, "trend": "N/A",
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
