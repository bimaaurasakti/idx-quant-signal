import { SignalBadge } from "@/components/shared/signal-badge";
import { formatIdr, formatPctId } from "@/lib/format";

interface PriceHeaderProps {
  ticker: string;
  sektor: string | null;
  price: number | null;
  change: number | null;
  changePct: number | null;
  signal: string | null;
  hasActivePosition?: boolean;
}

export function PriceHeader({
  ticker,
  sektor,
  price,
  change,
  changePct,
  signal,
  hasActivePosition = false,
}: PriceHeaderProps) {
  const positive = (change ?? 0) >= 0;

  // Resolusi status sinyal yang jelas dan tidak ambigu:
  // 1. BUY: ada sinyal beli hari ini
  // 2. Jika punya posisi aktif terbuka: HOLD_ACTIVE -> "Hold (Posisi Aktif)"
  // 3. Jika tidak punya posisi & tidak ada sinyal beli: WAIT & SEE -> "Wait & See"
  const s = (signal ?? "").toUpperCase();
  const resolvedSignal =
    s === "BUY" ? "BUY" : hasActivePosition ? "HOLD_ACTIVE" : "WAIT & SEE";

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
      <div className="flex flex-col items-end gap-1.5">
        <SignalBadge signal={resolvedSignal} />
      </div>
    </div>
  );
}
