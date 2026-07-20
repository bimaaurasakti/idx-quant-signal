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


def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Input: DataFrame OHLCV mentah.
    Output: DataFrame dengan indikator + kolom 'Signal' (1=BUY, -1=SELL, 0=HOLD)
    dan kolom 'SignalStrength' (0-3, jumlah konfirmasi yang terpenuhi).
    """
    d = add_all_indicators(df)

    # --- Kondisi TREND ---
    uptrend = (d["Close"] > d["SMA50"]) & (d["SMA50"] > d["SMA200"])
    downtrend = (d["Close"] < d["SMA50"]) & (d["SMA50"] < d["SMA200"])

    # --- Kondisi MOMENTUM ---
    macd_cross_up = (d["MACD"] > d["MACD_Signal"]) & (
        d["MACD"].shift(1) <= d["MACD_Signal"].shift(1)
    )
    macd_cross_down = (d["MACD"] < d["MACD_Signal"]) & (
        d["MACD"].shift(1) >= d["MACD_Signal"].shift(1)
    )
    rsi_healthy_bull = (d["RSI14"] >= 40) & (d["RSI14"] <= 70)
    rsi_healthy_bear = (d["RSI14"] <= 60) & (d["RSI14"] >= 30)

    # --- Kondisi VOLUME ---
    volume_confirmed = d["VolRatio20"] >= 1.2  # 20% di atas rata-rata 20 hari

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
    # BUY hanya jika minimal trend + momentum confirm (score >= 2), sell serupa
    signal[(buy_score >= 2) & (macd_cross_up)] = 1
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
