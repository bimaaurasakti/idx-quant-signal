"""
Position manager — mengelola siklus hidup "ongoing position" per emiten.

ATURAN KERAS (sesuai requirement):
  1. LONG-ONLY. Modul ini HANYA membuka posisi saat Signal == 1 (BUY).
     Signal == -1 (SELL) TIDAK PERNAH dipakai sebagai trigger entry —
     hanya dipakai sebagai salah satu kondisi EXIT dari posisi long yang
     sudah terbuka. Pasar Indonesia (reguler) tidak mengizinkan short.
  2. MAKS 1 POSISI AKTIF PER EMITEN. Sebelum membuka posisi baru, modul ini
     selalu cek dulu apakah sudah ada posisi berstatus PENDING_ENTRY/OPEN
     untuk ticker tsb. Constraint ini di-enforce DUA lapis: di sini (logic)
     dan di schema.sql (partial unique index) sebagai pengaman kedua.

Siklus status:
  PENDING_ENTRY  -> sinyal BUY baru saja muncul di bar terakhir; menunggu
                     dieksekusi di open hari bursa berikutnya.
  OPEN           -> sudah entry (planned_entry_date tercapai), TP/SL aktif.
  CLOSED_TP      -> keluar karena harga kena Take Profit.
  CLOSED_SL      -> keluar karena harga kena Stop Loss.
  CLOSED_SIGNAL  -> keluar karena sinyal SELL muncul sebelum TP/SL kena.
  CLOSED_TIME    -> keluar karena batas waktu maksimum holding tercapai.

Posisi dengan status CLOSED_* otomatis tidak lagi muncul di tampilan
"Ongoing Position" (app.py hanya query status PENDING_ENTRY/OPEN) — sesuai
requirement "hilangkan dari ongoing position kalau sudah TP/SL".
"""
from __future__ import annotations
import pandas as pd

from idx_calendar import next_trading_day
from backtester import R_MULTIPLE_TP, SL_ATR_MULT, MAX_HOLD_DAYS
from supabase_client import get_active_position, insert_position, update_position


def sync_position(client, ticker: str, d: pd.DataFrame) -> dict | None:
    """
    Dipanggil sekali per ticker, sekali per hari bursa (dari worker), SETELAH
    generate_signals() dijalankan pada data historis terbaru.

    d: DataFrame dengan index=DatetimeIndex terurut naik, minimal kolom
       Open/High/Low/Close, ATR14, Signal.

    Return: dict ringkasan aksi (untuk logging) atau None kalau tidak ada
    perubahan status.
    """
    if d is None or d.empty:
        return None

    last_row = d.iloc[-1]
    last_date = d.index[-1]
    last_date = last_date.date() if hasattr(last_date, "date") else last_date

    active = get_active_position(client, ticker)

    if active is not None:
        return _handle_existing_position(client, ticker, active, last_row, last_date)

    return _maybe_open_new_position(client, ticker, last_row, last_date)


def _handle_existing_position(client, ticker, active, last_row, last_date) -> dict | None:
    status = active["status"]

    if status == "PENDING_ENTRY":
        planned = _to_date(active["planned_entry_date"])
        if last_date < planned:
            return None  # belum waktunya entry

        # Hari ini >= planned_entry_date -> eksekusi entry di harga Open hari ini.
        entry_price = float(last_row["Open"])
        atr_signal = float(active["atr_at_signal"])
        tp_price = entry_price + R_MULTIPLE_TP * atr_signal
        sl_price = entry_price - SL_ATR_MULT * atr_signal

        update_position(client, active["id"], {
            "status": "OPEN",
            "entry_date": last_date,
            "entry_price": entry_price,
            "tp_price": tp_price,
            "sl_price": sl_price,
        })
        # Sengaja TIDAK langsung cek TP/SL di hari entry yang sama —
        # konsisten dengan backtester.py yang mulai cek exit dari H+1 setelah entry.
        return {"type": "ENTERED", "ticker": ticker, "entry_price": round(entry_price, 2)}

    if status == "OPEN":
        entry_date = _to_date(active["entry_date"])
        if entry_date is not None and last_date <= entry_date:
            return None  # hari yang sama dengan entry, belum dicek

        high = float(last_row["High"])
        low = float(last_row["Low"])
        close = float(last_row["Close"])
        tp_price = float(active["tp_price"])
        sl_price = float(active["sl_price"])
        entry_price = float(active["entry_price"])
        hold_days = (last_date - entry_date).days if entry_date else 0

        exit_price, reason = None, None
        # SL dicek lebih dulu dari TP (asumsi konservatif kalau keduanya
        # kena di hari yang sama) -> konsisten dengan backtester.py
        if low <= sl_price:
            exit_price, reason = sl_price, "CLOSED_SL"
        elif high >= tp_price:
            exit_price, reason = tp_price, "CLOSED_TP"
        elif int(last_row["Signal"]) == -1:
            exit_price, reason = close, "CLOSED_SIGNAL"
        elif hold_days >= MAX_HOLD_DAYS:
            exit_price, reason = close, "CLOSED_TIME"

        if reason is None:
            return None  # posisi tetap terbuka, tidak ada perubahan

        return_pct = (exit_price - entry_price) / entry_price * 100
        update_position(client, active["id"], {
            "status": reason,
            "exit_date": last_date,
            "exit_price": exit_price,
            "exit_reason": reason,
            "return_pct": round(return_pct, 2),
        })
        return {"type": reason, "ticker": ticker, "return_pct": round(return_pct, 2)}

    return None  # status tidak dikenal, jangan lakukan apa-apa


def _maybe_open_new_position(client, ticker, last_row, last_date) -> dict | None:
    # LONG-ONLY: satu-satunya trigger pembukaan posisi adalah Signal == 1.
    if int(last_row["Signal"]) != 1:
        return None

    atr_val = last_row.get("ATR14")
    if atr_val is None or pd.isna(atr_val):
        return None  # ATR belum tersedia (data historis terlalu pendek), skip

    planned_entry = next_trading_day(last_date)
    insert_position(client, {
        "ticker": ticker,
        "status": "PENDING_ENTRY",
        "signal_date": last_date,
        "planned_entry_date": planned_entry,
        "atr_at_signal": float(atr_val),
    })
    return {"type": "NEW_SIGNAL", "ticker": ticker, "planned_entry_date": str(planned_entry)}


def _to_date(v):
    if v is None:
        return None
    if isinstance(v, str):
        return pd.to_datetime(v).date()
    if hasattr(v, "date"):
        return v.date()
    return v
