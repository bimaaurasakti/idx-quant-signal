import { SignalBadge } from "@/components/shared/signal-badge";
import { ConvictionMeter } from "@/components/shared/conviction-meter";
import { formatIdr, formatPctId } from "@/lib/format";

interface PriceHeaderProps {
  ticker: string;
  sektor: string | null;
  price: number | null;
  change: number | null;
  changePct: number | null;
  signal: string | null;
  filled: number;
  total: number;
}

export function PriceHeader({
  ticker,
  sektor,
  price,
  change,
  changePct,
  signal,
  filled,
  total,
}: PriceHeaderProps) {
  const positive = (change ?? 0) >= 0;
  return (
    <div className="flex flex-wrap items-center justify-between gap-4 rounded-lg border border-border bg-surface-1 px-5 py-4">
      <div>
        <div className="text-[12.5px] text-text-secondary">{sektor ?? "–"}</div>
        <div className="font-mono text-[22px] font-bold text-text-primary">{ticker}</div>
        <div className="mt-1 flex items-baseline gap-2">
          <span className="font-mono text-[32px] font-bold text-text-primary">{formatIdr(price)}</span>
          {change != null && changePct != null && (
            <span
              className="rounded-full px-2 py-0.5 font-mono text-[12px] font-semibold"
              style={{
                backgroundColor: positive ? "var(--bullish-bg)" : "var(--bearish-bg)",
                color: positive ? "var(--bullish)" : "var(--bearish)",
              }}
            >
              {formatIdr(change)} ({formatPctId(changePct)})
            </span>
          )}
        </div>
      </div>
      <div className="flex flex-col items-end gap-2">
        <SignalBadge signal={signal} />
        <ConvictionMeter filled={filled} total={total} signal={signal} />
      </div>
    </div>
  );
}
