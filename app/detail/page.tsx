"use client";

import Link from "next/link";

import { PageHeader } from "@/components/shared/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useTickersMeta } from "@/hooks/use-meta";

/** /detail tanpa ticker -- pemilih saham (grid), lompat ke /detail/{ticker}. */
export default function DetailIndexPage() {
  const { data, isLoading, isError } = useTickersMeta();
  const sectors = data ? Object.entries(data.sectors) : [];

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Detail Saham" description="Pilih saham untuk melihat detail performa & chart." />

      {isLoading && (
        <div className="grid grid-cols-4 gap-2 sm:grid-cols-6 lg:grid-cols-9">
          {Array.from({ length: 18 }).map((_, i) => (
            <Skeleton key={i} className="h-10 rounded-md" />
          ))}
        </div>
      )}

      {isError && <EmptyState title="Gagal memuat daftar saham." />}

      {sectors.map(([sektor, tickers]) => (
        <div key={sektor}>
          <h3 className="mb-2 text-[12.5px] font-medium text-text-secondary">
            {sektor.replaceAll("_", " ")}
          </h3>
          <div className="flex flex-wrap gap-2">
            {tickers.map((t) => (
              <Link
                key={t}
                href={`/detail/${t}`}
                className="rounded-md border border-border bg-surface-1 px-3 py-1.5 font-mono text-[13px] text-text-primary transition-colors hover:border-brand hover:bg-surface-2"
              >
                {t}
              </Link>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
