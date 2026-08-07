"""
views/backtest.py
==================
Halaman Backtest Lab -- eksplorasi kombinasi indikator custom (lihat
IMPLEMENTATION_PLAN_UI_BACKTEST_LAB.md §3.6 utk spesifikasi alur UI dasar,
dan IMPLEMENTATION_PLAN_UI_REDESIGN_STOCKBIT.md §9.4 utk redesign Fase 5).

READ-ONLY & EPHEMERAL: halaman ini TIDAK PERNAH menulis ke Supabase dan
TIDAK terkait ongoing_positions/position_manager.py sama sekali. Data OHLCV
dibaca dari price_history (Supabase, sudah bersumber yfinance lewat
worker) -- BUKAN memanggil yfinance langsung.

FASE 5: perubahan HANYA presentasi (badge jumlah terpilih di expander
indikator, metric card berwarna, Meteran Konfirmasi utk trade BUY
terbaru). Chart (statis & animasi replay) TIDAK diedit di sini -- sudah
otomatis ke-theme sejak Fase 2 lewat chart_builder.py.
"""
from __future__ import annotations
import pandas as pd
import streamlit as st

import data_loaders
import components
from theme import COLORS
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


def _last_trade_confirmation(d_clean: pd.DataFrame, trades: list[dict], total: int) -> tuple[int, int] | None:
    """Meteran Konfirmasi utk trade BUY PALING BARU. filled = BullishCount
    pada bar SINYAL (1 bar sebelum entry_date -- lihat backtester.py:
    entry_idx = i+1 dari bar sinyal ke-i). SEMUA trade di Backtest Lab
    selalu trade BUY (backtester.py cuma membuka posisi dari signals==1,
    long-only, lihat docstring position_manager.py) jadi arahnya selalu
    bullish -- tidak perlu cek arah. Return None (bukan raise) kalau bar
    sinyal sudah terbuang oleh _drop_warmup_nan di atas atau di luar
    jangkauan d_clean -- pemanggil WAJIB skip elemen ini dgn aman."""
    if not trades:
        return None
    entry_date = pd.Timestamp(trades[-1]["entry_date"])
    if entry_date not in d_clean.index:
        return None
    entry_loc = d_clean.index.get_loc(entry_date)
    signal_loc = entry_loc - 1
    if signal_loc < 0 or "BullishCount" not in d_clean.columns:
        return None
    filled = int(d_clean["BullishCount"].iloc[signal_loc])
    return filled, total


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
        # Badge jumlah terpilih di judul expander -- dibaca dari session_state
        # widget SEBELUM widget itu sendiri dibuat ulang di run ini (nilai
        # dari run sebelumnya tetap ada di session_state), supaya user tidak
        # perlu buka tiap expander cuma utk tahu apa yg sudah dipilih.
        n_prev = len(st.session_state.get(f"bt_pick_{cat}", []))
        label = f"📂 {cat}" + (f" · {n_prev} dipilih" if n_prev else "")
        with st.expander(label, expanded=(cat == "Trend")):
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
            "🚀 Jalankan Backtest", type="primary", width="stretch", disabled=not selected,
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

    pf = result["profit_factor"]
    winrate = result["winrate"]
    expectancy = result["expectancy_pct"]

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    with m1:
        components.render_metric_card("Jml Trade", str(result["n_trades"]), tone="neutral")
    with m2:
        components.render_metric_card(
            "Winrate", f"{winrate:.1f}%", tone="bullish" if winrate > 50 else "neutral",
        )
    with m3:
        components.render_metric_card(
            "Expectancy", f"{expectancy:.2f}%", tone="bullish" if expectancy > 0 else "bearish",
        )
    with m4:
        components.render_metric_card(
            "Profit Factor", f"{pf:.2f}" if pf is not None else "∞",
            tone="bullish" if (pf is None or pf > 1) else "bearish",
        )
    with m5:
        components.render_metric_card(
            "Max Drawdown", f"{result['max_drawdown_pct']:.2f}%", tone="bearish",
        )
    with m6:
        components.render_metric_card("Sharpe (kasar)", f"{result['sharpe_rough']:.2f}", tone="neutral")

    meter_info = _last_trade_confirmation(d_clean, trades, len(selected))
    if meter_info:
        filled, total = meter_info
        st.markdown(
            f'<div style="margin:10px 0 4px;font-size:12.5px;color:{COLORS["text_secondary"]};">'
            f"Konfirmasi trade BUY terakhir: "
            f'{components.confirmation_meter_html(filled, total, "bullish")} '
            f'<span class="iqs-mono">{filled}/{total} indikator sepakat</span></div>',
            unsafe_allow_html=True,
        )

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
        st.plotly_chart(fig_static, width="stretch")

        from chart_animation import estimate_frame_count
        est_frames = estimate_frame_count(len(d_clean))
        if est_frames > 0:
            if st.button("▶️ Putar Animasi Replay", key="bt_play_animation"):
                with st.spinner(f"Membangun {est_frames} frame animasi..."):
                    from chart_animation import build_animated_backtest_chart
                    fig_anim = build_animated_backtest_chart(d_clean, selected, trades)
                st.plotly_chart(fig_anim, width="stretch")
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
        from shared_ui import style_exit_reason_row
        st.dataframe(disp[cols].style.apply(style_exit_reason_row, axis=1), width="stretch", hide_index=True)
        csv = disp[cols].to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download riwayat trade sebagai CSV", csv,
                            f"backtest_{payload['ticker']}.csv", "text/csv")

    with tab_equity:
        equity = compute_equity_curve(trades)
        if not equity.empty:
            import plotly.express as px
            from theme import apply_chart_theme
            fig_eq = px.line(
                x=list(range(1, len(equity) + 1)), y=(equity - 1) * 100,
                labels={"x": "Trade ke-", "y": "Return Kumulatif (%, compounding)"},
                title="Equity Curve (Compounding per Trade)",
            )
            fig_eq.update_traces(line_color=COLORS["brand"])
            apply_chart_theme(fig_eq)
            st.plotly_chart(fig_eq, width="stretch")
            st.caption(
                "Beda dengan 'Total Return (Sum)' di halaman lain (non-kompound): equity curve "
                "ini MENGKOMPOUND tiap trade berurutan, asumsi seluruh modal dipakai ulang tiap trade."
            )
