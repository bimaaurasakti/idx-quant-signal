"""
Smoke test app.py memakai streamlit.testing.v1.AppTest (headless, tanpa
browser). Jalankan: python test_app_boot.py

Tidak butuh kredensial Supabase asli -- yang diverifikasi adalah app.py
(ui_layout.py + theme.py) bisa di-import & dijalankan Streamlit sampai
titik kegagalan koneksi yang SUDAH ditangani dengan baik oleh kode asli
(try/except -> st.error + st.stop(), lihat app.py::main()), BUKAN
exception mentah yang tidak tertangani. Ini membuktikan wiring
inject_css() -> theme.get_global_css() tidak merusak jalur boot aplikasi.
"""
from streamlit.testing.v1 import AppTest

at = AppTest.from_file("app.py", default_timeout=30)
at.run()

print("exception tertangkap AppTest:", at.exception)
print("jumlah elemen error (st.error):", len(at.error))
if at.error:
    for e in at.error:
        print("  - st.error value (potongan):", str(e.value)[:200].replace("\n", " "))

assert not at.exception, f"app.py melempar exception TAK TERTANGANI: {at.exception}"
assert len(at.error) >= 1, "Harusnya app berhenti di st.error('Koneksi ke Supabase belum berhasil...') karena tidak ada kredensial di lingkungan test ini"
assert any("Supabase" in str(e.value) for e in at.error), "Pesan error yang tampil bukan pesan koneksi Supabase yang diharapkan"

print("\nPASS: app.py + ui_layout.py (Fase 0) boot tanpa exception tak tertangani,")
print("      berhenti tepat di titik yang SAMA seperti sebelum redesign (tidak ada")
print("      kredensial Supabase di lingkungan test ini) -- perilaku tidak berubah.")
