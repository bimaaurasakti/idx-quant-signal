"use client";

import * as React from "react";
import { ArrowDownRight, ArrowUpRight, CheckCircle2, History } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { exitReasonColor, exitReasonLabel } from "@/lib/constants";
import { formatIdr, formatNumberId, formatPctId } from "@/lib/format";
import type { TradeRow } from "@/lib/types";

interface ReplayTradesTableProps {
  trades: TradeRow[];
  ticker: string;
}

export function ReplayTradesTable({ trades, ticker }: ReplayTradesTableProps) {
  if (trades.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-border/80 bg-surface-1/50 p-8 text-center">
        <div className="flex size-10 items-center justify-center rounded-full bg-surface-2 text-text-muted">
          <History className="size-5" />
        </div>
        <div className="text-xs font-semibold text-text-primary">
          Belum Ada Posisi yang Selesai (Closed)
        </div>
        <div className="max-w-md text-[11.5px] text-text-muted">
          Trade yang dieksekusi akan otomatis tercatat di tabel ini saat lilin replay menyentuh tanggal exit.
          Tekan tombol <strong className="text-text-primary">Play (Space)</strong> atau <strong className="text-text-primary">Step Forward</strong> untuk memutar simulasi.
        </div>
      </div>
    );
  }

  // Tampilkan urutan trade terbaru di atas
  const reversedTrades = [...trades].reverse();

  return (
    <div className="overflow-hidden rounded-xl border border-border/80 bg-surface-1/90 shadow-sm">
      <div className="flex items-center justify-between border-b border-border/60 px-4 py-3">
        <div className="flex items-center gap-2">
          <History className="size-4 text-brand" />
          <span className="text-xs font-semibold text-text-primary">
            Daftar Posisi Selesai ({trades.length} Trade)
          </span>
        </div>
        <span className="font-mono text-[11px] text-text-muted">
          Emiten: {ticker}
        </span>
      </div>

      <div className="max-h-80 overflow-y-auto">
        <Table>
          <TableHeader className="bg-surface-2/60 sticky top-0 backdrop-blur-xs">
            <TableRow className="border-border/60 text-[11px]">
              <TableHead className="w-12 text-center">#</TableHead>
              <TableHead>Tgl Entry</TableHead>
              <TableHead>Harga Beli</TableHead>
              <TableHead>Tgl Exit</TableHead>
              <TableHead>Harga Jual</TableHead>
              <TableHead className="text-right">Return PnL</TableHead>
              <TableHead>Alasan Exit</TableHead>
              <TableHead className="text-right">Hold</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody className="divide-y divide-border/40 text-xs font-mono">
            {reversedTrades.map((t, idx) => {
              const isProfit = t.return_pct >= 0;
              const reasonTone = exitReasonColor(t.reason);
              const originalIndex = trades.length - idx;

              return (
                <TableRow key={`${t.entry_date}-${t.exit_date}-${idx}`} className="hover:bg-surface-2/40 transition-colors">
                  <TableCell className="text-center font-normal text-text-muted text-[11px]">
                    {originalIndex}
                  </TableCell>
                  <TableCell className="text-text-primary">{t.entry_date}</TableCell>
                  <TableCell className="text-text-secondary">{formatIdr(t.entry_price)}</TableCell>
                  <TableCell className="text-text-primary">{t.exit_date}</TableCell>
                  <TableCell className="text-text-secondary">{formatIdr(t.exit_price)}</TableCell>
                  <TableCell className="text-right">
                    <span
                      className={`inline-flex items-center gap-1 font-bold ${
                        isProfit ? "text-emerald-400" : "text-rose-400"
                      }`}
                    >
                      {isProfit ? <ArrowUpRight className="size-3.5" /> : <ArrowDownRight className="size-3.5" />}
                      {formatPctId(t.return_pct)}
                    </span>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="outline"
                      className="font-mono text-[10px] font-medium"
                      style={{
                        borderColor: `var(--${reasonTone})`,
                        color: `var(--${reasonTone})`,
                        backgroundColor: `var(--${reasonTone}-bg)`,
                      }}
                    >
                      {exitReasonLabel(t.reason)}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right text-text-secondary">
                    {t.hold_days} hr
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
