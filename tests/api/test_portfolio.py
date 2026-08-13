from __future__ import annotations

import pandas as pd

import api.services.portfolio_service as portfolio_service


def _fake_closed() -> pd.DataFrame:
    return pd.DataFrame([
        {"ticker": "BBCA", "status": "CLOSED_TP", "signal_date": "2026-06-01", "entry_date": "2026-06-02",
         "entry_price": 9700.0, "exit_date": "2026-06-09", "exit_price": 9880.0, "return_pct": 1.86},
        {"ticker": "TLKM", "status": "CLOSED_SL", "signal_date": "2026-05-10", "entry_date": "2026-05-11",
         "entry_price": 3200.0, "exit_date": "2026-05-14", "exit_price": 3120.0, "return_pct": -2.5},
    ])


def test_portfolio_endpoint(client, monkeypatch):
    monkeypatch.setattr(portfolio_service, "fetch_closed_positions", lambda c: _fake_closed())

    resp = client.get("/api/portfolio")
    assert resp.status_code == 200
    data = resp.json()

    assert len(data["positions"]) == 2
    tickers = {p["ticker"] for p in data["positions"]}
    assert tickers == {"BBCA", "TLKM"}
    # sektor & hold_days harus sudah dihitung server-side (get_sector_of + selisih tanggal)
    bbca = next(p for p in data["positions"] if p["ticker"] == "BBCA")
    assert bbca["sektor"] == "Perbankan"
    assert bbca["hold_days"] == 7


def test_portfolio_kosong(client, monkeypatch):
    monkeypatch.setattr(portfolio_service, "fetch_closed_positions", lambda c: pd.DataFrame())
    resp = client.get("/api/portfolio")
    assert resp.status_code == 200
    assert resp.json()["positions"] == []
