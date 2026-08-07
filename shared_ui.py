"""
shared_ui.py
============
Konstanta & helper UI yang dipakai lebih dari satu view module (Detail
Saham + Portfolio, dan nantinya Backtest Lab utk skema warna exit-reason
yang konsisten). Dipisah dari app.py supaya tidak ada duplikasi/drift
antar view saat isi tab lama dipecah ke views/*.py.

TIDAK ada perubahan nilai/logika dari versi app.py sebelumnya.

FASE 1 REDESIGN: EXIT_REASON_CHART_COLORS (warna hex solid, dipakai chart
Plotly) sekarang merujuk theme.COLORS alih-alih hex literal terpisah,
supaya warna exit-reason dan warna sinyal BUY/SELL/HOLD (baru, lihat
theme.signal_colors()) berasal dari SATU sumber kebenaran yang sama --
nilainya identik dengan sebelumnya ("Take Profit"=hijau, "Stop
Loss"=merah, "Sinyal SELL"=biru, "Batas Waktu"=kuning). EXIT_REASON_ROW_
COLORS (rgba dengan alpha, dipakai background baris tabel) TETAP literal
apa adanya -- alpha-nya (0.18/0.12) sengaja beda dari token badge _bg
milik theme.py (0.14), jadi tidak di-refactor ikut supaya nol perubahan
visual. Lihat IMPLEMENTATION_PLAN_UI_REDESIGN_STOCKBIT.md §9.1.
"""
from __future__ import annotations

from theme import COLORS as _COLORS

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
    # CATATAN: alpha di sini (0.18/0.12) SENGAJA beda dari theme.COLORS["*_bg"]
    # (0.14 seragam, dipakai badge kecil) -- background baris tabel penuh
    # butuh bobot visual berbeda dari badge kecil, jadi tetap literal rgba
    # persis nilai asli (bukan re-use token _bg) supaya nol perubahan visual
    # di tabel yang sudah ada (portfolio.py, dst).
    "Take Profit": "rgba(34, 197, 94, 0.18)",    # hijau, hue sama dgn theme.COLORS['bullish']
    "Stop Loss": "rgba(239, 68, 68, 0.18)",      # merah, hue sama dgn theme.COLORS['bearish']
    "Sinyal SELL": "rgba(59, 130, 246, 0.12)",   # biru netral, hue sama dgn theme.COLORS['info']
    "Batas Waktu": "rgba(234, 179, 8, 0.12)",    # amber netral, hue sama dgn theme.COLORS['neutral']
}
EXIT_REASON_CHART_COLORS = {
    "Take Profit": _COLORS["bullish"],   # == "#22c55e" spt sebelumnya (huruf besar/kecil hex sama nilainya)
    "Stop Loss": _COLORS["bearish"],     # == "#ef4444"
    "Sinyal SELL": _COLORS["info"],      # == "#3b82f6"
    "Batas Waktu": _COLORS["neutral"],   # == "#eab308"
}


def style_exit_reason_row(row):
    """Styler.apply(..., axis=1) -- background-color per baris berdasar
    'Alasan Exit'. Warna cuma penanda visual tambahan (kolom teks Alasan
    Exit tetap ditampilkan apa adanya untuk aksesibilitas)."""
    color = EXIT_REASON_ROW_COLORS.get(row["Alasan Exit"], "")
    css = f"background-color: {color}" if color else ""
    return [css] * len(row)
