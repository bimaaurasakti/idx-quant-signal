"""
Daftar default ticker saham Indonesia (IDX) untuk yfinance.
Semua ticker IDX di Yahoo Finance memakai suffix '.JK'.

Yahoo Finance TIDAK meng-cover seluruh 900+ emiten IDX dengan kualitas data
yang layak (banyak yang datanya kosong/tidak likuid). Daftar di bawah ini
berisi saham-saham yang secara umum aktif diperdagangkan dan datanya
tersedia dengan baik di Yahoo Finance, dikelompokkan per sektor.

Anda bisa menambah/mengurangi ticker sendiri di file ini, atau upload
file custom_tickers.txt (satu ticker per baris, tanpa '.JK') dan aplikasi
akan otomatis menggabungkannya.
"""

IDX_TICKERS = {
    "Perbankan": [
        "BBCA", "BBRI", "BMRI", "BBNI", "BRIS", "BJTM", "BJBR", "BTPS",
        "BNGA", "BDMN", "PNBN", "MEGA", "AGRO", "BABP", "BBTN", "BNLI",
        "ARTO", "BBYB", "BANK", "NISP",
    ],
    "Consumer_Goods": [
        "UNVR", "ICBP", "INDF", "MYOR", "ULTJ", "CPIN", "JPFA", "GGRM",
        "HMSP", "KLBF", "SIDO", "TSPC", "KAEF", "AMRT", "MAPI", "ACES",
        "CMRY", "ROTI", "STTP", "MIDI",
    ],
    "Infrastruktur_Energi": [
        "TLKM", "EXCL", "ISAT", "TOWR", "TBIG", "PGAS", "PTBA", "ADRO",
        "ITMG", "MEDC", "AKRA", "ELSA", "PGEO", "BREN", "JSMR", "META",
    ],
    "Pertambangan": [
        "ANTM", "INCO", "TINS", "MDKA", "HRUM", "BUMI", "PTRO", "DOID",
        "MBMA", "NCKL", "AMMN",
    ],
    "Properti_Konstruksi": [
        "BSDE", "CTRA", "PWON", "SMRA", "ASRI", "PANI", "WIKA", "WSKT",
        "PTPP", "ADHI", "SMGR", "INTP", "MTLA", "APLN",
    ],
    "Otomotif_Industri": [
        "ASII", "AUTO", "SMSM", "GJTL", "IMAS", "BRAM", "UNTR", "GDST",
    ],
    "Keuangan_NonBank": [
        "BFIN", "ADMF", "MFIN", "TUGU", "PNIN", "ASDM", "PNLF",
    ],
    "Teknologi_Digital": [
        "GOTO", "BUKA", "EMTK", "MTDL", "DCII", "WIFI", "CYBR",
    ],
    "Ritel_Konsumsi": [
        "MAPA", "LPPF", "RALS", "ERAA", "CSAP", "HERO",
    ],
    "Kesehatan": [
        "MIKA", "SILO", "HEAL", "PRDA", "SAME",
    ],
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
