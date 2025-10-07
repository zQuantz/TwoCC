"""
Data Manager - Central coordinator for all data operations.
"""

from typing import List, Optional
import pandas as pd
from datetime import datetime

from .data_downloader import DataDownloader
from .instrument_generator import InstrumentGenerator
from .feature_calculator import FeatureCalculator


class DataManager:
    """
    Central hub for downloading, transforming, storing, and accessing market data.

    The Data Manager coordinates three main components:
    1. Data Downloader - retrieves and caches market data
    2. Instrument Generator - creates synthetic instruments
    3. Feature Calculator - computes technical indicators
    """

    def __init__(self, db_path: str = "market_data.db", use_cache: bool = True):
        """
        Initialize DataManager.

        Args:
            db_path: Path to SQLite database for data persistence
        """
        self.downloader = DataDownloader(db_path=db_path, use_cache=use_cache)
        self.instrument_generator = InstrumentGenerator()
        self.feature_calculator = FeatureCalculator()
        self._data_cache: pd.DataFrame = None
        self._cache_valid: bool = False

    def get_data(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        interval: str,
        source: str,
        include_generated: bool = True,
        include_features: bool = True,
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """
        Get market data with optional synthetic instruments and features.

        Args:
            symbols: List of asset identifiers
            start_date: Beginning of data range
            end_date: End of data range
            interval: Data frequency (e.g., '1h', '4h', '1d')
            source: Data source to use (e.g., 'binance', 'yahoo')
            include_generated: Include synthetic instruments (default: True)
            include_features: Calculate features (default: True)

        Returns:
            DataFrame with market data, synthetic instruments, and features
        """
        # Download base market data
        data = self.downloader.get_data(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            source=source,
        )

        if data.empty:
            return data

        # Generate synthetic instruments
        if include_generated:
            generated_data = self.instrument_generator.generate_instruments(data)
            if not generated_data.empty:
                data = pd.concat([data, generated_data])

        # Calculate features
        if include_features:
            data = self.feature_calculator.calculate_features(data)

        # Update cache
        self._data_cache = data
        self._cache_valid = True

        return data

    def get_symbol_data(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """
        Get data for a specific symbol from cache.

        Args:
            symbol: Symbol to retrieve
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            DataFrame with data for the specified symbol
        """
        if not self._cache_valid or self._data_cache is None:
            raise ValueError("No data in cache. Call get_data() first.")

        data = self._data_cache[
            self._data_cache.index.get_level_values("symbol") == symbol
        ].copy()

        if start_date:
            data = data[
                data.index.get_level_values("timestamp") >= pd.Timestamp(start_date)
            ]

        if end_date:
            data = data[
                data.index.get_level_values("timestamp") <= pd.Timestamp(end_date)
            ]

        return data

    def get_available_symbols(self) -> List[str]:
        """
        Get list of all available symbols (base + generated).

        Returns:
            List of symbol names
        """
        if not self._cache_valid or self._data_cache is None:
            return []

        return self._data_cache.index.get_level_values("symbol").unique().tolist()

    def get_feature_names(self) -> List[str]:
        """
        Get list of all registered feature names.

        Returns:
            List of feature column names
        """
        return self.feature_calculator.get_feature_names()

    def clear_cache(self):
        """Clear the internal data cache."""
        self._data_cache = None
        self._cache_valid = False

    def export_to_csv(self, filepath: str):
        """
        Export cached data to CSV file.

        Args:
            filepath: Path to output CSV file
        """
        if not self._cache_valid or self._data_cache is None:
            raise ValueError("No data in cache. Call get_data() first.")

        self._data_cache.to_csv(filepath)

    def get_summary(self) -> dict:
        """
        Get summary statistics of cached data.

        Returns:
            Dictionary with summary information
        """
        if not self._cache_valid or self._data_cache is None:
            return {
                "status": "No data loaded",
                "symbols": 0,
                "records": 0,
                "date_range": None,
            }

        symbols = self._data_cache.index.get_level_values("symbol").unique()
        date_range = (self._data_cache.index.min(), self._data_cache.index.max())

        return {
            "status": "Data loaded",
            "symbols": len(symbols),
            "symbol_list": symbols.tolist(),
            "records": len(self._data_cache),
            "date_range": date_range,
            "features": self.feature_calculator.get_feature_names(),
        }

    def __repr__(self) -> str:
        """String representation of DataManager."""
        summary = self.get_summary()
        return (
            f"DataManager(symbols={summary['symbols']}, records={summary['records']})"
        )
