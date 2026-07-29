"""
views/risk.py
=============
Isi tab "Risk Calculator" dari app.py versi lama, dipindah apa adanya.
Tidak butuh client Supabase -- murni kalkulator lokal.
"""
from __future__ import annotations
import streamlit as st


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
    r1.metric("Jumlah Saham (dibulatkan ke lot)", f"{shares:,}")
    r2.metric("Nilai Posisi", f"Rp {position_value:,.0f}")
    r3.metric("Risk : Reward Ratio", f"1 : {reward_risk_ratio:.2f}")

    r4, r5, r6 = st.columns(3)
    r4.metric("Stop Loss", f"Rp {sl_price:,.0f}")
    r5.metric("Take Profit", f"Rp {tp_price:,.0f}")
    r6.metric("Max Risiko (Rp)", f"Rp {risk_rupiah:,.0f}")

    if position_value > capital:
        st.error(
            "⚠️ Nilai posisi melebihi modal Anda! Stop loss terlalu ketat relatif ke ATR, "
            "atau risk % per trade terlalu besar untuk modal ini. Perbesar jarak SL atau kurangi risk %."
        )
