/**
 * lib/types.ts
 * =============
 * Cermin 1:1 dari api/schemas/*.py di backend (§4.4 implementation plan).
 * Field name SENGAJA snake_case di kedua sisi supaya tidak perlu mapping
 * manual antara response JSON backend dan tipe di sini.
 */

// ---------------- /api/meta/* ----------------
export interface IndicatorParamSpec {
  type: "int" | "float";
  default: number;
  min: number | null;
  max: number | null;
}

export interface IndicatorSpec {
  key: string;
  label: string;
  category: "Trend" | "Momentum" | "Volatilitas" | "Volume";
  tier: 1 | 2;
  overlay: boolean;
  params: Record<string, IndicatorParamSpec>;
}

export interface IndicatorsMetaResponse {
  indicators: IndicatorSpec[];
  categories: string[];
  max_indicators_selected: number;
}

export interface LastUpdateResponse {
  run_at: string | null;
  tickers_processed: number | null;
  tickers_failed: number | null;
  status: "OK" | "SKIPPED" | "FAILED" | null;
}

export interface TickersMetaResponse {
  sectors: Record<string, string[]>;
  idx30: string[];
}

// ---------------- /api/screener ----------------
export interface ScreenerRow {
  ticker: string;
  sektor: string | null;
  last_close: number | null;
  last_date: string | null;
  signal_today: "BUY" | "SELL" | "HOLD" | "NO_DATA" | null;
  signal_strength: number | null;
  trend: string | null;
  rsi: number | null;
  atr: number | null;
  winrate: number | null;
  expectancy_pct: number | null;
  profit_factor: number | null;
  max_drawdown_pct: number | null;
  n_trades: number | null;
  sharpe_rough: number | null;
  is_idx30: boolean;
  is_lq45: boolean;
}

export interface BuyTomorrowRow {
  ticker: string;
  sektor: string | null;
  planned_entry_date: string;
  signal_strength: number | null;
  winrate: number | null;
  expectancy_pct: number | null;
  profit_factor: number | null;
  last_close: number | null;
}

export interface OpenPositionRow {
  ticker: string;
  sektor: string | null;
  entry_price: number | null;
  tp_price: number | null;
  sl_price: number | null;
  entry_date: string | null;
  last_close: number | null;
  last_date: string | null;
  return_pct_now: number | null;
  hold_days: number | null;
}

export interface ScreenerResponse {
  updated_at: string | null;
  rows: ScreenerRow[];
  buy_tomorrow: BuyTomorrowRow[];
  ongoing_positions: OpenPositionRow[];
}

// ---------------- /api/tickers/{ticker} ----------------
export interface ActivePosition {
  status: "PENDING_ENTRY" | "OPEN";
  planned_entry_date?: string | null;
  entry_date?: string | null;
  entry_price?: number | null;
  tp_price?: number | null;
  sl_price?: number | null;
}

export interface DetailMetrics {
  winrate: number | null;
  expectancy_pct: number | null;
  profit_factor: number | null;
  max_drawdown_pct: number | null;
  total_return_pct: number | null;
}

export interface PriceBar {
  date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
  sma20: number | null;
  sma50: number | null;
  sma200: number | null;
  rsi14: number | null;
  macd: number | null;
  macd_signal: number | null;
  macd_hist: number | null;
  signal: -1 | 0 | 1;
}

export interface TradeRow {
  entry_date: string;
  exit_date: string;
  entry_price: number;
  exit_price: number;
  return_pct: number;
  reason: "TP" | "SL" | "SELL_SIGNAL" | "TIME_EXIT";
  hold_days: number;
}

export interface TickerDetailResponse {
  ticker: string;
  sektor: string | null;
  last_close: number | null;
  change: number | null;
  change_pct: number | null;
  signal_today: string | null;
  signal_strength: number | null;
  active_position: ActivePosition | null;
  metrics: DetailMetrics;
  price_history: PriceBar[];
  trades: TradeRow[];
}

// ---------------- /api/portfolio ----------------
export interface ClosedPosition {
  ticker: string;
  sektor: string;
  status: "CLOSED_TP" | "CLOSED_SL" | "CLOSED_SIGNAL" | "CLOSED_TIME";
  signal_date: string | null;
  entry_date: string;
  entry_price: number;
  exit_date: string;
  exit_price: number;
  return_pct: number;
  hold_days: number;
}

export interface PortfolioResponse {
  positions: ClosedPosition[];
}

// ---------------- POST /api/backtest/run ----------------
export interface BacktestRunRequest {
  ticker: string;
  period: "1y" | "2y" | "3y" | "5y";
  selected_indicators: string[];
  params: Record<string, Record<string, number>>;
  confirmation_threshold: number;
  tp_multiple: number;
  sl_multiple: number;
  max_hold_days: number;
}

export interface Bar {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface IndicatorSeries {
  key: string;
  label: string;
  overlay: boolean;
  values: (number | null)[];
}

export interface BacktestMetrics {
  n_trades: number;
  winrate: number | null;
  avg_win_pct: number | null;
  avg_loss_pct: number | null;
  expectancy_pct: number | null;
  profit_factor: number | null;
  max_drawdown_pct: number | null;
  sharpe_rough: number | null;
}

export interface BacktestRunResponse {
  ticker: string;
  bars: Bar[];
  indicator_series: IndicatorSeries[];
  bullish_count: number[];
  bearish_count: number[];
  signal: (-1 | 0 | 1)[];
  trades: TradeRow[];
  metrics: BacktestMetrics;
  equity_curve: number[];
  last_trade_confirmation: { filled: number; total: number } | null;
}
