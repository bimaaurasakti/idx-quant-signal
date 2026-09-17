"use client";

import * as React from "react";
import { Calculator, RotateCcw, AlertTriangle, ShieldCheck } from "lucide-react";

import { PageHeader } from "@/components/shared/page-header";
import { MetricCard } from "@/components/shared/metric-card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { TwoTierVisualizer } from "@/components/risk/two-tier-visualizer";
import { formatIdr, formatNumberId } from "@/lib/format";

/**
 * Formula perhitungan position sizing berdasarkan toleransi risiko modal.
 * Mendukung simulasi Hybrid 2-Tier Exit (SL 1.5 ATR & TP1 2.0 ATR).
 */
function calcRisk(
  capital: number,
  riskPct: number,
  entryPrice: number,
  atr: number,
  slMult: number,
  tpMult: number,
) {
  const riskRupiah = capital * (riskPct / 100);
  const slPrice = Math.max(entryPrice - slMult * atr, 0);
  const tpPrice = entryPrice + tpMult * atr;
  const riskPerShare = entryPrice - slPrice;
  let shares = riskPerShare > 0 ? Math.floor(riskRupiah / riskPerShare) : 0;
  shares = Math.floor(shares / 100) * 100; // dibulatkan ke lot (100 lembar)
  const positionValue = shares * entryPrice;
  const rr = riskPerShare > 0 ? (tpPrice - entryPrice) / riskPerShare : 0;
  return { riskRupiah, slPrice, tpPrice, shares, positionValue, rr, overCapital: positionValue > capital };
}

export default function RiskPage() {
  const [capital, setCapital] = React.useState(50_000_000);
  const [riskPct, setRiskPct] = React.useState(1.0);
  const [entryPrice, setEntryPrice] = React.useState(5000);
  const [atrValue, setAtrValue] = React.useState(100);
  const [slMult, setSlMult] = React.useState(1.5); // Default strategi baru 1.5 ATR
  const [tpMult, setTpMult] = React.useState(2.0); // Default strategi baru 2.0 ATR

  const result = calcRisk(capital, riskPct, entryPrice, atrValue, slMult, tpMult);

  function resetToStrategyDefaults() {
    setSlMult(1.5);
    setTpMult(2.0);
    setRiskPct(1.0);
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Kalkulator Position Sizing & Risk Management"
        description="Sinyal bagus tidak berguna tanpa position sizing yang disiplin. Tentukan alokasi lot dan manajemen risiko 2-tier sebelum entry."
        action={
          <Button
            variant="outline"
            size="sm"
            onClick={resetToStrategyDefaults}
            className="flex items-center gap-1.5 border-border bg-surface-1 text-xs text-text-secondary hover:text-text-primary"
          >
            <RotateCcw className="size-3.5 text-brand" />
            <span>Preset Strategi Baru (SL 1.5 / TP1 2.0)</span>
          </Button>
        }
      />

      {/* Input Form Grid */}
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="flex flex-col gap-4 rounded-lg border border-border bg-surface-1 p-4 text-xs">
          <div className="font-semibold text-[13.5px] text-text-primary flex items-center gap-2">
            <Calculator className="size-4 text-emerald-400" />
            <span>Parameter Modal &amp; Harga</span>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="capital">Modal total portofolio (Rp)</Label>
            <Input
              id="capital"
              type="number"
              value={capital}
              onChange={(e) => setCapital(Number(e.target.value) || 0)}
              min={1_000_000}
              step={1_000_000}
            />
          </div>

          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <Label>Risiko per trade (% dari modal)</Label>
              <span className="font-mono text-[13px] text-text-primary">{riskPct.toFixed(1)}%</span>
            </div>
            <Slider value={[riskPct]} onValueChange={([v]) => setRiskPct(v)} min={0.5} max={5} step={0.5} />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="entry">Harga entry pembelian (Rp)</Label>
            <Input
              id="entry"
              type="number"
              value={entryPrice}
              onChange={(e) => setEntryPrice(Number(e.target.value) || 0)}
              min={1}
              step={50}
            />
          </div>
        </div>

        <div className="flex flex-col gap-4 rounded-lg border border-border bg-surface-1 p-4 text-xs">
          <div className="font-semibold text-[13.5px] text-text-primary flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldCheck className="size-4 text-blue-400" />
              <span>Parameter Volatilitas ATR &amp; Kelipatan</span>
            </div>
            <Badge variant="outline" className="text-[10px] text-text-secondary">
              Vol-Based Sizing
            </Badge>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="atr">ATR(14) saham ini (Rp)</Label>
            <Input
              id="atr"
              type="number"
              value={atrValue}
              onChange={(e) => setAtrValue(Number(e.target.value) || 0)}
              min={1}
              step={10}
            />
          </div>

          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <Label>Stop loss awal = X &times; ATR</Label>
              <span className="font-mono text-[13px] text-text-primary">
                {slMult.toFixed(1)}&times; ({formatIdr(slMult * atrValue)})
              </span>
            </div>
            <Slider value={[slMult]} onValueChange={([v]) => setSlMult(v)} min={0.5} max={3} step={0.1} />
          </div>

          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <Label>Take profit 1 (TP1) = X &times; ATR</Label>
              <span className="font-mono text-[13px] text-text-primary">
                {tpMult.toFixed(1)}&times; ({formatIdr(tpMult * atrValue)})
              </span>
            </div>
            <Slider value={[tpMult]} onValueChange={([v]) => setTpMult(v)} min={1} max={5} step={0.5} />
          </div>
        </div>
      </div>

      {/* Over-Capital Warning */}
      {result.overCapital && (
        <div className="flex items-center gap-2.5 rounded-lg border border-red-500/30 bg-red-500/10 p-3.5 text-xs text-red-300">
          <AlertTriangle className="size-4 shrink-0 text-red-400" />
          <span>
            <strong>Peringatan Alokasi:</strong> Nilai posisi melebihi modal Anda! Stop loss terlalu ketat relatif terhadap ATR, atau risk % terlalu besar untuk modal saat ini. Perbesar jarak SL atau kurangi persentase risiko.
          </span>
        </div>
      )}

      {/* Two-Tier Visualizer Component */}
      <TwoTierVisualizer
        shares={result.shares}
        entryPrice={entryPrice}
        atr={atrValue}
        slMult={slMult}
        tpMult={tpMult}
        capital={capital}
        riskRupiah={result.riskRupiah}
      />

      {/* Metric Cards Summary */}
      <div>
        <h2 className="mb-3 text-[1.125rem] font-semibold text-text-primary">
          Ringkasan Metrik Posisi
        </h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          <MetricCard
            label="Total Saham (Lot)"
            value={result.shares / 100}
            format={(v) => `${formatNumberId(v)} lot`}
            tone="neutral"
          />
          <MetricCard
            label="Total Nilai Posisi"
            value={result.positionValue}
            format={(v) => formatIdr(v)}
            tone="neutral"
          />
          <MetricCard
            label="Risk : Reward ke TP1"
            value={result.rr}
            format={(v) => `1 : ${v.toFixed(2)}`}
            tone={result.rr >= 1.3 ? "bullish" : "bearish"}
          />
          <MetricCard label="Stop Loss Awal" value={result.slPrice} format={(v) => formatIdr(v)} tone="bearish" />
          <MetricCard label="Target TP1 (+50%)" value={result.tpPrice} format={(v) => formatIdr(v)} tone="bullish" />
          <MetricCard
            label="Maksimum Risiko (Rp)"
            value={result.riskRupiah}
            format={(v) => formatIdr(v)}
            tone="neutral"
          />
        </div>
      </div>
    </div>
  );
}
