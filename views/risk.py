"""
views/risk.py
=============
Isi tab "Risk Calculator" -- FASE 7 REDESIGN (lihat
IMPLEMENTATION_PLAN_UI_REDESIGN_STOCKBIT.md §9.6). Tidak butuh client
Supabase -- murni kalkulator lokal, logika perhitungan 100% tidak berubah.

Perubahan HANYA presentasi: 6x st.metric -> components.render_metric_card
dgn tone warna (R:R ratio hijau kalau >= 1:1.5, TP hijau/SL merah -- pola
sama seperti kartu Ongoing Position di Screener, lihat components.
render_position_card), format Rupiah gaya Indonesia (theme.format_idr).
"""
from __future__ import annotations
import streamlit as st

import components
from theme import format_idr


def render(ctx) -> None:
    st.subheader("🧮 Kalkulator Position Sizing & Risk Management")
    st.caption(
        "Sinyal bagus tidak ada gunanya tanpa position sizing yang benar. "
        "Hedge fund sungguhan selalu menentukan ukuran posisi berdasarkan risiko, bukan 'feeling'."
    )

    c1, c2 = st.columns(2)
    with c1:
        capital = st.number_input("Modal total (Rp)", min_value=1_000_000, value=50_000_000, step=1_000_000)
        risk_pct = st.slider("Risiko per trade (% dari modal)", 0.5, 5.0, 1.0, step=0.5)
        entry_price = st.number_input("Harga entry (Rp)", min_value=1.0, value=5000.0, step=50.0)
    with c2:
        atr_value = st.number_input("ATR(14) saham ini (Rp)", min_value=1.0, value=100.0, step=10.0)
        sl_mult = st.slider("Stop loss = X × ATR", 0.5, 3.0, 1.0, step=0.5)
        tp_mult = st.slider("Take profit = X × ATR", 1.0, 5.0, 2.0, step=0.5)

    risk_rupiah = capital * (risk_pct / 100)
    sl_price = entry_price - (sl_mult * atr_value)
    tp_price = entry_price + (tp_mult * atr_value)
    risk_per_share = entry_price - sl_price
    shares = int(risk_rupiah / risk_per_share) if risk_per_share > 0 else 0
    shares = (shares // 100) * 100
    position_value = shares * entry_price
    reward_risk_ratio = (tp_price - entry_price) / risk_per_share if risk_per_share > 0 else 0

    st.markdown("### Hasil Perhitungan")
    r1, r2, r3 = st.columns(3)
    with r1:
        components.render_metric_card("Jumlah Saham (dibulatkan ke lot)", f"{shares:,}", tone="neutral")
    with r2:
        components.render_metric_card("Nilai Posisi", format_idr(position_value), tone="neutral")
    with r3:
        components.render_metric_card(
            "Risk : Reward Ratio", f"1 : {reward_risk_ratio:.2f}",
            tone="bullish" if reward_risk_ratio >= 1.5 else "bearish",
        )

    r4, r5, r6 = st.columns(3)
    with r4:
        components.render_metric_card("Stop Loss", format_idr(sl_price), tone="bearish")
    with r5:
        components.render_metric_card("Take Profit", format_idr(tp_price), tone="bullish")
    with r6:
        components.render_metric_card("Max Risiko (Rp)", format_idr(risk_rupiah), tone="neutral")

    if position_value > capital:
        st.error(
            "⚠️ Nilai posisi melebihi modal Anda! Stop loss terlalu ketat relatif ke ATR, "
            "atau risk % per trade terlalu besar untuk modal ini. Perbesar jarak SL atau kurangi risk %."
        )
