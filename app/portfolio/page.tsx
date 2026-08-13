"use client";

import * as React from "react";

import { PageHeader } from "@/components/shared/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { MetricCard } from "@/components/shared/metric-card";
import { Skeleton } from "@/components/ui/skeleton";
import { FiltersBar } from "@/components/portfolio/filters-bar";
import { ExitBreakdownChart } from "@/components/portfolio/exit-breakdown-chart";
import { SectorPerformanceChart } from "@/components/portfolio/sector-performance-chart";
import { CumulativeReturnChart } from "@/components/portfolio/cumulative-return-chart";
import { ClosedPositionsTable } from "@/components/portfolio/closed-positions-table";
import { usePortfolio } from "@/hooks/use-portfolio";
import { computeMetrics } from "@/lib/portfolio-metrics";
import { formatNumberId, formatPctId } from "@/lib/format";
import { METRIC_TOOLTIP } from "@/lib/constants";

export default function PortfolioPage() {
  const { data, isLoading, isError, error } = usePortfolio();

  const [selectedSectors, setSelectedSectors] = React.useState<string[]>([]);
  const [dateFrom, setDateFrom] = React.useState("");
  const [dateTo, setDateTo] = React.useState("");
  const [tickerSearch, setTickerSearch] = React.useState("");

  const allSectors = React.useMemo(
    () => Array.from(new Set((data?.positions ?? []).map((p) => p.sektor))).sort(),
    [data],
  );

  const filtered = React.useMemo(() => {
    if (!data) return [];
    return data.positions.filter((p) => {
      if (selectedSectors.length > 0 && !selectedSectors.includes(p.sektor)) return false;
      if (dateFrom && p.exit_date < dateFrom) return false;
      if (dateTo && p.exit_date > dateTo) return false;
      if (tickerSearch && !p.ticker.toUpperCase().includes(tickerSearch.toUpperCase())) return false;
      return true;
    });
  }, [data, selectedSectors, dateFrom, dateTo, tickerSearch]);

  const metrics = React.useMemo(() => computeMetrics(filtered), [filtered]);

  function toggleSector(s: string) {
    setSelectedSectors((prev) => (prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]));
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="💼 Portfolio — Riwayat Posisi Closed"
        description="Jejak sinyal LIVE — posisi yang benar-benar dibuka & ditutup hari demi hari, tanpa lookahead, tidak pernah direvisi ke belakang."
      />

      {isLoading && (
        <div className="flex flex-col gap-4">
          <Skeleton className="h-20 rounded-lg" />
          <div className="grid grid-cols-3 gap-3 sm:grid-cols-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-20 rounded-md" />
            ))}
          </div>
        </div>
      )}

      {isError && (
        <EmptyState
          title="Gagal memuat data portfolio"
          description={error instanceof Error ? error.message : "Coba muat ulang halaman."}
        />
      )}

      {data && data.positions.length === 0 && (
        <EmptyState
          title="📭 Belum ada posisi yang closed."
          description="Data akan mulai muncul setelah sebuah posisi live mencapai Take Profit, Stop Loss, sinyal SELL, atau batas waktu holding (20 hari bursa)."
        />
      )}

      {data && data.positions.length > 0 && (
        <>
          <FiltersBar
            sectors={allSectors}
            selectedSectors={selectedSectors}
            onToggleSector={toggleSector}
            dateFrom={dateFrom}
            dateTo={dateTo}
            onDateFromChange={setDateFrom}
            onDateToChange={setDateTo}
            tickerSearch={tickerSearch}
            onTickerSearchChange={setTickerSearch}
          />

          {metrics && metrics.n < 20 && (
            <div
              className="rounded-lg border-l-4 px-4 py-2.5 text-[13px] text-text-primary"
              style={{ borderLeftColor: "var(--signal-hold)", backgroundColor: "var(--signal-hold-bg)" }}
            >
              ⚠️ Sample masih kecil (n={metrics.n} posisi closed). Hati-hati menarik kesimpulan statistik
              dari jumlah trade sekecil ini.
            </div>
          )}

          {metrics ? (
            <>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
                <MetricCard label="Total Closed" value={metrics.n} format={(v) => formatNumberId(v)} tone="neutral" />
                <MetricCard
                  label="Winrate"
                  value={metrics.winrate}
                  format={(v) => `${formatNumberId(v, 1)}%`}
                  tone={metrics.winrate > 50 ? "bullish" : "neutral"}
                  helpText={METRIC_TOOLTIP.winrate}
                />
                <MetricCard
                  label="Expectancy"
                  value={metrics.expectancy}
                  format={(v) => formatPctId(v)}
                  tone={metrics.expectancy > 0 ? "bullish" : "bearish"}
                  helpText={METRIC_TOOLTIP.expectancy}
                />
                <MetricCard
                  label="Profit Factor"
                  value={metrics.profitFactor}
                  format={(v) => formatNumberId(v, 2)}
                  tone={metrics.profitFactor == null || metrics.profitFactor > 1 ? "bullish" : "bearish"}
                  helpText={METRIC_TOOLTIP.profitFactor}
                />
                <MetricCard
                  label="Total Return (Sum)"
                  value={metrics.totalReturn}
                  format={(v) => formatPctId(v)}
                  tone={metrics.totalReturn > 0 ? "bullish" : "bearish"}
                  helpText={METRIC_TOOLTIP.totalReturn}
                />
                <MetricCard
                  label="Avg Hold"
                  value={metrics.avgHoldDays}
                  format={(v) => `${formatNumberId(v, 1)} hari`}
                  tone="neutral"
                />
              </div>
              {metrics.profitFactor == null && (
                <p className="text-[11.5px] text-text-muted">
                  ∞ = belum ada trade rugi sama sekali dalam sample/filter saat ini.
                </p>
              )}

              <div className="grid gap-4 lg:grid-cols-2">
                <ExitBreakdownChart positions={filtered} />
                <SectorPerformanceChart positions={filtered} />
              </div>
              <CumulativeReturnChart positions={filtered} />

              <div>
                <h2 className="mb-3 text-[1.125rem] font-semibold text-text-primary">
                  📋 Detail Posisi Closed
                </h2>
                <ClosedPositionsTable positions={filtered} />
              </div>
            </>
          ) : (
            <EmptyState title="Tidak ada posisi closed yang cocok dengan filter di atas." />
          )}
        </>
      )}
    </div>
  );
}
