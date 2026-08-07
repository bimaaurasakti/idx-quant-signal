"""
views/detail.py
================
Isi tab "Detail Saham" -- FASE 4 REDESIGN (lihat
IMPLEMENTATION_PLAN_UI_REDESIGN_STOCKBIT.md §9.3). Menampilkan performa
STRATEGI PRODUKSI TETAP (signals.py) per saham -- BUKAN Backtest Lab
(lihat perbandingan scope di IMPLEMENTATION_PLAN §1.7).

Perubahan dari versi sebelumnya HANYA presentasi:
  - Header harga baru ("stock profile" style) dgn perubahan harian
    (change/change_pct) yg DITURUNKAN dari price_history yg SUDAH dimuat --
    pola yg sama persis dgn portfolio.py._prepare_portfolio_df() yg sudah
    ada (menurunkan kolom presentasi dari data mentah), BUKAN fetch baru.
  - Kartu status posisi aktif (bukan st.info/st.success bawaan).
  - 5 metric card (components.render_metric_card) menggantikan st.metric,
    dgn tone warna dinamis sesuai kualitas angkanya.
  - Chart theming SUDAH diterapkan di Fase 2 -- tidak berubah lagi di sini.
"""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

import data_loaders
import components
from shared_ui import TOOLTIP, style_exit_reason_row
from theme import apply_chart_theme, CANDLESTICK_COLORS, COLORS, format_idr


def _price_change(d: pd.DataFrame) -> tuple[float | None, float | None, float | None]:
    """Turunkan (last_close, change, change_pct) dari price_history yang
    SUDAH dimuat -- murni presentasi, bukan kalkulasi bisnis baru (lihat
    docstring modul & IMPLEMENTATION_PLAN §9.3)."""
    if d.empty:
        return None, None, None
    last_close = float(d["Close"].iloc[-1])
    if len(d) < 2:
        return last_close, None, None
    prev_close = float(d["Close"].iloc[-2])
    change = last_close - prev_close
    change_pct = (change / prev_close * 100) if prev_close else None
    return last_close, change, change_pct


def render(ctx) -> None:
    client = ctx.client
    screener_df = data_loaders.load_screener(client)
    if screener_df.empty:
        st.warning("Belum ada data. Lihat halaman Screener untuk info lebih lanjut.")
        return

    ticker_choice = st.selectbox("Pilih saham", sorted(screener_df["ticker"].unique()))
    if not ticker_choice:
        return

    d = data_loaders.load_price_history(client, ticker_choice)
    trades_df = data_loaders.load_trades(client, ticker_choice)
    row = screener_df[screener_df["ticker"] == ticker_choice].iloc[0]
    total_return = trades_df["return_pct"].sum() if not trades_df.empty else None

    last_close, change, change_pct = _price_change(d)
    strength = row.get("signal_strength")
    components.render_price_header(
        ticker=ticker_choice, sektor=row.get("sektor") or "–",
        price=last_close if last_close is not None else row.get("last_close"),
        change=change, change_pct=change_pct,
        signal=row.get("signal_today"),
        filled=int(strength) if pd.notna(strength) else 0, total=3,
    )

    active_positions = data_loaders.load_positions(client, ("PENDING_ENTRY", "OPEN"))
    my_position = None
    if not active_positions.empty:
        match = active_positions[active_positions["ticker"] == ticker_choice]
        if not match.empty:
            my_position = match.iloc[0]

    if my_position is not None:
        if my_position["status"] == "PENDING_ENTRY":
            entry_fmt = pd.to_datetime(my_position["planned_entry_date"]).strftime("%d/%m/%Y")
            components.render_status_card(
                f"🎯 Sinyal BUY aktif untuk <b>{ticker_choice}</b> — rencana entry <b>{entry_fmt}</b>.",
                tone="info",
            )
        else:
            entry_fmt = pd.to_datetime(my_position["entry_date"]).strftime("%d/%m/%Y")
            components.render_status_card(
                f"📌 Posisi <b>OPEN</b> sejak {entry_fmt} di harga {format_idr(my_position['entry_price'])} "
                f"&bull; TP: {format_idr(my_position['tp_price'])} &bull; SL: {format_idr(my_position['sl_price'])}",
                tone="bullish",
            )
        st.write("")  # spasi kecil antara status card & metric row

    winrate = row["winrate"] if pd.notna(row["winrate"]) else None
    expectancy = row["expectancy_pct"] if pd.notna(row["expectancy_pct"]) else None
    profit_factor = row["profit_factor"] if pd.notna(row["profit_factor"]) else None
    max_dd = row["max_drawdown_pct"] if pd.notna(row["max_drawdown_pct"]) else None

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        components.render_metric_card(
            "Winrate Historis", f"{winrate:.1f}%" if winrate is not None else "N/A",
            tone="bullish" if (winrate or 0) > 50 else "neutral", help_text=TOOLTIP["winrate"],
        )
    with c2:
        components.render_metric_card(
            "Expectancy", f"{expectancy:.2f}%" if expectancy is not None else "N/A",
            tone="bullish" if (expectancy or 0) > 0 else ("bearish" if expectancy is not None else "neutral"),
            help_text=TOOLTIP["expectancy"],
        )
    with c3:
        components.render_metric_card(
            "Profit Factor", f"{profit_factor:.2f}" if profit_factor is not None else "N/A",
            tone="bullish" if (profit_factor or 0) > 1 else ("bearish" if profit_factor is not None else "neutral"),
            help_text=TOOLTIP["profit_factor"],
        )
    with c4:
        components.render_metric_card(
            "Max Drawdown", f"{max_dd:.2f}%" if max_dd is not None else "N/A",
            tone="bearish" if max_dd is not None else "neutral", help_text=TOOLTIP["max_dd"],
        )
    with c5:
        components.render_metric_card(
            "Total Return (Sum)", f"{total_return:.2f}%" if total_return is not None else "N/A",
            tone="bullish" if (total_return or 0) > 0 else ("bearish" if total_return is not None else "neutral"),
            help_text=TOOLTIP["total_return"],
        )

    st.write("")
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
            name="Harga", **CANDLESTICK_COLORS,
        ), row=1, col=1)
        fig.add_trace(go.Scatter(x=d.index, y=d["SMA50"], line=dict(width=1), name="SMA50"), row=1, col=1)
        fig.add_trace(go.Scatter(x=d.index, y=d["SMA200"], line=dict(width=1), name="SMA200"), row=1, col=1)

        buys = d[d["Signal"] == 1]
        sells = d[d["Signal"] == -1]
        fig.add_trace(go.Scatter(
            x=buys.index, y=buys["Low"] * 0.98, mode="markers",
            marker=dict(symbol="triangle-up", size=10, color=COLORS["bullish"]), name="BUY",
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=sells.index, y=sells["High"] * 1.02, mode="markers",
            marker=dict(symbol="triangle-down", size=10, color=COLORS["bearish"]), name="SELL",
        ), row=1, col=1)

        fig.add_trace(go.Scatter(x=d.index, y=d["RSI14"], name="RSI14", line=dict(color="purple")), row=2, col=1)
        fig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="green", row=2, col=1)

        fig.add_trace(go.Bar(x=d.index, y=d["MACD_Hist"], name="MACD Hist"), row=3, col=1)
        fig.add_trace(go.Scatter(x=d.index, y=d["MACD"], name="MACD", line=dict(color="blue")), row=3, col=1)
        fig.add_trace(go.Scatter(x=d.index, y=d["MACD_Signal"], name="Signal", line=dict(color="orange")), row=3, col=1)

        fig.update_layout(height=800, xaxis_rangeslider_visible=False, hovermode="x unified")
        apply_chart_theme(fig)
        st.plotly_chart(fig, width="stretch")

    st.markdown("#### 📋 Riwayat Trade dari Backtest")
    if not trades_df.empty:
        trades_disp = trades_df.rename(columns={
            "entry_date": "Tanggal Entry", "exit_date": "Tanggal Exit",
            "entry_price": "Harga Entry", "exit_price": "Harga Exit",
            "return_pct": "Return (%)", "reason": "Alasan Exit", "hold_days": "Lama Hold (hari)",
        })
        label_map = {"TP": "Take Profit", "SL": "Stop Loss", "SELL_SIGNAL": "Sinyal SELL", "TIME_EXIT": "Batas Waktu"}
        trades_disp["Alasan Exit"] = trades_disp["Alasan Exit"].map(label_map).fillna(trades_disp["Alasan Exit"])
        cols = ["Tanggal Entry", "Tanggal Exit", "Harga Entry", "Harga Exit",
                "Return (%)", "Alasan Exit", "Lama Hold (hari)"]
        cols_present = [c for c in cols if c in trades_disp.columns]
        st.dataframe(
            trades_disp[cols_present].style.apply(style_exit_reason_row, axis=1),
            width="stretch", hide_index=True,
        )
        st.caption(f"Total {len(trades_df)} trade historis • SUM(Return %) = **{total_return:.2f}%** (non-kompound).")
    else:
        st.info("Belum ada trade historis yang tercatat untuk saham ini.")
