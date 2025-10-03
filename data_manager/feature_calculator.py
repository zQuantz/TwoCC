"""
Feature Calculator for computing technical indicators and derived features.
"""

from typing import List
import pandas as pd
import numpy as np

from .base import BaseFeatureCalculator


class FeatureCalculator:
    """
    Manages the calculation of technical features for market data.
    Features are automatically calculated for all symbols.
    """

    def __init__(self):
        """Initialize FeatureCalculator."""
        self._calculators = []

    def register_calculator(self, calculator: BaseFeatureCalculator):
        """
        Register a feature calculator that will be applied to all symbols.

        Args:
            calculator: Instance of a feature calculator
        """
        self._calculators.append(calculator)

    def calculate_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all registered features for all symbols in the data.

        Args:
            data: DataFrame with multi-index (timestamp, symbol)

        Returns:
            DataFrame with added feature columns
        """
        if data.empty:
            return data

        result = data.copy()

        # Get unique symbols from the multi-index
        symbols = result.index.get_level_values('symbol').unique()

        # Process each symbol separately
        symbol_dfs = []
        for symbol in symbols:
            # Extract data for this symbol using xs (cross-section)
            symbol_data = result.xs(symbol, level='symbol').copy()

            for calculator in self._calculators:
                try:
                    symbol_data = calculator.calculate(symbol_data)
                except Exception as e:
                    print(f"Error calculating features for {symbol}: {e}")
                    continue

            # Add symbol back as index level
            symbol_data['symbol'] = symbol
            symbol_data = symbol_data.reset_index()
            symbol_data = symbol_data.set_index(['timestamp', 'symbol'])
            symbol_dfs.append(symbol_data)

        # Combine all symbols back together
        result = pd.concat(symbol_dfs).sort_index()

        return result

    def get_feature_names(self) -> List[str]:
        """Return list of all registered feature names."""
        features = []
        for calc in self._calculators:
            features.extend(calc.get_feature_names())
        return features


class SMACalculator(BaseFeatureCalculator):
    """Simple Moving Average calculator."""

    def __init__(self, periods: List[int], column: str = 'close'):
        """
        Initialize SMACalculator.

        Args:
            periods: List of periods for SMA (e.g., [20, 50, 200])
            column: Column to calculate SMA on (default: 'close')
        """
        self.periods = periods
        self.column = column

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate Simple Moving Averages."""
        result = data.copy()

        for period in self.periods:
            feature_name = f'sma_{period}'
            result[feature_name] = result[self.column].rolling(window=period).mean()

        return result

    def get_feature_names(self) -> List[str]:
        """Return list of feature names."""
        return [f'sma_{period}' for period in self.periods]


class EMACalculator(BaseFeatureCalculator):
    """Exponential Moving Average calculator."""

    def __init__(self, periods: List[int], column: str = 'close'):
        """
        Initialize EMACalculator.

        Args:
            periods: List of periods for EMA (e.g., [12, 26])
            column: Column to calculate EMA on (default: 'close')
        """
        self.periods = periods
        self.column = column

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate Exponential Moving Averages."""
        result = data.copy()

        for period in self.periods:
            feature_name = f'ema_{period}'
            result[feature_name] = result[self.column].ewm(span=period, adjust=False).mean()

        return result

    def get_feature_names(self) -> List[str]:
        """Return list of feature names."""
        return [f'ema_{period}' for period in self.periods]


class RSICalculator(BaseFeatureCalculator):
    """Relative Strength Index calculator."""

    def __init__(self, period: int = 14, column: str = 'close'):
        """
        Initialize RSICalculator.

        Args:
            period: Period for RSI calculation (default: 14)
            column: Column to calculate RSI on (default: 'close')
        """
        self.period = period
        self.column = column

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate Relative Strength Index."""
        result = data.copy()

        delta = result[self.column].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()

        rs = gain / loss
        result[f'rsi_{self.period}'] = 100 - (100 / (1 + rs))

        return result

    def get_feature_names(self) -> List[str]:
        """Return list of feature names."""
        return [f'rsi_{self.period}']


class BollingerBandsCalculator(BaseFeatureCalculator):
    """Bollinger Bands calculator."""

    def __init__(self, period: int = 20, std_dev: float = 2.0, column: str = 'close'):
        """
        Initialize BollingerBandsCalculator.

        Args:
            period: Period for moving average (default: 20)
            std_dev: Number of standard deviations (default: 2.0)
            column: Column to calculate on (default: 'close')
        """
        self.period = period
        self.std_dev = std_dev
        self.column = column

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate Bollinger Bands."""
        result = data.copy()

        sma = result[self.column].rolling(window=self.period).mean()
        std = result[self.column].rolling(window=self.period).std()

        result[f'bb_middle_{self.period}'] = sma
        result[f'bb_upper_{self.period}'] = sma + (std * self.std_dev)
        result[f'bb_lower_{self.period}'] = sma - (std * self.std_dev)
        result[f'bb_width_{self.period}'] = (result[f'bb_upper_{self.period}'] -
                                              result[f'bb_lower_{self.period}']) / sma

        return result

    def get_feature_names(self) -> List[str]:
        """Return list of feature names."""
        return [
            f'bb_middle_{self.period}',
            f'bb_upper_{self.period}',
            f'bb_lower_{self.period}',
            f'bb_width_{self.period}'
        ]


class MACDCalculator(BaseFeatureCalculator):
    """MACD (Moving Average Convergence Divergence) calculator."""

    def __init__(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        column: str = 'close'
    ):
        """
        Initialize MACDCalculator.

        Args:
            fast_period: Fast EMA period (default: 12)
            slow_period: Slow EMA period (default: 26)
            signal_period: Signal line period (default: 9)
            column: Column to calculate on (default: 'close')
        """
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.column = column

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate MACD."""
        result = data.copy()

        ema_fast = result[self.column].ewm(span=self.fast_period, adjust=False).mean()
        ema_slow = result[self.column].ewm(span=self.slow_period, adjust=False).mean()

        result['macd'] = ema_fast - ema_slow
        result['macd_signal'] = result['macd'].ewm(span=self.signal_period, adjust=False).mean()
        result['macd_histogram'] = result['macd'] - result['macd_signal']

        return result

    def get_feature_names(self) -> List[str]:
        """Return list of feature names."""
        return ['macd', 'macd_signal', 'macd_histogram']


class ATRCalculator(BaseFeatureCalculator):
    """Average True Range calculator."""

    def __init__(self, period: int = 14):
        """
        Initialize ATRCalculator.

        Args:
            period: Period for ATR calculation (default: 14)
        """
        self.period = period

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate Average True Range."""
        result = data.copy()

        high_low = result['high'] - result['low']
        high_close = np.abs(result['high'] - result['close'].shift())
        low_close = np.abs(result['low'] - result['close'].shift())

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        result[f'atr_{self.period}'] = true_range.rolling(window=self.period).mean()

        return result

    def get_feature_names(self) -> List[str]:
        """Return list of feature names."""
        return [f'atr_{self.period}']
