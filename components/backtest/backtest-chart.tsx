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
  type IChartApi,
  type ISeriesApi,
  type ISeriesMarkersPluginApi,
  type SeriesMarker,
  type Time,
} from "lightweight-charts";

import type { Bar, IndicatorSeries, TradeRow } from "@/lib/types";

interface BacktestChartProps {
  bars: Bar[];
  indicatorSeries: IndicatorSeries[];
  trades: TradeRow[];
  /** null = tampilkan semua data & marker (mode statis). Bukan-null =
   * mode replay: viewport & marker dibatasi sampai tanggal ini. */
  playbackDate: string | null;
  height?: number;
}

const OVERLAY_COLORS = ["#6366f1", "#eab308", "#a78bfa", "#f97316"];
const SUBPLOT_COLORS = ["#a78bfa", "#3b82f6", "#eab308", "#f97316", "#ec4899", "#22c55e"];

/**
 * Chart dinamis untuk Backtest Lab -- menerima indicator_series APAPUN dari
 * /api/backtest/run (overlay -> pane 0, subplot -> pane sendiri-sendiri).
 *
 * PENYEDERHANAAN ARSITEKTUR (§6 implementation plan): seluruh data
 * (bars+indicator+trades) di-set SEKALI lewat setData(). "Replay" TIDAK
 * membangun ulang chart / re-fetch apa pun -- hanya menggeser viewport
 * (timeScale().setVisibleRange) + menyaring marker per tanggal playback,
 * dua operasi yang sangat murah. Ini menggantikan chart_animation.py yang
 * dulu membangun N figure Plotly terpisah di server.
 */
export function BacktestChart({ bars, indicatorSeries, trades, playbackDate, height = 480 }: BacktestChartProps) {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const chartRef = React.useRef<IChartApi | null>(null);
  const candleSeriesRef = React.useRef<ISeriesApi<"Candlestick"> | null>(null);
  const markersRef = React.useRef<ISeriesMarkersPluginApi<Time> | null>(null);

  // ---- Setup chart & set SELURUH data -- SEKALI per perubahan hasil backtest ----
  React.useEffect(() => {
    if (!containerRef.current || bars.length === 0) return;

    const chart = createChart(containerRef.current, {
      height,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#94a3b8",
        panes: { separatorColor: "#232b3d", separatorHoverColor: "rgba(99,102,241,0.15)" },
      },
      grid: { vertLines: { color: "#1a2233" }, horzLines: { color: "#1a2233" } },
      rightPriceScale: { borderColor: "#232b3d" },
      timeScale: { borderColor: "#232b3d" },
      crosshair: { mode: CrosshairMode.Normal },
    });
    chartRef.current = chart;

    const candleSeries = chart.addSeries(
      CandlestickSeries,
      { upColor: "#22c55e", downColor: "#ef4444", borderVisible: false, wickUpColor: "#22c55e", wickDownColor: "#ef4444" },
      0,
    );
    candleSeries.setData(bars.map((b) => ({ time: b.date as Time, open: b.open, high: b.high, low: b.low, close: b.close })));
    candleSeriesRef.current = candleSeries;

    const overlays = indicatorSeries.filter((s) => s.overlay);
    const subplots = indicatorSeries.filter((s) => !s.overlay);

    overlays.forEach((s, i) => {
      const line = chart.addSeries(LineSeries, { color: OVERLAY_COLORS[i % OVERLAY_COLORS.length], lineWidth: 1, title: s.label }, 0);
      const points = bars
        .map((b, idx) => ({ time: b.date as Time, value: s.values[idx] }))
        .filter((d): d is { time: Time; value: number } => d.value != null);
      line.setData(points);
    });

    subplots.forEach((s, i) => {
      const paneIndex = i + 1;
      const line = chart.addSeries(LineSeries, { color: SUBPLOT_COLORS[i % SUBPLOT_COLORS.length], lineWidth: 1, title: s.label }, paneIndex);
      const points = bars
        .map((b, idx) => ({ time: b.date as Time, value: s.values[idx] }))
        .filter((d): d is { time: Time; value: number } => d.value != null);
      line.setData(points);
    });

    const volumePaneIndex = subplots.length + 1;
    const volumeSeries = chart.addSeries(HistogramSeries, { title: "Volume" }, volumePaneIndex);
    volumeSeries.setData(
      bars.map((b) => ({
        time: b.date as Time,
        value: b.volume,
        color: b.close >= b.open ? "rgba(34,197,94,0.45)" : "rgba(239,68,68,0.45)",
      })),
    );

    markersRef.current = createSeriesMarkers(candleSeries, []);

    const panes = chart.panes();
    const nPanes = panes.length;
    if (nPanes > 1) {
      const priceHeight = Math.round(height * 0.5);
      const otherHeight = Math.round((height - priceHeight) / (nPanes - 1));
      panes[0]?.setHeight(priceHeight);
      for (let i = 1; i < nPanes; i++) panes[i]?.setHeight(otherHeight);
    }

    chart.timeScale().fitContent();

    const resizeObserver = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (entry) chart.applyOptions({ width: entry.contentRect.width });
    });
    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      markersRef.current = null;
    };
  }, [bars, indicatorSeries, height]);

  // ---- Update marker + viewport TIAP playbackDate berubah -- MURAH, tanpa re-create chart ----
  React.useEffect(() => {
    if (!markersRef.current || !chartRef.current || bars.length === 0) return;

    const relevant = playbackDate == null ? trades : trades.filter((t) => t.entry_date <= playbackDate);
    const markers: SeriesMarker<Time>[] = [];
    for (const t of relevant) {
      markers.push({ time: t.entry_date as Time, position: "belowBar", color: "#22c55e", shape: "arrowUp" });
      if (playbackDate == null || t.exit_date <= playbackDate) {
        markers.push({ time: t.exit_date as Time, position: "aboveBar", color: "#ef4444", shape: "arrowDown" });
      }
    }
    markers.sort((a, b) => String(a.time).localeCompare(String(b.time)));
    markersRef.current.setMarkers(markers);

    if (playbackDate != null) {
      chartRef.current.timeScale().setVisibleRange({ from: bars[0].date as Time, to: playbackDate as Time });
    } else {
      chartRef.current.timeScale().fitContent();
    }
  }, [playbackDate, trades, bars]);

  return <div ref={containerRef} className="w-full overflow-hidden rounded-lg" />;
}
