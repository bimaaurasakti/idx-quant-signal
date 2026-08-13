"""
tests/api/conftest.py
======================
Fixture bersama semua test API. Supabase client di-override lewat
app.dependency_overrides (pola resmi FastAPI utk testing) -- TIDAK butuh
SUPABASE_URL/SUPABASE_ANON_KEY asli sama sekali, karena setiap test
memonkeypatch fungsi fetch_* di namespace SERVICE yang memanggilnya
(persis pola _DummyClient + monkeypatch di test_navigation_fase1.py /
test_screener_fase3.py yang sudah ada di project).
"""
from __future__ import annotations
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.core.deps import get_supabase_client


class _DummyClient:
    """Client Supabase palsu -- tidak pernah benar-benar dipakai karena
    semua fungsi fetch_* di-monkeypatch di masing-masing test module."""
    pass


@pytest.fixture
def client():
    app.dependency_overrides[get_supabase_client] = lambda: _DummyClient()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
