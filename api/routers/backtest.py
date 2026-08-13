from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from api.core.deps import get_supabase_client
from api.core.rate_limit import limiter
from api.schemas.backtest import BacktestRunRequest, BacktestRunResponse
from api.services import backtest_service

router = APIRouter(prefix="/api/backtest", tags=["backtest"])


@router.post("/run", response_model=BacktestRunResponse)
@limiter.limit("10/minute")
async def run_backtest(
    request: Request, body: BacktestRunRequest, client=Depends(get_supabase_client),
) -> BacktestRunResponse:
    return await backtest_service.run_backtest(client, body)
