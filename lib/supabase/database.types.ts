/**
 * lib/supabase/database.types.ts
 * ================================
 * Tipe mentah tabel Supabase, cermin 1:1 dari schema.sql. Idealnya
 * di-generate otomatis lewat Supabase CLI:
 *
 *   supabase gen types typescript --project-id <ref> > lib/supabase/database.types.ts
 *
 * Versi di bawah ditulis manual mengikuti schema.sql yang ada di project
 * ini -- kalau schema berubah, regenerate atau update manual di sini.
 * File ini TIDAK dipakai langsung oleh komponen UI; itu tugas lib/types.ts
 * (lihat lib/supabase/mappers.ts sebagai jembatan keduanya).
 */

export interface Database {
  public: {
    Tables: {
      screener_results: {
        Row: {
          ticker: string;
          sektor: string | null;
          last_close: number | null;
          last_date: string | null;
          signal_today: string | null;
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
          updated_at: string;
          is_idx30: boolean;
          is_lq45: boolean;
        };
      };
      price_history: {
        Row: {
          ticker: string;
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
          atr14: number | null;
          signal: number | null;
        };
      };
      backtest_trades: {
        Row: {
          id: number;
          ticker: string;
          entry_date: string | null;
          exit_date: string | null;
          entry_price: number | null;
          exit_price: number | null;
          return_pct: number | null;
          reason: string | null;
          hold_days: number | null;
        };
      };
      ongoing_positions: {
        Row: {
          id: number;
          ticker: string;
          status: string;
          signal_date: string | null;
          planned_entry_date: string | null;
          entry_date: string | null;
          entry_price: number | null;
          atr_at_signal: number | null;
          tp_price: number | null;
          sl_price: number | null;
          exit_date: string | null;
          exit_price: number | null;
          exit_reason: string | null;
          return_pct: number | null;
          created_at: string;
          updated_at: string;
        };
      };
      update_log: {
        Row: {
          id: number;
          run_at: string;
          tickers_processed: number | null;
          tickers_failed: number | null;
          status: string | null;
          notes: string | null;
        };
      };
    };
  };
}

export type ScreenerResultsRow = Database["public"]["Tables"]["screener_results"]["Row"];
export type PriceHistoryRow = Database["public"]["Tables"]["price_history"]["Row"];
export type BacktestTradesRow = Database["public"]["Tables"]["backtest_trades"]["Row"];
export type OngoingPositionsRow = Database["public"]["Tables"]["ongoing_positions"]["Row"];
export type UpdateLogRow = Database["public"]["Tables"]["update_log"]["Row"];
