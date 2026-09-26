/**
 * lib/supabase/mappers.ts
 * =========================
 * Jembatan antara bentuk data mentah Supabase (lib/supabase/database.types.ts)
 * dan kontrak tipe yang dipakai seluruh UI (lib/types.ts). Mengisolasi
 * quirk skema database dari komponen -- kalau schema berubah, cukup ubah
 * di sini, hooks & components/ tidak perlu tahu.
 */
import { businessDaysBetween, computeReturnPctNow } from "@/lib/derive";
import type {
  ActivePosition,
  BuyTomorrowRow,
  ClosedPosition,
  OpenPositionRow,
  PriceBar,
  ScreenerRow,
  TradeRow,
} from "@/lib/types";

import type {
  BacktestTradesRow,
  OngoingPositionsRow,
  PriceHistoryRow,
  ScreenerResultsRow,
} from "./database.types";

export function mapScreenerRow(row: ScreenerResultsRow): ScreenerRow {
  return {
    ticker: row.ticker,
    sektor: row.sektor,
    last_close: row.last_close,
    last_date: row.last_date,
    signal_today: row.signal_today as ScreenerRow["signal_today"],
    signal_strength: row.signal_strength,
    trend: row.trend,
    rsi: row.rsi,
    atr: row.atr,
    winrate: row.winrate,
    expectancy_pct: row.expectancy_pct,
    profit_factor: row.profit_factor,
    max_drawdown_pct: row.max_drawdown_pct,
    n_trades: row.n_trades,
    sharpe_rough: row.sharpe_rough,
    is_idx30: row.is_idx30,
    is_lq45: row.is_lq45,
  };
}

export function mapPriceBar(row: PriceHistoryRow): PriceBar {
  return {
    date: row.date,
    open: row.open,
    high: row.high,
    low: row.low,
    close: row.close,
    volume: row.volume,
    sma20: row.sma20,
    sma50: row.sma50,
    sma200: row.sma200,
    rsi14: row.rsi14,
    macd: row.macd,
    macd_signal: row.macd_signal,
    macd_hist: row.macd_hist,
    signal: (row.signal ?? 0) as PriceBar["signal"],
  };
}

export function mapTradeRow(row: BacktestTradesRow): TradeRow {
  return {
    entry_date: row.entry_date ?? "",
    exit_date: row.exit_date ?? "",
    entry_price: row.entry_price ?? 0,
    exit_price: row.exit_price ?? 0,
    return_pct: row.return_pct ?? 0,
    reason: (row.reason ?? "TIME_EXIT") as TradeRow["reason"],
    hold_days: row.hold_days ?? 0,
  };
}

export function mapOngoingClosedToTradeRow(pos: OngoingPositionsRow): TradeRow {
  return {
    entry_date: pos.entry_date ?? "",
    exit_date: pos.exit_date ?? "",
    entry_price: pos.entry_price ?? 0,
    exit_price: pos.exit_price ?? 0,
    return_pct: pos.return_pct ?? 0,
    reason: (pos.exit_reason ?? "TIME_EXIT") as TradeRow["reason"],
    hold_days:
      pos.entry_date && pos.exit_date ? businessDaysBetween(pos.entry_date, pos.exit_date) : 0,
  };
}

export function mapActivePosition(pos: OngoingPositionsRow): ActivePosition {
  return {
    status: pos.status as ActivePosition["status"],
    planned_entry_date: pos.planned_entry_date,
    entry_date: pos.entry_date,
    entry_price: pos.entry_price,
    tp_price: pos.tp_price,
    sl_price: pos.sl_price,
  };
}

/**
 * `screener` bisa `undefined` kalau ticker sudah tidak ada di
 * screener_results (edge case, mis. delisting) -- semua field terkait
 * fallback ke null, bukan melempar error, supaya 1 ticker bermasalah tidak
 * menjatuhkan seluruh halaman Screener.
 */
export function mapBuyTomorrowRow(
  pos: OngoingPositionsRow,
  screener: ScreenerResultsRow | undefined,
): BuyTomorrowRow {
  return {
    ticker: pos.ticker,
    sektor: screener?.sektor ?? null,
    // PENDING_ENTRY seharusnya selalu punya planned_entry_date; fallback ke
    // signal_date lalu string kosong murni jaga-jaga.
    planned_entry_date: pos.planned_entry_date ?? pos.signal_date ?? "",
    signal_strength: screener?.signal_strength ?? null,
    winrate: screener?.winrate ?? null,
    expectancy_pct: screener?.expectancy_pct ?? null,
    profit_factor: screener?.profit_factor ?? null,
    last_close: screener?.last_close ?? null,
  };
}

export function mapOpenPositionRow(
  pos: OngoingPositionsRow,
  screener: ScreenerResultsRow | undefined,
): OpenPositionRow {
  const lastClose = screener?.last_close ?? null;
  const lastDate = screener?.last_date ?? null;
  return {
    ticker: pos.ticker,
    sektor: screener?.sektor ?? null,
    entry_price: pos.entry_price,
    tp_price: pos.tp_price,
    sl_price: pos.sl_price,
    entry_date: pos.entry_date,
    last_close: lastClose,
    last_date: lastDate,
    return_pct_now: computeReturnPctNow(pos.entry_price, lastClose),
    hold_days: pos.entry_date && lastDate ? businessDaysBetween(pos.entry_date, lastDate) : null,
  };
}

/**
 * `sektor` diambil terpisah (bukan seluruh row screener_results) karena
 * ClosedPosition hanya butuh field ini dari sana -- lihat api.ts::portfolio()
 * yang cuma select("ticker, sektor").
 */
export function mapClosedPosition(
  pos: OngoingPositionsRow,
  sektor: string | null | undefined,
): ClosedPosition {
  return {
    ticker: pos.ticker,
    sektor: sektor ?? "-", // fallback kalau ticker sudah tidak ada di screener_results
    status: pos.status as ClosedPosition["status"],
    signal_date: pos.signal_date,
    entry_date: pos.entry_date ?? "",
    entry_price: pos.entry_price ?? 0,
    exit_date: pos.exit_date ?? "",
    exit_price: pos.exit_price ?? 0,
    return_pct: pos.return_pct ?? 0,
    hold_days:
      pos.entry_date && pos.exit_date ? businessDaysBetween(pos.entry_date, pos.exit_date) : 0,
  };
}
