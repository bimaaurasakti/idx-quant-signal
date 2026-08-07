"""
views/about.py
===============
Isi tab "Tentang Metodologi" -- FASE 7 REDESIGN (lihat
IMPLEMENTATION_PLAN_UI_REDESIGN_STOCKBIT.md §9.7).

PENTING: isi teks (semua kalimat penjelasan) TIDAK DIUBAH SATU KATA PUN
dari versi sebelumnya -- HANYA dipecah dari 1 blok st.markdown() raksasa
jadi beberapa st.container(border=True) per section, supaya konsisten
secara visual dengan bahasa kartu di halaman lain. st.container(border=True)
dipakai (bukan class custom .iqs-card) krn ini fitur native Streamlit yang
sudah lama dipakai di codebase ini (lihat ui_layout.py versi sebelumnya) --
lebih aman utk konten campuran markdown+code-block+list drpd HTML custom.
"""
from __future__ import annotations
import streamlit as st


def render(ctx) -> None:
    st.subheader("ℹ️ Metodologi & Batasan Jujur")

    with st.container(border=True):
        st.markdown("""
### Arsitektur — kenapa "1 sumber data yang sama"?

Dashboard ini **tidak** melakukan fetch yfinance sendiri tiap kali dibuka. Alurnya:

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

Semua pengunjung — siapa pun, kapan pun — melihat angka yang **persis sama**. Ini juga
menghindari setiap pengunjung memicu rate limit Yahoo Finance sendiri-sendiri.

**🧪 Backtest Lab** (menu terpisah) bekerja dengan prinsip yang sama: membaca harga
OHLCV historis dari Supabase (sudah bersumber dari yfinance lewat worker), lalu
menghitung ULANG indikator & sinyal sesuai pilihan Anda **secara lokal di sesi Anda**
— tanpa memanggil yfinance langsung dan tanpa menulis apa pun ke database bersama.
        """)

    with st.container(border=True):
        st.markdown("""
### 🎯 Universe Saham: IDX30 & LQ45

Dashboard ini secara default HANYA memantau saham-saham yang menjadi konstituen
resmi indeks **LQ45** (45 saham paling likuid & berkapitalisasi besar di BEI) —
yang otomatis mencakup seluruh **30 saham IDX30**.

BEI me-review & me-rebalance komposisi kedua indeks ini **setiap kuartal**. Anda
tetap bisa menambah saham lain di luar universe default lewat `custom_tickers.txt`.
        """)

    with st.container(border=True):
        st.markdown("""
### Bagaimana sinyal dihasilkan? (Screener & Detail Saham)

Multi-confirmation signal: BUY/SELL hanya muncul kalau minimal 2 dari 3 kondisi
searah — **Trend** (harga > SMA50 > SMA200), **Momentum** (MACD cross + RSI di
zona sehat), **Volume** (≥20% di atas rata-rata 20 hari).
        """)

    with st.container(border=True):
        st.markdown("""
### Bagaimana "Ongoing Position" bekerja?

1. Sinyal BUY muncul di penutupan hari ini → status **PENDING_ENTRY**.
2. Hari bursa berikutnya, worker eksekusi entry di harga **Open** → status **OPEN**,
   TP/SL dihitung dari ATR saat sinyal muncul (TP = entry + 2×ATR, SL = entry − 1×ATR).
3. Setiap hari bursa, worker cek TP/SL/sinyal SELL/batas waktu (20 hari bursa) →
   posisi ditutup, otomatis hilang dari "Ongoing Position".

**Dua aturan keras yang selalu dijaga**: Long-only (sinyal SELL tidak pernah membuka
posisi baru), dan maks 1 posisi aktif per emiten.
        """)

    with st.container(border=True):
        st.markdown("""
### Kamus istilah

- **Winrate**: % trade yang profit dari seluruh trade historis.
- **Expectancy**: (winrate × avg profit) − (lossrate × avg loss).
- **Profit Factor**: total profit ÷ total loss. >1 = profitable secara agregat.
- **Max Drawdown**: penurunan terbesar puncak-ke-lembah pada equity curve backtest.
- **Total Return (Sum)**: SUM(return_pct) seluruh trade historis, tidak dikompund.
        """)

    with st.container(border=True):
        st.markdown("""
### Kenapa ini BUKAN "kelas Renaissance Technologies"

- **Data**: yfinance = data harian/delayed. RenTech pakai data tick-by-tick, order
  book, dan data alternatif eksklusif puluhan tahun.
- **Eksekusi**: dashboard ini tidak terhubung ke broker — sinyal dieksekusi manual.
- **Riset**: strategi di sini trend-following klasik yang dikenal luas.
- **Skala**: cocok untuk trading personal, bukan mengelola miliaran dolar.
        """)

    with st.container(border=True):
        st.markdown("""
### Keterbatasan data

- Universe terbatas 45 konstituen IDX30/LQ45.
- Beberapa saham IDX punya data kosong/tidak lengkap di Yahoo Finance.
- Backtest tidak memperhitungkan biaya transaksi, pajak, atau slippage nyata.
- Ini alat bantu keputusan, **bukan pengganti riset fundamental dan manajemen
  risiko yang disiplin**.
        """)
