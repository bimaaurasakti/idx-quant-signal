"""
Test integrasi views/screener.py setelah redesign Fase 3 (kartu sinyal +
tabel ranking berwarna). Jalankan: python test_screener_fase3.py

Menguji 2 kondisi jumlah baris (grid kartu vs fallback tabel), Meteran
Konfirmasi terisi benar sesuai signal_strength, dan kondisi kosong (tanpa
sinyal/tanpa posisi) tetap aman -- semua lewat AppTest.from_function()
dengan data_loaders di-mock (tidak butuh Supabase asli).
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest

import data_loaders

errors = []


def check(label, cond):
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {label}")
    if not cond:
        errors.append(label)


TICKERS_5 = ["BBCA", "TLKM", "ASII", "BBRI", "UNVR"]


def _synthetic_screener(n_tickers=5) -> pd.DataFrame:
    rng = np.random.default_rng(5)
    rows = []
    for i, t in enumerate((TICKERS_5 * (n_tickers // 5 + 1))[:n_tickers]):
        rows.append({
            "ticker": f"{t}{i}" if i >= 5 else t, "sektor": "Perbankan", "last_close": 5000.0 + i * 10,
            "last_date": "2026-08-03", "signal_today": ["BUY", "SELL", "HOLD"][i % 3],
            "signal_strength": [3, 2, 1, 0, 3][i % 5], "trend": "Uptrend", "rsi": 55.0, "atr": 90.0,
            "winrate": 60.0, "expectancy_pct": 1.5, "profit_factor": 1.8, "max_drawdown_pct": -8.0,
            "n_trades": 15, "sharpe_rough": 1.1, "is_idx30": i % 2 == 0, "is_lq45": True,
        })
    return pd.DataFrame(rows)


def _synthetic_pending(n=3) -> pd.DataFrame:
    rows = []
    for i in range(n):
        rows.append({
            "id": i, "ticker": TICKERS_5[i % 5], "status": "PENDING_ENTRY",
            "signal_date": "2026-08-03", "planned_entry_date": "2026-08-04",
            "entry_date": None, "entry_price": None, "atr_at_signal": 90.0,
            "tp_price": None, "sl_price": None, "exit_date": None, "exit_price": None,
            "exit_reason": None, "return_pct": None,
        })
    return pd.DataFrame(rows)


def _synthetic_open(n=3) -> pd.DataFrame:
    rows = []
    for i in range(n):
        rows.append({
            "id": i, "ticker": TICKERS_5[i % 5], "status": "OPEN",
            "signal_date": "2026-07-28", "planned_entry_date": "2026-07-29",
            "entry_date": "2026-07-29", "entry_price": 5000.0, "atr_at_signal": 90.0,
            "tp_price": 5180.0, "sl_price": 4910.0, "exit_date": None, "exit_price": None,
            "exit_reason": None, "return_pct": None,
        })
    return pd.DataFrame(rows)


def _run_screener(n_screener, n_pending, n_open):
    import streamlit as st
    from dataclasses import dataclass, field
    from typing import Any
    import views.screener as screener

    @dataclass
    class _Ctx:
        client: Any = None
        settings: dict = field(default_factory=lambda: {"sector_filter": [], "min_trades_filter": 3})

    screener.render(_Ctx())


def _mock_and_run(n_screener, n_pending, n_open):
    data_loaders.fetch_screener_results = lambda client: _synthetic_screener(n_screener)

    def _fake_positions(client, statuses):
        statuses = tuple(statuses)
        if statuses == ("PENDING_ENTRY",):
            return _synthetic_pending(n_pending)
        if statuses == ("OPEN",):
            return _synthetic_open(n_open)
        return pd.DataFrame()

    data_loaders.fetch_ongoing_positions = _fake_positions
    data_loaders.load_screener.clear()
    data_loaders.load_positions.clear()

    at = AppTest.from_function(_run_screener, args=(n_screener, n_pending, n_open), default_timeout=30)
    at.run()
    return at


print("=== Kondisi 1: sedikit baris (mode GRID KARTU, 3 pending + 3 open, 8 screener) ===")
at1 = _mock_and_run(n_screener=8, n_pending=3, n_open=3)
print("Exception:", at1.exception)
check("tidak ada exception (mode kartu)", not at1.exception)
check("markdown 'Sinyal BUY Besok' muncul", any("Sinyal BUY Besok" in m.value for m in at1.markdown))
check("markdown 'Ongoing Position' muncul", any("Ongoing Position" in m.value for m in at1.markdown))
# Kartu di-render via st.markdown(unsafe_allow_html) berisi class iqs-card
n_iqs_cards = sum(1 for m in at1.markdown if "iqs-card" in m.value)
print(f"  jumlah elemen markdown mengandung 'iqs-card': {n_iqs_cards} (harus >= 6: 3 signal card + 3 position card)")
check("minimal 6 kartu ter-render (3 signal + 3 position)", n_iqs_cards >= 6)
# cek meteran konfirmasi: BBCA (index 0) signal_strength=3 -> 3 bar bullish
meter_full = any('title="Konfirmasi 3 dari 3"' in m.value for m in at1.markdown)
check("Meteran Konfirmasi '3 dari 3' muncul utk ticker dgn signal_strength=3", meter_full)
check("dataframe ranking tetap ter-render (st.dataframe)", len(at1.get("dataframe")) >= 1)

print("\n=== Kondisi 2: banyak baris (mode FALLBACK TABEL, 15 pending, 15 open) ===")
at2 = _mock_and_run(n_screener=20, n_pending=15, n_open=15)
print("Exception:", at2.exception)
check("tidak ada exception (mode fallback tabel)", not at2.exception)
n_iqs_cards2 = sum(1 for m in at2.markdown if "iqs-card" in m.value)
print(f"  jumlah elemen 'iqs-card' saat 15 baris (harus 0, harusnya fallback tabel): {n_iqs_cards2}")
check("TIDAK render kartu saat baris > _CARD_GRID_MAX_ROWS (pakai tabel)", n_iqs_cards2 == 0)
check("jumlah dataframe bertambah (BUY Besok + Ongoing + Ranking = 3 tabel)", len(at2.get("dataframe")) >= 3)

print("\n=== Kondisi 3: kosong (tanpa sinyal, tanpa posisi) ===")
at3 = _mock_and_run(n_screener=10, n_pending=0, n_open=0)
print("Exception:", at3.exception)
check("tidak ada exception (kondisi kosong)", not at3.exception)
info_texts = " | ".join(i.value for i in at3.info)
check("pesan 'Tidak ada sinyal BUY baru' muncul", "Tidak ada sinyal BUY baru" in info_texts)
check("pesan 'Tidak ada posisi yang sedang berjalan' muncul", "Tidak ada posisi yang sedang berjalan" in info_texts)

print(f"\n{'='*70}")
if errors:
    print(f"GAGAL: {len(errors)} pengecekan tidak lolos -> {errors}")
    raise SystemExit(1)
print("SEMUA TEST views/screener.py (Fase 3) PASS ✅")
print(f"{'='*70}")
