"use client";

import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { closedStatusToReason, exitReasonColor, exitReasonLabel } from "@/lib/constants";
import type { ClosedPosition } from "@/lib/types";

export function ExitBreakdownChart({ positions }: { positions: ClosedPosition[] }) {
  const counts = new Map<string, number>();
  for (const p of positions) {
    const reason = closedStatusToReason(p.status);
    counts.set(reason, (counts.get(reason) ?? 0) + 1);
  }
  const data = Array.from(counts.entries()).map(([reason, count]) => ({
    reason,
    label: exitReasonLabel(reason),
    count,
    color: exitReasonColor(reason),
  }));

  return (
    <div className="rounded-lg border border-border bg-surface-1 p-4">
      <h3 className="mb-3 text-[13px] font-medium text-text-secondary">Breakdown Alasan Exit</h3>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1a2233" vertical={false} />
          <XAxis
            dataKey="label"
            tick={{ fill: "#94a3b8", fontSize: 11 }}
            axisLine={{ stroke: "#232b3d" }}
            tickLine={false}
          />
          <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
          <Tooltip
            contentStyle={{ background: "#1e2740", border: "1px solid #2e3850", borderRadius: 8, fontSize: 12 }}
            labelStyle={{ color: "#f1f5f9" }}
            cursor={{ fill: "rgba(255,255,255,0.03)" }}
          />
          <Bar dataKey="count" radius={[4, 4, 0, 0]}>
            {data.map((d) => (
              <Cell key={d.reason} fill={d.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
