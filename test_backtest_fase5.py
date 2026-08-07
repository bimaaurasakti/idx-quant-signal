"""
Test integrasi views/backtest.py setelah redesign Fase 5 (badge jumlah
indikator, metric card, Meteran Konfirmasi trade terakhir). Jalankan:
python test_backtest_fase5.py
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest

import data_loaders
from custom_backtest import generate_custom_signals
from backtester import backtest_signals
import views.backtest as backtest

errors = []


def check(label, cond):
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {label}")
    if not cond:
        errors.append(label)


def make_ohlcv(n=260, seed=13) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2024-01-01", periods=n, freq="B")
    returns = rng.normal(0.0012, 0.012, n)
    close = 1000.0 * np.cumprod(1 + returns)
    high = close * (1 + np.abs(rng.normal(0, 0.004, n)))
    low = close * (1 - np.abs(rng.normal(0, 0.004, n)))
    open_ = low + (high - low) * rng.uniform(0.2, 0.8, n)
    volume = rng.integers(1_000_000, 5_000_000, n).astype(float)
    return pd.DataFrame({"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume}, index=dates)


print("=== Unit test: _last_trade_confirmation() ===")
df = make_ohlcv()
selected = ["ema_crossover", "rsi", "macd"]
d = generate_custom_signals(df, selected, confirmation_threshold=1)
d_clean = backtest._drop_warmup_nan(d, selected)
bt = backtest_signals(d_clean)
print(f"  Data sintetis: {len(d_clean)} bar, {bt['n_trades']} trade dari {selected}")

if bt["n_trades"] > 0:
    result = backtest._last_trade_confirmation(d_clean, bt["trades"], len(selected))
    check("return bukan None utk data valid", result is not None)
    if result:
        filled, total = result
        check("total == len(selected) == 3", total == 3)
        check("filled dalam rentang [0, total]", 0 <= filled <= total)
        # Verifikasi manual: filled harus == BullishCount di bar (entry_loc - 1)
        entry_date = pd.Timestamp(bt["trades"][-1]["entry_date"])
        entry_loc = d_clean.index.get_loc(entry_date)
        expected_filled = int(d_clean["BullishCount"].iloc[entry_loc - 1])
        check(f"filled ({filled}) == BullishCount manual di bar sinyal ({expected_filled})", filled == expected_filled)

check("trades=[] -> return None (bukan crash)", backtest._last_trade_confirmation(d_clean, [], 3) is None)
check("entry_date di luar index -> return None",
      backtest._last_trade_confirmation(d_clean, [{"entry_date": pd.Timestamp("2099-01-01")}], 3) is None)
empty_d = d_clean.iloc[:0]
check("d_clean kosong -> return None (bukan IndexError)",
      backtest._last_trade_confirmation(empty_d, bt["trades"] or [{"entry_date": d_clean.index[10]}], 3) is None)

print("\n=== Integrasi: render() dgn form submit sungguhan (AppTest) ===")
data_loaders.fetch_screener_results = lambda client: pd.DataFrame([
    {"ticker": "BBCA", "sektor": "Perbankan", "last_close": 5000.0, "last_date": "2026-08-03",
     "signal_today": "BUY", "signal_strength": 3, "trend": "Uptrend", "rsi": 55.0, "atr": 90.0,
     "winrate": 60.0, "expectancy_pct": 1.5, "profit_factor": 1.8, "max_drawdown_pct": -8.0,
     "n_trades": 15, "sharpe_rough": 1.1, "is_idx30": True, "is_lq45": True},
])
data_loaders.fetch_price_history = lambda client, ticker: make_ohlcv(n=400, seed=21)
data_loaders.load_screener.clear()
data_loaders.load_price_history.clear()


def _run_backtest_page():
    import streamlit as st
    from dataclasses import dataclass, field
    from typing import Any
    import views.backtest as bt_module

    @dataclass
    class _Ctx:
        client: Any = None
        settings: dict = field(default_factory=dict)

    bt_module.render(_Ctx())


at = AppTest.from_function(_run_backtest_page, default_timeout=60)
at.run()
check("render() awal (form belum submit) tidak exception", not at.exception)

# Pilih 2 indikator lewat multiselect kategori Trend, lalu submit form.
trend_multiselect = at.multiselect(key="bt_pick_Trend")
trend_multiselect.select("sma").select("ema_crossover").run()
check("setelah pilih 2 indikator, tidak exception", not at.exception)
expander_labels = [e.label for e in at.get("expander")]
print(f"  Label expander saat ini: {expander_labels}")
check("badge jumlah terpilih '2 dipilih' muncul di label expander Trend",
      any("Trend" in lbl and "2 dipilih" in lbl for lbl in expander_labels))

buttons = at.get("button")
submit = next((b for b in buttons if "Jalankan Backtest" in b.label), None)
check("tombol submit 'Jalankan Backtest' ditemukan", submit is not None)
if submit:
    submit.click().run(timeout=60)
    print("Exception setelah submit:", at.exception)
    check("submit backtest tidak exception", not at.exception)
    md_result = " ".join(m.value for m in at.markdown)
    check("hasil backtest ter-render ('Hasil Backtest')", "Hasil Backtest" in md_result)
    warning_texts = " ".join(w.value for w in at.warning)
    check("warning in-sample TETAP ada verbatim", "bersifat in-sample" in warning_texts)
    check("minimal 1 chart Plotly ter-render (tab Chart)", len(at.get("plotly_chart")) >= 1)
    check("tab (Chart/Riwayat Trade/Equity Curve) ter-render", len(at.tabs) >= 1 or len(at.get("tab")) >= 1)

print(f"\n{'='*70}")
if errors:
    print(f"GAGAL: {len(errors)} pengecekan tidak lolos -> {errors}")
    raise SystemExit(1)
print("SEMUA TEST views/backtest.py (Fase 5) PASS ✅")
print(f"{'='*70}")
