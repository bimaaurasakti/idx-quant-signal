"""
Daftar default ticker saham Indonesia (IDX) untuk yfinance.
Semua ticker IDX di Yahoo Finance memakai suffix '.JK'.

UNIVERSE: konstituen resmi indeks LQ45 (otomatis mencakup seluruh anggota
IDX30, karena IDX30 adalah 30 saham paling likuid/berkapitalisasi besar
YANG DIPILIH DARI DALAM LQ45).
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
    """True kalau ticker ini termasuk 45 konstituen default (LQ45)."""
    t = ticker_no_suffix.upper().replace(".JK", "")
    for tickers in IDX_TICKERS.values():
        if t in tickers:
            return True
    return False
