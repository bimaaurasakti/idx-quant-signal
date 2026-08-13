from __future__ import annotations

from fastapi import APIRouter, Depends

from api.core.deps import get_supabase_client
from api.schemas.portfolio import PortfolioResponse
from api.services import portfolio_service

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.get("", response_model=PortfolioResponse)
async def get_portfolio(client=Depends(get_supabase_client)) -> PortfolioResponse:
    return portfolio_service.get_portfolio(client)
