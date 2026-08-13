from __future__ import annotations
from typing import Literal

from pydantic import BaseModel, Field


class BacktestRunRequest(BaseModel):
    ticker: str
    period: Literal["1y", "2y", "3y", "5y"] = "5y"
    selected_indicators: list[str] = Field(min_length=1, max_length=8)
    params: dict[str, dict[str, float]] = Field(default_factory=dict)
    confirmation_threshold: int = 1
    tp_multiple: float = 2.0
    sl_multiple: float = 1.0
    max_hold_days: int = 20


class Bar(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class IndicatorSeries(BaseModel):
    key: str
    label: str
    overlay: bool
    values: list[float | None]


class Trade(BaseModel):
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    return_pct: float
    reason: str
    hold_days: int


class BacktestMetrics(BaseModel):
    n_trades: int
    winrate: float | None
    avg_win_pct: float | None
    avg_loss_pct: float | None
    expectancy_pct: float | None
    profit_factor: float | None
    max_drawdown_pct: float | None
    sharpe_rough: float | None


class LastTradeConfirmation(BaseModel):
    filled: int
    total: int


class BacktestRunResponse(BaseModel):
    ticker: str
    bars: list[Bar]
    indicator_series: list[IndicatorSeries]
    bullish_count: list[int]
    bearish_count: list[int]
    signal: list[int]
    trades: list[Trade]
    metrics: BacktestMetrics
    equity_curve: list[float]
    last_trade_confirmation: LastTradeConfirmation | None
