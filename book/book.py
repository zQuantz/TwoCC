"""
Book Module - Portfolio Management System

Tracks all trading activity, maintains current state of holdings,
and provides strategy attribution.
"""

from typing import List, Dict, Optional, Set
from collections import defaultdict
from pathlib import Path
import json

import sys
sys.path.append(".")

from book.trade import Trade, TradeAction

class Position:
    """Represents a current open position for a symbol."""

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.quantity: float = 0.0
        self.entry_trades: List[Trade] = []
        self.exit_trades: List[Trade] = []
        self.is_open: bool = False

    @property
    def average_entry_price(self) -> float:
        """Calculate weighted average entry price."""
        if not self.entry_trades:
            return 0.0

        total_cost = sum(trade.quantity * trade.price for trade in self.entry_trades)
        total_quantity = sum(trade.quantity for trade in self.entry_trades)

        return total_cost / total_quantity if total_quantity > 0 else 0.0

    @property
    def current_quantity(self) -> float:
        """Calculate current position quantity."""
        entry_qty = sum(trade.quantity for trade in self.entry_trades)
        exit_qty = sum(trade.quantity for trade in self.exit_trades)
        return entry_qty - exit_qty

    def add_entry_trade(self, trade: Trade):
        """Add an entry trade to the position."""
        self.entry_trades.append(trade)
        self.quantity = self.current_quantity
        self.is_open = self.quantity > 0

    def add_exit_trade(self, trade: Trade):
        """Add an exit trade to the position."""
        self.exit_trades.append(trade)
        self.quantity = self.current_quantity
        self.is_open = self.quantity > 0

    def to_dict(self) -> Dict:
        """Convert position to dictionary."""
        return {
            'symbol': self.symbol,
            'quantity': self.quantity,
            'is_open': self.is_open,
            'average_entry_price': self.average_entry_price,
            'entry_trades': [trade.to_dict() for trade in self.entry_trades],
            'exit_trades': [trade.to_dict() for trade in self.exit_trades]
        }


class Book:
    """
    Centralized portfolio management system.

    Tracks all trading activity, maintains current state of holdings,
    and provides comprehensive query and analysis capabilities.
    """

    def __init__(self, name: str = "default"):
        self.name = name
        self._trades: List[Trade] = []
        self._positions: Dict[str, Position] = {}
        self._strategy_registry: Dict[str, str] = {}

    def register_strategy(self, strategy_id: str, strategy_name: str):
        """
        Register a strategy in the strategy registry.

        Args:
            strategy_id: Unique identifier for the strategy
            strategy_name: Human-readable name for the strategy
        """
        self._strategy_registry[strategy_id] = strategy_name

    def add_trade(self, trade: Trade):
        """
        Add a trade to the book.

        Args:
            trade: Trade object to add

        Updates:
            - Appends trade to historical record
            - Updates position tracking
            - Maintains open position state
        """
        # Add to historical record
        self._trades.append(trade)

        # Update position tracking
        if trade.symbol not in self._positions:
            self._positions[trade.symbol] = Position(trade.symbol)

        position = self._positions[trade.symbol]

        # Categorize trade as entry or exit
        if trade.action in [TradeAction.BUY, TradeAction.SHORT]:
            position.add_entry_trade(trade)
        elif trade.action in [TradeAction.SELL, TradeAction.CLOSE, TradeAction.COVER]:
            position.add_exit_trade(trade)

    def has_open_position(self, symbol: str) -> bool:
        """
        Check if a symbol has an open position.

        Args:
            symbol: Ticker symbol to check

        Returns:
            True if position is open, False otherwise
        """
        if symbol not in self._positions:
            return False
        return self._positions[symbol].is_open

    def get_position(self, symbol: str) -> Optional[Position]:
        """
        Get position for a symbol.

        Args:
            symbol: Ticker symbol

        Returns:
            Position object if exists, None otherwise
        """
        return self._positions.get(symbol)

    def get_open_positions(self) -> Dict[str, Position]:
        """
        Get all open positions.

        Returns:
            Dictionary of symbol -> Position for all open positions
        """
        return {symbol: pos for symbol, pos in self._positions.items() if pos.is_open}

    def get_all_positions(self) -> Dict[str, Position]:
        """
        Get all positions (open and closed).

        Returns:
            Dictionary of symbol -> Position for all positions
        """
        return self._positions.copy()

    def get_trades(self, symbol: Optional[str] = None) -> List[Trade]:
        """
        Get trades, optionally filtered by symbol.

        Args:
            symbol: Optional ticker symbol to filter by

        Returns:
            List of Trade objects
        """
        if symbol is None:
            return self._trades.copy()
        return [trade for trade in self._trades if trade.symbol == symbol]

    def get_trades_by_strategy(self, strategy_id: str) -> List[Trade]:
        """
        Get all trades for a specific strategy.

        Args:
            strategy_id: Strategy identifier

        Returns:
            List of Trade objects from this strategy
        """
        return [trade for trade in self._trades if trade.strategy_id == strategy_id]

    def get_strategy_performance(self) -> Dict[str, Dict]:
        """
        Calculate performance metrics by strategy.

        Returns:
            Dictionary of strategy_id -> performance metrics
        """
        strategy_metrics = defaultdict(lambda: {
            'total_trades': 0,
            'entry_trades': 0,
            'exit_trades': 0,
            'symbols_traded': set()
        })

        for trade in self._trades:
            metrics = strategy_metrics[trade.strategy_id]
            metrics['total_trades'] += 1
            metrics['symbols_traded'].add(trade.symbol)

            if trade.action in [TradeAction.BUY, TradeAction.SHORT]:
                metrics['entry_trades'] += 1
            else:
                metrics['exit_trades'] += 1

        # Convert sets to lists for JSON serialization
        result = {}
        for strategy_id, metrics in strategy_metrics.items():
            metrics['symbols_traded'] = list(metrics['symbols_traded'])
            metrics['strategy_name'] = self._strategy_registry.get(strategy_id, 'Unknown')
            result[strategy_id] = metrics

        return result

    def get_symbols(self) -> Set[str]:
        """
        Get all symbols that have been traded.

        Returns:
            Set of ticker symbols
        """
        return set(self._positions.keys())

    def get_total_trades(self) -> int:
        """Get total number of trades."""
        return len(self._trades)

    def save(self, filepath: str):
        """
        Save book to JSON file.

        Args:
            filepath: Path to save file
        """
        data = {
            'name': self.name,
            'trades': [trade.to_dict() for trade in self._trades],
            'strategy_registry': self._strategy_registry
        }

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> 'Book':
        """
        Load book from JSON file.

        Args:
            filepath: Path to load file

        Returns:
            Book instance
        """
        with open(filepath, 'r') as f:
            data = json.load(f)

        book = cls(name=data['name'])
        book._strategy_registry = data.get('strategy_registry', {})

        for trade_data in data['trades']:
            trade = Trade.from_dict(trade_data)
            book.add_trade(trade)

        return book

    def summary(self) -> Dict:
        """
        Generate summary statistics for the book.

        Returns:
            Dictionary with summary metrics
        """
        open_positions = self.get_open_positions()

        return {
            'book_name': self.name,
            'total_trades': self.get_total_trades(),
            'total_symbols': len(self.get_symbols()),
            'open_positions': len(open_positions),
            'open_symbols': list(open_positions.keys()),
            'total_strategies': len(set(trade.strategy_id for trade in self._trades)),
            'strategy_performance': self.get_strategy_performance()
        }

    def __repr__(self) -> str:
        """String representation of book."""
        return (f"Book(name={self.name}, trades={len(self._trades)}, "
                f"open_positions={len(self.get_open_positions())})")
