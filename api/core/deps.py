"""
api/core/deps.py
=================
FastAPI dependency untuk Supabase client. @lru_cache membuat client hanya
SEKALI per siklus hidup proses -- padanan langsung @st.cache_resource yang
dipakai _get_client() di app.py versi Streamlit lama. Selalu anon key
(use_service_role=False): API publik ini HANYA baca, persis filosofi
schema.sql (RLS public read-only). Service role key TETAP eksklusif milik
worker_fetch_and_update.py via GitHub Actions secret -- tidak pernah
menyentuh proses API ini.
"""
from __future__ import annotations
from functools import lru_cache

from supabase_client import get_client


@lru_cache(maxsize=1)
def get_supabase_client():
    return get_client(use_service_role=False)
