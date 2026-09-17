import Link from "next/link";
import { Card } from "@/components/ui/card";
import { formatIdr, formatPctId, formatDateId } from "@/lib/format";
import type { OpenPositionRow } from "@/lib/types";
import { ShieldCheck, ChevronRight } from "lucide-react";

export function OngoingPositionGrid({ rows }: { rows: OpenPositionRow[] }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
      {rows.map((row) => {
        const positive = (row.return_pct_now ?? 0) >= 0;
        const isRunner =
          row.sl_price != null &&
          row.entry_price != null &&
          row.sl_price >= row.entry_price;

        return (
          <Link
            key={row.ticker}
            href={`/detail/${row.ticker}`}
            className="group focus:outline-none"
          >
            <Card className="gap-2.5 px-3.5 py-3.5 transition-all duration-150 group-hover:border-blue-500/40 group-hover:-translate-y-0.5 group-hover:shadow-sm">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-1.5 font-mono text-[15px] font-semibold text-text-primary group-hover:text-blue-400 transition-colors">
                    <span>{row.ticker}</span>
                    <ChevronRight className="size-3.5 opacity-0 -translate-x-1 group-hover:opacity-100 group-hover:translate-x-0 transition-all text-blue-400" />
                  </div>
                  <div className="text-[11px] text-text-muted">
                    {row.sektor ?? "–"} &bull; {formatDateId(row.entry_date)}
                  </div>
                </div>
                <span
                  className="font-mono text-[15px] font-semibold"
                  style={{ color: positive ? "var(--bullish)" : "var(--bearish)" }}
                >
                  {formatPctId(row.return_pct_now)}
                </span>
              </div>

              {isRunner ? (
                <div className="flex items-center gap-1 text-[10.5px] font-semibold text-emerald-400">
                  <ShieldCheck className="size-3.5 shrink-0" />
                  <span>Runner Aktif (SL di Break-Even)</span>
                </div>
              ) : (
                <div className="text-[10.5px] text-text-secondary">
                  Fase 1: Toleransi SL 1.5 ATR
                </div>
              )}

              <div className="flex justify-between border-t border-border pt-2 text-[11.5px]">
                <div>
                  <div className="text-text-secondary">Entry</div>
                  <div className="font-mono text-text-primary">{formatIdr(row.entry_price)}</div>
                </div>
                <div className="text-right">
                  <div className="text-text-secondary">TP1 (+2 ATR)</div>
                  <div className="font-mono" style={{ color: "var(--bullish)" }}>
                    {formatIdr(row.tp_price)}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-text-secondary">SL</div>
                  <div
                    className="font-mono"
                    style={{
                      color: isRunner ? "var(--bullish)" : "var(--bearish)",
                    }}
                  >
                    {formatIdr(row.sl_price)}
                    {isRunner && <span className="ml-0.5 text-[9.5px] font-sans font-bold">(BE)</span>}
                  </div>
                </div>
              </div>
            </Card>
          </Link>
        );
      })}
    </div>
  );
}
