"""
Pengambilan data harga saham IDX via yfinance, dengan retry sederhana untuk
menghadapi rate limit / error sementara dari Yahoo Finance.
"""
from __future__ import annotations
import time
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

import pandas as pd

try:
    import yfinance as yf
except ImportError:
    yf = None

YFINANCE_TIMEOUT = 60  # detik per panggilan yfinance, cegah hang forever

logger = logging.getLogger("idx_quant.data_fetcher")


def fetch_history(
    ticker: str,
    period: str = "2y",
    interval: str = "1d",
    max_retries: int = 3,
    retry_delay: float = 2.0,
) -> pd.DataFrame | None:
    """
    Ambil data historis satu ticker, dengan retry otomatis (exponential backoff).
    """
    if yf is None:
        raise RuntimeError(
            "Library 'yfinance' belum terinstall. Jalankan: pip install yfinance"
        )

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            t = yf.Ticker(ticker)
            pool = ThreadPoolExecutor(max_workers=1)
            try:
                fut = pool.submit(
                    t.history, period=period, interval=interval, auto_adjust=True
                )
                df = fut.result(timeout=YFINANCE_TIMEOUT)
            finally:
                pool.shutdown(wait=False)
            if df is None or df.empty:
                logger.warning("Data kosong untuk %s (attempt %d)", ticker, attempt)
                return None
            return df.dropna(subset=["Close"])
        except FuturesTimeout:
            last_error = TimeoutError(
                f"yfinance timeout {YFINANCE_TIMEOUT}s (attempt {attempt}/{max_retries})"
            )
            logger.warning(
                "Timeout fetch %s (attempt %d/%d) — %ss exceeded",
                ticker, attempt, max_retries, YFINANCE_TIMEOUT,
            )
            if attempt < max_retries:
                time.sleep(retry_delay * attempt)
        except Exception as e:
            last_error = e
            logger.warning(
                "Gagal fetch %s (attempt %d/%d): %s", ticker, attempt, max_retries, e
            )
            if attempt < max_retries:
                time.sleep(retry_delay * attempt)

    logger.warning("Fetch %s gagal total setelah %d percobaan: %s", ticker, max_retries, last_error)
    return None


def fetch_many(
    tickers: list[str],
    period: str = "2y",
    interval: str = "1d",
    sleep_between: float = 0.4,
    progress_callback=None,
) -> dict[str, pd.DataFrame]:
    results: dict[str, pd.DataFrame] = {}
    total = len(tickers)
    for i, ticker in enumerate(tickers, start=1):
        df = fetch_history(ticker, period=period, interval=interval)
        if df is not None and not df.empty:
            results[ticker] = df
        if sleep_between > 0:
            time.sleep(sleep_between)
        if progress_callback:
            progress_callback(i, total, ticker)
    return results
