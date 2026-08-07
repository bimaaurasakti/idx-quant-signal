"""
Test integrasi views/portfolio.py & views/backtest.py setelah chart
theming (Fase 2). Jalankan: python test_pages_chart_theming.py

Beda dari test_navigation_fase1.py (yang lewat app.py penuh dan kena
limitasi switch_page), test ini pakai AppTest.from_function() utk
memanggil views.portfolio.render(ctx) / views.backtest.render(ctx) SECARA
LANGSUNG dengan ctx palsu -- lebih presisi menguji 1 halaman spesifik
tanpa bergantung pada navigasi app.py sama sekali.
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


def _synthetic_closed_positions(n=24) -> pd.DataFrame:
    tickers = ["BBCA", "TLKM", "ASII", "BBRI", "UNVR"] * (n // 5 + 1)
    rng = np.random.default_rng(3)
    rows = []
    base = pd.Timestamp("2026-05-01")
    for i in range(n):
        entry = base + pd.Timedelta(days=int(rng.integers(0, 60)))
        exit_ = entry + pd.Timedelta(days=int(rng.integers(1, 15)))
        ret = float(rng.normal(1.0, 4.0))
        status = rng.choice(["CLOSED_TP", "CLOSED_SL", "CLOSED_SIGNAL", "CLOSED_TIME"])
        rows.append({
            "ticker": tickers[i], "status": status,
            "signal_date": entry - pd.Timedelta(days=1), "entry_date": entry, "exit_date": exit_,
            "entry_price": 5000.0, "exit_price": 5000.0 * (1 + ret / 100),
            "atr_at_signal": 80.0, "tp_price": 5160.0, "sl_price": 4920.0,
            "return_pct": ret,
        })
    return pd.DataFrame(rows)


data_loaders.fetch_closed_positions = lambda client: _synthetic_closed_positions()
data_loaders.load_closed_positions.clear()

print("=== views/portfolio.py dengan data sintetis (24 posisi closed) ===")


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


at = AppTest.from_function(_run_portfolio, default_timeout=30)
at.run()
print("Exception:", at.exception)
check("portfolio.render() tidak melempar exception", not at.exception)
check("minimal 3 chart Plotly ter-render (breakdown exit, sektor, cumulative)", len(at.get("plotly_chart")) >= 3)
print("  (Catatan: AppTest tidak expose objek go.Figure Python asli dari plotly_chart,")
print("   jadi warna paper_bgcolor persis tidak bisa diverifikasi lewat elemen ini --")
print("   sudah diverifikasi terpisah & lebih presisi di test_chart_theming.py yang")
print("   memanggil build_chart_figure()/apply_chart_theme() langsung sbg objek Python.)")

print("\n=== views/backtest.py: equity curve chart (fig_eq) ===")


def _run_backtest_equity():
    """Panggil langsung _render_result() dgn payload sintetis -- melewati
    form input (submit) yg butuh interaksi widget kompleks, fokus HANYA ke
    verifikasi bagian equity curve chart (§8 poin 5)."""
    import views.backtest as backtest
    import pandas as pd
    dates = pd.date_range("2024-01-01", periods=120, freq="B")
    d_clean = pd.DataFrame({
        "Open": 1000.0, "High": 1010.0, "Low": 990.0, "Close": 1000.0, "Volume": 1_000_000,
    }, index=dates)
    trades = [
        {"entry_date": dates[i], "exit_date": dates[i + 3], "entry_price": 1000.0, "exit_price": 1020.0,
         "return_pct": 2.0, "reason": "TP", "hold_days": 3}
        for i in range(0, 30, 5)
    ]
    result = {
        "n_trades": len(trades), "winrate": 100.0, "avg_win_pct": 2.0, "avg_loss_pct": 0.0,
        "expectancy_pct": 2.0, "profit_factor": None, "max_drawdown_pct": -1.0,
        "sharpe_rough": 1.5, "trades": trades,
    }
    backtest._render_result({"ticker": "BBCA", "d_clean": d_clean, "result": result, "selected": ["rsi"]})


at2 = AppTest.from_function(_run_backtest_equity, default_timeout=30)
at2.run()
print("Exception:", at2.exception)
check("_render_result() (termasuk tab equity curve) tidak melempar exception", not at2.exception)
check("chart Plotly ter-render di _render_result (chart statis + equity curve)", len(at2.get("plotly_chart")) >= 1)

print(f"\n{'='*70}")
if errors:
    print(f"GAGAL: {len(errors)} pengecekan tidak lolos -> {errors}")
    raise SystemExit(1)
print("SEMUA TEST integrasi chart portfolio.py & backtest.py (Fase 2) PASS ✅")
print(f"{'='*70}")
