"use client";

import * as React from "react";

import { PageHeader } from "@/components/shared/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Skeleton } from "@/components/ui/skeleton";
import { IndicatorPicker } from "@/components/backtest/indicator-picker";
import { ParamPanel } from "@/components/backtest/param-panel";
import { BacktestResult } from "@/components/backtest/backtest-result";
import { useIndicatorsMeta, useTickersMeta } from "@/hooks/use-meta";
import { useRunBacktest } from "@/hooks/use-backtest";
import type { IndicatorSpec } from "@/lib/types";

const PERIOD_OPTIONS = [
  { value: "1y", label: "1 Tahun" },
  { value: "2y", label: "2 Tahun" },
  { value: "3y", label: "3 Tahun" },
  { value: "5y", label: "5 Tahun (maks)" },
] as const;

type Period = (typeof PERIOD_OPTIONS)[number]["value"];

export default function BacktestPage() {
  const { data: indicatorsMeta, isLoading: loadingIndicators } = useIndicatorsMeta();
  const { data: tickersMeta } = useTickersMeta();
  const runBacktest = useRunBacktest();

  const allTickers = React.useMemo(
    () => (tickersMeta ? Array.from(new Set(Object.values(tickersMeta.sectors).flat())).sort() : []),
    [tickersMeta],
  );

  const [ticker, setTicker] = React.useState("BBCA");
  const [period, setPeriod] = React.useState<Period>("5y");
  const [selected, setSelected] = React.useState<string[]>([]);
  const [params, setParams] = React.useState<Record<string, Record<string, number>>>({});
  const [confirmationThreshold, setConfirmationThreshold] = React.useState(1);
  const [tpMult, setTpMult] = React.useState(2.0);
  const [slMult, setSlMult] = React.useState(1.0);
  const [maxHold, setMaxHold] = React.useState(20);
  const [playbackDate, setPlaybackDate] = React.useState<string | null>(null);

  // Ticker efektif diturunkan langsung saat render (bukan disinkronkan lewat
  // effect + setState) -- kalau ticker default belum ada di universe (mis.
  // "BBCA" sebelum tickersMeta selesai fetch), pakai ticker pertama yg valid.
  const effectiveTicker = allTickers.length > 0 && !allTickers.includes(ticker) ? allTickers[0] : ticker;

  const maxIndicators = indicatorsMeta?.max_indicators_selected ?? 8;

  const indicatorsByCategory = React.useMemo<Record<string, IndicatorSpec[]>>(() => {
    const map: Record<string, IndicatorSpec[]> = {};
    for (const ind of indicatorsMeta?.indicators ?? []) {
      (map[ind.category] ??= []).push(ind);
    }
    return map;
  }, [indicatorsMeta]);

  const selectedSpecs = (indicatorsMeta?.indicators ?? []).filter((i) => selected.includes(i.key));

  function toggleIndicator(key: string) {
    setSelected((prev) => {
      if (prev.includes(key)) {
        const next = prev.filter((k) => k !== key);
        setConfirmationThreshold((t) => Math.min(t, Math.max(1, next.length)));
        return next;
      }
      if (prev.length >= maxIndicators) return prev;
      return [...prev, key];
    });
  }

  function updateParam(indicatorKey: string, paramName: string, value: number) {
    setParams((prev) => ({ ...prev, [indicatorKey]: { ...(prev[indicatorKey] ?? {}), [paramName]: value } }));
  }

  function handleSubmit() {
    if (selected.length === 0) return;
    setPlaybackDate(null);
    runBacktest.mutate({
      ticker: effectiveTicker,
      period,
      selected_indicators: selected,
      params,
      confirmation_threshold: confirmationThreshold,
      tp_multiple: tpMult,
      sl_multiple: slMult,
      max_hold_days: maxHold,
    });
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="🧪 Backtest Lab"
        description="Coba kombinasi indikator sendiri & lihat bagaimana strategi itu tampil di data historis — lengkap dengan replay, indikator, dan posisi entry/exit."
      />

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="ticker-select">Pilih saham</Label>
          <select
            id="ticker-select"
            value={effectiveTicker}
            onChange={(e) => setTicker(e.target.value)}
            className="rounded-md border border-border bg-surface-1 px-3 py-1.5 font-mono text-[13px] text-text-primary"
          >
            {allTickers.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="period-select">Periode</Label>
          <select
            id="period-select"
            value={period}
            onChange={(e) => setPeriod(e.target.value as Period)}
            className="rounded-md border border-border bg-surface-1 px-3 py-1.5 text-[13px] text-text-primary"
          >
            {PERIOD_OPTIONS.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <h2 className="mb-3 text-[1.125rem] font-semibold text-text-primary">1️⃣ Pilih Indikator</h2>
        {loadingIndicators ? (
          <Skeleton className="h-40 rounded-lg" />
        ) : (
          <IndicatorPicker
            categories={indicatorsMeta?.categories ?? []}
            indicatorsByCategory={indicatorsByCategory}
            selected={selected}
            onToggle={toggleIndicator}
            maxSelected={maxIndicators}
          />
        )}
        {selected.length > 0 && (
          <div className="mt-3">
            <p className="mb-2 text-[12.5px] text-text-secondary">
              <strong className="text-text-primary">{selected.length} indikator dipilih</strong> — atur
              parameter tiap indikator (opsional):
            </p>
            <ParamPanel specs={selectedSpecs} params={params} onChange={updateParam} />
          </div>
        )}
        {!loadingIndicators && selected.length === 0 && (
          <p className="mt-3 text-[12.5px] text-text-muted">
            Pilih minimal 1 indikator di atas untuk melanjutkan.
          </p>
        )}
      </div>

      <div>
        <h2 className="mb-3 text-[1.125rem] font-semibold text-text-primary">
          2️⃣ Aturan Sinyal &amp; Manajemen Risiko
        </h2>
        <div className="flex flex-col gap-4 rounded-lg border border-border bg-surface-1 p-4">
          {selected.length >= 2 ? (
            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <Label>Minimal Konfirmasi (jumlah indikator yang harus sepakat)</Label>
                <span className="font-mono text-[13px] text-text-primary">{confirmationThreshold}</span>
              </div>
              <Slider
                value={[confirmationThreshold]}
                onValueChange={([v]) => setConfirmationThreshold(v)}
                min={1}
                max={selected.length}
                step={1}
              />
            </div>
          ) : (
            <p className="text-[12.5px] text-text-muted">
              Minimal Konfirmasi: <span className="font-mono text-text-secondary">1</span> — pilih minimal
              2 indikator di atas untuk mengatur seberapa banyak yang harus sepakat.
            </p>
          )}

          <div className="grid gap-4 sm:grid-cols-3">
            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <Label>Take Profit (× ATR)</Label>
                <span className="font-mono text-[13px] text-text-primary">{tpMult.toFixed(1)}×</span>
              </div>
              <Slider value={[tpMult]} onValueChange={([v]) => setTpMult(v)} min={1} max={5} step={0.5} />
            </div>
            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <Label>Stop Loss (× ATR)</Label>
                <span className="font-mono text-[13px] text-text-primary">{slMult.toFixed(1)}×</span>
              </div>
              <Slider value={[slMult]} onValueChange={([v]) => setSlMult(v)} min={0.5} max={3} step={0.5} />
            </div>
            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <Label>Maks Hari Holding</Label>
                <span className="font-mono text-[13px] text-text-primary">{maxHold}</span>
              </div>
              <Slider value={[maxHold]} onValueChange={([v]) => setMaxHold(v)} min={5} max={60} step={5} />
            </div>
          </div>

          <Button type="button" onClick={handleSubmit} disabled={selected.length === 0 || runBacktest.isPending}>
            {runBacktest.isPending ? "Menjalankan..." : "🚀 Jalankan Backtest"}
          </Button>
        </div>
      </div>

      {runBacktest.isError && (
        <EmptyState
          title="Backtest gagal dijalankan"
          description={runBacktest.error instanceof Error ? runBacktest.error.message : "Coba lagi."}
        />
      )}

      {runBacktest.data && (
        <BacktestResult result={runBacktest.data} playbackDate={playbackDate} onPlaybackDateChange={setPlaybackDate} />
      )}
    </div>
  );
}
