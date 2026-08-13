from __future__ import annotations

from pydantic import BaseModel


class ActivePosition(BaseModel):
    status: str
    planned_entry_date: str | None = None
    entry_date: str | None = None
    entry_price: float | None = None
    tp_price: float | None = None
    sl_price: float | None = None


class DetailMetrics(BaseModel):
    winrate: float | None
    expectancy_pct: float | None
    profit_factor: float | None
    max_drawdown_pct: float | None
    total_return_pct: float | None


class PriceBar(BaseModel):
    date: str
    open: float | None
    high: float | None
    low: float | None
    close: float | None
    volume: float | None
    sma20: float | None
    sma50: float | None
    sma200: float | None
    rsi14: float | None
    macd: float | None
    macd_signal: float | None
    macd_hist: float | None
    signal: int


class TradeRow(BaseModel):
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    return_pct: float
    reason: str
    hold_days: int


class TickerDetailResponse(BaseModel):
    ticker: str
    sektor: str | None
    last_close: float | None
    change: float | None
    change_pct: float | None
    signal_today: str | None
    signal_strength: int | None
    active_position: ActivePosition | None
    metrics: DetailMetrics
    price_history: list[PriceBar]
    trades: list[TradeRow]
