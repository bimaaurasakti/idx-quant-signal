"use client";

import * as React from "react";

import { SignalBadge } from "@/components/shared/signal-badge";
import { formatIdr, formatPctId, formatNumberId } from "@/lib/format";
import type { ScreenerRow } from "@/lib/types";

type SortKey = keyof Pick<
  ScreenerRow,
  "ticker" | "last_close" | "winrate" | "expectancy_pct" | "profit_factor" | "max_drawdown_pct" | "n_trades"
>;

export function RankingTable({ rows }: { rows: ScreenerRow[] }) {
  const [sortKey, setSortKey] = React.useState<SortKey>("expectancy_pct");
  const [sortDesc, setSortDesc] = React.useState(true);
  const [sectorFilter, setSectorFilter] = React.useState<string>("");

  const sectors = React.useMemo(
    () => Array.from(new Set(rows.map((r) => r.sektor).filter(Boolean))).sort() as string[],
    [rows],
  );

  const filtered = React.useMemo(() => {
    const base = sectorFilter ? rows.filter((r) => r.sektor === sectorFilter) : rows;
    return [...base].sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (av == null) return 1;
      if (bv == null) return -1;
      if (typeof av === "string" || typeof bv === "string") {
        return sortDesc ? String(bv).localeCompare(String(av)) : String(av).localeCompare(String(bv));
      }
      return sortDesc ? (bv as number) - (av as number) : (av as number) - (bv as number);
    });
  }, [rows, sectorFilter, sortKey, sortDesc]);

  function toggleSort(key: SortKey) {
    if (key === sortKey) setSortDesc((d) => !d);
    else {
      setSortKey(key);
      setSortDesc(true);
    }
  }

  const columns: { key: SortKey; label: string }[] = [
    { key: "ticker", label: "Ticker" },
    { key: "last_close", label: "Harga" },
    { key: "winrate", label: "Winrate" },
    { key: "expectancy_pct", label: "Expectancy" },
    { key: "profit_factor", label: "P.Factor" },
    { key: "max_drawdown_pct", label: "Max DD" },
    { key: "n_trades", label: "Trades" },
  ];

  return (
    <div className="rounded-lg border border-border">
      <div className="flex items-center justify-between border-b border-border px-3 py-2">
        <select
          value={sectorFilter}
          onChange={(e) => setSectorFilter(e.target.value)}
          className="rounded-md border border-border bg-surface-1 px-2 py-1 text-[12.5px] text-text-primary"
        >
          <option value="">Semua sektor</option>
          {sectors.map((s) => (
            <option key={s} value={s}>
              {s.replaceAll("_", " ")}
            </option>
          ))}
        </select>
        <span className="text-[12px] text-text-muted">{filtered.length} saham</span>
      </div>
      <div className="max-h-[420px] overflow-auto">
        <table className="w-full text-[12.5px]">
          <thead className="sticky top-0 bg-surface-1 text-text-secondary">
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  onClick={() => toggleSort(col.key)}
                  className="cursor-pointer select-none px-3 py-2 text-right font-medium first:text-left"
                >
                  {col.label}
                  {sortKey === col.key && (sortDesc ? " ↓" : " ↑")}
                </th>
              ))}
              <th className="px-3 py-2 text-left font-medium">Sinyal</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((row) => (
              <tr key={row.ticker} className="border-t border-border-subtle hover:bg-surface-1">
                <td className="px-3 py-2 font-mono font-medium text-text-primary">{row.ticker}</td>
                <td className="px-3 py-2 text-right font-mono">{formatIdr(row.last_close)}</td>
                <td className="px-3 py-2 text-right font-mono">
                  {row.winrate != null ? `${formatNumberId(row.winrate, 1)}%` : "–"}
                </td>
                <td
                  className="px-3 py-2 text-right font-mono"
                  style={{
                    color:
                      (row.expectancy_pct ?? 0) > 0
                        ? "var(--bullish)"
                        : (row.expectancy_pct ?? 0) < 0
                          ? "var(--bearish)"
                          : "var(--text-primary)",
                  }}
                >
                  {formatPctId(row.expectancy_pct)}
                </td>
                <td className="px-3 py-2 text-right font-mono">
                  {row.profit_factor != null ? formatNumberId(row.profit_factor, 2) : "–"}
                </td>
                <td className="px-3 py-2 text-right font-mono" style={{ color: "var(--bearish)" }}>
                  {formatPctId(row.max_drawdown_pct)}
                </td>
                <td className="px-3 py-2 text-right font-mono">{row.n_trades ?? "–"}</td>
                <td className="px-3 py-2">
                  <SignalBadge signal={row.signal_today} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
