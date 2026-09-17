"use client";

import { useRouter } from "next/navigation";
import { History, ShieldCheck, CheckCircle2, Layers } from "lucide-react";

import { PageHeader } from "@/components/shared/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { MetricCard } from "@/components/shared/metric-card";
import { PriceChart } from "@/components/shared/price-chart";
import { PriceHeader } from "@/components/detail/price-header";
import { PositionStatusBanner } from "@/components/detail/position-status-banner";
import { TradeHistoryTable } from "@/components/detail/trade-history-table";
import { useTickerDetail } from "@/hooks/use-detail";
import { useTickersMeta } from "@/hooks/use-meta";
import { formatPctId, formatNumberId } from "@/lib/format";
import { METRIC_TOOLTIP } from "@/lib/constants";

export function DetailClient({ ticker }: { ticker: string }) {
  const router = useRouter();
  const { data, isLoading, isError, error } = useTickerDetail(ticker);
  const { data: tickersMeta } = useTickersMeta();

  const allTickers = tickersMeta
    ? Array.from(new Set(Object.values(tickersMeta.sectors).flat())).sort()
    : [];

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Detail Saham"
        description="Performa strategi produksi (multi-confirmation, signals.py) per saham."
        action={
          allTickers.length > 0 ? (
            <div className="flex items-center gap-2">
              <span className="text-xs text-text-secondary hidden sm:inline">Pilih Emiten:</span>
              <select
                value={ticker}
                onChange={(e) => router.push(`/detail/${e.target.value}`)}
                className="rounded-md border border-border bg-surface-1 px-3 py-1.5 font-mono text-[13px] text-text-primary focus:border-brand focus:outline-none"
              >
                {allTickers.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
          ) : undefined
        }
      />

      {isLoading && (
        <div className="flex flex-col gap-4">
          <Skeleton className="h-28 rounded-lg" />
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-20 rounded-md" />
            ))}
          </div>
          <Skeleton className="h-[480px] rounded-lg" />
        </div>
      )}

      {isError && (
        <EmptyState
          title="Gagal memuat data saham"
          description={
            error instanceof Error
              ? error.message
              : "Periksa apakah backend API sudah berjalan & ticker ini ada di screener_results."
          }
        />
      )}

      {data && (
        <>
          <PriceHeader
            ticker={data.ticker}
            sektor={data.sektor}
            price={data.last_close}
            change={data.change}
            changePct={data.change_pct}
            signal={data.signal_today}
            filled={data.signal_strength ?? 0}
            total={3}
          />

          {data.active_position && <PositionStatusBanner position={data.active_position} />}

          {/* Hard Gates Verification Checklist Bar */}
          <div className="flex flex-wrap items-center gap-2 rounded-lg border border-border bg-surface-1 px-3.5 py-2 text-xs">
            <span className="font-medium text-text-secondary">Pemeriksaan Syarat Strategi:</span>
            <Badge variant="outline" className="border-border bg-surface-0 text-[10.5px] text-text-secondary">
              <CheckCircle2 className="size-3 text-emerald-400" /> Market Regime IHSG
            </Badge>
            <Badge variant="outline" className="border-border bg-surface-0 text-[10.5px] text-text-secondary">
              <ShieldCheck className="size-3 text-blue-400" /> Stage 2 Uptrend (SMA50 &gt; 200)
            </Badge>
            <Badge variant="outline" className="border-border bg-surface-0 text-[10.5px] text-text-secondary">
              <Layers className="size-3 text-purple-400" /> Anti-FOMO &amp; RSI Normal
            </Badge>
          </div>

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
            <MetricCard
              label="Winrate Historis"
              value={data.metrics.winrate}
              format={(v) => `${formatNumberId(v, 1)}%`}
              tone={(data.metrics.winrate ?? 0) > 50 ? "bullish" : "neutral"}
              helpText={METRIC_TOOLTIP.winrate}
            />
            <MetricCard
              label="Expectancy"
              value={data.metrics.expectancy_pct}
              format={(v) => formatPctId(v)}
              tone={(data.metrics.expectancy_pct ?? 0) > 0 ? "bullish" : "bearish"}
              helpText={METRIC_TOOLTIP.expectancy}
            />
            <MetricCard
              label="Profit Factor"
              value={data.metrics.profit_factor}
              format={(v) => formatNumberId(v, 2)}
              tone={(data.metrics.profit_factor ?? 0) > 1 ? "bullish" : "bearish"}
              helpText={METRIC_TOOLTIP.profitFactor}
            />
            <MetricCard
              label="Max Drawdown"
              value={data.metrics.max_drawdown_pct}
              format={(v) => formatPctId(v)}
              tone="bearish"
              helpText={METRIC_TOOLTIP.maxDrawdown}
            />
            <MetricCard
              label="Total Return (Sum)"
              value={data.metrics.total_return_pct}
              format={(v) => formatPctId(v)}
              tone={(data.metrics.total_return_pct ?? 0) > 0 ? "bullish" : "bearish"}
              helpText={METRIC_TOOLTIP.totalReturn}
            />
          </div>

          {data.price_history.length > 0 ? (
            <PriceChart bars={data.price_history} />
          ) : (
            <EmptyState title="Data harga belum tersedia untuk saham ini." />
          )}

          <div>
            <div className="flex items-center gap-2 mb-3">
              <History className="size-4 text-blue-400" />
              <h2 className="text-[1.125rem] font-semibold text-text-primary">
                Riwayat Trade dari Backtest
              </h2>
            </div>
            {data.trades.length > 0 ? (
              <TradeHistoryTable trades={data.trades} />
            ) : (
              <EmptyState title="Belum ada trade historis yang tercatat untuk saham ini." />
            )}
          </div>
        </>
      )}
    </div>
  );
}
