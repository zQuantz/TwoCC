"""
Example usage of the Data Manager component.

This script demonstrates how to:
1. Initialize the Data Manager
2. Register data downloaders
3. Download and cache market data
4. Generate synthetic instruments
5. Calculate technical features
6. Access and export data
"""

from datetime import datetime, timedelta
from data_manager import (
    DataManager,
    BinanceDataDownloader,
    YahooFinanceDataDownloader,
    SpreadGenerator,
    RatioGenerator,
    WeightedCombinationGenerator,
    SMACalculator,
    EMACalculator,
    RSICalculator,
    BollingerBandsCalculator,
    MACDCalculator,
    ATRCalculator
)


def example_binance_basic():
    """Basic example: Download Bitcoin data from Binance."""
    print("=" * 60)
    print("Example 1: Basic Binance Data Download")
    print("=" * 60)

    # Initialize Data Manager
    dm = DataManager(db_path="crypto_data.db")

    # Register Binance downloader
    dm.downloader.register_downloader('binance', BinanceDataDownloader())

    # Download data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    data = dm.get_data(
        symbols=['BTCUSDT'],
        start_date=start_date,
        end_date=end_date,
        interval='1d',
        source='binance',
        include_generated=False,
        include_features=False
    )

    print(f"\nDownloaded {len(data)} records for BTCUSDT")
    print("\nFirst 5 rows:")
    print(data.head())
    print("\nSummary:")
    print(dm.get_summary())


def example_multiple_symbols_with_features():
    """Example: Download multiple cryptocurrencies and calculate features."""
    print("\n" + "=" * 60)
    print("Example 2: Multiple Symbols with Technical Features")
    print("=" * 60)

    dm = DataManager(db_path="crypto_data.db")
    dm.downloader.register_downloader('binance', BinanceDataDownloader())

    # Register feature calculators for BTC
    dm.feature_calculator.register_calculator(
        SMACalculator(symbol='BTCUSDT', periods=[20, 50, 200])
    )
    dm.feature_calculator.register_calculator(
        EMACalculator(symbol='BTCUSDT', periods=[12, 26])
    )
    dm.feature_calculator.register_calculator(
        RSICalculator(symbol='BTCUSDT', period=14)
    )
    dm.feature_calculator.register_calculator(
        MACDCalculator(symbol='BTCUSDT')
    )

    # Download data with features
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)

    data = dm.get_data(
        symbols=['BTCUSDT', 'ETHUSDT'],
        start_date=start_date,
        end_date=end_date,
        interval='1d',
        source='binance'
    )

    print(f"\nTotal records: {len(data)}")
    print(f"Available symbols: {dm.get_available_symbols()}")

    # Get BTC data with features
    btc_data = dm.get_symbol_data('BTCUSDT')
    print(f"\nBTC features: {dm.get_features_for_symbol('BTCUSDT')}")
    print("\nBTC data with features (last 5 rows):")
    print(btc_data.tail())


def example_synthetic_instruments():
    """Example: Create synthetic instruments from market data."""
    print("\n" + "=" * 60)
    print("Example 3: Synthetic Instruments")
    print("=" * 60)

    dm = DataManager(db_path="crypto_data.db")
    dm.downloader.register_downloader('binance', BinanceDataDownloader())

    # Register synthetic instrument generators
    dm.instrument_generator.register_generator(
        SpreadGenerator('BTCUSDT', 'ETHUSDT', 'BTC_ETH_SPREAD')
    )
    dm.instrument_generator.register_generator(
        RatioGenerator('BTCUSDT', 'ETHUSDT', 'BTC_ETH_RATIO')
    )
    dm.instrument_generator.register_generator(
        WeightedCombinationGenerator(
            weights={'BTCUSDT': 0.6, 'ETHUSDT': 0.4},
            new_symbol='CRYPTO_INDEX'
        )
    )

    # Register features for synthetic instruments
    dm.feature_calculator.register_calculator(
        SMACalculator(symbol='BTC_ETH_RATIO', periods=[20, 50])
    )
    dm.feature_calculator.register_calculator(
        RSICalculator(symbol='BTC_ETH_RATIO', period=14)
    )

    # Download data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)

    data = dm.get_data(
        symbols=['BTCUSDT', 'ETHUSDT'],
        start_date=start_date,
        end_date=end_date,
        interval='1d',
        source='binance'
    )

    print(f"\nAvailable symbols: {dm.get_available_symbols()}")

    # Get synthetic instrument data
    ratio_data = dm.get_symbol_data('BTC_ETH_RATIO')
    print("\nBTC/ETH Ratio (last 5 rows):")
    print(ratio_data.tail())

    spread_data = dm.get_symbol_data('BTC_ETH_SPREAD')
    print("\nBTC-ETH Spread (last 5 rows):")
    print(spread_data[['open', 'high', 'low', 'close']].tail())


def example_yahoo_finance():
    """Example: Download traditional financial instruments from Yahoo Finance."""
    print("\n" + "=" * 60)
    print("Example 4: Yahoo Finance Data")
    print("=" * 60)

    dm = DataManager(db_path="stocks_data.db")
    dm.downloader.register_downloader('yahoo', YahooFinanceDataDownloader())

    # Register features
    dm.feature_calculator.register_calculator(
        SMACalculator(symbol='AAPL', periods=[50, 200])
    )
    dm.feature_calculator.register_calculator(
        BollingerBandsCalculator(symbol='AAPL', period=20)
    )
    dm.feature_calculator.register_calculator(
        ATRCalculator(symbol='AAPL', period=14)
    )

    # Download data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    data = dm.get_data(
        symbols=['AAPL', 'MSFT', 'GOOGL'],
        start_date=start_date,
        end_date=end_date,
        interval='1d',
        source='yahoo'
    )

    print(f"\nDownloaded data for: {dm.get_available_symbols()}")

    # Get Apple data with features
    aapl_data = dm.get_symbol_data('AAPL')
    print(f"\nAAPL features: {dm.get_features_for_symbol('AAPL')}")
    print("\nAAPL with Bollinger Bands (last 5 rows):")
    print(aapl_data[['close', 'bb_lower_20', 'bb_middle_20', 'bb_upper_20']].tail())


def example_caching():
    """Example: Demonstrate intelligent caching behavior."""
    print("\n" + "=" * 60)
    print("Example 5: Intelligent Caching")
    print("=" * 60)

    dm = DataManager(db_path="cache_test.db")
    dm.downloader.register_downloader('binance', BinanceDataDownloader())

    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    # First call - downloads from API
    print("\nFirst call - downloading from API...")
    import time
    start_time = time.time()

    data1 = dm.get_data(
        symbols=['BTCUSDT'],
        start_date=start_date,
        end_date=end_date,
        interval='1d',
        source='binance',
        include_generated=False,
        include_features=False
    )

    first_call_time = time.time() - start_time
    print(f"Downloaded {len(data1)} records in {first_call_time:.2f} seconds")

    # Second call - retrieves from cache
    print("\nSecond call - retrieving from cache...")
    start_time = time.time()

    data2 = dm.get_data(
        symbols=['BTCUSDT'],
        start_date=start_date,
        end_date=end_date,
        interval='1d',
        source='binance',
        include_generated=False,
        include_features=False
    )

    second_call_time = time.time() - start_time
    print(f"Retrieved {len(data2)} records in {second_call_time:.2f} seconds")
    print(f"\nSpeedup: {first_call_time / second_call_time:.1f}x faster")


def example_export():
    """Example: Export data to CSV."""
    print("\n" + "=" * 60)
    print("Example 6: Export Data to CSV")
    print("=" * 60)

    dm = DataManager(db_path="crypto_data.db")
    dm.downloader.register_downloader('binance', BinanceDataDownloader())

    dm.feature_calculator.register_calculator(
        SMACalculator(symbol='BTCUSDT', periods=[20, 50])
    )

    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    data = dm.get_data(
        symbols=['BTCUSDT'],
        start_date=start_date,
        end_date=end_date,
        interval='1d',
        source='binance'
    )

    # Export to CSV
    output_file = 'btc_data_with_features.csv'
    dm.export_to_csv(output_file)
    print(f"\nData exported to: {output_file}")
    print(f"Records exported: {len(data)}")


if __name__ == "__main__":
    print("Data Manager - Example Usage")
    print("=" * 60)

    # Run examples
    # Note: You need to have python-binance and yfinance installed:
    # pip install python-binance yfinance

    try:
        example_binance_basic()
    except Exception as e:
        print(f"Error in example 1: {e}")

    try:
        example_multiple_symbols_with_features()
    except Exception as e:
        print(f"Error in example 2: {e}")

    try:
        example_synthetic_instruments()
    except Exception as e:
        print(f"Error in example 3: {e}")

    try:
        example_yahoo_finance()
    except Exception as e:
        print(f"Error in example 4: {e}")

    try:
        example_caching()
    except Exception as e:
        print(f"Error in example 5: {e}")

    try:
        example_export()
    except Exception as e:
        print(f"Error in example 6: {e}")

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
