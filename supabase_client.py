"""
Lapisan akses Supabase — satu-satunya tempat kode lain boleh bicara ke Supabase.

Dua mode client:
  - use_service_role=False (ANON KEY) -> dipakai app.py (publik, HANYA baca).
    Kunci ini aman ditaruh di Streamlit secrets karena RLS di schema.sql
    cuma mengizinkan SELECT untuk role anon.
  - use_service_role=True  (SERVICE ROLE KEY) -> dipakai worker_fetch_and_update.py
    (GitHub Actions, privat). Key ini BYPASS RLS sepenuhnya -> JANGAN PERNAH
    taruh di kode publik/Streamlit secrets. Hanya sebagai GitHub Actions secret.

Kredensial dicari dari (urutan prioritas):
  1. Environment variable (works untuk GitHub Actions & local dev)
  2. st.secrets (works untuk Streamlit Community Cloud)
  3. secrets.toml di root project (local dev — file ini SUDAH di .gitignore)
"""
from __future__ import annotations
import os
import math
import logging
from typing import Any

import pandas as pd

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = None

logger = logging.getLogger("idx_quant.supabase_client")

_SECRETS_TOML_CACHE: dict[str, str] | None = None


def _load_secrets_toml() -> dict[str, str]:
    global _SECRETS_TOML_CACHE
    if _SECRETS_TOML_CACHE is not None:
        return _SECRETS_TOML_CACHE
    import tomllib

    path = os.path.join(os.getcwd(), "secrets.toml")
    try:
        with open(path, "rb") as f:
            _SECRETS_TOML_CACHE = tomllib.load(f)
    except (FileNotFoundError, PermissionError):
        _SECRETS_TOML_CACHE = {}
    return _SECRETS_TOML_CACHE


# ----------------------------------------------------------------------
# Client construction
# ----------------------------------------------------------------------
def _get_secret(name: str) -> str | None:
    # 1. Environment variable
    val = os.environ.get(name)
    if val:
        return val
    # 2. Streamlit secrets (Community Cloud)
    try:
        import streamlit as st
        if hasattr(st, "secrets") and name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    # 3. secrets.toml root project (local dev)
    return _load_secrets_toml().get(name)


class _ServiceRoleClient:
    """Minimal wrapper — menyediakan .table() seperti SupabaseClient, tapi
    menggunakan SyncPostgrestClient langsung dengan service_role key di header
    Authorization. Me-bypass bug supabase-py v2.x yang tidak menghormati
    service_role key (RLS tetap di-enforce)."""

    def __init__(self, postgrest_client: Any) -> None:
        self._postgrest = postgrest_client

    def table(self, name: str) -> Any:
        return self._postgrest.from_(name)


def get_client(use_service_role: bool = False) -> Any:
    """Return SupabaseClient (anon) atau _ServiceRoleClient (service_role).

    Service_role mode pake PostgREST langsung, bukan create_client(), karena
    supabase-py v2.x gagal bypass RLS via service_role key.
    """
    url = _get_secret("SUPABASE_URL")
    key_name = "SUPABASE_SERVICE_ROLE_KEY" if use_service_role else "SUPABASE_ANON_KEY"
    key = _get_secret(key_name)

    if not url or not key:
        raise RuntimeError(
            f"Kredensial Supabase belum diset. Butuh SUPABASE_URL dan {key_name} "
            "sebagai environment variable atau di st.secrets. Lihat README.md."
        )

    if use_service_role:
        from postgrest import SyncPostgrestClient

        rest_url = f"{url.rstrip('/')}/rest/v1"
        pg = SyncPostgrestClient(
            rest_url,
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
            },
        )
        return _ServiceRoleClient(pg)

    if create_client is None:
        raise RuntimeError(
            "Library 'supabase' belum terinstall. Jalankan: pip install supabase"
        )
    return create_client(url, key)


# ----------------------------------------------------------------------
# Helpers: sanitasi nilai sebelum dikirim ke Supabase (JSON tidak terima NaN)
# ----------------------------------------------------------------------
def _safe_float(v: Any) -> float | None:
    try:
        if v is None:
            return None
        f = float(v)
        return None if (math.isnan(f) or math.isinf(f)) else round(f, 4)
    except (TypeError, ValueError):
        return None


def _safe_int(v: Any) -> int | None:
    try:
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return None
        return int(v)
    except (TypeError, ValueError):
        return None


def _date_str(d: Any) -> str | None:
    if d is None:
        return None
    if hasattr(d, "strftime"):
        return d.strftime("%Y-%m-%d")
    return str(d)


def _bulk_insert_chunked(table_query, records: list[dict], chunk_size: int = 500) -> None:
    for i in range(0, len(records), chunk_size):
        chunk = records[i:i + chunk_size]
        if chunk:
            table_query.insert(chunk).execute()


# ----------------------------------------------------------------------
# WRITE operations (dipakai worker, butuh service_role client)
# ----------------------------------------------------------------------
def upsert_screener_result(client, row: dict) -> None:
    clean = {
        "ticker": row["ticker"],
        "sektor": row.get("sektor"),
        "last_close": _safe_float(row.get("last_close")),
        "last_date": _date_str(row.get("last_date")),
        "signal_today": row.get("signal_today"),
        "signal_strength": _safe_int(row.get("signal_strength")),
        "trend": row.get("trend"),
        "rsi": _safe_float(row.get("rsi")),
        "atr": _safe_float(row.get("atr")),
        "winrate": _safe_float(row.get("winrate")),
        "expectancy_pct": _safe_float(row.get("expectancy_pct")),
        "profit_factor": _safe_float(row.get("profit_factor")),
        "max_drawdown_pct": _safe_float(row.get("max_drawdown_pct")),
        "n_trades": _safe_int(row.get("n_trades")),
        "sharpe_rough": _safe_float(row.get("sharpe_rough")),
        "is_idx30": bool(row.get("is_idx30", False)),
        "is_lq45": bool(row.get("is_lq45", False)),
    }
    client.table("screener_results").upsert(clean, on_conflict="ticker").execute()


def replace_price_history(client, ticker: str, d: pd.DataFrame) -> None:
    """Hapus semua baris price_history utk ticker ini, lalu insert ulang dari DataFrame d
    (hasil generate_signals(), index=DatetimeIndex)."""
    client.table("price_history").delete().eq("ticker", ticker).execute()

    records = []
    for idx, row in d.iterrows():
        records.append({
            "ticker": ticker,
            "date": _date_str(idx),
            "open": _safe_float(row.get("Open")),
            "high": _safe_float(row.get("High")),
            "low": _safe_float(row.get("Low")),
            "close": _safe_float(row.get("Close")),
            "volume": _safe_int(row.get("Volume")),
            "sma20": _safe_float(row.get("SMA20")),
            "sma50": _safe_float(row.get("SMA50")),
            "sma200": _safe_float(row.get("SMA200")),
            "rsi14": _safe_float(row.get("RSI14")),
            "macd": _safe_float(row.get("MACD")),
            "macd_signal": _safe_float(row.get("MACD_Signal")),
            "macd_hist": _safe_float(row.get("MACD_Hist")),
            "atr14": _safe_float(row.get("ATR14")),
            "signal": _safe_int(row.get("Signal", 0)),
        })
    _bulk_insert_chunked(client.table("price_history"), records)


def replace_backtest_trades(client, ticker: str, trades: list[dict]) -> None:
    client.table("backtest_trades").delete().eq("ticker", ticker).execute()
    if not trades:
        return
    records = [{
        "ticker": ticker,
        "entry_date": _date_str(t["entry_date"]),
        "exit_date": _date_str(t["exit_date"]),
        "entry_price": _safe_float(t["entry_price"]),
        "exit_price": _safe_float(t["exit_price"]),
        "return_pct": _safe_float(t["return_pct"]),
        "reason": t["reason"],
        "hold_days": _safe_int(t["hold_days"]),
    } for t in trades]
    _bulk_insert_chunked(client.table("backtest_trades"), records)


def get_active_position(client, ticker: str) -> dict | None:
    """Posisi aktif (PENDING_ENTRY atau OPEN) untuk 1 ticker. None kalau tidak ada."""
    resp = (
        client.table("ongoing_positions")
        .select("*")
        .eq("ticker", ticker)
        .in_("status", ["PENDING_ENTRY", "OPEN"])
        .execute()
    )
    rows = resp.data or []
    return rows[0] if rows else None


def insert_position(client, row: dict) -> None:
    clean = {
        "ticker": row["ticker"],
        "status": row["status"],
        "signal_date": _date_str(row.get("signal_date")),
        "planned_entry_date": _date_str(row.get("planned_entry_date")),
        "atr_at_signal": _safe_float(row.get("atr_at_signal")),
    }
    client.table("ongoing_positions").insert(clean).execute()


def update_position(client, position_id, updates: dict) -> None:
    clean = {}
    for k, v in updates.items():
        if k in ("entry_date", "exit_date", "signal_date", "planned_entry_date"):
            clean[k] = _date_str(v)
        elif k in ("entry_price", "exit_price", "tp_price", "sl_price", "atr_at_signal", "return_pct"):
            clean[k] = _safe_float(v)
        else:
            clean[k] = v
    client.table("ongoing_positions").update(clean).eq("id", position_id).execute()


def log_update_run(client, summary: dict) -> None:
    client.table("update_log").insert({
        "tickers_processed": _safe_int(summary.get("tickers_processed")),
        "tickers_failed": _safe_int(summary.get("tickers_failed")),
        "status": summary.get("status"),
        "notes": summary.get("notes"),
    }).execute()


# ----------------------------------------------------------------------
# READ operations (dipakai app.py, cukup anon client)
# ----------------------------------------------------------------------
def _coerce_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """PostgREST kadang mengembalikan kolom `numeric` sebagai string (bukan
    JSON number) tergantung konfigurasi, supaya presisi tidak hilang. Paksa
    ke float di sisi client supaya sorting/formatting/SUM() di app.py aman
    terlepas dari perilaku serialisasi itu."""
    for c in columns:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def fetch_active_position_tickers(client) -> list[str]:
    """Ticker (TANPA suffix .JK) yang sedang berstatus PENDING_ENTRY atau
    OPEN. Dipakai worker_fetch_and_update.py untuk 'grandfathering': ticker
    yang sudah di luar default universe (IDX30/LQ45 terbaru, lihat
    tickers_idx.py) tapi masih punya posisi aktif tetap di-fetch & di-update
    sampai posisinya closed secara alami -- supaya tidak ada posisi live
    yang 'ditinggal' begitu saja hanya karena rebalancing indeks BEI
    mengeluarkan tickernya dari LQ45/IDX30. Lihat IMPLEMENTATION_PLAN
    Bagian 2.4."""
    resp = (
        client.table("ongoing_positions").select("ticker")
        .in_("status", ["PENDING_ENTRY", "OPEN"]).execute()
    )
    rows = resp.data or []
    return sorted({r["ticker"] for r in rows})


def fetch_screener_results(client) -> pd.DataFrame:
    resp = client.table("screener_results").select("*").execute()
    df = pd.DataFrame(resp.data or [])
    return _coerce_numeric(df, [
        "last_close", "signal_strength", "rsi", "atr", "winrate",
        "expectancy_pct", "profit_factor", "max_drawdown_pct", "n_trades", "sharpe_rough",
    ])


def fetch_price_history(client, ticker: str) -> pd.DataFrame:
    resp = (
        client.table("price_history").select("*")
        .eq("ticker", ticker).order("date").execute()
    )
    df = pd.DataFrame(resp.data or [])
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date").sort_index()
        # samakan nama kolom dengan konvensi indicators.py/signals.py (PascalCase)
        df = df.rename(columns={
            "open": "Open", "high": "High", "low": "Low", "close": "Close",
            "volume": "Volume", "signal": "Signal",
            "sma20": "SMA20", "sma50": "SMA50", "sma200": "SMA200",
            "rsi14": "RSI14", "macd": "MACD", "macd_signal": "MACD_Signal",
            "macd_hist": "MACD_Hist", "atr14": "ATR14",
        })
        df = _coerce_numeric(df, [
            "Open", "High", "Low", "Close", "Volume", "SMA20", "SMA50", "SMA200",
            "RSI14", "MACD", "MACD_Signal", "MACD_Hist", "ATR14", "Signal",
        ])
    return df


def fetch_backtest_trades(client, ticker: str) -> pd.DataFrame:
    resp = (
        client.table("backtest_trades").select("*")
        .eq("ticker", ticker).order("entry_date").execute()
    )
    df = pd.DataFrame(resp.data or [])
    return _coerce_numeric(df, ["entry_price", "exit_price", "return_pct", "hold_days"])


def fetch_ongoing_positions(client, statuses: list[str]) -> pd.DataFrame:
    resp = (
        client.table("ongoing_positions").select("*")
        .in_("status", statuses).execute()
    )
    df = pd.DataFrame(resp.data or [])
    return _coerce_numeric(df, [
        "atr_at_signal", "entry_price", "tp_price", "sl_price", "exit_price", "return_pct",
    ])


CLOSED_POSITION_STATUSES = ["CLOSED_TP", "CLOSED_SL", "CLOSED_SIGNAL", "CLOSED_TIME"]


def fetch_closed_positions(client, statuses: list[str] | None = None) -> pd.DataFrame:
    """Riwayat posisi yang SUDAH closed (TP/SL/SIGNAL/TIME) dari ongoing_positions.

    PENTING — ini BEDA dengan backtest_trades:
    - backtest_trades = simulasi ulang SELURUH histori, di-REPLACE tiap worker run.
    - Tabel ini (ongoing_positions status closed) = jejak sinyal LIVE, di-APPEND
      satu-satu tiap kali sebuah posisi real-time benar-benar closed. Tidak pernah
      direvisi ke belakang. Ini genuine forward-testing track record — dipakai
      di tab Portfolio (app.py) sebagai bahan evaluasi strategi yang lebih jujur
      dibanding backtest_trades.
    """
    statuses = statuses or CLOSED_POSITION_STATUSES
    resp = (
        client.table("ongoing_positions").select("*")
        .in_("status", statuses)
        .order("exit_date", desc=True)
        .execute()
    )
    df = pd.DataFrame(resp.data or [])
    return _coerce_numeric(df, [
        "atr_at_signal", "entry_price", "tp_price", "sl_price", "exit_price", "return_pct",
    ])


def fetch_position_for_ticker(client, ticker: str, statuses: list[str] | None = None) -> pd.DataFrame:
    q = client.table("ongoing_positions").select("*").eq("ticker", ticker)
    if statuses:
        q = q.in_("status", statuses)
    resp = q.order("created_at", desc=True).execute()
    return pd.DataFrame(resp.data or [])


def fetch_last_update(client) -> dict | None:
    resp = (
        client.table("update_log").select("*")
        .order("run_at", desc=True).limit(1).execute()
    )
    rows = resp.data or []
    return rows[0] if rows else None
