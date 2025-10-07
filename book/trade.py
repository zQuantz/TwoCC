"""
Trade Module - Individual Trade Record

Represents a single trade execution with complete details for tracking,
analysis, and strategy attribution.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class TradeAction(Enum):
    """Enumeration of possible trade actions."""
    BUY = "BUY"
    SELL = "SELL"
    CLOSE = "CLOSE"
    SHORT = "SHORT"
    COVER = "COVER"


@dataclass
class Trade:
    """
    Represents a single trade execution.

    Essential Fields:
        symbol: Ticker identifier
        action: Type of trade (BUY, SELL, CLOSE, etc.)
        quantity: Number of units traded
        timestamp: When the trade was executed
        price: Execution price per unit
        strategy_id: Identifier of the strategy that generated this signal
        strategy_name: Human-readable name of the strategy

    Additional Fields:
        fees: Transaction costs/fees
        order_type: Type of order (MARKET, LIMIT, etc.)
        signal_strength: Confidence level of the signal (0-1)
        notes: Additional context or metadata
        metadata: Flexible dictionary for additional strategy-specific data
    """

    # Essential fields
    symbol: str
    action: TradeAction
    quantity: float
    timestamp: datetime
    price: float
    strategy_id: str
    strategy_name: Optional[str] = None

    # Additional fields for analysis
    fees: float = 0.0
    order_type: str = "MARKET"
    signal_strength: Optional[float] = None
    notes: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate trade data after initialization."""
        if self.quantity <= 0:
            raise ValueError(f"Trade quantity must be positive, got {self.quantity}")

        if self.price <= 0:
            raise ValueError(f"Trade price must be positive, got {self.price}")

        if self.fees < 0:
            raise ValueError(f"Trade fees cannot be negative, got {self.fees}")

        if self.signal_strength is not None and not (0 <= self.signal_strength <= 1):
            raise ValueError(f"Signal strength must be between 0 and 1, got {self.signal_strength}")

        # Convert string action to TradeAction enum if necessary
        if isinstance(self.action, str):
            self.action = TradeAction[self.action.upper()]

    @property
    def total_value(self) -> float:
        """Calculate total value of the trade including fees."""
        return (self.quantity * self.price) + self.fees

    @property
    def net_value(self) -> float:
        """
        Calculate net value considering trade direction.

        Returns:
            Positive for money out (BUY, COVER), negative for money in (SELL, CLOSE)
        """
        base_value = self.quantity * self.price

        if self.action in [TradeAction.BUY, TradeAction.COVER]:
            return base_value + self.fees
        else:  # SELL, CLOSE, SHORT
            return -(base_value - self.fees)

    def to_dict(self) -> Dict[str, Any]:
        """Convert trade to dictionary for serialization."""
        return {
            'symbol': self.symbol,
            'action': self.action.value,
            'quantity': self.quantity,
            'timestamp': self.timestamp.isoformat(),
            'price': self.price,
            'strategy_id': self.strategy_id,
            'strategy_name': self.strategy_name,
            'fees': self.fees,
            'order_type': self.order_type,
            'signal_strength': self.signal_strength,
            'notes': self.notes,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Trade':
        """Create Trade instance from dictionary."""
        data_copy = data.copy()

        # Convert timestamp string to datetime
        if isinstance(data_copy['timestamp'], str):
            data_copy['timestamp'] = datetime.fromisoformat(data_copy['timestamp'])

        # Convert action string to enum
        if isinstance(data_copy['action'], str):
            data_copy['action'] = TradeAction[data_copy['action']]

        return cls(**data_copy)

    def __repr__(self) -> str:
        """String representation of trade."""
        return (f"Trade(symbol={self.symbol}, action={self.action.value}, "
                f"quantity={self.quantity}, price={self.price}, "
                f"timestamp={self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}, "
                f"strategy={self.strategy_name or self.strategy_id})")
