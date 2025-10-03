"""
Base classes and abstract interfaces for Data Manager components.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import pandas as pd
from datetime import datetime


class BaseDataDownloader(ABC):
    """Abstract base class for data downloaders."""

    @abstractmethod
    def download(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        interval: str
    ) -> pd.DataFrame:
        """
        Download market data for specified symbols and date range.

        Args:
            symbols: List of asset identifiers
            start_date: Beginning of data range
            end_date: End of data range
            interval: Data frequency (e.g., '1h', '4h', '1d')

        Returns:
            DataFrame with OHLCV data
        """
        pass


class BaseInstrumentGenerator(ABC):
    """Abstract base class for instrument generators."""

    @abstractmethod
    def generate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate synthetic instrument from existing market data.

        Args:
            data: DataFrame containing market data for required instruments

        Returns:
            DataFrame with generated instrument data
        """
        pass

    @abstractmethod
    def get_symbol(self) -> str:
        """Return the symbol identifier for the generated instrument."""
        pass

    @abstractmethod
    def get_required_symbols(self) -> List[str]:
        """Return list of symbols required for generation."""
        pass


class BaseFeatureCalculator(ABC):
    """Abstract base class for feature calculators."""

    @abstractmethod
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical features and add them to the data.

        Args:
            data: DataFrame containing market data for a single symbol

        Returns:
            DataFrame with added feature columns
        """
        pass

    @abstractmethod
    def get_feature_names(self) -> List[str]:
        """Return list of feature column names added by this calculator."""
        pass
