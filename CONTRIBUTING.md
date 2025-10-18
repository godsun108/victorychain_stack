# Contributing to VictoryChain Trading System

Thank you for your interest in contributing to VictoryChain! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- Git
- Virtual environment (venv or conda)
- Basic understanding of cryptocurrency trading concepts

### Development Setup

1. **Fork the repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/yourusername/victorychain-stack.git
   cd victorychain-stack
   ```

2. **Set up development environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install development dependencies
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   
   # Install pre-commit hooks
   pre-commit install
   ```

3. **Configure environment**
   ```bash
   cp config/.env.template config/.env
   # Add your test API keys (use testnet keys for development)
   ```

4. **Run tests**
   ```bash
   python -m pytest tests/ -v
   ```

## 📋 How to Contribute

### Types of Contributions

We welcome all types of contributions:
- 🐛 Bug fixes
- ✨ New features
- 📚 Documentation improvements
- 🧪 Additional tests
- 🎨 Code style improvements
- 🔧 Configuration enhancements
- 💡 Trading strategy implementations

### Contribution Process

1. **Check existing issues**
   - Look through [existing issues](https://github.com/yourusername/victorychain-stack/issues)
   - Comment on issues you'd like to work on

2. **Create a new issue** (for new features/bugs)
   - Use appropriate issue templates
   - Provide detailed description
   - Include reproduction steps for bugs

3. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b bugfix/your-bug-fix
   ```

4. **Make your changes**
   - Follow coding standards (see below)
   - Add tests for new functionality
   - Update documentation as needed

5. **Test your changes**
   ```bash
   # Run all tests
   python -m pytest tests/ -v
   
   # Run linting
   black src/
   flake8 src/
   mypy src/
   
   # Test specific functionality
   python src/utilities/quick_status.py
   ```

6. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new trading strategy"
   # Use conventional commit messages (see below)
   ```

7. **Push and create pull request**
   ```bash
   git push origin feature/your-feature-name
   ```
   - Create PR on GitHub
   - Fill out PR template
   - Link related issues

## 📝 Coding Standards

### Code Style

**Python Style**
- Follow PEP 8 guidelines
- Use Black for automatic formatting
- Maximum line length: 88 characters
- Use type hints for all function parameters and return values

**Example:**
```python
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class TradingSignal:
    symbol: str
    action: str
    confidence: float
    timestamp: datetime

def analyze_market_data(
    symbols: List[str], 
    timeframe: str = "1h"
) -> Dict[str, TradingSignal]:
    """
    Analyze market data for given symbols.
    
    Args:
        symbols: List of trading symbols to analyze
        timeframe: Timeframe for analysis (1h, 4h, 1d)
        
    Returns:
        Dictionary mapping symbols to trading signals
        
    Raises:
        ValueError: If invalid timeframe provided
    """
    # Implementation here
    pass
```

### Documentation

**Docstrings**
- Use Google-style docstrings
- Document all public functions and classes
- Include type information in docstrings
- Provide usage examples for complex functions

**Comments**
- Use comments sparingly, prefer self-documenting code
- Explain "why" not "what"
- Update comments when code changes

### Testing

**Test Requirements**
- Unit tests for all new functions
- Integration tests for API interactions
- Mock external dependencies (APIs, databases)
- Test both success and failure scenarios

**Test Structure**
```python
import pytest
from unittest.mock import Mock, patch
from src.core.trading_engine import TradingEngine

class TestTradingEngine:
    """Test suite for TradingEngine class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = TradingEngine()
    
    def test_calculate_position_size_valid_input(self):
        """Test position size calculation with valid inputs."""
        # Arrange
        account_value = 10000
        risk_per_trade = 0.02
        
        # Act
        position_size = self.engine.calculate_position_size(
            account_value, risk_per_trade
        )
        
        # Assert
        assert position_size == 200
        
    def test_calculate_position_size_invalid_risk(self):
        """Test position size calculation with invalid risk."""
        with pytest.raises(ValueError, match="Risk must be between 0 and 1"):
            self.engine.calculate_position_size(10000, 1.5)
```

## 🏷️ Commit Message Guidelines

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```bash
feat(trading): add momentum trading strategy
fix(api): handle connection timeout errors
docs(readme): update installation instructions
test(portfolio): add unit tests for portfolio consolidation
```

## 🧪 Testing Guidelines

### Test Categories

**Unit Tests** (`tests/unit/`)
- Test individual functions and classes
- Mock external dependencies
- Fast execution (<1 second each)

**Integration Tests** (`tests/integration/`)
- Test component interactions
- Use test APIs/mock services
- Moderate execution time

**End-to-End Tests** (`tests/e2e/`)
- Test complete workflows
- Use sandbox/testnet environments
- Slower execution acceptable

### Test Data

**Use Fixtures**
```python
@pytest.fixture
def sample_portfolio():
    """Sample portfolio data for testing."""
    return {
        'total_value': 10000,
        'positions': [
            {'symbol': 'BTC', 'amount': 0.1, 'value': 4500},
            {'symbol': 'ETH', 'amount': 2.0, 'value': 5500}
        ]
    }
```

**Mock External APIs**
```python
@patch('src.api.binance_client.BinanceClient.get_account')
def test_get_portfolio(mock_get_account, sample_portfolio):
    """Test portfolio retrieval."""
    mock_get_account.return_value = sample_portfolio
    # Test implementation
```

## 🚀 Feature Development

### Trading Strategies

When adding new trading strategies:

1. **Inherit from base strategy class**
   ```python
   from src.core.base_strategy import BaseStrategy
   
   class MyStrategy(BaseStrategy):
       def generate_signals(self, market_data):
           # Implementation
           pass
   ```

2. **Include backtesting**
   - Provide historical performance data
   - Document strategy parameters
   - Include risk metrics

3. **Add configuration options**
   ```python
   STRATEGY_CONFIG = {
       'timeframe': '1h',
       'risk_per_trade': 0.02,
       'max_positions': 5
   }
   ```

### API Integrations

When adding new exchange integrations:

1. **Follow adapter pattern**
   ```python
   from src.core.exchange_adapter import ExchangeAdapter
   
   class NewExchangeAdapter(ExchangeAdapter):
       def get_account_balance(self):
           # Implementation
           pass
   ```

2. **Handle rate limiting**
3. **Implement error handling**
4. **Add comprehensive tests**

## 🐛 Bug Reports

### Bug Report Template

```markdown
**Bug Description**
Clear description of what the bug is.

**Steps to Reproduce**
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected Behavior**
What you expected to happen.

**Actual Behavior**
What actually happened.

**Environment**
- OS: [e.g. macOS, Windows, Linux]
- Python Version: [e.g. 3.9.0]
- VictoryChain Version: [e.g. 2.0.0]

**Additional Context**
- Log files
- Screenshots
- Configuration details
```

## 💡 Feature Requests

### Feature Request Template

```markdown
**Feature Description**
Clear description of the feature you'd like to see.

**Use Case**
Explain why this feature would be useful.

**Proposed Implementation**
If you have ideas on how it could be implemented.

**Additional Context**
Any other context or screenshots about the feature request.
```

## 🏆 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes for significant contributions
- Hall of Fame for major contributors

## 📞 Getting Help

- **GitHub Discussions**: For questions and general discussion
- **GitHub Issues**: For bugs and feature requests
- **Discord**: [Join our community](https://discord.gg/victorychain)
- **Email**: dev@victorychain.dev

## 📚 Resources

### Learning Resources
- [Python Trading Libraries](https://github.com/tradingstrategy-ai/trading-strategy)
- [Cryptocurrency Trading Basics](https://academy.binance.com/)
- [Technical Analysis](https://www.investopedia.com/technical-analysis-4689674)

### Development Tools
- [Black](https://black.readthedocs.io/) - Code formatting
- [Flake8](https://flake8.pycqa.org/) - Linting
- [MyPy](https://mypy.readthedocs.io/) - Type checking
- [Pytest](https://docs.pytest.org/) - Testing framework

Thank you for contributing to VictoryChain! 🚀
