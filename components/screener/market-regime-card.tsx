import { ShieldCheck, ShieldAlert, Gauge, AlertCircle, Zap } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { MarketRegimeInfo } from "@/lib/types";

interface MarketRegimeCardProps {
  regime: MarketRegimeInfo;
  activeCount: number;
}

export function MarketRegimeCard({ regime, activeCount }: MarketRegimeCardProps) {
  const isHighAlpha = regime.tier === "HIGH_ALPHA";
  const isTactical = regime.tier === "TACTICAL_SWING";
  const isDefensive = regime.tier === "DEFENSIVE";

  const tierBadgeStyle = isHighAlpha
    ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-400"
    : isTactical
    ? "border-amber-500/40 bg-amber-500/10 text-amber-400"
    : "border-rose-500/40 bg-rose-500/10 text-rose-400";

  const tierLabel = isHighAlpha
    ? "High Alpha (Bull Market)"
    : isTactical
    ? "Tactical Swing (Rebound)"
    : "Defensive (Risk-Off)";

  const sizingBadgeStyle = isHighAlpha
    ? "border-emerald-500/30 bg-emerald-500/15 text-emerald-300"
    : isTactical
    ? "border-amber-500/30 bg-amber-500/15 text-amber-300"
    : "border-rose-500/30 bg-rose-500/15 text-rose-300";

  const maxSlots = regime.max_positions || 7;
  const slotsFull = activeCount >= maxSlots;

  return (
    <div
      className={`relative overflow-hidden rounded-xl border p-4 transition-all ${
        isHighAlpha
          ? "border-emerald-500/25 bg-emerald-950/15"
          : isTactical
          ? "border-amber-500/25 bg-amber-950/15"
          : "border-rose-500/25 bg-rose-950/15"
      }`}
    >
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        {/* Left: Regime Description & Badges */}
        <div className="flex flex-col gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">
              Market Regime IHSG:
            </span>
            <Badge variant="outline" className={`text-xs font-semibold ${tierBadgeStyle}`}>
              {isHighAlpha ? (
                <ShieldCheck className="mr-1 size-3.5" />
              ) : isTactical ? (
                <Zap className="mr-1 size-3.5" />
              ) : (
                <ShieldAlert className="mr-1 size-3.5" />
              )}
              {tierLabel}
            </Badge>

            <Badge variant="outline" className={`text-xs font-mono font-medium ${sizingBadgeStyle}`}>
              <Gauge className="mr-1 size-3" />
              Sizing: {regime.sizing_pct}% Lot
            </Badge>

            <Badge
              variant="outline"
              className={`text-xs font-mono font-medium ${
                slotsFull
                  ? "border-rose-500/40 bg-rose-500/15 text-rose-300"
                  : "border-border bg-surface-1 text-text-secondary"
              }`}
            >
              Kapasitas: {activeCount} / {maxSlots} Posisi
            </Badge>
          </div>

          <p className="text-[12.5px] leading-relaxed text-text-secondary">
            {regime.description}
          </p>
        </div>

        {/* Right: Dual-Horizon Status Pill */}
        <div className="flex shrink-0 items-center gap-3 border-t border-border/40 pt-2 md:border-t-0 md:pt-0">
          <div className="flex items-center gap-1.5 rounded-lg border border-border/60 bg-surface-1/80 px-3 py-1.5 text-[11.5px]">
            <span className="text-text-muted">Macro:</span>
            <span
              className={`font-semibold ${
                regime.macro_bull ? "text-emerald-400" : "text-amber-400"
              }`}
            >
              {regime.macro_bull ? "IHSG > SMA200" : "IHSG < SMA200"}
            </span>
            <span className="text-text-muted/60">|</span>
            <span className="text-text-muted">Momentum:</span>
            <span
              className={`font-semibold ${
                regime.momentum_green ? "text-emerald-400" : "text-rose-400"
              }`}
            >
              {regime.momentum_green ? "Hijau (Rebound)" : "Merah (Dump)"}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
