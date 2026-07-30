# IDX Quant Signal Dashboard — Public Edition

Dashboard sinyal trading kuantitatif **publik** untuk saham Indonesia (IDX),
dengan **1 sumber data yang sama** untuk semua pengunjung. Data diambil dari
[yfinance](https://github.com/ranaroussi/yfinance), diproses otomatis
setiap akhir sesi bursa, dan disimpan terpusat di [Supabase](https://supabase.com).

> ⚠️ **Bukan nasihat keuangan.** Alat riset kuantitatif berbasis data
> historis. Performa masa lalu tidak menjamin hasil masa depan. Pasar
> Indonesia hanya mendukung posisi **long/spot** — dashboard ini tidak
> pernah menghasilkan sinyal short.

---

## 1. Arsitektur

```
┌─────────────────────────┐     tulis      ┌──────────────┐     baca      ┌─────────────────────┐
│   GitHub Actions (cron)  │ ─────────────▶ │   Supabase   │ ─────────────▶│  Streamlit App       │
│  worker_fetch_and_update │  service_role  │  (Postgres)  │   anon key    │  (app.py, publik)    │
│  ~16:30 WIB, Senin-Jumat │     key        │              │  read-only    │  read-only            │
└─────────────────────────┘                └──────────────┘               └─────────────────────┘
         │
         ▼
    yfinance (Yahoo Finance)
```

**Kenapa begini?** Supaya SEMUA pengunjung dashboard melihat angka yang
**persis sama**, dihitung sekali per hari oleh satu proses terpusat —
bukan tiap pengunjung memicu fetch yfinance-nya sendiri (yang akan kena
rate limit dan bisa memberi angka berbeda-beda antar pengunjung).

- **Worker** (`worker_fetch_and_update.py`) — dijalankan otomatis oleh
  GitHub Actions, satu-satunya proses yang boleh MENULIS ke Supabase
  (pakai *service role key*, privat).
- **App** (`app.py`) — dashboard Streamlit publik, HANYA membaca dari
  Supabase (pakai *anon key*, aman untuk publik karena dibatasi
  Row Level Security ke read-only).

---

## 2. Setup Supabase

1. Buat project baru di [supabase.com](https://supabase.com) (gratis).
2. Buka **SQL Editor** → **New query** → copy-paste seluruh isi
   [`schema.sql`](./schema.sql) → **Run**.
   Ini membuat 5 tabel (`screener_results`, `price_history`,
   `backtest_trades`, `ongoing_positions`, `update_log`) beserta Row Level
   Security (publik read-only).
3. Buka **Project Settings → API**, catat 3 nilai ini:
   - **Project URL** → `SUPABASE_URL`
   - **anon public key** → `SUPABASE_ANON_KEY`
   - **service_role key** → `SUPABASE_SERVICE_ROLE_KEY` (⚠️ **RAHASIA**,
     bypass semua security rule — jangan pernah expose ke publik)

---

## 3. Setup GitHub Actions (worker terjadwal)

1. Push seluruh folder ini ke repository GitHub baru.
2. Di repo, buka **Settings → Secrets and variables → Actions → New repository secret**,
   tambahkan 2 secret:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
3. Workflow di `.github/workflows/update_after_market_close.yml` akan
   otomatis berjalan **Senin–Jumat, ~16:30 WIB** (09:30 UTC — buffer ~15
   menit setelah sesi 2 IDX tutup pukul 15:49 WIB + pre/post-closing).
4. **Jalankan manual sekali** untuk mengisi data pertama kali (tidak perlu
   menunggu jadwal cron): tab **Actions** di GitHub → pilih workflow
   "Update Sinyal IDX Setelah Tutup Bursa" → **Run workflow**.

> Catatan: cron GitHub Actions bersifat "best effort" — bisa molor beberapa
> menit saat traffic tinggi. Ini normal dan sudah diantisipasi lewat buffer waktu.

---

## 4. Deploy dashboard (Streamlit Community Cloud)

1. Buka [share.streamlit.io](https://share.streamlit.io) → **New app** →
   pilih repo ini, file utama `app.py`.
2. Di **Advanced settings → Secrets**, isi (format TOML):
   ```toml
   SUPABASE_URL = "https://xxxxxxxxxxxx.supabase.co"
   SUPABASE_ANON_KEY = "eyJhbGci....."
   ```
   (Isi persis seperti `.streamlit/secrets.toml.example` — **jangan** pakai
   service role key di sini.)
3. Deploy. Dashboard akan otomatis baca data terbaru dari Supabase setiap
   ada pengunjung (di-cache 10 menit per query untuk efisiensi).

### Menjalankan lokal (opsional, untuk development)

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# edit .streamlit/secrets.toml, isi SUPABASE_URL & SUPABASE_ANON_KEY
streamlit run app.py
```

### Menjalankan worker secara manual (testing lokal)

```bash
export SUPABASE_URL="https://xxxxxxxxxxxx.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="eyJhbGci....."   # service role, bukan anon!
python worker_fetch_and_update.py
```

---

## 5. Struktur Project

```
idx-quant-dashboard/
├── app.py                          # Orkestrator: top bar, dual sidebar, routing ke views/
├── ui_layout.py                    # Layout: CSS, session_state, sidebar kiri (nav) & kanan (settings)
├── data_loaders.py                 # Loader @st.cache_data terpusat (dipakai semua views/*.py)
├── shared_ui.py                    # Konstanta/helper lintas view (TOOLTIP, warna exit-reason)
├── views/                          # Satu modul per halaman (BUKAN folder "pages/", lihat catatan di ui_layout.py)
│   ├── screener.py                 # Screener + Sinyal BUY Besok + Ongoing Position
│   ├── backtest.py                 # 🧪 Backtest Lab -- kombinasi indikator custom + animasi
│   ├── detail.py                   # Detail Saham (strategi produksi tetap, signals.py)
│   ├── portfolio.py                # Riwayat posisi closed (jejak sinyal live)
│   ├── risk.py                     # Risk Calculator
│   └── about.py                    # Tentang Metodologi
├── worker_fetch_and_update.py      # Worker: fetch yfinance -> hitung -> tulis ke Supabase
├── position_manager.py             # State machine ongoing position (long-only, 1/ticker)
├── supabase_client.py              # Semua query/upsert ke Supabase (satu-satunya titik akses)
├── idx_calendar.py                 # Kalender hari bursa IDX (skip libur, hitung "besok")
├── data_fetcher.py                 # Wrapper yfinance dengan retry (dipakai worker saja)
├── indicators.py                   # ~24 indikator (SMA/EMA/WMA, MACD, ADX, PSAR, Supertrend,
│                                    #   Ichimoku, RSI, Stochastic, CCI, Bollinger, OBV, MFI, dll)
├── indicator_registry.py           # Metadata indikator utk Backtest Lab (label/param/vote rule)
├── custom_backtest.py              # Algoritma Vote & Trigger (signal dari kombinasi indikator user)
├── chart_builder.py                # Chart builder (dipakai statis & tiap frame animasi)
├── chart_animation.py              # Animasi replay Plotly (sliding window + adaptive frame-step)
├── signals.py                      # Logika sinyal PRODUKSI TETAP (trend+momentum+volume)
├── backtester.py                   # Backtest event-driven, entry di Open H+1 (no lookahead)
├── tickers_idx.py                  # Universe: 45 konstituen indeks IDX30 & LQ45, per sektor
├── test_position_manager.py        # Test state machine posisi
├── test_tickers_idx.py             # Test struktur universe saham
├── test_indicators_extended.py     # Test ~18 indikator baru (Backtest Lab)
├── test_custom_backtest.py         # Test algoritma Vote & Trigger
├── schema.sql                      # Skema Supabase + Row Level Security
├── requirements.txt
├── .github/workflows/
│   └── update_after_market_close.yml   # Cron GitHub Actions
├── .streamlit/
│   ├── config.toml                 # Tema warna (opsional, polish visual)
│   └── secrets.toml.example
└── custom_tickers.example.txt
```

> Detail arsitektur & alasan desain dual sidebar + Backtest Lab ada di
> `IMPLEMENTATION_PLAN_UI_BACKTEST_LAB.md` (dokumen perencanaan teknis).

---

## 6. Cara Kerja Fitur-Fitur Utama

### 🎯 Sinyal BUY Besok (prioritas #1 di Screener)
Begitu sinyal BUY muncul di penutupan sesi hari ini, sistem langsung
menghitung hari bursa berikutnya (otomatis skip weekend & libur bursa
resmi BEI) dan menampilkannya sebagai rencana entry — misal
**"Sinyal BUY Besok (21/07/2026)"**.

### 🧪 Backtest Lab
Menu terpisah (bukan bagian dari strategi produksi Screener) untuk
bereksperimen dengan kombinasi indikator sendiri:

1. Pilih saham, periode, dan indikator (dikelompokkan Trend/Momentum/
   Volatilitas/Volume — total ~24 indikator, termasuk SMA/EMA Crossover,
   MACD, ADX, Parabolic SAR, Supertrend, Ichimoku Cloud, RSI, Stochastic,
   Bollinger Bands, OBV, MFI, dan lainnya). Maksimal 8 indikator sekaligus
   (anti-overfitting).
2. Atur **Minimal Konfirmasi** (berapa indikator harus sepakat searah
   sebelum sinyal muncul) dan parameter Take Profit/Stop Loss/Maks Hari
   Holding.
3. Jalankan — hasil backtest (winrate, expectancy, profit factor, max
   drawdown) tampil lengkap dengan chart harga+indikator+posisi entry/exit,
   riwayat trade, equity curve, dan **animasi replay** yang bisa diputar
   untuk menonton bagaimana strategi itu berjalan dari waktu ke waktu.

Data OHLCV diambil dari `price_history` di Supabase (sama seperti halaman
lain — sudah bersumber dari yfinance lewat worker), **bukan** memanggil
yfinance langsung, supaya tidak ada risiko rate-limit dari banyak
pengunjung yang bereksperimen bersamaan. Halaman ini murni eksplorasi
per-sesi — tidak pernah menulis apa pun ke database bersama, dan hasilnya
**in-sample** (bukan validasi out-of-sample) — lihat disclaimer di halaman
itu sendiri.

### 📌 Ongoing Position (prioritas #2 di Screener)
Saat hari bursa yang direncanakan tiba, posisi otomatis "masuk" (status
`OPEN`) di harga Open hari itu, lengkap dengan Take Profit (2×ATR) dan
Stop Loss (1×ATR) yang dihitung dari ATR saat sinyal muncul. Setiap hari
bursa berikutnya, worker mengecek apakah TP/SL/sinyal SELL/batas waktu
tercapai — begitu salah satu terjadi, posisi **otomatis hilang** dari
tabel Ongoing Position (riwayatnya tetap ada di tab Detail Saham).

Dua aturan yang selalu dijaga (di kode DAN di database via constraint):
- **Long-only** — sinyal SELL tidak pernah membuka posisi baru, cuma
  menutup posisi long yang sudah ada.
- **Maks 1 posisi aktif per emiten** — dicegah baik di `position_manager.py`
  maupun lewat partial unique index di `schema.sql`.

### 📊 Detail Saham
Menampilkan Winrate, Expectancy, Profit Factor, Max Drawdown (masing-masing
dengan tooltip ⓘ penjelasan), **Total Return** (`SUM(return_pct)` seluruh
trade historis, non-kompound), chart candlestick + sinyal + RSI + MACD, dan
tabel riwayat trade lengkap.

---

## 7. Troubleshooting

| Masalah | Solusi |
|---|---|
| Dashboard nampilin "Koneksi ke Supabase belum berhasil" | Cek `SUPABASE_URL`/`SUPABASE_ANON_KEY` sudah benar di secrets. |
| Screener kosong / "Belum ada data di database" | Worker belum pernah jalan — trigger manual lewat tab Actions di GitHub (lihat bagian 3.4). |
| `YFRateLimitError` di log worker | Yahoo Finance membatasi rate. Worker sudah pakai retry+delay antar-ticker; kalau masih sering gagal, kurangi jumlah ticker di `tickers_idx.py` atau perbesar `SLEEP_BETWEEN_TICKERS`. |
| Tanggal "Sinyal BUY Besok" meleset di sekitar hari libur | Kalender libur bursa (`idx_calendar.py`) perlu di-update manual tiap tahun setelah BEI merilis kalender resminya (biasanya September tahun sebelumnya). |
| Worker gagal total (semua ticker) | Cek log run di GitHub Actions tab; kemungkinan `SUPABASE_SERVICE_ROLE_KEY` salah/expired, atau Yahoo Finance sedang down. |
| Ingin re-test logika ongoing position | `python test_position_manager.py` — test mandiri tanpa perlu koneksi Supabase asli. |
| Ingin re-test struktur universe saham (IDX30/LQ45) | `python test_tickers_idx.py` — test mandiri, tanpa koneksi apa pun. |
| Ingin re-test indikator baru / algoritma sinyal Backtest Lab | `python test_indicators_extended.py` dan `python test_custom_backtest.py` — test mandiri, tanpa koneksi apa pun. |
| Backtest Lab: "Data historis terlalu pendek" | Indikator dgn periode panjang (mis. SMA200, Ichimoku) butuh warm-up banyak bar — coba periode lebih panjang (mis. 5 Tahun) atau kurangi periode indikator yg dipilih. |
| Sebuah ticker masih muncul padahal di luar daftar sektor manapun | Wajar kalau ticker itu sedang punya posisi PENDING_ENTRY/OPEN aktif ("grandfathering") — worker tetap memprosesnya sampai posisi closed. Lihat `fetch_active_position_tickers()` di `supabase_client.py`. |

---

## 8. Batasan Jujur (baca ini!)

- **Universe saham terbatas pada IDX30 & LQ45** (45 saham blue-chip paling
  likuid) — tidak mencakup saham second-liner/small-cap. BEI me-rebalance
  komposisi indeks ini **tiap kuartal** (Feb/Mei/Agu/Nov) — `tickers_idx.py`
  perlu diverifikasi ulang & diupdate manual pada setiap periode supaya
  universe tetap akurat (lihat komentar maintenance di file tsb).
- Strategi di dashboard ini adalah **trend-following klasik dengan
  multi-konfirmasi** — pendekatan yang sudah dikenal luas, bukan strategi
  proprietary rahasia kelas hedge fund besar.
- Backtest **tidak memperhitungkan**: biaya transaksi/broker fee, pajak,
  slippage eksekusi nyata, dan likuiditas saat entry/exit dalam volume besar.
- Data yfinance untuk saham Indonesia kadang tidak selengkap/seakurat data
  premium (Bloomberg, Refinitiv, dll), dan tidak meng-cover seluruh 900+
  emiten IDX.
- "Total Return (Sum)" di tab Detail Saham adalah penjumlahan sederhana
  return per trade, **bukan** return portofolio riil yang dikompund —
  lihat tooltip di dashboard untuk detail.
- **Backtest Lab bersifat in-sample**: kombinasi indikator diuji pada
  periode historis yang sama dipakai untuk memilihnya — bukan validasi
  out-of-sample/walk-forward. Makin banyak indikator dikombinasikan bukan
  berarti makin baik; risiko overfitting/curve-fitting justru meningkat.
  Hasil bagus di Backtest Lab **tidak otomatis** berarti strategi itu akan
  bekerja di masa depan.
- Ini alat bantu keputusan berbasis data, **bukan pengganti riset
  fundamental dan manajemen risiko yang disiplin**.

Selamat membangun dan trading dengan disiplin. 📊
