import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BarChart3, TrendingUp, ShieldCheck, Zap } from "lucide-react";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";

interface BenchmarkMetric {
  label: string;
  baseline: string;
  revamped: string;
  impact: string;
  impactType: "positive" | "neutral";
  detail: string;
}

const BENCHMARK_METRICS: BenchmarkMetric[] = [
  {
    label: "Cumulative Net Return",
    baseline: "-334.02%",
    revamped: "+47.00%",
    impact: "+381.02%",
    impactType: "positive",
    detail: "Pembalikan dari defisit kumulatif menjadi keuntungan bersih konsisten.",
  },
  {
    label: "Win Rate",
    baseline: "29.86%",
    revamped: "40.00%",
    impact: "+10.14%",
    impactType: "positive",
    detail: "Proporsi posisi yang ditutup dalam kondisi profit.",
  },
  {
    label: "Profit Factor",
    baseline: "0.87 (Rugi)",
    revamped: "1.07 (Untung)",
    impact: "+0.20",
    impactType: "positive",
    detail: "Rasio total keuntungan terhadap total kerugian (> 1.0 = positive edge).",
  },
  {
    label: "Premature Noise SL (<2 Hari)",
    baseline: "61.9% (431 trade)",
    revamped: "40.1% (61 trade)",
    impact: "-85.8% Whipsaw",
    impactType: "positive",
    detail: "Pemangkasan drastis trade yang mati dini akibat fluktuasi harian acak.",
  },
  {
    label: "Expectancy per Trade",
    baseline: "-0.32% / trade",
    revamped: "+0.17% / trade",
    impact: "+0.49%",
    impactType: "positive",
    detail: "Ekspektansi matematis nilai harapan keuntungan per entry.",
  },
  {
    label: "Rata-rata Durasi Hold",
    baseline: "4.0 hari",
    revamped: "10.5 hari",
    impact: "+6.5 hari",
    impactType: "neutral",
    detail: "Transisi dari churn & burn acak menjadi trend-following yang stabil.",
  },
  {
    label: "TP1 Locked & Risk-Free Runners",
    baseline: "0 posisi",
    revamped: "108 posisi",
    impact: "+108 runner",
    impactType: "positive",
    detail: "Posisi yang berhasil mengunci 50% profit dan risiko sisa menjadi 0.",
  },
];

export function BenchmarkMatrixCard() {
  return (
    <Card className="border-border bg-surface-1">
      <CardHeader className="pb-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <div className="flex size-8 items-center justify-center rounded-md bg-emerald-500/10 text-emerald-400">
              <BarChart3 className="size-4" />
            </div>
            <div>
              <CardTitle className="text-[15px] font-semibold text-text-primary">
                Bukti Empiris: Validasi Benchmark Historis 5 Tahun
              </CardTitle>
              <CardDescription className="text-xs text-text-secondary">
                Simulasi kuantitatif pada 44.000+ bar candle harian riil konstituen IDX30 &amp; LQ45
              </CardDescription>
            </div>
          </div>
          <Badge variant="outline" className="border-emerald-500/30 bg-emerald-500/10 text-[11px] text-emerald-400">
            <ShieldCheck className="size-3" /> Validated on 44k+ Bars
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="flex flex-col gap-4 text-xs">
        {/* Responsive Table / Grid */}
        <div className="overflow-x-auto rounded-md border border-border bg-surface-0">
          <Table className="text-xs">
            <TableHeader>
              <TableRow className="border-border bg-surface-2/60 text-[11.5px] font-medium text-text-secondary hover:bg-surface-2/60">
                <TableHead className="py-2.5 px-3">Metrik Kuantitatif</TableHead>
                <TableHead className="py-2.5 px-3">Sistem Lama (Defisit)</TableHead>
                <TableHead className="py-2.5 px-3">Engine Baru (Revamped)</TableHead>
                <TableHead className="py-2.5 px-3 text-right">Dampak Kuantitatif</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody className="font-mono text-[12px]">
              {BENCHMARK_METRICS.map((m, idx) => (
                <TableRow key={idx} className="border-border hover:bg-surface-2/40 transition-colors">
                  <TableCell className="py-2.5 px-3 font-sans text-text-primary">
                    <div className="font-medium">{m.label}</div>
                    <div className="text-[10.5px] text-text-secondary">{m.detail}</div>
                  </TableCell>
                  <TableCell className="py-2.5 px-3 text-red-400/90 line-through decoration-red-400/50">
                    {m.baseline}
                  </TableCell>
                  <TableCell className="py-2.5 px-3 font-semibold text-emerald-400">
                    {m.revamped}
                  </TableCell>
                  <TableCell className="py-2.5 px-3 text-right">
                    <span
                      className={`inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[11px] font-semibold ${
                        m.impactType === "positive"
                          ? "bg-emerald-500/15 text-emerald-400"
                          : "bg-surface-2 text-text-secondary"
                      }`}
                    >
                      {m.impactType === "positive" && <TrendingUp className="size-3" />}
                      {m.impact}
                    </span>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {/* Insight Callout */}
        <div className="flex items-start gap-2.5 rounded-md border border-emerald-500/20 bg-emerald-500/5 p-3 text-text-secondary">
          <Zap className="mt-0.5 size-4 shrink-0 text-emerald-400" />
          <div className="text-[11.5px] leading-relaxed">
            <strong className="text-text-primary">Kesimpulan Algoritmik:</strong> Pembalikan dari performa defisit ke profit positif dicapai bukan dengan meramal masa depan, melainkan dengan memangkas <strong className="text-emerald-400">73% sinyal acak</strong> (menolak saham downtrend), memperlebar SL ke <strong className="text-emerald-400">1.5 ATR</strong> agar terhindar dari whipsaw harian, serta menerapkan <strong className="text-emerald-400">Hybrid 2-Tier Exit</strong> yang membiarkan sisa posisi menangkap reli besar.
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
