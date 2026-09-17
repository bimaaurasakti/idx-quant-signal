-- ============================================================================
-- IDX Quant Signal Dashboard — Supabase Schema Reference
-- ============================================================================
create table if not exists screener_results (
    ticker              text primary key,
    sektor              text,
    last_close          numeric,
    last_date           date,
    signal_today        text,       -- 'BUY' | 'SELL' | 'HOLD' | 'NO_DATA'
    signal_strength     int,        -- 0-3, jumlah konfirmasi yang terpenuhi
    trend               text,       -- 'Uptrend' | 'Downtrend' | 'Sideways/Mixed'
    rsi                 numeric,
    atr                 numeric,
    winrate             numeric,    -- persen
    expectancy_pct      numeric,    -- persen
    profit_factor       numeric,
    max_drawdown_pct    numeric,    -- persen, negatif
    n_trades            int,        -- jumlah trade historis dari backtest
    sharpe_rough        numeric,
    is_idx30            boolean not null default false,
    is_lq45             boolean not null default false,
    updated_at          timestamptz not null default now()
);

create table if not exists price_history (
    ticker          text not null,
    date            date not null,
    open            numeric,
    high            numeric,
    low             numeric,
    close           numeric,
    volume          bigint,
    sma20           numeric,
    sma50           numeric,
    sma200          numeric,
    rsi14           numeric,
    macd            numeric,
    macd_signal     numeric,
    macd_hist       numeric,
    atr14           numeric,
    signal          int,        -- -1 (SELL) | 0 (HOLD) | 1 (BUY)
    primary key (ticker, date)
);

create index if not exists idx_price_history_ticker on price_history (ticker);

create table if not exists backtest_trades (
    id              bigserial primary key,
    ticker          text not null,
    entry_date      date,
    exit_date       date,
    entry_price     numeric,
    exit_price      numeric,
    return_pct      numeric,
    reason          text,   -- 'TP' | 'SL' | 'SELL_SIGNAL' | 'TIME_EXIT'
    hold_days       int
);

create index if not exists idx_backtest_trades_ticker on backtest_trades (ticker);

create table if not exists ongoing_positions (
    id                  bigserial primary key,
    ticker              text not null,
    status              text not null,
    signal_date         date,
    planned_entry_date  date,
    entry_date          date,
    entry_price         numeric,
    atr_at_signal       numeric,
    tp_price            numeric,
    sl_price            numeric,
    exit_date           date,
    exit_price          numeric,
    exit_reason         text,
    return_pct          numeric,
    created_at          timestamptz not null default now(),
    updated_at          timestamptz not null default now()
);

create index if not exists idx_ongoing_positions_ticker on ongoing_positions (ticker);
create index if not exists idx_ongoing_positions_status on ongoing_positions (status);

create unique index if not exists one_active_position_per_ticker
    on ongoing_positions (ticker)
    where status in ('PENDING_ENTRY', 'OPEN');

create table if not exists update_log (
    id                  bigserial primary key,
    run_at              timestamptz not null default now(),
    tickers_processed   int,
    tickers_failed      int,
    status              text,   -- 'OK' | 'FAILED' | 'SKIPPED'
    notes               text
);

-- Row Level Security: Public Read-Only
alter table screener_results   enable row level security;
alter table price_history      enable row level security;
alter table backtest_trades    enable row level security;
alter table ongoing_positions  enable row level security;
alter table update_log         enable row level security;

create policy "public read screener_results"  on screener_results  for select using (true);
create policy "public read price_history"     on price_history     for select using (true);
create policy "public read backtest_trades"   on backtest_trades   for select using (true);
create policy "public read ongoing_positions" on ongoing_positions for select using (true);
create policy "public read update_log"        on update_log        for select using (true);
