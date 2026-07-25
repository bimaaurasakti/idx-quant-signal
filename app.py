"""
IDX Quant Signal Dashboard — PUBLIC EDITION
=============================================
Dashboard publik, READ-ONLY. Semua data (sinyal, backtest, ongoing position)
sudah dihitung sebelumnya oleh worker_fetch_and_update.py (GitHub Actions,
terjadwal tiap akhir sesi bursa IDX) dan disimpan di Supabase. Dashboard ini
TIDAK melakukan fetch yfinance sendiri — semua pengunjung melihat 1 SUMBER
DATA YANG SAMA, diperbarui otomatis setiap hari bursa (~16:30 WIB).

Jalankan dengan:
    streamlit run app.py

Butuh secrets (lihat .streamlit/secrets.toml.example / README.md):
    SUPABASE_URL, SUPABASE_ANON_KEY

PENTING: Ini adalah alat riset kuantitatif, BUKAN nasihat keuangan. Pasar
Indonesia hanya mendukung posisi long/spot — dashboard ini tidak pernah
menghasilkan sinyal short.
"""
from __future__ import annotations
import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from supabase_client import (
    get_client,
    fetch_screener_results,
    fetch_price_history,
    fetch_backtest_trades,
    fetch_ongoing_positions,
    fetch_closed_positions,
    fetch_last_update,
)
from tickers_idx import IDX_TICKERS, get_sector_of

st.set_page_config(page_title="IDX Quant Signal Dashboard", page_icon="📈", layout="wide")

TOOLTIP = {
    "winrate": (
        "Persentase trade yang profit dari seluruh trade historis. Winrate tinggi "
        "TIDAK otomatis berarti profitable — selalu cek Expectancy juga."
    ),
    "expectancy": (
        "Rata-rata hasil per trade (%), memperhitungkan winrate DAN besar rata-rata "
        "profit/loss: (winrate × avg profit) − (lossrate × avg loss). Metrik utama "
        "untuk menilai kualitas sebuah strategi — lebih jujur daripada winrate saja."
    ),
    "profit_factor": (
        "Total profit dibagi total loss dari seluruh trade historis. Di atas 1 berarti "
        "profit agregat lebih besar dari loss agregat. Di bawah 1 berarti strategi ini "
        "historically merugi meski winrate-nya mungkin terlihat oke."
    ),
    "max_dd": (
        "Penurunan terbesar dari puncak ke lembah pada equity curve hasil backtest "
        "(compounding tiap trade). Menggambarkan potensi kerugian maksimum yang harus ditahan."
    ),
    "total_return": (
        "Jumlah (SUM) return_pct dari SELURUH trade historis, TIDAK dikompund. Bukan "
        "return portofolio riil (posisi tiap trade diasumsikan sama besar), tapi indikator "
        "kasar seberapa produktif sinyal ini secara total sepanjang periode backtest."
    ),
}

# ----------------------------------------------------------------------
# Koneksi Supabase
# ----------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def _client():
    return get_client(use_service_role=False)


try:
    client = _client()
except Exception as e:
    st.error(
        "⚠️ **Koneksi ke Supabase belum berhasil.**\n\n"
        f"Detail: `{e}`\n\n"
        "Pastikan `SUPABASE_URL` dan `SUPABASE_ANON_KEY` sudah diset di "
        "`.streamlit/secrets.toml` (lokal) atau di Settings → Secrets "
        "(Streamlit Community Cloud). Lihat **README.md → Setup Supabase**."
    )
    st.stop()


@st.cache_data(ttl=600, show_spinner="Memuat data screener...")
def load_screener() -> pd.DataFrame:
    return fetch_screener_results(client)


@st.cache_data(ttl=600, show_spinner=False)
def load_positions(statuses: tuple[str, ...]) -> pd.DataFrame:
    return fetch_ongoing_positions(client, list(statuses))


@st.cache_data(ttl=600, show_spinner=False)
def load_last_update():
    return fetch_last_update(client)


@st.cache_data(ttl=600, show_spinner="Memuat riwayat harga...")
def load_price_history(ticker: str) -> pd.DataFrame:
    return fetch_price_history(client, ticker)


@st.cache_data(ttl=600, show_spinner=False)
def load_trades(ticker: str) -> pd.DataFrame:
    return fetch_backtest_trades(client, ticker)


@st.cache_data(ttl=600, show_spinner="Memuat riwayat portfolio...")
def load_closed_positions() -> pd.DataFrame:
    return fetch_closed_positions(client)


def _prepare_portfolio_df(df: pd.DataFrame) -> pd.DataFrame:
    """Siapkan closed_positions mentah dari Supabase: parse tanggal, hitung
    hold_days, lookup sektor, kasih label yang enak dibaca."""
    if df.empty:
        return df
    d = df.copy()
    d["entry_date"] = pd.to_datetime(d["entry_date"])
    d["exit_date"] = pd.to_datetime(d["exit_date"])
    d["signal_date"] = pd.to_datetime(d["signal_date"])
    d["hold_days"] = (d["exit_date"] - d["entry_date"]).dt.days
    d["sektor"] = d["ticker"].apply(get_sector_of)

    label_map = {
        "CLOSED_TP": "Take Profit", "CLOSED_SL": "Stop Loss",
        "CLOSED_SIGNAL": "Sinyal SELL", "CLOSED_TIME": "Batas Waktu",
    }
    d["exit_label"] = d["status"].map(label_map).fillna(d["status"])
    d["is_win"] = d["return_pct"] > 0
    return d.sort_values("exit_date", ascending=False)


def _portfolio_metrics(d: pd.DataFrame) -> dict:
    """Formula IDENTIK dengan backtester.py._compute_metrics — supaya angka
    'Total Return', 'Expectancy', dll. bisa dibandingkan apple-to-apple antara
    tab Portfolio (live) dan tab Detail Saham (backtest)."""
    n = len(d)
    if n == 0:
        return {"n_closed": 0}
    wins = d[d["return_pct"] > 0]
    losses = d[d["return_pct"] <= 0]
    winrate = len(wins) / n * 100
    avg_win = wins["return_pct"].mean() if not wins.empty else 0.0
    avg_loss = abs(losses["return_pct"].mean()) if not losses.empty else 0.0
    lossrate = 100 - winrate
    expectancy = (winrate / 100 * avg_win) - (lossrate / 100 * avg_loss)
    total_profit = wins["return_pct"].sum() if not wins.empty else 0.0
    total_loss = abs(losses["return_pct"].sum()) if not losses.empty else 0.0
    # None (bukan exception / bukan np.inf) kalau belum ada trade rugi sama sekali
    profit_factor = (total_profit / total_loss) if total_loss > 0 else None
    return {
        "n_closed": n,
        "winrate": winrate,
        "expectancy": expectancy,
        "profit_factor": profit_factor,
        "total_return": d["return_pct"].sum(),
        "avg_hold_days": d["hold_days"].mean(),
    }


# ----------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------
st.sidebar.title("⚙️ Pengaturan")

last_update = load_last_update()
if last_update:
    try:
        run_at_wib = pd.to_datetime(last_update["run_at"]).tz_convert("Asia/Jakarta")
    except Exception:
        run_at_wib = pd.to_datetime(last_update["run_at"])
    status_icon = {"OK": "🟢", "SKIPPED": "🟡", "FAILED": "🔴"}.get(last_update.get("status"), "⚪")
    st.sidebar.markdown(
        f"**{status_icon} Data terakhir diperbarui:**  \n"
        f"{run_at_wib.strftime('%d/%m/%Y %H:%M')} WIB  \n"
        f"_{last_update.get('tickers_processed', '?')} saham diproses_"
    )
else:
    st.sidebar.warning("Belum ada riwayat update — worker mungkin belum pernah dijalankan.")

st.sidebar.caption(
    "Data diperbarui **otomatis setiap hari bursa** ±16:30 WIB (setelah sesi 2 tutup) "
    "oleh proses terjadwal — bukan saat Anda membuka halaman ini. Semua pengunjung "
    "melihat data yang sama persis."
)

sector_filter = st.sidebar.multiselect(
    "Filter sektor", options=list(IDX_TICKERS.keys()), default=[],
    help="Kosongkan untuk menampilkan semua sektor.",
)
min_trades_filter = st.sidebar.slider(
    "Minimal jumlah trade historis (filter reliabilitas)", 3, 30, 8,
    help="Saham dengan trade historis terlalu sedikit statistiknya tidak reliabel — sembunyikan dari screener.",
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "⚠️ **Disclaimer**: Alat riset kuantitatif berbasis data historis (yfinance). "
    "Winrate & expectancy dihitung dari backtest masa lalu — **tidak menjamin hasil "
    "masa depan**. Bukan nasihat keuangan. Pasar Indonesia hanya mendukung posisi "
    "**long/spot** — dashboard ini tidak pernah menghasilkan sinyal short."
)

# ----------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------
st.title("📈 IDX Quant Signal Dashboard")
st.caption("Multi-confirmation trend signal system • Data bersama via Supabase • Sumber harga: yfinance")

tab_screener, tab_detail, tab_portfolio, tab_risk, tab_about = st.tabs(
    ["🔍 Screener", "📊 Detail Saham", "💼 Portfolio", "🧮 Risk Calculator", "ℹ️ Tentang Metodologi"]
)

# ----------------------------------------------------------------------
# TAB 1: Screener
# ----------------------------------------------------------------------
with tab_screener:
    screener_df = load_screener()

    if screener_df.empty:
        st.warning(
            "Belum ada data di database. Worker mungkin belum pernah dijalankan. "
            "Trigger manual lewat tab **Actions** di GitHub repo → workflow "
            "\"Update Sinyal IDX Setelah Tutup Bursa\" → **Run workflow**."
        )
    else:
        if sector_filter:
            allowed = set()
            for s in sector_filter:
                allowed.update(IDX_TICKERS[s])
            screener_df = screener_df[screener_df["ticker"].isin(allowed)]

        # ================= PRIORITAS 1: Sinyal BUY Besok =================
        pending = load_positions(("PENDING_ENTRY",))
        if not pending.empty:
            pending = pending.merge(
                screener_df[["ticker", "sektor", "winrate", "expectancy_pct", "profit_factor", "last_close"]],
                on="ticker", how="left",
            )
            pending["planned_entry_date"] = pd.to_datetime(pending["planned_entry_date"])
            main_date = pending["planned_entry_date"].mode()[0]
            st.markdown(f"## 🎯 Sinyal BUY Besok ({main_date.strftime('%d/%m/%Y')})")
            st.caption(
                "Sinyal baru muncul pada penutupan sesi terakhir. Rencana entry di harga "
                "**Open** pada tanggal bursa berikutnya (lihat kolom Tanggal Entry — bisa "
                "berbeda antar saham bila ada gangguan data)."
            )
            disp = pending.copy()
            disp["Tanggal Entry"] = disp["planned_entry_date"].dt.strftime("%d/%m/%Y")
            disp = disp.rename(columns={
                "ticker": "Ticker", "sektor": "Sektor", "last_close": "Harga Terakhir",
                "winrate": "Winrate (%)", "expectancy_pct": "Expectancy (%)",
                "profit_factor": "Profit Factor",
            })
            cols_show = ["Ticker", "Sektor", "Tanggal Entry", "Harga Terakhir",
                         "Winrate (%)", "Expectancy (%)", "Profit Factor"]
            st.dataframe(
                disp[cols_show].sort_values("Expectancy (%)", ascending=False),
                use_container_width=True, hide_index=True,
            )
        else:
            st.markdown("## 🎯 Sinyal BUY Besok")
            st.info("Tidak ada sinyal BUY baru untuk sesi bursa berikutnya saat ini.")

        st.divider()

        # ================= PRIORITAS 2: Ongoing Position =================
        st.markdown("## 📌 Ongoing Position")
        open_pos = load_positions(("OPEN",))
        if not open_pos.empty:
            open_pos = open_pos.merge(
                screener_df[["ticker", "sektor", "last_close", "last_date"]],
                on="ticker", how="left",
            )
            open_pos["entry_date"] = pd.to_datetime(open_pos["entry_date"])
            open_pos["last_date"] = pd.to_datetime(open_pos["last_date"])
            open_pos["Return Saat Ini (%)"] = (
                (open_pos["last_close"] - open_pos["entry_price"]) / open_pos["entry_price"] * 100
            ).round(2)
            open_pos["Hari ke-"] = (open_pos["last_date"] - open_pos["entry_date"]).dt.days
            open_pos["Tanggal Entry"] = open_pos["entry_date"].dt.strftime("%d/%m/%Y")
            disp2 = open_pos.rename(columns={
                "ticker": "Ticker", "sektor": "Sektor", "entry_price": "Harga Entry",
                "tp_price": "Take Profit", "sl_price": "Stop Loss", "last_close": "Harga Terakhir",
            })
            cols_show2 = ["Ticker", "Sektor", "Tanggal Entry", "Harga Entry", "Harga Terakhir",
                          "Take Profit", "Stop Loss", "Return Saat Ini (%)", "Hari ke-"]
            st.dataframe(
                disp2[cols_show2].sort_values("Return Saat Ini (%)", ascending=False),
                use_container_width=True, hide_index=True,
            )
            st.caption(
                "Posisi otomatis hilang dari tabel ini begitu kena Take Profit atau Stop Loss "
                "— riwayatnya tetap tersimpan dan bisa dilihat di tab **Detail Saham → Riwayat Trade**."
            )
        else:
            st.info("Tidak ada posisi yang sedang berjalan (open) saat ini.")

        st.divider()

        # ================= PRIORITAS 3: Ranking lengkap =================
        st.markdown("## 🏆 Ranking Semua Saham (berdasarkan Expectancy)")
        st.caption(
            "Expectancy = (winrate × rata-rata profit) − (lossrate × rata-rata loss) — metrik "
            "yang lebih jujur dibanding winrate mentah, karena winrate tinggi bisa tetap rugi "
            "kalau rata-rata loss jauh lebih besar dari rata-rata profit."
        )
        filtered = screener_df[screener_df["n_trades"].fillna(0) >= min_trades_filter].copy()
        ranked = filtered.sort_values("expectancy_pct", ascending=False)
        display_cols = {
            "ticker": "Ticker", "sektor": "Sektor", "last_close": "Harga Terakhir",
            "signal_today": "Sinyal Terkini", "trend": "Trend", "rsi": "RSI(14)",
            "winrate": "Winrate (%)", "expectancy_pct": "Expectancy (%)",
            "profit_factor": "Profit Factor", "max_drawdown_pct": "Max Drawdown (%)",
            "n_trades": "Jml Trade Historis", "sharpe_rough": "Sharpe (kasar)",
        }
        ranked_disp = ranked.rename(columns=display_cols)[list(display_cols.values())]
        st.dataframe(
            ranked_disp.style.format({
                "Harga Terakhir": "{:,.0f}", "RSI(14)": "{:.1f}",
                "Winrate (%)": "{:.1f}%", "Expectancy (%)": "{:.2f}%",
                "Max Drawdown (%)": "{:.2f}%", "Sharpe (kasar)": "{:.2f}",
            }, na_rep="-"),
            use_container_width=True, height=450,
        )

        csv = ranked_disp.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download hasil sebagai CSV", csv, "idx_screener_result.csv", "text/csv")

# ----------------------------------------------------------------------
# TAB 2: Detail Saham
# ----------------------------------------------------------------------
with tab_detail:
    screener_df = load_screener()
    if screener_df.empty:
        st.warning("Belum ada data. Lihat tab Screener untuk info lebih lanjut.")
    else:
        ticker_choice = st.selectbox("Pilih saham", sorted(screener_df["ticker"].unique()))

        if ticker_choice:
            active_positions = load_positions(("PENDING_ENTRY", "OPEN"))
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

            d = load_price_history(ticker_choice)
            trades_df = load_trades(ticker_choice)
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

# ----------------------------------------------------------------------
# TAB baru: Portfolio (riwayat posisi closed — jejak sinyal LIVE)
# ----------------------------------------------------------------------
with tab_portfolio:
    st.markdown("## 💼 Portfolio — Riwayat Posisi Closed")
    st.caption(
        "Beda dengan tab **Detail Saham → Riwayat Trade** (hasil *backtest* yang "
        "dihitung ULANG dari seluruh histori data setiap worker jalan): data di "
        "tab ini adalah jejak sinyal **LIVE** — posisi yang benar-benar dibuka & "
        "ditutup hari demi hari oleh sistem, tanpa lookahead, dan tidak pernah "
        "direvisi ke belakang. Data ini akan terus **bertambah** seiring waktu — "
        "bukan langsung lengkap sejak hari pertama dashboard berjalan. Posisi yang "
        "masih berjalan (belum closed) ada di tab **Screener → Ongoing Position**."
    )

    raw_closed = load_closed_positions()
    closed_df = _prepare_portfolio_df(raw_closed)

    if closed_df.empty:
        st.info(
            "📭 Belum ada posisi yang closed. Data akan mulai muncul setelah "
            "sebuah posisi live mencapai Take Profit, Stop Loss, sinyal SELL, "
            "atau batas waktu holding (20 hari bursa) — perlu waktu berjalan, "
            "bukan instan."
        )
    else:
        # ---------------- Filter ----------------
        fc1, fc2, fc3, fc4 = st.columns([1.2, 1.2, 1.4, 1.2])
        with fc1:
            reason_opts = closed_df["exit_label"].unique().tolist()
            reason_pick = st.multiselect(
                "Alasan Exit", options=reason_opts, default=reason_opts,
                key="portfolio_reason_filter",
            )
        with fc2:
            sektor_opts = sorted(closed_df["sektor"].unique().tolist())
            sektor_pick = st.multiselect(
                "Sektor", options=sektor_opts, default=[],
                key="portfolio_sektor_filter",
                help="Kosongkan untuk menampilkan semua sektor.",
            )
        with fc3:
            min_d, max_d = closed_df["exit_date"].min(), closed_df["exit_date"].max()
            date_pick = st.date_input(
                "Rentang Tanggal Exit", value=(min_d, max_d),
                min_value=min_d, max_value=max_d, key="portfolio_date_filter",
            )
        with fc4:
            ticker_search = st.text_input(
                "Cari Ticker", placeholder="mis. BBCA", key="portfolio_ticker_search",
            )

        f = closed_df[closed_df["exit_label"].isin(reason_pick)]
        if sektor_pick:
            f = f[f["sektor"].isin(sektor_pick)]
        if isinstance(date_pick, tuple) and len(date_pick) == 2:
            start_d, end_d = pd.Timestamp(date_pick[0]), pd.Timestamp(date_pick[1])
            f = f[(f["exit_date"] >= start_d) & (f["exit_date"] <= end_d)]
        if ticker_search:
            f = f[f["ticker"].str.contains(ticker_search.strip().upper(), regex=False)]

        if f.empty:
            st.warning("Tidak ada posisi closed yang cocok dengan filter di atas.")
        else:
            metrics = _portfolio_metrics(f)

            if metrics["n_closed"] < 20:
                st.warning(
                    f"⚠️ Sample masih kecil (n={metrics['n_closed']} posisi closed). "
                    "Hati-hati menarik kesimpulan statistik dari jumlah trade sekecil "
                    "ini — idealnya tunggu minimal puluhan trade sebelum menilai "
                    "strategi secara serius."
                )

            # ---------------- Metric cards ----------------
            m1, m2, m3, m4, m5, m6 = st.columns(6)
            m1.metric("Total Closed", f"{metrics['n_closed']}")
            m2.metric("Winrate", f"{metrics['winrate']:.1f}%", help=TOOLTIP["winrate"])
            m3.metric("Expectancy", f"{metrics['expectancy']:.2f}%", help=TOOLTIP["expectancy"])
            pf = metrics["profit_factor"]
            pf_disp = f"{pf:.2f}" if pf is not None else "∞"
            m4.metric("Profit Factor", pf_disp, help=TOOLTIP["profit_factor"])
            m5.metric("Total Return (Sum)", f"{metrics['total_return']:.2f}%", help=TOOLTIP["total_return"])
            m6.metric("Avg Hold", f"{metrics['avg_hold_days']:.1f} hari")
            if pf is None:
                st.caption("∞ = belum ada trade rugi sama sekali dalam sample/filter saat ini.")

            st.divider()

            # ---------------- Charts ----------------
            cc1, cc2 = st.columns(2)
            with cc1:
                exit_counts = f["exit_label"].value_counts().reset_index()
                exit_counts.columns = ["Alasan Exit", "Jumlah"]
                fig_exit = px.bar(
                    exit_counts, x="Alasan Exit", y="Jumlah", color="Alasan Exit",
                    text="Jumlah", title="Breakdown Alasan Exit",
                )
                fig_exit.update_layout(showlegend=False)
                st.plotly_chart(fig_exit, use_container_width=True)
            with cc2:
                sektor_stats = (
                    f.groupby("sektor")
                    .agg(Jumlah=("ticker", "count"), AvgReturn=("return_pct", "mean"))
                    .reset_index().sort_values("AvgReturn", ascending=False)
                )
                fig_sektor = px.bar(
                    sektor_stats, x="sektor", y="AvgReturn", color="AvgReturn",
                    color_continuous_scale=["red", "lightgray", "green"],
                    title="Rata-rata Return per Sektor (%)",
                )
                st.plotly_chart(fig_sektor, use_container_width=True)

            timeline = f.sort_values("exit_date").copy()
            timeline["cum_return"] = timeline["return_pct"].cumsum()
            fig_cum = px.line(
                timeline, x="exit_date", y="cum_return", markers=True,
                title="Return Kumulatif dari Waktu ke Waktu (Non-Kompound, Sum)",
            )
            st.plotly_chart(fig_cum, use_container_width=True)
            st.caption(
                "Grafik ini adalah **penjumlahan** (bukan compounding) return_pct "
                "tiap trade closed, asumsi ukuran posisi sama rata. **Bukan** "
                "equity curve portfolio riil — asumsi ukuran posisi sama besar per "
                "trade, sedangkan posisi antar-ticker bisa berjalan paralel tanpa "
                "model alokasi modal riil."
            )

            st.divider()

            # ---------------- Tabel detail ----------------
            st.markdown("### 📋 Detail Posisi Closed")
            disp = f.rename(columns={
                "ticker": "Ticker", "sektor": "Sektor",
                "signal_date": "Tanggal Sinyal", "entry_date": "Tanggal Entry",
                "entry_price": "Harga Entry", "exit_date": "Tanggal Exit",
                "exit_price": "Harga Exit", "exit_label": "Alasan Exit",
                "return_pct": "Return (%)", "hold_days": "Lama Hold (hari)",
            })
            cols_show = ["Ticker", "Sektor", "Tanggal Sinyal", "Tanggal Entry",
                         "Harga Entry", "Tanggal Exit", "Harga Exit", "Alasan Exit",
                         "Return (%)", "Lama Hold (hari)"]
            st.dataframe(
                disp[cols_show].style.format({
                    "Harga Entry": "{:,.0f}", "Harga Exit": "{:,.0f}",
                    "Return (%)": "{:+.2f}%",
                }, na_rep="-"),
                use_container_width=True, hide_index=True, height=400,
            )

            csv = disp[cols_show].to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Download riwayat portfolio sebagai CSV", csv,
                "idx_portfolio_closed_positions.csv", "text/csv",
            )

            # ---------------- Ringkasan untuk Analisis AI ----------------
            with st.expander("📋 Ringkasan untuk Analisis AI (copy teks di bawah)"):
                ai_summary = f"""Ringkasan Portfolio Live — IDX Quant Signal Dashboard
Per tanggal: {pd.Timestamp.now().strftime('%d/%m/%Y')}
Filter aktif: alasan={reason_pick}, sektor={sektor_pick or 'semua'}

METRIK UTAMA
- Total posisi closed: {metrics['n_closed']}
- Winrate: {metrics['winrate']:.1f}%
- Expectancy: {metrics['expectancy']:.2f}% per trade
- Profit Factor: {pf_disp}
- Total Return (sum, non-kompound): {metrics['total_return']:.2f}%
- Rata-rata lama hold: {metrics['avg_hold_days']:.1f} hari bursa

BREAKDOWN ALASAN EXIT
{exit_counts.to_string(index=False)}

BREAKDOWN PERFORMA PER SEKTOR (rata-rata return %)
{sektor_stats.to_string(index=False)}

Catatan: metrik non-kompound, asumsi ukuran posisi sama rata per trade.
Ini jejak sinyal LIVE (bukan hasil backtest simulasi ulang)."""
                st.code(ai_summary, language=None)

# ----------------------------------------------------------------------
# TAB 3: Risk Calculator
# ----------------------------------------------------------------------
with tab_risk:
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
    shares = (shares // 100) * 100  # bulatkan ke lot (100 lembar)
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

# ----------------------------------------------------------------------
# TAB 4: Tentang Metodologi
# ----------------------------------------------------------------------
with tab_about:
    st.subheader("ℹ️ Metodologi & Batasan Jujur")
    st.markdown("""
### Arsitektur — kenapa "1 sumber data yang sama"?

Dashboard ini **tidak lagi** melakukan fetch yfinance sendiri tiap kali dibuka.
Alurnya sekarang:

```
GitHub Actions (cron, ~16:30 WIB tiap hari bursa)
        │
        ▼
worker_fetch_and_update.py  →  fetch yfinance, hitung sinyal + backtest
        │
        ▼
   Supabase (database bersama)
        │
        ▼
app.py (dashboard publik ini)  →  HANYA membaca, tidak pernah menghitung ulang
```

Semua pengunjung — siapa pun, kapan pun — melihat angka yang **persis sama**,
karena semuanya dibaca dari satu database yang sama. Ini juga menghindari
setiap pengunjung memicu rate limit Yahoo Finance sendiri-sendiri.

### Bagaimana sinyal dihasilkan?

Multi-confirmation signal: BUY/SELL hanya muncul kalau minimal 2 dari 3
kondisi searah — **Trend** (harga > SMA50 > SMA200), **Momentum** (MACD
cross + RSI di zona sehat), **Volume** (≥20% di atas rata-rata 20 hari).

### Bagaimana "Ongoing Position" bekerja?

1. Sinyal BUY muncul di penutupan hari ini → status **PENDING_ENTRY**,
   ditampilkan sebagai "Sinyal BUY Besok" dengan tanggal entry (hari bursa
   berikutnya, otomatis skip weekend & libur bursa).
2. Saat hari bursa berikutnya tiba, worker mengeksekusi entry di harga
   **Open** hari itu → status berubah jadi **OPEN**, TP/SL dihitung dari
   ATR saat sinyal muncul (TP = entry + 2×ATR, SL = entry − 1×ATR).
3. Setiap hari bursa, worker cek apakah High/Low hari itu menyentuh TP/SL,
   atau muncul sinyal SELL, atau sudah melewati batas waktu maksimum
   holding (20 hari bursa) → posisi ditutup, **otomatis hilang** dari
   tabel "Ongoing Position", dan riwayatnya tersimpan di tab Detail Saham.

**Dua aturan keras yang selalu dijaga** (di-enforce di kode DAN di database):
- **Long-only**: sinyal SELL tidak pernah membuka posisi baru — cuma
  dipakai untuk menutup posisi long yang sudah ada. Sesuai regulasi pasar
  reguler Indonesia yang tidak mengizinkan short selling untuk investor ritel umum.
- **Maks 1 posisi aktif per emiten**: sebelum membuka posisi baru, sistem
  selalu cek dulu apakah emiten itu sudah punya posisi berjalan.

### Kamus istilah (lihat juga ikon ⓘ di tiap metrik pada tab Detail Saham)

- **Winrate**: % trade yang profit dari seluruh trade historis.
- **Expectancy**: (winrate × avg profit) − (lossrate × avg loss) — metrik
  utama, lebih jujur dari winrate mentah.
- **Profit Factor**: total profit ÷ total loss. >1 = profitable secara agregat.
- **Max Drawdown**: penurunan terbesar puncak-ke-lembah pada equity curve backtest.
- **Total Return (Sum)**: SUM(return_pct) seluruh trade historis — **tidak
  dikompund**, cuma indikator kasar produktivitas total, bukan return portofolio riil.

### Kenapa ini BUKAN "kelas Renaissance Technologies"

- **Data**: yfinance = data harian/delayed dari Yahoo Finance. RenTech pakai
  data tick-by-tick, order book, dan data alternatif eksklusif puluhan tahun.
- **Eksekusi**: dashboard ini tidak terhubung ke broker — sinyal harus
  dieksekusi manual, dengan slippage & delay yang tidak terhindarkan.
- **Riset**: strategi di sini trend-following klasik yang dikenal luas
  (crowded strategy), bukan alpha proprietary yang belum diketahui pasar.
- **Skala**: cocok untuk trading personal skala kecil-menengah di saham
  likuid, bukan mengelola miliaran dolar dengan risk-adjusted return luar biasa.

### Keterbatasan data

- Beberapa saham IDX punya data kosong/tidak lengkap di Yahoo Finance.
- Backtest tidak memperhitungkan biaya transaksi, pajak, atau slippage nyata.
- Kalender libur bursa di-hardcode per tahun (lihat `idx_calendar.py`) —
  perlu di-update manual tiap tahun setelah BEI merilis kalender resminya.
- Ini alat bantu keputusan, **bukan pengganti riset fundamental dan
  manajemen risiko yang disiplin**.
    """)
