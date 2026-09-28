"use client";

import * as React from "react";
import {
  ChevronsLeft,
  ChevronsRight,
  Clock,
  FastForward,
  Info,
  Pause,
  Play,
  RotateCcw,
  SkipBack,
  SkipForward,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface ReplayToolbarProps {
  tickers: string[];
  selectedTicker: string;
  onTickerChange: (ticker: string) => void;
  dates: string[];
  currentIndex: number;
  isPlaying: boolean;
  speed: number;
  onPlayPause: () => void;
  onStepForward: () => void;
  onStepBackward: () => void;
  onNextTrade: () => void;
  onPrevTrade: () => void;
  onSpeedChange: (speed: number) => void;
  onIndexChange: (index: number) => void;
  onResetToLive: () => void;
  onCutToStart: () => void;
  isLive: boolean;
}

const SPEEDS = [
  { label: "0.5x", value: 0.5 },
  { label: "1x", value: 1 },
  { label: "2x", value: 2 },
  { label: "5x", value: 5 },
  { label: "10x", value: 10 },
];

export function ReplayToolbar({
  tickers,
  selectedTicker,
  onTickerChange,
  dates,
  currentIndex,
  isPlaying,
  speed,
  onPlayPause,
  onStepForward,
  onStepBackward,
  onNextTrade,
  onPrevTrade,
  onSpeedChange,
  onIndexChange,
  onResetToLive,
  onCutToStart,
  isLive,
}: ReplayToolbarProps) {
  const totalBars = dates.length;
  const progressPct = totalBars > 0 ? Math.round(((currentIndex + 1) / totalBars) * 100) : 0;

  const tickerOptions = React.useMemo(
    () => tickers.map((t) => ({ value: t, label: t })),
    [tickers],
  );

  return (
    <TooltipProvider delayDuration={150}>
      <div className="flex flex-col gap-2.5 rounded-xl border border-border/80 bg-surface-1/90 p-3 shadow-md backdrop-blur-md">
        {/* Baris Atas: Pemilih Emiten & Tombol Kontrol Playback Utama */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          {/* Sisi Kiri: Dropdown Pemilih Emiten */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-text-muted">Emiten:</span>
            <div className="w-28">
              <Select
                value={selectedTicker}
                onValueChange={onTickerChange}
                options={tickerOptions}
                searchable
                searchPlaceholder="Cari..."
                placeholder="Pilih Saham"
                triggerClassName="h-8 font-mono text-xs font-bold bg-surface-0 shadow-sm hover:border-brand/50"
              />
            </div>

            {/* Tombol Cut Bar / Mulai Replay */}
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={onCutToStart}
                  className="h-8 gap-1.5 border-border/70 bg-surface-0 px-2.5 text-xs text-text-secondary hover:text-text-primary hover:border-brand/40 shadow-sm cursor-pointer"
                >
                  <Clock className="size-3.5 text-indigo-400" />
                  <span className="hidden sm:inline">Mulai Replay</span>
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="text-xs">
                Potong lilin ke 2 tahun lalu untuk mulai memutar simulasi
              </TooltipContent>
            </Tooltip>
          </div>

          {/* Sisi Tengah: Kontrol Navigasi Lilin (Prev Trade, Step Back, Play/Pause, Step Forward, Next Trade) */}
          <div className="flex items-center gap-1.5 rounded-lg border border-border/60 bg-surface-0/70 p-1 shadow-inner">
            {/* Prev Trade */}
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="size-7 text-text-secondary hover:bg-surface-2 hover:text-text-primary cursor-pointer"
                  onClick={onPrevTrade}
                >
                  <ChevronsLeft className="size-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="text-xs">
                Trade Sebelumnya
              </TooltipContent>
            </Tooltip>

            {/* Step Backward 1 Bar */}
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="size-7 text-text-secondary hover:bg-surface-2 hover:text-text-primary cursor-pointer"
                  onClick={onStepBackward}
                  disabled={currentIndex <= 0}
                >
                  <SkipBack className="size-3.5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="text-xs">
                Mundur 1 Lilin (← Arrow Left)
              </TooltipContent>
            </Tooltip>

            {/* Play / Pause Utama */}
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  size="icon"
                  className={`size-8 rounded-md font-bold shadow-md transition-all duration-200 cursor-pointer ${
                    isPlaying
                      ? "bg-amber-500 text-slate-950 hover:bg-amber-400"
                      : "bg-brand text-white hover:bg-brand/90 hover:shadow-brand/20 hover:scale-105"
                  }`}
                  onClick={onPlayPause}
                >
                  {isPlaying ? <Pause className="size-4" /> : <Play className="size-4 ml-0.5" />}
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="text-xs">
                {isPlaying ? "Jeda Replay (Space)" : "Putar Replay (Space)"}
              </TooltipContent>
            </Tooltip>

            {/* Step Forward 1 Bar */}
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="size-7 text-text-secondary hover:bg-surface-2 hover:text-text-primary cursor-pointer"
                  onClick={onStepForward}
                  disabled={currentIndex >= totalBars - 1}
                >
                  <SkipForward className="size-3.5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="text-xs">
                Maju 1 Lilin (→ Arrow Right)
              </TooltipContent>
            </Tooltip>

            {/* Next Trade */}
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="size-7 text-text-secondary hover:bg-surface-2 hover:text-text-primary cursor-pointer"
                  onClick={onNextTrade}
                >
                  <ChevronsRight className="size-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="text-xs">
                Trade Berikutnya
              </TooltipContent>
            </Tooltip>
          </div>

          {/* Sisi Kanan: Pengatur Kecepatan & Tombol Reset ke Live */}
          <div className="flex items-center gap-2">
            {/* Speed Selector Pills */}
            <div className="flex items-center rounded-lg border border-border/70 bg-surface-0/80 p-0.5 text-xs">
              <span className="hidden sm:inline px-1.5 text-[10px] text-text-muted">Kecepatan:</span>
              {SPEEDS.map((s) => (
                <button
                  key={s.value}
                  type="button"
                  onClick={() => onSpeedChange(s.value)}
                  className={`rounded px-1.5 py-0.5 font-mono text-[11px] font-semibold transition-colors cursor-pointer ${
                    speed === s.value
                      ? "bg-brand text-white shadow-xs"
                      : "text-text-secondary hover:text-text-primary"
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>

            {/* Reset to Live */}
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={onResetToLive}
                  disabled={isLive}
                  className="h-8 gap-1.5 px-2 text-xs text-text-secondary hover:text-text-primary disabled:opacity-40 cursor-pointer"
                >
                  <RotateCcw className="size-3.5" />
                  <span className="hidden md:inline">Lompat ke Live</span>
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom" className="text-xs">
                Kembalikan chart ke lilin hari bursa terbaru
              </TooltipContent>
            </Tooltip>
          </div>
        </div>

        {/* Baris Bawah: Timeline Scrubber Slider */}
        <div className="flex items-center gap-3 pt-1">
          <div className="flex-1">
            <Slider
              value={[currentIndex]}
              min={0}
              max={Math.max(0, totalBars - 1)}
              step={1}
              onValueChange={([val]) => onIndexChange(val)}
              className="cursor-pointer"
            />
          </div>

          {/* Label Bar Progress */}
          <div className="flex shrink-0 items-center gap-2 font-mono text-[11.5px] text-text-secondary">
            <span>
              Bar <strong className="text-text-primary">{currentIndex + 1}</strong> / {totalBars}
            </span>
            <span className="text-border">|</span>
            <span className="w-10 text-right text-brand font-semibold">{progressPct}%</span>
          </div>
        </div>
      </div>
    </TooltipProvider>
  );
}
