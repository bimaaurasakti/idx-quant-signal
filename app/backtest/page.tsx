"use client";

import { FlaskConical } from "lucide-react";

import { EmptyState } from "@/components/shared/empty-state";
import { PageHeader } from "@/components/shared/page-header";

/**
 * Backtest Lab -- SENGAJA dinonaktifkan sementara.
 *
 * Sebelumnya halaman ini memanggil FastAPI (metaIndicators + runBacktest)
 * untuk menghitung indikator, sinyal multi-confirmation, dan simulasi
 * trade. Sejak migrasi ke akses Supabase langsung, backend itu tidak lagi
 * dijalankan -- dan engine backtest-nya BELUM di-porting ke TypeScript
 * (butuh source code backend untuk verifikasi formula indikator/sinyal/
 * metrik, supaya angka yang tampil tidak menyesatkan; lihat §6.3, §9.4,
 * §13 di IMPLEMENTATION_PLAN_SUPABASE_MIGRATION.md).
 *
 * `lib/api.ts::metaIndicators()` dan `::runBacktest()` sekarang melempar
 * ApiError yang jelas kalau ada kode lain yang mencoba memanggilnya --
 * halaman ini SENGAJA tidak memanggil keduanya sama sekali, supaya tidak
 * ada request yang gagal di-console atau state loading yang menggantung.
 *
 * Untuk mengaktifkan lagi: kerjakan Fase 2 di rencana implementasi, lalu
 * kembalikan halaman ini ke versi lengkap (indicator picker, param panel,
 * hasil backtest) yang memanggil useIndicatorsMeta()/useRunBacktest() dari
 * hooks/use-meta.ts & hooks/use-backtest.ts seperti semula -- kedua hook
 * itu TIDAK berubah sama sekali selama migrasi ini, jadi tinggal pakai.
 */
export default function BacktestPage() {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="🧪 Backtest Lab"
        description="Coba kombinasi indikator sendiri & lihat bagaimana strategi itu tampil di data historis — lengkap dengan replay, indikator, dan posisi entry/exit."
      />

      <EmptyState
        icon={FlaskConical}
        title="Backtest Lab sedang dalam pengembangan ulang"
        description="Halaman ini sementara dinonaktifkan selama migrasi dashboard ke akses Supabase langsung, tanpa backend API terpisah. Screener, Detail Saham, Portfolio, dan Risk Calculator sudah bisa dipakai penuh sekarang — Backtest Lab menyusul setelah engine-nya selesai dipindahkan."
      />
    </div>
  );
}
