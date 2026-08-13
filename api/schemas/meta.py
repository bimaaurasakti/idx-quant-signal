from __future__ import annotations

from pydantic import BaseModel


class IndicatorParamSpec(BaseModel):
    type: str
    default: float
    min: float | None
    max: float | None


class IndicatorSpec(BaseModel):
    key: str
    label: str
    category: str
    tier: int
    overlay: bool
    params: dict[str, IndicatorParamSpec]


class IndicatorsMetaResponse(BaseModel):
    indicators: list[IndicatorSpec]
    categories: list[str]
    max_indicators_selected: int


class LastUpdateResponse(BaseModel):
    run_at: str | None
    tickers_processed: int | None
    tickers_failed: int | None
    status: str | None


class TickersMetaResponse(BaseModel):
    sectors: dict[str, list[str]]
    idx30: list[str]
