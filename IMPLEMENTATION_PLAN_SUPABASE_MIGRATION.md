# IMPLEMENTATION PLAN — Migrasi Frontend ke Akses Supabase Langsung

**Project:** IDX Quant Signal — Frontend
**Dibuat untuk:** eksekusi oleh Claude Sonnet 5 (Claude Code / agentic session)
**Dibuat:** 14 Agustus 2026
**Status sumber:** disusun dari seluruh isi repo frontend (kecuali folder `components/`) + `schema.sql`

## Status Implementasi Terkini

| Fase | Status | Catatan |
|---|---|---|
| Fase 0 — Fondasi | ✅ Selesai | `lib/supabase/client.ts`, `database.types.ts` sudah dibuat & type-check bersih |
| Fase 1 — Migrasi Baca Data | ✅ Selesai | `screener()`, `tickerDetail()`, `portfolio()`, `metaTickers()`, `metaLastUpdate()` sudah baca langsung dari Supabase, terverifikasi `tsc --noEmit` bersih (lihat temuan penting di §9.2) |
| Fase 2 — Engine Backtest | ⏸️ **Sengaja ditunda** | Butuh source code backend (indicators.py/signals.py/backtester.py) untuk verifikasi formula. `metaIndicators()` & `runBacktest()` sekarang melempar `ApiError` yang jelas; `app/backtest/page.tsx` menampilkan status "belum tersedia" alih-alih memanggil backend yang sudah tidak ada |
| Fase 3 — Pembersihan | ✅ Sebagian besar selesai | `NEXT_PUBLIC_API_BASE_URL` sudah dihapus total, `README.md` & `app/about/page.tsx` sudah diperbarui. Sisa: dekomisioning FastAPI di infrastruktur (di luar scope kode) |

Dengan status di atas, **seluruh frontend berjalan 100% dari Supabase tanpa backend API terpisah**, kecuali Backtest Lab yang sengaja dinonaktifkan sampai Fase 2 dikerjakan.

---

## Cara Memakai Dokumen Ini

Dokumen ini dipecah jadi **5 fase berurutan** (Fase 0–4). Setiap fase punya *acceptance criteria* sendiri dan bisa di-deploy independen. Jalankan satu fase per sesi Claude Code, verifikasi di browser sungguhan (bukan cuma `npm run build` lulus), baru lanjut ke fase berikutnya — terutama sebelum masuk **Fase 2 (Backtest Engine)**, yang paling berisiko.

Jangan mulai Fase 2 tanpa membaca **§8 Gap Analysis** dan **§13 Risk Register** — ada beberapa formula yang saya **tidak** bisa verifikasi dari file yang tersedia (source code backend Python tidak ikut di-share), dan saya tandai eksplisit di mana saja itu.

---

## Daftar Isi

0. [Ringkasan Eksekutif](#0-ringkasan-eksekutif)
1. [Ruang Lingkup](#1-ruang-lingkup)
2. [Prinsip Desain](#2-prinsip-desain)
3. [Arsitektur: Sebelum → Sesudah](#3-arsitektur-sebelum--sesudah)
4. [Audit Kode Saat Ini](#4-audit-kode-saat-ini)
5. [Pemetaan Data: `api.ts` → `schema.sql`](#5-pemetaan-data-apits--schemasql)
6. [Gap Analysis — Logic yang Perlu Di-porting](#6-gap-analysis--logic-yang-perlu-di-porting)
7. [Struktur File](#7-struktur-file)
8. [Rencana Fase](#8-rencana-fase)
9. [Spesifikasi Teknis](#9-spesifikasi-teknis)
10. [Environment Variables](#10-environment-variables)
11. [Keamanan & RLS Checklist](#11-keamanan--rls-checklist)
12. [Testing & Validasi](#12-testing--validasi)
13. [Risk Register / Pertanyaan Terbuka](#13-risk-register--pertanyaan-terbuka)
14. [Pertimbangan UX](#14-pertimbangan-ux)
15. [Rollout & Rollback](#15-rollout--rollback)
16. [Definition of Done](#16-definition-of-done)

---

## 0. Ringkasan Eksekutif

Saat ini frontend punya arsitektur 3-lapis: **Next.js → FastAPI → Supabase**. Semua fetch data lewat satu titik (`lib/api.ts`), yang memanggil FastAPI lewat `NEXT_PUBLIC_API_BASE_URL`.

**Target:** hilangkan lapisan FastAPI untuk kebutuhan *baca* frontend. Next.js memanggil Supabase langsung via `@supabase/supabase-js` (PostgREST + `anon` key, dilindungi RLS yang sudah *public-read-only* di `schema.sql`).

Ini **bukan** migrasi yang seragam — ada dua jenis kebutuhan data yang sangat berbeda sifatnya:

| Jenis | Contoh | Pendekatan |
|---|---|---|
| **Query murni** (SELECT langsung / gabungan sederhana) | Screener, Detail, Portfolio, Meta | Ganti `fetch()` dengan `supabase.from(...).select(...)` — risiko rendah |
| **Komputasi** (bukan cuma baca, tapi *menghitung*) | Backtest Lab | Perlu **porting engine backtest dari Python ke TypeScript**, dijalankan di browser — risiko & effort tinggi, jadi fase terpisah |

**Rekomendasi arsitektur untuk Backtest Lab:** jalankan engine di **client-side (browser)**, bukan Supabase Edge Function. Alasannya:
1. Pola ini sudah ada presedennya di codebase — `lib/portfolio-metrics.ts` sudah melakukan hal serupa ("*dataset closed positions cukup kecil untuk ini aman dilakukan di client*").
2. Dataset per-request kecil (1 ticker × maks 5 tahun harian ≈ 1.250 bar) — komputasi ini ringan untuk JS, tidak butuh server.
3. Paling literal memenuhi permintaan "tidak tergantung backend API lagi" — nol round-trip server sama sekali untuk fitur ini.
4. Skalabilitas "gratis": setiap pengguna menghitung di device masing-masing, tidak ada beban server bersama yang bertambah seiring jumlah pengguna.

Alternatif (Supabase Edge Function) tetap saya dokumentasikan di §9.4 sebagai *escape hatch* kalau nanti ada masalah performa di device rendah atau alasan menyembunyikan formula.

**Implikasi infrastruktur:** kalau FastAPI backend **hanya** melayani frontend ini (tidak dipakai konsumen lain), setelah migrasi selesai backend itu berpotensi **didekomisioning sepenuhnya** — worker (`worker_fetch_and_update.py`, cron GitHub Actions) menulis ke Supabase langsung via `service_role` key, jadi tidak bergantung pada FastAPI. Verifikasi ini di repo backend sebelum benar-benar mematikan servicenya.

---

## 1. Ruang Lingkup

**Termasuk:**
- Seluruh isi `lib/api.ts` dan konsumsi datanya (hooks, halaman di `app/`)
- Katalog indikator & engine backtest (porting logic)
- Update dokumentasi yang menyebut arsitektur lama (`README.md`, halaman `/about`)
- Environment variables

**Tidak termasuk (di luar akses saya ke source code-nya):**
- `worker_fetch_and_update.py` — tetap menulis ke Supabase via `service_role` key, **tidak berubah**
- Kode FastAPI itu sendiri — keputusan dekomisioning adalah tindak lanjut terpisah
- Provisioning project Supabase / penulisan ulang RLS policy — `schema.sql` yang di-share sudah benar (public read-only), tidak perlu diubah untuk migrasi ini
- Autentikasi pengguna — dashboard ini sepenuhnya publik/anonim, tidak ada login

---

## 2. Prinsip Desain

1. **`lib/types.ts` adalah kontrak yang stabil.** Setiap hook (`hooks/use-*.ts`) dan seluruh isi `components/` (yang tidak di-share ke saya) **harus tetap berfungsi tanpa modifikasi**, selama `lib/api.ts` terus mengembalikan data dengan bentuk (shape) yang identik ke tipe yang sudah ada. Ini prinsip paling penting di seluruh rencana ini — didesain supaya migrasi tidak menyentuh folder yang tidak bisa saya verifikasi.
2. **`lib/api.ts` tetap satu-satunya titik akses data**, mengikuti filosofi yang sudah tertulis di file itu sendiri ("*SATU-SATUNYA titik komunikasi frontend ke luar*") — hanya *implementasinya* yang berubah, dari `fetch()` ke Supabase client.
3. **Mulai dari yang murni-query, baru masuk ke yang komputasi.** Fase 1 (risiko rendah) sebelum Fase 2 (risiko tinggi).
4. **Jangan migrasi skema database di awal.** Karena skala data kecil (~45 ticker IDX30/LQ45), pendekatan "2 query paralel + gabung di client" sudah cukup cepat — tidak perlu menambah foreign key atau database view di iterasi pertama. Ini mengurangi risiko (tidak perlu migration SQL yang bisa mengganggu `worker_fetch_and_update.py`).
5. **Setiap fase harus bisa diverifikasi & di-deploy independen** (rollout bertahap, bukan big-bang).

---

## 3. Arsitektur: Sebelum → Sesudah

**SEBELUM** (sesuai diagram yang sudah ada di `app/about/page.tsx`):

```text
GitHub Actions (cron, ~16:30 WIB tiap hari bursa)
        |
        v
worker_fetch_and_update.py  ->  fetch yfinance, hitung sinyal + backtest
        |
        v
   Supabase (database bersama)
        |
        v
FastAPI backend  ->  SATU-SATUNYA klien Supabase, tidak pernah dihitung ulang
        |
        v
Next.js frontend (dashboard ini)  ->  HANYA memanggil FastAPI lewat REST/JSON
```

**SESUDAH** (target):

```text
GitHub Actions (cron, ~16:30 WIB tiap hari bursa)
        |
        v
worker_fetch_and_update.py  ->  fetch yfinance, hitung sinyal + backtest   [TIDAK BERUBAH]
        |
        v   (tulis via service_role key, bypass RLS — tidak berubah)
   Supabase (Postgres + PostgREST, RLS public-read di 5 tabel)
        |
        v   (baca via anon key dari browser; RLS memastikan hanya SELECT yang diizinkan)
Next.js frontend (dashboard ini)  ->  @supabase/supabase-js langsung
        |
        v   (khusus Backtest Lab)
Engine backtest TypeScript  ->  jalan di browser pengguna, input: price_history
```

FastAPI hilang total dari jalur baca. `worker_fetch_and_update.py` dan `service_role` key tetap seperti sekarang — keduanya tidak disentuh rencana ini.

---

## 4. Audit Kode Saat Ini

Poin-poin kunci yang jadi dasar rencana ini:

- **`lib/api.ts`** adalah satu-satunya tempat `fetch()` dipanggil. Komentarnya eksplisit: *"Frontend TIDAK PERNAH mengimpor @supabase/* atau menyimpan kredensial Supabase apa pun"* — baris ini yang akan dibalik oleh migrasi ini, jadi wajib diperbarui (lihat §8, Fase 3).
- **5 file hook** (`use-screener`, `use-detail`, `use-portfolio`, `use-backtest`, `use-meta`) semuanya hanya memanggil `api.xxx()` lewat TanStack Query — **tidak ada hook yang perlu diubah** selama `lib/api.ts` mempertahankan signature & return type-nya.
- **`app/risk/page.tsx`** sudah 100% independen dari API — murni kalkulator client-side dari input pengguna. **Tidak perlu perubahan.**
- **`lib/portfolio-metrics.ts`** sudah membuktikan pola "port formula Python ke TypeScript, hitung di client" untuk metrik portfolio (winrate, expectancy, profit factor) — docblock-nya bahkan menyebut nama file sumber di backend: `backtester.py::_compute_metrics` / `portfolio.py::_portfolio_metrics`. Ini petunjuk berharga untuk Fase 2.
- **`app/about/page.tsx`** ternyata berisi dokumentasi informal yang sangat berguna untuk migrasi ini — ada penjelasan tertulis soal:
  - Formula sinyal produksi: *"BUY/SELL hanya muncul kalau minimal 2 dari 3 kondisi searah — Trend (harga > SMA50 > SMA200), Momentum (MACD cross + RSI di zona sehat), Volume (≥20% di atas rata-rata 20 hari)"*
  - State machine posisi: PENDING_ENTRY → OPEN (entry di harga Open hari bursa berikutnya, TP = entry + 2×ATR, SL = entry − 1×ATR) → CLOSED_*
  
  Ini **bukan** spesifikasi API asli Backtest Lab (yang punya katalog indikator lebih luas & parameter *adjustable*), tapi memberi baseline formula produksi yang harus konsisten dengan hasil default engine backtest baru.
- **`package.json`** belum punya `@supabase/supabase-js`.
- **`schema.sql`**: 5 tabel, semua RLS *enabled* dengan policy `for select using (true)` untuk publik, **tidak ada** policy insert/update/delete untuk role `anon` — artinya expose `anon` key ke browser **aman** (ini memang cara Supabase dirancang dipakai).
- **Tidak ada foreign key** antar tabel (`ticker` cuma kolom `text` biasa yang berulang di beberapa tabel, bukan `references`). Konsekuensinya: fitur *auto-embedding* PostgREST (`select('*, other_table(*)')`) **tidak otomatis jalan** tanpa FK. Solusi: 2 query paralel + gabung di JS (lihat Prinsip #4).

---

## 5. Pemetaan Data: `api.ts` → `schema.sql`

| Fungsi `api.*` saat ini | Tipe balik (`types.ts`) | Sumber tabel Supabase | Cukup query langsung? |
|---|---|---|---|
| `screener()` | `ScreenerResponse` | `screener_results` (semua baris) + `ongoing_positions` (status `PENDING_ENTRY` & `OPEN`) + `update_log` (baris terakhir) | ✅ — 3–4 query paralel + gabung di JS |
| `tickerDetail(ticker)` | `TickerDetailResponse` | `screener_results` (1 baris) + `price_history` (semua baris ticker itu) + `ongoing_positions` (0–1 baris aktif) + `backtest_trades` (semua baris ticker itu) | ✅ — 4 query paralel |
| `portfolio()` | `PortfolioResponse` | `ongoing_positions` (status `CLOSED_%`) + `screener_results` (untuk `sektor`) | ✅ — 2 query + gabung |
| `metaTickers()` | `TickersMetaResponse` | `screener_results` (`ticker`, `sektor`, `is_idx30`) | ✅ — 1 query, group-by di JS |
| `metaLastUpdate()` | `LastUpdateResponse` | `update_log` (baris terakhir, `order by run_at desc limit 1`) | ✅ — 1 query |
| `metaIndicators()` | `IndicatorsMetaResponse` | **Tidak ada tabel** | ❌ — jadi konstanta statis di frontend (lihat §6) |
| `runBacktest(body)` | `BacktestRunResponse` | `price_history` (input mentah saja) | ❌ — perlu *compute engine* (lihat §6 & §9.4) |

---

## 6. Gap Analysis — Logic yang Perlu Di-porting

Bagian ini daftar semua tempat di mana migrasi **bukan sekadar** "ganti fetch jadi query", tapi butuh logic baru:

### 6.1 Field turunan (derived) — effort kecil, tapi wajib benar

| Field | Dipakai di | Cara hitung yang direkomendasikan |
|---|---|---|
| `change`, `change_pct` | `TickerDetailResponse` | Ambil 2 baris terakhir `price_history` (ordered by date) untuk ticker itu → `close[n] - close[n-1]` dan persentasenya. **Tidak tersimpan di DB.** |
| `return_pct_now` | `OpenPositionRow` | `(last_close - entry_price) / entry_price * 100`, dari `ongoing_positions.entry_price` + `screener_results.last_close`. |
| `hold_days` (posisi OPEN/CLOSED di `ongoing_positions`) | `OpenPositionRow`, `ClosedPosition` | **Tidak ada kolom `hold_days` di tabel `ongoing_positions`** (beda dengan `backtest_trades` yang sudah punya kolom ini). Dua pendekatan, pilih sesuai konteks: <br>**(a) Cepat/aproksimasi** — hitung hari kerja (Senin–Jumat) antara `entry_date` dan `exit_date`/`last_date`. Murah (pure JS date math), tidak butuh query tambahan, tapi tidak memperhitungkan libur nasional/bursa Indonesia. Cocok untuk tabel/list (Portfolio, Screener) di mana fetch `price_history` penuh per baris terlalu mahal.<br>**(b) Presisi** — hitung jumlah *bar* di `price_history` ticker tsb di antara dua tanggal itu (karena `price_history` cuma berisi hari bursa asli, tidak perlu kalender libur terpisah). Hanya lakukan ini kalau `price_history` ticker itu **sudah** ter-fetch di context yang sama (mis. halaman Detail) — jangan fetch khusus untuk ini di halaman list. |
| `total_return_pct` | `DetailMetrics` | `SUM(return_pct)` dari `backtest_trades` ticker itu. Karena baris `backtest_trades` **sudah** di-fetch untuk menampilkan tabel `trades`, hitung sum-nya di client dari array yang sama (tidak perlu query agregat terpisah). |

### 6.2 Katalog indikator (`metaIndicators`) — effort sedang

Tidak ada tabelnya di `schema.sql`. Karena katalog ini jarang berubah (daftar indikator yang didukung engine), rekomendasi: jadikan **konstanta statis** di `lib/backtest-engine/indicators-catalog.ts`.

⚠️ **PENTING:** saya **tidak** punya akses ke source code backend (`indicators.py`/`signals.py` — nama file ini saya simpulkan dari komentar di `detail-client.tsx`: *"Performa strategi produksi (multi-confirmation, signals.py)"*). Isi katalog yang benar — daftar lengkap indikator per kategori (Trend/Momentum/Volatilitas/Volume), Tier 1 vs 2, `params` (default/min/max tiap indikator), dan `max_indicators_selected` — **harus diambil dari repo backend**, bukan ditebak. §9.5 memberi kerangka/contoh yang jelas ditandai sebagai *placeholder*.

### 6.3 Engine backtest (`runBacktest`) — effort besar, paling berisiko

Ini satu-satunya bagian yang benar-benar butuh *porting algoritma*, bukan query. Rincian breakdown ada di §9.4. Empat formula yang perlu diverifikasi presisi terhadap backend (bukan hanya "kelihatan benar"):

1. Formula tiap indikator teknikal (SMA, RSI, MACD, ATR, dll — tergantung katalog asli)
2. Logic *multi-confirmation signal* yang digeneralisasi untuk N indikator + `confirmation_threshold`
3. Simulasi trade (entry/exit/TP/SL/time-exit) — draft awal formulanya **ada** di `app/about/page.tsx` (lihat §4), tapi versi Backtest Lab men-generalisasi `tp_multiple`/`sl_multiple`/`max_hold_days` jadi parameter, bukan konstanta 2×/1×/20-hari
4. `max_drawdown_pct` dan `sharpe_rough` — winrate/expectancy/profit_factor sudah ada presisi formulanya di `lib/portfolio-metrics.ts` (bisa dipakai ulang/diadaptasi langsung), tapi drawdown & Sharpe **belum ada** portingan-nya di frontend manapun. Sumber otoritatif kemungkinan besar `backtester.py::_compute_metrics` (disebut eksplisit di docblock `portfolio-metrics.ts`).

---

## 7. Struktur File

```text
lib/
  api.ts                        [DIUBAH TOTAL — internal saja, export shape sama]
  types.ts                      [TIDAK BERUBAH — tetap jadi kontrak]
  format.ts                     [tidak berubah]
  constants.ts                  [tidak berubah]
  portfolio-metrics.ts          [tidak berubah — dipakai ulang formulanya di backtest-engine/metrics.ts]
  utils.ts                      [tidak berubah]
  derive.ts                     [BARU — computeHoldDays, computeReturnPctNow, computeChangeAndChangePct, sum()]

  supabase/
    client.ts                   [BARU — singleton Supabase client]
    database.types.ts           [BARU — tipe mentah tabel, idealnya di-generate via Supabase CLI]
    mappers.ts                  [BARU — raw row -> types.ts interfaces]

  backtest-engine/
    indicators.ts                [BARU — sma, ema, rsi, macd, atr, dst]
    indicators-catalog.ts        [BARU — pengganti metaIndicators(), PERLU VERIFIKASI backend]
    signals.ts                   [BARU — multi-confirmation, generalized]
    simulate-trades.ts           [BARU — state machine entry/TP/SL/time-exit]
    metrics.ts                   [BARU — winrate/expectancy/profit_factor (reuse pola portfolio-metrics) + drawdown/sharpe (baru)]
    run-backtest.ts               [BARU — orchestrator, hasil = BacktestRunResponse]

hooks/
  use-screener.ts               [TIDAK BERUBAH]
  use-detail.ts                 [TIDAK BERUBAH]
  use-portfolio.ts              [TIDAK BERUBAH]
  use-meta.ts                   [TIDAK BERUBAH]
  use-backtest.ts               [TIDAK BERUBAH]

app/
  about/page.tsx                [DIUBAH — teks & diagram arsitektur]

package.json                    [+ @supabase/supabase-js]
.env.local.example              [DIUBAH — variable baru + komentar]
.env.local                      [DIUBAH — variable baru + komentar]
README.md                       [DIUBAH — arsitektur, cara jalan]
```

**Yang TIDAK disentuh sama sekali (dan seharusnya tidak perlu):** seluruh `components/` (tidak ikut di-share, tapi menurut README "SATU-SATUNYA titik fetch ke backend" adalah `lib/api.ts`, jadi komponen seharusnya hanya konsumsi lewat hooks), `app/risk/page.tsx`, `app/layout.tsx`, `app/globals.css`, `next.config.ts`, `tsconfig.json`, `eslint.config.mjs`.

---

## 8. Rencana Fase

### Fase 0 — Fondasi

**Tugas:**
1. `npm install @supabase/supabase-js` di `package.json` (biarkan npm resolve versi terbaru, jangan hardcode versi lama).
2. Buat project Supabase (kalau belum ada instance terpisah untuk frontend) atau pastikan sudah tahu `Project URL` + `anon public key` dari project yang sama dipakai `worker_fetch_and_update.py`.
3. Buat `lib/supabase/client.ts` (lihat §9.1).
4. Generate tipe database: jalankan `supabase gen types typescript` (Supabase CLI) mengarah ke project/schema yang sesuai `schema.sql`, simpan sebagai `lib/supabase/database.types.ts`. Kalau CLI tidak tersedia di environment eksekusi, tulis manual mengikuti pola di §9.1 (cukup 5 tabel, tidak kompleks).
5. **Verifikasi asumsi arsitektur:** grep seluruh repo untuk `fetch(`, `NEXT_PUBLIC_API_BASE_URL`, dan `ApiError` di luar `lib/api.ts` — pastikan tidak ada komponen yang fetch langsung (README mengklaim `api.ts` adalah satu-satunya titik, tapi karena `components/` tidak ikut di-review, ini wajib diverifikasi, bukan diasumsikan).

**Acceptance criteria:** `npm run build` tetap lulus (belum ada perubahan fungsional), Supabase client bisa `console.log` hasil query sederhana (mis. `select('*').from('update_log').limit(1)`) tanpa error.

---

### Fase 1 — Migrasi Baca Data

Cakupan: `screener()`, `tickerDetail()`, `portfolio()`, `metaTickers()`, `metaLastUpdate()`. **`metaIndicators()` dan `runBacktest()` TETAP memanggil FastAPI lama di fase ini** (migrasi parsial disengaja — supaya value langsung kelihatan tanpa menunggu Fase 2 yang jauh lebih besar).

**Tugas:**
1. Tulis `lib/derive.ts` (lihat §9.3).
2. Tulis `lib/supabase/mappers.ts` (raw row → `types.ts` interfaces).
3. Rewrite `lib/api.ts`: ganti isi `screener`, `tickerDetail`, `portfolio`, `metaTickers`, `metaLastUpdate` — **signature & return type harus identik** dengan sebelumnya. `metaIndicators` dan `runBacktest` untuk sementara **tetap** pakai implementasi `fetch()` lama (biarkan `API_BASE_URL` masih dipakai untuk 2 fungsi ini saja).
4. Uji manual tiap halaman yang terpengaruh: `/screener`, `/detail/[ticker]` (coba beberapa ticker termasuk yang punya posisi OPEN dan yang tidak punya posisi sama sekali), `/portfolio` (termasuk kasus 0 posisi closed, dan kasus filter sektor/tanggal/ticker), `/detail` (index picker).
5. Bandingkan angka yang tampil dengan versi FastAPI lama (screenshot atau devtools network tab) untuk beberapa sample ticker — pastikan match persis (winrate, expectancy, profit factor terutama, karena ini angka yang kalau salah bisa menyesatkan keputusan trading).

**Acceptance criteria:**
- Kelima fungsi di atas tidak lagi memanggil `NEXT_PUBLIC_API_BASE_URL`.
- Semua state (`isLoading`, `isError`, `EmptyState`) masih berfungsi seperti sebelumnya — tidak ada regresi UX.
- Data yang tampil identik dengan versi lama untuk minimal 5 ticker sample + halaman Portfolio.
- Zero perubahan di `hooks/*.ts` dan `components/*`.

---

### Fase 2 — Porting Engine Backtest

Bagian terbesar & paling berisiko. Baca §6.3, §9.4, dan §13 dulu sebelum mulai.

**Tugas:**
1. **Ambil katalog indikator asli dari backend** (`indicators.py`/`signals.py` atau nama file setara) — kalau repo backend tidak tersedia di sesi ini, buat `indicators-catalog.ts` dengan struktur benar tapi isi ditandai `// TODO: verifikasi terhadap backend` per entry, dan **jangan** treat sebagai final.
2. Implementasi `lib/backtest-engine/indicators.ts` — satu fungsi murni per indikator, input `number[]` (atau `Bar[]` untuk yang butuh OHLC seperti ATR), output `(number | null)[]` sepanjang input (null untuk periode warm-up di awal).
3. Implementasi `lib/backtest-engine/signals.ts` — generalisasi dari deskripsi 3-faktor di `about/page.tsx` (Trend/Momentum/Volume) menjadi N-indikator + `confirmation_threshold` yang bisa dipilih user.
4. Implementasi `lib/backtest-engine/simulate-trades.ts` — state machine: `PENDING_ENTRY` di hari sinyal muncul → entry di `open` hari bursa berikutnya → exit di TP (`entry + tp_multiple × ATR`), SL (`entry − sl_multiple × ATR`), sinyal berlawanan, atau `max_hold_days` — urutan prioritas exit per hari **harus** diverifikasi terhadap backend (mis. kalau TP dan SL sama-sama tersentuh di hari yang sama, mana yang menang?).
5. Implementasi `lib/backtest-engine/metrics.ts` — reuse formula winrate/expectancy/profit_factor dari `portfolio-metrics.ts` (sudah terbukti benar), tambah `max_drawdown_pct` (dari `equity_curve`) dan `sharpe_rough` (formula perlu verifikasi backend — lihat §13).
6. Implementasi `lib/backtest-engine/run-backtest.ts` — orchestrator: fetch `price_history` mentah untuk `ticker` (filter periode sesuai `period` request), panggil signals → simulate-trades → metrics, susun jadi `BacktestRunResponse` persis sesuai `types.ts`.
7. Ganti isi `api.runBacktest` dan `api.metaIndicators` di `lib/api.ts` untuk memanggil modul lokal, bukan `fetch()`.
8. **Parity testing (wajib, bukan opsional):** untuk minimal 3 ticker × 2 kombinasi indikator berbeda, jalankan request yang identik ke FastAPI lama (kalau masih hidup) dan engine baru, bandingkan tiap field `BacktestMetrics` — toleransi floating point kecil (mis. 1e-6), bukan toleransi "kira-kira mirip".

**Acceptance criteria:**
- `hooks/use-backtest.ts` tidak berubah sama sekali.
- Hasil parity test cocok dengan backend lama dalam toleransi floating-point untuk seluruh sample.
- Waktu komputasi untuk periode 5 tahun (~1.250 bar) di browser terasa instan (idealnya < 200ms) — kalau lebih lambat dari itu di device biasa, pertimbangkan Web Worker (lihat §9.4) sebelum menganggap fase ini selesai.
- `indicators-catalog.ts` sudah diverifikasi (bukan lagi placeholder) terhadap backend.

---

### Fase 3 — Pembersihan & Dekomisioning

**Tugas:**
1. Hapus `NEXT_PUBLIC_API_BASE_URL` dari `.env.local.example` dan `.env.local` sepenuhnya.
2. Update komentar yang sekarang **salah**:
   - `.env.local.example` & `.env.local`: baris *"Frontend TIDAK PERNAH butuh kredensial Supabase apa pun"* → balik jadi benar (frontend sekarang **butuh** `NEXT_PUBLIC_SUPABASE_URL` + `NEXT_PUBLIC_SUPABASE_ANON_KEY`, dan jelaskan kenapa expose `anon` key ke browser tetap aman karena RLS).
   - `lib/api.ts` docblock: *"Frontend TIDAK PERNAH mengimpor @supabase/* ... cek file ini + grep seluruh repo untuk 'supabase' harus NOL hasil"* → tulis ulang total, docblock baru harus menjelaskan pola baru (Supabase langsung, RLS public-read, service_role tetap hanya di worker).
   - `README.md` bagian **"Struktur yang sudah ada"**: baris `lib/api.ts SATU-SATUNYA titik fetch ke backend -- TIDAK ADA Supabase di sini` → balik.
   - `README.md` bagian **"Menjalankan lokal"**: instruksi `.env.local` sekarang minta Supabase URL + anon key, bukan `NEXT_PUBLIC_API_BASE_URL`.
3. Update `app/about/page.tsx`: ganti ASCII diagram arsitektur + paragraf yang menjelaskan alur `FastAPI backend -> SATU-SATUNYA klien Supabase` (lihat §3 di dokumen ini untuk teks diagram baru). Pertahankan bagian lain (metodologi sinyal, kamus istilah, keterbatasan) — itu masih akurat & tidak terkait arsitektur data.
4. Konfirmasi ke pemilik repo backend: apakah FastAPI masih dipakai konsumen lain selain frontend ini. Kalau tidak, tandai sebagai kandidat dekomisioning (di luar scope eksekusi teknis dokumen ini).
5. Bundle size check: `next build` lalu cek ukuran chunk yang memuat `@supabase/supabase-js` — pastikan tidak melonjak drastis (biasanya tree-shaking baik untuk package ini).

**Acceptance criteria:** grep `NEXT_PUBLIC_API_BASE_URL` dan `ApiError` (versi lama yang fetch-based) di seluruh repo menghasilkan nol match. Tidak ada komentar/dokumentasi yang menyebut arsitektur lama secara keliru.

---

### Fase 4 — Peningkatan Skalabilitas (opsional, backlog)

Tidak wajib untuk memenuhi permintaan awal, tapi nilai tambah kalau ada waktu:

- **Tuning `staleTime` TanStack Query.** Data hanya di-update worker ~1x/hari (~16:30 WIB). `useScreener`/`useTickerDetail`/`usePortfolio` saat ini pakai default TanStack Query (biasanya refetch agresif). Set `staleTime` beberapa jam untuk data screener/detail/portfolio — mengurangi beban baca ke Supabase signifikan tanpa mengorbankan freshness (karena datanya memang tidak berubah secepat itu).
- **Materialized view / index tambahan** kalau universe ticker berkembang jauh melebihi 45 (IDX30/LQ45). Index yang sudah ada di `schema.sql` (`idx_price_history_ticker`, `idx_backtest_trades_ticker`, `idx_ongoing_positions_ticker`/`status`) sudah cukup untuk skala saat ini — **jangan** optimasi prematur di skala sekarang.
- **Pindahkan backtest engine ke Supabase Edge Function** kalau ternyata jadi bottleneck di device low-end, atau kalau formula ingin disembunyikan dari bundle client. Lihat §9.4 untuk trade-off lengkap.
- **Realtime subscription** ke `update_log` (Supabase Realtime) supaya dashboard auto-refresh begitu worker selesai jalan, tanpa perlu reload manual. Prioritas rendah mengingat update cuma 1x/hari.

---

## 9. Spesifikasi Teknis

### 9.1 Setup Supabase Client

```typescript
// lib/supabase/client.ts
import { createClient } from "@supabase/supabase-js";
import type { Database } from "./database.types";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error(
    "NEXT_PUBLIC_SUPABASE_URL dan NEXT_PUBLIC_SUPABASE_ANON_KEY wajib di-set di .env.local",
  );
}

// Singleton -- satu instance dipakai di seluruh app, mirip pola queryClient
// di components/layout/query-provider.tsx.
export const supabase = createClient<Database>(supabaseUrl, supabaseAnonKey);
```

Catatan: karena aplikasi ini 100% publik & tanpa autentikasi pengguna (RLS hanya expose `SELECT` ke role `anon`), `@supabase/supabase-js` polos sudah cukup. Package `@supabase/ssr` (session/cookie handling) **belum** diperlukan sampai ada fitur akun pengguna di masa depan.

Contoh minimal `database.types.ts` (untuk 2 tabel sebagai pola — ulangi untuk 3 tabel lain, atau lebih baik generate via `supabase gen types typescript`):

```typescript
// lib/supabase/database.types.ts (contoh pola, idealnya di-generate CLI)
export interface Database {
  public: {
    Tables: {
      screener_results: {
        Row: {
          ticker: string;
          sektor: string | null;
          last_close: number | null;
          last_date: string | null;
          signal_today: string | null;
          signal_strength: number | null;
          trend: string | null;
          rsi: number | null;
          atr: number | null;
          winrate: number | null;
          expectancy_pct: number | null;
          profit_factor: number | null;
          max_drawdown_pct: number | null;
          n_trades: number | null;
          sharpe_rough: number | null;
          updated_at: string;
          is_idx30: boolean;
          is_lq45: boolean;
        };
      };
      update_log: {
        Row: {
          id: number;
          run_at: string;
          tickers_processed: number | null;
          tickers_failed: number | null;
          status: string | null;
          notes: string | null;
        };
      };
      // ...ongoing_positions, price_history, backtest_trades: pola sama,
      // ikuti kolom persis dari schema.sql.
    };
  };
}
```

### 9.2 Pola Query — Contoh `screener()`

⚠️ **Temuan penting (sudah diverifikasi lewat `tsc --noEmit` sungguhan, bukan cuma dugaan):** versi `@supabase/supabase-js` yang beredar saat rencana ini ditulis (2.112.3) meng-infer tipe hasil `.select()` dengan **mem-parse string kolomnya di level tipe** (AST parser di `postgrest-js`, lewat type `GetResult<...>`). Untuk skema tanpa foreign key eksplisit seperti `schema.sql` ini, parser tersebut diam-diam gagal dan hasilnya jatuh ke `never` — TANPA error yang jelas di titik definisi `Database`, hanya muncul sebagai `Property 'x' does not exist on type 'never'` di titik pemakaian. Sudah diverifikasi: bahkan `Database` paling minimal (cuma `Tables`, tanpa `Views`/`Functions`) tetap kena masalah yang sama.

**Solusi yang terbukti bekerja:** beri *generic override* eksplisit ke setiap `.select()` — `​.select<QueryString, ResultType>(queryString)` — supaya melompati parser AST yang rapuh dan langsung pakai tipe dari `database.types.ts`. Ini pola WAJIB diikuti untuk setiap query baru yang ditulis di Fase 2 nanti, bukan cuma di Fase 1.

Contoh (representatif karena melibatkan gabungan 3 tabel tanpa FK — pola "2–3 query paralel + gabung di JS" dari §2 Prinsip #4):

```typescript
// lib/api.ts (potongan relevan, sudah diverifikasi tsc --noEmit bersih)
import { supabase } from "@/lib/supabase/client";
import type { OngoingPositionsRow, ScreenerResultsRow, UpdateLogRow } from "@/lib/supabase/database.types";
import { mapScreenerRow, mapBuyTomorrowRow, mapOpenPositionRow } from "@/lib/supabase/mappers";

async function screener(): Promise<ScreenerResponse> {
  const [screenerRes, pendingRes, openRes, logRes] = await Promise.all([
    supabase.from("screener_results").select<"*", ScreenerResultsRow>("*").order("ticker"),
    supabase
      .from("ongoing_positions")
      .select<"*", OngoingPositionsRow>("*")
      .eq("status", "PENDING_ENTRY"),
    supabase.from("ongoing_positions").select<"*", OngoingPositionsRow>("*").eq("status", "OPEN"),
    supabase
      .from("update_log")
      .select<"run_at", Pick<UpdateLogRow, "run_at">>("run_at")
      .order("run_at", { ascending: false })
      .limit(1),
  ]);

  if (screenerRes.error) throw new ApiError(500, screenerRes.error.message);
  if (pendingRes.error) throw new ApiError(500, pendingRes.error.message);
  if (openRes.error) throw new ApiError(500, openRes.error.message);

  const screenerByTicker = new Map((screenerRes.data ?? []).map((r) => [r.ticker, r]));

  return {
    updated_at: logRes.data?.[0]?.run_at ?? null,
    rows: (screenerRes.data ?? []).map(mapScreenerRow),
    buy_tomorrow: (pendingRes.data ?? []).map((p) => mapBuyTomorrowRow(p, screenerByTicker.get(p.ticker))),
    ongoing_positions: (openRes.data ?? []).map((o) => mapOpenPositionRow(o, screenerByTicker.get(o.ticker))),
  };
}
```

Untuk select kolom parsial (bukan `"*"`), override generic-nya pakai `Pick<Row, "kolom1" | "kolom2">`, misal:
`.select<"ticker, sektor", Pick<ScreenerResultsRow, "ticker" | "sektor">>("ticker, sektor")`.

`tickerDetail`, `portfolio`, `metaTickers`, `metaLastUpdate` mengikuti pola yang sama persis (query paralel dengan `Promise.all`, generic override di tiap `.select()`, gabung dengan `Map`, map ke tipe `types.ts` lewat fungsi di `mappers.ts`). Implementasi lengkap kelima fungsi ini sudah disediakan sebagai kode jadi di `lib/api.ts` (lihat file terpisah yang menyertai dokumen ini) — **sudah type-check bersih (`tsc --noEmit`, exit code 0)** terhadap `lib/types.ts` yang asli.

**Penanganan error:** Supabase JS client mengembalikan `{ data, error }`, bukan `throw` seperti `fetch()` yang gagal. Pertahankan class `ApiError` yang sudah ada supaya UI (`error instanceof Error` check di `page.tsx`) tidak perlu berubah — cukup lempar `ApiError` manual saat `error` dari Supabase tidak null.

### 9.3 Fungsi Turunan

```typescript
// lib/derive.ts

/** Aproksimasi cepat (hari kerja Senin-Jumat), TIDAK memperhitungkan libur bursa.
 *  Cocok untuk tampilan list (Portfolio, Screener). */
export function businessDaysBetween(startDate: string, endDate: string): number {
  const start = new Date(startDate);
  const end = new Date(endDate);
  let count = 0;
  const cur = new Date(start);
  while (cur < end) {
    cur.setDate(cur.getDate() + 1);
    const day = cur.getDay();
    if (day !== 0 && day !== 6) count++;
  }
  return count;
}

/** Presisi -- hitung jumlah bar price_history di antara 2 tanggal untuk 1 ticker.
 *  Pakai HANYA kalau `bars` sudah ter-fetch di context yang sama (mis. halaman Detail). */
export function barsBetween(bars: { date: string }[], startDate: string, endDate: string): number {
  const dates = bars.map((b) => b.date).sort();
  const startIdx = dates.indexOf(startDate);
  const endIdx = dates.indexOf(endDate);
  if (startIdx === -1 || endIdx === -1) return businessDaysBetween(startDate, endDate); // fallback
  return endIdx - startIdx;
}

export function computeReturnPctNow(entryPrice: number, lastClose: number | null): number | null {
  if (lastClose == null) return null;
  return ((lastClose - entryPrice) / entryPrice) * 100;
}

export function computeChangeAndChangePct(
  bars: { close: number | null }[],
): { change: number | null; change_pct: number | null } {
  if (bars.length < 2) return { change: null, change_pct: null };
  const [prev, curr] = bars.slice(-2);
  if (prev.close == null || curr.close == null) return { change: null, change_pct: null };
  const change = curr.close - prev.close;
  return { change, change_pct: (change / prev.close) * 100 };
}

export function sum(arr: number[]): number {
  return arr.reduce((a, b) => a + b, 0);
}
```

### 9.4 Engine Backtest — Breakdown Modul

```typescript
// lib/backtest-engine/indicators.ts
// Satu fungsi murni per indikator. Tambah/kurangi sesuai katalog ASLI dari backend.
export function sma(closes: number[], period: number): (number | null)[] { /* ... */ }
export function ema(closes: number[], period: number): (number | null)[] { /* ... */ }
export function rsi(closes: number[], period: number): (number | null)[] { /* ... */ }
export function macd(
  closes: number[],
  fast: number,
  slow: number,
  signalPeriod: number,
): { macd: (number | null)[]; signal: (number | null)[]; hist: (number | null)[] } { /* ... */ }
export function atr(bars: Bar[], period: number): (number | null)[] { /* ... */ }
// ...indikator lain sesuai indicators-catalog.ts

// lib/backtest-engine/signals.ts
export function computeIndicatorSeries(
  bars: Bar[],
  selected: { key: string; params: Record<string, number> }[],
): IndicatorSeries[] { /* panggil fungsi indicators.ts sesuai key */ }

export function computeConfirmations(
  series: IndicatorSeries[],
  // logika "bullish/bearish per indikator per bar" spesifik tiap indikator --
  // generalisasi dari 3-faktor Trend/Momentum/Volume di about/page.tsx
): { bullishCount: number[]; bearishCount: number[] } { /* ... */ }

export function generateSignal(
  bullishCount: number[],
  bearishCount: number[],
  confirmationThreshold: number,
): (-1 | 0 | 1)[] { /* ... */ }

// lib/backtest-engine/simulate-trades.ts
export function simulateTrades(
  bars: Bar[],
  signal: (-1 | 0 | 1)[],
  atrSeries: (number | null)[],
  opts: { tpMultiple: number; slMultiple: number; maxHoldDays: number },
): TradeRow[] {
  // State machine: entry di bars[i+1].open setelah signal[i] === 1,
  // exit pertama dari: harga menyentuh TP, harga menyentuh SL,
  // signal berlawanan muncul, atau maxHoldDays terlampaui.
  // VERIFIKASI urutan prioritas exit terhadap backend (about/page.tsx
  // menjelaskan urutan cek "TP/SL/sinyal SELL/batas waktu" tapi tidak
  // menjelaskan prioritas kalau >1 kondisi terpenuhi di hari yang sama).
}

// lib/backtest-engine/metrics.ts
// Reuse pola dari lib/portfolio-metrics.ts untuk winrate/expectancy/profit_factor.
export function computeBacktestMetrics(trades: TradeRow[], equityCurve: number[]): BacktestMetrics { /* ... */ }
export function computeEquityCurve(trades: TradeRow[]): number[] { /* kompounding return_pct tiap trade */ }
export function computeMaxDrawdown(equityCurve: number[]): number { /* ... */ }
export function computeSharpeRough(trades: TradeRow[]): number { /* FORMULA PERLU VERIFIKASI BACKEND */ }

// lib/backtest-engine/run-backtest.ts
export async function runBacktestLocal(req: BacktestRunRequest): Promise<BacktestRunResponse> {
  const bars = await fetchPriceHistoryForPeriod(req.ticker, req.period); // dari Supabase
  const series = computeIndicatorSeries(bars, req.selected_indicators.map(k => ({ key: k, params: req.params[k] ?? {} })));
  const { bullishCount, bearishCount } = computeConfirmations(series, /* ... */);
  const signal = generateSignal(bullishCount, bearishCount, req.confirmation_threshold);
  const atrSeries = atr(bars, 14); // atau param dari req kalau ATR jadi indikator terpilih
  const trades = simulateTrades(bars, signal, atrSeries, {
    tpMultiple: req.tp_multiple,
    slMultiple: req.sl_multiple,
    maxHoldDays: req.max_hold_days,
  });
  const equity_curve = computeEquityCurve(trades);
  const metrics = computeBacktestMetrics(trades, equity_curve);

  return {
    ticker: req.ticker,
    bars,
    indicator_series: series,
    bullish_count: bullishCount,
    bearish_count: bearishCount,
    signal,
    trades,
    metrics,
    equity_curve,
    last_trade_confirmation:
      series.length > 0
        ? { filled: bullishCount.at(-1) ?? 0, total: req.selected_indicators.length }
        : null,
  };
}
```

**Opsi B — Supabase Edge Function** (alternatif kalau client-side dianggap tidak cukup di masa depan): pindahkan seluruh isi `lib/backtest-engine/` ke `supabase/functions/run-backtest/index.ts` (Deno runtime), panggil dari frontend lewat `supabase.functions.invoke('run-backtest', { body: req })`. Effort porting logic-nya **sama persis** (kode TypeScript yang sama, cuma beda tempat eksekusi) — bedanya cuma butuh pipeline deploy tambahan (`supabase functions deploy`). Simpan opsi ini sebagai *fallback*, jangan jadi pilihan default di Fase 2.

### 9.5 Katalog Indikator (contoh pola — WAJIB diverifikasi ke backend)

```typescript
// lib/backtest-engine/indicators-catalog.ts
//
// CATATAN PENTING: isi di bawah adalah KERANGKA/CONTOH, BUKAN sumber
// kebenaran. Nilai key/label/kategori/tier/param default-min-max HARUS
// dicocokkan 1:1 terhadap katalog asli di backend sebelum fase ini
// dianggap selesai. Jangan gunakan angka di bawah sebagai final.

export const INDICATOR_CATALOG: IndicatorSpec[] = [
  {
    key: "sma_trend",
    label: "SMA 50/200 Cross",
    category: "Trend",
    tier: 1,
    overlay: true,
    params: {
      fast: { type: "int", default: 50, min: 5, max: 100 },
      slow: { type: "int", default: 200, min: 20, max: 300 },
    },
  },
  {
    key: "rsi",
    label: "RSI",
    category: "Momentum",
    tier: 1,
    overlay: false,
    params: { period: { type: "int", default: 14, min: 2, max: 50 } },
  },
  // ...TODO: lengkapi sesuai backend -- MACD, ATR, Bollinger Bands, Volume,
  // dst. Jumlah total indikator menentukan wajar-tidaknya nilai
  // `max_indicators_selected` di IndicatorsMetaResponse.
];

export const INDICATOR_META: IndicatorsMetaResponse = {
  indicators: INDICATOR_CATALOG,
  categories: ["Trend", "Momentum", "Volatilitas", "Volume"],
  max_indicators_selected: 8, // TODO: verifikasi angka asli dari backend
};
```

---

## 10. Environment Variables

**`.env.local.example`** (baru):

```bash
# URL & anon key project Supabase (lihat idx-quant-signal-backend untuk project
# yang sama dipakai worker_fetch_and_update.py). anon key AMAN diexpose ke
# browser -- seluruh tabel di schema.sql sudah RLS public-read-only, TIDAK ADA
# policy insert/update/delete untuk role anon. Hanya service_role key (dipakai
# worker via GitHub Actions secret) yang bisa menulis -- JANGAN PERNAH taruh
# service_role key di sini.
NEXT_PUBLIC_SUPABASE_URL=https://xxxxxxxxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

`.env.local` (aktual, isi dengan value project sungguhan — file ini sudah di-gitignore lewat `.env*` di `.gitignore`, tidak berubah).

`NEXT_PUBLIC_API_BASE_URL` dihapus total di akhir Fase 3.

---

## 11. Keamanan & RLS Checklist

Checklist ini **wajib** dijalankan sebelum Fase 1 di-deploy ke production, karena `anon` key akan terlihat di browser bundle (ini normal & aman untuk Supabase — tapi RLS-nya harus benar):

- [ ] Kelima tabel (`screener_results`, `price_history`, `backtest_trades`, `ongoing_positions`, `update_log`) punya `enable row level security` — sudah ✅ di `schema.sql` yang di-share.
- [ ] Kelima tabel punya persis satu policy `for select using (true)`, **tidak ada** policy `insert`/`update`/`delete` untuk role `anon` atau `authenticated` — sudah ✅ di `schema.sql`.
- [ ] `service_role` key **tidak pernah** muncul di kode frontend, di `.env.local.example`, atau di variable environment mana pun yang berprefix `NEXT_PUBLIC_` (prefix ini artinya ter-bundle ke browser).
- [ ] Uji langsung: dari console browser (pakai `anon` key), coba `supabase.from('screener_results').insert(...)` — **harus gagal** dengan error permission. Kalau berhasil, ada kebocoran RLS yang harus diperbaiki sebelum lanjut.
- [ ] Pertimbangkan menambahkan test otomatis kecil yang mengulang cek di atas sebagai regression guard, supaya perubahan RLS di masa depan (kalau ada) tidak diam-diam membuka celah tulis.

---

## 12. Testing & Validasi

**Fase 1 (query murni):**
- Perbandingan manual angka tampilan vs FastAPI lama, minimal 5 ticker + halaman Portfolio dengan berbagai kombinasi filter.
- Uji edge case: ticker tanpa posisi aktif, ticker tanpa trade historis (`n_trades = 0`), Portfolio dengan 0 posisi closed, Screener saat `buy_tomorrow`/`ongoing_positions` kosong (pastikan `EmptyState` tetap muncul benar).

**Fase 2 (backtest engine) — parity testing wajib:**
- Susun minimal 3 ticker × 2 kombinasi indikator × 1 kombinasi param non-default = 6 skenario uji.
- Jalankan tiap skenario ke FastAPI lama (kalau masih hidup selama masa transisi) dan ke engine baru, bandingkan **setiap field** `BacktestMetrics` dan panjang array `trades`/`equity_curve`.
- Simpan hasil skenario ini sebagai *fixture* (JSON) untuk regression test otomatis jangka panjang, supaya perubahan kode di masa depan tidak diam-diam mengubah hasil backtest.
- Ukur waktu eksekusi di browser (bukan cuma Node) untuk periode 5 tahun — target subjektif < 200ms, kalau jauh melebihi itu pertimbangkan Web Worker (`new Worker(...)`) supaya UI utama tidak nge-freeze.

---

## 13. Risk Register / Pertanyaan Terbuka

Ini bagian paling penting untuk dibaca sebelum eksekusi — daftar hal yang **saya tidak bisa pastikan** dari file yang tersedia, karena source code backend Python tidak ikut di-share:

| # | Risiko / Pertanyaan Terbuka | Dampak kalau salah | Mitigasi |
|---|---|---|---|
| 1 | Katalog indikator lengkap (daftar, kategori, tier, param default/min/max, `max_indicators_selected`) tidak diketahui persis — §9.5 cuma kerangka | Backtest Lab bisa menawarkan indikator yang salah/beda dari yang production pakai | Wajib ambil dari repo backend sebelum Fase 2 dianggap selesai; kalau repo tidak tersedia, minimal replikasi 3 faktor yang **sudah** terdokumentasi di `about/page.tsx` (SMA50/200, MACD+RSI, Volume 20d) sebagai baseline |
| 2 | Formula `sharpe_rough` tidak diketahui persis (kata "rough" menyiratkan simplifikasi, tapi metodenya tidak jelas) | Angka Sharpe yang tampil bisa salah/tidak konsisten dengan versi lama | Cari `backtester.py::_compute_metrics` di repo backend (nama file ini disebut eksplisit di `portfolio-metrics.ts`); kalau tidak tersedia, dokumentasikan formula yang dipakai secara eksplisit di kode + UI (mis. tooltip) supaya tidak menyesatkan |
| 3 | Prioritas exit kalau TP & SL sama-sama tersentuh di hari/bar yang sama | Hasil backtest bisa lebih optimis/pesimis dari kenyataan | Verifikasi ke backend; kalau tidak ada, pilih konvensi konservatif (SL menang) dan dokumentasikan asumsi ini dengan jelas di kode |
| 4 | Algoritma persis `hold_days` untuk backend lama (kalender vs hari bursa vs libur nasional IDX) | Angka hold_days di Screener/Portfolio bisa beda beberapa hari dari sebelumnya | §6.1 memberi 2 pendekatan (cepat vs presisi); bandingkan dengan sample data lama sebelum Fase 3, dan terima toleransi kecil karena ini murni field tampilan, bukan input perhitungan P&L |
| 5 | Semantik `last_close`/`last_date` untuk posisi OPEN — asumsi rencana ini: ambil dari `screener_results` (snapshot harian yang sama), bukan query terpisah ke `price_history` | Kalau asumsi salah, angka `return_pct_now` di Screener bisa sedikit basi/tidak sinkron | Verifikasi: apakah worker selalu update `screener_results.last_close` dan `price_history` di run yang sama; kemungkinan besar ya (satu worker run) |
| 6 | Apakah FastAPI backend punya konsumen lain selain frontend ini | Kalau ada, jangan sarankan dekomisioning penuh | Tanyakan/verifikasi ke pemilik repo backend sebelum mematikan service |

---

## 14. Pertimbangan UX

- **State loading/error harus dipertahankan identik.** `Skeleton`, `EmptyState`, pesan error (`error instanceof Error ? error.message : "..."`) di tiap halaman sudah dirancang baik — jangan berubah perilakunya, cukup pastikan `ApiError` dari lapisan Supabase tetap kompatibel dengan pengecekan ini (lihat §9.2).
- **Backtest Lab akan terasa jauh lebih cepat** setelah Fase 2 (tidak ada lagi round-trip network, cuma komputasi lokal). Tombol *"🚀 Jalankan Backtest"* yang sekarang menampilkan teks *"Menjalankan..."* saat `isPending` mungkin jadi nyaris tidak terlihat kalau komputasi selesai dalam puluhan milidetik — ini **bagus** untuk pengalaman pengguna, tidak perlu ditambah delay artifisial, tapi pastikan transisi UI tetap halus (tidak "flash" aneh) saat state berubah super cepat.
- **Freshness indicator.** Karena `updated_at`/`run_at` dari `update_log` sekarang diambil langsung tanpa perantara, ini momen bagus untuk memastikan info "data terakhir diupdate kapan" tetap menonjol di UI (kemungkinan sudah ada di `components/` yang tidak di-share) — tidak ada perubahan wajib, cuma catatan supaya tidak terlewat saat QA.

---

## 15. Rollout & Rollback

- **Feature-flag per fungsi**, bukan per file: karena `lib/api.ts` mengekspor object `api` dengan banyak method independen, migrasi masing-masing method bisa di-deploy terpisah (Fase 1 mengganti 5 dari 7 method, sisanya tetap lama untuk sementara — sudah didesain begitu di §8).
- **Simpan implementasi lama** (versi `fetch()`-based) di git history / branch terpisah sebagai referensi cepat kalau perlu rollback satu fungsi tanpa revert seluruh migrasi.
- **Urutan deploy yang disarankan:** Fase 0 → Fase 1 → (jeda observasi beberapa hari di production, bandingkan tidak ada laporan data aneh) → Fase 2 → Fase 3.
- Jangan hapus `NEXT_PUBLIC_API_BASE_URL` dan matikan FastAPI sampai Fase 2 selesai **dan** parity testing lulus — Backtest Lab adalah satu-satunya fitur yang masih butuh fallback ke backend lama sampai saat itu.

---

## 16. Definition of Done

- [ ] `lib/api.ts` tidak lagi memanggil `fetch()` ke `NEXT_PUBLIC_API_BASE_URL` sama sekali.
- [ ] `NEXT_PUBLIC_API_BASE_URL` dihapus dari kedua file env.
- [ ] Semua 5 file hook (`use-screener`, `use-detail`, `use-portfolio`, `use-meta`, `use-backtest`) tidak berubah dari versi asli.
- [ ] Zero perubahan yang wajib di `components/` (kalau ternyata ada komponen yang fetch langsung dan perlu diubah, itu artinya asumsi arsitektur di §4 salah — dokumentasikan sebagai temuan, bukan diam-diam ditambal).
- [ ] Parity test Fase 2 lulus untuk seluruh skenario di §12, dengan hasil tersimpan sebagai fixture regression test.
- [ ] `app/about/page.tsx` dan `README.md` menjelaskan arsitektur yang **benar** (Supabase langsung, bukan FastAPI).
- [ ] Checklist keamanan §11 lulus semua.
- [ ] `indicators-catalog.ts` sudah diverifikasi terhadap backend, tidak lagi berstatus placeholder.
- [ ] `npm run build` dan `npm run lint` lulus 0 error/warning (mengikuti standar yang sudah ditetapkan README: *"npm run build — 0 error, 0 warning"*).
