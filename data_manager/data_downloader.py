"""
Data Downloader implementations for various market data sources.
"""

from typing import List, Optional
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path
import logging

from .base import BaseDataDownloader

logger = logging.getLogger(__name__)


class DataDownloader:
    """
    Manages data downloading with SQLite persistence and intelligent caching.
    """

    def __init__(self, db_path: str = "market_data.db", use_cache: bool = True):
        """
        Initialize DataDownloader with database path.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.use_cache = use_cache
        
        self._init_database()
        self._downloaders = {}

    def _init_database(self):
        """Initialize SQLite database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_data (
                symbol TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                source TEXT NOT NULL,
                interval TEXT NOT NULL,
                PRIMARY KEY (symbol, timestamp, interval, source)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_symbol_timestamp
            ON market_data(symbol, timestamp)
        """)

        conn.commit()
        conn.close()

    def register_downloader(self, source: str, downloader: BaseDataDownloader):
        """
        Register a data downloader for a specific source.

        Args:
            source: Source identifier (e.g., 'binance', 'yahoo')
            downloader: Instance of a data downloader
        """
        self._downloaders[source] = downloader

    def get_data(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        interval: str,
        source: str,
    ) -> pd.DataFrame:
        """
        Get market data with intelligent caching.

        Args:
            symbols: List of asset identifiers
            start_date: Beginning of data range
            end_date: End of data range
            interval: Data frequency (e.g., '1h', '4h', '1d')
            source: Data source to use

        Returns:
            DataFrame with OHLCV data
        """
        if source not in self._downloaders:
            raise ValueError(f"No downloader registered for source: {source}")

        logger.info(f"Fetching data for {len(symbols)} symbols from {source} ({start_date} to {end_date}, interval: {interval})")
        all_data = []

        for idx, symbol in enumerate(symbols, 1):
            logger.info(f"Processing symbol {idx}/{len(symbols)}: {symbol}")

            # Check cache first
            cached_data = self._get_cached_data(symbol, start_date, end_date, interval, source)

            if self.use_cache and cached_data is not None and not cached_data.empty:
                logger.info(f"Found {len(cached_data)} cached records for {symbol}")

                # Identify missing data gaps
                missing_ranges = self._identify_missing_ranges(
                    cached_data, start_date, end_date, interval
                )

                if missing_ranges:
                    logger.info(f"Found {len(missing_ranges)} missing data range(s) for {symbol}")

                    # Download only missing data
                    for gap_idx, (gap_start, gap_end) in enumerate(missing_ranges, 1):
                        logger.info(f"Downloading missing range {gap_idx}/{len(missing_ranges)} for {symbol}: {gap_start} to {gap_end}")
                        new_data = self._downloaders[source].download(
                            [symbol], gap_start, gap_end, interval
                        )
                        if not new_data.empty:
                            logger.info(f"Downloaded {len(new_data)} new records for {symbol}")
                            self._save_to_cache(new_data, source, interval)
                            all_data.append(new_data)
                else:
                    logger.info(f"Cache is complete for {symbol}, no download needed")

                all_data.append(cached_data)
            else:
                logger.info(f"No cached data for {symbol}, downloading full range")

                # No cached data, download everything
                new_data = self._downloaders[source].download(
                    [symbol], start_date, end_date, interval
                )
                if not new_data.empty:
                    logger.info(f"Downloaded {len(new_data)} records for {symbol}")
                    self._save_to_cache(new_data, source, interval)
                    all_data.append(new_data)
                else:
                    logger.warning(f"No data received for {symbol}")

        if not all_data:
            logger.warning("No data retrieved for any symbols")
            return pd.DataFrame()

        # Combine and sort - data already has multi-index (timestamp, symbol)
        result = pd.concat(all_data, ignore_index=False)
        result = result.sort_index()
        result = result[~result.index.duplicated(keep='last')]

        logger.info(f"Successfully retrieved {len(result)} total records across all symbols")
        return result

    def _get_cached_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str,
        source: str
    ) -> Optional[pd.DataFrame]:
        """Retrieve cached data from SQLite database."""
        conn = sqlite3.connect(self.db_path)

        query = """
            SELECT timestamp, open, high, low, close, volume, symbol
            FROM market_data
            WHERE symbol = ?
                AND timestamp >= ?
                AND timestamp <= ?
                AND interval = ?
                AND source = ?
            ORDER BY timestamp
        """

        start_ts = int(start_date.timestamp())
        end_ts = int(end_date.timestamp())

        df = pd.read_sql_query(
            query,
            conn,
            params=(symbol, start_ts, end_ts, interval, source)
        )

        conn.close()

        if df.empty:
            return None

        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df = df.set_index(['timestamp', 'symbol'])

        return df

    def _identify_missing_ranges(
        self,
        cached_data: pd.DataFrame,
        start_date: datetime,
        end_date: datetime,
        interval: str
    ) -> List[tuple]:
        """Identify gaps in cached data."""
        missing_ranges = []

        if cached_data.empty:
            return [(start_date, end_date)]

        # Get timestamp level (first level of multi-index)
        timestamps = cached_data.index.get_level_values('timestamp')

        # Check if there's missing data before the first cached point
        first_cached = timestamps.min()
        if pd.Timestamp(start_date) < first_cached:
            missing_ranges.append((start_date, first_cached.to_pydatetime()))

        # Check if there's missing data after the last cached point
        last_cached = timestamps.max()
        if pd.Timestamp(end_date) > last_cached:
            missing_ranges.append((last_cached.to_pydatetime(), end_date))

        return missing_ranges

    def _save_to_cache(self, data: pd.DataFrame, source: str, interval: str):
        """Save downloaded data to SQLite database."""
        if data.empty:
            return

        logger.debug(f"Saving {len(data)} records to cache (source: {source}, interval: {interval})")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for idx, row in data.iterrows():
            # idx is now a tuple (timestamp, symbol) from multi-index
            timestamp_val, symbol_val = idx
            timestamp = int(timestamp_val.timestamp())

            cursor.execute("""
                INSERT OR REPLACE INTO market_data
                (symbol, timestamp, open, high, low, close, volume, source, interval)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol_val,
                timestamp,
                float(row['open']),
                float(row['high']),
                float(row['low']),
                float(row['close']),
                float(row['volume']),
                source,
                interval
            ))

        conn.commit()
        conn.close()
        logger.debug(f"Successfully cached {len(data)} records")


class BinanceDataDownloader(BaseDataDownloader):
    """Downloader for Binance cryptocurrency market data."""

    # Binance API limit is 1000 candles per request
    MAX_CANDLES_PER_REQUEST = 100

    def _get_interval_delta(self, interval: str) -> timedelta:
        """Convert Binance interval string to timedelta."""
        interval_map = {
            '1m': timedelta(minutes=1),
            '3m': timedelta(minutes=3),
            '5m': timedelta(minutes=5),
            '15m': timedelta(minutes=15),
            '30m': timedelta(minutes=30),
            '1h': timedelta(hours=1),
            '2h': timedelta(hours=2),
            '4h': timedelta(hours=4),
            '6h': timedelta(hours=6),
            '8h': timedelta(hours=8),
            '12h': timedelta(hours=12),
            '1d': timedelta(days=1),
            '3d': timedelta(days=3),
            '1w': timedelta(weeks=1),
            '1M': timedelta(days=30),  # Approximate
        }
        return interval_map.get(interval, timedelta(hours=1))

    def _create_batches(
        self,
        start_date: datetime,
        end_date: datetime,
        interval: str
    ) -> List[tuple]:
        """
        Create batches of date ranges to stay within API limits.

        Args:
            start_date: Beginning of data range
            end_date: End of data range
            interval: Binance interval string

        Returns:
            List of (start, end) datetime tuples
        """
        batches = []
        interval_delta = self._get_interval_delta(interval)
        batch_size = interval_delta * (self.MAX_CANDLES_PER_REQUEST - 1)

        current_start = start_date
        while current_start < end_date:
            current_end = min(current_start + batch_size, end_date)
            batches.append((current_start, current_end))
            current_start = current_end

        return batches

    def download(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        interval: str
    ) -> pd.DataFrame:
        """
        Download data from Binance API with automatic batching.

        Args:
            symbols: List of trading pairs (e.g., ['BTCUSDT', 'ETHUSDT'])
            start_date: Beginning of data range
            end_date: End of data range
            interval: Binance interval (e.g., '1h', '4h', '1d')

        Returns:
            DataFrame with OHLCV data
        """
        try:
            from binance.client import Client
        except ImportError:
            raise ImportError(
                "python-binance package required. Install with: pip install python-binance"
            )

        client = Client()
        all_data = []

        # Create batches to respect API limits
        batches = self._create_batches(start_date, end_date, interval)
        logger.info(f"Binance download: {len(batches)} batch(es) required for date range")

        for symbol in symbols:
            logger.info(f"Downloading {symbol} from Binance in {len(batches)} batch(es)")
            symbol_data = []

            for batch_idx, (batch_start, batch_end) in enumerate(batches, 1):
                try:
                    logger.debug(f"Batch {batch_idx}/{len(batches)} for {symbol}: {batch_start} to {batch_end}")

                    klines = client.get_historical_klines(
                        symbol,
                        interval,
                        batch_start.strftime("%d %b %Y %H:%M:%S"),
                        batch_end.strftime("%d %b %Y %H:%M:%S")
                    )

                    if not klines:
                        logger.warning(f"No data returned for {symbol} batch {batch_idx}/{len(batches)}")
                        continue

                    df = pd.DataFrame(klines, columns=[
                        'timestamp', 'open', 'high', 'low', 'close', 'volume',
                        'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                        'taker_buy_quote', 'ignore'
                    ])

                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df['symbol'] = symbol
                    df = df.set_index(['timestamp', 'symbol'])

                    df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)

                    symbol_data.append(df)
                    logger.info(f"Successfully downloaded {len(df)} candles for {symbol} (batch {batch_idx}/{len(batches)})")

                except Exception as e:
                    logger.error(f"Error downloading {symbol} from Binance (batch {batch_idx}/{len(batches)} - {batch_start} to {batch_end}): {e}")
                    continue

            # Combine all batches for this symbol
            if symbol_data:
                combined_symbol_df = pd.concat(symbol_data)
                combined_symbol_df = combined_symbol_df[~combined_symbol_df.index.duplicated(keep='last')]
                all_data.append(combined_symbol_df)
                logger.info(f"Total records for {symbol}: {len(combined_symbol_df)} (after deduplication)")
            else:
                logger.warning(f"No data collected for {symbol}")

        if not all_data:
            logger.warning("Binance download: No data collected for any symbols")
            return pd.DataFrame()

        result = pd.concat(all_data)
        logger.info(f"Binance download complete: {len(result)} total records across {len(symbols)} symbol(s)")
        return result


class YahooFinanceDataDownloader(BaseDataDownloader):
    """Downloader for Yahoo Finance market data."""

    def download(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        interval: str
    ) -> pd.DataFrame:
        """
        Download data from Yahoo Finance.

        Args:
            symbols: List of ticker symbols (e.g., ['AAPL', 'MSFT'])
            start_date: Beginning of data range
            end_date: End of data range
            interval: Yahoo Finance interval (e.g., '1h', '1d')

        Returns:
            DataFrame with OHLCV data
        """
        try:
            import yfinance as yf
        except ImportError:
            raise ImportError(
                "yfinance package required. Install with: pip install yfinance"
            )

        logger.info(f"Yahoo Finance download: {len(symbols)} symbol(s) from {start_date} to {end_date}")
        all_data = []

        for idx, symbol in enumerate(symbols, 1):
            try:
                logger.info(f"Downloading {symbol} from Yahoo Finance ({idx}/{len(symbols)})")

                ticker = yf.Ticker(symbol)
                df = ticker.history(
                    start=start_date,
                    end=end_date,
                    interval=interval
                )

                if df.empty:
                    logger.warning(f"No data returned for {symbol}")
                    continue

                df.columns = df.columns.str.lower()
                df['symbol'] = symbol
                # Reset index to get timestamp as column, then set multi-index
                df = df.reset_index()
                df = df.rename(columns={'date': 'timestamp'})
                df = df.set_index(['timestamp', 'symbol'])
                df = df[['open', 'high', 'low', 'close', 'volume']]

                all_data.append(df)
                logger.info(f"Successfully downloaded {len(df)} records for {symbol}")

            except Exception as e:
                logger.error(f"Error downloading {symbol} from Yahoo Finance: {e}")
                continue

        if not all_data:
            logger.warning("Yahoo Finance download: No data collected for any symbols")
            return pd.DataFrame()

        result = pd.concat(all_data)
        logger.info(f"Yahoo Finance download complete: {len(result)} total records across {len(symbols)} symbol(s)")
        return result
