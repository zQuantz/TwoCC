"""
Instrument Generator for creating synthetic instruments from market data.
"""

from typing import List, Callable, Dict
import pandas as pd
import numpy as np

from .base import BaseInstrumentGenerator


class InstrumentGenerator:
    """
    Manages the generation of synthetic instruments from existing market data.
    """

    def __init__(self):
        """Initialize InstrumentGenerator."""
        self._generators = {}

    def register_generator(self, generator: BaseInstrumentGenerator):
        """
        Register an instrument generator.

        Args:
            generator: Instance of an instrument generator
        """
        symbol = generator.get_symbol()
        self._generators[symbol] = generator

    def generate_instruments(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate all registered synthetic instruments.

        Args:
            data: DataFrame with multi-index (timestamp, symbol)

        Returns:
            DataFrame containing all generated instruments with multi-index
        """
        generated_data = []

        for symbol, generator in self._generators.items():
            required_symbols = generator.get_required_symbols()

            # Check if all required symbols are available
            available_symbols = data.index.get_level_values('symbol').unique()
            if not all(sym in available_symbols for sym in required_symbols):
                print(f"Warning: Cannot generate {symbol}. Missing required symbols.")
                continue

            try:
                synthetic_df = generator.generate(data)
                generated_data.append(synthetic_df)
            except Exception as e:
                print(f"Error generating {symbol}: {e}")
                continue

        if not generated_data:
            return pd.DataFrame()

        return pd.concat(generated_data).sort_index()

    def get_registered_symbols(self) -> List[str]:
        """Return list of all registered synthetic instrument symbols."""
        return list(self._generators.keys())


class SpreadGenerator(BaseInstrumentGenerator):
    """
    Generates a spread instrument (difference between two instruments).
    Example: BTC - ETH
    """

    def __init__(self, symbol1: str, symbol2: str, new_symbol: str):
        """
        Initialize SpreadGenerator.

        Args:
            symbol1: First instrument symbol
            symbol2: Second instrument symbol (to subtract)
            new_symbol: Symbol for the generated spread instrument
        """
        self.symbol1 = symbol1
        self.symbol2 = symbol2
        self.new_symbol = new_symbol

    def generate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate spread instrument."""
        # Extract data for each symbol using cross-section
        data1 = data.xs(self.symbol1, level='symbol').copy()
        data2 = data.xs(self.symbol2, level='symbol').copy()

        # Calculate spread for OHLC (timestamps already aligned by index)
        result = pd.DataFrame(index=data1.index)
        result['open'] = data1['open'] - data2['open']
        result['high'] = data1['high'] - data2['high']
        result['low'] = data1['low'] - data2['low']
        result['close'] = data1['close'] - data2['close']
        result['volume'] = data1['volume']  # Use volume from first instrument

        # Add symbol and create multi-index
        result['symbol'] = self.new_symbol
        result = result.reset_index()
        result = result.set_index(['timestamp', 'symbol'])

        return result

    def get_symbol(self) -> str:
        """Return the generated symbol."""
        return self.new_symbol

    def get_required_symbols(self) -> List[str]:
        """Return required symbols."""
        return [self.symbol1, self.symbol2]


class RatioGenerator(BaseInstrumentGenerator):
    """
    Generates a ratio instrument (division of two instruments).
    Example: BTC / ETH
    """

    def __init__(self, symbol1: str, symbol2: str, new_symbol: str):
        """
        Initialize RatioGenerator.

        Args:
            symbol1: Numerator instrument symbol
            symbol2: Denominator instrument symbol
            new_symbol: Symbol for the generated ratio instrument
        """
        self.symbol1 = symbol1
        self.symbol2 = symbol2
        self.new_symbol = new_symbol

    def generate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate ratio instrument."""
        # Extract data for each symbol using cross-section
        data1 = data.xs(self.symbol1, level='symbol').copy()
        data2 = data.xs(self.symbol2, level='symbol').copy()

        # Calculate ratio for OHLC (timestamps already aligned by index)
        result = pd.DataFrame(index=data1.index)
        result['open'] = data1['open'] / data2['open']
        result['high'] = data1['high'] / data2['high']
        result['low'] = data1['low'] / data2['low']
        result['close'] = data1['close'] / data2['close']
        result['volume'] = data1['volume']  # Use volume from first instrument

        # Add symbol and create multi-index
        result['symbol'] = self.new_symbol
        result = result.reset_index()
        result = result.set_index(['timestamp', 'symbol'])

        return result

    def get_symbol(self) -> str:
        """Return the generated symbol."""
        return self.new_symbol

    def get_required_symbols(self) -> List[str]:
        """Return required symbols."""
        return [self.symbol1, self.symbol2]


class WeightedCombinationGenerator(BaseInstrumentGenerator):
    """
    Generates a weighted combination of multiple instruments.
    Example: 0.5 * BTC + 0.3 * ETH - 0.2 * SOL
    """

    def __init__(self, weights: Dict[str, float], new_symbol: str):
        """
        Initialize WeightedCombinationGenerator.

        Args:
            weights: Dictionary mapping symbols to their weights
                    Example: {'BTC': 0.5, 'ETH': 0.3, 'SOL': -0.2}
            new_symbol: Symbol for the generated instrument
        """
        self.weights = weights
        self.new_symbol = new_symbol

    def generate(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate weighted combination instrument."""
        result_data = None

        for symbol, weight in self.weights.items():
            # Extract data for this symbol using cross-section
            symbol_data = data.xs(symbol, level='symbol').copy()

            if result_data is None:
                result_data = pd.DataFrame(index=symbol_data.index)
                result_data['open'] = symbol_data['open'] * weight
                result_data['high'] = symbol_data['high'] * weight
                result_data['low'] = symbol_data['low'] * weight
                result_data['close'] = symbol_data['close'] * weight
                result_data['volume'] = symbol_data['volume']
            else:
                result_data['open'] += symbol_data['open'] * weight
                result_data['high'] += symbol_data['high'] * weight
                result_data['low'] += symbol_data['low'] * weight
                result_data['close'] += symbol_data['close'] * weight

        # Add symbol and create multi-index
        result_data['symbol'] = self.new_symbol
        result_data = result_data.reset_index()
        result_data = result_data.set_index(['timestamp', 'symbol'])

        return result_data

    def get_symbol(self) -> str:
        """Return the generated symbol."""
        return self.new_symbol

    def get_required_symbols(self) -> List[str]:
        """Return required symbols."""
        return list(self.weights.keys())
