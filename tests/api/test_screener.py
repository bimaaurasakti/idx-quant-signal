from __future__ import annotations

import pandas as pd

import api.services.screener_service as screener_service


def _fake_screener_results(client) -> pd.DataFrame:
    return pd.DataFrame([
        {"ticker": "BBCA", "sektor": "Perbankan", "last_close": 9850.0, "last_date": "2026-08-07",
         "signal_today": "BUY", "signal_strength": 3, "trend": "Uptrend", "rsi": 58.0, "atr": 95.0,
         "winrate": 62.5, "expectancy_pct": 1.8, "profit_factor": 2.1, "max_drawdown_pct": -7.5,
         "n_trades": 18, "sharpe_rough": 1.3, "is_idx30": True, "is_lq45": True},
        {"ticker": "TLKM", "sektor": "Telekomunikasi_Infrastruktur", "last_close": 3200.0, "last_date": "2026-08-07",
         "signal_today": "HOLD", "signal_strength": 1, "trend": "Sideways/Mixed", "rsi": 48.0, "atr": 40.0,
         "winrate": 51.0, "expectancy_pct": 0.4, "profit_factor": 1.1, "max_drawdown_pct": -12.0,
         "n_trades": 22, "sharpe_rough": 0.4, "is_idx30": True, "is_lq45": True},
    ])


def _fake_pending() -> pd.DataFrame:
    return pd.DataFrame([{
        "id": 1, "ticker": "BBCA", "status": "PENDING_ENTRY", "signal_date": "2026-08-07",
        "planned_entry_date": "2026-08-10", "entry_date": None, "entry_price": None,
        "atr_at_signal": 95.0, "tp_price": None, "sl_price": None,
    }])


def _fake_open() -> pd.DataFrame:
    return pd.DataFrame([{
        "id": 2, "ticker": "TLKM", "status": "OPEN", "signal_date": "2026-07-28",
        "planned_entry_date": "2026-07-29", "entry_date": "2026-07-29", "entry_price": 3100.0,
        "atr_at_signal": 40.0, "tp_price": 3180.0, "sl_price": 3060.0,
    }])


def _fake_ongoing(client, statuses):
    if statuses == ["PENDING_ENTRY"]:
        return _fake_pending()
    if statuses == ["OPEN"]:
        return _fake_open()
    return pd.DataFrame()


def test_screener_endpoint(client, monkeypatch):
    monkeypatch.setattr(screener_service, "fetch_screener_results", _fake_screener_results)
    monkeypatch.setattr(screener_service, "fetch_ongoing_positions", _fake_ongoing)
    monkeypatch.setattr(
        screener_service, "fetch_last_update",
        lambda c: {"run_at": "2026-08-07T09:35:00+00:00", "tickers_processed": 45,
                   "tickers_failed": 0, "status": "OK"},
    )

    resp = client.get("/api/screener")
    assert resp.status_code == 200
    data = resp.json()

    assert len(data["rows"]) == 2
    assert {r["ticker"] for r in data["rows"]} == {"BBCA", "TLKM"}

    assert len(data["buy_tomorrow"]) == 1
    assert data["buy_tomorrow"][0]["ticker"] == "BBCA"
    assert data["buy_tomorrow"][0]["sektor"] == "Perbankan"  # hasil merge dengan screener_df

    assert len(data["ongoing_positions"]) == 1
    op = data["ongoing_positions"][0]
    assert op["ticker"] == "TLKM"
    assert op["return_pct_now"] == round((3200.0 - 3100.0) / 3100.0 * 100, 2)

    assert data["updated_at"] is not None


def test_screener_kosong(client, monkeypatch):
    monkeypatch.setattr(screener_service, "fetch_screener_results", lambda c: pd.DataFrame())
    monkeypatch.setattr(screener_service, "fetch_last_update", lambda c: None)

    resp = client.get("/api/screener")
    assert resp.status_code == 200
    data = resp.json()
    assert data["rows"] == []
    assert data["buy_tomorrow"] == []
    assert data["ongoing_positions"] == []
