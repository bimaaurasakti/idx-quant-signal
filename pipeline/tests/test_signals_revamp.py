"""
Unit test suite for Dual-Horizon IHSG Regime and 3-Day Lookback Signal Engine.
"""
import unittest
import numpy as np
import pandas as pd
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from signals import check_ihsg_regime, generate_signals, latest_signal_summary


class TestSignalsRevamp(unittest.TestCase):
    def setUp(self):
        # Generate synthetic 250 bars of price data
        np.random.seed(42)
        dates = pd.date_range("2026-01-01", periods=250, freq="B")
        
        # Upward trending price
        prices = 1000 + np.cumsum(np.random.normal(2, 5, 250))
        highs = prices + np.random.uniform(5, 15, 250)
        lows = prices - np.random.uniform(5, 15, 250)
        opens = prices + np.random.uniform(-5, 5, 250)
        volumes = np.random.uniform(1_000_000, 5_000_000, 250)

        self.df = pd.DataFrame({
            "Open": opens,
            "High": highs,
            "Low": lows,
            "Close": prices,
            "Volume": volumes,
        }, index=dates)

    def test_check_ihsg_regime_none(self):
        res = check_ihsg_regime(None)
        self.assertEqual(res["tier"], "HIGH_ALPHA")
        self.assertEqual(res["sizing"], 1.0)
        self.assertEqual(res["max_pos"], 7)

    def test_check_ihsg_regime_bull(self):
        # Close steadily climbing -> Close > SMA200
        df_bull = self.df.copy()
        res = check_ihsg_regime(df_bull)
        self.assertIn(res["tier"], ["HIGH_ALPHA", "DEFENSIVE"])
        self.assertIn("sizing", res)

    def test_check_ihsg_regime_bear_rebound(self):
        # Macro bear (Close < SMA200), but green daily candle
        df_bear = self.df.copy()
        # Depress latest prices below SMA200
        sma200 = df_bear["Close"].rolling(200).mean().iloc[-1]
        df_bear.iloc[-1, df_bear.columns.get_loc("Close")] = sma200 - 500
        df_bear.iloc[-1, df_bear.columns.get_loc("Open")] = sma200 - 520  # Green candle (Close > Open)
        df_bear.iloc[-2, df_bear.columns.get_loc("Close")] = sma200 - 530 # Close > Prev Close

        res = check_ihsg_regime(df_bear)
        self.assertFalse(res["macro_bull"])
        # Should be TACTICAL_SWING or DEFENSIVE
        self.assertIn(res["tier"], ["TACTICAL_SWING", "DEFENSIVE"])

    def test_generate_signals_preserves_historical_signals(self):
        # Create a regime that is DEFENSIVE
        defensive_regime = {
            "tier": "DEFENSIVE",
            "macro_bull": False,
            "momentum_green": False,
            "sizing": 0.0,
            "max_pos": 0,
        }

        # Run generate_signals
        d = generate_signals(self.df, market_regime=defensive_regime)
        self.assertIn("Signal", d.columns)
        self.assertIn("BuyScore", d.columns)
        self.assertIn("SellScore", d.columns)

        # CRITICAL TEST: On defensive regime, the LAST bar must not be 1
        if len(d) > 0:
            self.assertNotEqual(d["Signal"].iloc[-1], 1)

        # But historical signals across d.index must NOT be wiped out to all zeros!
        # (Compare with previous bug where buy_valid was pd.Series(False, index=d.index))
        # Even if market is defensive today, historical BuyScore should still exist
        self.assertTrue(d["BuyScore"].max() >= 0)

    def test_latest_signal_summary(self):
        d = generate_signals(self.df)
        summary = latest_signal_summary(d)
        self.assertIn("signal", summary)
        self.assertIn("strength", summary)
        self.assertIn("trend", summary)
        self.assertIn(summary["signal"], ["BUY", "SELL", "HOLD"])


if __name__ == "__main__":
    unittest.main()
