"use client";

import * as React from "react";
import {
  Activity,
  Calendar,
  Clock,
  TrendingDown,
  TrendingUp,
  Wallet,
  Zap,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { formatIdr, formatNumberId, formatPctId } from "@/lib/format";
import type { ReplayCumulativeMetrics, ReplayPositionState } from "@/lib/types";

interface ReplayHudProps {
  ticker: string;
  playbackDate: string | null;
  positionState: ReplayPositionState;
  metrics: ReplayCumulativeMetrics;
  isLive: boolean;
}

export function ReplayHud({
  ticker,
  playbackDate,
  positionState,
  metrics,
  isLive,
}: ReplayHudProps) {
  const isHolding = positionState.status === "HOLDING";
  const floatingPnL = positionState.floatingPnL ?? 0;
  const isProfit = floatingPnL >= 0;

  return (
    <div className="flex flex-col gap-3 rounded-xl border border-border/80 bg-surface-1/90 p-3.5 shadow-md backdrop-blur-md transition-all duration-200">
      {/* Baris Atas: Tanggal Playback, Status Mode, dan Status Posisi Aktif */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 pb-2.5">
        <div className="flex items-center gap-2">
          <div className="flex size-7 items-center justify-center rounded-lg bg-brand/10 text-brand">
            <Calendar className="size-4" />
          </div>
          <div>
            <div className="text-[10.5px] font-medium tracking-wide text-text-muted uppercase">
              Tanggal Lilin Playback
            </div>
            <div className="font-mono text-xs font-semibold text-text-primary">
              {playbackDate ?? "–"}
            </div>
          </div>

          <Badge
            variant="outline"
            className={`ml-2 font-mono text-[10px] tracking-wider uppercase ${
              isLive
                ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-400"
                : "border-indigo-500/40 bg-indigo-500/10 text-indigo-400"
            }`}
          >
            {isLive ? "● LIVE BAR" : "⚡ REPLAY MODE"}
          </Badge>
        </div>

        {/* Status Posisi Trading */}
        <div className="flex items-center gap-2">
          {isHolding ? (
            <div className="flex items-center gap-2 rounded-lg border border-emerald-500/30 bg-emerald-950/20 px-3 py-1 text-xs">
              <span className="relative flex size-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex size-2 rounded-full bg-emerald-500" />
              </span>
              <span className="font-mono text-xs font-bold text-emerald-400">
                HOLDING {ticker}
              </span>
              <span className="text-border">|</span>
              <span className="text-[11px] text-text-secondary">
                Entry: <strong className="font-mono text-text-primary">{formatIdr(positionState.entryPrice)}</strong>
              </span>
              <span className="text-border">|</span>
              <span className="text-[11px] text-text-secondary">
                Close: <strong className="font-mono text-text-primary">{formatIdr(positionState.currentClose)}</strong>
              </span>
              <span className="text-border">|</span>
              <div
                className={`flex items-center gap-1 font-mono text-xs font-bold ${
                  isProfit ? "text-emerald-400" : "text-rose-400"
                }`}
              >
                {isProfit ? <TrendingUp className="size-3.5" /> : <TrendingDown className="size-3.5" />}
                <span>Floating: {formatPctId(floatingPnL)}</span>
              </div>
              <span className="text-border">|</span>
              <span className="flex items-center gap-1 text-[11px] text-text-secondary">
                <Clock className="size-3 text-text-muted" />
                <span>{positionState.holdDaysElapsed} Hari</span>
              </span>
            </div>
          ) : (
            <div className="flex items-center gap-2 rounded-lg border border-border/70 bg-surface-2/60 px-3 py-1 text-xs text-text-secondary">
              <span className="size-2 rounded-full bg-slate-500" />
              <span className="font-mono text-xs font-semibold text-text-muted">
                FLAT (CASH)
              </span>
              <span className="hidden sm:inline text-[11px] text-text-muted">
                — Menunggu sinyal konfirmasi valid
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Baris Bawah: Metrik Kumulatif Real-Time hingga Lilin Ini */}
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-4">
        {/* Metrik 1: Trade Selesai */}
        <div className="flex items-center gap-2.5 rounded-lg border border-border/40 bg-surface-2/50 px-3 py-2">
          <div className="flex size-7 shrink-0 items-center justify-center rounded-md bg-surface-3 text-text-secondary">
            <Activity className="size-3.5" />
          </div>
          <div className="min-w-0">
            <div className="truncate text-[10.5px] text-text-muted">Trade Selesai</div>
            <div className="font-mono text-[13px] font-semibold text-text-primary">
              {metrics.totalTrades} <span className="text-[11px] font-normal text-text-muted">posisi</span>
            </div>
          </div>
        </div>

        {/* Metrik 2: Winrate Kumulatif */}
        <div className="flex items-center gap-2.5 rounded-lg border border-border/40 bg-surface-2/50 px-3 py-2">
          <div className="flex size-7 shrink-0 items-center justify-center rounded-md bg-surface-3 text-text-secondary">
            <Zap className="size-3.5" />
          </div>
          <div className="min-w-0">
            <div className="truncate text-[10.5px] text-text-muted">Winrate Berjalan</div>
            <div
              className={`font-mono text-[13px] font-semibold ${
                (metrics.winrate ?? 0) >= 50 ? "text-emerald-400" : "text-text-primary"
              }`}
            >
              {metrics.winrate != null ? `${formatNumberId(metrics.winrate, 1)}%` : "–"}
            </div>
          </div>
        </div>

        {/* Metrik 3: Realized Return Kumulatif */}
        <div className="flex items-center gap-2.5 rounded-lg border border-border/40 bg-surface-2/50 px-3 py-2">
          <div className="flex size-7 shrink-0 items-center justify-center rounded-md bg-surface-3 text-text-secondary">
            <TrendingUp className="size-3.5" />
          </div>
          <div className="min-w-0">
            <div className="truncate text-[10.5px] text-text-muted">Realized PnL</div>
            <div
              className={`font-mono text-[13px] font-semibold ${
                metrics.realizedReturnPct >= 0 ? "text-emerald-400" : "text-rose-400"
              }`}
            >
              {formatPctId(metrics.realizedReturnPct)}
            </div>
          </div>
        </div>

        {/* Metrik 4: Indeks Modal Simulasi */}
        <div className="flex items-center gap-2.5 rounded-lg border border-border/40 bg-surface-2/50 px-3 py-2">
          <div className="flex size-7 shrink-0 items-center justify-center rounded-md bg-surface-3 text-text-secondary">
            <Wallet className="size-3.5" />
          </div>
          <div className="min-w-0">
            <div className="truncate text-[10.5px] text-text-muted">Simulasi Ekuitas</div>
            <div className="font-mono text-[13px] font-semibold text-text-primary">
              {formatNumberId(100 + metrics.realizedReturnPct + (isHolding ? floatingPnL : 0), 1)}%
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
