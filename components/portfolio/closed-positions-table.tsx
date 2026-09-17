"use client";

import * as React from "react";
import Link from "next/link";

import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableSortHead,
  TableCell,
} from "@/components/ui/table";
import { closedStatusToReason, exitReasonColor, exitReasonLabel } from "@/lib/constants";
import { formatDateId, formatPctId } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { ClosedPosition } from "@/lib/types";

type SortKey = "ticker" | "sektor" | "entry_date" | "exit_date" | "return_pct" | "hold_days";

export function ClosedPositionsTable({ positions }: { positions: ClosedPosition[] }) {
  const [sortKey, setSortKey] = React.useState<SortKey>("exit_date");
  const [sortDesc, setSortDesc] = React.useState(true);

  const sortedPositions = React.useMemo(() => {
    return [...positions].sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (av == null) return 1;
      if (bv == null) return -1;
      if (typeof av === "string" || typeof bv === "string") {
        return sortDesc ? String(bv).localeCompare(String(av)) : String(av).localeCompare(String(bv));
      }
      return sortDesc ? (bv as number) - (av as number) : (av as number) - (bv as number);
    });
  }, [positions, sortKey, sortDesc]);

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
                isSorted={sortKey === "ticker"}
                sortDirection={sortKey === "ticker" ? (sortDesc ? "desc" : "asc") : undefined}
                onSort={() => toggleSort("ticker")}
              >
                Ticker
              </TableSortHead>
              <TableSortHead
                isSorted={sortKey === "sektor"}
                sortDirection={sortKey === "sektor" ? (sortDesc ? "desc" : "asc") : undefined}
                onSort={() => toggleSort("sektor")}
              >
                Sektor
              </TableSortHead>
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
            {sortedPositions.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="h-28 text-center text-xs text-text-muted">
                  Tidak ada posisi closed yang cocok dengan kriteria filter saat ini.
                </TableCell>
              </TableRow>
            ) : (
              sortedPositions.map((p, i) => {
                const reason = closedStatusToReason(p.status);
                const color = exitReasonColor(reason);
                const positive = p.return_pct >= 0;

                return (
                  <TableRow
                    key={`${p.ticker}-${p.exit_date}-${i}`}
                    className="border-border-subtle transition-colors"
                  >
                    <TableCell className="font-mono font-semibold text-text-primary">
                      <Link
                        href={`/detail/${p.ticker}`}
                        className="transition-colors hover:text-brand hover:underline"
                      >
                        {p.ticker}
                      </Link>
                    </TableCell>
                    <TableCell className="text-text-secondary text-xs">
                      {p.sektor.replaceAll("_", " ")}
                    </TableCell>
                    <TableCell className="font-mono text-xs text-text-secondary">
                      {formatDateId(p.entry_date)}
                    </TableCell>
                    <TableCell className="font-mono text-xs text-text-secondary">
                      {formatDateId(p.exit_date)}
                    </TableCell>
                    <TableCell
                      className={cn(
                        "text-right font-mono font-semibold text-xs",
                        positive ? "text-bullish" : "text-bearish",
                      )}
                    >
                      {formatPctId(p.return_pct)}
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
                        {exitReasonLabel(reason)}
                      </span>
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs text-text-secondary">
                      {p.hold_days}h
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
