# Data Manager

The Data Manager is the first pillar of the TwoCandleCrypto algorithmic trading system. It encapsulates all logic for downloading, transforming, storing, and accessing market data.

## Architecture

The Data Manager consists of three main components:

### 1. Data Downloader
- Downloads market data from multiple sources (Binance, Yahoo Finance)
- Persists data to SQLite database for caching
- Implements intelligent caching to minimize API calls
- Automatically fills data gaps

### 2. Instrument Generator
- Creates synthetic instruments from existing market data
- Supports spread, ratio, and weighted combination calculations
- Generated instruments are accessible like regular market data

### 3. Feature Calculator
- Computes technical indicators and features
- Supports SMA, EMA, RSI, MACD, Bollinger Bands, ATR, and more
- Features are automatically recalculated when new data is added

## Installation

Install required dependencies:

```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```python
from datetime import datetime, timedelta
from data_manager import DataManager, BinanceDataDownloader

# Initialize Data Manager
dm = DataManager(db_path="market_data.db")

# Register a data source
dm.downloader.register_downloader('binance', BinanceDataDownloader())

# Download data
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

data = dm.get_data(
    symbols=['BTCUSDT'],
    start_date=start_date,
    end_date=end_date,
    interval='1d',
    source='binance'
)

print(data.head())
```

### Adding Technical Indicators

```python
from data_manager import SMACalculator, RSICalculator, MACDCalculator

# Register feature calculators
dm.feature_calculator.register_calculator(
    SMACalculator(symbol='BTCUSDT', periods=[20, 50, 200])
)
dm.feature_calculator.register_calculator(
    RSICalculator(symbol='BTCUSDT', period=14)
)
dm.feature_calculator.register_calculator(
    MACDCalculator(symbol='BTCUSDT')
)

# Features are automatically calculated
data = dm.get_data(
    symbols=['BTCUSDT'],
    start_date=start_date,
    end_date=end_date,
    interval='1d',
    source='binance',
    include_features=True
)
```

### Creating Synthetic Instruments

```python
from data_manager import SpreadGenerator, RatioGenerator

# Create BTC/ETH ratio
dm.instrument_generator.register_generator(
    RatioGenerator('BTCUSDT', 'ETHUSDT', 'BTC_ETH_RATIO')
)

# Create BTC-ETH spread
dm.instrument_generator.register_generator(
    SpreadGenerator('BTCUSDT', 'ETHUSDT', 'BTC_ETH_SPREAD')
)

data = dm.get_data(
    symbols=['BTCUSDT', 'ETHUSDT'],
    start_date=start_date,
    end_date=end_date,
    interval='1d',
    source='binance',
    include_generated=True
)

# Access synthetic instrument
ratio_data = dm.get_symbol_data('BTC_ETH_RATIO')
```

## Available Components

### Data Downloaders
- `BinanceDataDownloader` - Cryptocurrency data from Binance
- `YahooFinanceDataDownloader` - Traditional financial instruments

### Instrument Generators
- `SpreadGenerator` - Calculate difference between instruments
- `RatioGenerator` - Calculate ratio between instruments
- `WeightedCombinationGenerator` - Create weighted portfolios

### Feature Calculators
- `SMACalculator` - Simple Moving Average
- `EMACalculator` - Exponential Moving Average
- `RSICalculator` - Relative Strength Index
- `BollingerBandsCalculator` - Bollinger Bands
- `MACDCalculator` - MACD indicator
- `ATRCalculator` - Average True Range

## Extending the System

### Creating a Custom Downloader

```python
from data_manager.base import BaseDataDownloader
import pandas as pd

class CustomDataDownloader(BaseDataDownloader):
    def download(self, symbols, start_date, end_date, interval):
        # Your custom download logic
        data = pd.DataFrame()  # Your data here
        return data

# Register it
dm.downloader.register_downloader('custom', CustomDataDownloader())
```

### Creating a Custom Feature Calculator

```python
from data_manager.base import BaseFeatureCalculator

class CustomFeature(BaseFeatureCalculator):
    def __init__(self, symbol):
        self.symbol = symbol

    def calculate(self, data):
        # Add your custom feature
        data['custom_feature'] = data['close'].pct_change()
        return data

    def get_symbol(self):
        return self.symbol

    def get_feature_names(self):
        return ['custom_feature']

# Register it
dm.feature_calculator.register_calculator(CustomFeature('BTCUSDT'))
```

## Caching and Performance

The Data Manager implements intelligent caching:
- Downloaded data is automatically stored in SQLite
- Subsequent requests retrieve data from cache
- Only missing data gaps are downloaded
- Significantly reduces API calls and improves performance

## Examples

See [example_data_manager.py](example_data_manager.py) for comprehensive usage examples including:
- Basic data download
- Multiple symbols with features
- Synthetic instruments
- Yahoo Finance integration
- Caching demonstration
- Data export

## Design Principles

- **Single Responsibility**: Each component handles one aspect of data management
- **Extensibility**: New downloaders, generators, and calculators can be added without modifying existing code
- **Efficient Caching**: Minimize redundant downloads and calculations
- **Consistent Interface**: All data is accessed through uniform methods
- **Clean Separation**: Data acquisition, transformation, and access logic are clearly separated

## File Structure

```
data_manager/
├── __init__.py              # Package exports
├── base.py                  # Abstract base classes
├── data_downloader.py       # Downloader implementations
├── instrument_generator.py  # Synthetic instrument generators
├── feature_calculator.py    # Technical indicator calculators
└── data_manager.py          # Main coordinator class
```

## Next Steps

The Data Manager serves as the foundation for the remaining pillars:
- **TradingStrategy** - Define entry/exit rules using the data
- **Book** - Track positions and transactions
- **Backtester** - Historical strategy evaluation
- **BookAnalyzer** - Performance metrics and reporting
- **LiveSystem** - Real-time trade execution
