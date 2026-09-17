import Link from "next/link";
import { Card } from "@/components/ui/card";
import { SignalBadge } from "@/components/shared/signal-badge";
import { ConvictionMeter } from "@/components/shared/conviction-meter";
import { formatDateId } from "@/lib/format";
import type { BuyTomorrowRow } from "@/lib/types";
import { CheckCircle2, ChevronRight } from "lucide-react";

export function BuyTomorrowGrid({ rows }: { rows: BuyTomorrowRow[] }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
      {rows.map((row) => (
        <Link
          key={row.ticker}
          href={`/detail/${row.ticker}`}
          className="group focus:outline-none"
        >
          <Card className="gap-2.5 px-3.5 py-3.5 transition-all duration-150 group-hover:border-emerald-500/40 group-hover:-translate-y-0.5 group-hover:shadow-sm">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-1 font-mono text-[15px] font-semibold text-text-primary group-hover:text-emerald-400 transition-colors">
                  <span>{row.ticker}</span>
                  <ChevronRight className="size-3.5 opacity-0 -translate-x-1 group-hover:opacity-100 group-hover:translate-x-0 transition-all text-emerald-400" />
                </div>
                <div className="text-[11px] text-text-muted">{row.sektor ?? "–"}</div>
              </div>
              <SignalBadge signal="BUY" />
            </div>

            <div className="flex items-center gap-1 text-[11px] font-medium text-emerald-400/90">
              <CheckCircle2 className="size-3 shrink-0" />
              <span>Hard Gate Uptrend Valid</span>
            </div>

            <ConvictionMeter filled={row.signal_strength ?? 0} total={3} signal="BUY" />

            <div className="flex items-center justify-between border-t border-border pt-2 text-[11.5px]">
              <span className="text-text-secondary">Eksekusi Open</span>
              <span className="font-mono font-medium text-text-primary">
                {formatDateId(row.planned_entry_date)}
              </span>
            </div>
          </Card>
        </Link>
      ))}
    </div>
  );
}
