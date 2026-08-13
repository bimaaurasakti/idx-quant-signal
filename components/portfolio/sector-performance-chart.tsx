"use client";

import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { formatPctId } from "@/lib/format";
import type { ClosedPosition } from "@/lib/types";

export function SectorPerformanceChart({ positions }: { positions: ClosedPosition[] }) {
  const bySector = new Map<string, number[]>();
  for (const p of positions) {
    const arr = bySector.get(p.sektor) ?? [];
    arr.push(p.return_pct);
    bySector.set(p.sektor, arr);
  }
  const data = Array.from(bySector.entries())
    .map(([sektor, returns]) => ({
      sektor: sektor.replaceAll("_", " "),
      avgReturn: returns.reduce((a, b) => a + b, 0) / returns.length,
    }))
    .sort((a, b) => b.avgReturn - a.avgReturn);

  return (
    <div className="rounded-lg border border-border bg-surface-1 p-4">
      <h3 className="mb-3 text-[13px] font-medium text-text-secondary">Rata-rata Return per Sektor (%)</h3>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data} layout="vertical" margin={{ left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1a2233" horizontal={false} />
          <XAxis type="number" tick={{ fill: "#94a3b8", fontSize: 11 }} axisLine={{ stroke: "#232b3d" }} tickLine={false} />
          <YAxis
            type="category"
            dataKey="sektor"
            width={140}
            tick={{ fill: "#94a3b8", fontSize: 10.5 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{ background: "#1e2740", border: "1px solid #2e3850", borderRadius: 8, fontSize: 12 }}
            labelStyle={{ color: "#f1f5f9" }}
            formatter={(v) => formatPctId(Number(v))}
            cursor={{ fill: "rgba(255,255,255,0.03)" }}
          />
          <Bar dataKey="avgReturn" radius={[0, 4, 4, 0]}>
            {data.map((d) => (
              <Cell key={d.sektor} fill={d.avgReturn >= 0 ? "var(--bullish)" : "var(--bearish)"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
