"use client";

import { TrendingUp } from "lucide-react";

import { PageHeader } from "@/components/shared/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useScreener } from "@/hooks/use-screener";
import { BuyTomorrowGrid } from "@/components/screener/buy-tomorrow-grid";
import { OngoingPositionGrid } from "@/components/screener/ongoing-position-grid";
import { RankingTable } from "@/components/screener/ranking-table";

export default function ScreenerPage() {
  const { data, isLoading, isError, error } = useScreener();

  return (
    <div className="flex flex-col gap-8">
      <PageHeader
        title="Screener"
        description="Sinyal BUY Besok, posisi berjalan, dan ranking seluruh saham IDX30 & LQ45."
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
              : "Periksa apakah backend API sudah berjalan & NEXT_PUBLIC_API_BASE_URL benar."
          }
        />
      )}

      {data && (
        <>
          <section>
            <h2 className="mb-3 text-[1.125rem] font-semibold text-text-primary">
              🎯 Sinyal BUY Besok
            </h2>
            {data.buy_tomorrow.length > 0 ? (
              <BuyTomorrowGrid rows={data.buy_tomorrow} />
            ) : (
              <EmptyState
                icon={TrendingUp}
                title="Belum ada sinyal BUY baru untuk sesi bursa berikutnya."
              />
            )}
          </section>

          <section>
            <h2 className="mb-3 text-[1.125rem] font-semibold text-text-primary">
              📌 Ongoing Position
            </h2>
            {data.ongoing_positions.length > 0 ? (
              <OngoingPositionGrid rows={data.ongoing_positions} />
            ) : (
              <EmptyState title="Tidak ada posisi yang sedang berjalan (open) saat ini." />
            )}
          </section>

          <section>
            <h2 className="mb-3 text-[1.125rem] font-semibold text-text-primary">
              🏆 Ranking Semua Saham
            </h2>
            <RankingTable rows={data.rows} />
          </section>
        </>
      )}
    </div>
  );
}
