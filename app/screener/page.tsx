"use client";

import { Zap, Activity, Trophy, TrendingUp, ShieldCheck, Scale, Layers } from "lucide-react";

import { PageHeader } from "@/components/shared/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { useScreener } from "@/hooks/use-screener";
import { BuyTomorrowGrid } from "@/components/screener/buy-tomorrow-grid";
import { OngoingPositionGrid } from "@/components/screener/ongoing-position-grid";
import { RankingTable } from "@/components/screener/ranking-table";

export default function ScreenerPage() {
  const { data, isLoading, isError, error } = useScreener();

  const activeCount = data?.ongoing_positions.length ?? 0;
  const maxSlots = 7;
  const slotsFull = activeCount >= maxSlots;

  return (
    <div className="flex flex-col gap-8">
      <PageHeader
        title="Screener Kuantitatif"
        description="Sinyal BUY Besok, posisi aktif berjalan, dan ranking momentum seluruh saham IDX30 & LQ45."
        action={
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <Badge variant="outline" className="border-border bg-surface-1 text-text-secondary text-[11px]">
              <Layers className="size-3 text-blue-400" /> Universe: LQ45 &amp; IDX30
            </Badge>

            <Badge
              variant="outline"
              className="border-emerald-500/30 bg-emerald-500/10 text-emerald-400 text-[11px]"
            >
              <ShieldCheck className="size-3" /> Regime: IHSG &gt; SMA200
            </Badge>

            <Badge
              variant="outline"
              className={`text-[11px] ${
                slotsFull
                  ? "border-red-500/30 bg-red-500/10 text-red-400"
                  : activeCount >= 5
                  ? "border-amber-500/30 bg-amber-500/10 text-amber-400"
                  : "border-border bg-surface-1 text-text-secondary"
              }`}
            >
              <Scale className="size-3" /> Slot: {activeCount} / {maxSlots} Aktif
            </Badge>
          </div>
        }
      />

      {isLoading && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-lg" />
          ))}
        </div>
      )}

      {isError && (
        <EmptyState
          title="Gagal memuat data screener"
          description={
            error instanceof Error
              ? error.message
              : "Periksa koneksi database Supabase atau muat ulang halaman."
          }
        />
      )}

      {data && (
        <>
          {/* Section: Sinyal BUY Besok */}
          <section className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="flex size-6 items-center justify-center rounded-md bg-emerald-500/10 text-emerald-400">
                  <Zap className="size-3.5" />
                </div>
                <h2 className="text-[1.125rem] font-semibold text-text-primary">
                  Sinyal BUY Besok (Eksekusi Open)
                </h2>
              </div>
              {data.buy_tomorrow.length > 0 && (
                <span className="text-xs text-text-muted">
                  {data.buy_tomorrow.length} setup terkonfirmasi
                </span>
              )}
            </div>

            {slotsFull && (
              <div className="rounded-md border border-amber-500/30 bg-amber-500/10 p-2.5 text-xs text-amber-300">
                <strong>Catatan Kapasitas:</strong> Portofolio telah mencapai batas maksimum 7 slot aktif. Sinyal baru disarankan ditahan hingga ada posisi yang closed.
              </div>
            )}

            {data.buy_tomorrow.length > 0 ? (
              <BuyTomorrowGrid rows={data.buy_tomorrow} />
            ) : (
              <EmptyState
                icon={TrendingUp}
                title="Belum ada sinyal BUY baru untuk sesi bursa berikutnya."
                description="Sistem mempertahankan disiplin tinggi dengan menolak saham yang belum lolos 3 Hard Gates (Uptrend Stage 2, RSI Sehat, dan Anti-FOMO)."
              />
            )}
          </section>

          {/* Section: Ongoing Position */}
          <section className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="flex size-6 items-center justify-center rounded-md bg-blue-500/10 text-blue-400">
                  <Activity className="size-3.5" />
                </div>
                <h2 className="text-[1.125rem] font-semibold text-text-primary">
                  Posisi Berjalan (Ongoing Positions)
                </h2>
              </div>
              <span className="text-xs text-text-muted">
                {data.ongoing_positions.length} posisi aktif
              </span>
            </div>

            {data.ongoing_positions.length > 0 ? (
              <OngoingPositionGrid rows={data.ongoing_positions} />
            ) : (
              <EmptyState title="Tidak ada posisi yang sedang berjalan (open) saat ini." />
            )}
          </section>

          {/* Section: Ranking Semua Saham */}
          <section className="flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <div className="flex size-6 items-center justify-center rounded-md bg-amber-500/10 text-amber-400">
                <Trophy className="size-3.5" />
              </div>
              <h2 className="text-[1.125rem] font-semibold text-text-primary">
                Ranking Momentum Saham IDX30 / LQ45
              </h2>
            </div>
            <RankingTable rows={data.rows} />
          </section>
        </>
      )}
    </div>
  );
}
