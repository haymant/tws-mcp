# MCP Prompts Quick Reference

## Available Prompts (6)

### 📊 Portfolio Management

#### 1. setup_trading_workspace
**Purpose**: Complete workspace setup with streaming resources  
**Parameters**: 
- `symbol` (default: "AAPL") - Stock symbol to monitor

**Use When**: 
- Starting a new trading session
- Setting up analysis for a specific symbol
- Need market data, portfolio, and news streaming

**Returns**: Step-by-step guide to:
- Connect to TWS
- Subscribe to market data
- Monitor portfolio in real-time
- Set up news alerts
- Proper cleanup procedures

---

#### 2. rebalance_portfolio
**Purpose**: Rebalance portfolio to target allocations  
**Parameters**:
- `target_allocations` (default: "") - Target allocation percentages (JSON or description)

**Use When**:
- Need to adjust portfolio weightings
- Periodic rebalancing (quarterly, monthly)
- Strategy requires different allocations

**Returns**: Workflow covering:
- Current position analysis
- Delta calculations
- Tax-efficient execution order (sells first)
- OCA groups for simultaneous orders
- Verification of final allocations

---

#### 3. assess_portfolio_risk
**Purpose**: Comprehensive portfolio risk analysis  
**Parameters**:
- `benchmark` (default: "SPX") - Benchmark for beta calculation

**Use When**:
- Need to understand portfolio risk exposure
- Before major market events
- Regular risk reviews (weekly, monthly)
- Planning hedging strategies

**Returns**: Analysis including:
- Portfolio beta (systematic risk)
- Value at Risk (VaR) calculation
- Stress testing scenarios
- Correlation matrix
- Concentration analysis
- Hedging recommendations

---

### 💼 Trading Execution

#### 4. execute_bracket_order
**Purpose**: Execute bracket order with take-profit and stop-loss  
**Parameters**:
- `symbol` (default: "AAPL") - Stock symbol
- `entry_price` (default: 0.0) - Entry price (0 = market)
- `take_profit` (default: 0.0) - Take profit price (0 = auto-calculate)
- `stop_loss` (default: 0.0) - Stop loss price (0 = auto-calculate)

**Use When**:
- Making directional trades with defined risk
- Want automated exits (no monitoring needed)
- Following risk management rules (2% max risk)

**Returns**: Complete workflow for:
- Market condition assessment
- Position sizing (based on account risk)
- OCA group setup (auto-exit management)
- Order monitoring and execution
- Partial fill handling
- Advanced: trailing stops, scale-out exits

---

#### 5. execute_options_strategy
**Purpose**: Execute options strategies for hedging or income  
**Parameters**:
- `symbol` (default: "AAPL") - Underlying stock symbol
- `strategy_type` (default: "covered_call") - Strategy type

**Supported Strategies**:
- Covered calls (income generation)
- Protective puts (downside protection)
- Collars (zero-cost protection)
- Iron condors (range-bound income)

**Use When**:
- Need to generate income on stock holdings
- Want downside protection during volatility
- Earnings approaching (protective strategies)
- Portfolio hedging required

**Returns**: Strategy-specific guidance:
- Position verification (shares owned)
- Options chain analysis
- Strike and expiration selection
- Greeks analysis (delta, theta, vega, gamma)
- Order execution
- Assignment and expiration handling
- Rolling positions

---

### 📈 Market Analysis

#### 6. analyze_market_conditions
**Purpose**: Multi-dimensional market analysis  
**Parameters**:
- `symbol` (default: "AAPL") - Stock to analyze
- `benchmark` (default: "SPX") - Benchmark for comparison

**Use When**:
- Before making trading decisions
- Need comprehensive market overview
- Research new trading ideas
- Validate existing positions

**Returns**: Complete analysis covering:
- **Technical**: Trends, support/resistance, indicators
- **Volatility**: IV vs HV, regime detection, ATR
- **Sentiment**: News analysis, headline scanning
- **Options**: Put/call ratios, IV term structure, max pain
- **Fundamental**: P/E, growth, analyst ratings
- **Relative**: Beta, correlation, sector rotation
- **Risk**: Volatility, event, liquidity assessment
- **Recommendation**: Trading ideas with entry/exit/targets

---

## Usage Patterns

### Quick Start Workflow
```
1. analyze_market_conditions (research)
   ↓
2. execute_bracket_order (enter position)
   ↓
3. assess_portfolio_risk (monitor risk)
   ↓
4. rebalance_portfolio (adjust weightings)
```

### Options Income Strategy
```
1. setup_trading_workspace (monitor stock)
   ↓
2. analyze_market_conditions (confirm neutral/bullish)
   ↓
3. execute_options_strategy (covered call)
   ↓
4. assess_portfolio_risk (check overall exposure)
```

### Risk Management Workflow
```
1. assess_portfolio_risk (identify issues)
   ↓
2. analyze_market_conditions (understand market)
   ↓
3. execute_options_strategy (protective puts)
   ↓
4. rebalance_portfolio (reduce concentration)
```

---

## Common Use Cases

### Daily Trading Routine
1. **Morning**: `setup_trading_workspace` for watchlist symbols
2. **Pre-Market**: `analyze_market_conditions` for top ideas
3. **Trading**: `execute_bracket_order` for entries
4. **End of Day**: `assess_portfolio_risk` for overnight positions

### Weekly Portfolio Review
1. `assess_portfolio_risk` to check current risk metrics
2. `rebalance_portfolio` if allocations drift >5%
3. `execute_options_strategy` for income generation
4. `analyze_market_conditions` for new ideas

### Event-Driven Trading
1. **Earnings**: `analyze_market_conditions` + `execute_options_strategy` (protective puts)
2. **Fed Meetings**: `assess_portfolio_risk` + hedge with options if needed
3. **Rebalancing**: `rebalance_portfolio` quarterly
4. **New Positions**: `analyze_market_conditions` → `execute_bracket_order`

---

## Pro Tips

### Prompt Chaining
Combine prompts for powerful workflows:
```
analyze_market_conditions(symbol="AAPL")
  → If bullish signal (score > 7/10):
    execute_bracket_order(symbol="AAPL", entry_price=market, take_profit=+5%, stop_loss=-2%)
  → Then:
    assess_portfolio_risk(benchmark="SPX")
```

### Parameter Customization
Use custom parameters for specific needs:
```
# Conservative bracket order (wider stops)
execute_bracket_order(symbol="NVDA", stop_loss=entry*0.97)  # 3% stop

# Aggressive covered call (at-the-money)
execute_options_strategy(symbol="TSLA", strategy_type="covered_call")
  → Select ATM strike in workflow

# Sector-specific risk assessment
assess_portfolio_risk(benchmark="XLF")  # Financial sector benchmark
```

### Resource Streaming
Most prompts reference streaming resources:
```
setup_trading_workspace → ibkr://market-data/{symbol}
                        → ibkr://portfolio/{account}
                        → ibkr://news-bulletins

Keep these open for real-time monitoring!
```

---

## Integration with MCP Inspector

### Accessing Prompts
```
1. Open MCP Inspector
2. Navigate to "Prompts" section
3. Select prompt from dropdown
4. Fill in parameters (or use defaults)
5. Click "Get Prompt"
6. Follow step-by-step workflow
```

### Executing Workflows
```
1. Copy tool calls from prompt output
2. Paste into MCP Inspector "Tools" section
3. Execute each step sequentially
4. Verify results before next step
5. Use streaming resources for monitoring
```

---

## Troubleshooting

### Prompt Not Appearing
- Restart MCP server
- Check `src/server.py` has `register_all_prompts(mcp)`
- Verify no import errors in prompts modules

### Tool Call Failures
- Ensure TWS connection active (`ibkr_connect`)
- Check market data subscriptions
- Verify account permissions for options/trading

### Parameter Errors
- All parameters have defaults (can invoke without params)
- Use type hints: strings in quotes, numbers without
- Invalid strategy_type → defaults to covered_call

---

## Next Actions

1. **Start Server**: `python3 main.py`
2. **Open MCP Inspector**: Connect to server
3. **Test Prompts**: Try each prompt with default parameters
4. **Real Trading**: Use `analyze_market_conditions` for research
5. **Risk Management**: Run `assess_portfolio_risk` regularly

Happy trading! 🚀
