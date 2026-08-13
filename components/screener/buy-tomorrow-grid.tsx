import { Card } from "@/components/ui/card";
import { SignalBadge } from "@/components/shared/signal-badge";
import { ConvictionMeter } from "@/components/shared/conviction-meter";
import { formatDateId } from "@/lib/format";
import type { BuyTomorrowRow } from "@/lib/types";

export function BuyTomorrowGrid({ rows }: { rows: BuyTomorrowRow[] }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
      {rows.map((row) => (
        <Card key={row.ticker} className="gap-2 px-3.5 py-3.5">
          <div className="flex items-start justify-between">
            <div>
              <div className="font-mono text-[15px] font-semibold text-text-primary">
                {row.ticker}
              </div>
              <div className="text-[11.5px] text-text-muted">{row.sektor ?? "–"}</div>
            </div>
            <SignalBadge signal="BUY" />
          </div>
          <ConvictionMeter filled={row.signal_strength ?? 0} total={3} signal="BUY" />
          <div className="flex items-center justify-between border-t border-border pt-2 text-[12px]">
            <span className="text-text-secondary">Entry</span>
            <span className="font-mono text-text-primary">
              {formatDateId(row.planned_entry_date)}
            </span>
          </div>
        </Card>
      ))}
    </div>
  );
}
