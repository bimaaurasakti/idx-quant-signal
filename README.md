# IDX Quant Signal — Monorepo (Next.js Dashboard + Python Quant Pipeline)

[![Next.js 16](https://img.shields.io/badge/Next.js-16.3%20(Turbopack)-black?style=flat-square&logo=next.js)](https://nextjs.org/)
[![React 19](https://img.shields.io/badge/React-19-blue?style=flat-square&logo=react)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6?style=flat-square&logo=typescript)](https://www.typescriptlang.org/)
[![Tailwind CSS v4](https://img.shields.io/badge/Tailwind_CSS-v4-38B2AC?style=flat-square&logo=tailwind-css)](https://tailwindcss.com/)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=flat-square&logo=supabase)](https://supabase.com/)
[![Python 3.11](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python)](https://python.org/)
[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Automated_CI%2FCD-2088FF?style=flat-square&logo=github-actions)](https://github.com/features/actions)

Platform analitik kuantitatif, screener saham, dan simulator **TradingView Bar Replay** untuk konstituen saham Indonesia (**IDX30 & LQ45**). Platform ini digerakkan oleh algoritma *multi-confirmation trend-following* 5-pilar objektif yang dilengkapi manajemen risiko posisi asimetris *hybrid 2-tier exit*.

---

## 🏛️ Arsitektur Sistem (Zero-Proxy Serverless)

```
                                  [ Yahoo Finance API ]
                                            │
                                            ▼ (Data OHLCV Resmi EOD)
[ GitHub Actions Cron ] ──────► [ pipeline/worker_fetch_and_update.py ]
(12:37 & 16:34 WIB)                         │ (Hitung 5 Pilar Indikator, Sinyal, Sizing)
                                            ▼ (Service Role Key)
                                 [ Supabase PostgreSQL DB ]
                                            │
                                            ▼ (Public Anon Key / RLS Read-Only)
                                [ Next.js 16 Web Dashboard ]
                                (Vercel / Cloudflare / Node Server)
```

- **Zero 24/7 Server Cost:** Tidak membutuhkan server web Python / VPS yang menyala terus-menerus. Frontend adalah web app statis/SSR hemat biaya, dan pipeline kuantitatif berjalan otomatis via free compute runner **GitHub Actions**.
- **Single Source of Truth:** Database Supabase PostgreSQL menyimpan seluruh riwayat lilin harga harian, sinyal kuantitatif, dan status posisi secara terpusat.
- **Client-Side Scalability:** Dashboard membaca data langsung dari Supabase tanpa latensi perantara (*zero-proxy*), dilindungi oleh PostgreSQL *Row Level Security* (RLS) `public-read-only`.

---

## 🌟 Fitur Utama Platform

### 1. 🔍 Market Screener & Ranking Matrix (`/screener`)
- Pemindaian otomatis seluruh konstituen **LQ45 & IDX30** pasca pasar tutup (*End-of-Day*).
- Matriks evaluasi sinyal kuantitatif: skor konfirmasi (*conviction rating*), pemeringkatan komposit (*composite rank*), dan daftar pantau kandidat entri esok hari (*Buy Tomorrow*).

### 2. 📊 Detail Saham & Status Syarat Strategi (`/detail/[ticker]`)
- **Status Syarat Strategi 5-Pilar Dinamis**: Menampilkan status *live* kelima pilar aturan kuantitatif (*Market Regime IHSG*, *Stage 2 Trend*, *Pullback MA20*, *RSI Momentum*, dan *Konfirmasi Volume*).
- **Resolusi Sinyal Akurat**: Membedakan secara tegas antara status `Buy`, `Hold (Posisi Aktif)` jika saham sedang dimiliki, dan `Wait & See` (netral) jika sedang di luar posisi.
- **Chart TradingView Lightweight Charts v5 Setinggi 820px Simetris**:
  - **Pane 0 (380px)**: Candlestick, Overlay Volume Histogram, SMA50, SMA200, serta penanda panah BUY/EXIT.
  - **Pane 1 (220px)**: Subplot RSI 14 lengkap dengan garis batas 70 (*Overbought*), 50 (*Centerline*), dan 30 (*Oversold*).
  - **Pane 2 (220px)**: Subplot MACD dengan Garis Nol (*Zero Line*) dan Histogram 4-Warna dinamis.
  - Alokasi rasio pane seimbang 1:1 untuk RSI dan MACD via `setStretchFactor(380, 220, 220)`.
- **Interactive Connected Trade Markers**: Arahkan kursor (*hover*) pada panah BUY/EXIT untuk menyorot (*glow*) pasangan trade tersebut dan memunculkan *floating glassmorphic trade card*.
- **Tabel Riwayat Posisi**: Catatan riwayat hasil trade riil per saham tanpa eksposur teknis kode internal.

### 3. ⚡ TradingView Bar Replay di Back Test Lab (`/backtest`)
- **Simulasi True Cut-Off**: Lilin masa depan disembunyikan (*cut-off*) dan dimunculkan satu per satu tanpa bias masa depan (*no hindsight bias*).
- **Kontrol Playback Komprehensif**:
  - `Play / Pause` (shortcut: <kbd>Space</kbd>).
  - `Step Forward` 1 lilin (shortcut: <kbd>→</kbd> Panah Kanan).
  - `Step Backward` 1 lilin (shortcut: <kbd>←</kbd> Panah Kiri).
  - `Prev Trade` & `Next Trade` untuk melompat langsung antar-titik eksekusi trade.
  - Pengatur kecepatan: `0.5x`, `1x`, `2x`, `5x`, dan `10x`.
  - Timeline Scrubber Slider interaktif dengan tooltip progress bar.
- **Live Replay HUD & Dynamic Position Tracking**:
  - Menampilkan status posisi live saat replay berjalan: `🟢 HOLDING` (dengan harga beli, harga lilin saat ini, durasi hari bursa, dan **Floating PnL %** yang berfluktuasi hidup) vs `⚪ FLAT (CASH)`.
  - 4 metrik kumulatif berjalan: Winrate live %, Total realized PnL %, jumlah trade selesai, dan indeks modal.
- **Live Tabs**:
  - Tabel *Riwayat Trade Selesai* yang bertambah dinamis saat lilin menyentuh tanggal exit.
  - Grafik *Live Equity Curve* (pertumbuhan modal compounding per trade).

### 4. 💼 Portfolio Forward-Testing Tracker (`/portfolio`)
- Buku besar (*ledger*) seluruh posisi yang telah selesai (*closed*) dengan kalkulasi winrate, total return, profit factor, dan rincian alasan exit (*TP1*, *Trailing SL*, *Time Exit*, *Sell Signal*).

### 5. 🛡️ Risk Management & Position Sizing (`/risk`)
- **Kalkulator Ukuran Posisi**: Alokasi risiko modal terukur berbasis jarak volatilitas ATR harian.
- **Visualisasi Hybrid 2-Tier Exit**:
  - **Fase 1 (Entry)**: Toleransi Stop Loss awal 1.5 ATR untuk menyerap fluktuasi intra-day.
  - **Fase 2 (TP1 Tercapai)**: Realisasi profit 50% porsi pada target +2.0 ATR, sisa posisi digeser ke Break-Even (*Risk = 0*).
  - **Fase 3 (Runner Trailing)**: Sisa 50% posisi dibiarkan berlari mengikuti tren dengan trailing stop SMA20 hingga tren patah.

### 6. 📖 Metodologi & Kamus Kuantitatif (`/about`)
- Dokumentasi matematis transparansi algoritma, matriks validasi empiris 5 tahun pada 44.000+ lilin bursa, serta kamus istilah quant (*Winrate*, *Profit Factor*, *Expectancy*, *ATR*).

---

## 📁 Struktur Direktori Monorepo

```
.
├── .github/
│   └── workflows/
│       └── update_after_market_close.yml   # Workflow otomatisasi GitHub Actions
├── app/                                    # Next.js 16 App Router
│   ├── screener/                           # Screener emiten & matriks peringkat
│   ├── detail/[ticker]/                    # Detail teknikal, status syarat 5-pilar & chart
│   ├── backtest/                           # TradingView Bar Replay & simulator interaktif
│   ├── portfolio/                          # Forward-tested position tracking & metrics
│   ├── risk/                               # Kalkulator sizing & visualizer 2-tier exit
│   └── about/                              # Metodologi, parameter kuantitatif & kamus
├── components/                             # Komponen UI modern & modular
│   ├── ui/                                 # Primitif accessible (Table, Select, Slider, dll)
│   ├── backtest/                           # ReplayToolbar, ReplayHud, BacktestChart, TradesTable
│   ├── detail/                             # PriceHeader, StrategyStatusChecklist, Banners
│   ├── screener/                           # RankingTable, BuyTomorrowGrid, OngoingGrid
│   ├── portfolio/                          # ClosedPositionsTable, FiltersBar, Chart cards
│   ├── risk/                               # TwoTierVisualizer & parameter sizing
│   ├── about/                              # ArchitectureTab, SignalEngineTab, RiskTab
│   └── shared/                             # PriceChart, MetricCard, PageHeader, AppShell
├── pipeline/                               # Python Quant Pipeline & Worker Engine
│   ├── worker_fetch_and_update.py          # Script eksekusi utama EOD GitHub Actions
│   ├── indicators.py                       # Implementasi indikator teknikal murni
│   ├── indicator_registry.py               # Registry metadata indikator & voting rules
│   ├── signals.py                          # Multi-confirmation rules & IHSG regime check
│   ├── position_manager.py                 # Hybrid 2-tier exit position state machine
│   ├── backtester.py                       # Event-driven backtester (no lookahead bias)
│   ├── data_fetcher.py                     # Yahoo Finance client with retry logic
│   ├── idx_calendar.py                     # Kalender hari bursa resmi BEI (skip libur)
│   ├── supabase_client.py                  # Client database Supabase untuk worker
│   ├── requirements.txt                    # Dependensi Python minimal (pandas, numpy, dll)
│   └── schema.sql                          # Skema DDL tabel database Supabase
├── hooks/                                  # React Query hooks untuk fetch data reaktif
├── lib/                                    # Supabase client, API mappers, formatters, type contracts
└── public/                                 # Static assets & icons
```

---

## 🚀 Panduan Menjalankan Secara Lokal

### 1. Menjalankan Frontend (Next.js Dashboard)

Pastikan telah menginstall **Bun** (direkomendasikan) atau **Node.js >= 20**:

```bash
# 1. Install dependensi
bun install
# atau: npm install

# 2. Siapkan environment variable lokal
cp .env.local.example .env.local
# Isi NEXT_PUBLIC_SUPABASE_URL dan NEXT_PUBLIC_SUPABASE_ANON_KEY

# 3. Jalankan development server
bun run dev
# atau: npm run dev

# 4. Buka di browser
# http://localhost:3000
```

### 2. Menjalankan Pipeline Kuantitatif (Python)

Pastikan telah menginstall **Python 3.11+**:

```bash
cd pipeline

# 1. Buat dan aktifkan virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 2. Install dependensi
pip install -r requirements.txt

# 3. Set environment variable
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="eyJhbGciOi..."
# Windows PowerShell:
# $env:SUPABASE_URL="https://your-project.supabase.co"
# $env:SUPABASE_SERVICE_ROLE_KEY="eyJhbGciOi..."

# 4. Jalankan worker harian
python worker_fetch_and_update.py
```

---

## ⏰ Jadwal Otomatisasi GitHub Actions (Dual Schedule)

Untuk mencegah sinyal palsu dari lilin setengah hari, otomatisasi dibagi menjadi dua sesi terpisah:
1. **Sesi 1 (12:37 WIB / `--monitor-only`)**: Mode pengawasan murni untuk mengevaluasi apakah posisi aktif menyentuh TP1 (+2.0 ATR) atau Stop Loss. **Dilarang memicu sinyal BUY baru.**
2. **Sesi EOD (16:34 WIB / Master EOD Run)**: Pengambilan candle resmi final penutupan pasar, pengujian Market Regime IHSG, validasi syarat strategi 5-pilar, dan penerbitan sinyal baru.

---

## 🔒 Keamanan & Variabel Lingkungan

| Variabel | Lingkup | Deskripsi |
| :--- | :--- | :--- |
| `NEXT_PUBLIC_SUPABASE_URL` | Frontend & Pipeline | Endpoint URL project Supabase. |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Frontend | Kunci publik aman browser, dilindungi oleh PostgreSQL Row Level Security (*read-only*). |
| `SUPABASE_SERVICE_ROLE_KEY` | Pipeline Worker Sahaja | Kunci *service role* dengan hak tulis tabel. **DILARANG KERAS** dibocorkan ke frontend. Disimpan sebagai GitHub Actions Secret. |

---

## 📄 Lisensi & Penafian (*Disclaimer*)

Platform ini dibangun untuk tujuan edukasi analisis kuantitatif dan riset strategi pasar modal. **Bukan merupakan rekomendasi atau nasihat keuangan individual.** Performa historis dan hasil simulasi backtest tidak menjamin performa masa depan. Selalu terapkan manajemen risiko yang disiplin dalam bertransaksi saham.
