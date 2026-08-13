from __future__ import annotations

from pydantic import BaseModel


class PositionRow(BaseModel):
    id: int | None = None
    ticker: str
    status: str
    signal_date: str | None = None
    planned_entry_date: str | None = None
    entry_date: str | None = None
    entry_price: float | None = None
    atr_at_signal: float | None = None
    tp_price: float | None = None
    sl_price: float | None = None
    exit_date: str | None = None
    exit_price: float | None = None
    exit_reason: str | None = None
    return_pct: float | None = None


class PositionsResponse(BaseModel):
    positions: list[PositionRow]
