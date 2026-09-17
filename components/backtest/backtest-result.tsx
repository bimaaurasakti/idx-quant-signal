"use client";

import { MetricCard } from "@/components/shared/metric-card";
import { ConvictionMeter } from "@/components/shared/conviction-meter";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { BacktestChart } from "@/components/backtest/backtest-chart";
import { ReplayScrubber } from "@/components/backtest/replay-scrubber";
import { EquityCurveChart } from "@/components/backtest/equity-curve-chart";
import { exitReasonColor, exitReasonLabel } from "@/lib/constants";
import { formatIdr, formatNumberId, formatPctId } from "@/lib/format";
import type { BacktestRunResponse } from "@/lib/types";

interface BacktestResultProps {
  result: BacktestRunResponse;
  playbackDate: string | null;
  onPlaybackDateChange: (d: string | null) => void;
}

export function BacktestResult({ result, playbackDate, onPlaybackDateChange }: BacktestResultProps) {
  const { metrics, trades } = result;

  if (metrics.n_trades === 0) {
    return (
      <div className="rounded-lg border border-dashed border-border px-6 py-10 text-center text-[13.5px] text-text-secondary">
        Tidak ada trade yang terbentuk dengan kombinasi indikator &amp; threshold ini pada periode yang
        dipilih. Coba turunkan Minimal Konfirmasi, tambah indikator, atau perpanjang periode.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-5 border-t border-border pt-6">
      <h2 className="text-[1.25rem] font-semibold text-text-primary">📊 Hasil Backtest — {result.ticker}</h2>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <MetricCard label="Jml Trade" value={metrics.n_trades} format={(v) => formatNumberId(v)} tone="neutral" />
        <MetricCard
          label="Winrate"
          value={metrics.winrate}
          format={(v) => `${formatNumberId(v, 1)}%`}
          tone={(metrics.winrate ?? 0) > 50 ? "bullish" : "neutral"}
        />
        <MetricCard
          label="Expectancy"
          value={metrics.expectancy_pct}
          format={(v) => formatPctId(v)}
          tone={(metrics.expectancy_pct ?? 0) > 0 ? "bullish" : "bearish"}
        />
        <MetricCard
          label="Profit Factor"
          value={metrics.profit_factor}
          format={(v) => formatNumberId(v, 2)}
          tone={metrics.profit_factor == null || metrics.profit_factor > 1 ? "bullish" : "bearish"}
        />
        <MetricCard label="Max Drawdown" value={metrics.max_drawdown_pct} format={(v) => formatPctId(v)} tone="bearish" />
        <MetricCard label="Sharpe (kasar)" value={metrics.sharpe_rough} format={(v) => formatNumberId(v, 2)} tone="neutral" />
      </div>

      {result.last_trade_confirmation && (
        <div className="flex items-center gap-2 text-[12.5px] text-text-secondary">
          <span>Konfirmasi trade BUY terakhir:</span>
          <ConvictionMeter
            filled={result.last_trade_confirmation.filled}
            total={result.last_trade_confirmation.total}
            direction="bullish"
            size="sm"
          />
          <span className="font-mono text-text-primary">
            {result.last_trade_confirmation.filled}/{result.last_trade_confirmation.total} indikator sepakat
          </span>
        </div>
      )}

      <div
        className="rounded-lg border-l-4 px-4 py-3 text-[13px] text-text-primary"
        style={{ borderLeftColor: "var(--signal-hold)", backgroundColor: "var(--signal-hold-bg)" }}
      >
        ⚠️ <strong>Backtest ini bersifat in-sample</strong> (diuji pada data historis yang sama dipakai
        untuk memilih indikator) — bukan validasi out-of-sample. Performa masa lalu tidak menjamin hasil
        masa depan. Makin banyak indikator dikombinasikan, makin besar risiko overfitting/curve-fitting.{" "}
        <strong>Bukan nasihat keuangan.</strong>
      </div>

      <Tabs defaultValue="chart">
        <TabsList>
          <TabsTrigger value="chart">📈 Chart</TabsTrigger>
          <TabsTrigger value="trades">📋 Riwayat Trade</TabsTrigger>
          <TabsTrigger value="equity">💰 Equity Curve</TabsTrigger>
        </TabsList>

        <TabsContent value="chart" className="flex flex-col gap-3">
          <BacktestChart
            bars={result.bars}
            indicatorSeries={result.indicator_series}
            trades={result.trades}
            playbackDate={playbackDate}
          />
          <ReplayScrubber dates={result.bars.map((b) => b.date)} onDateChange={onPlaybackDateChange} />
        </TabsContent>

        <TabsContent value="trades">
          <div className="overflow-hidden rounded-lg border border-border bg-surface-1">
            <Table className="text-xs">
              <TableHeader className="bg-surface-1">
                <TableRow className="hover:bg-transparent">
                  <TableHead>Entry</TableHead>
                  <TableHead>Exit</TableHead>
                  <TableHead className="text-right">Harga Entry</TableHead>
                  <TableHead className="text-right">Harga Exit</TableHead>
                  <TableHead className="text-right">Return</TableHead>
                  <TableHead>Alasan</TableHead>
                  <TableHead className="text-right">Hold</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {trades.map((t, i) => {
                  const color = exitReasonColor(t.reason);
                  const positive = t.return_pct >= 0;
                  return (
                    <TableRow
                      key={`${t.entry_date}-${i}`}
                      className="border-border-subtle transition-colors"
                    >
                      <TableCell className="font-mono text-xs text-text-primary">{t.entry_date}</TableCell>
                      <TableCell className="font-mono text-xs text-text-primary">{t.exit_date}</TableCell>
                      <TableCell className="text-right font-mono text-xs text-text-secondary">{formatIdr(t.entry_price)}</TableCell>
                      <TableCell className="text-right font-mono text-xs text-text-secondary">{formatIdr(t.exit_price)}</TableCell>
                      <TableCell
                        className={`text-right font-mono font-semibold text-xs ${
                          positive ? "text-bullish" : "text-bearish"
                        }`}
                      >
                        {formatPctId(t.return_pct)}
                      </TableCell>
                      <TableCell>
                        <span
                          className="inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium"
                          style={{
                            color,
                            borderColor: `color-mix(in srgb, ${color} 35%, transparent)`,
                            backgroundColor: `color-mix(in srgb, ${color} 10%, transparent)`,
                          }}
                        >
                          {exitReasonLabel(t.reason)}
                        </span>
                      </TableCell>
                      <TableCell className="text-right font-mono text-xs text-text-secondary">{t.hold_days}h</TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        </TabsContent>

        <TabsContent value="equity">
          <EquityCurveChart equityCurve={result.equity_curve} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
