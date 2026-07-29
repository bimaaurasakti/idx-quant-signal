"""
data_loaders.py
================
Semua fungsi loader ber-cache (@st.cache_data) dipusatkan di sini supaya
bisa dipakai lintas view module tanpa duplikasi cache namespace. Sebelumnya
fungsi-fungsi ini didefinisikan langsung di app.py.

TIDAK ada perubahan logika dari versi app.py sebelumnya -- murni pemindahan.
"""
from __future__ import annotations
import pandas as pd
import streamlit as st

from supabase_client import (
    fetch_screener_results,
    fetch_price_history,
    fetch_backtest_trades,
    fetch_ongoing_positions,
    fetch_closed_positions,
    fetch_last_update,
)


@st.cache_data(ttl=600, show_spinner="Memuat data screener...")
def load_screener(_client) -> pd.DataFrame:
    return fetch_screener_results(_client)


@st.cache_data(ttl=600, show_spinner=False)
def load_positions(_client, statuses: tuple[str, ...]) -> pd.DataFrame:
    return fetch_ongoing_positions(_client, list(statuses))


@st.cache_data(ttl=600, show_spinner=False)
def load_last_update(_client):
    return fetch_last_update(_client)


@st.cache_data(ttl=600, show_spinner="Memuat riwayat harga...")
def load_price_history(_client, ticker: str) -> pd.DataFrame:
    return fetch_price_history(_client, ticker)


@st.cache_data(ttl=600, show_spinner=False)
def load_trades(_client, ticker: str) -> pd.DataFrame:
    return fetch_backtest_trades(_client, ticker)


@st.cache_data(ttl=600, show_spinner="Memuat riwayat portfolio...")
def load_closed_positions(_client) -> pd.DataFrame:
    return fetch_closed_positions(_client)
