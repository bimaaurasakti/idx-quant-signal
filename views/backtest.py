"""
views/backtest.py
==================
Halaman Backtest Lab -- eksplorasi kombinasi indikator custom (lihat
IMPLEMENTATION_PLAN_UI_BACKTEST_LAB.md §3.6 utk spesifikasi alur UI).

READ-ONLY & EPHEMERAL: halaman ini TIDAK PERNAH menulis ke Supabase dan
TIDAK terkait ongoing_positions/position_manager.py sama sekali (§1.6/§3
rencana implementasi). Data OHLCV dibaca dari price_history (Supabase,
sudah bersumber yfinance lewat worker) -- BUKAN memanggil yfinance
langsung (§1.1).
"""
from __future__ import annotations
import pandas as pd
import streamlit as st

import data_loaders
from backtester import backtest_signals
from custom_backtest import generate_custom_signals, validate_min_bars, compute_equity_curve
from indicator_registry import INDICATOR_SPECS, CATEGORIES, MAX_INDICATORS_SELECTED, list_by_category

MIN_BARS_REQUIRED = 60  # konsisten dgn worker_fetch_and_update.py

_PERIOD_TO_DAYS = {"1 Tahun": 365, "2 Tahun": 365 * 2, "3 Tahun": 365 * 3, "5 Tahun (maks)": 365 * 5}


def _drop_warmup_nan(d: pd.DataFrame, selected: list[str]) -> pd.DataFrame:
    """Buang bar awal yg masih NaN krn warm-up rolling/ewm indikator terpilih
    (mis. SMA200 butuh 200 bar pertama sebelum ada nilai). Deteksi LANGSUNG
    dari kolom hasil compute (first_valid_index) -- lebih robust drpd
    menebak dari nama parameter, karena tidak semua indikator pakai nama
    param 'period' (mis. EMA Crossover pakai fast/slow, Ichimoku pakai
    tenkan/kijun/senkou_b)."""
    check_cols = [c for c in d.columns if any(c.startswith(f"{k}_") for k in selected)] + ["ATR14"]
    first_valid_locs = []
    for c in check_cols:
        if c not in d.columns:
            continue
        idx = d[c].first_valid_index()
        if idx is not None:
            first_valid_locs.append(d.index.get_loc(idx))
    warm_up_end = max(first_valid_locs, default=0)
    # CATATAN: Ichimoku Chikou (lagging span, digeser MUNDUR) secara desain
    # akan tetap NaN di bar-bar TERBARU (bukan warm-up di awal) -- itu wajar
    # (garis referensi lagging, Plotly merender sbg celah/gap di garis),
    # fungsi ini SENGAJA tidak mencoba menghapusnya krn itu akan membuang
    # data terbaru yg justru paling relevan.
    return d.iloc[warm_up_end:] if warm_up_end < len(d) else d


def render(ctx) -> None:
    client = ctx.client
    st.markdown("## 🧪 Backtest Lab")
    st.caption(
        "Coba kombinasi indikator sendiri & lihat bagaimana strategi itu tampil di data "
        "historis — lengkap dengan replay animasi harga, indikator, dan posisi entry/exit. "
        "Data OHLCV bersumber dari `price_history` (Supabase, sudah di-fetch dari yfinance "
        "oleh worker) — halaman ini tidak menulis apa pun ke database bersama."
    )

    screener_df = data_loaders.load_screener(client)
    if screener_df.empty:
        st.warning("Belum ada data ticker. Lihat halaman Screener untuk info lebih lanjut.")
        return

    # ---------------- 1. Ticker & periode (reaktif, di luar form) ----------------
    c_ticker, c_period = st.columns([2, 1])
    with c_ticker:
        ticker = st.selectbox("Pilih saham", sorted(screener_df["ticker"].unique()), key="bt_ticker")
    with c_period:
        period_label = st.selectbox("Periode", list(_PERIOD_TO_DAYS.keys()), index=3, key="bt_period")

    # ---------------- 2. Pilih indikator (reaktif -- param muncul dinamis) -------
    st.markdown("#### 1️⃣ Pilih Indikator")
    selected: list[str] = []
    for cat in CATEGORIES:
        with st.expander(f"📂 {cat}", expanded=(cat == "Trend")):
            options = list_by_category(cat)
            picked = st.multiselect(
                f"Indikator {cat}",
                options=[key for key, _ in options],
                format_func=lambda k: INDICATOR_SPECS[k]["label"],
                key=f"bt_pick_{cat}",
                label_visibility="collapsed",
            )
            selected.extend(picked)

    if len(selected) > MAX_INDICATORS_SELECTED:
        st.warning(
            f"⚠️ Anda memilih {len(selected)} indikator — dibatasi maks. {MAX_INDICATORS_SELECTED} "
            "(makin banyak indikator dikombinasikan bukan berarti makin baik, risiko overfitting "
            f"meningkat). Hanya {MAX_INDICATORS_SELECTED} pertama yang dipakai."
        )
        selected = selected[:MAX_INDICATORS_SELECTED]

    indicator_params: dict[str, dict] = {}
    if selected:
        st.caption(f"**{len(selected)} indikator dipilih** — atur parameter tiap indikator (opsional):")
        param_cols = st.columns(min(len(selected), 3))
        for i, key in enumerate(selected):
            spec = INDICATOR_SPECS[key]
            with param_cols[i % len(param_cols)]:
                st.markdown(f"**{spec['label']}**")
                p = {}
                for pname, pcfg in spec["params"].items():
                    widget_key = f"bt_param_{key}_{pname}"
                    if pcfg["type"] == "float":
                        p[pname] = st.number_input(
                            pname, value=float(pcfg["default"]),
                            min_value=float(pcfg["min"]) if pcfg["min"] is not None else None,
                            max_value=float(pcfg["max"]) if pcfg["max"] is not None else None,
                            key=widget_key,
                        )
                    else:
                        p[pname] = st.number_input(
                            pname, value=int(pcfg["default"]),
                            min_value=int(pcfg["min"]) if pcfg["min"] is not None else None,
                            max_value=int(pcfg["max"]) if pcfg["max"] is not None else None,
                            step=1, key=widget_key,
                        )
                indicator_params[key] = p
    else:
        st.info("Pilih minimal 1 indikator di atas untuk melanjutkan.")

    # ---------------- 3. Konfirmasi & risk management (di dalam form) ------------
    st.markdown("#### 2️⃣ Aturan Sinyal & Manajemen Risiko")
    with st.form("bt_run_form"):
        f1, f2 = st.columns(2)
        with f1:
            n_selected = len(selected)
            if n_selected >= 2:
                confirmation_threshold = st.slider(
                    "Minimal Konfirmasi (jumlah indikator yang harus sepakat)",
                    1, n_selected, value=max(1, (n_selected + 1) // 2),
                    help="Sinyal BUY/SELL hanya muncul kalau minimal sekian indikator terpilih "
                         "sepakat searah di bar yang sama.",
                )
            else:
                # Streamlit melarang slider dgn min_value == max_value -- kalau
                # cuma 0/1 indikator terpilih, tidak ada rentang berarti utk
                # digeser (butuh minimal 2 indikator baru "threshold" masuk akal).
                confirmation_threshold = 1
                st.caption(
                    "Minimal Konfirmasi: **1** — pilih minimal 2 indikator di atas untuk "
                    "mengatur seberapa banyak yang harus sepakat."
                    if n_selected == 1 else
                    "Pilih minimal 1 indikator di atas dulu untuk mengatur Minimal Konfirmasi."
                )
        with f2:
            st.caption(" ")
            st.caption(f"Dari {len(selected)} indikator terpilih.")

        r1, r2, r3 = st.columns(3)
        with r1:
            tp_mult = st.slider("Take Profit (× ATR)", 1.0, 5.0, 2.0, step=0.5)
        with r2:
            sl_mult = st.slider("Stop Loss (× ATR)", 0.5, 3.0, 1.0, step=0.5)
        with r3:
            max_hold = st.slider("Maks Hari Holding", 5, 60, 20, step=5)

        submitted = st.form_submit_button(
            "🚀 Jalankan Backtest", type="primary", use_container_width=True, disabled=not selected,
        )

    if submitted and selected:
        _run_backtest(
            client, ticker, period_label, selected, indicator_params,
            confirmation_threshold, tp_mult, sl_mult, max_hold,
        )
    elif st.session_state.get("bt_result") and st.session_state.get("bt_result_ticker") == ticker:
        # Tampilkan hasil run sebelumnya kalau user cuma pindah2 kontrol animasi
        # (bukan submit ulang) -- state disimpan supaya tidak hilang.
        _render_result(st.session_state["bt_result"])


def _run_backtest(client, ticker, period_label, selected, indicator_params,
                   confirmation_threshold, tp_mult, sl_mult, max_hold) -> None:
    raw = data_loaders.load_price_history(client, ticker)
    if raw.empty:
        st.error("Data harga tidak tersedia untuk ticker ini.")
        return

    cutoff = raw.index.max() - pd.Timedelta(days=_PERIOD_TO_DAYS[period_label])
    df = raw[raw.index >= cutoff][["Open", "High", "Low", "Close", "Volume"]].copy()

    ok, msg = validate_min_bars(df, MIN_BARS_REQUIRED)
    if not ok:
        st.error(f"⚠️ {msg}")
        return

    with st.spinner("Menghitung indikator & menjalankan backtest..."):
        d = generate_custom_signals(df, selected, indicator_params, confirmation_threshold)
        result = backtest_signals(d, r_multiple_tp=tp_mult, sl_atr_mult=sl_mult, max_hold_days=max_hold)
        d_clean = _drop_warmup_nan(d, selected)

    payload = {
        "ticker": ticker, "d_clean": d_clean, "result": result, "selected": selected,
    }
    st.session_state["bt_result"] = payload
    st.session_state["bt_result_ticker"] = ticker
    _render_result(payload)


def _render_result(payload: dict) -> None:
    result = payload["result"]
    d_clean = payload["d_clean"]
    selected = payload["selected"]
    trades = result["trades"]

    st.divider()
    st.markdown(f"### 📊 Hasil Backtest — {payload['ticker']}")

    if result["n_trades"] == 0:
        st.info(
            "Tidak ada trade yang terbentuk dengan kombinasi indikator & threshold ini pada "
            "periode yang dipilih. Coba turunkan Minimal Konfirmasi, tambah indikator, atau "
            "perpanjang periode."
        )
        return

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Jml Trade", result["n_trades"])
    m2.metric("Winrate", f"{result['winrate']:.1f}%")
    m3.metric("Expectancy", f"{result['expectancy_pct']:.2f}%")
    pf = result["profit_factor"]
    m4.metric("Profit Factor", f"{pf:.2f}" if pf is not None else "∞")
    m5.metric("Max Drawdown", f"{result['max_drawdown_pct']:.2f}%")
    m6.metric("Sharpe (kasar)", f"{result['sharpe_rough']:.2f}")

    st.warning(
        "⚠️ **Backtest ini bersifat in-sample** (diuji pada data historis yang sama dipakai "
        "utk memilih indikator) — bukan validasi out-of-sample. Performa masa lalu tidak "
        "menjamin hasil masa depan. Makin banyak indikator dikombinasikan, makin besar risiko "
        "overfitting/curve-fitting. **Bukan nasihat keuangan.**",
        icon="⚠️",
    )

    tab_chart, tab_trades, tab_equity = st.tabs(["📈 Chart", "📋 Riwayat Trade", "💰 Equity Curve"])

    with tab_chart:
        from chart_builder import build_chart_figure
        fig_static = build_chart_figure(d_clean, selected, trades)
        st.plotly_chart(fig_static, use_container_width=True)

        from chart_animation import estimate_frame_count
        est_frames = estimate_frame_count(len(d_clean))
        if est_frames > 0:
            if st.button("▶️ Putar Animasi Replay", key="bt_play_animation"):
                with st.spinner(f"Membangun {est_frames} frame animasi..."):
                    from chart_animation import build_animated_backtest_chart
                    fig_anim = build_animated_backtest_chart(d_clean, selected, trades)
                st.plotly_chart(fig_anim, use_container_width=True)
                st.caption(
                    "Klik ▶️ Play pada chart di atas untuk memutar replay, atau geser slider "
                    "untuk melompat ke tanggal tertentu secara manual."
                )

    with tab_trades:
        trades_df = pd.DataFrame(trades)
        label_map = {"TP": "Take Profit", "SL": "Stop Loss", "SELL_SIGNAL": "Sinyal SELL", "TIME_EXIT": "Batas Waktu"}
        trades_df["Alasan Exit"] = trades_df["reason"].map(label_map).fillna(trades_df["reason"])
        disp = trades_df.rename(columns={
            "entry_date": "Tanggal Entry", "exit_date": "Tanggal Exit",
            "entry_price": "Harga Entry", "exit_price": "Harga Exit",
            "return_pct": "Return (%)", "hold_days": "Lama Hold (hari)",
        })
        cols = ["Tanggal Entry", "Tanggal Exit", "Harga Entry", "Harga Exit",
                "Alasan Exit", "Return (%)", "Lama Hold (hari)"]
        st.dataframe(disp[cols], use_container_width=True, hide_index=True)
        csv = disp[cols].to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download riwayat trade sebagai CSV", csv,
                            f"backtest_{payload['ticker']}.csv", "text/csv")

    with tab_equity:
        equity = compute_equity_curve(trades)
        if not equity.empty:
            import plotly.express as px
            fig_eq = px.line(
                x=list(range(1, len(equity) + 1)), y=(equity - 1) * 100,
                labels={"x": "Trade ke-", "y": "Return Kumulatif (%, compounding)"},
                title="Equity Curve (Compounding per Trade)",
            )
            st.plotly_chart(fig_eq, use_container_width=True)
            st.caption(
                "Beda dengan 'Total Return (Sum)' di halaman lain (non-kompound): equity curve "
                "ini MENGKOMPOUND tiap trade berurutan, asumsi seluruh modal dipakai ulang tiap trade."
            )
