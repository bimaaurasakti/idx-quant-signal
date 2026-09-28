"use client";

import * as React from "react";
import {
  BarChart3,
  FlaskConical,
  Keyboard,
  Layers,
  Sparkles,
  TrendingUp,
} from "lucide-react";

import { BacktestChart } from "@/components/backtest/backtest-chart";
import { EquityCurveChart } from "@/components/backtest/equity-curve-chart";
import { ReplayHud } from "@/components/backtest/replay-hud";
import { ReplayToolbar } from "@/components/backtest/replay-toolbar";
import { ReplayTradesTable } from "@/components/backtest/replay-trades-table";
import { PageHeader } from "@/components/shared/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/lib/api";
import type {
  PriceBar,
  ReplayCumulativeMetrics,
  ReplayPositionState,
  TradeRow,
} from "@/lib/types";

const DEFAULT_TICKERS = [
  "BBCA",
  "BBRI",
  "BMRI",
  "TLKM",
  "ASII",
  "BBNI",
  "ICBP",
  "UNTR",
  "ADRO",
  "KLBF",
];

export default function BacktestPage() {
  const [tickers, setTickers] = React.useState<string[]>(DEFAULT_TICKERS);
  const [selectedTicker, setSelectedTicker] = React.useState<string>("BBCA");
  const [loading, setLoading] = React.useState<boolean>(true);
  const [bars, setBars] = React.useState<PriceBar[]>([]);
  const [trades, setTrades] = React.useState<TradeRow[]>([]);

  // State Replay Engine
  const [currentIndex, setCurrentIndex] = React.useState<number>(0);
  const [isPlaying, setIsPlaying] = React.useState<boolean>(false);
  const [speed, setSpeed] = React.useState<number>(1);

  // 1. Muat Daftar Ticker Saham pada Mount
  React.useEffect(() => {
    let active = true;
    async function loadMeta() {
      try {
        const meta = await api.metaTickers();
        if (!active) return;
        const allTickers = Array.from(
          new Set(Object.values(meta.sectors).flat().concat(meta.idx30)),
        ).sort();
        if (allTickers.length > 0) {
          setTickers(allTickers);
        }
      } catch (err) {
        console.error("Gagal memuat meta tickers:", err);
      }
    }
    loadMeta();
    return () => {
      active = false;
    };
  }, []);

  // 2. Muat Data Lilin Harga & Trade Saham yang Dipilih
  React.useEffect(() => {
    let active = true;
    async function loadTickerData() {
      setLoading(true);
      setIsPlaying(false);
      try {
        const detail = await api.tickerDetail(selectedTicker);
        if (!active) return;

        const priceBars = detail.price_history ?? [];
        const tradeRows = detail.trades ?? [];

        setBars(priceBars);
        setTrades(tradeRows);

        // Setel titik awal replay ke sekitar 250 lilin terakhir (~1 tahun bursa)
        // agar pengguna memiliki ruang ideal untuk langsung mencoba Play
        if (priceBars.length > 0) {
          const defaultStart = Math.max(0, priceBars.length - 250);
          setCurrentIndex(defaultStart);
        } else {
          setCurrentIndex(0);
        }
      } catch (err) {
        console.error(`Gagal memuat data ticker ${selectedTicker}:`, err);
      } finally {
        if (active) setLoading(false);
      }
    }

    loadTickerData();
    return () => {
      active = false;
    };
  }, [selectedTicker]);

  // 3. Playback Interval Loop saat isPlaying = true
  React.useEffect(() => {
    if (!isPlaying || bars.length === 0) return;

    const intervalMs =
      speed === 0.5 ? 800 : speed === 1 ? 400 : speed === 2 ? 200 : speed === 5 ? 80 : 40;

    const id = setInterval(() => {
      setCurrentIndex((prev) => {
        if (prev >= bars.length - 1) {
          setIsPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, intervalMs);

    return () => clearInterval(id);
  }, [isPlaying, speed, bars.length]);

  // 4. Kalkulasi Live Replay State & Posisi Berjalan pada currentIndex
  const currentBar = bars[currentIndex];
  const currentDate = currentBar?.date ?? null;
  const isLive = currentIndex === bars.length - 1;

  const positionState: ReplayPositionState = React.useMemo(() => {
    if (!currentDate || !currentBar) {
      return {
        status: "FLAT",
        trade: null,
        floatingPnL: null,
        entryPrice: null,
        currentClose: 0,
        holdDaysElapsed: 0,
      };
    }

    // Cari apakah ada trade yang sedang terbuka pada lilin saat ini
    const activeTrade = trades.find(
      (t) => t.entry_date <= currentDate && t.exit_date > currentDate,
    );

    if (activeTrade) {
      const entryPrice = activeTrade.entry_price;
      const currentClose = currentBar.close ?? currentBar.open ?? entryPrice;
      const floatingPnL = ((currentClose - entryPrice) / entryPrice) * 100;

      // Hitung durasi hari bursa yang telah berjalan
      const holdIndex = bars.findIndex((b) => b.date === activeTrade.entry_date);
      const holdDaysElapsed = holdIndex >= 0 ? Math.max(1, currentIndex - holdIndex + 1) : 1;

      return {
        status: "HOLDING",
        trade: activeTrade,
        floatingPnL,
        entryPrice,
        currentClose,
        holdDaysElapsed,
      };
    }

    return {
      status: "FLAT",
      trade: null,
      floatingPnL: null,
      entryPrice: null,
      currentClose: currentBar.close ?? 0,
      holdDaysElapsed: 0,
    };
  }, [bars, trades, currentIndex, currentDate, currentBar]);

  // 5. Kalkulasi Metrik Kumulatif dari Trade yang Sudah Selesai (Closed) hingga currentDate
  const { closedTrades, cumulativeMetrics } = React.useMemo(() => {
    if (!currentDate) {
      return {
        closedTrades: [],
        cumulativeMetrics: {
          totalTrades: 0,
          closedTrades: [],
          winrate: null,
          realizedReturnPct: 0,
          equityPoints: [],
        },
      };
    }

    const closed = trades.filter((t) => t.exit_date <= currentDate);
    const totalTrades = closed.length;
    const wins = closed.filter((t) => t.return_pct > 0).length;
    const winrate = totalTrades > 0 ? (wins / totalTrades) * 100 : null;
    const realizedReturnPct = closed.reduce((acc, t) => acc + t.return_pct, 0);

    const metrics: ReplayCumulativeMetrics = {
      totalTrades,
      closedTrades: closed,
      winrate,
      realizedReturnPct,
      equityPoints: [],
    };

    return { closedTrades: closed, cumulativeMetrics: metrics };
  }, [trades, currentDate]);

  // 6. Action Handlers Navigasi Replay
  const handlePlayPause = React.useCallback(() => {
    if (currentIndex >= bars.length - 1) {
      // Jika sudah di ujung, ulangi dari 250 lilin sebelumnya
      setCurrentIndex(Math.max(0, bars.length - 250));
      setIsPlaying(true);
    } else {
      setIsPlaying((prev) => !prev);
    }
  }, [currentIndex, bars.length]);

  const handleStepForward = React.useCallback(() => {
    setIsPlaying(false);
    setCurrentIndex((prev) => Math.min(bars.length - 1, prev + 1));
  }, [bars.length]);

  const handleStepBackward = React.useCallback(() => {
    setIsPlaying(false);
    setCurrentIndex((prev) => Math.max(0, prev - 1));
  }, []);

  const handleNextTrade = React.useCallback(() => {
    setIsPlaying(false);
    if (!currentDate) return;
    const nextTrade = trades.find((t) => t.entry_date > currentDate);
    if (nextTrade) {
      const targetIdx = bars.findIndex((b) => b.date === nextTrade.entry_date);
      if (targetIdx >= 0) setCurrentIndex(targetIdx);
    }
  }, [currentDate, trades, bars]);

  const handlePrevTrade = React.useCallback(() => {
    setIsPlaying(false);
    if (!currentDate) return;
    // Cari trade sebelumnya
    const prevTrades = trades.filter((t) => t.entry_date < currentDate);
    if (prevTrades.length > 0) {
      const prevTrade = prevTrades[prevTrades.length - 1];
      const targetIdx = bars.findIndex((b) => b.date === prevTrade.entry_date);
      if (targetIdx >= 0) setCurrentIndex(targetIdx);
    }
  }, [currentDate, trades, bars]);

  const handleCutToStart = React.useCallback(() => {
    setIsPlaying(false);
    // Potong ke ~500 lilin sebelum akhir atau awal dataset
    const startIdx = Math.max(0, bars.length - 500);
    setCurrentIndex(startIdx);
  }, [bars.length]);

  const handleResetToLive = React.useCallback(() => {
    setIsPlaying(false);
    setCurrentIndex(Math.max(0, bars.length - 1));
  }, [bars.length]);

  // 7. Keyboard Shortcuts (Space, ArrowRight, ArrowLeft)
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (
        document.activeElement?.tagName === "INPUT" ||
        document.activeElement?.tagName === "SELECT" ||
        document.activeElement?.tagName === "TEXTAREA"
      ) {
        return;
      }

      if (e.code === "Space") {
        e.preventDefault();
        handlePlayPause();
      } else if (e.code === "ArrowRight") {
        e.preventDefault();
        handleStepForward();
      } else if (e.code === "ArrowLeft") {
        e.preventDefault();
        handleStepBackward();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handlePlayPause, handleStepForward, handleStepBackward]);

  const dateList = React.useMemo(() => bars.map((b) => b.date), [bars]);

  return (
    <div className="flex flex-col gap-6">
      {/* Header Halaman */}
      <PageHeader
        title="Backtest Lab — TradingView Bar Replay"
        description="Simulasi interaktif pergerakan harga lilin demi lilin tanpa bias masa depan. Putar replay untuk menguji strategi dan melihat eksekusi posisi secara real-time."
      />

      {loading ? (
        <div className="flex flex-col gap-4">
          <Skeleton className="h-16 w-full rounded-xl bg-surface-1" />
          <Skeleton className="h-24 w-full rounded-xl bg-surface-1" />
          <Skeleton className="h-[820px] w-full rounded-xl bg-surface-1" />
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {/* Replay Toolbar Utama */}
          <ReplayToolbar
            tickers={tickers}
            selectedTicker={selectedTicker}
            onTickerChange={setSelectedTicker}
            dates={dateList}
            currentIndex={currentIndex}
            isPlaying={isPlaying}
            speed={speed}
            onPlayPause={handlePlayPause}
            onStepForward={handleStepForward}
            onStepBackward={handleStepBackward}
            onNextTrade={handleNextTrade}
            onPrevTrade={handlePrevTrade}
            onSpeedChange={setSpeed}
            onIndexChange={(idx) => {
              setIsPlaying(false);
              setCurrentIndex(idx);
            }}
            onCutToStart={handleCutToStart}
            onResetToLive={handleResetToLive}
            isLive={isLive}
          />

          {/* Replay HUD: Status Posisi Aktif & Metrik Real-Time */}
          <ReplayHud
            ticker={selectedTicker}
            playbackDate={currentDate}
            positionState={positionState}
            metrics={cumulativeMetrics}
            isLive={isLive}
          />

          {/* Chart TradingView 3-Pane Simetris dengan True Cut-Off */}
          <div className="relative overflow-hidden rounded-xl border border-border bg-surface-0 shadow-md">
            <BacktestChart
              bars={bars}
              currentIndex={currentIndex}
              trades={trades}
              height={820}
            />

            {/* Hint Keyboard Shortcuts di Pojok Bawah */}
            <div className="pointer-events-none absolute bottom-2 left-3 z-20 hidden sm:flex items-center gap-2 rounded-md border border-border/60 bg-surface-1/80 px-2 py-1 text-[10.5px] text-text-muted backdrop-blur-xs">
              <Keyboard className="size-3" />
              <span>Space = Play/Pause</span>
              <span>•</span>
              <span>→ = Step Forward</span>
              <span>•</span>
              <span>← = Step Back</span>
            </div>
          </div>

          {/* Section Bawah: Tab Riwayat Trade Selesai & Live Equity Curve */}
          <Tabs defaultValue="trades" className="mt-2 flex flex-col gap-3">
            <div className="flex items-center justify-between border-b border-border/60 pb-2">
              <TabsList className="bg-surface-1 border border-border/70 p-1">
                <TabsTrigger value="trades" className="gap-1.5 text-xs">
                  <Layers className="size-3.5" />
                  <span>Riwayat Trade Selesai ({closedTrades.length})</span>
                </TabsTrigger>
                <TabsTrigger value="equity" className="gap-1.5 text-xs">
                  <TrendingUp className="size-3.5" />
                  <span>Live Equity Curve</span>
                </TabsTrigger>
              </TabsList>

              <div className="hidden sm:flex items-center gap-1.5 text-xs text-text-muted">
                <Sparkles className="size-3.5 text-brand" />
                <span>Data ter-update otomatis seiring replay berjalan maju</span>
              </div>
            </div>

            <TabsContent value="trades">
              <ReplayTradesTable trades={closedTrades} ticker={selectedTicker} />
            </TabsContent>

            <TabsContent value="equity">
              <EquityCurveChart trades={closedTrades} />
            </TabsContent>
          </Tabs>

          {/* Catatan Metodologi & Edukasi Strategi */}
          <Card className="border-border bg-surface-1/70">
            <CardContent className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 text-xs">
              <div className="flex items-start gap-3">
                <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-400">
                  <BarChart3 className="size-4" />
                </div>
                <div>
                  <div className="font-semibold text-text-primary text-[13.5px]">
                    Strategi Multi-Konfirmasi 5-Pilar IDX Quant
                  </div>
                  <div className="text-text-secondary mt-0.5 leading-relaxed">
                    Setiap trade entry dan exit pada replay ini merupakan hasil validasi aturan kuantitatif
                    (Market Regime Bullish, Trend EMA200/50, Pullback MA20, RSI Momentum, &amp; Konfirmasi Volume)
                    tanpa intervensi emosional.
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
