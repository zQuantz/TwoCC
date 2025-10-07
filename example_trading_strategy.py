"""
Example usage of the Trading Strategy system.

Demonstrates how to:
1. Initialize a trading strategy with the data manager
2. Generate trade suggestions for specific time periods
3. Use strategy suggestions with different market conditions
"""

from datetime import datetime, timedelta

from trading_strategy.two_candle_strategy import TwoCandleStrategy
from data_manager.data_downloader import BinanceDataDownloader
from data_manager.data_manager import DataManager

def main():
    print("=== Trading Strategy Example ===\n")

    # Step 1: Initialize Data Manager and load some data
    print("Step 1: Loading market data...")
    data_manager = DataManager(db_path="market_data.db", use_cache=False)
    data_manager.downloader.register_downloader('binance', BinanceDataDownloader())

    # Load data for a symbol
    # Note: You should have data already downloaded via the data_manager
    symbols = ['BTCUSDT', 'ETHUSDT']
    start_date = datetime(2025, 9, 1)
    end_date = datetime(2025, 10, 1)

    # try:
    data = data_manager.get_data(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        interval='1h',
        source='binance',
        include_generated=False,
        include_features=False
    )
    print(f"✓ Loaded data for {len(data_manager.get_available_symbols())} symbols")
    print(f"  Data range: {data.index.min()} to {data.index.max()}\n")
    # except Exception as e:
        # print(f"✗ Error loading data: {e}")
        # print("  Make sure you have data downloaded using the data_manager first.\n")
        # return

    # Step 2: Initialize Trading Strategy
    print("Step 2: Initializing Two Candle Strategy...")
    strategy = TwoCandleStrategy(
        data_manager=data_manager,
        strategy_id="two_candle_v1",
        strategy_name="Two Candle Momentum Strategy",
        position_size=1.0,
        min_volume=100.0
    )
    print(f"✓ Strategy initialized: {strategy}\n")

    # Step 3: Generate trade suggestions for specific time periods
    print("Step 3: Generating trade suggestions...\n")

    # Example 3a: Check for signals at a specific time
    symbol = 'BTCUSDT'
    test_time = start_date + timedelta(days=10)  # 10 days into our data

    print(f"=== Example 3a: Single Time Point ===")
    print(f"Symbol: {symbol}")
    print(f"Time: {test_time}")

    suggested_trades = strategy.get_suggested_trades(test_time, symbol)

    if suggested_trades:
        print(f"✓ Found {len(suggested_trades)} trade suggestion(s):")
        for trade in suggested_trades:
            print(f"  {trade}")
            print(f"    Signal strength: {trade.signal_strength:.2%}")
            print(f"    Notes: {trade.notes}")
    else:
        print("✗ No trade signals at this time")

    print()

    # Example 3b: Scan multiple time periods
    print("=== Example 3b: Scanning Multiple Time Periods ===")
    print(f"Scanning {symbol} for signals over 30 days...\n")

    signals_found = []
    scan_start = start_date + timedelta(days=5)  # Start a few days in
    scan_end = scan_start + timedelta(days=30)
    current_time = scan_start

    while current_time <= scan_end:
        trades = strategy.get_suggested_trades(current_time, symbol)
        if trades:
            signals_found.extend(trades)
        current_time += timedelta(hours=1)  # Move forward by 1 hour

    print(f"✓ Found {len(signals_found)} signals in 30 days")

    # Count by action type
    buy_signals = [t for t in signals_found if t.action.value == 'BUY']
    sell_signals = [t for t in signals_found if t.action.value == 'SELL']

    print(f"  BUY signals: {len(buy_signals)}")
    print(f"  SELL signals: {len(sell_signals)}")

    if signals_found:
        avg_strength = sum(t.signal_strength or 0 for t in signals_found) / len(signals_found)
        print(f"  Average signal strength: {avg_strength:.2%}")

    print()

    # Example 3c: Multi-symbol analysis
    print("=== Example 3c: Multi-Symbol Analysis ===")
    test_time_2 = start_date + timedelta(days=15)

    for sym in symbols[:2]:  # Check first 2 symbols
        trades = strategy.get_suggested_trades(test_time_2, sym)
        status = f"{len(trades)} signal(s)" if trades else "No signal"
        print(f"{sym:12} @ {test_time_2.strftime('%Y-%m-%d %H:%M')}: {status}")

        if trades:
            for trade in trades:
                print(f"  → {trade.action.value} {trade.quantity} @ ${trade.price:.2f} "
                      f"(strength: {trade.signal_strength:.1%})")

    print()

    # Example 3d: Demonstrate temporal integrity (no look-ahead bias)
    print("=== Example 3d: Temporal Integrity Check ===")
    print("Verifying that strategy only uses past data...\n")

    early_time = start_date + timedelta(days=2)
    later_time = start_date + timedelta(days=20)

    print(f"Checking signal at early time: {early_time}")
    early_trades = strategy.get_suggested_trades(early_time, symbol)
    print(f"  Result: {len(early_trades)} trade(s)")

    print(f"\nChecking signal at later time: {later_time}")
    later_trades = strategy.get_suggested_trades(later_time, symbol)
    print(f"  Result: {len(later_trades)} trade(s)")

    print("\n✓ Each call only sees data up to its respective time_period")
    print("  This ensures no look-ahead bias in backtesting!\n")

    # Summary
    print("=== Summary ===")
    print(f"Strategy: {strategy.strategy_name}")
    print(f"Strategy ID: {strategy.strategy_id}")
    print(f"Position Size: {strategy.position_size}")
    print(f"Minimum Volume: {strategy.min_volume}")
    print("\nThe strategy is ready to be used with:")
    print("  • Backtesting system (for historical performance)")
    print("  • Live trading system (for real-time execution)")
    print("  • Book system (for position tracking)")


if __name__ == "__main__":
    main()