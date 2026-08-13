"""
api/services/screener_service.py
==================================
Port 1:1 dari logika assembly views/screener.py (merge pending/open position
dengan screener_results, sort) -- TIDAK ADA logika baru, hanya dipindah dari
konteks Streamlit ke response Pydantic. supabase_client.fetch_* dipanggil
apa adanya, tidak dimodifikasi.
"""
from __future__ import annotations

import pandas as pd

from supabase_client import fetch_screener_results, fetch_ongoing_positions, fetch_last_update

from api.core.serialize import to_float, to_int, to_str_or_none, to_bool
from api.schemas.screener import ScreenerRow, BuyTomorrowRow, OpenPositionRow, ScreenerResponse


def get_screener(client) -> ScreenerResponse:
    screener_df = fetch_screener_results(client)
    last_update = fetch_last_update(client)
    updated_at = to_str_or_none(last_update.get("run_at")) if last_update else None

    if screener_df.empty:
        return ScreenerResponse(updated_at=updated_at, rows=[], buy_tomorrow=[], ongoing_positions=[])

    rows = [
        ScreenerRow(
            ticker=r["ticker"],
            sektor=to_str_or_none(r.get("sektor")),
            last_close=to_float(r.get("last_close")),
            last_date=to_str_or_none(r.get("last_date")),
            signal_today=to_str_or_none(r.get("signal_today")),
            signal_strength=to_int(r.get("signal_strength")),
            trend=to_str_or_none(r.get("trend")),
            rsi=to_float(r.get("rsi")),
            atr=to_float(r.get("atr")),
            winrate=to_float(r.get("winrate")),
            expectancy_pct=to_float(r.get("expectancy_pct")),
            profit_factor=to_float(r.get("profit_factor")),
            max_drawdown_pct=to_float(r.get("max_drawdown_pct")),
            n_trades=to_int(r.get("n_trades")),
            sharpe_rough=to_float(r.get("sharpe_rough")),
            is_idx30=to_bool(r.get("is_idx30")),
            is_lq45=to_bool(r.get("is_lq45")),
        )
        for _, r in screener_df.iterrows()
    ]

    buy_tomorrow: list[BuyTomorrowRow] = []
    pending = fetch_ongoing_positions(client, ["PENDING_ENTRY"])
    if not pending.empty:
        merged = pending.merge(
            screener_df[["ticker", "sektor", "winrate", "expectancy_pct", "profit_factor",
                         "last_close", "signal_strength"]],
            on="ticker", how="left",
        ).sort_values("expectancy_pct", ascending=False)
        for _, r in merged.iterrows():
            buy_tomorrow.append(BuyTomorrowRow(
                ticker=r["ticker"], sektor=to_str_or_none(r.get("sektor")),
                planned_entry_date=str(r["planned_entry_date"]),
                signal_strength=to_int(r.get("signal_strength")), winrate=to_float(r.get("winrate")),
                expectancy_pct=to_float(r.get("expectancy_pct")), profit_factor=to_float(r.get("profit_factor")),
                last_close=to_float(r.get("last_close")),
            ))

    ongoing_positions: list[OpenPositionRow] = []
    open_pos = fetch_ongoing_positions(client, ["OPEN"])
    if not open_pos.empty:
        merged = open_pos.merge(
            screener_df[["ticker", "sektor", "last_close", "last_date"]], on="ticker", how="left",
        )
        merged["entry_date_dt"] = pd.to_datetime(merged["entry_date"])
        merged["last_date_dt"] = pd.to_datetime(merged["last_date"])
        merged["return_pct_now"] = (
            (merged["last_close"] - merged["entry_price"]) / merged["entry_price"] * 100
        ).round(2)
        merged["hold_days_calc"] = (merged["last_date_dt"] - merged["entry_date_dt"]).dt.days
        merged = merged.sort_values("return_pct_now", ascending=False)
        for _, r in merged.iterrows():
            ongoing_positions.append(OpenPositionRow(
                ticker=r["ticker"], sektor=to_str_or_none(r.get("sektor")),
                entry_price=to_float(r.get("entry_price")), tp_price=to_float(r.get("tp_price")),
                sl_price=to_float(r.get("sl_price")), entry_date=to_str_or_none(r.get("entry_date")),
                last_close=to_float(r.get("last_close")), last_date=to_str_or_none(r.get("last_date")),
                return_pct_now=to_float(r.get("return_pct_now")), hold_days=to_int(r.get("hold_days_calc")),
            ))

    return ScreenerResponse(
        updated_at=updated_at, rows=rows, buy_tomorrow=buy_tomorrow, ongoing_positions=ongoing_positions,
    )
