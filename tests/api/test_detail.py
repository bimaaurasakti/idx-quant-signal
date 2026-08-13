from __future__ import annotations

import numpy as np
import pandas as pd

import api.services.detail_service as detail_service


def _fake_screener() -> pd.DataFrame:
    return pd.DataFrame([{
        "ticker": "BBCA", "sektor": "Perbankan", "last_close": 9850.0, "last_date": "2026-08-07",
        "signal_today": "BUY", "signal_strength": 3, "trend": "Uptrend", "rsi": 58.0, "atr": 95.0,
        "winrate": 62.5, "expectancy_pct": 1.8, "profit_factor": 2.1, "max_drawdown_pct": -7.5,
        "n_trades": 18, "sharpe_rough": 1.3, "is_idx30": True, "is_lq45": True,
    }])


def _fake_price_history(n: int = 80) -> pd.DataFrame:
    dates = pd.date_range("2026-04-01", periods=n, freq="B")
    close = 9000.0 + np.cumsum(np.random.default_rng(1).normal(5, 40, n))
    close[-1] = close[-2] + 50.0  # bar terakhir naik pasti -> change positif, gampang divalidasi
    return pd.DataFrame({
        "Open": close - 10, "High": close + 20, "Low": close - 20, "Close": close, "Volume": 2_000_000,
        "SMA20": close, "SMA50": close, "SMA200": close, "RSI14": 55.0, "MACD": 1.2,
        "MACD_Signal": 1.0, "MACD_Hist": 0.2, "ATR14": 95.0,
        "Signal": [1 if i % 40 == 0 else 0 for i in range(n)],
    }, index=dates)


def _fake_trades() -> pd.DataFrame:
    return pd.DataFrame([
        {"ticker": "BBCA", "entry_date": "2026-06-01", "exit_date": "2026-06-08",
         "entry_price": 9700.0, "exit_price": 9880.0, "return_pct": 1.86, "reason": "TP", "hold_days": 7},
    ])


def test_ticker_detail_endpoint(client, monkeypatch):
    monkeypatch.setattr(detail_service, "fetch_screener_results", lambda c: _fake_screener())
    monkeypatch.setattr(detail_service, "fetch_price_history", lambda c, t: _fake_price_history())
    monkeypatch.setattr(detail_service, "fetch_backtest_trades", lambda c, t: _fake_trades())
    monkeypatch.setattr(detail_service, "fetch_ongoing_positions", lambda c, statuses: pd.DataFrame())

    resp = client.get("/api/tickers/BBCA")
    assert resp.status_code == 200
    data = resp.json()

    assert data["ticker"] == "BBCA"
    assert data["sektor"] == "Perbankan"
    assert len(data["price_history"]) == 80
    assert data["change"] is not None and data["change"] > 0  # bar terakhir sengaja naik
    assert len(data["trades"]) == 1
    assert data["metrics"]["winrate"] == 62.5
    assert data["active_position"] is None


def test_ticker_detail_dengan_posisi_pending(client, monkeypatch):
    monkeypatch.setattr(detail_service, "fetch_screener_results", lambda c: _fake_screener())
    monkeypatch.setattr(detail_service, "fetch_price_history", lambda c, t: _fake_price_history())
    monkeypatch.setattr(detail_service, "fetch_backtest_trades", lambda c, t: pd.DataFrame())

    def _fake_positions(c, statuses):
        return pd.DataFrame([{
            "ticker": "BBCA", "status": "PENDING_ENTRY", "planned_entry_date": "2026-08-10",
            "entry_date": None, "entry_price": None, "tp_price": None, "sl_price": None,
        }])

    monkeypatch.setattr(detail_service, "fetch_ongoing_positions", _fake_positions)

    resp = client.get("/api/tickers/BBCA")
    assert resp.status_code == 200
    data = resp.json()
    assert data["active_position"]["status"] == "PENDING_ENTRY"
    assert data["active_position"]["planned_entry_date"] == "2026-08-10"


def test_ticker_detail_not_found(client, monkeypatch):
    monkeypatch.setattr(detail_service, "fetch_screener_results", lambda c: _fake_screener())
    resp = client.get("/api/tickers/ZZZZ")
    assert resp.status_code == 404
