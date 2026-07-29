"""
views/detail.py
================
Isi tab "Detail Saham" dari app.py versi lama, dipindah apa adanya.
Menampilkan performa STRATEGI PRODUKSI TETAP (signals.py) per saham --
BUKAN Backtest Lab (lihat perbandingan scope di IMPLEMENTATION_PLAN §1.7).
"""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

import data_loaders
from shared_ui import TOOLTIP


def render(ctx) -> None:
    client = ctx.client
    screener_df = data_loaders.load_screener(client)
    if screener_df.empty:
        st.warning("Belum ada data. Lihat halaman Screener untuk info lebih lanjut.")
        return

    ticker_choice = st.selectbox("Pilih saham", sorted(screener_df["ticker"].unique()))
    if not ticker_choice:
        return

    active_positions = data_loaders.load_positions(client, ("PENDING_ENTRY", "OPEN"))
    my_position = None
    if not active_positions.empty:
        match = active_positions[active_positions["ticker"] == ticker_choice]
        if not match.empty:
            my_position = match.iloc[0]

    if my_position is not None:
        if my_position["status"] == "PENDING_ENTRY":
            entry_fmt = pd.to_datetime(my_position["planned_entry_date"]).strftime("%d/%m/%Y")
            st.info(f"🎯 Sinyal BUY aktif untuk {ticker_choice} — rencana entry **{entry_fmt}**.")
        else:
            entry_fmt = pd.to_datetime(my_position["entry_date"]).strftime("%d/%m/%Y")
            st.success(
                f"📌 Posisi **OPEN** sejak {entry_fmt} di harga Rp {my_position['entry_price']:,.0f} "
                f"| TP: Rp {my_position['tp_price']:,.0f} | SL: Rp {my_position['sl_price']:,.0f}"
            )

    d = data_loaders.load_price_history(client, ticker_choice)
    trades_df = data_loaders.load_trades(client, ticker_choice)
    row = screener_df[screener_df["ticker"] == ticker_choice].iloc[0]
    total_return = trades_df["return_pct"].sum() if not trades_df.empty else None

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Winrate Historis",
              f"{row['winrate']:.1f}%" if pd.notna(row["winrate"]) else "N/A",
              help=TOOLTIP["winrate"])
    c2.metric("Expectancy",
              f"{row['expectancy_pct']:.2f}%" if pd.notna(row["expectancy_pct"]) else "N/A",
              help=TOOLTIP["expectancy"])
    c3.metric("Profit Factor",
              f"{row['profit_factor']:.2f}" if pd.notna(row["profit_factor"]) else "N/A",
              help=TOOLTIP["profit_factor"])
    c4.metric("Max Drawdown",
              f"{row['max_drawdown_pct']:.2f}%" if pd.notna(row["max_drawdown_pct"]) else "N/A",
              help=TOOLTIP["max_dd"])
    c5.metric("Total Return (Sum)",
              f"{total_return:.2f}%" if total_return is not None else "N/A",
              help=TOOLTIP["total_return"])

    if d.empty:
        st.warning("Data harga belum tersedia untuk saham ini.")
    else:
        fig = make_subplots(
            rows=3, cols=1, shared_xaxes=True,
            row_heights=[0.55, 0.20, 0.25], vertical_spacing=0.03,
            subplot_titles=("Harga & Sinyal", "RSI(14)", "MACD"),
        )
        fig.add_trace(go.Candlestick(
            x=d.index, open=d["Open"], high=d["High"], low=d["Low"], close=d["Close"],
            name="Harga",
        ), row=1, col=1)
        fig.add_trace(go.Scatter(x=d.index, y=d["SMA50"], line=dict(width=1), name="SMA50"), row=1, col=1)
        fig.add_trace(go.Scatter(x=d.index, y=d["SMA200"], line=dict(width=1), name="SMA200"), row=1, col=1)

        buys = d[d["Signal"] == 1]
        sells = d[d["Signal"] == -1]
        fig.add_trace(go.Scatter(
            x=buys.index, y=buys["Low"] * 0.98, mode="markers",
            marker=dict(symbol="triangle-up", size=10, color="green"), name="BUY",
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=sells.index, y=sells["High"] * 1.02, mode="markers",
            marker=dict(symbol="triangle-down", size=10, color="red"), name="SELL",
        ), row=1, col=1)

        fig.add_trace(go.Scatter(x=d.index, y=d["RSI14"], name="RSI14", line=dict(color="purple")), row=2, col=1)
        fig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="green", row=2, col=1)

        fig.add_trace(go.Bar(x=d.index, y=d["MACD_Hist"], name="MACD Hist"), row=3, col=1)
        fig.add_trace(go.Scatter(x=d.index, y=d["MACD"], name="MACD", line=dict(color="blue")), row=3, col=1)
        fig.add_trace(go.Scatter(x=d.index, y=d["MACD_Signal"], name="Signal", line=dict(color="orange")), row=3, col=1)

        fig.update_layout(height=800, xaxis_rangeslider_visible=False, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### 📋 Riwayat Trade dari Backtest")
    if not trades_df.empty:
        trades_disp = trades_df.rename(columns={
            "entry_date": "Tanggal Entry", "exit_date": "Tanggal Exit",
            "entry_price": "Harga Entry", "exit_price": "Harga Exit",
            "return_pct": "Return (%)", "reason": "Alasan Exit", "hold_days": "Lama Hold (hari)",
        })
        cols = ["Tanggal Entry", "Tanggal Exit", "Harga Entry", "Harga Exit",
                "Return (%)", "Alasan Exit", "Lama Hold (hari)"]
        st.dataframe(trades_disp[[c for c in cols if c in trades_disp.columns]],
                     use_container_width=True, hide_index=True)
        st.caption(f"Total {len(trades_df)} trade historis • SUM(Return %) = **{total_return:.2f}%** (non-kompound).")
    else:
        st.info("Belum ada trade historis yang tercatat untuk saham ini.")
