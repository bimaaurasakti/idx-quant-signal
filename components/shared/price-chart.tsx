"use client";

import * as React from "react";
import {
  createChart,
  CandlestickSeries,
  LineSeries,
  HistogramSeries,
  createSeriesMarkers,
  ColorType,
  CrosshairMode,
  LineStyle,
  type IChartApi,
  type ISeriesMarkersPluginApi,
  type SeriesMarker,
  type Time,
} from "lightweight-charts";
import { Info, TrendingUp, TrendingDown, Clock, ShieldAlert, Target, Sparkles, CheckCircle2 } from "lucide-react";

import type { PriceBar, TradeRow, ActivePosition } from "@/lib/types";
import { formatIdr, formatPctId } from "@/lib/format";
import { Badge } from "@/components/ui/badge";

export interface PriceChartProps {
  bars: PriceBar[];
  trades?: TradeRow[];
  activePosition?: ActivePosition | null;
  ticker?: string;
  lastClose?: number | null;
  height?: number;
}

export interface PairedTradeItem {
  id: string;
  entryDate: string;
  exitDate?: string | null;
  entryPrice: number;
  exitPrice?: number | null;
  returnPct?: number | null;
  reason?: string | null;
  holdDays?: number | null;
  isOpen: boolean;
}

function formatExitReason(reason?: string | null): string {
  if (!reason) return "Exit Posisi";
  switch (reason) {
    case "TP":
    case "CLOSED_TP":
    case "CLOSED_TP1_BE":
      return "Take Profit / Trailing Stop";
    case "SL":
    case "CLOSED_SL":
      return "Stop Loss (SL)";
    case "SELL_SIGNAL":
    case "CLOSED_SIGNAL":
      return "Pembalikan Tren (MACD Death Cross)";
    case "CLOSED_RUNNER_SMA20":
      return "Trailing Stop SMA20 Break";
    case "TIME_EXIT":
    case "CLOSED_TIME":
      return "Batas Waktu Hold";
    default:
      return reason.replace("CLOSED_", "").replace(/_/g, " ");
  }
}

function normalizeTime(time: Time | unknown): string {
  if (!time) return "";
  if (typeof time === "string") return time;
  if (typeof time === "object" && time !== null) {
    if ("year" in time && "month" in time && "day" in time) {
      const t = time as { year: number; month: number; day: number };
      const m = String(t.month).padStart(2, "0");
      const d = String(t.day).padStart(2, "0");
      return `${t.year}-${m}-${d}`;
    }
  }
  if (typeof time === "number") {
    const dt = new Date(time * 1000);
    return dt.toISOString().split("T")[0];
  }
  return String(time);
}

/**
 * Chart candlestick + SMA50/SMA200 overlay + marker BUY/EXIT terhubung (pane 0),
 * RSI (pane 1), MACD (pane 2) -- SATU instance chart lightweight-charts v5
 * memakai native multi-pane.
 *
 * Fitur:
 * - Stateful Pairing: Panah merah selalu menutup panah hijau (tidak ada panah merah menggantung).
 * - Interactive Glow: Saat lilin panah disentuh kursor, pasangan Open & Close membesar dan menyala neon.
 * - Floating Trade Card: Menampilkan detail lengkap trade terhubung atau posisi aktif.
 */
export function PriceChart({
  bars,
  trades = [],
  activePosition = null,
  ticker,
  lastClose,
  height = 820,
}: PriceChartProps) {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const markersPluginRef = React.useRef<ISeriesMarkersPluginApi<Time> | null>(null);
  const hoveredTradeRef = React.useRef<PairedTradeItem | null>(null);

  const [hoveredTrade, setHoveredTrade] = React.useState<PairedTradeItem | null>(null);

  // 1. Bangun pasangan trade (Stateful Pairing)
  const pairedTrades = React.useMemo(() => {
    if (!bars || bars.length === 0) return [];

    // Jika ada data trades dari backtest
    if (trades && trades.length > 0) {
      const list: PairedTradeItem[] = trades.map((t, idx) => ({
        id: `trade-${idx}-${t.entry_date}`,
        entryDate: t.entry_date,
        exitDate: t.exit_date,
        entryPrice: t.entry_price,
        exitPrice: t.exit_price,
        returnPct: t.return_pct,
        reason: t.reason,
        holdDays: t.hold_days,
        isOpen: false,
      }));

      // Tambahkan posisi aktif saat ini jika ada
      if (activePosition && activePosition.entry_date && activePosition.status === "OPEN") {
        const entryBar = bars.find((b) => b.date === activePosition.entry_date);
        const resolvedEntryPrice =
          activePosition.entry_price ?? entryBar?.open ?? entryBar?.close ?? lastClose ?? 0;

        const entryTime = new Date(activePosition.entry_date).getTime();
        const diffDays = Math.max(0, Math.floor((Date.now() - entryTime) / (1000 * 60 * 60 * 24)));

        list.push({
          id: `active-${activePosition.entry_date}`,
          entryDate: activePosition.entry_date,
          exitDate: null,
          entryPrice: resolvedEntryPrice,
          exitPrice: null,
          returnPct:
            lastClose && resolvedEntryPrice > 0
              ? ((lastClose - resolvedEntryPrice) / resolvedEntryPrice) * 100
              : null,
          reason: "HOLDING",
          holdDays: diffDays,
          isOpen: true,
        });
      }

      return list;
    }

    // Fallback: Kronologis stateful scan pada lilin bars.signal
    const list: PairedTradeItem[] = [];
    let currentEntry: { date: string; price: number; index: number } | null = null;

    for (let i = 0; i < bars.length; i++) {
      const b = bars[i];
      if (b.signal === 1 && !currentEntry) {
        currentEntry = { date: b.date, price: b.close ?? 0, index: i };
      } else if (b.signal === -1 && currentEntry) {
        const exitPrice = b.close ?? 0;
        const retPct =
          currentEntry.price > 0 ? ((exitPrice - currentEntry.price) / currentEntry.price) * 100 : 0;
        list.push({
          id: `synth-${currentEntry.date}-${b.date}`,
          entryDate: currentEntry.date,
          exitDate: b.date,
          entryPrice: currentEntry.price,
          exitPrice,
          returnPct: Number(retPct.toFixed(2)),
          reason: "CLOSED_SIGNAL",
          holdDays: i - currentEntry.index,
          isOpen: false,
        });
        currentEntry = null;
      }
    }

    if (currentEntry) {
      list.push({
        id: `synth-active-${currentEntry.date}`,
        entryDate: currentEntry.date,
        exitDate: null,
        entryPrice: currentEntry.price,
        exitPrice: null,
        returnPct:
          lastClose && currentEntry.price > 0
            ? ((lastClose - currentEntry.price) / currentEntry.price) * 100
            : null,
        reason: "HOLDING",
        holdDays: bars.length - 1 - currentEntry.index,
        isOpen: true,
      });
    }

    return list;
  }, [bars, trades, activePosition, lastClose]);

  // 2. Base Markers Generator
  const baseMarkers = React.useMemo(() => {
    const markers: SeriesMarker<Time>[] = [];

    for (const t of pairedTrades) {
      markers.push({
        time: t.entryDate as Time,
        position: "belowBar",
        color: "#22c55e",
        shape: "arrowUp",
        size: 1,
        text: t.isOpen ? "BUY (ACTIVE)" : "BUY",
      });

      if (t.exitDate && !t.isOpen) {
        markers.push({
          time: t.exitDate as Time,
          position: "aboveBar",
          color: "#ef4444",
          shape: "arrowDown",
          size: 1,
          text: "EXIT",
        });
      }
    }

    markers.sort((a, b) => String(a.time).localeCompare(String(b.time)));
    return markers;
  }, [pairedTrades]);

  // Map tanggal lilin ke Trade terhubung untuk pencarian instan O(1)
  const dateToTradeMap = React.useMemo(() => {
    const map = new Map<string, PairedTradeItem>();
    for (const t of pairedTrades) {
      map.set(t.entryDate, t);
      if (t.exitDate) {
        map.set(t.exitDate, t);
      }
    }
    return map;
  }, [pairedTrades]);

  React.useEffect(() => {
    if (!containerRef.current || bars.length === 0) return;

    const chart: IChartApi = createChart(containerRef.current, {
      height,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#94a3b8",
        panes: {
          separatorColor: "#232b3d",
          separatorHoverColor: "rgba(99,102,241,0.15)",
        },
      },
      grid: {
        vertLines: { color: "#1a2233" },
        horzLines: { color: "#1a2233" },
      },
      rightPriceScale: { borderColor: "#232b3d" },
      timeScale: { borderColor: "#232b3d" },
      crosshair: { mode: CrosshairMode.Normal },
    });

    // ---- Pane 0: Candlestick + SMA50/SMA200 + Marker Terhubung ----
    const candleSeries = chart.addSeries(
      CandlestickSeries,
      {
        upColor: "#22c55e",
        downColor: "#ef4444",
        borderVisible: false,
        wickUpColor: "#22c55e",
        wickDownColor: "#ef4444",
      },
      0,
    );

    candleSeries.setData(
      bars
        .filter((b) => b.open != null && b.high != null && b.low != null && b.close != null)
        .map((b) => ({
          time: b.date as Time,
          open: b.open as number,
          high: b.high as number,
          low: b.low as number,
          close: b.close as number,
        })),
    );

    const sma50 = chart.addSeries(LineSeries, { color: "#6366f1", lineWidth: 1, title: "SMA50" }, 0);
    sma50.setData(
      bars.filter((b) => b.sma50 != null).map((b) => ({ time: b.date as Time, value: b.sma50 as number })),
    );

    const sma200 = chart.addSeries(LineSeries, { color: "#eab308", lineWidth: 1, title: "SMA200" }, 0);
    sma200.setData(
      bars.filter((b) => b.sma200 != null).map((b) => ({ time: b.date as Time, value: b.sma200 as number })),
    );

    // Inisialisasi plugin SeriesMarkers dengan baseMarkers yang sudah berpasangan rapi
    const markerPrimitive = createSeriesMarkers(candleSeries, baseMarkers);
    markersPluginRef.current = markerPrimitive;

    // ---- Pane 1: RSI(14) ----
    const rsiSeries = chart.addSeries(LineSeries, { color: "#a78bfa", lineWidth: 1, title: "RSI14" }, 1);
    rsiSeries.setData(
      bars.filter((b) => b.rsi14 != null).map((b) => ({ time: b.date as Time, value: b.rsi14 as number })),
    );

    // Garis batas atas (70: Overbought), batas bawah (30: Oversold), dan Centerline (50)
    rsiSeries.createPriceLine({
      price: 70,
      color: "rgba(239, 68, 68, 0.75)",
      lineWidth: 1,
      lineStyle: LineStyle.Dashed,
      axisLabelVisible: true,
      title: "Overbought (70)",
    });
    rsiSeries.createPriceLine({
      price: 50,
      color: "rgba(148, 163, 184, 0.45)",
      lineWidth: 1,
      lineStyle: LineStyle.Dotted,
      axisLabelVisible: true,
      title: "Center (50)",
    });
    rsiSeries.createPriceLine({
      price: 30,
      color: "rgba(34, 197, 94, 0.75)",
      lineWidth: 1,
      lineStyle: LineStyle.Dashed,
      axisLabelVisible: true,
      title: "Oversold (30)",
    });

    // ---- Pane 2: MACD ----
    const macdHist = chart.addSeries(HistogramSeries, { title: "MACD Hist" }, 2);
    const histBars = bars.filter((b) => b.macd_hist != null);
    macdHist.setData(
      histBars.map((b, idx) => {
        const val = b.macd_hist as number;
        const prevVal = idx > 0 ? (histBars[idx - 1].macd_hist as number) : val;
        let color: string;
        if (val >= 0) {
          color = val >= prevVal ? "#22c55e" : "#15803d"; // Hijau terang (menguat) vs hijau sedang (melambat)
        } else {
          color = val <= prevVal ? "#ef4444" : "#f87171"; // Merah terang (menguat) vs merah pudar (mereda)
        }
        return {
          time: b.date as Time,
          value: val,
          color,
        };
      }),
    );

    // Garis Nol (Zero Line = 0) untuk batas momentum
    macdHist.createPriceLine({
      price: 0,
      color: "rgba(148, 163, 184, 0.5)",
      lineWidth: 1,
      lineStyle: LineStyle.Dotted,
      axisLabelVisible: true,
      title: "Zero (0)",
    });

    const macdLine = chart.addSeries(LineSeries, { color: "#3b82f6", lineWidth: 1, title: "MACD" }, 2);
    macdLine.setData(
      bars.filter((b) => b.macd != null).map((b) => ({ time: b.date as Time, value: b.macd as number })),
    );
    const macdSignalLine = chart.addSeries(LineSeries, { color: "#eab308", lineWidth: 1, title: "Signal" }, 2);
    macdSignalLine.setData(
      bars
        .filter((b) => b.macd_signal != null)
        .map((b) => ({ time: b.date as Time, value: b.macd_signal as number })),
    );

    // Rasio tinggi antar-pane simetris (380 Candlestick, 220 RSI, 220 MACD)
    // Gunakan setStretchFactor() alih-alih setHeight() karena pada Lightweight Charts v5,
    // setHeight() mendistribusikan perubahan tinggi ke pane lain sehingga pemanggilan berurutan
    // saling menimpa. setStretchFactor() menjamin tinggi RSI (pane 1) dan MACD (pane 2) sama persis 1:1.
    const panes = chart.panes();
    panes[0]?.setStretchFactor(380);
    panes[1]?.setStretchFactor(220);
    panes[2]?.setStretchFactor(220);

    chart.timeScale().fitContent();

    // ---- Event Crosshair Move: Interactive Glow & Linking ----
    chart.subscribeCrosshairMove((param) => {
      if (!param.time) {
        if (hoveredTradeRef.current !== null) {
          hoveredTradeRef.current = null;
          setHoveredTrade(null);
          markersPluginRef.current?.setMarkers(baseMarkers);
        }
        return;
      }

      const currentDateStr = normalizeTime(param.time);
      const matched = dateToTradeMap.get(currentDateStr);

      if (matched) {
        if (hoveredTradeRef.current?.id !== matched.id) {
          hoveredTradeRef.current = matched;
          setHoveredTrade(matched);

          // Buat marker dengan highlight menyala (glow) untuk pasangan trade ini
          const glowingMarkers: SeriesMarker<Time>[] = [];
          for (const t of pairedTrades) {
            if (t.id === matched.id) {
              // Panah BUY menyala terang
              glowingMarkers.push({
                time: t.entryDate as Time,
                position: "belowBar",
                color: "#4ade80", // Vibrant glowing neon emerald
                shape: "arrowUp",
                size: 2,
                text: `BUY @ ${formatIdr(t.entryPrice)}`,
              });

              // Panah EXIT pasangan menyala terang
              if (t.exitDate && !t.isOpen) {
                const retStr = t.returnPct != null ? formatPctId(t.returnPct) : "";
                glowingMarkers.push({
                  time: t.exitDate as Time,
                  position: "aboveBar",
                  color: "#f87171", // Vibrant glowing neon crimson
                  shape: "arrowDown",
                  size: 2,
                  text: `EXIT (${retStr})`,
                });
              }
            } else {
              // Marker trade lain dibuat sedikit lebih redup agar fokus ke pasangan aktif
              glowingMarkers.push({
                time: t.entryDate as Time,
                position: "belowBar",
                color: "rgba(34, 197, 94, 0.45)",
                shape: "arrowUp",
                size: 1,
                text: t.isOpen ? "BUY" : "BUY",
              });
              if (t.exitDate && !t.isOpen) {
                glowingMarkers.push({
                  time: t.exitDate as Time,
                  position: "aboveBar",
                  color: "rgba(239, 68, 68, 0.45)",
                  shape: "arrowDown",
                  size: 1,
                  text: "EXIT",
                });
              }
            }
          }

          glowingMarkers.sort((a, b) => String(a.time).localeCompare(String(b.time)));
          markersPluginRef.current?.setMarkers(glowingMarkers);
        }
      } else {
        if (hoveredTradeRef.current !== null) {
          hoveredTradeRef.current = null;
          setHoveredTrade(null);
          markersPluginRef.current?.setMarkers(baseMarkers);
        }
      }
    });

    const resizeObserver = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (entry) chart.applyOptions({ width: entry.contentRect.width });
    });
    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      markersPluginRef.current = null;
      hoveredTradeRef.current = null;
    };
  }, [bars, baseMarkers, dateToTradeMap, pairedTrades, height]);

  const isProfit = (hoveredTrade?.returnPct ?? 0) >= 0;

  return (
    <div className="relative w-full overflow-hidden rounded-lg border border-border bg-surface-0 shadow-sm">
      {/* Floating Glassmorphic Trade Card saat kursor hover di panah terhubung */}
      {hoveredTrade && (
        <div className="pointer-events-none absolute top-3 left-3 z-30 flex max-w-sm flex-col gap-2 rounded-xl border border-border/80 bg-surface-1/95 p-3.5 shadow-2xl backdrop-blur-md transition-all duration-200 animate-in fade-in zoom-in-95">
          <div className="flex items-center justify-between gap-2 border-b border-border/60 pb-2">
            <div className="flex items-center gap-1.5">
              {hoveredTrade.isOpen ? (
                <>
                  <span className="relative flex size-2">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                    <span className="relative inline-flex size-2 rounded-full bg-emerald-500" />
                  </span>
                  <span className="font-mono text-xs font-bold tracking-wide text-emerald-400">
                    POSISI AKTIF (HOLDING)
                  </span>
                </>
              ) : (
                <>
                  <Sparkles className="size-3.5 text-blue-400" />
                  <span className="font-mono text-xs font-bold tracking-wide text-text-primary">
                    TRADE TERHUBUNG
                  </span>
                </>
              )}
            </div>

            {hoveredTrade.returnPct != null && (
              <Badge
                variant="outline"
                className={`font-mono text-xs font-semibold ${
                  isProfit
                    ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-400"
                    : "border-rose-500/40 bg-rose-500/10 text-rose-400"
                }`}
              >
                {isProfit ? <TrendingUp className="size-3" /> : <TrendingDown className="size-3" />}
                {formatPctId(hoveredTrade.returnPct)}
              </Badge>
            )}
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="flex flex-col rounded-md bg-surface-0/70 p-2 border border-border/40">
              <span className="text-[10.5px] font-medium text-text-muted">Masuk (Entry)</span>
              <span className="font-semibold text-text-primary">{formatIdr(hoveredTrade.entryPrice)}</span>
              <span className="font-mono text-[10px] text-text-muted">{hoveredTrade.entryDate}</span>
            </div>

            <div className="flex flex-col rounded-md bg-surface-0/70 p-2 border border-border/40">
              <span className="text-[10.5px] font-medium text-text-muted">
                {hoveredTrade.isOpen ? "Harga Terakhir" : "Keluar (Exit)"}
              </span>
              <span className="font-semibold text-text-primary">
                {hoveredTrade.isOpen
                  ? formatIdr(lastClose ?? hoveredTrade.entryPrice)
                  : formatIdr(hoveredTrade.exitPrice)}
              </span>
              <span className="font-mono text-[10px] text-text-muted">
                {hoveredTrade.isOpen ? "Sedang Berjalan" : hoveredTrade.exitDate}
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between gap-2 pt-1 text-[11px] text-text-secondary">
            <div className="flex items-center gap-1">
              <Clock className="size-3 text-text-muted" />
              <span>Durasi: {hoveredTrade.holdDays ?? 0} hari</span>
            </div>

            <div className="flex items-center gap-1 font-medium">
              {hoveredTrade.isOpen ? (
                <>
                  {activePosition?.sl_price && (
                    <span className="text-rose-400">SL: {formatIdr(activePosition.sl_price)}</span>
                  )}
                  {activePosition?.tp_price && (
                    <span className="text-emerald-400 ml-1.5">TP: {formatIdr(activePosition.tp_price)}</span>
                  )}
                </>
              ) : (
                <span className="text-blue-400">{formatExitReason(hoveredTrade.reason)}</span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Subtle hint saat kursor tidak sedang hover */}
      {!hoveredTrade && (
        <div className="pointer-events-none absolute top-2 right-3 z-10 hidden sm:flex items-center gap-1.5 rounded-full border border-border/60 bg-surface-1/70 px-2.5 py-1 text-[10.5px] text-text-muted backdrop-blur-sm">
          <Info className="size-3 text-blue-400" />
          <span>Arahkan kursor ke panah BUY / EXIT untuk melihat pasangan trade</span>
        </div>
      )}

      {/* Chart Canvas Container */}
      <div ref={containerRef} className="w-full overflow-hidden" />
    </div>
  );
}
