# IDX Quant Signal Dashboard

Dashboard sinyal trading kuantitatif untuk saham Indonesia (IDX), berbasis data
[yfinance](https://github.com/ranaroussi/yfinance). Menampilkan sinyal
multi-konfirmasi (trend + momentum + volume) beserta backtest historis yang
transparan — winrate, expectancy, profit factor, max drawdown — dihitung
langsung dari data, bukan angka klaim.

> ⚠️ **Bukan nasihat keuangan.** Ini alat riset kuantitatif untuk membantu
> Anda membuat keputusan berbasis data. Performa historis tidak menjamin
> hasil masa depan. Selalu lakukan due diligence sendiri.

---

## 1. Instalasi

Jalankan di komputer Anda sendiri (butuh koneksi internet aktif — dashboard
ini TIDAK bisa dijalankan tanpa akses ke Yahoo Finance):

```bash
# 1. Buat virtual environment (opsional tapi disarankan)
python -m venv venv
source venv/bin/activate      # Mac/Linux
# venv\Scripts\activate       # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Jalankan dashboard
streamlit run app.py
```

Dashboard akan otomatis terbuka di browser (biasanya `http://localhost:8501`).

---

## 2. Struktur Project

```
idx-quant-dashboard/
├── app.py                      # Aplikasi Streamlit utama (4 tab)
├── tickers_idx.py               # Daftar default ~150+ saham IDX per sektor
├── data_fetcher.py              # Pengambilan data via yfinance + caching lokal
├── indicators.py                 # Indikator teknikal (SMA, EMA, RSI, MACD, ATR, Bollinger)
├── signals.py                    # Logika sinyal multi-konfirmasi
├── backtester.py                 # Backtest event-driven (no lookahead bias)
├── custom_tickers.example.txt   # Contoh cara menambah ticker sendiri
├── requirements.txt
└── .cache/                       # (dibuat otomatis) cache data parquet
```

---

## 3. Cara Pakai

### Tab Screener
Klik **"Jalankan Analisis"** untuk fetch & analisis semua saham di daftar
default. Proses ini bisa memakan waktu beberapa menit untuk pertama kali
(tergantung jumlah saham dan koneksi internet Anda) — hasil akan di-cache
lokal selama 6 jam supaya reload berikutnya jauh lebih cepat.

Hasil diranking berdasarkan **Expectancy**, bukan winrate mentah — karena
winrate tinggi bisa tetap merugi kalau rata-rata kerugian jauh lebih besar
dari rata-rata profit. Gunakan filter **"Minimal jumlah trade historis"**
untuk menyembunyikan saham dengan sampel data terlalu sedikit (statistik
tidak reliabel).

### Tab Detail Saham
Pilih satu saham untuk melihat chart candlestick lengkap dengan sinyal
BUY/SELL historis, indikator RSI & MACD, plus tabel rinci setiap trade yang
tercatat dalam backtest.

### Tab Risk Calculator
Hitung ukuran posisi (position sizing) berdasarkan modal, toleransi risiko
per trade, dan ATR saham — bukan asal tebak jumlah lot.

### Tab Tentang Metodologi
Penjelasan lengkap & jujur soal cara kerja sinyal, cara backtest dihitung,
dan batasan sistem ini dibanding hedge fund kuantitatif sungguhan.

---

## 4. Menambah Saham Sendiri

Rename `custom_tickers.example.txt` menjadi `custom_tickers.txt`, lalu isi
satu ticker per baris (tanpa suffix `.JK`), misalnya:

```
PANI
CYBR
RATU
```

File ini akan otomatis digabung dengan daftar default saat aplikasi berjalan.

---

## 5. Troubleshooting

| Masalah | Solusi |
|---|---|
| `YFRateLimitError` / banyak `Gagal fetch` | Yahoo Finance membatasi rate. Tunggu beberapa menit, atau kurangi jumlah saham yang dianalisis sekaligus (pakai filter sektor). |
| Data kosong untuk saham tertentu | Beberapa saham IDX tidak/kurang di-cover Yahoo Finance. Ini keterbatasan data, bukan bug. |
| Import error `yfinance`/`streamlit` | Pastikan `pip install -r requirements.txt` berhasil di virtual environment yang aktif. |
| Analisis lambat pertama kali | Normal — setelah cache terisi (`.cache/` folder), reload berikutnya jauh lebih cepat. |
| `pyarrow` error saat caching | Jalankan `pip install pyarrow` secara terpisah. |

---

## 6. Batasan Jujur (baca ini!)

- Strategi di dashboard ini adalah **trend-following klasik dengan multi-konfirmasi**
  — pendekatan yang sudah dikenal luas, bukan strategi proprietary rahasia.
- Backtest di sini **tidak memperhitungkan**: biaya transaksi/broker fee, pajak,
  slippage eksekusi nyata, dan likuiditas saat entry/exit dalam volume besar.
- Data yfinance untuk saham Indonesia kadang tidak selengkap/seakurat data
  premium (Bloomberg, Refinitiv, dll).
- Ini alat bantu keputusan, **bukan pengganti riset fundamental dan manajemen
  risiko yang disiplin**.

Selamat trading dengan disiplin dan manajemen risiko yang baik. 📊
