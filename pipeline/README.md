# IDX Quant Signal — Pipeline & Batch Worker

Direktori ini berisi engine kuantitatif, kalkulator indikator teknikal, strategi sinyal multi-konfirmasi, position manager, dan batch worker yang dijalankan secara otomatis oleh **GitHub Actions**.

---

## 🛠️ Modul Utama

- **`worker_fetch_and_update.py`**: Orchestrator worker harian yang dieksekusi oleh GitHub Actions cron.
  - Mode `--monitor-only`: Dijalankan pada penutupan sesi 1 (12:08 / 12:37 WIB) untuk memantau posisi aktif.
  - Mode EOD Master (default): Dijalankan setelah pasar tutup (16:34 WIB) untuk full universe update & sinkronisasi database Supabase.
- **`indicators.py` & `indicator_registry.py`**: Implementasi matematis murni seluruh indikator teknikal berbasis NumPy dan Pandas (tanpa ketergantungan TA-Lib C-library).
- **`signals.py`**: Logika konfirmasi multi-indikator (Uptrend Hard Gate, MACD crossover, RSI healthy bull, Volume breakout, Anti-FOMO SMA20 distance) & Market Regime filter IHSG (^JKSE).
- **`position_manager.py`**: State machine posisi long-only dengan sistem Hybrid 2-Tier Exit (TP1 2.0 ATR amankan 50% lot, geser SL sisa runner ke Break-Even, trailing runner exit SMA20).
- **`backtester.py` & `custom_backtest.py`**: Event-driven backtesting engine (tanpa lookahead bias).
- **`data_fetcher.py`**: Pengambilan data OHLCV harian dari Yahoo Finance (`yfinance`) dengan exponential backoff retry.
- **`idx_calendar.py`**: Kalender hari bursa resmi Bursa Efek Indonesia (BEI) untuk bypass run saat weekend/libur bursa.
- **`supabase_client.py`**: Client koneksi database Supabase khusus worker menggunakan `SUPABASE_SERVICE_ROLE_KEY`.

---

## 🚀 Menjalankan Secara Lokal

### 1. Buat Virtual Environment & Install Dependencies
```bash
cd pipeline
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Set Variabel Lingkungan
Salin `.env.example` menjadi `.env`:
```env
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_SERVICE_ROLE_KEY="eyJhbGciOi..."
```

### 3. Eksekusi Worker
```bash
# Dari root monorepo:
python pipeline/worker_fetch_and_update.py

# Atau hanya mode monitoring sesi siang:
python pipeline/worker_fetch_and_update.py --monitor-only
```
