-- ============================================================================
-- MIGRATION: Restrict ticker universe ke konstituen IDX30 & LQ45
-- ============================================================================
-- Bagian dari: IMPLEMENTATION_PLAN_IDX30_LQ45.md (restrukturisasi universe saham)
-- Dibuat: 27 Juli 2026
--
-- CARA JALANKAN:
--   Supabase Dashboard > SQL Editor > New query > paste SELURUH file ini > Run
--   (jalankan sebagai satu skrip utuh, bukan statement per statement, supaya
--   transaksi BEGIN...COMMIT di bawah bekerja sebagaimana mestinya)
--
-- URUTAN WAJIB (lihat IMPLEMENTATION_PLAN_IDX30_LQ45.md Fase 2-3):
--   1. Deploy dulu kode baru (tickers_idx.py, worker_fetch_and_update.py,
--      supabase_client.py yang sudah diupdate) ke repo/GitHub Actions.
--   2. Jalankan worker MINIMAL SEKALI (trigger manual lewat tab Actions di
--      GitHub -> workflow "Update Sinyal IDX Setelah Tutup Bursa" -> Run
--      workflow) supaya 45 ticker universe baru SUDAH punya baris
--      screener_results / price_history / backtest_trades yang FRESH.
--   3. BARU jalankan migration ini untuk bersih-bersih data ticker lama.
--
-- Kalau urutan dibalik (migration dulu baru worker), dashboard publik akan
-- sempat kosong / rankingnya tidak lengkap sampai worker run berikutnya.
--
-- APA YANG DIHAPUS vs TIDAK PERNAH DIHAPUS:
--   - screener_results / price_history / backtest_trades: dihapus utk ticker
--     yang (a) di luar universe baru DAN (b) tidak sedang punya posisi aktif
--     -- tabel-tabel ini murni "current state" yang di-recompute penuh tiap
--     worker run (lihat replace_price_history/replace_backtest_trades di
--     supabase_client.py), jadi 100% aman dihapus & akan terisi ulang normal
--     kalau ticker itu suatu saat masuk lagi ke universe.
--   - ongoing_positions dengan status CLOSED_* (CLOSED_TP/CLOSED_SL/
--     CLOSED_SIGNAL/CLOSED_TIME): TIDAK PERNAH DIHAPUS, apa pun universe-nya.
--     Ini live track record ("tidak pernah direvisi ke belakang" -- lihat
--     komentar fetch_closed_positions() di supabase_client.py) dan tetap
--     tampil di tab Portfolio meskipun tickernya sudah bukan bagian dari
--     universe default lagi.
--   - ongoing_positions dengan status PENDING_ENTRY/OPEN utk ticker di luar
--     universe baru: TIDAK DIHAPUS -- worker versi baru akan terus meng-
--     update-nya ("grandfathering", union dengan universe statis) sampai
--     posisi closed dengan sendirinya. Lihat perubahan worker_fetch_and_
--     update.py Langkah 1.3 di IMPLEMENTATION_PLAN.
-- ============================================================================

begin;

-- 1. Universe baru (LQ45 penuh, otomatis mencakup semua anggota IDX30).
--    HARUS SAMA PERSIS dengan flatten(IDX_TICKERS) di tickers_idx_NEW.py.
--    Kalau di Fase 0 Anda memverifikasi ulang & ternyata komposisinya sudah
--    berubah (BEI dijadwalkan rebalance akhir Juli/awal Agustus 2026 --
--    lihat catatan expiry di tickers_idx_NEW.py), UPDATE daftar di bawah ini
--    DULU supaya konsisten dengan tickers_idx.py yang benar-benar dideploy.
create temporary table _new_universe (ticker text primary key);
insert into _new_universe (ticker) values
    ('AADI'), ('ADMR'), ('ADRO'), ('AKRA'), ('AMMN'), ('AMRT'), ('ANTM'),
    ('ASII'), ('BBCA'), ('BBNI'), ('BBRI'), ('BBTN'), ('BMRI'), ('BRPT'),
    ('BUMI'), ('CPIN'), ('CUAN'), ('DEWA'), ('EMTK'), ('ESSA'), ('EXCL'),
    ('GOTO'), ('HRTA'), ('ICBP'), ('INCO'), ('INDF'), ('INKP'), ('ISAT'),
    ('ITMG'), ('JPFA'), ('KLBF'), ('MAPI'), ('MBMA'), ('MDKA'), ('MEDC'),
    ('PGAS'), ('PGEO'), ('PTBA'), ('SCMA'), ('SMGR'), ('TLKM'), ('TOWR'),
    ('UNTR'), ('UNVR'), ('WIFI');

-- 2. Ticker yang MASIH punya posisi aktif (PENDING_ENTRY/OPEN) -- ini
--    "grandfathered", tidak boleh ikut terhapus dari tabel current-state
--    walau di luar _new_universe (biar tabel Ongoing Position di app.py
--    tidak pecah / kolom sektor & harga jadi NaN akibat kehilangan baris
--    screener_results pasangannya).
create temporary table _grandfathered (ticker text primary key);
insert into _grandfathered (ticker)
    select distinct ticker from ongoing_positions
    where status in ('PENDING_ENTRY', 'OPEN');

-- 3. PREVIEW -- baca hasilnya sebelum lanjut ke DELETE. Ini SELECT biasa,
--    TIDAK menghapus apa pun; kalau daftarnya terlihat aneh (misal ticker
--    yang menurut Anda seharusnya masih aktif malah muncul di sini), STOP
--    dan cek ulang _new_universe / _grandfathered di atas dulu.
select ticker, 'akan dihapus dari screener_results/price_history/backtest_trades' as keterangan
from screener_results
where ticker not in (select ticker from _new_universe)
  and ticker not in (select ticker from _grandfathered)
order by ticker;

-- 4. Hapus data current-state utk ticker di luar universe baru & tanpa
--    posisi aktif.
delete from backtest_trades
where ticker not in (select ticker from _new_universe)
  and ticker not in (select ticker from _grandfathered);

delete from price_history
where ticker not in (select ticker from _new_universe)
  and ticker not in (select ticker from _grandfathered);

delete from screener_results
where ticker not in (select ticker from _new_universe)
  and ticker not in (select ticker from _grandfathered);

-- 5. TIDAK ADA delete terhadap ongoing_positions di sini -- lihat catatan
--    "APA YANG DIHAPUS vs TIDAK PERNAH DIHAPUS" di header file ini.

commit;

-- ============================================================================
-- 6. VERIFIKASI SETELAH COMMIT (temp table masih hidup sepanjang sesi ini,
--    karena dibuat tanpa "ON COMMIT DROP" -- aman dipakai lagi di bawah)
-- ============================================================================

-- Ekspektasi: <= 45 (ukuran universe baru) + jumlah ticker grandfathered yang
-- kebetulan di luar universe baru (biasanya 0, atau kecil sekali).
select count(*) as total_screener_rows_setelah_migrasi from screener_results;

-- Harus VALID (baris ini boleh muncul) HANYA kalau ticker tsb memang sedang
-- grandfathered (posisi aktif); kalau ada baris lain di luar itu, ada yang
-- tidak konsisten dan perlu diselidiki sebelum lanjut.
select op.ticker, op.status, op.planned_entry_date, op.entry_date
from ongoing_positions op
where op.status in ('PENDING_ENTRY', 'OPEN')
  and op.ticker not in (select ticker from _new_universe);

-- Sanity check tambahan: pastikan tidak ada baris screener_results yang
-- "yatim" (di luar universe baru DAN di luar grandfathered) yang lolos --
-- harusnya mengembalikan 0 baris.
select count(*) as harus_nol from screener_results
where ticker not in (select ticker from _new_universe)
  and ticker not in (select ticker from _grandfathered);

-- 7. Beres-beres temp table (opsional -- otomatis hilang saat sesi SQL
--    Editor ditutup, tapi baik utk kebersihan kalau mau lanjut query lain).
drop table if exists _new_universe;
drop table if exists _grandfathered;

-- ============================================================================
-- SELESAI. Lanjut ke Fase 4 (Verifikasi & QA) di IMPLEMENTATION_PLAN.md:
--   - Buka dashboard, cek tab Screener menampilkan maksimal 45 baris (+
--     grandfathered kalau ada).
--   - Cek tab Portfolio -- riwayat closed position historis (termasuk dari
--     ticker yang sudah di luar universe) HARUS TETAP UTUH, tidak berkurang.
--   - Cek filter sektor di sidebar -- opsinya sekarang harus 7 sektor baru
--     (Perbankan, Consumer_Goods, Energi_Komoditas, Telekomunikasi_
--     Infrastruktur, Pertambangan, Industri_Manufaktur, Teknologi_Digital),
--     bukan 10 sektor lama.
-- ============================================================================
