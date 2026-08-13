from __future__ import annotations

from supabase_client import fetch_ongoing_positions

from api.core.serialize import to_float, to_int, to_str_or_none
from api.schemas.positions import PositionRow, PositionsResponse


def get_positions(client, statuses: list[str]) -> PositionsResponse:
    df = fetch_ongoing_positions(client, statuses)
    if df.empty:
        return PositionsResponse(positions=[])

    rows = [
        PositionRow(
            id=to_int(r.get("id")),
            ticker=r["ticker"], status=r["status"],
            signal_date=to_str_or_none(r.get("signal_date")),
            planned_entry_date=to_str_or_none(r.get("planned_entry_date")),
            entry_date=to_str_or_none(r.get("entry_date")),
            entry_price=to_float(r.get("entry_price")),
            atr_at_signal=to_float(r.get("atr_at_signal")),
            tp_price=to_float(r.get("tp_price")),
            sl_price=to_float(r.get("sl_price")),
            exit_date=to_str_or_none(r.get("exit_date")),
            exit_price=to_float(r.get("exit_price")),
            exit_reason=to_str_or_none(r.get("exit_reason")),
            return_pct=to_float(r.get("return_pct")),
        )
        for _, r in df.iterrows()
    ]
    return PositionsResponse(positions=rows)
