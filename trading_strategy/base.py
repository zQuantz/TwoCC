"""
Base Trading Strategy - Abstract interface for all trading strategies.

Defines the contract that all trading strategies must implement to ensure
compatibility with the backtesting and live trading systems.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from book.trade import Trade
from data_manager.data_manager import DataManager


class TradingStrategy(ABC):
    """
    Abstract base class for all trading strategies.

    All strategies must implement the get_suggested_trades method which
    analyzes market data and returns trade suggestions.

    Key Principles:
    - Strategies are signal generators that propose trades
    - Must respect temporal boundaries (no look-ahead bias)
    - Should be stateless where possible
    - Work identically in backtesting and live modes
    """

    def __init__(self, data_manager: DataManager, strategy_id: str, strategy_name: Optional[str] = None):
        """
        Initialize the trading strategy.

        Args:
            data_manager: DataManager instance for accessing market data
            strategy_id: Unique identifier for this strategy instance
            strategy_name: Human-readable name for the strategy
        """
        self.data_manager = data_manager
        self.strategy_id = strategy_id
        self.strategy_name = strategy_name or self.__class__.__name__

    @abstractmethod
    def get_suggested_trades(self, time_period: datetime, symbol: str) -> List[Trade]:
        """
        Analyze market conditions and generate trade suggestions.

        This is the core method that all strategies must implement.

        CRITICAL: Must only use data where timestamp <= time_period to avoid look-ahead bias.

        Args:
            time_period: Current time point for analysis (only data up to this point should be used)
            symbol: The ticker symbol to analyze

        Returns:
            List of suggested Trade objects (empty list if no signals)
            Each Trade should include:
                - symbol: The symbol to trade
                - action: BUY, SELL, CLOSE, etc.
                - quantity: Number of units
                - timestamp: Same as time_period
                - price: Expected execution price
                - strategy_id: This strategy's ID
                - strategy_name: This strategy's name
                - signal_strength: Optional confidence level (0-1)
                - notes: Optional reasoning for the trade
        """
        pass

    def get_available_data(self, symbol: str, end_date: datetime, lookback_periods: Optional[int] = None):
        """
        Helper method to get historical data respecting temporal boundaries.

        Ensures no look-ahead bias by only returning data up to end_date.

        Args:
            symbol: Symbol to retrieve
            end_date: Maximum timestamp (exclusive upper bound)
            lookback_periods: Optional number of periods to look back

        Returns:
            DataFrame with historical data up to (but not including) end_date
        """
        data = self.data_manager.get_symbol_data(symbol, end_date=end_date)

        # Ensure we don't include data from the future
        data = data[data.index.get_level_values('timestamp') < end_date]

        # Limit to lookback periods if specified
        if lookback_periods is not None and len(data) > lookback_periods:
            data = data.tail(lookback_periods)

        return data

    def __repr__(self) -> str:
        """String representation of the strategy."""
        return f"{self.__class__.__name__}(id={self.strategy_id}, name={self.strategy_name})"
