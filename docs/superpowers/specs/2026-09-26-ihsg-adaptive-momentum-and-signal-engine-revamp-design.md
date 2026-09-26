# Technical Design Document: Dual-Horizon IHSG Adaptive Momentum & Flexible Multi-Confirmation Signal Engine

- **Date:** 2026-09-26
- **Status:** Approved by User / Ready for Implementation Plan
- **Author:** Senior Quantitative Developer & Trading Systems Architect
- **Target Projects:** `idx-quant-signal-frontend` (Monorepo: Next.js Dashboard + Python Quant Pipeline)

---

## 1. Executive Summary & Root Cause Empirical Evidence

Between September 16 and September 26, 2026 (over 2 to 3 weeks), the quantitative screener failed to generate a single BUY signal across all 45 tickers in the IDX30 and LQ45 universe. In addition, all historical backtest performance metrics in the dashboard screener collapsed into `null` (`winrate: null`, `expectancy_pct: null`, `n_trades: 0`).

### Root Causes Discovered:
1. **IHSG Macro Hard-Gate Circuit Breaker (`check_ihsg_regime`)**:
   - IHSG (`^JKSE`) closed at **6,241.89** vs SMA200 of **7,227.45** (~1,000 points / -13.6% below SMA200).
   - In `signals.py`, `if not market_bullish: buy_valid = pd.Series(False, index=d.index)`.
   - Because IHSG has been below SMA200 every day in September, **100% of all BUY signals were globally killed**, even for stocks showing independent relative strength.
2. **The "5-Way Coincidence" Conjunction Trap**:
   - Even without the IHSG filter, the engine demanded 5 rigid conditions on the exact same daily candle:
     1. Structural Uptrend (`Close > SMA50 > SMA200`) — only 9.9% pass rate in September.
     2. Single-day MACD Golden Cross (`Cross on day t`) — 2.6% pass rate.
     3. Volume Spike (`VolRatio20 >= 1.2`) — 24.2% pass rate.
     4. RSI in healthy bull zone (`40 <= RSI <= 65`) — 67.1% pass rate.
     5. Anti-FOMO buffer (`Close <= SMA20 * 1.05`) — 87.6% pass rate.
   - Empirical simulation on 855 stock-day bars in September 2026 revealed that the mathematical probability of all 5 occurring on the exact same bar is **~0.1%** (only 1 occurrence: AKRA on Sep 7). For 18 consecutive trading days, exactly zero stocks met this rigid standard.
3. **Critical Data Contamination Bug**:
   - Setting `buy_valid = pd.Series(False, index=d.index)` when `market_bullish == False` erased 5 years of historical signals in the DataFrame `d`.
   - This wiped out the event-driven backtester (`backtester.py`), causing `0` trades and `null` winrate/expectancy across all 45 stocks in Supabase.

---

## 2. Core Architectural Decisions

### Decision 1: Dual-Horizon IHSG Market Regime & Adaptive Sizing
Instead of a binary 0/1 kill switch, the system implements a quantitative **Dual-Horizon Framework**:

1. **Macro Trend Horizon (Structural Health)**:
   - Evaluates long-term baseline: $\text{Close}_{\text{IHSG}} \ge \text{SMA200}_{\text{IHSG}}$.
   - **Bullish Macro**: Structural bull market. Full capital deployment.
   - **Bearish Macro**: Structural bear market. Selective, tactical capital deployment.

2. **Micro Momentum Horizon (Tactical Timing Gate)**:
   - Evaluates short-term swing velocity to predict next-day bullish follow-through:
     - **Price Action**: $\text{Close}_t \ge \text{Open}_t$ OR $\text{Close}_t \ge \text{Close}_{t-1}$ (Green/reversal candle).
     - **Momentum Acceleration**: $\text{MACD Hist}_t > \text{MACD Hist}_{t-1}$ (selling exhaustion / positive momentum surge).
   - If Micro Momentum is **Red/Adverse** (market dumping with accelerating selling volume): **NO NEW BUY SIGNALS** (Cash is King, avoids gap-down traps).
   - If Micro Momentum is **Green/Favorable**: Trading signals are enabled according to the Regime Matrix.

### Decision 2: Quantitative Regime & Sizing Matrix

| Regime State | Macro IHSG | Tactical Momentum | Signal Generation | Capital Sizing | Max Positions | Required Conviction |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Tier 1: High Alpha** | Bull ($\ge \text{SMA200}$) | Green / Accelerating | Full BUY | 100% Lot | 7 positions | Score $\ge 2$ |
| **Tier 2: Tactical Swing** | Bear ($< \text{SMA200}$) | Green / Accelerating | Tactical BUY | 50% Lot | 3 positions | Score $\ge 3$ (Uptrend required) |
| **Tier 3: Risk-Off** | Any | Red / Decelerating | CASH / WAIT | 0% Lot | 0 new entries | - |

### Decision 3: Flexible Lookback Window (3-Day Confirmation Engine)
To eliminate the "5-Way Coincidence" trap while preserving strict risk discipline:
1. **Trend Baseline (Mandatory)**: Stock must be in structural uptrend ($\text{Close} > \text{SMA50}$ AND $\text{SMA50} > \text{SMA200}$, or $\text{Close} > \text{SMA200}$).
2. **Momentum Lookback (3 Days)**:
   - MACD Golden Cross within the last 3 bars ($\text{rolling}(3).\text{max}() == 1$) AND currently $\text{MACD} > \text{Signal}$.
   - Healthy RSI: $40 \le \text{RSI14} \le 68$.
3. **Volume Accumulation Lookback (3 Days)**:
   - Volume expansion $\ge 1.2\times$ within the last 3 bars OR current bar $\ge 1.1\times$.
4. **Anti-FOMO Guardrail**:
   - Price must remain within $5\%$ of structural support ($\text{Close} \le \text{SMA20} \times 1.05$).

### Decision 4: Backtest Integrity & Historical Date Alignment
- `market_bullish` will no longer mutate the historical DataFrame `d.index`.
- Live signal evaluation for `SignalToday` and `_maybe_open_new_position` operates strictly on the latest finalized candle ($t = -1$).
- Historical backtest (`backtester.py`) will accurately compute 5-year equity curve, win rate, and profit factor, restoring data to the frontend screener.

### Decision 5: Frontend Market Regime Header Widget
Add an interactive Market Regime indicator widget to the Next.js Screener header:
- Real-time IHSG status: Macro (Bull/Bear), Daily Momentum (Green/Red), and Active Regime Tier.
- Recommended Sizing: **100%**, **50% (Tactical)**, or **0% (Cash/Defensive)**.
- Visual badge explaining why signals are enabled or constrained.

---

## 3. Database Schema Updates
Add columns to `update_log` and `screener_results` (or derive dynamically):
- `update_log.notes` stores: `[EOD MASTER | IHSG=TACTICAL_SWING | SIZING=50%]`.
- Screener and Detail APIs continue using existing contracts with clean data.

---

## 4. Verification & Testing Plan
1. **Unit Test Python Pipeline**:
   - Verify `signals.py` generates valid signals with lookback window.
   - Verify `market_bullish` does not erase historical signals in `d`.
   - Verify `backtester.py` returns non-null metrics across 45 tickers.
2. **Empirical Simulation**:
   - Run simulation over August-September 2026 to ensure healthy signal flow without over-trading (expect 3-6 high-quality signals/month during bear rebounds).
3. **Frontend Build & Render**:
   - Verify Next.js components render the new Market Regime Widget cleanly on desktop and mobile.
