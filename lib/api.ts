/**
 * lib/api.ts
 * ===========
 * SATU-SATUNYA titik komunikasi frontend ke sumber data. Seluruh fungsi di
 * bawah membaca LANGSUNG dari Supabase lewat @supabase/supabase-js (anon
 * key, dilindungi RLS public-read-only di schema.sql) -- TIDAK ADA backend
 * API terpisah yang perlu dijalankan untuk menjalankan dashboard ini.
 *
 * STATUS: `metaIndicators()` dan `runBacktest()` (Backtest Lab) SENGAJA
 * belum diimplementasikan -- engine backtest TypeScript belum di-porting
 * dari backend Python (butuh source code indicators.py/signals.py/
 * backtester.py untuk verifikasi formula, lihat §6.3, §9.4, §13
 * IMPLEMENTATION_PLAN_SUPABASE_MIGRATION.md). Keduanya melempar ApiError
 * yang jelas alih-alih diam-diam gagal atau memanggil backend yang sudah
 * tidak dipakai lagi -- app/backtest/page.tsx sudah disesuaikan untuk
 * menampilkan status ini dengan rapi, bukan mencoba fetch ke URL mati.
 */
import { computeChangeAndChangePct, sum } from "@/lib/derive";
import { supabase } from "@/lib/supabase/client";
import {
  mapActivePosition,
  mapBuyTomorrowRow,
  mapClosedPosition,
  mapOpenPositionRow,
  mapPriceBar,
  mapScreenerRow,
  mapTradeRow,
} from "@/lib/supabase/mappers";
import type {
  BacktestTradesRow,
  OngoingPositionsRow,
  PriceHistoryRow,
  ScreenerResultsRow,
  UpdateLogRow,
} from "@/lib/supabase/database.types";
import type {
  BacktestRunRequest,
  BacktestRunResponse,
  IndicatorsMetaResponse,
  LastUpdateResponse,
  PortfolioResponse,
  ScreenerResponse,
  TickerDetailResponse,
  TickersMetaResponse,
} from "@/lib/types";

// CATATAN VERSI: lihat IMPLEMENTATION_PLAN_SUPABASE_MIGRATION.md §9.2 --
// @supabase/supabase-js meng-infer tipe hasil `.select()` dengan mem-parse
// string kolomnya di level tipe, dan untuk skema tanpa foreign key seperti
// ini parser tersebut bisa diam-diam jatuh ke `never`. Override generic
// eksplisit `.select<Query, ResultType>(...)` di bawah melompati itu --
// JANGAN dihapus meskipun terlihat redundan.

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

function assertNoError(label: string, error: { message: string } | null): void {
  if (error) throw new ApiError(500, `[${label}] ${error.message}`);
}

async function screener(): Promise<ScreenerResponse> {
  const [screenerRes, pendingRes, openRes, logRes] = await Promise.all([
    supabase.from("screener_results").select<"*", ScreenerResultsRow>("*").order("ticker"),
    supabase
      .from("ongoing_positions")
      .select<"*", OngoingPositionsRow>("*")
      .eq("status", "PENDING_ENTRY"),
    supabase.from("ongoing_positions").select<"*", OngoingPositionsRow>("*").eq("status", "OPEN"),
    supabase
      .from("update_log")
      .select<"run_at", Pick<UpdateLogRow, "run_at">>("run_at")
      .order("run_at", { ascending: false })
      .limit(1),
  ]);

  assertNoError("screener_results", screenerRes.error);
  assertNoError("ongoing_positions:PENDING_ENTRY", pendingRes.error);
  assertNoError("ongoing_positions:OPEN", openRes.error);
  assertNoError("update_log", logRes.error);

  // "Join" manual di JS -- tidak ada FK di schema.sql antar tabel ini,
  // dan skala data kecil (~45 ticker) membuat pendekatan ini lebih murah
  // daripada menambah view/FK di database (lihat §2 Prinsip Desain #4 &
  // §2 Prinsip #5 di rencana implementasi).
  const screenerByTicker = new Map((screenerRes.data ?? []).map((r) => [r.ticker, r]));

  return {
    updated_at: logRes.data?.[0]?.run_at ?? null,
    rows: (screenerRes.data ?? []).map(mapScreenerRow),
    buy_tomorrow: (pendingRes.data ?? []).map((p) =>
      mapBuyTomorrowRow(p, screenerByTicker.get(p.ticker)),
    ),
    ongoing_positions: (openRes.data ?? []).map((o) =>
      mapOpenPositionRow(o, screenerByTicker.get(o.ticker)),
    ),
  };
}

async function tickerDetail(ticker: string): Promise<TickerDetailResponse> {
  const [screenerRes, barsRes, activeRes, tradesRes] = await Promise.all([
    supabase
      .from("screener_results")
      .select<"*", ScreenerResultsRow>("*")
      .eq("ticker", ticker)
      .maybeSingle(),
    supabase
      .from("price_history")
      .select<"*", PriceHistoryRow>("*")
      .eq("ticker", ticker)
      .order("date", { ascending: true }),
    // Unique index `one_active_position_per_ticker` di schema.sql menjamin
    // maksimal 1 baris aktif (PENDING_ENTRY/OPEN) per ticker -> aman
    // pakai maybeSingle().
    supabase
      .from("ongoing_positions")
      .select<"*", OngoingPositionsRow>("*")
      .eq("ticker", ticker)
      .in("status", ["PENDING_ENTRY", "OPEN"])
      .maybeSingle(),
    supabase
      .from("backtest_trades")
      .select<"*", BacktestTradesRow>("*")
      .eq("ticker", ticker)
      .order("exit_date", { ascending: true }),
  ]);

  assertNoError("screener_results", screenerRes.error);
  assertNoError("price_history", barsRes.error);
  assertNoError("ongoing_positions", activeRes.error);
  assertNoError("backtest_trades", tradesRes.error);

  if (!screenerRes.data) {
    throw new ApiError(404, `Ticker "${ticker}" tidak ditemukan di screener_results.`);
  }

  const priceBars = (barsRes.data ?? []).map(mapPriceBar);
  const trades = (tradesRes.data ?? []).map(mapTradeRow);
  const { change, change_pct } = computeChangeAndChangePct(priceBars);

  return {
    ticker: screenerRes.data.ticker,
    sektor: screenerRes.data.sektor,
    last_close: screenerRes.data.last_close,
    change,
    change_pct,
    signal_today: screenerRes.data.signal_today,
    signal_strength: screenerRes.data.signal_strength,
    active_position: activeRes.data ? mapActivePosition(activeRes.data) : null,
    metrics: {
      winrate: screenerRes.data.winrate,
      expectancy_pct: screenerRes.data.expectancy_pct,
      profit_factor: screenerRes.data.profit_factor,
      max_drawdown_pct: screenerRes.data.max_drawdown_pct,
      // SUM dari array yang SUDAH di-fetch untuk tabel `trades` di bawah --
      // tidak perlu query agregat terpisah.
      total_return_pct: trades.length > 0 ? sum(trades.map((t) => t.return_pct)) : null,
    },
    price_history: priceBars,
    trades,
  };
}

async function portfolio(): Promise<PortfolioResponse> {
  const [closedRes, screenerRes] = await Promise.all([
    supabase
      .from("ongoing_positions")
      .select<"*", OngoingPositionsRow>("*")
      .like("status", "CLOSED_%"),
    supabase
      .from("screener_results")
      .select<"ticker, sektor", Pick<ScreenerResultsRow, "ticker" | "sektor">>("ticker, sektor"),
  ]);

  assertNoError("ongoing_positions:CLOSED", closedRes.error);
  assertNoError("screener_results", screenerRes.error);

  const sektorByTicker = new Map((screenerRes.data ?? []).map((r) => [r.ticker, r.sektor]));

  return {
    positions: (closedRes.data ?? []).map((pos) =>
      mapClosedPosition(pos, sektorByTicker.get(pos.ticker)),
    ),
  };
}

async function metaTickers(): Promise<TickersMetaResponse> {
  const { data, error } = await supabase
    .from("screener_results")
    .select<"ticker, sektor, is_idx30", Pick<ScreenerResultsRow, "ticker" | "sektor" | "is_idx30">>(
      "ticker, sektor, is_idx30",
    )
    .order("ticker");
  assertNoError("screener_results", error);

  const sectors: Record<string, string[]> = {};
  const idx30: string[] = [];

  for (const row of data ?? []) {
    const sektorKey = row.sektor ?? "Lainnya";
    (sectors[sektorKey] ??= []).push(row.ticker);
    if (row.is_idx30) idx30.push(row.ticker);
  }

  return { sectors, idx30 };
}

async function metaLastUpdate(): Promise<LastUpdateResponse> {
  const { data, error } = await supabase
    .from("update_log")
    .select<
      "run_at, tickers_processed, tickers_failed, status",
      Pick<UpdateLogRow, "run_at" | "tickers_processed" | "tickers_failed" | "status">
    >("run_at, tickers_processed, tickers_failed, status")
    .order("run_at", { ascending: false })
    .limit(1);
  assertNoError("update_log", error);

  const latest = data?.[0];
  return {
    run_at: latest?.run_at ?? null,
    tickers_processed: latest?.tickers_processed ?? null,
    tickers_failed: latest?.tickers_failed ?? null,
    status: (latest?.status as LastUpdateResponse["status"]) ?? null,
  };
}

// ---------------------------------------------------------------------------
// Backtest Lab -- BELUM diimplementasikan. Lihat docblock di atas file ini
// dan §6.3, §9.4, §13 IMPLEMENTATION_PLAN_SUPABASE_MIGRATION.md.
// ---------------------------------------------------------------------------

const BACKTEST_NOT_READY_MESSAGE =
  "Backtest Lab belum tersedia -- engine backtest TypeScript belum di-porting dari backend " +
  "(perlu verifikasi formula indikator/sinyal/metrik terhadap source code Python asli). " +
  "Lihat IMPLEMENTATION_PLAN_SUPABASE_MIGRATION.md \u00a76.3, \u00a79.4, \u00a713.";

async function metaIndicators(): Promise<IndicatorsMetaResponse> {
  throw new ApiError(501, BACKTEST_NOT_READY_MESSAGE);
}

async function runBacktest(_body: BacktestRunRequest): Promise<BacktestRunResponse> {
  throw new ApiError(501, BACKTEST_NOT_READY_MESSAGE);
}

export const api = {
  screener,
  tickerDetail,
  portfolio,
  metaIndicators,
  metaTickers,
  metaLastUpdate,
  runBacktest,
};
