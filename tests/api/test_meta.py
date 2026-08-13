from __future__ import annotations

import api.services.meta_service as meta_service


def test_indicators_meta(client):
    resp = client.get("/api/meta/indicators")
    assert resp.status_code == 200
    data = resp.json()
    assert data["max_indicators_selected"] == 8
    assert "Trend" in data["categories"]
    keys = {i["key"] for i in data["indicators"]}
    assert "sma" in keys and "rsi" in keys and "supertrend" in keys


def test_tickers_meta(client):
    resp = client.get("/api/meta/tickers")
    assert resp.status_code == 200
    data = resp.json()
    assert "Perbankan" in data["sectors"]
    assert "BBCA" in data["sectors"]["Perbankan"]
    assert len(data["idx30"]) == 30


def test_last_update(client, monkeypatch):
    monkeypatch.setattr(
        meta_service, "fetch_last_update",
        lambda c: {"run_at": "2026-08-07T09:35:00+00:00", "tickers_processed": 45,
                   "tickers_failed": 0, "status": "OK"},
    )
    resp = client.get("/api/meta/last-update")
    assert resp.status_code == 200
    assert resp.json()["status"] == "OK"


def test_last_update_kosong(client, monkeypatch):
    monkeypatch.setattr(meta_service, "fetch_last_update", lambda c: None)
    resp = client.get("/api/meta/last-update")
    assert resp.status_code == 200
    assert resp.json()["run_at"] is None


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
