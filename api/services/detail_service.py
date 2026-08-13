"""
api/services/detail_service.py
================================
Port dari views/detail.py. price_history dibaca APA ADANYA dari Supabase
(sudah berisi indikator+sinyal precomputed oleh worker via signals.py) --
service ini TIDAK memanggil generate_signals() ulang, murni membaca &
menyusun ulang jadi bentuk response.
"""
from __future__ import annotations

import pandas as pd
from fastapi import HTTPException

from supabase_client import (
    fetch_screener_results, fetch_price_history, fetch_backtest_trades, fetch_ongoing_positions,
)

from api.core.serialize import to_float, to_int, to_str_or_none
from api.schemas.detail import ActivePosition, DetailMetrics, PriceBar, TradeRow, TickerDetailResponse


def _price_change(d: pd.DataFrame) -> tuple[float | None, float | None, float | None]:
    """Identik _price_change() di views/detail.py."""
    if d.empty:
        return None, None, None
    last_close = float(d["Close"].iloc[-1])
    if len(d) < 2:
        return last_close, None, None
    prev_close = float(d["Close"].iloc[-2])
    change = last_close - prev_close
    change_pct = (change / prev_close * 100) if prev_close else None
    return last_close, change, change_pct


def get_ticker_detail(client, ticker: str) -> TickerDetailResponse:
    screener_df = fetch_screener_results(client)
    if screener_df.empty or ticker not in screener_df["ticker"].values:
        raise HTTPException(404, f"Ticker {ticker} tidak ditemukan di screener_results.")
    row = screener_df[screener_df["ticker"] == ticker].iloc[0]

    d = fetch_price_history(client, ticker)
    trades_df = fetch_backtest_trades(client, ticker)
    total_return = float(trades_df["return_pct"].sum()) if not trades_df.empty else None

    last_close, change, change_pct = _price_change(d)

    active_position = None
    active_positions = fetch_ongoing_positions(client, ["PENDING_ENTRY", "OPEN"])
    if not active_positions.empty:
        match = active_positions[active_positions["ticker"] == ticker]
        if not match.empty:
            p = match.iloc[0]
            active_position = ActivePosition(
                status=p["status"],
                planned_entry_date=to_str_or_none(p.get("planned_entry_date")),
                entry_date=to_str_or_none(p.get("entry_date")),
                entry_price=to_float(p.get("entry_price")),
                tp_price=to_float(p.get("tp_price")),
                sl_price=to_float(p.get("sl_price")),
            )

    price_history = [
        PriceBar(
            date=idx.strftime("%Y-%m-%d"),
            open=to_float(r.get("Open")), high=to_float(r.get("High")),
            low=to_float(r.get("Low")), close=to_float(r.get("Close")),
            volume=to_float(r.get("Volume")),
            sma20=to_float(r.get("SMA20")), sma50=to_float(r.get("SMA50")), sma200=to_float(r.get("SMA200")),
            rsi14=to_float(r.get("RSI14")), macd=to_float(r.get("MACD")),
            macd_signal=to_float(r.get("MACD_Signal")), macd_hist=to_float(r.get("MACD_Hist")),
            signal=to_int(r.get("Signal")) or 0,
        )
        for idx, r in d.iterrows()
    ]

    trades = [
        TradeRow(
            entry_date=to_str_or_none(t.get("entry_date")), exit_date=to_str_or_none(t.get("exit_date")),
            entry_price=float(t["entry_price"]), exit_price=float(t["exit_price"]),
            return_pct=float(t["return_pct"]), reason=t["reason"], hold_days=int(t["hold_days"]),
        )
        for _, t in trades_df.iterrows()
    ] if not trades_df.empty else []

    return TickerDetailResponse(
        ticker=ticker,
        sektor=to_str_or_none(row.get("sektor")),
        last_close=last_close if last_close is not None else to_float(row.get("last_close")),
        change=change, change_pct=change_pct,
        signal_today=to_str_or_none(row.get("signal_today")),
        signal_strength=to_int(row.get("signal_strength")),
        active_position=active_position,
        metrics=DetailMetrics(
            winrate=to_float(row.get("winrate")), expectancy_pct=to_float(row.get("expectancy_pct")),
            profit_factor=to_float(row.get("profit_factor")), max_drawdown_pct=to_float(row.get("max_drawdown_pct")),
            total_return_pct=total_return,
        ),
        price_history=price_history, trades=trades,
    )
