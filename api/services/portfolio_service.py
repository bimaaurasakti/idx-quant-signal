"""
api/services/portfolio_service.py
===================================
Port dari views/portfolio.py::_prepare_portfolio_df. Mengembalikan SELURUH
posisi closed (sudah dilengkapi sektor & hold_days) -- filter (sektor/
tanggal/ticker) & agregasi metrik (_portfolio_metrics) SENGAJA dilakukan di
frontend (TypeScript) untuk UX filter instan, lihat §5.6/§5.7 implementation
plan. Formula agregasi tetap didokumentasikan presisi di sana supaya tidak
drift dari backtester.py::_compute_metrics.
"""
from __future__ import annotations

import pandas as pd

from supabase_client import fetch_closed_positions
from tickers_idx import get_sector_of

from api.core.serialize import to_float, to_int, to_str_or_none
from api.schemas.portfolio import ClosedPosition, PortfolioResponse


def get_portfolio(client) -> PortfolioResponse:
    df = fetch_closed_positions(client)
    if df.empty:
        return PortfolioResponse(positions=[])

    d = df.copy()
    d["entry_date_dt"] = pd.to_datetime(d["entry_date"])
    d["exit_date_dt"] = pd.to_datetime(d["exit_date"])
    d["hold_days_calc"] = (d["exit_date_dt"] - d["entry_date_dt"]).dt.days
    d["sektor_calc"] = d["ticker"].apply(get_sector_of)

    positions = [
        ClosedPosition(
            ticker=r["ticker"], sektor=r["sektor_calc"], status=r["status"],
            signal_date=to_str_or_none(r.get("signal_date")),
            entry_date=r["entry_date_dt"].strftime("%Y-%m-%d"),
            entry_price=to_float(r.get("entry_price")) or 0.0,
            exit_date=r["exit_date_dt"].strftime("%Y-%m-%d"),
            exit_price=to_float(r.get("exit_price")) or 0.0,
            return_pct=to_float(r.get("return_pct")) or 0.0,
            hold_days=to_int(r.get("hold_days_calc")) or 0,
        )
        for _, r in d.iterrows()
    ]
    return PortfolioResponse(positions=positions)
