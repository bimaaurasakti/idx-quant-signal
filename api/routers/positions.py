from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from api.core.deps import get_supabase_client
from api.schemas.positions import PositionsResponse
from api.services import positions_service

router = APIRouter(prefix="/api/positions", tags=["positions"])

_VALID_STATUSES = {"PENDING_ENTRY", "OPEN", "CLOSED_TP", "CLOSED_SL", "CLOSED_SIGNAL", "CLOSED_TIME"}


@router.get("", response_model=PositionsResponse)
async def get_positions(
    status: list[str] = Query(default=["OPEN"]), client=Depends(get_supabase_client),
) -> PositionsResponse:
    statuses = [s for s in status if s in _VALID_STATUSES]
    return positions_service.get_positions(client, statuses)
