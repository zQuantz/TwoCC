"""
Two Candle Strategy - Simple momentum-based trading strategy.

Generates BUY signals when:
- Current candle's close is higher than previous candle's close
- Current candle's volume is higher than previous candle's volume
- Both conditions must be met (confirmation)

Generates SELL signals when:
- Current position is open
- Current candle's close is lower than previous candle's close
"""

from typing import List
from datetime import datetime
import pandas as pd

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from trading_strategy.base import TradingStrategy
from book.trade import Trade, TradeAction
from data_manager.data_manager import DataManager


class TwoCandleStrategy(TradingStrategy):
    """
    Simple two-candle comparison strategy.

    Looks at the current candle and the previous candle to make trading decisions.
    This is a basic momentum strategy that buys on strength and sells on weakness.
    """

    def __init__(
        self,
        data_manager: DataManager,
        strategy_id: str = "two_candle_v1",
        strategy_name: str = "Two Candle Strategy",
        position_size: float = 1.0,
        min_volume: float = 0.0
    ):
        """
        Initialize the Two Candle Strategy.

        Args:
            data_manager: DataManager instance for accessing market data
            strategy_id: Unique identifier for this strategy
            strategy_name: Human-readable name
            position_size: Default position size for trades
            min_volume: Minimum volume threshold to consider trades
        """
        super().__init__(data_manager, strategy_id, strategy_name)
        self.position_size = position_size
        self.min_volume = min_volume

    def get_suggested_trades(self, time_period: datetime, symbol: str) -> List[Trade]:
        """
        Generate trade suggestions based on two-candle analysis.

        Args:
            time_period: Current time point for analysis
            symbol: The ticker symbol to analyze

        Returns:
            List of suggested Trade objects (empty if no signal)
        """
        # Get historical data up to (but not including) current time_period
        # We need at least 2 candles to compare
        data = self.get_available_data(symbol, end_date=time_period, lookback_periods=2)

        # Need at least 2 candles to make a comparison
        if len(data) < 2:
            return []

        # Get the last two candles
        previous_candle = data.iloc[-2]
        current_candle = data.iloc[-1]

        # Check minimum volume requirement
        if current_candle['volume'] < self.min_volume:
            return []

        # Analyze for BUY signal
        buy_signal = self._check_buy_signal(previous_candle, current_candle)

        # Analyze for SELL signal
        sell_signal = self._check_sell_signal(previous_candle, current_candle)

        # Generate trade suggestions
        trades = []

        if buy_signal:
            signal_strength = self._calculate_signal_strength(previous_candle, current_candle)

            trade = Trade(
                symbol=symbol,
                action=TradeAction.BUY,
                quantity=self.position_size,
                timestamp=time_period,
                price=current_candle['close'],  # Use current close as expected price
                strategy_id=self.strategy_id,
                strategy_name=self.strategy_name,
                signal_strength=signal_strength,
                notes=f"Two candle BUY: Close {previous_candle['close']:.2f} -> {current_candle['close']:.2f}"
            )
            trades.append(trade)

        elif sell_signal:
            signal_strength = self._calculate_signal_strength(previous_candle, current_candle, is_sell=True)

            trade = Trade(
                symbol=symbol,
                action=TradeAction.SELL,
                quantity=self.position_size,
                timestamp=time_period,
                price=current_candle['close'],
                strategy_id=self.strategy_id,
                strategy_name=self.strategy_name,
                signal_strength=signal_strength,
                notes=f"Two candle SELL: Close {previous_candle['close']:.2f} -> {current_candle['close']:.2f}"
            )
            trades.append(trade)

        return trades

    def _check_buy_signal(self, previous: pd.Series, current: pd.Series) -> bool:
        """
        Check if conditions for a BUY signal are met.

        Args:
            previous: Previous candle data
            current: Current candle data

        Returns:
            True if BUY signal detected
        """
        # Price momentum: current close > previous close
        price_up = current['close'] > previous['close']

        # Volume confirmation: current volume > previous volume
        volume_up = current['volume'] > previous['volume']

        return price_up and volume_up

    def _check_sell_signal(self, previous: pd.Series, current: pd.Series) -> bool:
        """
        Check if conditions for a SELL signal are met.

        Args:
            previous: Previous candle data
            current: Current candle data

        Returns:
            True if SELL signal detected
        """
        # Price weakness: current close < previous close
        price_down = current['close'] < previous['close']

        return price_down

    def _calculate_signal_strength(
        self,
        previous: pd.Series,
        current: pd.Series,
        is_sell: bool = False
    ) -> float:
        """
        Calculate signal strength based on magnitude of price and volume changes.

        Args:
            previous: Previous candle data
            current: Current candle data
            is_sell: Whether this is a sell signal

        Returns:
            Signal strength between 0 and 1
        """
        # Calculate percentage change in price
        price_change_pct = abs((current['close'] - previous['close']) / previous['close'])

        # Calculate percentage change in volume
        volume_change_pct = abs((current['volume'] - previous['volume']) / previous['volume']) if previous['volume'] > 0 else 0

        # Combine both factors (weighted average)
        # Price change is more important (70%), volume is confirmation (30%)
        signal_strength = (0.7 * min(price_change_pct * 10, 1.0)) + (0.3 * min(volume_change_pct, 1.0))

        # Normalize to 0-1 range
        return min(max(signal_strength, 0.0), 1.0)

    def __repr__(self) -> str:
        """String representation of the strategy."""
        return (f"TwoCandleStrategy(id={self.strategy_id}, "
                f"position_size={self.position_size}, min_volume={self.min_volume})")
