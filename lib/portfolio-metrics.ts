/**
 * lib/portfolio-metrics.ts
 * =========================
 * Formula agregasi client-side -- WAJIB identik backtester.py::_compute_metrics
 * / portfolio.py::_portfolio_metrics (§5.7 implementation plan). Dipakai
 * untuk filter instan di halaman Portfolio tanpa round-trip ke server
 * (§5.6) -- dataset closed positions cukup kecil untuk ini aman dilakukan
 * di client.
 */
import type { ClosedPosition } from "@/lib/types";

export interface PortfolioMetrics {
  n: number;
  winrate: number;
  avgWin: number;
  avgLoss: number;
  expectancy: number;
  profitFactor: number | null;
  totalReturn: number;
  avgHoldDays: number;
}

function mean(arr: number[]): number {
  return arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;
}
function sum(arr: number[]): number {
  return arr.reduce((a, b) => a + b, 0);
}

export function computeMetrics(rows: ClosedPosition[]): PortfolioMetrics | null {
  const n = rows.length;
  if (n === 0) return null;

  const wins = rows.filter((r) => r.return_pct > 0);
  const losses = rows.filter((r) => r.return_pct <= 0);

  const winrate = (wins.length / n) * 100;
  const avgWin = mean(wins.map((r) => r.return_pct));
  const avgLoss = mean(losses.map((r) => Math.abs(r.return_pct)));
  const lossrate = 100 - winrate;
  const expectancy = (winrate / 100) * avgWin - (lossrate / 100) * avgLoss;

  const totalProfit = sum(wins.map((r) => r.return_pct));
  const totalLoss = sum(losses.map((r) => Math.abs(r.return_pct)));
  const profitFactor = totalLoss > 0 ? totalProfit / totalLoss : null; // null -> tampilkan "∞"

  const totalReturn = sum(rows.map((r) => r.return_pct));
  const avgHoldDays = mean(rows.map((r) => r.hold_days));

  return { n, winrate, avgWin, avgLoss, expectancy, profitFactor, totalReturn, avgHoldDays };
}
