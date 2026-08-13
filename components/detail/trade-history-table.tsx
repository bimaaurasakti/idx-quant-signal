import { formatIdr, formatPctId, formatDateId } from "@/lib/format";
import { exitReasonColor, exitReasonLabel } from "@/lib/constants";
import type { TradeRow } from "@/lib/types";

export function TradeHistoryTable({ trades }: { trades: TradeRow[] }) {
  return (
    <div className="overflow-hidden rounded-lg border border-border">
      <table className="w-full text-[12.5px]">
        <thead className="bg-surface-1 text-text-secondary">
          <tr>
            <th className="px-3 py-2 text-left font-medium">Entry</th>
            <th className="px-3 py-2 text-left font-medium">Exit</th>
            <th className="px-3 py-2 text-right font-medium">Harga Entry</th>
            <th className="px-3 py-2 text-right font-medium">Harga Exit</th>
            <th className="px-3 py-2 text-right font-medium">Return</th>
            <th className="px-3 py-2 text-left font-medium">Alasan Exit</th>
            <th className="px-3 py-2 text-right font-medium">Hold</th>
          </tr>
        </thead>
        <tbody>
          {trades.map((t, i) => {
            const color = exitReasonColor(t.reason);
            const positive = t.return_pct >= 0;
            return (
              <tr
                key={`${t.entry_date}-${i}`}
                className="border-t border-border-subtle"
                style={{ backgroundColor: `color-mix(in srgb, ${color} 10%, transparent)` }}
              >
                <td className="px-3 py-2 font-mono text-text-primary">{formatDateId(t.entry_date)}</td>
                <td className="px-3 py-2 font-mono text-text-primary">{formatDateId(t.exit_date)}</td>
                <td className="px-3 py-2 text-right font-mono">{formatIdr(t.entry_price)}</td>
                <td className="px-3 py-2 text-right font-mono">{formatIdr(t.exit_price)}</td>
                <td
                  className="px-3 py-2 text-right font-mono font-semibold"
                  style={{ color: positive ? "var(--bullish)" : "var(--bearish)" }}
                >
                  {formatPctId(t.return_pct)}
                </td>
                <td className="px-3 py-2">
                  <span className="text-[12px]" style={{ color }}>
                    {exitReasonLabel(t.reason)}
                  </span>
                </td>
                <td className="px-3 py-2 text-right font-mono text-text-secondary">{t.hold_days}h</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
