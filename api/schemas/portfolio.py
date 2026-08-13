from __future__ import annotations

from pydantic import BaseModel


class ClosedPosition(BaseModel):
    ticker: str
    sektor: str
    status: str
    signal_date: str | None
    entry_date: str
    entry_price: float
    exit_date: str
    exit_price: float
    return_pct: float
    hold_days: int


class PortfolioResponse(BaseModel):
    positions: list[ClosedPosition]
