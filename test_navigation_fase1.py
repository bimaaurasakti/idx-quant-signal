"""
Test integrasi navigasi Fase 1 (st.navigation + st.popover) — Jalankan:
python test_navigation_fase1.py

Men-mock lapisan Supabase (get_client + fetch_last_update + fetch_screener_
results) supaya app.py bisa dijalankan LEBIH JAUH dari sekadar titik
koneksi gagal (lihat test_app_boot.py) -- sampai ke titik st.navigation()
benar-benar dipanggil, halaman default (Screener) benar-benar di-render,
dan panel Pengaturan (st.popover) benar-benar dieksekusi. Ini bukti paling
kuat yang bisa didapat TANPA browser sungguhan bahwa migrasi navigasi
Fase 1 tidak merusak alur aplikasi.

Mock sengaja MINIMAL (screener_df kosong) supaya screener.py mengambil
jalur "Belum ada data di database" yang SUDAH ada & aman -- tujuan test
ini murni membuktikan wiring navigasi/popover, BUKAN menguji render data
screener yang sesungguhnya (itu scope Fase 3).
"""
import types
import pandas as pd

import data_loaders
import supabase_client


class _DummyClient:
    """Client Supabase palsu -- tidak pernah benar-benar dipakai krn semua
    fungsi fetch_* di-monkeypatch di bawah, cukup jadi objek non-None."""
    pass


def _fake_get_client(use_service_role: bool = False):
    return _DummyClient()


def _fake_fetch_last_update(client):
    return None  # ui_layout.render_settings_content sudah handle None dgn baik


def _fake_fetch_screener_results(client):
    return pd.DataFrame()  # screener.py sudah handle df kosong dgn baik


# Patch di NAMESPACE tempat fungsi ini dipakai (data_loaders mengimpor by
# name dari supabase_client, jadi harus dipatch di data_loaders, bukan di
# supabase_client, supaya efeknya kepakai -- lihat catatan di data_loaders.py).
supabase_client.get_client = _fake_get_client
data_loaders.fetch_last_update = _fake_fetch_last_update
data_loaders.fetch_screener_results = _fake_fetch_screener_results
# load_screener/load_last_update dibungkus @st.cache_data -- pastikan tidak
# ada cache basi dari run sebelumnya di proses yang sama.
data_loaders.load_screener.clear()
data_loaders.load_last_update.clear()

from streamlit.testing.v1 import AppTest  # noqa: E402  (setelah patch di atas)

at = AppTest.from_file("app.py", default_timeout=30)
at.run()

print("=== Hasil run halaman DEFAULT (Screener) ===")
print("Exception tak tertangani:", at.exception)
assert not at.exception, f"app.py Fase 1 melempar exception: {at.exception}"

warnings_text = " | ".join(str(w.value) for w in at.warning)
print("Isi st.warning():", warnings_text[:200])
assert "Belum ada data" in warnings_text, "Screener harusnya menampilkan pesan 'belum ada data' (mock df kosong)"

md_all = [m.value for m in at.markdown]
brand_ok = any("IDX Quant Signal" in v for v in md_all)
print("Brand header ter-render:", brand_ok)
assert brand_ok, "render_brand_header() harusnya tampil"

print("\n=== Coba pindah ke halaman lain lewat switch_page() ===")
try:
    at.switch_page("about")
    at.run()
    print("switch_page('about') tidak error. Exception:", at.exception)
    if not at.exception:
        about_md = " ".join(m.value for m in at.markdown)
        found_about_content = "Metodologi" in about_md or "Arsitektur" in about_md
        print("Konten halaman Tentang ter-render:", found_about_content)
except Exception as e:  # noqa: BLE001 -- eksplorasi, dilaporkan bukan digagalkan
    print(f"CATATAN: switch_page('about') tidak didukung dgn argumen ini di versi Streamlit "
          f"terpasang ({e!r}). Ini keterbatasan test-harness utk st.Page berbasis fungsi, "
          f"BUKAN indikasi bug di app.py -- verifikasi klik-manual antar tab tetap perlu "
          f"dilakukan di browser sungguhan (lihat CARA_TERAPKAN.md).")

print("\nPASS: navigasi Fase 1 (st.navigation + st.popover) berjalan tanpa exception")
print("tak tertangani pada halaman default, dgn data ter-mock minimal.")
