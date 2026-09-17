"use client";

import * as React from "react";

import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableSortHead,
  TableCell,
} from "@/components/ui/table";
import { formatIdr, formatPctId, formatDateId } from "@/lib/format";
import { exitReasonColor, exitReasonLabel } from "@/lib/constants";
import { cn } from "@/lib/utils";
import type { TradeRow } from "@/lib/types";

type SortKey = "entry_date" | "exit_date" | "entry_price" | "exit_price" | "return_pct" | "hold_days";

export function TradeHistoryTable({ trades }: { trades: TradeRow[] }) {
  const [sortKey, setSortKey] = React.useState<SortKey>("exit_date");
  const [sortDesc, setSortDesc] = React.useState(true);

  const sortedTrades = React.useMemo(() => {
    return [...trades].sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (av == null) return 1;
      if (bv == null) return -1;
      if (typeof av === "string" || typeof bv === "string") {
        return sortDesc ? String(bv).localeCompare(String(av)) : String(av).localeCompare(String(bv));
      }
      return sortDesc ? (bv as number) - (av as number) : (av as number) - (bv as number);
    });
  }, [trades, sortKey, sortDesc]);

  function toggleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDesc((d) => !d);
    } else {
      setSortKey(key);
      setSortDesc(true);
    }
  }

  return (
    <div className="overflow-hidden rounded-lg border border-border bg-surface-1">
      <div className="max-h-[440px] overflow-auto">
        <Table>
          <TableHeader className="sticky top-0 z-10 bg-surface-1/95 backdrop-blur-xs">
            <TableRow className="hover:bg-transparent">
              <TableSortHead
                isSorted={sortKey === "entry_date"}
                sortDirection={sortKey === "entry_date" ? (sortDesc ? "desc" : "asc") : undefined}
                onSort={() => toggleSort("entry_date")}
              >
                Entry
              </TableSortHead>
              <TableSortHead
                isSorted={sortKey === "exit_date"}
                sortDirection={sortKey === "exit_date" ? (sortDesc ? "desc" : "asc") : undefined}
                onSort={() => toggleSort("exit_date")}
              >
                Exit
              </TableSortHead>
              <TableSortHead
                isSorted={sortKey === "entry_price"}
                sortDirection={sortKey === "entry_price" ? (sortDesc ? "desc" : "asc") : undefined}
                onSort={() => toggleSort("entry_price")}
                className="text-right"
              >
                Harga Entry
              </TableSortHead>
              <TableSortHead
                isSorted={sortKey === "exit_price"}
                sortDirection={sortKey === "exit_price" ? (sortDesc ? "desc" : "asc") : undefined}
                onSort={() => toggleSort("exit_price")}
                className="text-right"
              >
                Harga Exit
              </TableSortHead>
              <TableSortHead
                isSorted={sortKey === "return_pct"}
                sortDirection={sortKey === "return_pct" ? (sortDesc ? "desc" : "asc") : undefined}
                onSort={() => toggleSort("return_pct")}
                className="text-right"
              >
                Return
              </TableSortHead>
              <TableHead>Alasan Exit</TableHead>
              <TableSortHead
                isSorted={sortKey === "hold_days"}
                sortDirection={sortKey === "hold_days" ? (sortDesc ? "desc" : "asc") : undefined}
                onSort={() => toggleSort("hold_days")}
                className="text-right"
              >
                Hold
              </TableSortHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedTrades.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="h-28 text-center text-xs text-text-muted">
                  Belum ada riwayat transaksi tertutup (closed trades) untuk emiten ini.
                </TableCell>
              </TableRow>
            ) : (
              sortedTrades.map((t, i) => {
                const color = exitReasonColor(t.reason);
                const positive = t.return_pct >= 0;

                return (
                  <TableRow
                    key={`${t.entry_date}-${t.exit_date}-${i}`}
                    className="border-border-subtle transition-colors"
                  >
                    <TableCell className="font-mono text-xs text-text-primary">
                      {formatDateId(t.entry_date)}
                    </TableCell>
                    <TableCell className="font-mono text-xs text-text-primary">
                      {formatDateId(t.exit_date)}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs text-text-secondary">
                      {formatIdr(t.entry_price)}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs text-text-secondary">
                      {formatIdr(t.exit_price)}
                    </TableCell>
                    <TableCell
                      className={cn(
                        "text-right font-mono font-semibold text-xs",
                        positive ? "text-bullish" : "text-bearish",
                      )}
                    >
                      {formatPctId(t.return_pct)}
                    </TableCell>
                    <TableCell>
                      <span
                        className="inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium"
                        style={{
                          color,
                          borderColor: `color-mix(in srgb, ${color} 35%, transparent)`,
                          backgroundColor: `color-mix(in srgb, ${color} 10%, transparent)`,
                        }}
                      >
                        {exitReasonLabel(t.reason)}
                      </span>
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs text-text-secondary">
                      {t.hold_days}h
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
