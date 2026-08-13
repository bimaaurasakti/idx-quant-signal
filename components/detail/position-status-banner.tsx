import { formatIdr, formatDateId } from "@/lib/format";
import type { ActivePosition } from "@/lib/types";

export function PositionStatusBanner({ position }: { position: ActivePosition }) {
  if (position.status === "PENDING_ENTRY") {
    return (
      <div
        className="rounded-lg border-l-4 px-4 py-3 text-[13.5px]"
        style={{ borderLeftColor: "var(--info)", backgroundColor: "var(--info-bg)" }}
      >
        <span className="text-text-primary">
          🎯 Sinyal BUY aktif — rencana entry{" "}
          <span className="font-mono font-semibold">{formatDateId(position.planned_entry_date)}</span>.
        </span>
      </div>
    );
  }

  return (
    <div
      className="rounded-lg border-l-4 px-4 py-3 text-[13.5px]"
      style={{ borderLeftColor: "var(--bullish)", backgroundColor: "var(--bullish-bg)" }}
    >
      <span className="text-text-primary">
        📌 Posisi <span className="font-semibold">OPEN</span> sejak{" "}
        <span className="font-mono">{formatDateId(position.entry_date)}</span> di harga{" "}
        <span className="font-mono">{formatIdr(position.entry_price)}</span> &bull; TP:{" "}
        <span className="font-mono" style={{ color: "var(--bullish)" }}>
          {formatIdr(position.tp_price)}
        </span>{" "}
        &bull; SL:{" "}
        <span className="font-mono" style={{ color: "var(--bearish)" }}>
          {formatIdr(position.sl_price)}
        </span>
      </span>
    </div>
  );
}
