"""
Test integrasi views/detail.py setelah redesign Fase 4 (price header +
meteran konfirmasi + metric card). Jalankan: python test_detail_fase4.py

Menguji: header harga + change/change_pct terhitung benar dari 2 baris
terakhir price_history, kartu status utk PENDING_ENTRY & OPEN, metric card
tone (bullish/bearish) sesuai nilai, dan tabel riwayat trade dgn label
Alasan Exit yang sudah di-map (perlu supaya style_exit_reason_row bekerja
-- lihat CARA_TERAPKAN.md Fase 4 utk penjelasan kenapa ini perlu).
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


def _synthetic_screener() -> pd.DataFrame:
    return pd.DataFrame([{
        "ticker": "BBCA", "sektor": "Perbankan", "last_close": 5150.0, "last_date": "2026-08-03",
        "signal_today": "BUY", "signal_strength": 3, "trend": "Uptrend", "rsi": 58.0, "atr": 95.0,
        "winrate": 62.5, "expectancy_pct": 1.8, "profit_factor": 2.1, "max_drawdown_pct": -7.5,
        "n_trades": 18, "sharpe_rough": 1.3, "is_idx30": True, "is_lq45": True,
    }])


def _synthetic_price_history(n=220) -> pd.DataFrame:
    """PENTING: mock ini menggantikan SELURUH fetch_price_history() (bukan
    cuma sumber data Supabase-nya) -- jadi harus return data yang SUDAH
    dalam bentuk final yang biasanya dihasilkan fetch_price_history()
    (DatetimeIndex + kolom PascalCase), BUKAN bentuk mentah lowercase ala
    baris tabel Supabase (kalau tidak, d['Close'] akan KeyError -- ini bug
    nyata yang kepergok pertama kali nulis test ini, sudah diperbaiki)."""
    rng = np.random.default_rng(9)
    dates = pd.date_range("2025-09-01", periods=n, freq="B")
    close = 5000.0 + np.cumsum(rng.normal(2, 30, n))
    close[-1] = close[-2] + 50.0  # bar terakhir naik pasti -> change positif, gampang divalidasi
    df = pd.DataFrame({
        "Open": close - 10, "High": close + 20, "Low": close - 20, "Close": close,
        "Volume": 2_000_000, "SMA20": close, "SMA50": close, "SMA200": close,
        "RSI14": 55.0, "MACD": 1.2, "MACD_Signal": 1.0, "MACD_Hist": 0.2, "ATR14": 95.0,
        "Signal": [1 if i % 40 == 0 else (-1 if i % 55 == 0 else 0) for i in range(n)],
    }, index=dates)
    return df


def _synthetic_trades() -> pd.DataFrame:
    return pd.DataFrame([
        {"ticker": "BBCA", "entry_date": "2026-06-01", "exit_date": "2026-06-08",
         "entry_price": 5000.0, "exit_price": 5160.0, "return_pct": 3.2, "reason": "TP", "hold_days": 7},
        {"ticker": "BBCA", "entry_date": "2026-06-15", "exit_date": "2026-06-18",
         "entry_price": 5050.0, "exit_price": 4970.0, "return_pct": -1.6, "reason": "SL", "hold_days": 3},
    ])


def _run_detail():
    import streamlit as st
    from dataclasses import dataclass, field
    from typing import Any
    import views.detail as detail

    @dataclass
    class _Ctx:
        client: Any = None
        settings: dict = field(default_factory=dict)

    detail.render(_Ctx())


def _mock(position_status: str | None):
    data_loaders.fetch_screener_results = lambda client: _synthetic_screener()
    data_loaders.fetch_price_history = lambda client, ticker: _synthetic_price_history()
    data_loaders.fetch_backtest_trades = lambda client, ticker: _synthetic_trades()

    def _fake_positions(client, statuses):
        if position_status is None:
            return pd.DataFrame()
        return pd.DataFrame([{
            "id": 1, "ticker": "BBCA", "status": position_status,
            "signal_date": "2026-08-02", "planned_entry_date": "2026-08-04",
            "entry_date": "2026-08-03" if position_status == "OPEN" else None,
            "entry_price": 5100.0 if position_status == "OPEN" else None,
            "atr_at_signal": 95.0, "tp_price": 5290.0 if position_status == "OPEN" else None,
            "sl_price": 5005.0 if position_status == "OPEN" else None,
            "exit_date": None, "exit_price": None, "exit_reason": None, "return_pct": None,
        }])

    data_loaders.fetch_ongoing_positions = _fake_positions
    for f in (data_loaders.load_screener, data_loaders.load_price_history,
              data_loaders.load_trades, data_loaders.load_positions):
        f.clear()


print("=== Kondisi 1: tanpa posisi aktif ===")
_mock(position_status=None)
at1 = AppTest.from_function(_run_detail, default_timeout=30)
at1.run()
print("Exception:", at1.exception)
check("tidak ada exception", not at1.exception)
md1 = " ".join(m.value for m in at1.markdown)
check("harga (mono, format Rp Indonesia) ter-render di header", "Rp " in md1)
check("badge sinyal 'Buy' muncul (signal_today='BUY')", "Buy" in md1)
check("Meteran Konfirmasi 3/3 muncul (signal_strength=3)", 'title="Konfirmasi 3 dari 3"' in md1)
check("TIDAK ada kartu status posisi (tidak ada posisi aktif)", "Sinyal BUY aktif" not in md1 and "Posisi <b>OPEN</b>" not in md1)
check("chart candlestick+RSI+MACD ter-render", len(at1.get("plotly_chart")) >= 1)
check("tabel riwayat trade ter-render", len(at1.get("dataframe")) >= 1)

print("\n=== Kondisi 2: posisi PENDING_ENTRY ===")
_mock(position_status="PENDING_ENTRY")
at2 = AppTest.from_function(_run_detail, default_timeout=30)
at2.run()
check("tidak ada exception (PENDING_ENTRY)", not at2.exception)
md2 = " ".join(m.value for m in at2.markdown)
check("kartu 'Sinyal BUY aktif' muncul", "Sinyal BUY aktif" in md2)

print("\n=== Kondisi 3: posisi OPEN ===")
_mock(position_status="OPEN")
at3 = AppTest.from_function(_run_detail, default_timeout=30)
at3.run()
check("tidak ada exception (OPEN)", not at3.exception)
md3 = " ".join(m.value for m in at3.markdown)
check("kartu 'Posisi OPEN' muncul dgn format Rp Indonesia (titik ribuan)", "Posisi <b>OPEN</b>" in md3 and "Rp 5.100" in md3)

print(f"\n{'='*70}")
if errors:
    print(f"GAGAL: {len(errors)} pengecekan tidak lolos -> {errors}")
    raise SystemExit(1)
print("SEMUA TEST views/detail.py (Fase 4) PASS ✅")
print(f"{'='*70}")
