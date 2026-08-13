"use client";

import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { formatPctId } from "@/lib/format";

export function EquityCurveChart({ equityCurve }: { equityCurve: number[] }) {
  const data = equityCurve.map((v, i) => ({ trade: i + 1, returnPct: Math.round((v - 1) * 10000) / 100 }));

  return (
    <div className="rounded-lg border border-border bg-surface-1 p-4">
      <h3 className="mb-3 text-[13px] font-medium text-text-secondary">Equity Curve (Compounding per Trade)</h3>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1a2233" />
          <XAxis
            dataKey="trade"
            tick={{ fill: "#94a3b8", fontSize: 11 }}
            axisLine={{ stroke: "#232b3d" }}
            tickLine={false}
          />
          <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip
            contentStyle={{ background: "#1e2740", border: "1px solid #2e3850", borderRadius: 8, fontSize: 12 }}
            labelStyle={{ color: "#f1f5f9" }}
            formatter={(v) => formatPctId(Number(v))}
            labelFormatter={(v) => `Trade ke-${v}`}
          />
          <Line type="monotone" dataKey="returnPct" stroke="var(--brand)" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
      <p className="mt-2 text-[11.5px] text-text-muted">
        Beda dengan &ldquo;Total Return (Sum)&rdquo; di halaman lain (non-kompound): equity curve ini
        MENGKOMPOUND tiap trade berurutan, asumsi seluruh modal dipakai ulang tiap trade.
      </p>
    </div>
  );
}
