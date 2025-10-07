"""
Example usage of the Book system.

Demonstrates creating trades, tracking positions, and analyzing strategy performance.
"""

from datetime import datetime

from book.trade import TradeAction
from book.trade import Trade
from book.book import Book

def main():
    # Create a new book
    book = Book(name="My Trading Book")

    # Register strategies
    book.register_strategy("momentum_v1", "Momentum Strategy v1")
    book.register_strategy("mean_reversion_v1", "Mean Reversion Strategy v1")
    book.register_strategy("risk_mgmt_v1", "Risk Management Strategy v1")

    # Example 1: Simple buy and sell
    print("=== Example 1: Simple Buy and Sell ===")

    # Entry trade
    buy_trade = Trade(
        symbol="AAPL",
        action=TradeAction.BUY,
        quantity=100,
        timestamp=datetime(2024, 1, 15, 10, 30),
        price=150.50,
        strategy_id="momentum_v1",
        strategy_name="Momentum Strategy v1",
        fees=1.0,
        signal_strength=0.85
    )
    book.add_trade(buy_trade)

    print(f"Added trade: {buy_trade}")
    print(f"Has open position in AAPL? {book.has_open_position('AAPL')}")

    # Exit trade
    sell_trade = Trade(
        symbol="AAPL",
        action=TradeAction.SELL,
        quantity=100,
        timestamp=datetime(2024, 1, 20, 15, 45),
        price=155.75,
        strategy_id="risk_mgmt_v1",  # Different strategy for exit
        strategy_name="Risk Management Strategy v1",
        fees=1.0
    )
    book.add_trade(sell_trade)

    print(f"Added trade: {sell_trade}")
    print(f"Has open position in AAPL? {book.has_open_position('AAPL')}")

    # Example 2: Multiple positions
    print("\n=== Example 2: Multiple Positions ===")

    trades = [
        Trade("TSLA", TradeAction.BUY, 50, datetime(2024, 2, 1, 9, 30), 200.0,
              "momentum_v1", fees=1.0),
        Trade("MSFT", TradeAction.BUY, 75, datetime(2024, 2, 1, 10, 0), 380.0,
              "mean_reversion_v1", fees=1.0),
        Trade("GOOGL", TradeAction.BUY, 30, datetime(2024, 2, 2, 11, 15), 140.0,
              "momentum_v1", fees=1.0),
    ]

    for trade in trades:
        book.add_trade(trade)

    print(f"Open positions: {list(book.get_open_positions().keys())}")
    print(f"Total symbols traded: {book.get_symbols()}")

    # Example 3: Position details
    print("\n=== Example 3: Position Details ===")

    position = book.get_position("AAPL")
    if position:
        print(f"AAPL Position:")
        print(f"  Current quantity: {position.current_quantity}")
        print(f"  Average entry price: ${position.average_entry_price:.2f}")
        print(f"  Is open: {position.is_open}")
        print(f"  Entry trades: {len(position.entry_trades)}")
        print(f"  Exit trades: {len(position.exit_trades)}")

    # Example 4: Strategy attribution
    print("\n=== Example 4: Strategy Attribution ===")

    strategy_perf = book.get_strategy_performance()
    for strategy_id, metrics in strategy_perf.items():
        print(f"\nStrategy: {metrics['strategy_name']} ({strategy_id})")
        print(f"  Total trades: {metrics['total_trades']}")
        print(f"  Entry trades: {metrics['entry_trades']}")
        print(f"  Exit trades: {metrics['exit_trades']}")
        print(f"  Symbols: {metrics['symbols_traded']}")

    # Example 5: Book summary
    print("\n=== Example 5: Book Summary ===")
    summary = book.summary()
    print(f"Book: {summary['book_name']}")
    print(f"Total trades: {summary['total_trades']}")
    print(f"Total symbols: {summary['total_symbols']}")
    print(f"Open positions: {summary['open_positions']}")
    print(f"Open symbols: {summary['open_symbols']}")

    # Example 6: Save and load
    print("\n=== Example 6: Save and Load ===")

    # Save book
    book.save("my_book.json")
    print("Book saved to my_book.json")

    # Load book
    loaded_book = Book.load("my_book.json")
    print(f"Loaded book: {loaded_book}")
    print(f"Trades in loaded book: {loaded_book.get_total_trades()}")


if __name__ == "__main__":
    main()
