"""
api/core/cache.py
==================
Pengganti langsung @st.cache_data(ttl=600) yang sebelumnya tersebar di
data_loaders.py -- dipusatkan di satu tempat supaya TTL-nya mudah diaudit.
Cocok untuk 1 instance proses (in-memory). Kalau nanti deploy multi-replica,
ganti backend-nya ke Redis (lihat catatan §4.5 implementation plan) --
signature cached() di bawah didesain supaya penggantian itu tidak mengubah
kode pemanggil.
"""
from __future__ import annotations
from functools import wraps

from cachetools import TTLCache

from api.core.config import settings

_cache: TTLCache = TTLCache(maxsize=256, ttl=settings.cache_ttl_seconds)


def cached(key: str):
    """Decorator untuk endpoint/service async tanpa argumen dinamis
    (screener, portfolio, meta) -- SATU key tetap per fungsi. Untuk service
    dengan argumen dinamis (mis. detail per-ticker), bentuk key sendiri di
    pemanggil sebelum memanggil helper get/set di bawah."""
    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            if key in _cache:
                return _cache[key]
            result = await fn(*args, **kwargs)
            _cache[key] = result
            return result
        return wrapper
    return decorator


def cache_get(key: str):
    return _cache.get(key)


def cache_set(key: str, value) -> None:
    _cache[key] = value


def clear_cache() -> None:
    _cache.clear()
