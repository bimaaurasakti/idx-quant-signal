import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Activity, CheckCircle2, Filter } from "lucide-react";

export function SignalEngineTab() {
  return (
    <div className="flex flex-col gap-4">
      {/* Intro Box */}
      <Card className="border-border bg-surface-1">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="flex size-7 items-center justify-center rounded-md bg-emerald-500/10 text-emerald-400">
                <Activity className="size-4" />
              </div>
              <CardTitle className="text-[14.5px] font-semibold text-text-primary">
                Engine Sinyal: Multi-Filter Hard Gates &amp; Momentum
              </CardTitle>
            </div>
            <Badge variant="outline" className="border-emerald-500/30 bg-emerald-500/10 text-[11px] text-emerald-400">
              Zero-Guesswork Entry
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="flex flex-col gap-3 text-xs">
          <p className="text-text-secondary leading-relaxed">
            Pada sistem terdahulu, sinyal BUY sering memicu posisi pada saham yang sedang bergerak turun tajam (<em className="text-red-400">catching falling knives</em>) karena hanya mengandalkan MACD cross tanpa syarat tren yang ketat. Engine baru menerapkan <strong className="text-text-primary">3 lapis Hard Gate mutlak</strong> sebelum sinyal BUY diperbolehkan aktif:
          </p>
        </CardContent>
      </Card>

      {/* 3 Hard Gates Grid */}
      <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
        {/* Gate 1: Market Regime */}
        <div className="flex flex-col gap-2.5 rounded-lg border border-blue-500/30 bg-surface-0 p-4">
          <div className="flex items-center justify-between">
            <span className="flex size-6 items-center justify-center rounded-full bg-blue-500/20 text-[11px] font-bold text-blue-400">
              1
            </span>
            <Badge variant="outline" className="border-blue-500/30 text-[10.5px] text-blue-400">
              Macro Circuit Breaker
            </Badge>
          </div>
          <div className="font-semibold text-text-primary">Market Regime Filter (IHSG)</div>
          <div className="rounded border border-border bg-surface-2/60 p-2 font-mono text-[11.5px] text-blue-300">
            IHSG (^JKSE) &gt; SMA200
          </div>
          <p className="text-[11.5px] text-text-secondary leading-relaxed">
            Jika indeks komposit IHSG berada di bawah garis rata-rata 200 hari (bear market makro), sistem secara otomatis mengunci diri dan <strong className="text-text-primary">menolak seluruh pembukaan posisi baru</strong> untuk mencegah kerugian sistematis pasar.
          </p>
        </div>

        {/* Gate 2: Hard Gate Uptrend */}
        <div className="flex flex-col gap-2.5 rounded-lg border border-emerald-500/30 bg-surface-0 p-4">
          <div className="flex items-center justify-between">
            <span className="flex size-6 items-center justify-center rounded-full bg-emerald-500/20 text-[11px] font-bold text-emerald-400">
              2
            </span>
            <Badge variant="outline" className="border-emerald-500/30 text-[10.5px] text-emerald-400">
              Stage 2 Trend Only
            </Badge>
          </div>
          <div className="font-semibold text-text-primary">Hard Gate Stage 2 Uptrend</div>
          <div className="rounded border border-border bg-surface-2/60 p-2 font-mono text-[11.5px] text-emerald-300">
            Close &gt; SMA50 &amp; SMA50 &gt; SMA200
          </div>
          <p className="text-[11.5px] text-text-secondary leading-relaxed">
            Saham WAJIB berada dalam struktur akumulasi Stage 2. Tidak peduli seberapa bullish indikator momentum, sinyal BUY <strong className="text-emerald-400">gugur seketika</strong> jika harga berada di bawah SMA50 atau SMA50 di bawah SMA200.
          </p>
        </div>

        {/* Gate 3: Anti-Overbought & Anti-FOMO */}
        <div className="flex flex-col gap-2.5 rounded-lg border border-purple-500/30 bg-surface-0 p-4">
          <div className="flex items-center justify-between">
            <span className="flex size-6 items-center justify-center rounded-full bg-purple-500/20 text-[11px] font-bold text-purple-400">
              3
            </span>
            <Badge variant="outline" className="border-purple-500/30 text-[10.5px] text-purple-400">
              Entry Price Sanity
            </Badge>
          </div>
          <div className="font-semibold text-text-primary">Anti-Overbought &amp; Anti-FOMO</div>
          <div className="rounded border border-border bg-surface-2/60 p-2 font-mono text-[11.5px] text-purple-300">
            40 &le; RSI14 &le; 65 &amp; Close &le; 1.05 &times; SMA20
          </div>
          <p className="text-[11.5px] text-text-secondary leading-relaxed">
            Menghindari pembelian di pucuk jenuh beli (<code className="text-text-primary">RSI &gt; 65</code>) dan menolak mengejar harga yang sudah melonjak terlalu jauh (&gt; 5%) di atas rata-rata 20 hari.
          </p>
        </div>
      </div>

      {/* Momentum & Multi-Confirmation Scoring */}
      <Card className="border-border bg-surface-1">
        <CardHeader className="pb-2">
          <div className="flex items-center gap-2">
            <div className="flex size-7 items-center justify-center rounded-md bg-amber-500/10 text-amber-400">
              <Filter className="size-4" />
            </div>
            <CardTitle className="text-[14.5px] font-semibold text-text-primary">
              Logika Konfirmasi Momentum &amp; Volume
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent className="flex flex-col gap-3 text-xs">
          <p className="text-text-secondary leading-relaxed">
            Setelah melewati ketiga Hard Gate di atas, sistem mengevaluasi skor sinyal multi-konfirmasi (<code className="text-text-primary">buy_score &ge; 2</code>) dengan trigger eksekusi:
          </p>

          <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
            <div className="flex items-start gap-2.5 rounded-md border border-border bg-surface-0 p-3">
              <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-emerald-400" />
              <div>
                <div className="font-medium text-text-primary">Trigger Momentum Utama</div>
                <div className="text-[11.5px] text-text-secondary mt-0.5">
                  Terjadi <strong className="text-text-primary">MACD Golden Cross</strong> (garis MACD memotong sinyal ke atas) ATAU <strong className="text-text-primary">Stochastic Oversold Cross</strong> (%K memotong %D ke atas saat di bawah 20).
                </div>
              </div>
            </div>

            <div className="flex items-start gap-2.5 rounded-md border border-border bg-surface-0 p-3">
              <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-emerald-400" />
              <div>
                <div className="font-medium text-text-primary">Konfirmasi Volume Partisipasi</div>
                <div className="text-[11.5px] text-text-secondary mt-0.5">
                  Volume transaksi harian tercatat <strong className="text-text-primary">&ge; 20% di atas rata-rata 20 hari</strong> (<code className="text-text-primary">Volume &ge; 1.2 &times; SMA20 Vol</code>) untuk memastikan dorongan likuiditas institusional.
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
