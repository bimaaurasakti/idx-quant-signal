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
  type SeriesMarker,
  type Time,
} from "lightweight-charts";

import type { PriceBar } from "@/lib/types";

interface PriceChartProps {
  bars: PriceBar[];
  height?: number;
}

/**
 * Chart candlestick + SMA50/SMA200 overlay + marker BUY/SELL (pane 0),
 * RSI (pane 1), MACD (pane 2) -- SATU instance chart lightweight-charts v5
 * memakai native multi-pane (bukan 3 chart terpisah yg disinkron manual).
 * Dipakai halaman Detail Saham (strategi produksi tetap, signals.py).
 *
 * Backtest Lab (Fase 5) akan butuh varian lebih generik yg menerima
 * indicator_series dinamis dari /api/backtest/run -- BUKAN file ini,
 * lihat §5.4/§6 implementation plan (chart_animation.py dihapus total,
 * replay jadi state React murni di atas komponen serupa ini).
 */
export function PriceChart({ bars, height = 480 }: PriceChartProps) {
  const containerRef = React.useRef<HTMLDivElement>(null);

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

    // ---- Pane 0: Harga + SMA50/SMA200 + marker BUY/SELL ----
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

    const markers: SeriesMarker<Time>[] = bars
      .filter((b) => b.signal !== 0)
      .map((b) => ({
        time: b.date as Time,
        position: b.signal === 1 ? "belowBar" : "aboveBar",
        color: b.signal === 1 ? "#22c55e" : "#ef4444",
        shape: b.signal === 1 ? "arrowUp" : "arrowDown",
      }));
    createSeriesMarkers(candleSeries, markers);

    // ---- Pane 1: RSI(14) ----
    const rsiSeries = chart.addSeries(LineSeries, { color: "#a78bfa", lineWidth: 1, title: "RSI14" }, 1);
    rsiSeries.setData(
      bars.filter((b) => b.rsi14 != null).map((b) => ({ time: b.date as Time, value: b.rsi14 as number })),
    );

    // ---- Pane 2: MACD ----
    const macdHist = chart.addSeries(HistogramSeries, { title: "MACD Hist" }, 2);
    macdHist.setData(
      bars
        .filter((b) => b.macd_hist != null)
        .map((b) => ({
          time: b.date as Time,
          value: b.macd_hist as number,
          color: (b.macd_hist as number) >= 0 ? "#22c55e" : "#ef4444",
        })),
    );
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

    // Pane harga lebih tinggi drpd subplot RSI/MACD.
    const panes = chart.panes();
    panes[0]?.setHeight(Math.round(height * 0.55));
    panes[1]?.setHeight(Math.round(height * 0.2));
    panes[2]?.setHeight(Math.round(height * 0.25));

    chart.timeScale().fitContent();

    const resizeObserver = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (entry) chart.applyOptions({ width: entry.contentRect.width });
    });
    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
    };
  }, [bars, height]);

  return <div ref={containerRef} className="w-full overflow-hidden rounded-lg" />;
}
