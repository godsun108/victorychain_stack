
# Microcap Trading System API Documentation

## Core Entities

### Price
Immutable value object representing monetary amounts with precision.
- **value**: Decimal precision amount
- **currency**: Currency code (default: USD)

### Position  
Domain entity representing a trading position.
- **symbol**: Trading pair symbol
- **entry_price**: Price at which position was opened
- **quantity**: Amount of tokens in position
- **stop_loss**: Risk management exit price

## Services

### MicrocapTradingService
Main application service orchestrating trading operations.

#### Methods
- `analyze_opportunities(symbols)`: Analyze multiple trading opportunities
- `create_optimal_portfolio(analyses)`: Create optimized portfolio
- `execute_portfolio(positions)`: Execute trading positions

## Architecture Patterns

### Clean Architecture
- **Domain Layer**: Entities, Value Objects, Business Rules
- **Application Layer**: Use Cases, Services
- **Infrastructure Layer**: External Dependencies, Data Access

### Design Patterns
- **Repository Pattern**: Data access abstraction
- **Strategy Pattern**: Pluggable algorithms
- **Observer Pattern**: Event handling
- **Dependency Injection**: Loose coupling
        