"""
shared_ui.py
============
Konstanta & helper UI yang dipakai lebih dari satu view module (Detail
Saham + Portfolio, dan nantinya Backtest Lab utk skema warna exit-reason
yang konsisten). Dipisah dari app.py supaya tidak ada duplikasi/drift
antar view saat isi tab lama dipecah ke views/*.py.

TIDAK ada perubahan nilai/logika dari versi app.py sebelumnya.
"""
from __future__ import annotations

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

# Skema warna exit reason -- dipakai di tabel detail & chart breakdown Portfolio,
# dan direuse Backtest Lab (Fase 5/6, lihat IMPLEMENTATION_PLAN §3.7) supaya
# konsisten visual di seluruh app.
EXIT_REASON_ROW_COLORS = {
    "Take Profit": "rgba(34, 197, 94, 0.18)",    # hijau
    "Stop Loss": "rgba(239, 68, 68, 0.18)",      # merah
    "Sinyal SELL": "rgba(59, 130, 246, 0.12)",   # biru netral
    "Batas Waktu": "rgba(234, 179, 8, 0.12)",    # amber netral
}
EXIT_REASON_CHART_COLORS = {
    "Take Profit": "#22c55e",
    "Stop Loss": "#ef4444",
    "Sinyal SELL": "#3b82f6",
    "Batas Waktu": "#eab308",
}


def style_exit_reason_row(row):
    """Styler.apply(..., axis=1) -- background-color per baris berdasar
    'Alasan Exit'. Warna cuma penanda visual tambahan (kolom teks Alasan
    Exit tetap ditampilkan apa adanya untuk aksesibilitas)."""
    color = EXIT_REASON_ROW_COLORS.get(row["Alasan Exit"], "")
    css = f"background-color: {color}" if color else ""
    return [css] * len(row)
