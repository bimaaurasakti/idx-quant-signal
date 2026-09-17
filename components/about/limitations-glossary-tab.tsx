import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BenchmarkMatrixCard } from "@/components/about/benchmark-matrix-card";
import { BookOpen, AlertTriangle } from "lucide-react";

export function LimitationsGlossaryTab() {
  return (
    <div className="flex flex-col gap-4">
      {/* 5-Year Benchmark Empirical Matrix */}
      <BenchmarkMatrixCard />

      {/* Quantitative Glossary */}
      <Card className="border-border bg-surface-1">
        <CardHeader className="pb-2">
          <div className="flex items-center gap-2">
            <div className="flex size-7 items-center justify-center rounded-md bg-blue-500/10 text-blue-400">
              <BookOpen className="size-4" />
            </div>
            <CardTitle className="text-[14.5px] font-semibold text-text-primary">
              Kamus Istilah Kuantitatif
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 text-xs">
          <div className="flex flex-col gap-1 rounded-md border border-border bg-surface-0 p-3">
            <span className="font-semibold text-text-primary">Win Rate (%)</span>
            <p className="text-[11.5px] text-text-secondary leading-relaxed">
              Persentase posisi yang ditutup dengan return positif dari seluruh posisi yang pernah dibuka.
            </p>
          </div>

          <div className="flex flex-col gap-1 rounded-md border border-border bg-surface-0 p-3">
            <span className="font-semibold text-text-primary">Profit Factor</span>
            <p className="text-[11.5px] text-text-secondary leading-relaxed">
              Total keuntungan kotor dibagi total kerugian kotor. Nilai &gt; 1.0 menandakan sistem memiliki keunggulan matematis (<em className="text-emerald-400">positive edge</em>).
            </p>
          </div>

          <div className="flex flex-col gap-1 rounded-md border border-border bg-surface-0 p-3">
            <span className="font-semibold text-text-primary">Expectancy per Trade</span>
            <p className="text-[11.5px] text-text-secondary leading-relaxed">
              Nilai harapan matematis keuntungan rata-rata per entri: <code>(Winrate &times; Avg Win) &minus; (Lossrate &times; Avg Loss)</code>.
            </p>
          </div>

          <div className="flex flex-col gap-1 rounded-md border border-border bg-surface-0 p-3">
            <span className="font-semibold text-text-primary">ATR (Average True Range 14)</span>
            <p className="text-[11.5px] text-text-secondary leading-relaxed">
              Indikator rentang volatilitas riil rata-rata harian suatu saham selama 14 hari terakhir. Digunakan untuk menentukan jarak Stop Loss dan Take Profit yang proporsional.
            </p>
          </div>

          <div className="flex flex-col gap-1 rounded-md border border-border bg-surface-0 p-3">
            <span className="font-semibold text-text-primary">Break-Even (BE) Runner</span>
            <p className="text-[11.5px] text-text-secondary leading-relaxed">
              Sisa 50% porsi posisi yang level Stop Loss-nya telah digeser ke harga beli awal (<code className="text-emerald-400">Entry Price</code>) setelah target TP1 tercapai. Risiko modal sisa menjadi 0.
            </p>
          </div>

          <div className="flex flex-col gap-1 rounded-md border border-border bg-surface-0 p-3">
            <span className="font-semibold text-text-primary">Trailing SMA20</span>
            <p className="text-[11.5px] text-text-secondary leading-relaxed">
              Garis keluar dinamis untuk posisi runner. Posisi ditutup jika harga penutupan harian resmi berada di bawah rata-rata 20 hari (<code className="text-text-primary">Close &lt; SMA20</code>).
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Honest Limitations & Disclaimers */}
      <Card className="border-border bg-surface-1">
        <CardHeader className="pb-2">
          <div className="flex items-center gap-2">
            <div className="flex size-7 items-center justify-center rounded-md bg-amber-500/10 text-amber-400">
              <AlertTriangle className="size-4" />
            </div>
            <CardTitle className="text-[14.5px] font-semibold text-text-primary">
              Batasan Jujur &amp; Keterbatasan Realistis
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent className="flex flex-col gap-2.5 text-xs">
          <div className="flex items-start gap-2.5 rounded-md border border-border bg-surface-0 p-3">
            <div className="font-semibold text-amber-400 shrink-0">1. Data End-of-Day:</div>
            <div className="text-text-secondary text-[11.5px] leading-relaxed">
              Data bersumber dari Yahoo Finance yang berbasis penutupan harian resmi (<em className="text-text-primary">EOD delayed</em>), bukan data order book tick-by-tick level 2 real-time.
            </div>
          </div>

          <div className="flex items-start gap-2.5 rounded-md border border-border bg-surface-0 p-3">
            <div className="font-semibold text-amber-400 shrink-0">2. Friksi Biaya Riil:</div>
            <div className="text-text-secondary text-[11.5px] leading-relaxed">
              Simulasi backtest belum memperhitungkan komisi broker (rata-rata 0.15% beli, 0.25% jual), pajak penjualan bursa, serta kemungkinan slippage pada volatilitas tinggi.
            </div>
          </div>

          <div className="flex items-start gap-2.5 rounded-md border border-border bg-surface-0 p-3">
            <div className="font-semibold text-amber-400 shrink-0">3. Bukan Magic Box:</div>
            <div className="text-text-secondary text-[11.5px] leading-relaxed">
              Dashboard ini dirancang sebagai instrumen bantu pengambilan keputusan yang disiplin dan objektif untuk trading personal, bukan pengelolaan dana miliaran dolar atau janji keuntungan tanpa risiko.
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
