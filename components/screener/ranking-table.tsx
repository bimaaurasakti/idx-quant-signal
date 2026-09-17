"use client";

import * as React from "react";
import Link from "next/link";
import { Search } from "lucide-react";

import { SignalBadge } from "@/components/shared/signal-badge";
import { Input } from "@/components/ui/input";
import { Select, type SelectOption } from "@/components/ui/select";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableSortHead,
  TableCell,
} from "@/components/ui/table";
import { formatIdr, formatPctId, formatNumberId } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { ScreenerRow } from "@/lib/types";

type SortKey = keyof Pick<
  ScreenerRow,
  "ticker" | "last_close" | "winrate" | "expectancy_pct" | "profit_factor" | "max_drawdown_pct" | "n_trades"
>;

interface ColumnDef {
  key: SortKey;
  label: string;
  align?: "left" | "right";
}

const COLUMNS: ColumnDef[] = [
  { key: "ticker", label: "Ticker", align: "left" },
  { key: "last_close", label: "Harga", align: "right" },
  { key: "winrate", label: "Winrate", align: "right" },
  { key: "expectancy_pct", label: "Expectancy", align: "right" },
  { key: "profit_factor", label: "P.Factor", align: "right" },
  { key: "max_drawdown_pct", label: "Max DD", align: "right" },
  { key: "n_trades", label: "Trades", align: "right" },
];

export function RankingTable({ rows }: { rows: ScreenerRow[] }) {
  const [sortKey, setSortKey] = React.useState<SortKey>("expectancy_pct");
  const [sortDesc, setSortDesc] = React.useState(true);
  const [sectorFilter, setSectorFilter] = React.useState<string>("ALL");
  const [searchQuery, setSearchQuery] = React.useState<string>("");

  const sectors = React.useMemo(
    () => Array.from(new Set(rows.map((r) => r.sektor).filter(Boolean))).sort() as string[],
    [rows],
  );

  const sectorOptions: SelectOption[] = React.useMemo(
    () => [
      { value: "ALL", label: "Semua Sektor" },
      ...sectors.map((s) => ({
        value: s,
        label: s.replaceAll("_", " "),
      })),
    ],
    [sectors],
  );

  const filtered = React.useMemo(() => {
    let base = rows;
    if (sectorFilter && sectorFilter !== "ALL") {
      base = base.filter((r) => r.sektor === sectorFilter);
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      base = base.filter(
        (r) =>
          r.ticker.toLowerCase().includes(q) ||
          (r.sektor && r.sektor.toLowerCase().includes(q)),
      );
    }

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
  }, [rows, sectorFilter, searchQuery, sortKey, sortDesc]);

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
      {/* Interactive Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border p-3">
        <div className="flex flex-wrap items-center gap-2.5">
          <div className="w-[180px]">
            <Select
              value={sectorFilter}
              onValueChange={setSectorFilter}
              options={sectorOptions}
              placeholder="Pilih Sektor"
              triggerClassName="h-8 text-xs bg-surface-2"
            />
          </div>
          <Input
            prefix={<Search className="size-3.5 text-text-muted" />}
            placeholder="Cari emiten / sektor..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onClear={() => setSearchQuery("")}
            className="h-8 w-[160px] bg-surface-2 text-xs sm:w-[210px]"
          />
        </div>
        <span className="font-mono text-xs text-text-muted">
          {filtered.length} emiten ditampilkan
        </span>
      </div>

      {/* Modern High-Performance Table */}
      <div className="max-h-[440px] overflow-auto">
        <Table>
          <TableHeader className="sticky top-0 z-10 bg-surface-1/95 backdrop-blur-xs">
            <TableRow className="hover:bg-transparent">
              {COLUMNS.map((col) => (
                <TableSortHead
                  key={col.key}
                  isSorted={sortKey === col.key}
                  sortDirection={sortKey === col.key ? (sortDesc ? "desc" : "asc") : undefined}
                  onSort={() => toggleSort(col.key)}
                  className={cn(col.align === "right" && "text-right")}
                >
                  {col.label}
                </TableSortHead>
              ))}
              <TableHead className="w-[110px]">Sinyal</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.length === 0 ? (
              <TableRow>
                <TableCell colSpan={COLUMNS.length + 1} className="h-28 text-center text-xs text-text-muted">
                  Tidak ada emiten yang sesuai dengan kriteria filter.
                </TableCell>
              </TableRow>
            ) : (
              filtered.map((row) => (
                <TableRow key={row.ticker} className="border-border-subtle">
                  <TableCell className="font-mono font-medium text-text-primary">
                    <Link
                      href={`/detail/${row.ticker}`}
                      className="transition-colors hover:text-brand hover:underline"
                    >
                      {row.ticker}
                    </Link>
                  </TableCell>
                  <TableCell className="text-right font-mono text-text-secondary">
                    {formatIdr(row.last_close)}
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {row.winrate != null ? `${formatNumberId(row.winrate, 1)}%` : "–"}
                  </TableCell>
                  <TableCell
                    className="text-right font-mono font-semibold"
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
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {row.profit_factor != null ? formatNumberId(row.profit_factor, 2) : "–"}
                  </TableCell>
                  <TableCell
                    className="text-right font-mono"
                    style={{ color: "var(--bearish)" }}
                  >
                    {formatPctId(row.max_drawdown_pct)}
                  </TableCell>
                  <TableCell className="text-right font-mono text-text-secondary">
                    {row.n_trades ?? "–"}
                  </TableCell>
                  <TableCell>
                    <SignalBadge signal={row.signal_today} />
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
