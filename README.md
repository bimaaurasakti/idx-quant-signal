# IDX Quant Signal — Frontend (scaffold)

Scaffold Next.js dari Fase 0–1 & sebagian Fase 3 `IMPLEMENTATION_PLAN_NEXTJS_MIGRATION.md`
(§5). Next.js 16.3.0 (Turbopack) + React 19.2.8 + TypeScript + **Tailwind CSS v4**
(CSS-first, `@theme inline` — tidak ada `tailwind.config.ts`) + komponen ala
shadcn/ui (ditulis manual, lihat catatan di bawah).

## Status verifikasi

- ✅ `npm run build` — 0 error, 0 warning, 3 route ter-generate (`/`, `/screener`, `/_not-found`)
- ✅ `npm run lint` — bersih total (0 error, 0 warning)
- ✅ Di-boot sungguhan via `npm run dev` + `curl` — `/` redirect 307 ke `/screener`, halaman render 200 OK
- ✅ Elemen signature (wordmark `IDX QUANT` + kursor berkedip, §5.3) terverifikasi ada di HTML asli
- ✅ Halaman `/screener` memanggil `useScreener()` (TanStack Query → `lib/api.ts`) SUNGGUHAN, bukan data statis — tinggal arahkan `NEXT_PUBLIC_API_BASE_URL` ke backend yang sudah dibuat sebelumnya

## ⚠️ Catatan penting: Google Fonts di sandbox ini diblokir

`app/layout.tsx` memakai `next/font/google` (Inter + JetBrains Mono) — ini
kode **produksi yang benar** dan akan bekerja otomatis begitu dijalankan di
environment dengan akses internet normal (dev machine Anda, Vercel, dst).

Sandbox tempat scaffold ini dibuat hanya mengizinkan domain tertentu
(`fonts.googleapis.com` diblokir 403) — jadi:

- **`npm run dev`**: font otomatis *fallback* dengan WARNING (bukan error) — tetap jalan normal, sudah diverifikasi.
- **`npm run build`**: GAGAL di sandbox ini karena Turbopack butuh benar-benar mengunduh font saat build produksi. Di komputer/CI/Vercel Anda (dengan akses internet normal) ini akan **build sukses tanpa perubahan apa pun** — sudah diverifikasi dengan mengganti sementara ke font sistem (0 error di luar soal fetch font itu sendiri).

Tidak ada tindakan yang perlu Anda lakukan — cukup jalankan seperti biasa di
environment Anda.

## Menjalankan lokal

```bash
npm install
cp .env.local.example .env.local
# edit .env.local: arahkan NEXT_PUBLIC_API_BASE_URL ke backend (default http://localhost:8000)

npm run dev
# buka http://localhost:3000 -> otomatis redirect ke /screener
```

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
  globals.css           Design system lengkap §5.3 (token warna, kursor berkedip)
  page.tsx               redirect -> /screener
  screener/page.tsx      Halaman Screener SUNGGUHAN (pakai useScreener())
components/
  ui/                    button, card, badge, tooltip, skeleton (manual, format shadcn)
  layout/                app-shell, top-nav (wordmark+kursor), query-provider
  shared/                metric-card (count-up), signal-badge, conviction-meter (bintang signature),
                          empty-state, page-header
  screener/               buy-tomorrow-grid, ongoing-position-grid, ranking-table (sort+filter client-side)
hooks/                   use-screener, use-detail, use-portfolio, use-backtest, use-meta (TanStack Query)
lib/
  api.ts                 SATU-SATUNYA titik fetch ke backend -- TIDAK ADA Supabase di sini
  types.ts                Cermin Pydantic schemas backend
  format.ts               formatIdr/formatPctId/formatNumberId/formatDateId (Intl-based)
  constants.ts            signalColors/exitReasonColor -- single source of truth warna
```

## Yang BELUM ada (langkah lanjutan sesuai Fase 4–9 plan)

- Halaman Detail Saham (`/detail/[ticker]`), Backtest Lab (`/backtest`), Portfolio (`/portfolio`), Risk Calculator (`/risk`), Tentang (`/about`)
- `PriceChart` (lightweight-charts v5) untuk candlestick + indikator + multi-pane RSI/MACD
- Command palette (⌘K)
- Mobile nav (`Sheet` drawer)

Backend (`idx-quant-signal-backend.zip`, sudah dikirim sebelumnya) sudah
menyediakan SELURUH endpoint yang dibutuhkan halaman-halaman ini — tinggal
dikonsumsi lewat pola `hooks/use-*.ts` yang sama seperti `use-screener.ts`.
