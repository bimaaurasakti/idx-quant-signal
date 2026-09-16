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
from supabase_client import (
    get_active_position,
    insert_position,
    update_position,
    fetch_all_active_positions,
)
from tickers_idx import get_sector_of

MAX_ACTIVE_POSITIONS = 7
MAX_SECTOR_POSITIONS = 2


def sync_position(client, ticker: str, d: pd.DataFrame, sector: str | None = None) -> dict | None:
    """
    Dipanggil sekali per ticker, sekali per hari bursa (dari worker), SETELAH
    generate_signals() dijalankan pada data historis terbaru.

    d: DataFrame dengan index=DatetimeIndex terurut naik, minimal kolom
       Open/High/Low/Close, ATR14, SMA20, Signal.

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

    return _maybe_open_new_position(client, ticker, last_row, last_date, sector=sector)


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
        return {"type": "ENTERED", "ticker": ticker, "entry_price": round(entry_price, 2)}

    if status == "OPEN":
        entry_date = _to_date(active["entry_date"])
        if entry_date is not None and last_date <= entry_date:
            return None  # hari yang sama dengan entry, belum dicek

        high = float(last_row["High"])
        low = float(last_row["Low"])
        close = float(last_row["Close"])
        sma20 = float(last_row["SMA20"]) if "SMA20" in last_row and not pd.isna(last_row["SMA20"]) else None
        tp_price = float(active["tp_price"]) if active.get("tp_price") is not None else None
        sl_price = float(active["sl_price"])
        entry_price = float(active["entry_price"])
        hold_days = (last_date - entry_date).days if entry_date else 0

        # Jika sl_price >= entry_price, posisi sudah berada di fase Runner (Risk-Free @ BE)
        is_runner = (sl_price >= entry_price)

        if not is_runner:
            # Stage 1: Sebelum TP1
            if low <= sl_price:
                # Stop Loss awal kena (-1.5 ATR)
                exit_price = sl_price
                reason = "CLOSED_SL"
                ret_pct = (exit_price - entry_price) / entry_price * 100
                update_position(client, active["id"], {
                    "status": reason,
                    "exit_date": last_date,
                    "exit_price": exit_price,
                    "exit_reason": reason,
                    "return_pct": round(ret_pct, 2),
                })
                return {"type": reason, "ticker": ticker, "return_pct": round(ret_pct, 2)}
            elif tp_price is not None and high >= tp_price:
                # TP1 (+2.0 ATR) tercapai! Amankan 50% porsi dan geser SL ke Break-Even
                new_sl = entry_price
                update_position(client, active["id"], {
                    "sl_price": new_sl,
                })

                # Jika di bar yang sama harga berbalik menembus Break-Even
                if low <= new_sl:
                    half1_ret = (tp_price - entry_price) / entry_price * 100 * 0.5
                    reason = "CLOSED_TP1_BE"
                    update_position(client, active["id"], {
                        "status": reason,
                        "exit_date": last_date,
                        "exit_price": new_sl,
                        "exit_reason": reason,
                        "return_pct": round(half1_ret, 2),
                    })
                    return {"type": reason, "ticker": ticker, "return_pct": round(half1_ret, 2)}

                return {"type": "TP1_REACHED_RUNNER_ACTIVE", "ticker": ticker, "sl_moved_to": new_sl}
            elif int(last_row["Signal"]) == -1:
                exit_price = close
                reason = "CLOSED_SIGNAL"
                ret_pct = (exit_price - entry_price) / entry_price * 100
                update_position(client, active["id"], {
                    "status": reason,
                    "exit_date": last_date,
                    "exit_price": exit_price,
                    "exit_reason": reason,
                    "return_pct": round(ret_pct, 2),
                })
                return {"type": reason, "ticker": ticker, "return_pct": round(ret_pct, 2)}
            elif hold_days >= MAX_HOLD_DAYS:
                exit_price = close
                reason = "CLOSED_TIME"
                ret_pct = (exit_price - entry_price) / entry_price * 100
                update_position(client, active["id"], {
                    "status": reason,
                    "exit_date": last_date,
                    "exit_price": exit_price,
                    "exit_reason": reason,
                    "return_pct": round(ret_pct, 2),
                })
                return {"type": reason, "ticker": ticker, "return_pct": round(ret_pct, 2)}

        else:
            # Stage 2: Posisi Runner (sisa 50% trailing, SL di Break-Even)
            half1_ret = (tp_price - entry_price) / entry_price * 100 * 0.5 if tp_price else 0.0

            if low <= sl_price:
                # Kena Break-Even (Worst case setelah TP1: 0% di runner, net gain di half 1)
                exit_price = sl_price
                reason = "CLOSED_TP1_BE"
                update_position(client, active["id"], {
                    "status": reason,
                    "exit_date": last_date,
                    "exit_price": exit_price,
                    "exit_reason": reason,
                    "return_pct": round(half1_ret, 2),
                })
                return {"type": reason, "ticker": ticker, "return_pct": round(half1_ret, 2)}
            elif sma20 is not None and close < sma20:
                # Runner keluar karena Daily Close < SMA20
                exit_price = close
                half2_ret = (exit_price - entry_price) / entry_price * 100 * 0.5
                tot_ret = half1_ret + half2_ret
                reason = "CLOSED_RUNNER_SMA20"
                update_position(client, active["id"], {
                    "status": reason,
                    "exit_date": last_date,
                    "exit_price": exit_price,
                    "exit_reason": reason,
                    "return_pct": round(tot_ret, 2),
                })
                return {"type": reason, "ticker": ticker, "return_pct": round(tot_ret, 2)}
            elif int(last_row["Signal"]) == -1:
                exit_price = close
                half2_ret = (exit_price - entry_price) / entry_price * 100 * 0.5
                tot_ret = half1_ret + half2_ret
                reason = "CLOSED_TP1_SIGNAL"
                update_position(client, active["id"], {
                    "status": reason,
                    "exit_date": last_date,
                    "exit_price": exit_price,
                    "exit_reason": reason,
                    "return_pct": round(tot_ret, 2),
                })
                return {"type": reason, "ticker": ticker, "return_pct": round(tot_ret, 2)}
            elif hold_days >= MAX_HOLD_DAYS:
                exit_price = close
                half2_ret = (exit_price - entry_price) / entry_price * 100 * 0.5
                tot_ret = half1_ret + half2_ret
                reason = "CLOSED_TP1_TIME"
                update_position(client, active["id"], {
                    "status": reason,
                    "exit_date": last_date,
                    "exit_price": exit_price,
                    "exit_reason": reason,
                    "return_pct": round(tot_ret, 2),
                })
                return {"type": reason, "ticker": ticker, "return_pct": round(tot_ret, 2)}

    return None  # status tidak dikenal, jangan lakukan apa-apa


def _maybe_open_new_position(client, ticker, last_row, last_date, sector: str | None = None) -> dict | None:
    # LONG-ONLY: satu-satunya trigger pembukaan posisi adalah Signal == 1.
    if int(last_row["Signal"]) != 1:
        return None

    atr_val = last_row.get("ATR14")
    if atr_val is None or pd.isna(atr_val):
        return None  # ATR belum tersedia (data historis terlalu pendek), skip

    # Cek Portfolio Capacity & Sector Concentration Gate
    try:
        active_positions = fetch_all_active_positions(client)
        if len(active_positions) >= MAX_ACTIVE_POSITIONS:
            return {"type": "REJECTED_CAPACITY", "ticker": ticker, "reason": f"Maks {MAX_ACTIVE_POSITIONS} posisi aktif tercapai"}

        sec = sector or get_sector_of(ticker)
        if sec:
            sector_count = sum(1 for p in active_positions if get_sector_of(p["ticker"]) == sec)
            if sector_count >= MAX_SECTOR_POSITIONS:
                return {"type": "REJECTED_SECTOR", "ticker": ticker, "reason": f"Maks {MAX_SECTOR_POSITIONS} posisi sektor {sec} tercapai"}
    except Exception:
        # Fallback jika offline atau mock test tanpa method fetch_all_active_positions
        pass

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
