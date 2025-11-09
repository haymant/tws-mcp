"""Portfolio management prompts for IBKR TWS."""

from mcp.server.fastmcp import FastMCP


def register_portfolio_prompts(mcp: FastMCP):
    """Register portfolio-related prompts."""
    
    @mcp.prompt()
    def setup_trading_workspace(symbol: str = "AAPL") -> str:
        """Complete trading workspace setup with market data, portfolio, and news monitoring.
        
        This prompt guides you through setting up a comprehensive trading environment by combining
        connection, streaming, and monitoring tools. It simplifies initial setup for portfolio
        oversight, ensuring real-time visibility into positions, market data, and news.
        
        Args:
            symbol: Stock symbol to monitor (default: AAPL)
            
        Returns:
            Step-by-step workflow for workspace setup
        """
        return f"""# Trading Workspace Setup for {symbol}

## Overview
Set up a complete trading workspace with real-time market data, portfolio monitoring, and news alerts.

## Prerequisites
- TWS or IB Gateway running on localhost:7496 (paper) or 4001 (live)
- Market data subscriptions active for {symbol}

## Step-by-Step Workflow

### 1. Connect to TWS
**Tool**: `ibkr_connect`
```
ibkr_connect(
    host="127.0.0.1",
    port=7496,  # 7496 for TWS paper, 4001 for IB Gateway paper
    clientId=1
)
```
**Expected**: Connection confirmation with server version

### 2. Start Real-Time Market Data Streaming
**Tool**: `ibkr_start_market_data_resource`
```
ibkr_start_market_data_resource(
    symbol="{symbol}",
    exchange="SMART",
    currency="USD"
)
```
**Resource URI**: `ibkr://market-data/{symbol}`
**Expected**: Streaming real-time quotes with bid/ask, last, volume

### 3. Start Portfolio Monitoring
**Tool**: `ibkr_start_portfolio_resource`
```
ibkr_start_portfolio_resource(
    account=""  # Leave empty to use default account
)
```
**Resource URI**: `ibkr://portfolio/{{account}}`
**Expected**: Real-time position updates with P&L, market values

### 4. Subscribe to News Alerts
**Tool**: `ibkr_start_news_resource`
```
ibkr_start_news_resource(
    allMessages=true
)
```
**Resource URI**: `ibkr://news-bulletins`
**Expected**: TWS system messages and trading alerts

**Optional - Symbol-Specific News**:
**Tool**: `ibkr_start_tick_news_resource`
```
ibkr_start_tick_news_resource(
    symbol="{symbol}",
    exchange="SMART"
)
```
**Resource URI**: `ibkr://tick-news/{symbol}`

### 5. View Current Positions
**Tool**: `ibkr_get_positions`
```
ibkr_get_positions()
```
**Expected**: List of all current positions with details

### 6. View Account Summary
**Tool**: `ibkr_get_account_summary`
```
ibkr_get_account_summary(
    tags="NetLiquidation,TotalCashValue,GrossPositionValue,AvailableFunds,BuyingPower"
)
```
**Expected**: Account values including buying power, P&L

## Best Practices
1. **Subscription Limits**: Limit concurrent market data subscriptions to avoid pacing violations
2. **Resource Management**: Use stop_*_resource tools when done to free up resources
3. **Error Handling**: Check connection status with `ibkr_get_status` if issues occur
4. **Multiple Symbols**: For multiple symbols, call `ibkr_start_market_data_resource` for each

## Monitoring Dashboard Components
After setup, you'll have:
- ✅ Real-time quotes for {symbol}
- ✅ Live portfolio positions and P&L
- ✅ Account margin and buying power
- ✅ News and system alerts
- ✅ Cash balances by currency

## Next Steps
- Add more symbols to market data streaming
- Set up price alerts with conditional orders
- Enable BroadTape news for market-wide coverage
- Monitor execution via order status tools

## Cleanup
When finished:
```
ibkr_stop_market_data_resource(resource_id="{symbol}")
ibkr_stop_portfolio_resource(account="")
ibkr_stop_news_resource()
ibkr_disconnect()
```
"""

    @mcp.prompt()
    def rebalance_portfolio(target_allocations: str = "") -> str:
        """Portfolio rebalancing workflow to align holdings with target allocations.
        
        This prompt guides you through comparing current portfolio holdings against target
        allocations and executing rebalancing trades. It mirrors TWS's Model Portfolios and
        Allocation Order Tool, automating portfolio alignment for diversification and risk control.
        
        Args:
            target_allocations: JSON string of target allocations, e.g. '{"AAPL": 30, "MSFT": 25, "GOOGL": 20, "SPY": 25}'
            
        Returns:
            Step-by-step rebalancing workflow
        """
        allocation_example = target_allocations or '{"AAPL": 30, "MSFT": 25, "GOOGL": 20, "SPY": 25}'
        
        return f"""# Portfolio Rebalancing Workflow

## Overview
Rebalance portfolio to target allocations: `{allocation_example}` (percentages)

## Prerequisites
- Active TWS connection
- Sufficient buying power for trades
- Target allocations add up to 100%

## Step-by-Step Workflow

### 1. Get Current Portfolio Positions
**Tool**: `ibkr_get_positions`
```
ibkr_get_positions()
```
**Action**: Record current positions, quantities, and market values
**Expected**: List of holdings with position sizes and values

### 2. Get Account Net Liquidation Value
**Tool**: `ibkr_get_account_summary`
```
ibkr_get_account_summary(
    tags="NetLiquidation,TotalCashValue,ExcessLiquidity"
)
```
**Action**: Note total portfolio value for percentage calculations
**Expected**: Account summary with net liquidation value

### 3. Calculate Target vs. Current Deltas
**Manual Calculation** (or use code execution):
```
For each symbol in target_allocations:
  target_value = NetLiquidation * (target_percentage / 100)
  current_value = current_position_value (from step 1)
  delta_value = target_value - current_value
  
  If delta_value > 0: Need to BUY
  If delta_value < 0: Need to SELL
  
  shares_to_trade = delta_value / current_market_price
```

### 4. Pre-Validate Orders with What-If Analysis
**Tool**: `ibkr_place_order` (with transmit=false for preview)

For positions to sell:
```
ibkr_place_order(
    symbol="SYMBOL",
    action="SELL",
    quantity=abs(shares_to_trade),
    orderType="MKT",
    transmit=false  # Preview only
)
```

Check margin impact before actual execution.

### 5. Execute Sell Orders First (Free Up Cash)
**Tool**: `ibkr_place_order`

For each symbol where delta_value < 0:
```
ibkr_place_order(
    symbol="SYMBOL",
    action="SELL",
    quantity=abs(shares_to_trade),
    orderType="LIMIT",
    price=market_price * 0.995,  # 0.5% below market for quick fill
    tif="DAY",
    transmit=true
)
```
**Best Practice**: Use LIMIT orders slightly below market for sells

### 6. Monitor Sell Order Executions
**Tool**: `ibkr_get_open_orders`
```
ibkr_get_open_orders()
```
**Action**: Wait for sells to fill before proceeding to buys
**Timeout**: Consider 30-60 seconds; cancel unfilled and use market orders if urgent

### 7. Execute Buy Orders
**Tool**: `ibkr_place_order`

For each symbol where delta_value > 0:
```
ibkr_place_order(
    symbol="SYMBOL",
    action="BUY",
    quantity=shares_to_trade,
    orderType="LIMIT",
    price=market_price * 1.005,  # 0.5% above market for quick fill
    tif="DAY",
    transmit=true
)
```
**Best Practice**: Use LIMIT orders slightly above market for buys

### 8. Monitor All Executions
**Tool**: `ibkr_get_executions`
```
ibkr_get_executions()
```
**Expected**: List of filled orders with execution prices and times

### 9. Verify Final Allocations
**Tool**: `ibkr_get_positions`
```
ibkr_get_positions()
```
**Action**: Calculate actual allocation percentages
**Verify**: Allocations match targets within acceptable tolerance (±2%)

### 10. Document Rebalancing
Record:
- Initial allocations
- Target allocations
- Final allocations
- Total transaction costs
- Execution quality (slippage)

## Advanced Features

### Use OCA Groups for Simultaneous Execution
For complex rebalancing, use One-Cancels-All groups:
```
ibkr_place_order(
    symbol="SYMBOL",
    action="BUY/SELL",
    quantity=shares,
    orderType="LIMIT",
    ocaGroup="REBALANCE_GROUP_1",
    transmit=true
)
```

### Tax Loss Harvesting
Before selling positions with gains:
- Check positions with losses
- Sell loss positions first to offset gains
- Use `ibkr_get_executions` to review cost basis

## Best Practices
1. **Order Sequencing**: Always sell before buying to ensure sufficient cash
2. **Risk Management**: Check excess liquidity before placing orders
3. **Slippage Control**: Use limit orders with reasonable spreads
4. **Monitoring**: Use `ibkr_start_portfolio_resource` for real-time position updates
5. **Fractional Shares**: IBKR supports fractional shares for easier rebalancing
6. **Transaction Costs**: Factor in commissions when calculating target quantities

## Error Handling
- **Insufficient funds**: Cancel buy orders, adjust targets
- **No market data**: Subscribe to market data before placing orders
- **Position limits**: Check account restrictions for concentrated positions

## Rebalancing Frequency Guidelines
- **Quarterly**: Most portfolios
- **Drift threshold**: Rebalance when allocation drifts >5% from target
- **Tax considerations**: Avoid frequent rebalancing in taxable accounts

## Sample Target Allocations
```json
{{
  "AAPL": 15,    // Tech sector
  "MSFT": 15,
  "GOOGL": 10,
  "SPY": 30,     // Market exposure
  "TLT": 15,     // Bonds
  "GLD": 10,     // Commodities
  "CASH": 5      // Cash buffer
}}
```

## Cleanup
After rebalancing:
```
ibkr_get_account_summary(tags="RealizedPnL,UnrealizedPnL")
```
Review P&L impact of rebalancing trades.
"""

    @mcp.prompt()
    def assess_portfolio_risk(benchmark: str = "SPX") -> str:
        """Assess and optimize portfolio risk with beta weighting and what-if scenarios.
        
        This prompt focuses on risk analysis, inspired by TWS's Risk Navigator for beta-weighted
        deltas, VaR, and scenario testing. It helps evaluate and mitigate portfolio risks.
        
        Args:
            benchmark: Benchmark symbol for beta weighting (default: SPX)
            
        Returns:
            Step-by-step risk assessment workflow
        """
        return f"""# Portfolio Risk Assessment & Optimization

## Overview
Assess portfolio risk relative to benchmark: **{benchmark}**

Use beta-weighted analysis, stress testing, and what-if scenarios to evaluate and mitigate portfolio risks.

## Prerequisites
- Active TWS connection
- Portfolio positions loaded
- Market data subscriptions for all holdings
- Historical data access

## Step-by-Step Workflow

### 1. Fetch Current Portfolio
**Tool**: `ibkr_get_positions`
```
ibkr_get_positions()
```
**Action**: Record all positions with quantities and current market values
**Expected**: List of holdings with position details

### 2. Get Account Summary for Risk Metrics
**Tool**: `ibkr_get_account_summary`
```
ibkr_get_account_summary(
    tags="NetLiquidation,MaintMarginReq,ExcessLiquidity,Cushion,FullMaintMarginReq"
)
```
**Key Metrics**:
- **Cushion**: (ExcessLiquidity / NetLiquidation) - risk of margin call
- **Maintenance Margin**: Required margin for current positions
- **Excess Liquidity**: Available for new positions

### 3. Calculate Beta-Weighted Deltas

#### a. Get Benchmark Data
**Tool**: `ibkr_get_historical_data`
```
ibkr_get_historical_data(
    symbol="{benchmark}",
    duration="1 Y",
    barSize="1 day",
    whatToShow="TRADES"
)
```
**Action**: Calculate benchmark returns

#### b. Get Historical Data for Each Position
For each holding:
```
ibkr_get_historical_data(
    symbol="HOLDING_SYMBOL",
    duration="1 Y",
    barSize="1 day",
    whatToShow="TRADES"
)
```

#### c. Compute Beta (Manual or Code Execution)
```python
# For each position:
beta = covariance(position_returns, benchmark_returns) / variance(benchmark_returns)
beta_weighted_delta = position_quantity * position_price * beta

# Total portfolio beta-weighted delta:
total_beta_delta = sum(beta_weighted_delta for all positions)
```

**Interpretation**:
- Beta = 1.0: Moves with market
- Beta > 1.0: More volatile than market
- Beta < 1.0: Less volatile than market

### 4. Analyze Greeks for Options Positions
**Tool**: `ibkr_get_market_data`

For options holdings:
```
ibkr_get_market_data(
    symbol="OPTION_SYMBOL",
    genericTickList="100,101,104,105,106"  # Greeks
)
```
**Metrics**:
- **Delta**: Directional exposure
- **Gamma**: Delta sensitivity
- **Theta**: Time decay
- **Vega**: IV sensitivity
- **Implied Vol**: Current volatility expectations

### 5. Run What-If Scenarios

**Tool**: Portfolio simulation (manual calculation or code execution)

Test scenarios:
1. **Market Crash**: {benchmark} drops 10%, 20%, 30%
2. **Volatility Spike**: IV increases 50%
3. **Sector Rotation**: Top position drops 15%
4. **Interest Rate Change**: TLT moves ±5%

Calculate impact on portfolio value for each scenario.

### 6. Calculate Value at Risk (VaR)

**95% VaR** (manual calculation):
```python
# Historical method:
1. Get daily portfolio returns for past year
2. Sort returns from worst to best
3. 95% VaR = 5th percentile return
4. Scale to dollar amount: VaR_dollars = VaR_percent * NetLiquidation

# Example:
If 5th percentile return = -2.5%
VaR_95 = 0.025 * $100,000 = $2,500 at risk in worst 5% of days
```

### 7. Stress Test Concentrated Positions

For positions > 10% of portfolio:
```
Position Size = (Position Value / Net Liquidation) * 100

If > 10%: High concentration risk
If > 20%: Very high concentration risk
```

**Action**: Consider diversifying concentrated positions

### 8. Correlation Analysis

Calculate correlation matrix between holdings:
- Low correlation (<0.3): Good diversification
- High correlation (>0.7): Redundant exposure

**Tool**: Historical data + code execution for correlation calculation

### 9. Generate Risk Mitigation Recommendations

Based on analysis, recommend actions:

#### High Beta Portfolio (Beta > 1.5):
- **Action**: Add low-beta stocks or bonds
- **Tools**: Buy TLT, utilities, consumer staples
- **Target**: Reduce overall portfolio beta to 1.0-1.2

#### Concentrated Position Risk:
- **Action**: Reduce position size or add protective puts
- **Tool**: `ibkr_get_option_chain` for protective puts
```
ibkr_get_option_chain(
    symbol="CONCENTRATED_POSITION",
    secType="STK"
)
```

#### High Volatility Exposure:
- **Action**: Sell covered calls or buy protective collars
- **Expected**: Reduce vega and delta exposure

#### Negative Excess Liquidity:
- **Action**: Close positions to increase margin cushion
- **Target**: Maintain cushion > 0.10 (10%)

### 10. Implement Hedging Strategy

Based on recommendations:

**Example 1: Reduce Beta with Index Puts**
```
ibkr_place_order(
    symbol="SPY PUT",
    action="BUY",
    quantity=hedge_quantity,
    orderType="LIMIT",
    price=option_ask * 1.02
)
```

**Example 2: Diversify Concentrated Position**
```
# Sell 50% of concentrated position
ibkr_place_order(
    symbol="CONCENTRATED_SYMBOL",
    action="SELL",
    quantity=current_quantity * 0.5,
    orderType="LIMIT"
)

# Buy diversified ETF
ibkr_place_order(
    symbol="SPY",
    action="BUY",
    quantity=shares_to_buy,
    orderType="LIMIT"
)
```

## Risk Metrics Dashboard

After analysis, you should have:
- ✅ Portfolio beta relative to {benchmark}
- ✅ Beta-weighted delta exposure
- ✅ 95% Value at Risk (VaR)
- ✅ Correlation matrix of holdings
- ✅ Concentration analysis
- ✅ Margin cushion status
- ✅ Options greeks exposure (if applicable)
- ✅ Stress test results

## Best Practices
1. **Beta Weighting**: Always beta-weight to relevant benchmark ({benchmark} for US equities)
2. **Position Limits**: Keep individual positions < 10% of portfolio for diversification
3. **Margin Cushion**: Maintain cushion > 10% to avoid margin calls
4. **Rebalancing**: Review and rebalance quarterly or when beta drifts >20%
5. **Options Hedging**: Use protective puts for concentrated positions
6. **Correlation**: Target average correlation < 0.5 between major holdings
7. **VaR Monitoring**: Set alerts if VaR exceeds 5% of portfolio value

## Advanced Risk Tools

### Portfolio Greeks (Options Heavy Portfolios)
```
Total Portfolio Delta = sum(position_delta * quantity)
Total Portfolio Gamma = sum(position_gamma * quantity)
Total Portfolio Theta = sum(position_theta * quantity)
Total Portfolio Vega = sum(position_vega * quantity)
```

### Sector Exposure Analysis
Group positions by sector and calculate:
- Sector weight as % of portfolio
- Sector beta
- Sector correlation to benchmark

### Downside Deviation
More conservative than standard deviation:
```
Downside_Dev = sqrt(average(min(return, 0)^2))
```
Focuses only on negative returns.

## Warning Signals
- 🔴 **Cushion < 0.05**: Margin call risk
- 🟡 **Position > 20%**: High concentration
- 🟡 **Beta > 1.8**: High market sensitivity
- 🟡 **VaR > 10%**: Excessive risk
- 🔴 **Correlation > 0.9**: Redundant positions

## Periodic Review
- **Daily**: Margin cushion, VaR
- **Weekly**: Beta, concentration
- **Monthly**: Full risk assessment with stress tests
- **Quarterly**: Rebalancing decisions

## Sample Risk Report Output
```
Portfolio Risk Assessment ({benchmark} Benchmark)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Net Liquidation: $150,000
Portfolio Beta: 1.32
Beta-Weighted Delta: +$198,000 (132% of NLV)
95% VaR (1-day): $3,750 (2.5% of NLV)
Margin Cushion: 15.2% ✓
Largest Position: AAPL (18.5%) ⚠️

Stress Tests:
- Market -10%: -$19,800 (-13.2%)
- Market -20%: -$39,600 (-26.4%)
- IV +50%: -$2,100 (-1.4%)

Recommendations:
1. Reduce AAPL position to <10%
2. Add bond exposure (TLT) to reduce beta
3. Consider protective puts on concentrated positions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
"""
