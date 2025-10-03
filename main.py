"""
Main entry point for the TwoCandleCrypto data processing pipeline.
"""

from datetime import datetime
from data_manager.data_downloader import BinanceDataDownloader
from data_manager.data_manager import DataManager
from data_manager.instrument_generator import (
    SpreadGenerator,
    RatioGenerator,
    WeightedCombinationGenerator
)
from data_manager.feature_calculator import (
    SMACalculator,
    EMACalculator,
    RSICalculator,
    BollingerBandsCalculator,
    MACDCalculator,
    ATRCalculator
)



def main():
    """Main data processing pipeline."""

    # Step 1: Specify all tickers we want to process
    tickers = [
        'BTCUSDT',
        'ETHUSDT',
        'SOLUSDT'
    ]

    # Step 2: Specify all instrument generators we want to use
    instrument_generators = [
        SpreadGenerator('BTCUSDT', 'ETHUSDT', 'BTC-ETH_SPREAD'),
        RatioGenerator('BTCUSDT', 'ETHUSDT', 'BTC/ETH_RATIO'),
    ]

    # Step 3: Specify all feature calculators we want to use
    feature_calculators = [
        SMACalculator(periods=[20, 50, 200]),
        EMACalculator(periods=[12, 26]),
        RSICalculator(period=14),
        BollingerBandsCalculator(period=20, std_dev=2.0),
        MACDCalculator(fast_period=12, slow_period=26, signal_period=9),
        ATRCalculator(period=14)
    ]

    # Step 4: Register everything to the data manager
    dm = DataManager(db_path="market_data.db", use_cache=True)
    dm.downloader.register_downloader('binance', BinanceDataDownloader())

    # Register instrument generators
    for generator in instrument_generators:
        dm.instrument_generator.register_generator(generator)

    # Register feature calculators
    for calculator in feature_calculators:
        dm.feature_calculator.register_calculator(calculator)

    # Step 5: Calculate the data
    start_date = datetime(2025, 7, 1)
    end_date = datetime(2025, 9, 30)
    interval = '1h'
    source = 'binance'

    print(f"Processing {len(tickers)} tickers...")
    print(f"Registered {len(instrument_generators)} instrument generators")
    print(f"Registered {len(feature_calculators)} feature calculators")
    print(f"Date range: {start_date} to {end_date}")
    print(f"Interval: {interval}")
    print()

    data = dm.get_data(
        symbols=tickers,
        start_date=start_date,
        end_date=end_date,
        interval=interval,
        source=source,
        include_generated=True,
        include_features=True
    )

    # Print summary
    print("\n" + "="*50)
    print("Data Processing Complete")
    print("="*50)
    summary = dm.get_summary()
    print(f"Status: {summary['status']}")
    print(f"Total symbols: {summary['symbols']}")
    print(f"Symbol list: {', '.join(summary['symbol_list'])}")
    print(f"Total records: {summary['records']}")
    print(f"Date range: {summary['date_range']}")
    print(f"Features: {', '.join(summary['features'])}")

    # Optionally export to CSV
    # dm.export_to_csv("output_data.csv")

    return dm, data


if __name__ == "__main__":
    dm, data = main()
    print(data.tail(10))
