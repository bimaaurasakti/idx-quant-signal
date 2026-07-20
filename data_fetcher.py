"""
Pengambilan data harga saham IDX via yfinance, dengan cache lokal (parquet)
supaya tidak berulang kali hit Yahoo Finance (menghindari rate limit /
YFRateLimitError) dan mempercepat reload dashboard.

Referensi API: yfinance v1.5.1
- yf.Ticker(ticker).history(period=..., interval=...)  -> DataFrame OHLCV
- yf.download(tickers, period=..., interval=..., group_by='ticker')
"""
from __future__ import annotations
import os
import time
import logging
from datetime import datetime, timedelta

import pandas as pd

try:
    import yfinance as yf
except ImportError:
    yf = None  # ditangani di app.py dengan pesan error yang jelas

CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")
os.makedirs(CACHE_DIR, exist_ok=True)

logger = logging.getLogger("idx_quant.data_fetcher")


def _cache_path(ticker: str, period: str, interval: str) -> str:
    safe = ticker.replace("/", "_")
    return os.path.join(CACHE_DIR, f"{safe}_{period}_{interval}.parquet")


def _cache_is_fresh(path: str, max_age_hours: float = 6.0) -> bool:
    if not os.path.exists(path):
        return False
    mtime = datetime.fromtimestamp(os.path.getmtime(path))
    return datetime.now() - mtime < timedelta(hours=max_age_hours)


def fetch_history(
    ticker: str,
    period: str = "2y",
    interval: str = "1d",
    use_cache: bool = True,
    max_age_hours: float = 6.0,
) -> pd.DataFrame | None:
    """
    Ambil data historis satu ticker. Return None jika gagal/kosong
    (misalnya ticker delisted atau tidak ditemukan di Yahoo Finance).
    """
    if yf is None:
        raise RuntimeError(
            "Library 'yfinance' belum terinstall. Jalankan: pip install yfinance"
        )

    path = _cache_path(ticker, period, interval)
    if use_cache and _cache_is_fresh(path, max_age_hours):
        try:
            return pd.read_parquet(path)
        except Exception:
            pass  # cache korup, fetch ulang

    try:
        t = yf.Ticker(ticker)
        df = t.history(period=period, interval=interval, auto_adjust=True)
        if df is None or df.empty:
            logger.warning("Data kosong untuk %s", ticker)
            return None
        df = df.dropna(subset=["Close"])
        if use_cache:
            try:
                df.to_parquet(path)
            except Exception as e:
                logger.warning("Gagal simpan cache untuk %s: %s", ticker, e)
        return df
    except Exception as e:
        logger.warning("Gagal fetch %s: %s", ticker, e)
        return None


def fetch_many(
    tickers: list[str],
    period: str = "2y",
    interval: str = "1d",
    use_cache: bool = True,
    max_age_hours: float = 6.0,
    sleep_between: float = 0.0,
    progress_callback=None,
) -> dict[str, pd.DataFrame]:
    """
    Ambil data historis untuk banyak ticker satu per satu (lebih aman dari
    rate limit dibanding yf.download() batch untuk jumlah ticker besar).

    progress_callback(i, total, ticker) dipanggil setelah tiap ticker selesai,
    berguna untuk update progress bar di Streamlit.
    """
    results: dict[str, pd.DataFrame] = {}
    total = len(tickers)
    for i, ticker in enumerate(tickers, start=1):
        df = fetch_history(
            ticker, period=period, interval=interval,
            use_cache=use_cache, max_age_hours=max_age_hours,
        )
        if df is not None and not df.empty:
            results[ticker] = df
        if sleep_between > 0:
            time.sleep(sleep_between)
        if progress_callback:
            progress_callback(i, total, ticker)
    return results


def fetch_info_safe(ticker: str) -> dict:
    """Ambil ticker.info dengan fallback aman kalau error/kosong."""
    if yf is None:
        return {}
    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
        return info
    except Exception as e:
        logger.warning("Gagal fetch info %s: %s", ticker, e)
        return {}
