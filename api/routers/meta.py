from __future__ import annotations

from fastapi import APIRouter, Depends

from api.core.deps import get_supabase_client
from api.schemas.meta import IndicatorsMetaResponse, LastUpdateResponse, TickersMetaResponse
from api.services import meta_service

router = APIRouter(prefix="/api/meta", tags=["meta"])


@router.get("/indicators", response_model=IndicatorsMetaResponse)
async def indicators_meta() -> IndicatorsMetaResponse:
    return meta_service.get_indicators_meta()


@router.get("/tickers", response_model=TickersMetaResponse)
async def tickers_meta() -> TickersMetaResponse:
    return meta_service.get_tickers_meta()


@router.get("/last-update", response_model=LastUpdateResponse)
async def last_update(client=Depends(get_supabase_client)) -> LastUpdateResponse:
    return meta_service.get_last_update(client)
