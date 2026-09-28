"use client";

import * as React from "react";
import { TrendingUp } from "lucide-react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { formatPctId } from "@/lib/format";
import type { TradeRow } from "@/lib/types";

interface EquityCurveChartProps {
  trades?: TradeRow[];
  equityCurve?: number[];
}

export function EquityCurveChart({ trades, equityCurve }: EquityCurveChartProps) {
  // Hitung compounding equity curve dari trade yang sudah closed atau dari array equityCurve
  const data = React.useMemo(() => {
    if (equityCurve && equityCurve.length > 0) {
      return equityCurve.map((v, i) => ({
        trade: i + 1,
        date: `T-${i + 1}`,
        returnPct: Math.round((v - 1) * 10000) / 100,
        equity: Math.round(v * 1000) / 10,
      }));
    }

    if (!trades || trades.length === 0) return [];

    let currentEquity = 1.0;
    const points = [{ trade: 0, date: "Awal", returnPct: 0, equity: 100 }];

    trades.forEach((t, i) => {
      currentEquity *= 1 + t.return_pct / 100;
      points.push({
        trade: i + 1,
        date: t.exit_date,
        returnPct: Math.round((currentEquity - 1) * 10000) / 100,
        equity: Math.round(currentEquity * 1000) / 10,
      });
    });

    return points;
  }, [trades, equityCurve]);

  if (data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-border/80 bg-surface-1/50 p-8 text-center">
        <div className="flex size-10 items-center justify-center rounded-full bg-surface-2 text-text-muted">
          <TrendingUp className="size-5" />
        </div>
        <div className="text-xs font-semibold text-text-primary">
          Belum Ada Data Kurva Modal (Equity Curve)
        </div>
        <div className="max-w-md text-[11.5px] text-text-muted">
          Kurva pertumbuhan modal akan digambar secara otomatis saat posisi pertama selesai ditutup (*closed*).
        </div>
      </div>
    );
  }

  const latestReturn = data[data.length - 1]?.returnPct ?? 0;
  const isProfit = latestReturn >= 0;

  return (
    <div className="rounded-xl border border-border/80 bg-surface-1/90 p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between border-b border-border/60 pb-2.5">
        <div>
          <h3 className="text-xs font-semibold text-text-primary">
            Live Equity Curve (Compounding Modal)
          </h3>
          <p className="text-[11px] text-text-muted">
            Pertumbuhan kumulatif modal berdasarkan trade yang telah terealisasi hingga lilin saat ini.
          </p>
        </div>
        <div className="text-right font-mono">
          <div className="text-[10.5px] text-text-muted">Net Return Kumulatif</div>
          <div
            className={`text-sm font-bold ${
              isProfit ? "text-emerald-400" : "text-rose-400"
            }`}
          >
            {formatPctId(latestReturn)}
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis
            dataKey="trade"
            tick={{ fill: "#94a3b8", fontSize: 11 }}
            axisLine={{ stroke: "#334155" }}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: "#94a3b8", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            domain={["auto", "auto"]}
          />
          <Tooltip
            contentStyle={{
              background: "#0f172a",
              border: "1px solid #334155",
              borderRadius: 8,
              fontSize: 12,
              color: "#f8fafc",
            }}
            formatter={(v) => [`${v}%`, "Net Return"]}
            labelFormatter={(v) => `Trade Selesai ke-${v}`}
          />
          <Line
            type="monotone"
            dataKey="returnPct"
            stroke={isProfit ? "#22c55e" : "#ef4444"}
            strokeWidth={2}
            dot={data.length <= 30 ? { r: 3, fill: isProfit ? "#22c55e" : "#ef4444" } : false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
