"use client";

import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { formatDateId, formatPctId } from "@/lib/format";
import type { ClosedPosition } from "@/lib/types";

export function CumulativeReturnChart({ positions }: { positions: ClosedPosition[] }) {
  const sorted = [...positions].sort((a, b) => a.exit_date.localeCompare(b.exit_date));
  // Akumulasi immutable (bukan `let cum` yg di-reassign di dalam .map) --
  // aturan lint react-hooks/immutability menolak mutasi variabel closure
  // selama render, jadi pakai reduce yg membangun array baru tiap langkah.
  const data = sorted.reduce<{ date: string; cumReturn: number }[]>((acc, p) => {
    const prevCum = acc.length > 0 ? acc[acc.length - 1].cumReturn : 0;
    const cumReturn = Math.round((prevCum + p.return_pct) * 100) / 100;
    return [...acc, { date: p.exit_date, cumReturn }];
  }, []);

  return (
    <div className="rounded-lg border border-border bg-surface-1 p-4">
      <h3 className="mb-3 text-[13px] font-medium text-text-secondary">
        Return Kumulatif dari Waktu ke Waktu (Non-Kompound, Sum)
      </h3>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1a2233" />
          <XAxis
            dataKey="date"
            tick={{ fill: "#94a3b8", fontSize: 10.5 }}
            axisLine={{ stroke: "#232b3d" }}
            tickLine={false}
            tickFormatter={(v) => formatDateId(v)}
            minTickGap={40}
          />
          <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip
            contentStyle={{ background: "#1e2740", border: "1px solid #2e3850", borderRadius: 8, fontSize: 12 }}
            labelStyle={{ color: "#f1f5f9" }}
            labelFormatter={(v) => formatDateId(v as string)}
            formatter={(v) => formatPctId(Number(v))}
          />
          <Line
            type="monotone"
            dataKey="cumReturn"
            stroke="var(--brand)"
            strokeWidth={2}
            dot={{ r: 2, fill: "var(--brand)" }}
          />
        </LineChart>
      </ResponsiveContainer>
      <p className="mt-2 text-[11.5px] text-text-muted">
        Grafik ini adalah penjumlahan (bukan compounding) return_pct tiap trade closed, asumsi ukuran
        posisi sama rata — bukan equity curve portfolio riil.
      </p>
    </div>
  );
}
