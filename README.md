# IDX Quant Signal — Monorepo (Next.js Dashboard + Python Quant Pipeline)

Platform kuantitatif dan dashboard analitik sinyal saham Indonesia (IDX30 & LQ45) berbasis strategi multi-konfirmasi trend-following dengan manajemen risiko posisi 2-tier.

Repository ini menggabungkan:
1. **Frontend Web Dashboard (`app/`, `components/`)**: Next.js 16 (Turbopack) + React 19 + TypeScript + Tailwind CSS v4 + TanStack Query yang membaca data secara reaktif dan aman langsung dari **Supabase** (Row Level Security anon read-only).
2. **Quant Pipeline & Batch Worker (`pipeline/`)**: Python quant engine yang dijalankan otomatis oleh **GitHub Actions** setiap hari bursa untuk fetch data Yahoo Finance, kalkulasi indikator, validasi regime IHSG, eksekusi sinyal multi-konfirmasi, dan sinkronisasi ke Supabase.
3. **Automated CI/CD Workflows (`.github/workflows/`)**: Scheduled GitHub Actions runner otomatis (Sesi 1 monitor & Master EOD run).

---

## 🏛️ Arsitektur Sistem

```
                                  [ Yahoo Finance API ]
                                            │
                                            ▼ (OHLCV Daily)
[ GitHub Actions Cron ] ──────► [ pipeline/worker_fetch_and_update.py ]
(12:08, 12:37, 16:34 WIB)                   │ (Indicators, Signals, Sizing, Backtest)
                                            ▼ (Service Role Key)
                                 [ Supabase PostgreSQL DB ]
                                            │
                                            ▼ (Public Anon Key / RLS Read-Only)
                                [ Next.js 16 Web Dashboard ]
                                (Vercel / Cloudflare / Node Server)
```

- **Zero 24/7 Server Cost:** Tidak membutuhkan server web Python / VPS yang menyala terus-menerus. Frontend adalah web app statis/SSR hemat biaya, dan pipeline berjalan via free compute GitHub Actions.
- **Single Source of Truth:** Database Supabase menyimpan hasil snapshot sinyal, riwayat candle, dan status posisi secara terpusat.

---

## 📁 Struktur Direktori Monorepo

```
.
├── .github/
│   └── workflows/
│       └── update_after_market_close.yml   # CI/CD otomatisasi update sinyal bursa
├── app/                                    # Next.js 16 App Router pages
│   ├── screener/                           # Screener emiten & matriks peringkat
│   ├── detail/[ticker]/                    # Detail teknikal & riwayat trade per saham
│   ├── portfolio/                          # Forward-tested live position tracking
│   ├── risk/                               # Kalkulator sizing & 2-tier exit visualizer
│   ├── backtest/                           # Laboratorium simulasi & replay
│   └── about/                              # Metodologi, formula & bukti empiris benchmark
├── components/                             # Komponen UI modern & accessible
│   ├── ui/                                 # Primitif table, select, input, button, slider
│   ├── screener/                           # RankingTable, BuyTomorrowGrid, OngoingGrid
│   ├── portfolio/                          # ClosedPositionsTable, FiltersBar, Chart cards
│   ├── detail/                             # PriceHeader, TradeHistoryTable, Banners
│   ├── risk/                               # TwoTierVisualizer & sizing parameters
│   └── shared/                             # MetricCard, PriceChart, SignalBadge, AppShell
├── pipeline/                               # Python Quant Pipeline & Worker Engine
│   ├── worker_fetch_and_update.py          # Script eksekusi utama GitHub Actions
│   ├── indicators.py                       # Implementasi indikator teknikal murni
│   ├── indicator_registry.py               # Registry metadata indikator & voting rules
│   ├── signals.py                          # Multi-confirmation rules & IHSG regime check
│   ├── position_manager.py                 # Hybrid 2-tier exit position state machine
│   ├── backtester.py                       # Event-driven backtester (no lookahead bias)
│   ├── custom_backtest.py                  # Dynamic indicator combination testing
│   ├── data_fetcher.py                     # Yahoo Finance client with retry logic
│   ├── idx_calendar.py                     # Kalender hari bursa resmi BEI (skip libur)
│   ├── supabase_client.py                  # Client database Supabase untuk worker
│   ├── requirements.txt                    # Dependensi Python minimal (pandas, numpy, dll)
│   └── schema.sql                          # Skema DDL tabel database Supabase
├── hooks/                                  # React Query hooks (useScreener, useDetail, dll)
├── lib/                                    # API client, mappers, formatters, type contracts
└── public/                                 # Static assets & icons
```

---

## 🚀 Panduan Menjalankan Secara Lokal

### 1. Menjalankan Frontend (Next.js)

Pastikan telah menginstall **Bun** (atau Node.js >= 20):

```bash
# 1. Install dependensi
bun install

# 2. Siapkan env lokal
cp .env.local.example .env.local
# Masukkan NEXT_PUBLIC_SUPABASE_URL dan NEXT_PUBLIC_SUPABASE_ANON_KEY

# 3. Jalankan development server
bun run dev
# Buka http://localhost:3000
```

### 2. Menjalankan Quant Pipeline (Python)

Pastikan telah menginstall **Python 3.11+**:

```bash
cd pipeline

# 1. Buat virtual environment
python -m venv venv
# Windows: .\venv\Scripts\activate
# Linux/macOS: source venv/bin/activate

# 2. Install dependensi
pip install -r requirements.txt

# 3. Set environment variable (bisa via .env atau export)
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="eyJhbGciOi..."

# 4. Jalankan worker
python worker_fetch_and_update.py
```

---

## 🔒 Keamanan & Variabel Lingkungan

- **`NEXT_PUBLIC_SUPABASE_ANON_KEY`**: Aman dipublikasikan ke browser karena dilindungi oleh PostgreSQL Row Level Security (RLS) `public-read-only`.
- **`SUPABASE_SERVICE_ROLE_KEY`**: **Hanya untuk pipeline**. Jangan pernah diletakkan di prefix `NEXT_PUBLIC_` atau dibocorkan ke frontend. Kunci ini disimpan sebagai Secret di GitHub Actions repository settings.
