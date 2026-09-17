"""
custom_backtest.py
===================
Signal generation dari kombinasi indikator pilihan user.
"""
from __future__ import annotations
import pandas as pd

import indicators as ind
from indicator_registry import INDICATOR_SPECS, default_params_for


def generate_custom_signals(
    df: pd.DataFrame,
    selected_indicators: list[str],
    params: dict[str, dict] | None = None,
    confirmation_threshold: int = 1,
) -> pd.DataFrame:
    params = params or {}
    out = df.copy()
    out["ATR14"] = ind.atr(out, 14)

    if not selected_indicators:
        out["BullishCount"] = 0
        out["BearishCount"] = 0
        out["Signal"] = 0
        return out

    bullish_votes, bearish_votes = [], []
    for key in selected_indicators:
        spec = INDICATOR_SPECS[key]
        p = {**default_params_for(key), **params.get(key, {})}
        value = spec["compute"](out, p, spec)
        bullish, bearish = spec["vote"](out, value, p, spec)
        bullish_votes.append(bullish.fillna(False))
        bearish_votes.append(bearish.fillna(False))
        _attach_chart_columns(out, key, value)

    bullish_count = pd.concat(bullish_votes, axis=1).sum(axis=1)
    bearish_count = pd.concat(bearish_votes, axis=1).sum(axis=1)
    out["BullishCount"] = bullish_count
    out["BearishCount"] = bearish_count

    threshold = max(1, min(confirmation_threshold, len(selected_indicators)))
    prev_bullish = bullish_count.shift(1).fillna(0)
    prev_bearish = bearish_count.shift(1).fillna(0)
    buy_trigger = (bullish_count >= threshold) & (prev_bullish < threshold)
    sell_trigger = (bearish_count >= threshold) & (prev_bearish < threshold)

    signal = pd.Series(0, index=out.index)
    signal[sell_trigger] = -1
    signal[buy_trigger & ~sell_trigger] = 1
    out["Signal"] = signal
    return out


def _attach_chart_columns(out: pd.DataFrame, key: str, value) -> None:
    if isinstance(value, pd.DataFrame):
        for col in value.columns:
            out[f"{key}_{col}"] = value[col]
    else:
        out[f"{key}_value"] = value


def validate_min_bars(df: pd.DataFrame, min_bars: int = 60) -> tuple[bool, str]:
    valid = df["Close"].dropna() if df is not None and not df.empty else pd.Series(dtype=float)
    if len(valid) < min_bars:
        return False, (
            f"Data historis terlalu pendek ({len(valid)} bar valid, minimal {min_bars}) "
            "-- coba periode lebih panjang atau kurangi periode indikator terpanjang yg dipilih."
        )
    return True, ""


def compute_equity_curve(trades: list[dict]) -> pd.Series:
    if not trades:
        return pd.Series(dtype=float)
    returns = pd.Series([t["return_pct"] for t in trades])
    return (1 + returns / 100).cumprod()
