"""
api/core/config.py
===================
Setting khusus lapisan API. SENGAJA tidak menaruh SUPABASE_URL/SUPABASE_ANON_KEY
di sini -- supabase_client.py (TIDAK DIUBAH) sudah punya mekanisme pencarian
kredensial sendiri (env var -> st.secrets -> secrets.toml, lihat _get_secret()
di file itu) dan tetap dipakai apa adanya lewat get_client(). File ini HANYA
untuk konfigurasi yang murni milik lapisan API baru.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    allowed_origins: str = "http://localhost:3000"
    cache_ttl_seconds: int = 600

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()
