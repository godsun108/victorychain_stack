# VictoryChain Stack

## Overview
VictoryChain Stack is a cryptocurrency trading framework designed to facilitate interactions with various exchanges, specifically focusing on the Binance US exchange. The framework provides a structured way to manage trading operations, validate trading symbols, and handle order management.

## Features
- **Exchange Adapters**: Modular design allowing easy integration with different cryptocurrency exchanges.
- **Symbol Validation**: Ensures that trading symbols are valid and adhere to exchange requirements.
- **Order Management**: Functions for creating, canceling, and managing orders seamlessly.

## Installation
To install the necessary dependencies, run:

```
pip install -r requirements.txt
```

## Usage
To use the Binance US adapter, you can initialize it as follows:

```python
from libs.exchange_adapters.binance_us import BinanceUSAdapter

adapter = BinanceUSAdapter()
```

You can then use the adapter to create orders, validate symbols, and manage trades.

## Running Tests
To run the unit tests for the project, use the following command:

```
pytest tests/
```

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.