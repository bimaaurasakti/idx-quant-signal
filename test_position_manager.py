"""
Test manual (bukan bagian dari deliverable) untuk memvalidasi position_manager.py
tanpa koneksi Supabase asli — pakai mock in-memory yang meniru perilaku
get_active_position / insert_position / update_position.
"""
import pandas as pd
import numpy as np
from datetime import date

import position_manager as pm

# ---------------- Mock in-memory "Supabase" ----------------
_STORE = {"positions": [], "_next_id": 1}


def mock_get_active_position(client, ticker):
    for p in _STORE["positions"]:
        if p["ticker"] == ticker and p["status"] in ("PENDING_ENTRY", "OPEN"):
            return p
    return None


def mock_insert_position(client, row):
    row = dict(row)
    row["id"] = _STORE["_next_id"]
    _STORE["_next_id"] += 1
    _STORE["positions"].append(row)


def mock_update_position(client, position_id, updates):
    for p in _STORE["positions"]:
        if p["id"] == position_id:
            p.update(updates)
            return


pm.get_active_position = mock_get_active_position
pm.insert_position = mock_insert_position
pm.update_position = mock_update_position
pm.fetch_all_active_positions = lambda c: [p for p in _STORE["positions"] if p["status"] in ("PENDING_ENTRY", "OPEN")]

client = object()  # dummy, tidak dipakai krn sudah di-mock


def make_bar(o, h, l, c, signal, atr=50.0, sma20=None):
    b = {"Open": o, "High": h, "Low": l, "Close": c, "Signal": signal, "ATR14": atr}
    if sma20 is not None:
        b["SMA20"] = sma20
    return pd.Series(b)


def run_day(ticker, d_date, o, h, l, c, signal, atr=50.0, sma20=None):
    df = pd.DataFrame([make_bar(o, h, l, c, signal, atr, sma20)], index=[pd.Timestamp(d_date)])
    action = pm.sync_position(client, ticker, df)
    print(f"  {d_date} O={o} H={h} L={l} C={c} sig={signal} -> action={action}")
    return action


print("=" * 70)
print("SKENARIO 1: BUY signal -> PENDING -> OPEN -> TP1 (SL to BE) -> Runner Exit on Close < SMA20")
print("=" * 70)
_STORE["positions"].clear()

# Hari 1 (Senin 20 Jul 2026): sinyal BUY muncul di close
run_day("BBCA", date(2026, 7, 20), 5000, 5050, 4980, 5040, signal=1, atr=100.0)
active = mock_get_active_position(client, "BBCA")
print("  Status setelah hari 1:", active["status"], "| planned_entry_date:", active["planned_entry_date"])
assert active["status"] == "PENDING_ENTRY"
assert str(active["planned_entry_date"]) == "2026-07-21", "harus besok (Selasa)"

# Hari 2 (Selasa 21 Jul 2026): entry di Open hari ini
run_day("BBCA", date(2026, 7, 21), 5045, 5100, 5030, 5080, signal=0, atr=100.0)
active = mock_get_active_position(client, "BBCA")
print("  Status setelah hari 2:", active["status"], "| entry_price:", active["entry_price"],
      "| TP:", active["tp_price"], "| SL:", active["sl_price"])
assert active["status"] == "OPEN"
assert active["entry_price"] == 5045.0
assert active["tp_price"] == 5045.0 + 2 * 100.0   # R_MULTIPLE_TP=2.0
assert active["sl_price"] == 5045.0 - 1.5 * 100.0 # SL_ATR_MULT=1.5 (initial SL)

# Hari 3: belum kena TP/SL
run_day("BBCA", date(2026, 7, 22), 5080, 5150, 5060, 5120, signal=0, atr=100.0)
active = mock_get_active_position(client, "BBCA")
assert active["status"] == "OPEN", "belum harus exit"
print("  Status setelah hari 3 (belum TP/SL): masih OPEN, benar.")

# Hari 4: High tembus TP1 (5045 + 200 = 5245), Low aman (5150 > entry 5045)
run_day("BBCA", date(2026, 7, 23), 5120, 5260, 5150, 5240, signal=0, atr=100.0, sma20=5100.0)
active_after_tp1 = mock_get_active_position(client, "BBCA")
assert active_after_tp1 is not None, "posisi runner masih aktif"
assert active_after_tp1["sl_price"] == 5045.0, "SL harus digeser ke Break-Even (entry price)"
print("  PASS: TP1 tercapai, posisi runner aktif, SL digeser ke BE (5045.0).")

# Hari 5: Runner exit saat daily Close < SMA20 (Close 5180 < SMA20 5200)
run_day("BBCA", date(2026, 7, 24), 5220, 5230, 5170, 5180, signal=0, atr=100.0, sma20=5200.0)
active_check = mock_get_active_position(client, "BBCA")
assert active_check is None, "posisi harus HILANG dari ongoing setelah runner exit"
closed = [p for p in _STORE["positions"] if p["ticker"] == "BBCA"][0]
print("  Status akhir:", closed["status"], "| return_pct:", closed["return_pct"])
assert closed["status"] == "CLOSED_RUNNER_SMA20"
assert closed["return_pct"] > 0
print("  PASS: Runner sukses keluar via CLOSED_RUNNER_SMA20 dgn profit positif.\n")


print("=" * 70)
print("SKENARIO 2: BUY -> OPEN -> kena STOP LOSS AWAL (-1.5 ATR)")
print("=" * 70)
_STORE["positions"].clear()
run_day("BBRI", date(2026, 7, 20), 4000, 4020, 3980, 4010, signal=1, atr=80.0)
run_day("BBRI", date(2026, 7, 21), 4005, 4030, 3990, 4015, signal=0, atr=80.0)  # entry di open=4005
active = mock_get_active_position(client, "BBRI")
print("  Entry price:", active["entry_price"], "SL:", active["sl_price"])
assert active["sl_price"] == 4005 - 1.5 * 80.0  # 3885.0
run_day("BBRI", date(2026, 7, 22), 3900, 3910, 3880, 3890, signal=0, atr=80.0)  # Low tembus SL
active_check = mock_get_active_position(client, "BBRI")
assert active_check is None
closed = [p for p in _STORE["positions"] if p["ticker"] == "BBRI"][0]
print("  Status akhir:", closed["status"], "| return_pct:", closed["return_pct"])
assert closed["status"] == "CLOSED_SL"
assert closed["return_pct"] < 0
print("  PASS: SL kena dengan benar, return negatif.\n")


print("=" * 70)
print("SKENARIO 3: Tidak boleh ada 2 posisi aktif untuk 1 ticker sekaligus")
print("=" * 70)
_STORE["positions"].clear()
run_day("TLKM", date(2026, 7, 20), 3000, 3050, 2980, 3040, signal=1, atr=50.0)
n_before = len([p for p in _STORE["positions"] if p["ticker"] == "TLKM"])
run_day("TLKM", date(2026, 7, 21), 3045, 3100, 3030, 3090, signal=1, atr=50.0)
n_after = len([p for p in _STORE["positions"] if p["ticker"] == "TLKM"])
print(f"  Jumlah row posisi TLKM: sebelum={n_before}, sesudah={n_after}")
assert n_after == 1, "TIDAK BOLEH ada posisi kedua selama yang pertama masih aktif"
active = mock_get_active_position(client, "TLKM")
print("  Status:", active["status"], "(harus OPEN, bukan PENDING_ENTRY baru)")
assert active["status"] == "OPEN"
print("  PASS: constraint 1 posisi per ticker terjaga.\n")


print("=" * 70)
print("SKENARIO 4: LONG-ONLY -- sinyal SELL tanpa posisi terbuka TIDAK membuka short")
print("=" * 70)
_STORE["positions"].clear()
run_day("ASII", date(2026, 7, 20), 6000, 6010, 5900, 5910, signal=-1, atr=100.0)
active = mock_get_active_position(client, "ASII")
n_rows = len([p for p in _STORE["positions"] if p["ticker"] == "ASII"])
print(f"  Posisi aktif: {active} | total rows: {n_rows}")
assert active is None and n_rows == 0, "sinyal SELL tanpa posisi terbuka HARUS diabaikan (no short)"
print("  PASS: tidak ada posisi short yang terbuka.\n")


print("=" * 70)
print("SKENARIO 5: Exit karena SELL SIGNAL sebelum TP1")
print("=" * 70)
_STORE["positions"].clear()
run_day("UNVR", date(2026, 7, 20), 2000, 2020, 1980, 2010, signal=1, atr=40.0)
run_day("UNVR", date(2026, 7, 21), 2005, 2030, 1995, 2020, signal=0, atr=40.0)
active = mock_get_active_position(client, "UNVR")
run_day("UNVR", date(2026, 7, 22), 2020, 2040, 2000, 2015, signal=-1, atr=40.0)
active_check = mock_get_active_position(client, "UNVR")
closed = [p for p in _STORE["positions"] if p["ticker"] == "UNVR"][0]
print("  Status akhir:", closed["status"])
assert active_check is None
assert closed["status"] == "CLOSED_SIGNAL"
print("  PASS: exit lewat sinyal SELL bekerja & posisi hilang dari ongoing.\n")

print("=" * 70)
print("SEMUA SKENARIO PASS OK")
print("=" * 70)
