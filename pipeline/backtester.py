"""
Backtester sederhana namun jujur (event-driven, no lookahead bias).
"""
from __future__ import annotations
import numpy as np
import pandas as pd

R_MULTIPLE_TP = 2.0      # take profit tier 1 = 2x ATR (amankan 50% porsi)
SL_ATR_MULT = 1.5        # initial stop loss = 1.5x ATR (hindari 1-2 day noise stop-out)
MAX_HOLD_DAYS = 30       # batas waktu holding maksimal


def backtest_signals(
    d: pd.DataFrame,
    r_multiple_tp: float = R_MULTIPLE_TP,
    sl_atr_mult: float = SL_ATR_MULT,
    max_hold_days: int = MAX_HOLD_DAYS,
) -> dict:
    """
    Input: DataFrame hasil generate_signals() (punya kolom Signal, ATR14, Close, High, Low, SMA20).
    Output: dict metrik + list trade detail.
    """
    if d is None or len(d) < 60:
        return _empty_result()

    trades = []
    n = len(d)
    opens = d["Open"].values
    closes = d["Close"].values
    highs = d["High"].values
    lows = d["Low"].values
    atrs = d["ATR14"].values
    signals = d["Signal"].values
    sma20s = d["SMA20"].values if "SMA20" in d.columns else pd.Series(closes).rolling(20, min_periods=20).mean().values
    dates = d.index

    i = 0
    while i < n - 1:
        if signals[i] == 1 and not np.isnan(atrs[i]):
            entry_idx = i + 1  # entry di hari berikutnya
            if entry_idx >= n:
                break
            entry_price = opens[entry_idx]
            atr_at_entry = atrs[i]
            tp1_price = entry_price + r_multiple_tp * atr_at_entry
            sl_price = entry_price - sl_atr_mult * atr_at_entry

            exit_price = None
            exit_reason = None
            exit_idx = None
            ret_pct = 0.0

            tp1_hit = False
            half1_ret = 0.0
            current_sl = sl_price

            for j in range(entry_idx + 1, min(entry_idx + 1 + max_hold_days, n)):
                if not tp1_hit:
                    if lows[j] <= current_sl:
                        exit_price = current_sl
                        exit_reason = "SL"
                        exit_idx = j
                        ret_pct = (exit_price - entry_price) / entry_price * 100
                        break
                    elif highs[j] >= tp1_price:
                        tp1_hit = True
                        half1_ret = (tp1_price - entry_price) / entry_price * 100 * 0.5
                        current_sl = entry_price
                        if lows[j] <= current_sl:
                            exit_price = current_sl
                            exit_reason = "TP1_BE"
                            exit_idx = j
                            ret_pct = half1_ret
                            break
                        continue
                    elif signals[j] == -1:
                        exit_price = closes[j]
                        exit_reason = "SELL_SIGNAL"
                        exit_idx = j
                        ret_pct = (exit_price - entry_price) / entry_price * 100
                        break
                else:
                    if lows[j] <= current_sl:
                        exit_price = current_sl
                        exit_reason = "TP1_BE"
                        exit_idx = j
                        ret_pct = half1_ret
                        break
                    elif not np.isnan(sma20s[j]) and closes[j] < sma20s[j]:
                        exit_price = closes[j]
                        exit_reason = "TP1_RUNNER"
                        exit_idx = j
                        half2_ret = (exit_price - entry_price) / entry_price * 100 * 0.5
                        ret_pct = half1_ret + half2_ret
                        break
                    elif signals[j] == -1:
                        exit_price = closes[j]
                        exit_reason = "TP1_SIGNAL"
                        exit_idx = j
                        half2_ret = (exit_price - entry_price) / entry_price * 100 * 0.5
                        ret_pct = half1_ret + half2_ret
                        break

            if exit_price is None:
                last_j = min(entry_idx + max_hold_days, n - 1)
                exit_price = closes[last_j]
                exit_idx = last_j
                if tp1_hit:
                    half2_ret = (exit_price - entry_price) / entry_price * 100 * 0.5
                    ret_pct = half1_ret + half2_ret
                    exit_reason = "TP1_TIME"
                else:
                    ret_pct = (exit_price - entry_price) / entry_price * 100
                    exit_reason = "TIME_EXIT"

            trades.append({
                "entry_date": dates[entry_idx],
                "exit_date": dates[exit_idx],
                "entry_price": round(float(entry_price), 2),
                "exit_price": round(float(exit_price), 2),
                "return_pct": round(float(ret_pct), 2),
                "reason": exit_reason,
                "hold_days": int(exit_idx - entry_idx),
            })
            i = exit_idx + 1
        else:
            i += 1

    return _compute_metrics(trades)


def _empty_result() -> dict:
    return {
        "n_trades": 0, "winrate": None, "avg_win_pct": None, "avg_loss_pct": None,
        "expectancy_pct": None, "profit_factor": None, "max_drawdown_pct": None,
        "sharpe_rough": None, "trades": [],
    }


def _compute_metrics(trades: list[dict]) -> dict:
    if not trades:
        return _empty_result()

    df = pd.DataFrame(trades)
    wins = df[df["return_pct"] > 0]
    losses = df[df["return_pct"] <= 0]

    n_trades = len(df)
    winrate = len(wins) / n_trades * 100
    avg_win = wins["return_pct"].mean() if not wins.empty else 0.0
    avg_loss = abs(losses["return_pct"].mean()) if not losses.empty else 0.0
    lossrate = 100 - winrate

    expectancy = (winrate / 100 * avg_win) - (lossrate / 100 * avg_loss)

    total_profit = wins["return_pct"].sum() if not wins.empty else 0.0
    total_loss = abs(losses["return_pct"].sum()) if not losses.empty else 0.0
    profit_factor = (total_profit / total_loss) if total_loss > 0 else np.inf

    equity = (1 + df["return_pct"] / 100).cumprod()
    running_max = equity.cummax()
    drawdown = (equity - running_max) / running_max * 100
    max_dd = drawdown.min()

    ret_std = df["return_pct"].std()
    sharpe_rough = (df["return_pct"].mean() / ret_std * np.sqrt(n_trades)) if ret_std and ret_std > 0 else 0.0

    return {
        "n_trades": n_trades,
        "winrate": round(winrate, 1),
        "avg_win_pct": round(avg_win, 2),
        "avg_loss_pct": round(avg_loss, 2),
        "expectancy_pct": round(expectancy, 2),
        "profit_factor": round(profit_factor, 2) if np.isfinite(profit_factor) else None,
        "max_drawdown_pct": round(float(max_dd), 2),
        "sharpe_rough": round(float(sharpe_rough), 2),
        "trades": trades,
    }
