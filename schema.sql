-- ============================================================================
-- IDX Quant Signal Dashboard — Supabase Schema
-- ============================================================================
-- Jalankan seluruh file ini di: Supabase Dashboard > SQL Editor > New Query
-- (Run sekali saat setup awal project)
--
-- ARSITEKTUR KEAMANAN:
--   - Semua tabel di bawah PUBLIC READ (siapa saja bisa SELECT via anon key,
--     karena dashboard ini memang dibuat publik dengan 1 sumber data yang sama).
--   - TIDAK ADA policy INSERT/UPDATE/DELETE untuk role anon -> hanya
--     SERVICE ROLE KEY (yang bypass RLS) yang bisa menulis. Service role key
--     HANYA boleh dipakai oleh worker_fetch_and_update.py via GitHub Actions
--     secret — JANGAN PERNAH taruh service role key di Streamlit secrets atau
--     di kode publik manapun.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. screener_results — ringkasan sinyal + backtest terkini per ticker
--    (di-upsert ulang oleh worker setiap hari bursa, 1 baris per ticker)
-- ----------------------------------------------------------------------------
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
    updated_at          timestamptz not null default now()
);

-- ----------------------------------------------------------------------------
-- 2. price_history — OHLCV + indikator + sinyal harian per ticker
--    (dipakai untuk render chart di tab Detail Saham; direplace penuh
--    per-ticker setiap run worker supaya data revisi dari Yahoo ikut update)
-- ----------------------------------------------------------------------------
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

-- ----------------------------------------------------------------------------
-- 3. backtest_trades — log setiap trade historis hasil backtest per ticker
--    (dipakai untuk tabel riwayat trade + SUM(return_pct) = Total Return
--    di tab Detail Saham)
-- ----------------------------------------------------------------------------
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

-- ----------------------------------------------------------------------------
-- 4. ongoing_positions — state machine posisi long, 1 aktif per ticker
-- ----------------------------------------------------------------------------
create table if not exists ongoing_positions (
    id                  bigserial primary key,
    ticker              text not null,
    status              text not null,  -- lihat position_manager.py utk daftar lengkap:
                                         -- PENDING_ENTRY | OPEN | CLOSED_TP | CLOSED_SL
                                         -- | CLOSED_SIGNAL | CLOSED_TIME
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

-- CONSTRAINT UTAMA (Catatan #1 requirement): hanya boleh ada 1 posisi AKTIF
-- (PENDING_ENTRY atau OPEN) per ticker pada satu waktu. Ini pengaman lapis-2
-- di level database — lapis-1 sudah di-enforce di position_manager.py.
create unique index if not exists one_active_position_per_ticker
    on ongoing_positions (ticker)
    where status in ('PENDING_ENTRY', 'OPEN');

-- Trigger kecil supaya updated_at otomatis ter-update tiap kali baris diubah
create or replace function set_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

drop trigger if exists trg_ongoing_positions_updated_at on ongoing_positions;
create trigger trg_ongoing_positions_updated_at
    before update on ongoing_positions
    for each row execute function set_updated_at();

-- ----------------------------------------------------------------------------
-- 5. update_log — riwayat tiap run worker (untuk transparansi "data terakhir
--    diupdate kapan" di dashboard, dan untuk debugging kalau ada run gagal)
-- ----------------------------------------------------------------------------
create table if not exists update_log (
    id                  bigserial primary key,
    run_at              timestamptz not null default now(),
    tickers_processed   int,
    tickers_failed      int,
    status              text,   -- 'OK' | 'FAILED' | 'SKIPPED'
    notes               text
);

-- ============================================================================
-- ROW LEVEL SECURITY — PUBLIC READ-ONLY
-- ============================================================================
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

-- TIDAK ADA policy insert/update/delete di atas -> role 'anon' (dipakai app.py
-- publik) hanya bisa baca. Hanya service_role (dipakai worker via GitHub
-- Actions secret) yang bisa menulis, karena service_role BYPASS RLS sepenuhnya.

-- ============================================================================
-- SELESAI. Setelah run script ini:
--   1. Ambil Project URL & anon key di: Project Settings > API
--      -> jadi SUPABASE_URL & SUPABASE_ANON_KEY (untuk Streamlit secrets)
--   2. Ambil service_role key di halaman yang sama
--      -> jadi SUPABASE_SERVICE_ROLE_KEY (untuk GitHub Actions secret SAJA)
-- ============================================================================
