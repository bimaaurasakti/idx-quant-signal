"""
Kalender hari bursa IDX (BEI) — dipakai untuk:
  1. Skip proses update otomatis di hari libur/weekend (worker tidak perlu jalan
     kalau bursa tutup).
  2. Menghitung "hari bursa berikutnya" untuk label "Sinyal BUY Besok (tanggal)".

PENTING — kalender ini perlu di-update TIAP TAHUN:
BEI merilis kalender libur bursa resmi tiap tahun, biasanya sekitar
September tahun sebelumnya. Data 2026 di bawah diambil dari pengumuman
resmi BEI No. Peng-00171/BEI.POP/09-2025 (23 September 2025). Ini BUKAN
cuma daftar libur nasional — termasuk cuti bersama yang ditetapkan ikut
meliburkan perdagangan bursa.

Kalau tahun berjalan belum ada di IDX_HOLIDAYS, fungsi is_holiday() akan
fallback ke "tidak libur" (konservatif) — artinya next_trading_day() bisa
sedikit meleset di sekitar hari libur nasional/keagamaan tahun tersebut
sampai kalendernya di-update manual di file ini.

Sumber: idx.co.id — Pengumuman Kalender Libur Bursa Tahun 2026
"""
from __future__ import annotations
from datetime import date, timedelta

IDX_HOLIDAYS: dict[int, set[date]] = {
    2026: {
        date(2026, 1, 1),    # Tahun Baru 2026 Masehi
        date(2026, 1, 16),   # Isra Mi'raj Nabi Muhammad SAW
        date(2026, 2, 16),   # Cuti Bersama Tahun Baru Imlek 2577
        date(2026, 2, 17),   # Tahun Baru Imlek 2577 Kongzili
        date(2026, 3, 18),   # Cuti Bersama Hari Suci Nyepi
        date(2026, 3, 19),   # Nyepi Tahun Baru Saka 1948
        date(2026, 3, 20),   # Cuti Bersama Idulfitri 1447 H
        date(2026, 3, 23),   # Cuti Bersama Idulfitri 1447 H
        date(2026, 3, 24),   # Cuti Bersama Idulfitri 1447 H
        date(2026, 4, 3),    # Wafat Yesus Kristus
        date(2026, 5, 1),    # Hari Buruh Internasional
        date(2026, 5, 14),   # Kenaikan Yesus Kristus
        date(2026, 5, 15),   # Cuti Bersama Kenaikan Yesus Kristus
        date(2026, 5, 27),   # Iduladha 1447 H
        date(2026, 5, 28),   # Cuti Bersama Iduladha 1447 H
        date(2026, 6, 1),    # Hari Lahir Pancasila
        date(2026, 6, 16),   # Tahun Baru Islam 1448 H (1 Muharram)
        date(2026, 8, 17),   # Proklamasi Kemerdekaan RI
        date(2026, 8, 25),   # Maulid Nabi Muhammad SAW
        date(2026, 12, 24),  # Cuti Bersama Natal
        date(2026, 12, 25),  # Natal
        date(2026, 12, 31),  # Libur Bursa Akhir Tahun
    },
    # 2027: { ... }  <- tambahkan di sini setelah BEI merilis kalendernya
}


def is_holiday(d: date) -> bool:
    return d in IDX_HOLIDAYS.get(d.year, set())


def is_trading_day(d: date) -> bool:
    """False kalau Sabtu/Minggu atau hari libur bursa."""
    if d.weekday() >= 5:  # Sabtu=5, Minggu=6
        return False
    return not is_holiday(d)


def next_trading_day(from_date: date) -> date:
    """Hari bursa berikutnya SETELAH from_date (tidak termasuk from_date itu sendiri)."""
    d = from_date + timedelta(days=1)
    while not is_trading_day(d):
        d += timedelta(days=1)
    return d


def previous_trading_day(from_date: date) -> date:
    """Hari bursa sebelum from_date (tidak termasuk from_date itu sendiri)."""
    d = from_date - timedelta(days=1)
    while not is_trading_day(d):
        d -= timedelta(days=1)
    return d
