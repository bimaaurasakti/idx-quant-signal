"""
api/core/rate_limit.py
=======================
Instance Limiter dipisah dari main.py supaya bisa diimpor router
(api/routers/backtest.py) TANPA circular import (main.py mengimpor semua
router, jadi limiter tidak boleh didefinisikan di main.py kalau router juga
butuh mengimpornya sebagai decorator). Hanya endpoint /api/backtest/run
yang memakai ini -- satu-satunya endpoint publik yang menerima input bebas
& cukup mahal secara komputasi utk disalahgunakan (lihat §4.6 rencana).
"""
from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
