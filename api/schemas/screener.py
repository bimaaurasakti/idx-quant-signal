from __future__ import annotations

from pydantic import BaseModel


class ScreenerRow(BaseModel):
    ticker: str
    sektor: str | None
    last_close: float | None
    last_date: str | None
    signal_today: str | None
    signal_strength: int | None
    trend: str | None
    rsi: float | None
    atr: float | None
    winrate: float | None
    expectancy_pct: float | None
    profit_factor: float | None
    max_drawdown_pct: float | None
    n_trades: int | None
    sharpe_rough: float | None
    is_idx30: bool
    is_lq45: bool


class BuyTomorrowRow(BaseModel):
    ticker: str
    sektor: str | None
    planned_entry_date: str
    signal_strength: int | None
    winrate: float | None
    expectancy_pct: float | None
    profit_factor: float | None
    last_close: float | None


class OpenPositionRow(BaseModel):
    ticker: str
    sektor: str | None
    entry_price: float | None
    tp_price: float | None
    sl_price: float | None
    entry_date: str | None
    last_close: float | None
    last_date: str | None
    return_pct_now: float | None
    hold_days: int | None


class ScreenerResponse(BaseModel):
    updated_at: str | None
    rows: list[ScreenerRow]
    buy_tomorrow: list[BuyTomorrowRow]
    ongoing_positions: list[OpenPositionRow]
