import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatIdr, formatNumberId, formatPctId } from "@/lib/format";
import { ShieldCheck, Lock, Sparkles } from "lucide-react";

interface TwoTierVisualizerProps {
  shares: number;
  entryPrice: number;
  atr: number;
  slMult: number;
  tpMult: number;
  capital: number;
  riskRupiah?: number;
}

export function TwoTierVisualizer({
  shares,
  entryPrice,
  atr,
  slMult,
  tpMult,
  capital,
}: TwoTierVisualizerProps) {
  const halfShares = Math.floor(shares / 200) * 100;
  const runnerShares = shares - halfShares;

  const slPrice = entryPrice - slMult * atr;
  const tp1Price = entryPrice + tpMult * atr;

  const totalPositionValue = shares * entryPrice;
  const tp1GainPerShare = tp1Price - entryPrice;
  const tp1ProfitRupiah = halfShares * tp1GainPerShare;
  const maxInitialLossRupiah = shares * (entryPrice - slPrice);

  const tp1GainPct = entryPrice > 0 ? (tp1GainPerShare / entryPrice) * 100 : 0;
  const slLossPct = entryPrice > 0 ? ((entryPrice - slPrice) / entryPrice) * 100 : 0;
  const rrRatio = slLossPct > 0 ? tp1GainPct / slLossPct : 0;

  return (
    <Card className="border-border bg-surface-1">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex size-7 items-center justify-center rounded-md bg-emerald-500/10 text-emerald-400">
              <ShieldCheck className="size-4" />
            </div>
            <CardTitle className="text-[14.5px] font-semibold text-text-primary">
              Simulasi Eksekusi Hybrid 2-Tier
            </CardTitle>
          </div>
          <Badge variant="outline" className="border-emerald-500/30 bg-emerald-500/10 text-[10.5px] text-emerald-400">
            Strategy Default (1.5 SL / 2.0 TP1)
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="flex flex-col gap-4 text-xs">
        {/* Tier Cards Grid */}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {/* Tier 1 Box */}
          <div className="flex flex-col gap-2 rounded-lg border border-emerald-500/30 bg-surface-0 p-3.5">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-text-primary">Tier 1: TP1 Lock (50% Lot)</span>
              <Badge variant="outline" className="border-emerald-500/30 text-[10px] text-emerald-400">
                <Lock className="size-3" /> Profit Pasti
              </Badge>
            </div>
            <div className="font-mono text-[18px] font-bold text-emerald-400">
              {formatIdr(tp1Price)}
              <span className="ml-1.5 text-xs font-normal text-text-secondary">
                ({formatPctId(tp1GainPct)})
              </span>
            </div>
            <div className="space-y-1 text-[11.5px] text-text-secondary">
              <div className="flex justify-between">
                <span>Porsi Lot:</span>
                <span className="font-mono text-text-primary">
                  {halfShares / 100} Lot ({halfShares.toLocaleString()} lembar)
                </span>
              </div>
              <div className="flex justify-between">
                <span>Estimasi Profit:</span>
                <span className="font-mono font-semibold text-emerald-400">
                  +{formatIdr(tp1ProfitRupiah)}
                </span>
              </div>
            </div>
            <div className="mt-1 rounded bg-emerald-500/10 p-2 text-[10.5px] text-emerald-300">
              Kunci 50% modal begitu target +{tpMult} ATR tercapai. SL sisa posisi otomatis geser ke BE.
            </div>
          </div>

          {/* Tier 2 Box */}
          <div className="flex flex-col gap-2 rounded-lg border border-purple-500/30 bg-surface-0 p-3.5">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-text-primary">Tier 2: The Runner (50% Lot)</span>
              <Badge variant="outline" className="border-purple-500/30 text-[10px] text-purple-400">
                <Sparkles className="size-3" /> Risiko Rp 0
              </Badge>
            </div>
            <div className="font-mono text-[18px] font-bold text-purple-300">
              Trailing SMA20
              <span className="ml-1.5 text-xs font-normal text-text-secondary">
                (Uncapped Upside)
              </span>
            </div>
            <div className="space-y-1 text-[11.5px] text-text-secondary">
              <div className="flex justify-between">
                <span>Porsi Lot:</span>
                <span className="font-mono text-text-primary">
                  {runnerShares / 100} Lot ({runnerShares.toLocaleString()} lembar)
                </span>
              </div>
              <div className="flex justify-between">
                <span>Stop Loss Efektif:</span>
                <span className="font-mono font-semibold text-text-primary">
                  {formatIdr(entryPrice)} (Break-Even)
                </span>
              </div>
            </div>
            <div className="mt-1 rounded bg-purple-500/10 p-2 text-[10.5px] text-purple-300">
              Posisi runner berjalan tanpa beban risiko modal. Exit hanya saat daily Close menembus bawah SMA20.
            </div>
          </div>
        </div>

        {/* Risk / Reward Metrics Row */}
        <div className="grid grid-cols-3 gap-2 rounded-lg border border-border bg-surface-0 p-3 text-center">
          <div>
            <div className="text-[11px] text-text-secondary">Maksimum Risiko Awal</div>
            <div className="font-mono text-[13.5px] font-semibold text-red-400">
              &minus;{formatIdr(maxInitialLossRupiah)}
            </div>
          </div>
          <div className="border-x border-border">
            <div className="text-[11px] text-text-secondary">Profit Kunci di TP1</div>
            <div className="font-mono text-[13.5px] font-semibold text-emerald-400">
              +{formatIdr(tp1ProfitRupiah)}
            </div>
          </div>
          <div>
            <div className="text-[11px] text-text-secondary">Risk : Reward ke TP1</div>
            <div className="font-mono text-[13.5px] font-semibold text-text-primary">
              1 : {formatNumberId(rrRatio, 2)}
            </div>
          </div>
        </div>

        {/* Visual Progress Bar: Capital Allocation */}
        <div className="flex flex-col gap-1.5">
          <div className="flex justify-between text-[11px] text-text-secondary">
            <span>Alokasi Modal Posisi terhadap Portofolio:</span>
            <span className="font-mono text-text-primary">
              {capital > 0 ? ((totalPositionValue / capital) * 100).toFixed(1) : 0}% dari modal
            </span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-surface-2">
            <div
              className="h-full rounded-full bg-brand transition-all duration-300"
              style={{
                width: `${Math.min(capital > 0 ? (totalPositionValue / capital) * 100 : 0, 100)}%`,
              }}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
