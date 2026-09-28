"use client";

import * as React from "react";
import {
  CandlestickSeries,
  ColorType,
  CrosshairMode,
  HistogramSeries,
  LineSeries,
  LineStyle,
  createChart,
  createSeriesMarkers,
  type IChartApi,
  type ISeriesApi,
  type ISeriesMarkersPluginApi,
  type SeriesMarker,
  type Time,
} from "lightweight-charts";

import type { Bar, IndicatorSeries, PriceBar, TradeRow } from "@/lib/types";

export type ChartBar = {
  date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
  sma20?: number | null;
  sma50?: number | null;
  sma200?: number | null;
  rsi14?: number | null;
  macd?: number | null;
  macd_signal?: number | null;
  macd_hist?: number | null;
};

interface BacktestChartProps {
  bars: ChartBar[];
  currentIndex?: number;
  trades: TradeRow[];
  indicatorSeries?: IndicatorSeries[];
  playbackDate?: string | null;
  height?: number;
}

export function BacktestChart({
  bars,
  currentIndex: explicitIndex,
  trades,
  playbackDate,
  height = 820,
}: BacktestChartProps) {
  const currentIndex =
    explicitIndex ??
    (playbackDate
      ? Math.max(0, bars.findIndex((b) => b.date >= playbackDate))
      : Math.max(0, bars.length - 1));

  const containerRef = React.useRef<HTMLDivElement>(null);
  const chartRef = React.useRef<IChartApi | null>(null);
  const markersPluginRef = React.useRef<ISeriesMarkersPluginApi<Time> | null>(null);

  // Simpan referensi seluruh series untuk update O(1) cepat
  const seriesRef = React.useRef<{
    candle: ISeriesApi<"Candlestick">;
    volume: ISeriesApi<"Histogram">;
    sma50: ISeriesApi<"Line">;
    sma200: ISeriesApi<"Line">;
    rsi: ISeriesApi<"Line">;
    macdHist: ISeriesApi<"Histogram">;
    macdLine: ISeriesApi<"Line">;
    macdSignal: ISeriesApi<"Line">;
  } | null>(null);

  const prevIndexRef = React.useRef<number>(-1);

  // Helper untuk membangun markers trade sampai tanggal tertentu
  const buildMarkers = React.useCallback(
    (maxDate: string): SeriesMarker<Time>[] => {
      const markers: SeriesMarker<Time>[] = [];
      for (const t of trades) {
        if (t.entry_date <= maxDate) {
          markers.push({
            time: t.entry_date as Time,
            position: "belowBar",
            color: "#22c55e",
            shape: "arrowUp",
            text: `BUY @ ${t.entry_price}`,
          });
        }
        if (t.exit_date <= maxDate) {
          const isWin = t.return_pct >= 0;
          markers.push({
            time: t.exit_date as Time,
            position: "aboveBar",
            color: isWin ? "#22c55e" : "#ef4444",
            shape: "arrowDown",
            text: `${t.reason} ${t.return_pct > 0 ? "+" : ""}${t.return_pct.toFixed(1)}%`,
          });
        }
      }
      markers.sort((a, b) => String(a.time).localeCompare(String(b.time)));
      return markers;
    },
    [trades],
  );

  // ---- Inisialisasi Chart 3-Pane Simetris ----
  React.useEffect(() => {
    if (!containerRef.current || bars.length === 0) return;

    // Reset container
    containerRef.current.innerHTML = "";

    const chart = createChart(containerRef.current, {
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
      timeScale: { borderColor: "#232b3d", fixLeftEdge: true },
      crosshair: { mode: CrosshairMode.Normal },
    });
    chartRef.current = chart;

    // ---- Pane 0: Candlestick + Volume Overlay + SMA50 + SMA200 ----
    const candle = chart.addSeries(
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

    const volume = chart.addSeries(
      HistogramSeries,
      {
        priceFormat: { type: "volume" },
        priceScaleId: "", // Overlay pada pane 0
      },
      0,
    );
    volume.priceScale().applyOptions({
      scaleMargins: { top: 0.82, bottom: 0 },
    });

    const sma50 = chart.addSeries(LineSeries, { color: "#6366f1", lineWidth: 1, title: "SMA50" }, 0);
    const sma200 = chart.addSeries(LineSeries, { color: "#eab308", lineWidth: 1, title: "SMA200" }, 0);

    const markersPlugin = createSeriesMarkers(candle, []);
    markersPluginRef.current = markersPlugin;

    // ---- Pane 1: RSI 14 (Level 70, 50, 30) ----
    const rsi = chart.addSeries(LineSeries, { color: "#a78bfa", lineWidth: 1, title: "RSI14" }, 1);
    rsi.createPriceLine({
      price: 70,
      color: "rgba(239, 68, 68, 0.75)",
      lineWidth: 1,
      lineStyle: LineStyle.Dashed,
      axisLabelVisible: true,
      title: "Overbought (70)",
    });
    rsi.createPriceLine({
      price: 50,
      color: "rgba(148, 163, 184, 0.45)",
      lineWidth: 1,
      lineStyle: LineStyle.Dotted,
      axisLabelVisible: true,
      title: "Center (50)",
    });
    rsi.createPriceLine({
      price: 30,
      color: "rgba(34, 197, 94, 0.75)",
      lineWidth: 1,
      lineStyle: LineStyle.Dashed,
      axisLabelVisible: true,
      title: "Oversold (30)",
    });

    // ---- Pane 2: MACD (Zero Line + 4-Color Histogram + MACD + Signal) ----
    const macdHist = chart.addSeries(HistogramSeries, { title: "MACD Hist" }, 2);
    macdHist.createPriceLine({
      price: 0,
      color: "rgba(148, 163, 184, 0.5)",
      lineWidth: 1,
      lineStyle: LineStyle.Dotted,
      axisLabelVisible: true,
      title: "Zero (0)",
    });
    const macdLine = chart.addSeries(LineSeries, { color: "#3b82f6", lineWidth: 1, title: "MACD" }, 2);
    const macdSignal = chart.addSeries(LineSeries, { color: "#eab308", lineWidth: 1, title: "Signal" }, 2);

    // Rasio tinggi antar-pane simetris dengan setStretchFactor (Candlestick: 380, RSI: 220, MACD: 220)
    const panes = chart.panes();
    panes[0]?.setStretchFactor(380);
    panes[1]?.setStretchFactor(220);
    panes[2]?.setStretchFactor(220);

    seriesRef.current = {
      candle,
      volume,
      sma50,
      sma200,
      rsi,
      macdHist,
      macdLine,
      macdSignal,
    };

    // Muat data awal (0 sampai currentIndex)
    const initialSlice = bars.slice(0, currentIndex + 1);
    candle.setData(
      initialSlice
        .filter((b) => b.open != null && b.high != null && b.low != null && b.close != null)
        .map((b) => ({
          time: b.date as Time,
          open: b.open as number,
          high: b.high as number,
          low: b.low as number,
          close: b.close as number,
        })),
    );

    volume.setData(
      initialSlice
        .filter((b) => b.volume != null)
        .map((b) => ({
          time: b.date as Time,
          value: b.volume as number,
          color: (b.close ?? 0) >= (b.open ?? 0) ? "rgba(34,197,94,0.45)" : "rgba(239,68,68,0.45)",
        })),
    );

    sma50.setData(
      initialSlice.filter((b) => b.sma50 != null).map((b) => ({ time: b.date as Time, value: b.sma50 as number })),
    );

    sma200.setData(
      initialSlice.filter((b) => b.sma200 != null).map((b) => ({ time: b.date as Time, value: b.sma200 as number })),
    );

    rsi.setData(
      initialSlice.filter((b) => b.rsi14 != null).map((b) => ({ time: b.date as Time, value: b.rsi14 as number })),
    );

    const histSlice = initialSlice.filter((b) => b.macd_hist != null);
    macdHist.setData(
      histSlice.map((b, idx) => {
        const val = b.macd_hist as number;
        const prevVal = idx > 0 ? (histSlice[idx - 1].macd_hist as number) : val;
        let color: string;
        if (val >= 0) {
          color = val >= prevVal ? "#22c55e" : "#15803d";
        } else {
          color = val <= prevVal ? "#ef4444" : "#f87171";
        }
        return { time: b.date as Time, value: val, color };
      }),
    );

    macdLine.setData(
      initialSlice.filter((b) => b.macd != null).map((b) => ({ time: b.date as Time, value: b.macd as number })),
    );

    macdSignal.setData(
      initialSlice
        .filter((b) => b.macd_signal != null)
        .map((b) => ({ time: b.date as Time, value: b.macd_signal as number })),
    );

    const currentBarDate = bars[currentIndex]?.date;
    if (currentBarDate) {
      markersPlugin.setMarkers(buildMarkers(currentBarDate));
    }

    chart.timeScale().fitContent();
    prevIndexRef.current = currentIndex;

    const resizeObserver = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (entry) chart.applyOptions({ width: entry.contentRect.width });
    });
    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
      markersPluginRef.current = null;
      seriesRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bars, height]);

  // ---- True Cut-Off Dynamic Update saat currentIndex Berubah ----
  React.useEffect(() => {
    const s = seriesRef.current;
    const chart = chartRef.current;
    if (!s || !chart || bars.length === 0 || currentIndex < 0 || currentIndex >= bars.length) return;

    const prev = prevIndexRef.current;
    const currentBar = bars[currentIndex];
    const isStepForward = currentIndex === prev + 1;

    if (isStepForward) {
      // Maju 1 lilin: Gunakan update() yang sangat cepat (O(1))
      if (currentBar.open != null && currentBar.high != null && currentBar.low != null && currentBar.close != null) {
        s.candle.update({
          time: currentBar.date as Time,
          open: currentBar.open,
          high: currentBar.high,
          low: currentBar.low,
          close: currentBar.close,
        });
      }

      if (currentBar.volume != null) {
        s.volume.update({
          time: currentBar.date as Time,
          value: currentBar.volume,
          color: (currentBar.close ?? 0) >= (currentBar.open ?? 0) ? "rgba(34,197,94,0.45)" : "rgba(239,68,68,0.45)",
        });
      }

      if (currentBar.sma50 != null) {
        s.sma50.update({ time: currentBar.date as Time, value: currentBar.sma50 });
      }

      if (currentBar.sma200 != null) {
        s.sma200.update({ time: currentBar.date as Time, value: currentBar.sma200 });
      }

      if (currentBar.rsi14 != null) {
        s.rsi.update({ time: currentBar.date as Time, value: currentBar.rsi14 });
      }

      if (currentBar.macd_hist != null) {
        const prevBar = prev >= 0 ? bars[prev] : currentBar;
        const val = currentBar.macd_hist;
        const prevVal = prevBar.macd_hist ?? val;
        let color: string;
        if (val >= 0) {
          color = val >= prevVal ? "#22c55e" : "#15803d";
        } else {
          color = val <= prevVal ? "#ef4444" : "#f87171";
        }
        s.macdHist.update({ time: currentBar.date as Time, value: val, color });
      }

      if (currentBar.macd != null) {
        s.macdLine.update({ time: currentBar.date as Time, value: currentBar.macd });
      }

      if (currentBar.macd_signal != null) {
        s.macdSignal.update({ time: currentBar.date as Time, value: currentBar.macd_signal });
      }
    } else {
      // Lompat atau scrub mundur: Gunakan setData() pada slice 0..currentIndex
      const slice = bars.slice(0, currentIndex + 1);

      s.candle.setData(
        slice
          .filter((b) => b.open != null && b.high != null && b.low != null && b.close != null)
          .map((b) => ({
            time: b.date as Time,
            open: b.open as number,
            high: b.high as number,
            low: b.low as number,
            close: b.close as number,
          })),
      );

      s.volume.setData(
        slice
          .filter((b) => b.volume != null)
          .map((b) => ({
            time: b.date as Time,
            value: b.volume as number,
            color: (b.close ?? 0) >= (b.open ?? 0) ? "rgba(34,197,94,0.45)" : "rgba(239,68,68,0.45)",
          })),
      );

      s.sma50.setData(
        slice.filter((b) => b.sma50 != null).map((b) => ({ time: b.date as Time, value: b.sma50 as number })),
      );

      s.sma200.setData(
        slice.filter((b) => b.sma200 != null).map((b) => ({ time: b.date as Time, value: b.sma200 as number })),
      );

      s.rsi.setData(
        slice.filter((b) => b.rsi14 != null).map((b) => ({ time: b.date as Time, value: b.rsi14 as number })),
      );

      const histSlice = slice.filter((b) => b.macd_hist != null);
      s.macdHist.setData(
        histSlice.map((b, idx) => {
          const val = b.macd_hist as number;
          const prevVal = idx > 0 ? (histSlice[idx - 1].macd_hist as number) : val;
          let color: string;
          if (val >= 0) {
            color = val >= prevVal ? "#22c55e" : "#15803d";
          } else {
            color = val <= prevVal ? "#ef4444" : "#f87171";
          }
          return { time: b.date as Time, value: val, color };
        }),
      );

      s.macdLine.setData(
        slice.filter((b) => b.macd != null).map((b) => ({ time: b.date as Time, value: b.macd as number })),
      );

      s.macdSignal.setData(
        slice
          .filter((b) => b.macd_signal != null)
          .map((b) => ({ time: b.date as Time, value: b.macd_signal as number })),
      );
    }

    // Perbarui markers sampai tanggal lilin saat ini
    if (markersPluginRef.current) {
      markersPluginRef.current.setMarkers(buildMarkers(currentBar.date));
    }

    // Auto-scroll viewport agar lilin replay terdepan selalu terlihat
    chart.timeScale().scrollToRealTime();

    prevIndexRef.current = currentIndex;
  }, [currentIndex, bars, buildMarkers]);

  return <div ref={containerRef} className="w-full overflow-hidden rounded-xl bg-surface-0 shadow-sm" />;
}
