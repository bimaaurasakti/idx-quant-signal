"""
api/services/meta_service.py
=============================
Membungkus indicator_registry.py & tickers_idx.py (TIDAK DIUBAH) menjadi
response JSON-ready. Dipakai frontend utk membangun UI pemilih indikator
Backtest Lab secara dinamis -- single source of truth metadata tetap di
Python, bukan diduplikasi hardcode di TypeScript.
"""
from __future__ import annotations

from indicator_registry import INDICATOR_SPECS, CATEGORIES, MAX_INDICATORS_SELECTED
from tickers_idx import IDX_TICKERS, IDX30_TICKERS
from supabase_client import fetch_last_update

from api.core.serialize import to_int, to_str_or_none
from api.schemas.meta import (
    IndicatorSpec, IndicatorParamSpec, IndicatorsMetaResponse,
    LastUpdateResponse, TickersMetaResponse,
)


def get_indicators_meta() -> IndicatorsMetaResponse:
    indicators = []
    for key, spec in INDICATOR_SPECS.items():
        params = {
            name: IndicatorParamSpec(
                type=cfg["type"], default=cfg["default"], min=cfg["min"], max=cfg["max"],
            )
            for name, cfg in spec["params"].items()
        }
        indicators.append(IndicatorSpec(
            key=key, label=spec["label"], category=spec["category"],
            tier=spec["tier"], overlay=spec["overlay"], params=params,
        ))
    return IndicatorsMetaResponse(
        indicators=indicators,
        categories=list(CATEGORIES),
        max_indicators_selected=MAX_INDICATORS_SELECTED,
    )


def get_tickers_meta() -> TickersMetaResponse:
    return TickersMetaResponse(sectors=IDX_TICKERS, idx30=sorted(IDX30_TICKERS))


def get_last_update(client) -> LastUpdateResponse:
    row = fetch_last_update(client)
    if row is None:
        return LastUpdateResponse(run_at=None, tickers_processed=None, tickers_failed=None, status=None)
    return LastUpdateResponse(
        run_at=to_str_or_none(row.get("run_at")),
        tickers_processed=to_int(row.get("tickers_processed")),
        tickers_failed=to_int(row.get("tickers_failed")),
        status=row.get("status"),
    )
