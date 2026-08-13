from __future__ import annotations

from fastapi import APIRouter, Depends

from api.core.deps import get_supabase_client
from api.schemas.detail import TickerDetailResponse
from api.services import detail_service

router = APIRouter(prefix="/api/tickers", tags=["detail"])


@router.get("/{ticker}", response_model=TickerDetailResponse)
async def get_ticker_detail(ticker: str, client=Depends(get_supabase_client)) -> TickerDetailResponse:
    return detail_service.get_ticker_detail(client, ticker.upper())
