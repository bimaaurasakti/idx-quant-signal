"""
Test manual untuk tickers_idx.py -- validasi struktur universe IDX30/LQ45
setelah restrukturisasi. Jalankan: python test_tickers_idx.py
Tidak butuh koneksi Supabase / yfinance sama sekali.
"""
from tickers_idx import IDX_TICKERS, IDX30_TICKERS, get_all_tickers, get_sector_of, is_idx30, is_lq45

print("=" * 70)
print("TEST 1: Tidak ada ticker duplikat lintas sektor")
print("=" * 70)
flat = []
for sektor, tickers in IDX_TICKERS.items():
    flat.extend(tickers)
dupes = [t for t in flat if flat.count(t) > 1]
assert len(flat) == len(set(flat)), f"Ada duplikat! {dupes}"
print(f"  PASS: {len(flat)} ticker, semua unik.\n")

print("=" * 70)
print("TEST 2: Semua ticker uppercase, tanpa suffix .JK, tanpa whitespace")
print("=" * 70)
for t in flat:
    assert t == t.upper(), f"{t} bukan uppercase"
    assert ".JK" not in t, f"{t} tidak boleh ada suffix .JK di IDX_TICKERS"
    assert t == t.strip(), f"{t} ada whitespace"
print("  PASS: semua ticker format-nya benar.\n")

print("=" * 70)
print("TEST 3: Tidak ada sektor kosong")
print("=" * 70)
for sektor, tickers in IDX_TICKERS.items():
    assert len(tickers) > 0, f"Sektor {sektor} kosong -- harus dihapus dari dict"
print(f"  PASS: {len(IDX_TICKERS)} sektor, semua terisi.\n")

print("=" * 70)
print("TEST 4: IDX30_TICKERS harus subset dari IDX_TICKERS, tepat 30 ticker")
print("=" * 70)
missing = IDX30_TICKERS - set(flat)
assert not missing, f"Ticker IDX30 ini tidak ada di IDX_TICKERS: {missing}"
assert len(IDX30_TICKERS) == 30, f"IDX30 harus 30 ticker, ada {len(IDX30_TICKERS)}"
print(f"  PASS: {len(IDX30_TICKERS)} ticker IDX30, semua ada di IDX_TICKERS.\n")

print("=" * 70)
print("TEST 5: Total universe harus 45 ticker (ukuran resmi LQ45)")
print("=" * 70)
assert len(flat) == 45, f"Universe harus 45 ticker (LQ45), ada {len(flat)}"
print("  PASS: 45 ticker persis.\n")

print("=" * 70)
print("TEST 6: get_sector_of() konsisten utk tiap ticker & variasi input")
print("=" * 70)
for sektor, tickers in IDX_TICKERS.items():
    for t in tickers:
        got = get_sector_of(t)
        assert got == sektor, f"get_sector_of('{t}') = '{got}', harusnya '{sektor}'"
        assert get_sector_of(t.lower()) == sektor
        assert get_sector_of(f"{t}.JK") == sektor
print("  PASS: get_sector_of() konsisten untuk semua ticker & variasi input.\n")

print("=" * 70)
print("TEST 7: get_sector_of() ticker asing/tidak dikenal -> 'Lainnya'")
print("=" * 70)
assert get_sector_of("ZZZZ") == "Lainnya"
print("  PASS.\n")

print("=" * 70)
print("TEST 8: is_idx30() & is_lq45() konsisten dengan definisi set-nya")
print("=" * 70)
for t in flat:
    assert is_idx30(t) == (t in IDX30_TICKERS), f"is_idx30('{t}') salah"
    assert is_idx30(f"{t}.JK") == (t in IDX30_TICKERS)
    assert is_lq45(t) is True, f"is_lq45('{t}') harus True utk semua ticker di universe"
assert is_idx30("ZZZZ") is False
assert is_lq45("ZZZZ") is False
print("  PASS.\n")

print("=" * 70)
print("TEST 9: get_all_tickers() -- jumlah & format suffix")
print("=" * 70)
with_suffix = get_all_tickers(with_suffix=True)
without_suffix = get_all_tickers(with_suffix=False)
assert len(with_suffix) == len(without_suffix)
assert len(with_suffix) >= len(flat), (
    "get_all_tickers() harus minimal mencakup semua entri IDX_TICKERS "
    "(bisa lebih banyak kalau ada custom_tickers.txt aktif di direktori ini)"
)
assert all(t.endswith(".JK") for t in with_suffix)
assert all(not t.endswith(".JK") for t in without_suffix)
print(f"  PASS: {len(with_suffix)} ticker (with_suffix=True), format benar.\n")

print("=" * 70)
print(f"SEMUA TEST tickers_idx.py PASS -- universe = {len(flat)} ticker "
      f"({len(IDX30_TICKERS)} di antaranya anggota IDX30), {len(IDX_TICKERS)} sektor")
print("=" * 70)
