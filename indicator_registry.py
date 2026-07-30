"""
indicator_registry.py
======================
Layer metadata yang menjembatani fungsi komputasi murni di indicators.py
dengan UI dinamis (Backtest Lab) + custom signal engine (custom_backtest.py).

indicators.py TETAP jadi lapisan komputasi murni (konsisten dgn filosofi
"manual pakai pandas/numpy" -- lihat docstring file itu); registry ini
sengaja dipisah supaya indicators.py tidak "kotor" dengan concern UI/vote-rule.

DESAIN PENTING (lihat IMPLEMENTATION_PLAN_UI_BACKTEST_LAB.md §3.3):
Setiap entri `vote(df, value, params)` SELALU mengembalikan DUA Series
boolean terpisah `(bullish, bearish)` -- BUKAN derivasi satu dari yang
lain (bearish = NOT bullish). Mayoritas indikator memang saling melengkapi
scr alami, tapi beberapa (ADX terutama) punya zona netral sah. Desain
generik ini menghindari bug halus kalau dipaksa biner.

Semua vote rule berorientasi TREND-FOLLOWING (bukan mean-reversion),
konsisten dgn filosofi signals.py yang sudah ada.
"""
from __future__ import annotations
from typing import Any, Callable

import pandas as pd

import indicators as ind


def _param(default, lo=None, hi=None, ptype="int"):
    return {"type": ptype, "default": default, "min": lo, "max": hi}


def _p(params: dict, spec: dict, name: str):
    """Ambil nilai param dari dict user (kalau ada) atau default dari spec."""
    if params and name in params:
        return params[name]
    return spec["params"][name]["default"]


# ============================================================================
# Fungsi compute & vote per indikator. Semua menerima (df, params_dict).
# df: OHLCV PascalCase (Open/High/Low/Close/Volume), sudah lengkap 1 ticker.
# ============================================================================

def _compute_sma(df, p, spec):
    return ind.sma(df["Close"], _p(p, spec, "period"))


def _vote_price_vs_line(df, value, p, spec):
    bullish = df["Close"] > value
    bearish = df["Close"] < value
    return bullish, bearish


def _compute_ema(df, p, spec):
    return ind.ema(df["Close"], _p(p, spec, "period"))


def _compute_wma(df, p, spec):
    return ind.wma(df["Close"], _p(p, spec, "period"))


def _compute_ma_crossover(df, p, spec, ma_fn):
    fast = ma_fn(df["Close"], _p(p, spec, "fast"))
    slow = ma_fn(df["Close"], _p(p, spec, "slow"))
    return pd.DataFrame({"Fast": fast, "Slow": slow})


def _vote_crossover(df, value, p, spec):
    bullish = value["Fast"] > value["Slow"]
    bearish = value["Fast"] < value["Slow"]
    return bullish, bearish


def _compute_macd(df, p, spec):
    line, signal, hist = ind.macd(df["Close"], _p(p, spec, "fast"), _p(p, spec, "slow"), _p(p, spec, "signal"))
    return pd.DataFrame({"MACD": line, "Signal": signal, "Hist": hist})


def _vote_macd(df, value, p, spec):
    bullish = value["MACD"] > value["Signal"]
    bearish = value["MACD"] < value["Signal"]
    return bullish, bearish


def _compute_adx(df, p, spec):
    return ind.adx(df, _p(p, spec, "period"))


def _vote_adx(df, value, p, spec):
    threshold = _p(p, spec, "threshold")
    strong = value["ADX"] > threshold
    bullish = strong & (value["PlusDI"] > value["MinusDI"])
    bearish = strong & (value["MinusDI"] > value["PlusDI"])
    return bullish, bearish


def _compute_psar(df, p, spec):
    return ind.parabolic_sar(df, _p(p, spec, "step"), _p(p, spec, "max_step"))


def _compute_supertrend(df, p, spec):
    return ind.supertrend(df, _p(p, spec, "period"), _p(p, spec, "multiplier"))


def _vote_supertrend(df, value, p, spec):
    bullish = df["Close"] > value["Supertrend"]
    bearish = df["Close"] < value["Supertrend"]
    return bullish, bearish


def _compute_ichimoku(df, p, spec):
    return ind.ichimoku(df, _p(p, spec, "tenkan"), _p(p, spec, "kijun"), _p(p, spec, "senkou_b"))


def _vote_ichimoku(df, value, p, spec):
    cloud_top = value[["SenkouA", "SenkouB"]].max(axis=1)
    cloud_bottom = value[["SenkouA", "SenkouB"]].min(axis=1)
    bullish = df["Close"] > cloud_top
    bearish = df["Close"] < cloud_bottom
    return bullish, bearish


def _compute_vwap(df, p, spec):
    return ind.vwap_rolling(df, _p(p, spec, "period"))


def _compute_rsi(df, p, spec):
    return ind.rsi(df["Close"], _p(p, spec, "period"))


def _vote_midline_50(df, value, p, spec):
    bullish = value > 50
    bearish = value < 50
    return bullish, bearish


def _compute_stochastic(df, p, spec):
    return ind.stochastic(df, _p(p, spec, "k_period"), _p(p, spec, "d_period"))


def _compute_stochastic_rsi(df, p, spec):
    return ind.stochastic_rsi(df["Close"], _p(p, spec, "rsi_period"), _p(p, spec, "stoch_period"), _p(p, spec, "d_period"))


def _vote_k_vs_d(df, value, p, spec):
    bullish = value["K"] > value["D"]
    bearish = value["K"] < value["D"]
    return bullish, bearish


def _compute_cci(df, p, spec):
    return ind.cci(df, _p(p, spec, "period"))


def _vote_zero_line(df, value, p, spec):
    bullish = value > 0
    bearish = value < 0
    return bullish, bearish


def _compute_williams_r(df, p, spec):
    return ind.williams_r(df, _p(p, spec, "period"))


def _vote_williams(df, value, p, spec):
    bullish = value > -50
    bearish = value < -50
    return bullish, bearish


def _compute_roc(df, p, spec):
    return ind.roc(df["Close"], _p(p, spec, "period"))


def _compute_bollinger(df, p, spec):
    upper, mid, lower = ind.bollinger_bands(df["Close"], _p(p, spec, "period"), _p(p, spec, "num_std"))
    return pd.DataFrame({"Upper": upper, "Middle": mid, "Lower": lower})


def _vote_vs_middle(df, value, p, spec):
    bullish = df["Close"] > value["Middle"]
    bearish = df["Close"] < value["Middle"]
    return bullish, bearish


def _compute_keltner(df, p, spec):
    return ind.keltner_channels(df, _p(p, spec, "ema_window"), _p(p, spec, "atr_window"), _p(p, spec, "mult"))


def _compute_donchian(df, p, spec):
    return ind.donchian_channels(df, _p(p, spec, "period"))


def _vote_donchian_breakout(df, value, p, spec):
    # Beda dgn Bollinger/Keltner: Donchian dipakai sbg sinyal BREAKOUT
    # (gaya Turtle Trading) -- bullish saat Close bikin high N-hari baru,
    # bukan sekadar di atas garis tengah. Lihat §3.2 rencana implementasi.
    bullish = df["Close"] >= value["Upper"]
    bearish = df["Close"] <= value["Lower"]
    return bullish, bearish


def _compute_obv(df, p, spec):
    return ind.obv(df)


def _vote_vs_own_sma(df, value, p, spec):
    baseline = ind.sma(value, 20)
    bullish = value > baseline
    bearish = value < baseline
    return bullish, bearish


def _compute_mfi(df, p, spec):
    return ind.mfi(df, _p(p, spec, "period"))


def _compute_cmf(df, p, spec):
    return ind.cmf(df, _p(p, spec, "period"))


def _compute_ad_line(df, p, spec):
    return ind.ad_line(df)


# ============================================================================
# REGISTRY -- entri final. Urutan mengikuti tabel §3.2 rencana implementasi.
# ============================================================================
INDICATOR_SPECS: dict[str, dict[str, Any]] = {
    # ---------------- Trend ----------------
    "sma": {
        "label": "SMA (Simple Moving Average)", "category": "Trend", "tier": 1, "overlay": True,
        "params": {"period": _param(50, 5, 200)},
        "compute": _compute_sma, "vote": _vote_price_vs_line,
    },
    "ema": {
        "label": "EMA (Exponential Moving Average)", "category": "Trend", "tier": 1, "overlay": True,
        "params": {"period": _param(21, 2, 200)},
        "compute": _compute_ema, "vote": _vote_price_vs_line,
    },
    "wma": {
        "label": "WMA (Weighted Moving Average)", "category": "Trend", "tier": 1, "overlay": True,
        "params": {"period": _param(20, 2, 200)},
        "compute": _compute_wma, "vote": _vote_price_vs_line,
    },
    "sma_crossover": {
        "label": "SMA Crossover (Golden/Death Cross)", "category": "Trend", "tier": 1, "overlay": True,
        "params": {"fast": _param(50, 2, 200), "slow": _param(200, 5, 400)},
        "compute": lambda df, p, spec: _compute_ma_crossover(df, p, spec, ind.sma), "vote": _vote_crossover,
    },
    "ema_crossover": {
        "label": "EMA Crossover (Fast/Slow)", "category": "Trend", "tier": 1, "overlay": True,
        "params": {"fast": _param(13, 2, 100), "slow": _param(21, 3, 200)},
        "compute": lambda df, p, spec: _compute_ma_crossover(df, p, spec, ind.ema), "vote": _vote_crossover,
    },
    "macd": {
        "label": "MACD", "category": "Trend", "tier": 1, "overlay": False,
        "params": {"fast": _param(12, 2, 50), "slow": _param(26, 5, 100), "signal": _param(9, 2, 50)},
        "compute": _compute_macd, "vote": _vote_macd,
    },
    "adx": {
        "label": "ADX (+DI/-DI)", "category": "Trend", "tier": 1, "overlay": False,
        "params": {"period": _param(14, 2, 60), "threshold": _param(20, 5, 50)},
        "compute": _compute_adx, "vote": _vote_adx,
    },
    "psar": {
        "label": "Parabolic SAR", "category": "Trend", "tier": 2, "overlay": True,
        "params": {"step": _param(0.02, 0.01, 0.1, "float"), "max_step": _param(0.2, 0.1, 0.5, "float")},
        "compute": _compute_psar, "vote": _vote_price_vs_line,
    },
    "supertrend": {
        "label": "Supertrend", "category": "Trend", "tier": 2, "overlay": True,
        "params": {"period": _param(10, 2, 50), "multiplier": _param(3.0, 1.0, 6.0, "float")},
        "compute": _compute_supertrend, "vote": _vote_supertrend,
    },
    "ichimoku": {
        "label": "Ichimoku Cloud", "category": "Trend", "tier": 1, "overlay": True,
        "params": {"tenkan": _param(9, 2, 30), "kijun": _param(26, 5, 60), "senkou_b": _param(52, 10, 120)},
        "compute": _compute_ichimoku, "vote": _vote_ichimoku,
    },
    "vwap": {
        "label": "VWAP (Rolling N-hari)", "category": "Trend", "tier": 1, "overlay": True,
        "params": {"period": _param(20, 5, 100)},
        "compute": _compute_vwap, "vote": _vote_price_vs_line,
    },
    # ---------------- Momentum ----------------
    "rsi": {
        "label": "RSI", "category": "Momentum", "tier": 1, "overlay": False,
        "params": {"period": _param(14, 2, 50)},
        "compute": _compute_rsi, "vote": _vote_midline_50,
    },
    "stochastic": {
        "label": "Stochastic Oscillator", "category": "Momentum", "tier": 1, "overlay": False,
        "params": {"k_period": _param(14, 2, 50), "d_period": _param(3, 2, 20)},
        "compute": _compute_stochastic, "vote": _vote_k_vs_d,
    },
    "stochastic_rsi": {
        "label": "Stochastic RSI", "category": "Momentum", "tier": 1, "overlay": False,
        "params": {"rsi_period": _param(14, 2, 50), "stoch_period": _param(14, 2, 50), "d_period": _param(3, 2, 20)},
        "compute": _compute_stochastic_rsi, "vote": _vote_k_vs_d,
    },
    "cci": {
        "label": "CCI (Commodity Channel Index)", "category": "Momentum", "tier": 1, "overlay": False,
        "params": {"period": _param(20, 5, 60)},
        "compute": _compute_cci, "vote": _vote_zero_line,
    },
    "williams_r": {
        "label": "Williams %R", "category": "Momentum", "tier": 1, "overlay": False,
        "params": {"period": _param(14, 2, 50)},
        "compute": _compute_williams_r, "vote": _vote_williams,
    },
    "roc": {
        "label": "ROC (Rate of Change)", "category": "Momentum", "tier": 1, "overlay": False,
        "params": {"period": _param(12, 2, 60)},
        "compute": _compute_roc, "vote": _vote_zero_line,
    },
    # ---------------- Volatilitas ----------------
    "bollinger": {
        "label": "Bollinger Bands", "category": "Volatilitas", "tier": 1, "overlay": True,
        "params": {"period": _param(20, 5, 60), "num_std": _param(2.0, 1.0, 4.0, "float")},
        "compute": _compute_bollinger, "vote": _vote_vs_middle,
    },
    "keltner": {
        "label": "Keltner Channels", "category": "Volatilitas", "tier": 1, "overlay": True,
        "params": {"ema_window": _param(20, 5, 60), "atr_window": _param(10, 2, 50), "mult": _param(2.0, 1.0, 4.0, "float")},
        "compute": _compute_keltner, "vote": _vote_vs_middle,
    },
    "donchian": {
        "label": "Donchian Channels (Breakout)", "category": "Volatilitas", "tier": 1, "overlay": True,
        "params": {"period": _param(20, 5, 100)},
        "compute": _compute_donchian, "vote": _vote_donchian_breakout,
    },
    # ---------------- Volume ----------------
    "obv": {
        "label": "OBV (On-Balance Volume)", "category": "Volume", "tier": 1, "overlay": False,
        "params": {},
        "compute": _compute_obv, "vote": _vote_vs_own_sma,
    },
    "mfi": {
        "label": "MFI (Money Flow Index)", "category": "Volume", "tier": 1, "overlay": False,
        "params": {"period": _param(14, 2, 50)},
        "compute": _compute_mfi, "vote": _vote_midline_50,
    },
    "cmf": {
        "label": "CMF (Chaikin Money Flow)", "category": "Volume", "tier": 1, "overlay": False,
        "params": {"period": _param(20, 5, 60)},
        "compute": _compute_cmf, "vote": _vote_zero_line,
    },
    "ad_line": {
        "label": "A/D Line", "category": "Volume", "tier": 1, "overlay": False,
        "params": {},
        "compute": _compute_ad_line, "vote": _vote_vs_own_sma,
    },
}

CATEGORIES = ["Trend", "Momentum", "Volatilitas", "Volume"]
MAX_INDICATORS_SELECTED = 8  # anti-overfitting soft cap, lihat §3.1 rencana


def default_params_for(key: str) -> dict:
    spec = INDICATOR_SPECS[key]
    return {name: cfg["default"] for name, cfg in spec["params"].items()}


def list_by_category(category: str) -> list[tuple[str, str]]:
    """Return [(key, label), ...] utk kategori tsb, dipakai render multiselect per grup."""
    return [(k, s["label"]) for k, s in INDICATOR_SPECS.items() if s["category"] == category]
