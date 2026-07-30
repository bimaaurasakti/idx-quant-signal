"""
custom_backtest.py
===================
Signal generation dari kombinasi indikator pilihan user -- generalisasi
dari pola `buy_score >= 2` di signals.py untuk N indikator bebas dipilih
user (bukan 3 kondisi hardcoded).

TIDAK menyentuh signals.py (strategi produksi tetap) sama sekali -- ini
modul TERPISAH khusus Backtest Lab. Lihat IMPLEMENTATION_PLAN_UI_BACKTEST_LAB.md
§3.4 utk penjelasan lengkap algoritma & alasan desainnya.
"""
from __future__ import annotations
import pandas as pd

import indicators as ind
from indicator_registry import INDICATOR_SPECS, default_params_for


def generate_custom_signals(
    df: pd.DataFrame,
    selected_indicators: list[str],
    params: dict[str, dict] | None = None,
    confirmation_threshold: int = 1,
) -> pd.DataFrame:
    """
    df: OHLCV mentah (PascalCase Open/High/Low/Close/Volume), 1 ticker,
        biasanya hasil data_loaders.load_price_history() (kolom lama seperti
        SMA20/RSI14/Signal dari strategi produksi BOLEH ada, akan diabaikan/
        ditimpa -- indikator dihitung ULANG dari OHLCV mentah di sini).
    selected_indicators: list key dari INDICATOR_SPECS (indicator_registry.py).
    params: {indicator_key: {param_name: value}} -- opsional, default dari
        registry dipakai utk param yg tidak disediakan.
    confirmation_threshold: minimal jumlah indikator yg harus "sepakat"
        (searah) di bar yg sama supaya sinyal BUY/SELL dianggap valid.

    Algoritma (Vote & Trigger, lihat §3.4):
      bullish_count[t] = jumlah indikator terpilih yg vote bullish di bar t
      bearish_count[t] = jumlah indikator terpilih yg vote bearish di bar t
      Signal[t] = 1  jika bullish_count[t] >= threshold DAN
                     bullish_count[t-1] < threshold  (momen baru capai ambang)
      Signal[t] = -1 jika kondisi simetris utk bearish_count
      Kalau kedua kondisi trigger di bar sama (jarang): prioritaskan -1
      (SELL) -- filosofi konservatif, kelola risiko turun didahulukan drpd
      buka posisi baru.

    Return: df + kolom hasil compute tiap indikator (prefix "{key}_", dipakai
    chart_builder.py utk overlay/subplot) + 'ATR14' (SELALU dihitung,
    terlepas dari indikator yg dipilih -- dipakai sizing TP/SL oleh
    backtester.backtest_signals(), BUKAN indikator vote) + 'BullishCount' /
    'BearishCount' (utk debugging/transparansi) + 'Signal' (1=BUY,-1=SELL,0=HOLD).
    """
    params = params or {}
    out = df.copy()
    out["ATR14"] = ind.atr(out, 14)  # selalu dihitung, lihat §3.1 rencana implementasi

    if not selected_indicators:
        out["BullishCount"] = 0
        out["BearishCount"] = 0
        out["Signal"] = 0
        return out

    bullish_votes, bearish_votes = [], []
    for key in selected_indicators:
        spec = INDICATOR_SPECS[key]
        p = {**default_params_for(key), **params.get(key, {})}
        value = spec["compute"](out, p, spec)
        bullish, bearish = spec["vote"](out, value, p, spec)
        bullish_votes.append(bullish.fillna(False))
        bearish_votes.append(bearish.fillna(False))
        _attach_chart_columns(out, key, value)

    bullish_count = pd.concat(bullish_votes, axis=1).sum(axis=1)
    bearish_count = pd.concat(bearish_votes, axis=1).sum(axis=1)
    out["BullishCount"] = bullish_count
    out["BearishCount"] = bearish_count

    threshold = max(1, min(confirmation_threshold, len(selected_indicators)))
    prev_bullish = bullish_count.shift(1).fillna(0)
    prev_bearish = bearish_count.shift(1).fillna(0)
    buy_trigger = (bullish_count >= threshold) & (prev_bullish < threshold)
    sell_trigger = (bearish_count >= threshold) & (prev_bearish < threshold)

    signal = pd.Series(0, index=out.index)
    signal[sell_trigger] = -1               # dievaluasi lebih dulu -> tie-break konservatif
    signal[buy_trigger & ~sell_trigger] = 1  # BUY hanya kalau SELL tidak trigger bareng
    out["Signal"] = signal
    return out


def _attach_chart_columns(out: pd.DataFrame, key: str, value) -> None:
    """Simpan hasil compute tiap indikator ke kolom df dgn prefix '{key}_'
    supaya chart_builder.py bisa menggambar overlay/subplot tanpa nabrak
    nama kolom lain (mis. dua indikator beda tetap tidak bentrok nama)."""
    if isinstance(value, pd.DataFrame):
        for col in value.columns:
            out[f"{key}_{col}"] = value[col]
    else:
        out[f"{key}_value"] = value


def validate_min_bars(df: pd.DataFrame, min_bars: int = 60) -> tuple[bool, str]:
    """Cek data (kolom Close) cukup panjang utk backtest bermakna, konsisten
    dgn MIN_BARS_REQUIRED di worker_fetch_and_update.py. Return (ok, pesan)."""
    valid = df["Close"].dropna() if df is not None and not df.empty else pd.Series(dtype=float)
    if len(valid) < min_bars:
        return False, (
            f"Data historis terlalu pendek ({len(valid)} bar valid, minimal {min_bars}) "
            "-- coba periode lebih panjang atau kurangi periode indikator terpanjang yg dipilih."
        )
    return True, ""


def compute_equity_curve(trades: list[dict]) -> pd.Series:
    """Equity curve kumulatif (compounding) dari list trade hasil
    backtester.backtest_signals()['trades'] -- formula identik dgn yg
    dipakai internal backtester.py utk hitung max_drawdown, direplikasi di
    sini krn backtester.py tidak mengembalikan seri equity penuh (cuma
    max_dd akhir), dan kita butuh seri lengkap utk chart equity curve."""
    if not trades:
        return pd.Series(dtype=float)
    returns = pd.Series([t["return_pct"] for t in trades])
    return (1 + returns / 100).cumprod()
