from __future__ import annotations

from fastapi import APIRouter, Depends

from api.core.deps import get_supabase_client
from api.schemas.screener import ScreenerResponse
from api.services import screener_service

router = APIRouter(prefix="/api/screener", tags=["screener"])


@router.get("", response_model=ScreenerResponse)
async def get_screener(client=Depends(get_supabase_client)) -> ScreenerResponse:
    return screener_service.get_screener(client)
