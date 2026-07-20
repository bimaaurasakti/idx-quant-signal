"""
Backtester sederhana namun jujur (event-driven, no lookahead bias).

Aturan trade:
  - Entry: hari setelah sinyal BUY muncul (open hari berikutnya), bukan di close
    hari sinyal itu sendiri -> menghindari lookahead bias.
  - Exit: yang lebih dulu tercapai antara:
      a) Take profit  = entry + R_MULTIPLE * ATR_at_entry
      b) Stop loss    = entry - 1.0 * ATR_at_entry
      c) Sinyal SELL / exit signal muncul
      d) Max holding period (hari)
  - Position sizing tidak dihitung di sini (itu urusan risk manager di app),
    backtester ini fokus ke *kualitas sinyal* per trade (menang/kalah, R-multiple).

Metrik yang dihasilkan:
  - Winrate           = trade profit / total trade
  - Avg Win / Avg Loss (dalam %)
  - Expectancy        = (winrate * avg_win) - (lossrate * avg_loss)
  - Profit Factor     = total profit / total loss
  - Max Drawdown      = pada equity curve kumulatif dari trade-trade ini
  - Sharpe (kasar)    = mean(return per trade) / std(return per trade) * sqrt(n_trades_per_year proxy)
"""
from __future__ import annotations
import numpy as np
import pandas as pd

R_MULTIPLE_TP = 2.0      # take profit = 2x ATR (risk:reward 1:2)
SL_ATR_MULT = 1.0        # stop loss = 1x ATR
MAX_HOLD_DAYS = 20       # keluar paksa kalau belum kena TP/SL dalam 20 hari


def backtest_signals(d: pd.DataFrame) -> dict:
    """
    Input: DataFrame hasil generate_signals() (punya kolom Signal, ATR14, Close, High, Low).
    Output: dict metrik + list trade detail.
    """
    if d is None or len(d) < 60:
        return _empty_result()

    trades = []
    n = len(d)
    closes = d["Close"].values
    highs = d["High"].values
    lows = d["Low"].values
    atrs = d["ATR14"].values
    signals = d["Signal"].values
    dates = d.index

    i = 0
    while i < n - 1:
        if signals[i] == 1 and not np.isnan(atrs[i]):
            entry_idx = i + 1  # entry di hari berikutnya
            if entry_idx >= n:
                break
            entry_price = closes[entry_idx]
            atr_at_entry = atrs[i]
            tp_price = entry_price + R_MULTIPLE_TP * atr_at_entry
            sl_price = entry_price - SL_ATR_MULT * atr_at_entry

            exit_price = None
            exit_reason = None
            exit_idx = None

            for j in range(entry_idx + 1, min(entry_idx + 1 + MAX_HOLD_DAYS, n)):
                if lows[j] <= sl_price:
                    exit_price = sl_price
                    exit_reason = "SL"
                    exit_idx = j
                    break
                if highs[j] >= tp_price:
                    exit_price = tp_price
                    exit_reason = "TP"
                    exit_idx = j
                    break
                if signals[j] == -1:
                    exit_price = closes[j]
                    exit_reason = "SELL_SIGNAL"
                    exit_idx = j
                    break

            if exit_price is None:
                # max holding period tercapai, exit di close terakhir yang tersedia
                last_j = min(entry_idx + MAX_HOLD_DAYS, n - 1)
                exit_price = closes[last_j]
                exit_reason = "TIME_EXIT"
                exit_idx = last_j

            ret_pct = (exit_price - entry_price) / entry_price * 100
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

    # Equity curve kasar dari compounding return per trade
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
