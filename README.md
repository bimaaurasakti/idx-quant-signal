# IDX Quant Signal — Frontend

Next.js 16.3.0 (Turbopack) + React 19.2.8 + TypeScript + **Tailwind CSS v4**
(CSS-first, `@theme inline` — tidak ada `tailwind.config.ts`) + komponen ala
shadcn/ui (ditulis manual, lihat catatan di bawah).

**Arsitektur data: akses Supabase langsung dari browser** (lewat
`@supabase/supabase-js`, anon key, dibatasi Row Level Security baca-saja) —
**tidak ada backend API terpisah** yang perlu dijalankan. Lihat
`IMPLEMENTATION_PLAN_SUPABASE_MIGRATION.md` untuk detail lengkap migrasi
dari arsitektur lama (Next.js → FastAPI → Supabase).

## Status

- ✅ Screener, Detail Saham, Portfolio, Risk Calculator, About — baca data
  langsung dari Supabase, sudah type-check bersih (`tsc --noEmit`) terhadap
  `lib/types.ts`.
- ⏳ **Backtest Lab** (`/backtest`) — sengaja dinonaktifkan sementara.
  Engine-nya (indikator teknikal, sinyal multi-confirmation, simulasi
  trade, metrik) belum di-porting dari backend Python ke TypeScript —
  butuh source code backend asli untuk verifikasi formula supaya angka
  yang tampil tidak menyesatkan. Lihat §6.3, §9.4, §13 di
  `IMPLEMENTATION_PLAN_SUPABASE_MIGRATION.md`.

## ⚠️ Yang HILANG dari zip ini: folder `components/`

Zip ini berisi **project utuh KECUALI `components/`** — folder itu tidak pernah
diberikan ke Claude (terlalu banyak file untuk copy-paste manual), jadi tidak
bisa direkonstruksi di sini. **Setelah extract zip ini, langkah WAJIB pertama:
salin folder `components/` dari project asli Anda ke root project ini**,
sebelum `npm install` / `npm run dev`.

Terverifikasi lewat `tsc --noEmit` sungguhan (bukan dugaan) — modul berikut
yang akan hilang tanpa `components/`:

```
components/ui/card.tsx
components/ui/input.tsx
components/ui/label.tsx
components/ui/skeleton.tsx
components/ui/slider.tsx
components/layout/app-shell.tsx
components/layout/query-provider.tsx
components/shared/empty-state.tsx
components/shared/metric-card.tsx
components/shared/page-header.tsx
components/shared/price-chart.tsx
components/screener/buy-tomorrow-grid.tsx
components/screener/ongoing-position-grid.tsx
components/screener/ranking-table.tsx
components/portfolio/filters-bar.tsx
components/portfolio/exit-breakdown-chart.tsx
components/portfolio/sector-performance-chart.tsx
components/portfolio/cumulative-return-chart.tsx
components/portfolio/closed-positions-table.tsx
components/detail/price-header.tsx
components/detail/position-status-banner.tsx
components/detail/trade-history-table.tsx
```

Ini daftar yang **langsung** diimpor oleh file yang ada di zip ini. `tsc` juga
menunjukkan ~23 error tambahan bertipe "implicitly has an 'any' type" di
`risk/page.tsx`, `portfolio/page.tsx`, dan `detail-client.tsx` (parameter
callback seperti `format={(v) => ...}` atau `onValueChange={([v]) => ...}`)
— **ini BUKAN bug terpisah**, semuanya konsekuensi dari akar masalah yang
sama: tanpa definisi tipe prop dari `MetricCard`/`Slider`/`Input` yang asli,
TypeScript tidak bisa meng-infer tipe parameter callback tsb secara
kontekstual. Begitu `components/` asli Anda masuk, seluruh error ini
(termasuk yang "implicitly any") akan hilang bersamaan.

Catatan tambahan: README versi asli menyebut `button`, `badge`, dan
`tooltip` juga ditulis manual di `components/ui/` — keduanya tidak muncul di
daftar "hilang" di atas karena tidak diimpor **langsung** oleh file yang ada
di zip ini (kemungkinan besar dipakai *di dalam* komponen lain yang memang
hilang, seperti `SignalBadge` atau tooltip di `MetricCard`). **Salin seluruh
folder `components/` apa adanya**, jangan cuma file-file di daftar atas.

## ⚠️ Catatan penting: Google Fonts di sandbox ini diblokir

`app/layout.tsx` memakai `next/font/google` (Inter + JetBrains Mono) — ini
kode **produksi yang benar** dan akan bekerja otomatis begitu dijalankan di
environment dengan akses internet normal (dev machine Anda, Vercel, dst).

Sandbox tempat scaffold ini dibuat hanya mengizinkan domain tertentu
(`fonts.googleapis.com` diblokir 403) — jadi:

- **`npm run dev`**: font otomatis *fallback* dengan WARNING (bukan error) — tetap jalan normal, sudah diverifikasi.
- **`npm run build`**: GAGAL di sandbox ini karena Turbopack butuh benar-benar mengunduh font saat build produksi. Di komputer/CI/Vercel Anda (dengan akses internet normal) ini akan **build sukses tanpa perubahan apa pun**.

Tidak ada tindakan yang perlu Anda lakukan — cukup jalankan seperti biasa di
environment Anda.

## Menjalankan lokal

```bash
npm install
cp .env.local.example .env.local
# edit .env.local: isi NEXT_PUBLIC_SUPABASE_URL & NEXT_PUBLIC_SUPABASE_ANON_KEY
# dengan nilai project Supabase Anda (project yang sama dipakai
# worker_fetch_and_update.py untuk menulis data).

npm run dev
# buka http://localhost:3000 -> otomatis redirect ke /screener
```

Tidak perlu menjalankan backend apa pun secara terpisah.

## Tentang komponen `components/ui/*`

CLI resmi (`npx shadcn@latest add ...`) mengambil komponen dari registry
`ui.shadcn.com`, yang **juga diblokir** di sandbox ini (sama seperti Google
Fonts). Komponen dasar (`button`, `card`, `badge`, `tooltip`, `skeleton`)
karena itu ditulis manual di sini — formatnya persis output resmi CLI style
`new-york`, jadi 100% kompatibel. Untuk menambah komponen lain di environment
Anda (yang punya akses internet normal), tetap pakai cara biasa:

```bash
npx shadcn@latest add tabs popover dialog select slider switch calendar dropdown-menu
```

## Struktur yang sudah ada

```
app/
  layout.tsx            RootLayout: font, QueryProvider, AppShell
  globals.css            Design system lengkap (token warna, kursor berkedip)
  page.tsx               redirect -> /screener
  screener/page.tsx      Screener (pakai useScreener())
  detail/page.tsx         Pemilih saham -> /detail/[ticker]
  detail/[ticker]/page.tsx  Detail Saham (pakai useTickerDetail())
  portfolio/page.tsx      Portfolio (pakai usePortfolio())
  risk/page.tsx           Risk Calculator (murni client-side, TANPA fetch apa pun)
  backtest/page.tsx       Backtest Lab -- SEMENTARA nonaktif, lihat bagian Status di atas
  about/page.tsx          Metodologi & batasan
components/
  ui/                    button, card, badge, tooltip, skeleton (manual, format shadcn)
  layout/                app-shell, top-nav (wordmark+kursor), query-provider
  shared/                metric-card (count-up), signal-badge, conviction-meter, empty-state, page-header
  screener/               buy-tomorrow-grid, ongoing-position-grid, ranking-table (sort+filter client-side)
hooks/                   use-screener, use-detail, use-portfolio, use-backtest, use-meta (TanStack Query,
                          TIDAK berubah oleh migrasi Supabase -- semua tetap konsumsi lewat lib/api.ts)
lib/
  api.ts                 SATU-SATUNYA titik akses data -- baca LANGSUNG dari Supabase (kecuali
                          metaIndicators/runBacktest, lihat bagian Status)
  supabase/
    client.ts             Singleton @supabase/supabase-js
    database.types.ts      Cermin tipe tabel Supabase dari schema.sql
    mappers.ts             Raw row Supabase -> lib/types.ts (kontrak yang dipakai seluruh UI)
  derive.ts               Fungsi turunan murni (hold_days, return_pct_now, change/change_pct, dll)
  types.ts                Kontrak tipe stabil dipakai seluruh UI (TIDAK berubah oleh migrasi Supabase)
  format.ts                formatIdr/formatPctId/formatNumberId/formatDateId (Intl-based)
  constants.ts             signalColors/exitReasonColor -- single source of truth warna
  portfolio-metrics.ts      Formula winrate/expectancy/profit_factor, dihitung client-side
```

## Rencana migrasi & catatan teknis

Lihat `IMPLEMENTATION_PLAN_SUPABASE_MIGRATION.md` di root repo untuk:
pemetaan lengkap tabel Supabase ↔ tipe frontend, alasan tiap keputusan
arsitektur, dan rencana Fase 2 (porting engine Backtest Lab) begitu source
code backend tersedia untuk verifikasi formula.
