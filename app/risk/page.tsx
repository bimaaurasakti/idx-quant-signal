"use client";

import * as React from "react";

import { PageHeader } from "@/components/shared/page-header";
import { MetricCard } from "@/components/shared/metric-card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { formatIdr, formatNumberId } from "@/lib/format";

/**
 * Formula IDENTIK views/risk.py (§5.7 implementation plan) -- port 1:1,
 * murni client-side, TANPA backend. Recompute real-time tiap input berubah,
 * sama seperti versi Streamlit reactive.
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
  const slPrice = entryPrice - slMult * atr;
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
  const [slMult, setSlMult] = React.useState(1.0);
  const [tpMult, setTpMult] = React.useState(2.0);

  const result = calcRisk(capital, riskPct, entryPrice, atrValue, slMult, tpMult);

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="🧮 Kalkulator Position Sizing & Risk Management"
        description="Sinyal bagus tidak ada gunanya tanpa position sizing yang benar. Hedge fund sungguhan selalu menentukan ukuran posisi berdasarkan risiko, bukan 'feeling'."
      />

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="flex flex-col gap-5 rounded-lg border border-border bg-surface-1 p-4">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="capital">Modal total (Rp)</Label>
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
            <Label htmlFor="entry">Harga entry (Rp)</Label>
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

        <div className="flex flex-col gap-5 rounded-lg border border-border bg-surface-1 p-4">
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
              <Label>Stop loss = X × ATR</Label>
              <span className="font-mono text-[13px] text-text-primary">{slMult.toFixed(1)}×</span>
            </div>
            <Slider value={[slMult]} onValueChange={([v]) => setSlMult(v)} min={0.5} max={3} step={0.5} />
          </div>
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <Label>Take profit = X × ATR</Label>
              <span className="font-mono text-[13px] text-text-primary">{tpMult.toFixed(1)}×</span>
            </div>
            <Slider value={[tpMult]} onValueChange={([v]) => setTpMult(v)} min={1} max={5} step={0.5} />
          </div>
        </div>
      </div>

      <div>
        <h2 className="mb-3 text-[1.125rem] font-semibold text-text-primary">Hasil Perhitungan</h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          <MetricCard
            label="Jumlah Saham (lot)"
            value={result.shares}
            format={(v) => formatNumberId(v)}
            tone="neutral"
          />
          <MetricCard
            label="Nilai Posisi"
            value={result.positionValue}
            format={(v) => formatIdr(v)}
            tone="neutral"
          />
          <MetricCard
            label="Risk : Reward Ratio"
            value={result.rr}
            format={(v) => `1 : ${v.toFixed(2)}`}
            tone={result.rr >= 1.5 ? "bullish" : "bearish"}
          />
          <MetricCard label="Stop Loss" value={result.slPrice} format={(v) => formatIdr(v)} tone="bearish" />
          <MetricCard label="Take Profit" value={result.tpPrice} format={(v) => formatIdr(v)} tone="bullish" />
          <MetricCard
            label="Max Risiko (Rp)"
            value={result.riskRupiah}
            format={(v) => formatIdr(v)}
            tone="neutral"
          />
        </div>
      </div>

      {result.overCapital && (
        <div
          className="rounded-lg border-l-4 px-4 py-3 text-[13.5px] text-text-primary"
          style={{ borderLeftColor: "var(--bearish)", backgroundColor: "var(--bearish-bg)" }}
        >
          ⚠️ Nilai posisi melebihi modal Anda! Stop loss terlalu ketat relatif ke ATR, atau risk % per
          trade terlalu besar untuk modal ini. Perbesar jarak SL atau kurangi risk %.
        </div>
      )}
    </div>
  );
}
