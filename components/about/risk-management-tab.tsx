import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ShieldCheck, PieChart } from "lucide-react";

export function RiskManagementTab() {
  return (
    <div className="flex flex-col gap-4">
      {/* Intro Header */}
      <Card className="border-border bg-surface-1">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="flex size-7 items-center justify-center rounded-md bg-emerald-500/10 text-emerald-400">
                <ShieldCheck className="size-4" />
              </div>
              <CardTitle className="text-[14.5px] font-semibold text-text-primary">
                Hybrid 2-Tier Exit System &amp; Manajemen Risiko
              </CardTitle>
            </div>
            <Badge variant="outline" className="border-emerald-500/30 bg-emerald-500/10 text-[11px] text-emerald-400">
              Asymmetric Edge
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="flex flex-col gap-3 text-xs">
          <p className="text-text-secondary leading-relaxed">
            Pada sistem lama, aturan Take Profit kaku (+2.0 ATR exit 100%) memotong keuntungan saham yang sedang reli besar, sementara Stop Loss 1.0 ATR terlalu sempit hingga memicu <strong className="text-red-400">61.9% stopout prematur</strong> hanya dalam 1–2 hari. Engine baru memecahkan masalah ini dengan sistem keluar 3 fase:
          </p>
        </CardContent>
      </Card>

      {/* 3-Phase Lifecycle Visual Cards */}
      <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
        {/* Phase 1 */}
        <div className="flex flex-col gap-2.5 rounded-lg border border-border bg-surface-0 p-4">
          <div className="flex items-center justify-between">
            <span className="flex size-6 items-center justify-center rounded-full bg-surface-2 text-[11px] font-bold text-text-primary">
              1
            </span>
            <Badge variant="outline" className="text-[10.5px] text-text-secondary">
              Breathing Room
            </Badge>
          </div>
          <div className="font-semibold text-text-primary">Fase 1: Entry &amp; Stop Loss 1.5 ATR</div>
          <div className="rounded border border-border bg-surface-2/60 p-2 font-mono text-[11.5px] text-text-primary">
            SL Awal = Entry &minus; (1.5 &times; ATR)
          </div>
          <p className="text-[11.5px] text-text-secondary leading-relaxed">
            Posisi dibuka pada harga <strong className="text-text-primary">Open</strong> hari bursa berikutnya. Stop Loss diberi toleransi 1.5 ATR untuk menyerap fluktuasi intra-day wajar tanpa terkena whipsaw prematur.
          </p>
        </div>

        {/* Phase 2 */}
        <div className="flex flex-col gap-2.5 rounded-lg border border-emerald-500/30 bg-emerald-500/5 p-4">
          <div className="flex items-center justify-between">
            <span className="flex size-6 items-center justify-center rounded-full bg-emerald-500/20 text-[11px] font-bold text-emerald-400">
              2
            </span>
            <Badge variant="outline" className="border-emerald-500/30 text-[10.5px] text-emerald-400">
              Risk = 0 (BE)
            </Badge>
          </div>
          <div className="font-semibold text-text-primary">Fase 2: TP1 Lock + Geser SL ke BE</div>
          <div className="rounded border border-emerald-500/30 bg-emerald-500/10 p-2 font-mono text-[11.5px] text-emerald-300">
            TP1 = Entry + (2.0 &times; ATR) &rarr; SL = Entry
          </div>
          <p className="text-[11.5px] text-text-secondary leading-relaxed">
            Saat harga mencapai TP1, sistem mengunci <strong className="text-emerald-400">50% porsi untuk profit pasti</strong>, dan sisa 50% porsi stop loss-nya <strong className="text-emerald-400">digeser ke Break-Even (harga beli)</strong>. Risiko modal seketika menjadi nol.
          </p>
        </div>

        {/* Phase 3 */}
        <div className="flex flex-col gap-2.5 rounded-lg border border-purple-500/30 bg-purple-500/5 p-4">
          <div className="flex items-center justify-between">
            <span className="flex size-6 items-center justify-center rounded-full bg-purple-500/20 text-[11px] font-bold text-purple-400">
              3
            </span>
            <Badge variant="outline" className="border-purple-500/30 text-[10.5px] text-purple-400">
              Big Rally Rider
            </Badge>
          </div>
          <div className="font-semibold text-text-primary">Fase 3: The Runner (Trailing SMA20)</div>
          <div className="rounded border border-purple-500/30 bg-purple-500/10 p-2 font-mono text-[11.5px] text-purple-300">
            Exit Runner = Daily Close &lt; SMA20
          </div>
          <p className="text-[11.5px] text-text-secondary leading-relaxed">
            Sisa 50% porsi posisi (<em className="text-purple-300">Runner</em>) dibiarkan trailing mengikuti rata-rata 20 hari tanpa batas TP kaku, memungkinkan menangkap reli panjang puluhan persen selama tren berlangsung.
          </p>
        </div>
      </div>

      {/* Portfolio Capacity & Sector Gates */}
      <Card className="border-border bg-surface-1">
        <CardHeader className="pb-2">
          <div className="flex items-center gap-2">
            <div className="flex size-7 items-center justify-center rounded-md bg-blue-500/10 text-blue-400">
              <PieChart className="size-4" />
            </div>
            <CardTitle className="text-[14.5px] font-semibold text-text-primary">
              Kapasitas Portofolio &amp; Batasan Konsentrasi Sektor
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-3 md:grid-cols-2 text-xs">
          <div className="flex flex-col gap-2 rounded-lg border border-border bg-surface-0 p-3.5">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-text-primary">Maksimal 7 Posisi Aktif Portofolio</span>
              <Badge variant="outline" className="text-[10px] text-text-secondary">
                Max 7 Slots
              </Badge>
            </div>
            <p className="text-text-secondary text-[11.5px] leading-relaxed">
              Algoritma membatasi total slot aktif maksimal 7 emiten secara bersamaan. Jika seluruh 7 slot terisi, sinyal BUY baru akan di-hold hingga ada posisi aktif yang ditutup, mencegah over-leverage modal.
            </p>
          </div>

          <div className="flex flex-col gap-2 rounded-lg border border-border bg-surface-0 p-3.5">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-text-primary">Maksimal 2 Posisi per Sektor</span>
              <Badge variant="outline" className="text-[10px] text-text-secondary">
                Sector Diversification
              </Badge>
            </div>
            <p className="text-text-secondary text-[11.5px] leading-relaxed">
              Sistem membatasi maksimal 2 saham aktif dalam sektor industri yang sama (misal: maks 2 perbankan atau tambang). Hal ini melindungi portofolio dari penurunan serentak akibat rotasi sektor makro.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
