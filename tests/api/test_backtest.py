from __future__ import annotations

import numpy as np
import pandas as pd

import api.services.backtest_service as backtest_service


def _fake_price_history(n: int = 300) -> pd.DataFrame:
    rng = np.random.default_rng(13)
    dates = pd.date_range("2024-01-01", periods=n, freq="B")
    returns = rng.normal(0.0008, 0.012, n)
    close = 1000.0 * np.cumprod(1 + returns)
    high = close * (1 + np.abs(rng.normal(0, 0.004, n)))
    low = close * (1 - np.abs(rng.normal(0, 0.004, n)))
    open_ = low + (high - low) * rng.uniform(0.2, 0.8, n)
    volume = rng.integers(1_000_000, 5_000_000, n).astype(float)
    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume}, index=dates,
    )


def _payload(**overrides) -> dict:
    base = {
        "ticker": "BBCA", "period": "1y",
        "selected_indicators": ["ema_crossover", "rsi"],
        "params": {"ema_crossover": {"fast": 13, "slow": 21}},
        "confirmation_threshold": 1,
        "tp_multiple": 2.0, "sl_multiple": 1.0, "max_hold_days": 20,
    }
    base.update(overrides)
    return base


def test_backtest_run(client, monkeypatch):
    monkeypatch.setattr(backtest_service, "fetch_price_history", lambda c, t: _fake_price_history())

    resp = client.post("/api/backtest/run", json=_payload())
    assert resp.status_code == 200
    data = resp.json()

    assert data["ticker"] == "BBCA"
    assert len(data["bars"]) > 0
    assert len(data["bars"]) == len(data["signal"]) == len(data["bullish_count"])
    # overlay=True (ema_crossover) + subplot (rsi) -> minimal 2 seri indikator (Fast & Slow EMA + RSI)
    assert len(data["indicator_series"]) >= 2
    assert set(data["metrics"].keys()) == {
        "n_trades", "winrate", "avg_win_pct", "avg_loss_pct", "expectancy_pct",
        "profit_factor", "max_drawdown_pct", "sharpe_rough",
    }
    assert isinstance(data["equity_curve"], list)


def test_backtest_indikator_tidak_dikenal_ditolak_server(client, monkeypatch):
    """Validasi ulang di server -- meskipun frontend seharusnya sudah
    memfilter opsi, endpoint TIDAK BOLEH percaya begitu saja (§4.6)."""
    monkeypatch.setattr(backtest_service, "fetch_price_history", lambda c, t: _fake_price_history())
    resp = client.post("/api/backtest/run", json=_payload(selected_indicators=["indikator_ngarang"]))
    assert resp.status_code == 422


def test_backtest_lebih_dari_8_indikator_ditolak(client, monkeypatch):
    monkeypatch.setattr(backtest_service, "fetch_price_history", lambda c, t: _fake_price_history())
    sembilan = ["sma", "ema", "wma", "macd", "adx", "rsi", "cci", "roc", "obv"]
    resp = client.post("/api/backtest/run", json=_payload(selected_indicators=sembilan, params={}))
    assert resp.status_code == 422


def test_backtest_data_terlalu_pendek(client, monkeypatch):
    monkeypatch.setattr(backtest_service, "fetch_price_history", lambda c, t: _fake_price_history(n=30))
    resp = client.post("/api/backtest/run", json=_payload(period="5y", selected_indicators=["rsi"], params={}))
    assert resp.status_code == 422
    assert "terlalu pendek" in resp.json()["detail"]


def test_backtest_ticker_tidak_ada_datanya(client, monkeypatch):
    monkeypatch.setattr(backtest_service, "fetch_price_history", lambda c, t: pd.DataFrame())
    resp = client.post("/api/backtest/run", json=_payload())
    assert resp.status_code == 404
