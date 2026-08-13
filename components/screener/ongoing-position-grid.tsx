import { Card } from "@/components/ui/card";
import { formatIdr, formatPctId, formatDateId } from "@/lib/format";
import type { OpenPositionRow } from "@/lib/types";

export function OngoingPositionGrid({ rows }: { rows: OpenPositionRow[] }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
      {rows.map((row) => {
        const positive = (row.return_pct_now ?? 0) >= 0;
        return (
          <Card key={row.ticker} className="gap-2.5 px-3.5 py-3.5">
            <div className="flex items-start justify-between">
              <div>
                <div className="font-mono text-[15px] font-semibold text-text-primary">
                  {row.ticker}
                </div>
                <div className="text-[11.5px] text-text-muted">
                  {row.sektor ?? "–"} &bull; entry {formatDateId(row.entry_date)}
                </div>
              </div>
              <span
                className="font-mono text-[15px] font-semibold"
                style={{ color: positive ? "var(--bullish)" : "var(--bearish)" }}
              >
                {formatPctId(row.return_pct_now)}
              </span>
            </div>
            <div className="flex justify-between border-t border-border pt-2 text-[11.5px]">
              <div>
                <div className="text-text-secondary">Entry</div>
                <div className="font-mono text-text-primary">{formatIdr(row.entry_price)}</div>
              </div>
              <div className="text-right">
                <div className="text-text-secondary">TP</div>
                <div className="font-mono" style={{ color: "var(--bullish)" }}>
                  {formatIdr(row.tp_price)}
                </div>
              </div>
              <div className="text-right">
                <div className="text-text-secondary">SL</div>
                <div className="font-mono" style={{ color: "var(--bearish)" }}>
                  {formatIdr(row.sl_price)}
                </div>
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
}
