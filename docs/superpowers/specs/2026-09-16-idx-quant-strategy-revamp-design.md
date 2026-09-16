# Technical Design Document: IDX Quant Signal Strategy & Execution Engine Revamp

- **Date:** 2026-09-16
- **Status:** Approved by User / Ready for Implementation
- **Author:** Senior Quantitative Developer & Trading Systems Architect
- **Target Projects:**
  - Python Backend: `C:\bima\Projects\Python\Idx-quant-signal-backend`
  - Next.js Frontend: `C:\bima\Projects\NextJS\idx-quant-signal-frontend`

---

## 1. Executive Summary & Root Cause Empirical Evidence

The portfolio's current ongoing positions and historical backtest exhibit a negative mathematical expectancy, resulting in cumulative deficits (-12.43% on live simulated trades, -334.02% across the 1,028-trade historical universe).

### Empirical Diagnostics from Historical Data:
1. **The Expectancy Deficit**:
   - Win Rate: 29.86% (Backtest) / 30.56% (Live Ongoing).
   - Realized Risk-to-Reward: ~1 : 2.0 (Avg Win +6.50% vs Avg Loss -3.24%).
   - Break-even win rate required: $\frac{1}{1+2} = 33.33\%$.
   - Because $30.56\% < 33.33\%$, the strategy suffers negative expectancy ($-0.35\%$ per trade), compounded by market friction (broker commissions & slippage).
2. **Counter-Trend Contamination (51.5% of Trades)**:
   - In `signals.py`, `buy_score >= 2 & macd_cross_up` triggered BUY signals even when `uptrend` was False (stocks below SMA200/SMA50).
   - Backtest simulation proves that 530 out of 1,028 trades were taken in non-uptrend conditions, generating a net -226% drag on portfolio equity.
3. **Premature Noise Stop-Outs (61.9% of Losses)**:
   - Initial Stop Loss of $1.0 \times \text{ATR}$ is equivalent to the typical single-day fluctuation of liquid IDX stocks.
   - 431 out of 696 stopped-out trades were knocked out within 1 to 2 days before any swing could mature.
4. **Capped Upside (TP Rigid 2.0 ATR)**:
   - Capping profit at +2.0 ATR prevents trend-following positions from riding fat-tail trends (e.g. 5x - 15x ATR on strong secular runners).
5. **Execution Scheduling Flaws**:
   - GitHub Actions workflow runs at 08:35 WIB (pre-market, incomplete data) and 12:37 WIB (mid-day, half-day volume), creating false volume spikes and premature intra-day stop-outs on unclosed daily candles.

---

## 2. Core Architectural Decisions & System Enhancements

### Decision 1: Target Universe Scope
All liquid target emiten in the configured IDX universe (IDX30 and LQ45) remain eligible. Rather than cherry-picking or banning specific emiten, the core strategy engine is enhanced to establish a statistical edge across all target tickers.

### Decision 2: Market Regime Gate (IHSG `^JKSE`)
- A new market filter checks the Jakarta Composite Index (`^JKSE`) daily trend.
- If IHSG is below its SMA200 (`Close < SMA200`), the market environment is classified as **Defensive/Risk-Off**. All new BUY signals are suppressed.

### Decision 3: Enhanced Entry Engine (`signals.py`)
A BUY signal (`Signal = 1`) is generated **only if ALL of the following criteria are met simultaneously**:
1. **Structural Uptrend Hard Gate**: $\text{Close} > \text{SMA50}$ AND $\text{SMA50} > \text{SMA200}$.
2. **Momentum Confirmation**: MACD bullish crossover ($\text{MACD} > \text{Signal}$ with prior bar $\le$) AND healthy non-overbought RSI ($40 \le \text{RSI14} \le 65$).
3. **Volume Participation**: $\text{VolRatio20} \ge 1.2$ on the finalized EOD candle.
4. **Anti-FOMO / Low-Risk Entry Buffer**: $\text{Close} \le \text{SMA20} \times 1.05$ (entry occurs within 5% of SMA20, not chasing extended parabolic moves).

### Decision 4: Hybrid 2-Tier Exit System (`position_manager.py` & `backtester.py`)
1. **Initial Stop Loss**: Expanded to $\text{Entry Price} - 1.5 \times \text{ATR}$ (granting sufficient breathing room past daily noise).
2. **Tier 1 (Partial Take Profit @ +2.0 ATR)**:
   - When $\text{High} \ge \text{Entry Price} + 2.0 \times \text{ATR}$, take 50% profit.
   - Immediately adjust the Stop Loss of the remaining 50% position to $\text{Entry Price}$ (**Break-Even**).
   - This eliminates downside risk for the remaining trade while locking in a guaranteed gain.
3. **Tier 2 (Runner Trailing Exit @ Daily Close < SMA20)**:
   - The remaining 50% position rides the trend freely with trailing protection.
   - Exit trigger: A finalized daily bar closes below SMA20 ($\text{Close} < \text{SMA20}$).
   - Worst case after Tier 1: Exit at Break-Even. Best case: Capture 10x-20x ATR mega-trends.
4. **Full Stop Loss (Pre-TP1)**:
   - If price drops to $\text{Entry Price} - 1.5 \times \text{ATR}$ before Tier 1 is reached, exit 100% of the position.

### Decision 5: Portfolio Capacity & Sizing Engine
- **Max Concurrent Positions**: 5 to 7 open positions.
- **Sector Concentration Limit**: Maximum 2 concurrent positions per sector (e.g. max 2 mining or 2 banking stocks).
- **Signal Priority Queue**: If valid BUY signals exceed available portfolio slots, rank candidates by:
  1. `SignalStrength` (confirmation count).
  2. Lowest percentage distance to SMA20 (closest to structural support = lowest risk).
  3. Lowest ATR volatility.

### Decision 6: Execution Schedule Alignment (`update_after_market_close.yml`)
- **Remove 08:35 WIB cron**: Pre-market run is redundant and carries stale or unaligned candle risks.
- **EOD Master Run (16:34 WIB, Mon-Fri)**: Official run on finalized daily OHLCV bars. Generates signals, calculates indicators, updates database, and queues `PENDING_ENTRY` for next day's open.
- **Mid-Day Position Sync (12:37 WIB Mon-Thu / 12:08 WIB Fri)**: Runs in `--monitor-only` mode. Only checks TP1 and Stop Loss on existing `OPEN` positions using Session 1 High/Low. Does NOT generate new BUY signals or screen incomplete half-day volume.

---

## 3. Database Schema & State Transition Updates

### Ongoing Position States:
- `PENDING_ENTRY`: BUY signal confirmed at EOD; waiting for execution at next trading day Open.
- `OPEN_FULL`: Position active with 100% allocation; SL at `entry - 1.5 * atr`.
- `OPEN_RUNNER`: Tier 1 (+2.0 ATR) achieved for 50%; remaining 50% trailing with SL at `entry_price`.
- `CLOSED_TP1_RUNNER`: Fully closed (Tier 1 reached, runner exited on Close < SMA20).
- `CLOSED_TP1_BE`: Tier 1 reached, runner exited at Break-Even.
- `CLOSED_SL`: 100% closed at Initial Stop Loss (`entry - 1.5 * atr`).
- `CLOSED_SIGNAL`: Closed on sell signal or trend invalidation.

---

## 4. Verification & Testing Strategy
1. **Unit & Regression Testing**:
   - Test signal generation edge cases (Uptrend hard gate, RSI boundaries, SMA20 distance limit).
   - Test hybrid 2-tier exit logic (TP1 hit, SL moved to BE, runner exit on Close < SMA20).
2. **Historical Simulation Benchmark**:
   - Re-run backtest on the full 5-year dataset in `data-example/price_history_rows.csv`.
   - Acceptance criteria: Positive net return, Profit Factor $\ge 1.2$, significant reduction in 1-day stop outs.
