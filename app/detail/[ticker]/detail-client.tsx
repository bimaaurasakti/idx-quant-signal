"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import {
  History,
  ShieldCheck,
  CheckCircle2,
  Layers,
  Activity,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  AlertTriangle,
  XCircle,
  Sparkles,
} from "lucide-react";

import { PageHeader } from "@/components/shared/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { MetricCard } from "@/components/shared/metric-card";
import { PriceChart } from "@/components/shared/price-chart";
import { PriceHeader } from "@/components/detail/price-header";
import { PositionStatusBanner } from "@/components/detail/position-status-banner";
import { TradeHistoryTable } from "@/components/detail/trade-history-table";
import { Select, type SelectOption } from "@/components/ui/select";
import { useTickerDetail } from "@/hooks/use-detail";
import { useTickersMeta, useMarketRegime } from "@/hooks/use-meta";
import { formatPctId, formatNumberId } from "@/lib/format";
import { METRIC_TOOLTIP } from "@/lib/constants";

export function DetailClient({ ticker }: { ticker: string }) {
  const router = useRouter();
  const { data, isLoading, isError, error } = useTickerDetail(ticker);
  const { data: tickersMeta } = useTickersMeta();
  const { regime } = useMarketRegime();

  const allTickers = React.useMemo(() => {
    if (!tickersMeta) return [];
    return Array.from(new Set(Object.values(tickersMeta.sectors).flat())).sort();
  }, [tickersMeta]);

  const tickerOptions: SelectOption[] = React.useMemo(
    () => allTickers.map((t) => ({ value: t, label: t })),
    [allTickers],
  );

  const lastBar =
    data?.price_history && data.price_history.length > 0
      ? data.price_history[data.price_history.length - 1]
      : null;

  // 1. Market Regime (IHSG)
  const isMacroBull = regime?.tier === "HIGH_ALPHA";
  const isTactical = regime?.tier === "TACTICAL_SWING";

  // 2. Stage 2 Uptrend
  const close = lastBar?.close ?? null;
  const sma50 = lastBar?.sma50 ?? null;
  const sma200 = lastBar?.sma200 ?? null;
  const isStage2 =
    close != null && sma50 != null && sma200 != null && close > sma50 && sma50 > sma200;
  const isAboveSma50 = close != null && sma50 != null && close > sma50;

  // 3. Momentum MACD
  const macd = lastBar?.macd ?? null;
  const macdSignal = lastBar?.macd_signal ?? null;
  const isMacdBull = macd != null && macdSignal != null && macd > macdSignal;

  // 4. Zona RSI Sehat (40 - 65)
  const rsi = lastBar?.rsi14 ?? null;
  const isRsiOptimal = rsi != null && rsi >= 40 && rsi <= 65;
  const isRsiOverbought = rsi != null && rsi > 65;

  // 5. Anti-FOMO Buffer (Maksimal +5% dari SMA20)
  const sma20 = lastBar?.sma20 ?? null;
  const sma20Dist =
    close != null && sma20 != null && sma20 > 0 ? ((close - sma20) / sma20) * 100 : null;
  const isAntiFomoOk = sma20Dist != null && sma20Dist <= 5;

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Detail Saham"
        description="Analisis teknikal kuantitatif, konfirmasi sinyal momentum, dan riwayat performa per saham."
        action={
          allTickers.length > 0 ? (
            <div className="flex items-center gap-2 justify-end">
              <span className="text-xs text-text-secondary hidden sm:inline shrink-0">Pilih Emiten:</span>
              <div className="w-[140px] sm:w-[160px]">
                <Select
                  value={ticker}
                  onValueChange={(val) => router.push(`/detail/${val}`)}
                  options={tickerOptions}
                  searchable={true}
                  searchPlaceholder="Cari emiten..."
                  placeholder="Pilih emiten"
                  align="end"
                  triggerClassName="w-full h-8 font-mono text-xs font-semibold bg-surface-1"
                />
              </div>
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
          <Skeleton className="h-[820px] rounded-lg" />
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
            hasActivePosition={Boolean(data.active_position && data.active_position.status === "OPEN")}
          />

          {data.active_position && <PositionStatusBanner position={data.active_position} />}

          {/* Status Syarat Strategi (5 Pilar Dinamis) */}
          <div className="flex flex-wrap items-center gap-2.5 rounded-lg border border-border bg-surface-1 px-3.5 py-2.5 text-xs shadow-sm">
            <span className="font-semibold text-text-secondary flex items-center gap-1.5 mr-1 shrink-0">
              <Sparkles className="size-3.5 text-blue-400" />
              Status Syarat Strategi:
            </span>
            <div className="flex flex-wrap items-center gap-2">
              {/* 1. Market Regime */}
              {isMacroBull ? (
                <Badge
                  variant="outline"
                  className="border-emerald-500/30 bg-emerald-500/10 text-emerald-400 text-[11px] gap-1.5 py-0.5"
                >
                  <CheckCircle2 className="size-3.5 text-emerald-400" />
                  <span>Rezim: <strong>Bullish Alpha (100%)</strong></span>
                </Badge>
              ) : isTactical ? (
                <Badge
                  variant="outline"
                  className="border-amber-500/30 bg-amber-500/10 text-amber-400 text-[11px] gap-1.5 py-0.5"
                >
                  <AlertCircle className="size-3.5 text-amber-400" />
                  <span>Rezim: <strong>Taktikal Swing (50%)</strong></span>
                </Badge>
              ) : (
                <Badge
                  variant="outline"
                  className="border-rose-500/30 bg-rose-500/10 text-rose-400 text-[11px] gap-1.5 py-0.5"
                >
                  <XCircle className="size-3.5 text-rose-400" />
                  <span>Rezim: <strong>Defensif (Cash 0%)</strong></span>
                </Badge>
              )}

              {/* 2. Stage 2 Uptrend */}
              {isStage2 ? (
                <Badge
                  variant="outline"
                  className="border-emerald-500/30 bg-emerald-500/10 text-emerald-400 text-[11px] gap-1.5 py-0.5"
                >
                  <ShieldCheck className="size-3.5 text-emerald-400" />
                  <span>Tren: <strong>Stage 2 Uptrend</strong></span>
                </Badge>
              ) : isAboveSma50 ? (
                <Badge
                  variant="outline"
                  className="border-amber-500/30 bg-amber-500/10 text-amber-400 text-[11px] gap-1.5 py-0.5"
                >
                  <ShieldCheck className="size-3.5 text-amber-400" />
                  <span>Tren: <strong>Transisi &gt; SMA50</strong></span>
                </Badge>
              ) : (
                <Badge
                  variant="outline"
                  className="border-rose-500/30 bg-rose-500/10 text-rose-400 text-[11px] gap-1.5 py-0.5"
                >
                  <XCircle className="size-3.5 text-rose-400" />
                  <span>Tren: <strong>Di Bawah SMA50</strong></span>
                </Badge>
              )}

              {/* 3. Momentum MACD */}
              {isMacdBull ? (
                <Badge
                  variant="outline"
                  className="border-emerald-500/30 bg-emerald-500/10 text-emerald-400 text-[11px] gap-1.5 py-0.5"
                >
                  <TrendingUp className="size-3.5 text-emerald-400" />
                  <span>MACD: <strong>Bullish Cross</strong></span>
                </Badge>
              ) : macd != null && macdSignal != null ? (
                <Badge
                  variant="outline"
                  className="border-rose-500/30 bg-rose-500/10 text-rose-400 text-[11px] gap-1.5 py-0.5"
                >
                  <TrendingDown className="size-3.5 text-rose-400" />
                  <span>MACD: <strong>Bearish / Cross Down</strong></span>
                </Badge>
              ) : (
                <Badge
                  variant="outline"
                  className="border-border bg-surface-0 text-text-secondary text-[11px] gap-1.5 py-0.5"
                >
                  <Activity className="size-3.5 text-text-muted" />
                  <span>MACD: <strong>N/A</strong></span>
                </Badge>
              )}

              {/* 4. Zona RSI Sehat */}
              {isRsiOptimal ? (
                <Badge
                  variant="outline"
                  className="border-emerald-500/30 bg-emerald-500/10 text-emerald-400 text-[11px] gap-1.5 py-0.5"
                >
                  <Activity className="size-3.5 text-emerald-400" />
                  <span>RSI: <strong>{rsi?.toFixed(1)} (Zona Sehat 40-65)</strong></span>
                </Badge>
              ) : isRsiOverbought ? (
                <Badge
                  variant="outline"
                  className="border-amber-500/30 bg-amber-500/10 text-amber-400 text-[11px] gap-1.5 py-0.5"
                >
                  <AlertTriangle className="size-3.5 text-amber-400" />
                  <span>RSI: <strong>{rsi?.toFixed(1)} (Overbought &gt; 65)</strong></span>
                </Badge>
              ) : rsi != null ? (
                <Badge
                  variant="outline"
                  className="border-rose-500/30 bg-rose-500/10 text-rose-400 text-[11px] gap-1.5 py-0.5"
                >
                  <AlertCircle className="size-3.5 text-rose-400" />
                  <span>RSI: <strong>{rsi?.toFixed(1)} (Lemah &lt; 40)</strong></span>
                </Badge>
              ) : (
                <Badge
                  variant="outline"
                  className="border-border bg-surface-0 text-text-secondary text-[11px] gap-1.5 py-0.5"
                >
                  <Activity className="size-3.5 text-text-muted" />
                  <span>RSI: <strong>N/A</strong></span>
                </Badge>
              )}

              {/* 5. Anti-FOMO Buffer */}
              {isAntiFomoOk ? (
                <Badge
                  variant="outline"
                  className="border-emerald-500/30 bg-emerald-500/10 text-emerald-400 text-[11px] gap-1.5 py-0.5"
                >
                  <Layers className="size-3.5 text-emerald-400" />
                  <span>Anti-FOMO: <strong>Aman ({sma20Dist != null && sma20Dist >= 0 ? "+" : ""}{sma20Dist?.toFixed(1)}% SMA20)</strong></span>
                </Badge>
              ) : sma20Dist != null ? (
                <Badge
                  variant="outline"
                  className="border-amber-500/30 bg-amber-500/10 text-amber-400 text-[11px] gap-1.5 py-0.5"
                >
                  <AlertTriangle className="size-3.5 text-amber-400" />
                  <span>Anti-FOMO: <strong>Overextended (+{sma20Dist?.toFixed(1)}% SMA20)</strong></span>
                </Badge>
              ) : (
                <Badge
                  variant="outline"
                  className="border-border bg-surface-0 text-text-secondary text-[11px] gap-1.5 py-0.5"
                >
                  <Layers className="size-3.5 text-text-muted" />
                  <span>Anti-FOMO: <strong>N/A</strong></span>
                </Badge>
              )}
            </div>
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
            <PriceChart
              bars={data.price_history}
              trades={data.trades}
              activePosition={data.active_position}
              ticker={ticker}
              lastClose={data.last_close}
              height={820}
            />
          ) : (
            <EmptyState title="Data harga belum tersedia untuk saham ini." />
          )}

          <div>
            <div className="flex items-center gap-2 mb-3">
              <History className="size-4 text-blue-400" />
              <h2 className="text-[1.125rem] font-semibold text-text-primary">
                Riwayat Posisi
              </h2>
            </div>
            {data.trades.length > 0 ? (
              <TradeHistoryTable trades={data.trades} />
            ) : (
              <EmptyState title="Belum ada riwayat posisi yang tercatat untuk saham ini." />
            )}
          </div>
        </>
      )}
    </div>
  );
}
