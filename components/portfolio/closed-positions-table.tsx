import { closedStatusToReason, exitReasonColor, exitReasonLabel } from "@/lib/constants";
import { formatDateId, formatPctId } from "@/lib/format";
import type { ClosedPosition } from "@/lib/types";

export function ClosedPositionsTable({ positions }: { positions: ClosedPosition[] }) {
  return (
    <div className="overflow-hidden rounded-lg border border-border">
      <div className="max-h-[420px] overflow-auto">
        <table className="w-full text-[12.5px]">
          <thead className="sticky top-0 bg-surface-1 text-text-secondary">
            <tr>
              <th className="px-3 py-2 text-left font-medium">Ticker</th>
              <th className="px-3 py-2 text-left font-medium">Sektor</th>
              <th className="px-3 py-2 text-left font-medium">Entry</th>
              <th className="px-3 py-2 text-left font-medium">Exit</th>
              <th className="px-3 py-2 text-right font-medium">Return</th>
              <th className="px-3 py-2 text-left font-medium">Alasan</th>
              <th className="px-3 py-2 text-right font-medium">Hold</th>
            </tr>
          </thead>
          <tbody>
            {positions.map((p, i) => {
              const reason = closedStatusToReason(p.status);
              const color = exitReasonColor(reason);
              const positive = p.return_pct >= 0;
              return (
                <tr
                  key={`${p.ticker}-${p.exit_date}-${i}`}
                  className="border-t border-border-subtle"
                  style={{ backgroundColor: `color-mix(in srgb, ${color} 8%, transparent)` }}
                >
                  <td className="px-3 py-2 font-mono font-medium text-text-primary">{p.ticker}</td>
                  <td className="px-3 py-2 text-text-secondary">{p.sektor.replaceAll("_", " ")}</td>
                  <td className="px-3 py-2 font-mono">{formatDateId(p.entry_date)}</td>
                  <td className="px-3 py-2 font-mono">{formatDateId(p.exit_date)}</td>
                  <td
                    className="px-3 py-2 text-right font-mono font-semibold"
                    style={{ color: positive ? "var(--bullish)" : "var(--bearish)" }}
                  >
                    {formatPctId(p.return_pct)}
                  </td>
                  <td className="px-3 py-2" style={{ color }}>
                    {exitReasonLabel(reason)}
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-text-secondary">{p.hold_days}h</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {positions.length === 0 && (
        <p className="px-3 py-6 text-center text-[12.5px] text-text-muted">
          Tidak ada posisi closed yang cocok dengan filter di atas.
        </p>
      )}
    </div>
  );
}
