"""
Test integrasi views/portfolio.py setelah redesign Fase 6 (metric card
bertone dinamis). Jalankan: python test_portfolio_fase6.py

Fokus: 2 skenario data (mayoritas profit vs mayoritas rugi) utk memverifikasi
tone metric card berubah sesuai data -- bukan cuma statis.
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


def _synthetic_closed(mostly_winning: bool, n=25) -> pd.DataFrame:
    rng = np.random.default_rng(17 if mostly_winning else 18)
    tickers = ["BBCA", "TLKM", "ASII", "BBRI", "UNVR"]
    mean_ret = 2.5 if mostly_winning else -2.5
    rows = []
    base = pd.Timestamp("2026-04-01")
    for i in range(n):
        entry = base + pd.Timedelta(days=int(rng.integers(0, 90)))
        exit_ = entry + pd.Timedelta(days=int(rng.integers(1, 15)))
        ret = float(rng.normal(mean_ret, 3.0))
        status = "CLOSED_TP" if ret > 0 else "CLOSED_SL"
        rows.append({
            "ticker": tickers[i % 5], "status": status,
            "signal_date": entry - pd.Timedelta(days=1), "entry_date": entry, "exit_date": exit_,
            "entry_price": 5000.0, "exit_price": 5000.0 * (1 + ret / 100),
            "atr_at_signal": 80.0, "tp_price": 5160.0, "sl_price": 4920.0, "return_pct": ret,
        })
    return pd.DataFrame(rows)


def _run_portfolio():
    import streamlit as st
    from dataclasses import dataclass, field
    from typing import Any
    import views.portfolio as portfolio

    @dataclass
    class _Ctx:
        client: Any = None
        settings: dict = field(default_factory=dict)

    portfolio.render(_Ctx())


def _run(mostly_winning: bool):
    data_loaders.fetch_closed_positions = lambda client: _synthetic_closed(mostly_winning)
    data_loaders.load_closed_positions.clear()
    at = AppTest.from_function(_run_portfolio, default_timeout=30)
    at.run()
    return at


print("=== Skenario 1: mayoritas WINNING (expectancy & total return positif) ===")
at1 = _run(mostly_winning=True)
check("tidak ada exception", not at1.exception)
md1 = " ".join(m.value for m in at1.markdown)
n_cards1 = sum(m.value.count("iqs-mono") for m in at1.markdown)
print(f"  jumlah kemunculan class 'iqs-mono' pada metric card (harus == 6): {n_cards1}")
check("persis 6 metric card ter-render (render_metric_card dipanggil 6x)", n_cards1 == 6)
check("3+ chart Plotly ter-render", len(at1.get("plotly_chart")) >= 3)

print("\n=== Skenario 2: mayoritas LOSING (expectancy & total return negatif) ===")
at2 = _run(mostly_winning=False)
check("tidak ada exception", not at2.exception)
md2 = " ".join(m.value for m in at2.markdown)

# Cek lebih presisi: metric card di-render lewat st.markdown(unsafe_allow_html) dgn class
# iqs-mono utk value -- warna tone (hijau/merah) ada di style inline, kita cek warna
# COLORS["bearish"] muncul (menandakan minimal 1 metric card ber-tone bearish di skenario losing).
from theme import COLORS
n_bearish_cards_losing = sum(1 for m in at2.markdown if COLORS["bearish"] in m.value and "iqs-mono" in m.value)
n_bullish_cards_winning = sum(1 for m in at1.markdown if COLORS["bullish"] in m.value and "iqs-mono" in m.value)
print(f"  Skenario winning: {n_bullish_cards_winning} metric card ber-tone bullish (warna hijau)")
print(f"  Skenario losing: {n_bearish_cards_losing} metric card ber-tone bearish (warna merah)")
check("skenario WINNING punya card ber-tone bullish (hijau)", n_bullish_cards_winning >= 1)
check("skenario LOSING punya card ber-tone bearish (merah)", n_bearish_cards_losing >= 1)
check("jumlah card bertone POSITIF di skenario winning > skenario losing",
      n_bullish_cards_winning > sum(1 for m in at2.markdown if COLORS["bullish"] in m.value and "iqs-mono" in m.value))

print(f"\n{'='*70}")
if errors:
    print(f"GAGAL: {len(errors)} pengecekan tidak lolos -> {errors}")
    raise SystemExit(1)
print("SEMUA TEST views/portfolio.py (Fase 6) PASS ✅")
print(f"{'='*70}")
