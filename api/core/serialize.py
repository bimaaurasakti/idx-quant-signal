"""
api/core/serialize.py
======================
Helper konversi nilai dari DataFrame/Series pandas (yang bisa berisi
numpy.float64/int64/NaN/NaT/None) ke tipe Python native yang aman
dikembalikan lewat Pydantic -> JSON. Dipusatkan di sini supaya SETIAP
service (screener/detail/portfolio/positions/backtest) memakai logika
konversi yang SAMA persis -- menghindari duplikasi 5x fungsi _num() kecil
yang gampang drift satu sama lain.
"""
from __future__ import annotations

import pandas as pd


def _is_na(v) -> bool:
    try:
        result = pd.isna(v)
        return bool(result) if not hasattr(result, "__len__") else False
    except (TypeError, ValueError):
        return False


def to_float(v) -> float | None:
    if v is None or _is_na(v):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def to_int(v) -> int | None:
    if v is None or _is_na(v):
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def to_str_or_none(v) -> str | None:
    if v is None or _is_na(v):
        return None
    return str(v)


def to_bool(v, default: bool = False) -> bool:
    if v is None or _is_na(v):
        return default
    return bool(v)
