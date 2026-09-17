"use client";

import Link from "next/link";
import { FlaskConical, BarChart3, ArrowRight } from "lucide-react";

import { EmptyState } from "@/components/shared/empty-state";
import { PageHeader } from "@/components/shared/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function BacktestPage() {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Backtest Lab"
        description="Eksplorasi simulasi historis strategi, indikator teknikal, dan replay posisi entry/exit."
      />

      <EmptyState
        icon={FlaskConical}
        title="Backtest Lab Sedang Dimodernisasi"
        description="Modul simulasi interaktif sedang dialihkan agar dapat berjalan langsung di browser memanfaatkan data harga historis Supabase tanpa beban server terpisah."
      />

      <Card className="border-border bg-surface-1">
        <CardContent className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 text-xs">
          <div className="flex items-start gap-3">
            <div className="flex size-8 shrink-0 items-center justify-center rounded-md bg-emerald-500/10 text-emerald-400">
              <BarChart3 className="size-4" />
            </div>
            <div>
              <div className="font-semibold text-text-primary text-[13.5px]">
                Ingin melihat hasil backtest resmi strategi 5 tahun?
              </div>
              <div className="text-text-secondary mt-0.5">
                Simulasi komprehensif pada 44.000+ candle harian konstituen IDX30/LQ45 telah divalidasi dan tersedia lengkap di halaman Metodologi.
              </div>
            </div>
          </div>

          <Button asChild variant="outline" size="sm" className="border-border bg-surface-0 hover:bg-surface-2 shrink-0">
            <Link href="/about" className="flex items-center gap-1.5 text-xs">
              <span>Buka Matriks Benchmark</span>
              <ArrowRight className="size-3 text-brand" />
            </Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
