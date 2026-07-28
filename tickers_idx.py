"""
Daftar default ticker saham Indonesia (IDX) untuk yfinance.
Semua ticker IDX di Yahoo Finance memakai suffix '.JK'.

UNIVERSE: konstituen resmi indeks LQ45 (otomatis mencakup seluruh anggota
IDX30, karena IDX30 adalah 30 saham paling likuid/berkapitalisasi besar
YANG DIPILIH DARI DALAM LQ45 -- lihat IMPLEMENTATION_PLAN.md Bagian 1).
Union(IDX30, LQ45) == LQ45, jadi cukup satu daftar 45 saham di bawah ini.

Ticker anggota IDX30 ditandai terpisah di IDX30_TICKERS (dipakai utk badge
"IDX30" di UI -- opsional, lihat IMPLEMENTATION_PLAN.md Bagian 2.5) tanpa
mengubah struktur sektor di bawah.

=====================================================================
PENTING -- JADWAL UPDATE: BEI me-rebalance LQ45/IDX30 SETIAP KUARTAL
    (evaluasi mayor Januari/April/Juli/Oktober, EFEKTIF Februari/Mei/
    Agustus/November -- kebijakan berlaku sejak April 2024, LEBIH SERING
    dari anggapan umum "2x setahun"). Daftar di bawah adalah konstituen
    periode 4 Mei 2026 -- 31 Juli 2026, hasil evaluasi BEI No.
    Peng-00067/BEI.POP/04-2026 (diverifikasi 27 Juli 2026).

    Periode ini SEGERA BERAKHIR. BEI sudah mengumumkan (14 Juli 2026)
    evaluasi berikutnya akan dilakukan akhir Juli 2026, efektif awal
    Agustus 2026, DENGAN KRITERIA BARU yang mengeluarkan saham "High
    Shareholding Concentration" (HSC) -- BEI mengidentifikasi 51 saham
    HSC (naik dari 14), jadi rotasi kali ini berpotensi lebih besar dari
    biasanya.

    SEBELUM PAKAI FILE INI DI PRODUCTION: verifikasi ulang komposisi
    terbaru di https://www.idx.co.id/id/produk/indeks/ (menu Berita >
    Pengumuman, cari "Evaluasi Indeks IDX30 LQ45 IDX80") atau berita
    pasar modal (Bisnis.com/Kontan/IDX Channel, keyword "rebalancing
    LQ45"). Kalau sudah ada daftar baru yang efektif, update dict di
    bawah SEBELUM menjalankan migrasi database (IMPLEMENTATION_PLAN.md
    Fase 3).
=====================================================================

Yahoo Finance tidak meng-cover seluruh 900+ emiten IDX dengan kualitas
data yang layak, tapi konstituen LQ45/IDX30 (blue-chip paling likuid)
umumnya punya data bagus di Yahoo Finance -- membatasi universe ke
saham-saham ini juga mengurangi risiko YFTickerMissingError/data kosong
dibanding universe lama yang mencakup banyak saham second-liner.

Anda bisa menambah ticker LAIN DI LUAR universe default ini lewat file
custom_tickers.txt (satu ticker per baris, tanpa '.JK') -- mekanisme ini
TIDAK BERUBAH dari versi sebelumnya.
"""

IDX_TICKERS = {
    "Perbankan": [
        "BBCA", "BBRI", "BMRI", "BBNI", "BBTN",
    ],
    "Consumer_Goods": [
        "UNVR", "ICBP", "INDF", "CPIN", "JPFA", "KLBF", "AMRT", "MAPI", "HRTA",
    ],
    "Energi_Komoditas": [
        "ADRO", "ITMG", "PTBA", "AKRA", "MEDC", "PGAS", "PGEO",
        "AADI", "BRPT", "CUAN", "ESSA",
    ],
    "Telekomunikasi_Infrastruktur": [
        "TLKM", "EXCL", "ISAT", "TOWR",
    ],
    "Pertambangan": [
        "ANTM", "INCO", "MDKA", "BUMI", "MBMA", "AMMN", "ADMR", "DEWA",
    ],
    "Industri_Manufaktur": [
        "ASII", "UNTR", "INKP", "SMGR",
    ],
    "Teknologi_Digital": [
        "GOTO", "EMTK", "WIFI", "SCMA",
    ],
}

# 30 anggota IDX30 -- subset paling elite (likuiditas & mkt-cap tertinggi)
# yang dipilih dari dalam LQ45 di atas. Semua ticker di sini WAJIB juga ada
# di IDX_TICKERS (divalidasi di test_tickers_idx.py).
IDX30_TICKERS = {
    "AADI", "ADRO", "ADMR", "AMRT", "ANTM", "ASII", "BBCA", "BBNI", "BBRI",
    "BMRI", "BRPT", "BUMI", "CPIN", "EMTK", "GOTO", "ICBP", "INCO", "INDF",
    "INKP", "JPFA", "KLBF", "MBMA", "MDKA", "MEDC", "PGAS", "PGEO", "PTBA",
    "TLKM", "UNTR", "UNVR",
}


def get_all_tickers(with_suffix: bool = True) -> list[str]:
    """Kembalikan daftar flat semua ticker (default + custom jika ada)."""
    flat = []
    for group in IDX_TICKERS.values():
        flat.extend(group)

    # Gabungkan dengan custom_tickers.txt jika ada, tanpa duplikat
    import os
    custom_path = os.path.join(os.path.dirname(__file__), "custom_tickers.txt")
    if os.path.exists(custom_path):
        with open(custom_path, "r") as f:
            for line in f:
                t = line.strip().upper().replace(".JK", "")
                if t and t not in flat:
                    flat.append(t)

    flat = sorted(set(flat))
    if with_suffix:
        return [f"{t}.JK" for t in flat]
    return flat


def get_sector_of(ticker_no_suffix: str) -> str:
    t = ticker_no_suffix.upper().replace(".JK", "")
    for sector, tickers in IDX_TICKERS.items():
        if t in tickers:
            return sector
    return "Lainnya"


def is_idx30(ticker_no_suffix: str) -> bool:
    """True kalau ticker ini anggota IDX30 (subset paling elite dari LQ45)."""
    return ticker_no_suffix.upper().replace(".JK", "") in IDX30_TICKERS


def is_lq45(ticker_no_suffix: str) -> bool:
    """True kalau ticker ini termasuk 45 konstituen default (LQ45) di
    IDX_TICKERS -- False untuk ticker legacy/grandfathered (posisi aktif
    dari ticker yang baru keluar universe) atau custom_tickers.txt yang
    berada di luar daftar LQ45 resmi."""
    t = ticker_no_suffix.upper().replace(".JK", "")
    for tickers in IDX_TICKERS.values():
        if t in tickers:
            return True
    return False
