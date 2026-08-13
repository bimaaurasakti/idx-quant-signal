"""
api/services/backtest_service.py
==================================
Endpoint paling kompleks tapi ~90% isinya reuse langsung: generate_custom_
signals(), backtest_signals(), compute_equity_curve() dipanggil TANPA
modifikasi dari custom_backtest.py & backtester.py. _drop_warmup_nan() dan
_last_trade_confirmation() dipindah VERBATIM dari views/backtest.py --
fungsi aslinya sudah presentational-agnostic (tidak ada st.* call sama
sekali di dalamnya), jadi aman dipindah apa adanya ke sini.

Satu-satunya bagian yang benar-benar BARU: serialisasi DataFrame -> Pydantic
response JSON (bagian bawah file ini).
"""
from __future__ import annotations

import pandas as pd
from fastapi import HTTPException

from custom_backtest import generate_custom_signals, validate_min_bars, compute_equity_curve
from backtester import backtest_signals
from indicator_registry import INDICATOR_SPECS, MAX_INDICATORS_SELECTED
from supabase_client import fetch_price_history

from api.core.serialize import to_float
from api.schemas.backtest import (
    BacktestRunRequest, BacktestRunResponse, Bar, IndicatorSeries, Trade,
    BacktestMetrics, LastTradeConfirmation,
)

MIN_BARS_REQUIRED = 60  # konsisten dgn worker_fetch_and_update.py & views/backtest.py lama
_PERIOD_TO_DAYS = {"1y": 365, "2y": 365 * 2, "3y": 365 * 3, "5y": 365 * 5}


def _drop_warmup_nan(d: pd.DataFrame, selected: list[str]) -> pd.DataFrame:
    """Portasi VERBATIM dari views/backtest.py::_drop_warmup_nan."""
    check_cols = [c for c in d.columns if any(c.startswith(f"{k}_") for k in selected)] + ["ATR14"]
    first_valid_locs = []
    for c in check_cols:
        if c not in d.columns:
            continue
        idx = d[c].first_valid_index()
        if idx is not None:
            first_valid_locs.append(d.index.get_loc(idx))
    warm_up_end = max(first_valid_locs, default=0)
    return d.iloc[warm_up_end:] if warm_up_end < len(d) else d


def _last_trade_confirmation(d_clean: pd.DataFrame, trades: list[dict], total: int) -> tuple[int, int] | None:
    """Portasi VERBATIM dari views/backtest.py::_last_trade_confirmation."""
    if not trades:
        return None
    entry_date = pd.Timestamp(trades[-1]["entry_date"])
    if entry_date not in d_clean.index:
        return None
    entry_loc = d_clean.index.get_loc(entry_date)
    signal_loc = entry_loc - 1
    if signal_loc < 0 or "BullishCount" not in d_clean.columns:
        return None
    filled = int(d_clean["BullishCount"].iloc[signal_loc])
    return filled, total


async def run_backtest(client, req: BacktestRunRequest) -> BacktestRunResponse:
    # Validasi ulang di server -- JANGAN percaya batas yang sudah ditegakkan di UI client (§4.6).
    unknown = [k for k in req.selected_indicators if k not in INDICATOR_SPECS]
    if unknown:
        raise HTTPException(422, f"Indikator tidak dikenal: {unknown}")
    if len(req.selected_indicators) > MAX_INDICATORS_SELECTED:
        raise HTTPException(422, f"Maksimal {MAX_INDICATORS_SELECTED} indikator sekaligus.")

    raw = fetch_price_history(client, req.ticker)          # supabase_client.py, TIDAK DIUBAH
    if raw.empty:
        raise HTTPException(404, "Data harga tidak tersedia untuk ticker ini.")

    cutoff = raw.index.max() - pd.Timedelta(days=_PERIOD_TO_DAYS[req.period])
    df = raw[raw.index >= cutoff][["Open", "High", "Low", "Close", "Volume"]].copy()

    ok, msg = validate_min_bars(df, MIN_BARS_REQUIRED)      # custom_backtest.py, TIDAK DIUBAH
    if not ok:
        raise HTTPException(422, msg)

    d = generate_custom_signals(                            # custom_backtest.py, TIDAK DIUBAH
        df, req.selected_indicators, req.params, req.confirmation_threshold,
    )
    result = backtest_signals(                               # backtester.py, TIDAK DIUBAH
        d, r_multiple_tp=req.tp_multiple, sl_atr_mult=req.sl_multiple, max_hold_days=req.max_hold_days,
    )
    d_clean = _drop_warmup_nan(d, req.selected_indicators)
    equity = compute_equity_curve(result["trades"])          # custom_backtest.py, TIDAK DIUBAH

    return _to_response(req.ticker, d_clean, result, equity, req.selected_indicators)


def _to_response(
    ticker: str, d_clean: pd.DataFrame, result: dict, equity: pd.Series, selected: list[str],
) -> BacktestRunResponse:
    bars = [
        Bar(
            date=idx.strftime("%Y-%m-%d"), open=float(r["Open"]), high=float(r["High"]),
            low=float(r["Low"]), close=float(r["Close"]), volume=float(r["Volume"]),
        )
        for idx, r in d_clean.iterrows()
    ]

    indicator_series: list[IndicatorSeries] = []
    for key in selected:
        spec = INDICATOR_SPECS[key]
        cols = [c for c in d_clean.columns if c.startswith(f"{key}_")]
        for c in cols:
            # Strip prefix "{key}_" secara eksplisit (BUKAN split("_",1) naif)
            # -- utk key yg sendiri mengandung underscore (mis. "ema_crossover"),
            # split naif salah memotong jadi "crossover_Fast", bukan "Fast".
            suffix = c[len(key) + 1 :] if c.startswith(f"{key}_") else c
            indicator_series.append(IndicatorSeries(
                key=c, label=f"{spec['label']} ({suffix})", overlay=spec["overlay"],
                values=[to_float(v) for v in d_clean[c].tolist()],
            ))

    trades = [
        Trade(
            entry_date=str(t["entry_date"]), exit_date=str(t["exit_date"]),
            entry_price=t["entry_price"], exit_price=t["exit_price"],
            return_pct=t["return_pct"], reason=t["reason"], hold_days=t["hold_days"],
        )
        for t in result["trades"]
    ]

    meter = _last_trade_confirmation(d_clean, result["trades"], len(selected))

    return BacktestRunResponse(
        ticker=ticker,
        bars=bars,
        indicator_series=indicator_series,
        bullish_count=d_clean["BullishCount"].astype(int).tolist() if "BullishCount" in d_clean else [],
        bearish_count=d_clean["BearishCount"].astype(int).tolist() if "BearishCount" in d_clean else [],
        signal=d_clean["Signal"].astype(int).tolist() if "Signal" in d_clean else [],
        trades=trades,
        metrics=BacktestMetrics(**{k: result[k] for k in (
            "n_trades", "winrate", "avg_win_pct", "avg_loss_pct", "expectancy_pct",
            "profit_factor", "max_drawdown_pct", "sharpe_rough",
        )}),
        equity_curve=[float(v) for v in equity.tolist()],
        last_trade_confirmation=LastTradeConfirmation(filled=meter[0], total=meter[1]) if meter else None,
    )
