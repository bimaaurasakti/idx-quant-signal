"""
worker_fetch_and_update.py
============================
Script yang dijalankan OTOMATIS oleh GitHub Actions setiap akhir sesi
perdagangan IDX (default: Senin-Jumat, ~16:30 WIB — lihat
.github/workflows/update_after_market_close.yml). Ini SATU-SATUNYA proses
yang boleh menulis ke Supabase (pakai SERVICE ROLE KEY, privat).

Alurnya:
  1. Cek apakah hari ini hari bursa (skip kalau weekend/libur bursa).
  2. Untuk tiap ticker: fetch data harga terbaru (yfinance) -> hitung
     indikator + sinyal + backtest -> tulis ke Supabase (screener_results,
     price_history, backtest_trades) -> update status ongoing position.
  3. Catat ringkasan run ke tabel update_log.

Jalankan manual untuk testing:
    export SUPABASE_URL="https://xxxx.supabase.co"
    export SUPABASE_SERVICE_ROLE_KEY="eyJ....."
    python worker_fetch_and_update.py

PENTING: script ini butuh koneksi internet (yfinance + Supabase REST API).
"""
from __future__ import annotations
import time
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo

from tickers_idx import get_all_tickers, get_sector_of
from data_fetcher import fetch_history
from signals import generate_signals, latest_signal_summary
from backtester import backtest_signals
from idx_calendar import is_trading_day
from position_manager import sync_position
from supabase_client import (
    get_client,
    upsert_screener_result,
    replace_price_history,
    replace_backtest_trades,
    log_update_run,
)

PERIOD = "5y"
MIN_BARS_REQUIRED = 60          # minimal data historis supaya indikator valid
SLEEP_BETWEEN_TICKERS = 0.4     # detik, menghindari rate limit Yahoo Finance


def now_wib() -> datetime:
    return datetime.now(ZoneInfo("Asia/Jakarta"))


def process_one_ticker(client, ticker: str) -> tuple[bool, dict | None]:
    """Return (sukses: bool, aksi_posisi: dict|None)."""
    ticker_clean = ticker.replace(".JK", "")
    raw = fetch_history(ticker, period=PERIOD)
    if raw is None or raw.empty or len(raw) < MIN_BARS_REQUIRED:
        return False, None

    d = generate_signals(raw)
    summary = latest_signal_summary(d)
    bt = backtest_signals(d)

    upsert_screener_result(client, {
        "ticker": ticker_clean,
        "sektor": get_sector_of(ticker_clean),
        "last_close": summary["last_close"],
        "last_date": d.index[-1],
        "signal_today": summary["signal"],
        "signal_strength": summary["strength"],
        "trend": summary["trend"],
        "rsi": summary["rsi"],
        "atr": summary["atr"],
        "winrate": bt["winrate"],
        "expectancy_pct": bt["expectancy_pct"],
        "profit_factor": bt["profit_factor"],
        "max_drawdown_pct": bt["max_drawdown_pct"],
        "n_trades": bt["n_trades"],
        "sharpe_rough": bt["sharpe_rough"],
    })

    replace_price_history(client, ticker_clean, d)
    replace_backtest_trades(client, ticker_clean, bt["trades"])

    action = sync_position(client, ticker_clean, d)
    return True, action


def main():
    start_time = time.time()
    today = now_wib().date()

    if not is_trading_day(today):
        print(f"[SKIP] {today} bukan hari bursa (weekend/libur). Tidak ada update yang dijalankan.")
        try:
            client = get_client(use_service_role=True)
            log_update_run(client, {
                "tickers_processed": 0,
                "tickers_failed": 0,
                "status": "SKIPPED",
                "notes": f"{today} bukan hari bursa (weekend/libur bursa)",
            })
        except Exception as e:
            print(f"[WARN] Gagal mencatat status skip ke Supabase: {e}")
        return

    client = get_client(use_service_role=True)
    all_tickers = get_all_tickers(with_suffix=True)
    print(f"[INFO] Mulai update untuk {len(all_tickers)} ticker pada {today} (WIB)")

    processed, failed = 0, 0
    position_actions = []

    for i, ticker in enumerate(all_tickers, start=1):
        try:
            ok, action = process_one_ticker(client, ticker)
            if ok:
                processed += 1
                tag = f"sinyal={action['type']}" if action else "tidak ada aksi posisi"
                print(f"[{i}/{len(all_tickers)}] {ticker} OK — {tag}")
                if action:
                    position_actions.append(action)
            else:
                failed += 1
                print(f"[{i}/{len(all_tickers)}] {ticker} — data tidak cukup, skip")
        except Exception as e:
            failed += 1
            print(f"[{i}/{len(all_tickers)}] {ticker} GAGAL: {e}")
            traceback.print_exc()

        time.sleep(SLEEP_BETWEEN_TICKERS)

    elapsed = round(time.time() - start_time, 1)
    print(f"[DONE] {processed} sukses, {failed} gagal, {elapsed} detik")
    print(f"[INFO] Total aksi posisi hari ini: {len(position_actions)}")
    for a in position_actions:
        print(f"        - {a}")

    try:
        log_update_run(client, {
            "tickers_processed": processed,
            "tickers_failed": failed,
            "status": "OK" if processed > 0 else "FAILED",
            "notes": f"{len(position_actions)} aksi posisi | {elapsed}s",
        })
    except Exception as e:
        print(f"[WARN] Gagal mencatat ringkasan run ke Supabase: {e}")


if __name__ == "__main__":
    main()
