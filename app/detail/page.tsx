"use client";

import * as React from "react";
import Link from "next/link";
import { Layers, Search } from "lucide-react";

import { PageHeader } from "@/components/shared/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useTickersMeta } from "@/hooks/use-meta";

export default function DetailIndexPage() {
  const { data, isLoading, isError } = useTickersMeta();
  const [search, setSearch] = React.useState("");

  const sectors = React.useMemo(() => {
    if (!data) return [];
    return Object.entries(data.sectors).map(([sektor, tickers]) => {
      const filteredTickers = search
        ? tickers.filter((t) => t.toUpperCase().includes(search.toUpperCase()))
        : tickers;
      return [sektor, filteredTickers] as const;
    }).filter(([, tickers]) => tickers.length > 0);
  }, [data, search]);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <PageHeader
          title="Detail Saham"
          description="Pilih saham konstituen IDX30 & LQ45 untuk melihat chart teknikal, metrik historis, dan status posisi."
          className="mb-0"
        />
        <div className="relative w-full sm:w-64">
          <Search className="absolute left-2.5 top-2.5 size-4 text-text-muted" />
          <Input
            placeholder="Cari kode saham (misal: BBCA)..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-8 text-xs bg-surface-1 font-mono uppercase"
          />
        </div>
      </div>

      {isLoading && (
        <div className="grid grid-cols-4 gap-2 sm:grid-cols-6 lg:grid-cols-9">
          {Array.from({ length: 18 }).map((_, i) => (
            <Skeleton key={i} className="h-10 rounded-md" />
          ))}
        </div>
      )}

      {isError && <EmptyState title="Gagal memuat daftar saham." />}

      {sectors.length === 0 && !isLoading && (
        <EmptyState title={`Tidak ada saham yang cocok dengan pencarian "${search}"`} />
      )}

      <div className="flex flex-col gap-5">
        {sectors.map(([sektor, tickers]) => (
          <div key={sektor} className="flex flex-col gap-2">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">
              <Layers className="size-3.5 text-blue-400" />
              <span>{sektor.replaceAll("_", " ")}</span>
              <Badge variant="outline" className="text-[10px] py-0 px-1 text-text-muted ml-1">
                {tickers.length}
              </Badge>
            </div>
            <div className="flex flex-wrap gap-2">
              {tickers.map((t) => (
                <Link
                  key={t}
                  href={`/detail/${t}`}
                  className="rounded-md border border-border bg-surface-1 px-3.5 py-1.5 font-mono text-[13px] font-medium text-text-primary transition-all duration-150 hover:border-brand hover:bg-surface-2 hover:shadow-xs hover:-translate-y-0.5"
                >
                  {t}
                </Link>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
