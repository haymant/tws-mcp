"""Trading execution prompts for IBKR TWS."""

from mcp.server.fastmcp import FastMCP


def register_trading_prompts(mcp: FastMCP):
    """Register trading-related prompts."""
    
    @mcp.prompt()
    def execute_bracket_order(
        symbol: str = "AAPL",
        entry_price: float = 0.0,
        take_profit: float = 0.0,
        stop_loss: float = 0.0
    ) -> str:
        """Execute a bracket order with take-profit and stop-loss for risk management.
        
        This prompt guides you through executing bracket orders (entry with attached take-profit
        and stop-loss) to manage risk. It leverages TWS's advanced order types for portfolio
        execution, automating position sizing and status monitoring.
        
        Args:
            symbol: Stock symbol (default: AAPL)
            entry_price: Entry limit price (0 = use market price)
            take_profit: Take profit price (0 = calculate from entry)
            stop_loss: Stop loss price (0 = calculate from entry)
            
        Returns:
            Step-by-step bracket order workflow
        """
        entry_note = f"${entry_price:.2f}" if entry_price > 0 else "market price"
        tp_note = f"${take_profit:.2f}" if take_profit > 0 else "calculate based on 2% profit"
        sl_note = f"${stop_loss:.2f}" if stop_loss > 0 else "calculate based on 1% loss"
        
        return f"""# Bracket Order Execution for {symbol}

## Overview
Execute a bracket order with:
- Entry: {entry_note}
- Take Profit: {tp_note}
- Stop Loss: {sl_note}

Bracket orders combine entry, profit target, and stop loss in one order group with risk management built-in.

## Prerequisites
- Active TWS connection
- Market data subscription for {symbol}
- Sufficient buying power
- Understanding of One-Cancels-All (OCA) order groups

## Step-by-Step Workflow

### 1. Check Current Market Conditions
**Tool**: `ibkr_get_market_data`
```
ibkr_get_market_data(
    symbol="{symbol}",
    exchange="SMART",
    genericTickList="100,101,104,105,106,165,221,225"  # Greeks, IV, RT Vol
)
```
**Action**: Record current bid, ask, last price, and volatility
**Expected**: Real-time market data with bid/ask spread

### 2. Calculate Risk Parameters

#### If Entry Price Not Specified:
```
entry_price = last_price
```

#### Calculate Position Size Based on Risk
**Tool**: `ibkr_get_account_summary`
```
ibkr_get_account_summary(
    tags="NetLiquidation,AvailableFunds,BuyingPower"
)
```

**Risk Management Calculation**:
```python
# Risk 1-2% of portfolio per trade
account_value = NetLiquidation
risk_per_trade = account_value * 0.02  # 2% max risk

# Calculate stop distance
if stop_loss == 0:
    # Use ATR or 1% rule
    stop_loss = entry_price * 0.99  # 1% below entry
    
stop_distance = entry_price - stop_loss
shares_to_trade = risk_per_trade / stop_distance

# Round down to whole shares
shares_to_trade = floor(shares_to_trade)

# Verify buying power
required_capital = shares_to_trade * entry_price
if required_capital > AvailableFunds:
    shares_to_trade = floor(AvailableFunds / entry_price)
```

#### Calculate Take Profit Level:
```python
if take_profit == 0:
    # Use 2:1 risk/reward ratio
    profit_distance = stop_distance * 2
    take_profit = entry_price + profit_distance
```

### 3. Preview Order Impact (Optional)
**Tool**: `ibkr_place_order` with transmit=false

Preview the entry order:
```
ibkr_place_order(
    symbol="{symbol}",
    action="BUY",
    quantity=shares_to_trade,
    orderType="LIMIT",
    price=entry_price,
    transmit=false  # Preview only - do not send to exchange
)
```
**Action**: Review commission, margin requirements
**Expected**: Order preview without actual submission

### 4. Place Bracket Order Using OCA Group

#### Step 4a: Place Entry Order (Parent)
**Tool**: `ibkr_place_order`
```
ibkr_place_order(
    symbol="{symbol}",
    action="BUY",
    quantity=shares_to_trade,
    orderType="LIMIT",
    price=entry_price,
    tif="DAY",
    transmit=true
)
```
**Expected**: Order ID for parent order
**Note**: Record the orderId for linking child orders

#### Step 4b: Place Take Profit Order (Child 1)
**Tool**: `ibkr_place_order`

**IMPORTANT**: Only place after entry order fills!

```
ibkr_place_order(
    symbol="{symbol}",
    action="SELL",
    quantity=shares_to_trade,
    orderType="LIMIT",
    price=take_profit,
    tif="GTC",  # Good-til-canceled
    ocaGroup="BRACKET_{symbol}_{timestamp}",
    ocaType=1,  # 1 = Cancel all remaining on fill
    parentOrderId=entry_order_id,  # Links to entry order
    transmit=true
)
```

#### Step 4c: Place Stop Loss Order (Child 2)
**Tool**: `ibkr_place_order`

**IMPORTANT**: Only place after entry order fills!

```
ibkr_place_order(
    symbol="{symbol}",
    action="SELL",
    quantity=shares_to_trade,
    orderType="STOP",
    auxPrice=stop_loss,  # Stop trigger price
    tif="GTC",
    ocaGroup="BRACKET_{symbol}_{timestamp}",  # Same OCA group as take profit
    ocaType=1,
    parentOrderId=entry_order_id,
    transmit=true
)
```

**OCA Group Behavior**: When either take profit OR stop loss fills, the other is automatically canceled.

### 5. Monitor Entry Order Execution
**Tool**: `ibkr_get_open_orders`
```
ibkr_get_open_orders()
```
**Action**: Wait for entry order to fill
**Timeout**: Consider 60 seconds; may need to adjust entry price if not filled

**Alternative Monitoring**:
**Tool**: `ibkr_get_order_status`
```
ibkr_get_order_status(orderId=entry_order_id)
```
**Expected Status**: Submitted → PreSubmitted → Filled

### 6. Verify Bracket Orders Are Active
Once entry fills, check child orders:
```
ibkr_get_open_orders()
```
**Expected**: 2 open orders in OCA group:
- LIMIT SELL at take_profit price
- STOP SELL at stop_loss price

### 7. Monitor Position and Exit Orders
**Tool**: `ibkr_start_portfolio_resource`
```
ibkr_start_portfolio_resource(account="")
```
**Resource URI**: `ibkr://portfolio/{{account}}`
**Expected**: Real-time position updates with P&L

**Monitor Exit Orders**:
- Check order status periodically
- Track unrealized P&L
- Adjust orders if market conditions change

### 8. Handle Partial Fills (If Applicable)
If entry order partially filled:
```
# Adjust exit order quantities to match filled quantity
filled_quantity = get from execution report

# Modify take profit quantity
ibkr_cancel_order(orderId=take_profit_order_id)
ibkr_place_order(
    symbol="{symbol}",
    action="SELL",
    quantity=filled_quantity,
    orderType="LIMIT",
    price=take_profit,
    ...
)

# Modify stop loss quantity
ibkr_cancel_order(orderId=stop_loss_order_id)
ibkr_place_order(
    symbol="{symbol}",
    action="SELL",
    quantity=filled_quantity,
    orderType="STOP",
    auxPrice=stop_loss,
    ...
)
```

### 9. Track Execution Results
**Tool**: `ibkr_get_executions`
```
ibkr_get_executions()
```
**Expected**: Execution details with fill prices, times, commissions

**Calculate Actual P&L**:
```
If take profit filled:
    profit = (take_profit - entry_fill_price) * shares - commissions
    
If stop loss filled:
    loss = (stop_fill_price - entry_fill_price) * shares - commissions
```

## Advanced Features

### Trailing Stop Instead of Fixed Stop
Replace fixed stop with trailing stop:
```
ibkr_place_order(
    symbol="{symbol}",
    action="SELL",
    quantity=shares_to_trade,
    orderType="TRAIL",
    auxPrice=0.50,  # Trail by $0.50 or use percentage
    trailingPercent=1.0,  # Trail by 1%
    parentOrderId=entry_order_id,
    ocaGroup="BRACKET_{symbol}_{timestamp}"
)
```

### Scale Out at Multiple Profit Targets
Instead of single take profit, use multiple exits:
```
# Exit 50% at first target
ibkr_place_order(quantity=shares_to_trade * 0.5, price=take_profit_1)

# Exit 30% at second target  
ibkr_place_order(quantity=shares_to_trade * 0.3, price=take_profit_2)

# Exit 20% at third target
ibkr_place_order(quantity=shares_to_trade * 0.2, price=take_profit_3)
```

### Adjust Orders Based on Technical Indicators
**Tool**: `ibkr_get_historical_data`

Get recent bars to calculate support/resistance:
```
ibkr_get_historical_data(
    symbol="{symbol}",
    duration="5 D",
    barSize="5 mins",
    whatToShow="TRADES"
)
```
Adjust stop loss to below recent support level.

## Best Practices

### Risk Management
1. **Position Sizing**: Never risk >2% of account on single trade
2. **Risk/Reward**: Minimum 2:1 ratio (take profit should be 2x stop distance)
3. **Stop Placement**: Use ATR (Average True Range) for volatility-based stops
4. **Account for Slippage**: Widen stops slightly for volatile stocks

### Order Entry
1. **Use LIMIT Orders**: Better control over entry price
2. **Check Spread**: Wide bid/ask spreads increase costs
3. **Time of Day**: Avoid first 30 mins and last 10 mins (high volatility)
4. **Transmit False First**: Preview orders before sending

### Order Management
1. **GTC vs DAY**: Use GTC for exit orders, DAY for entry
2. **OCA Groups**: Essential for automatic exit management
3. **Monitor Fills**: Set up alerts for order fills
4. **Adjust if Needed**: Move stops to breakeven once profitable

### After Trade
1. **Journal**: Record trade rationale, entry/exit prices, P&L
2. **Review**: Analyze what worked and what didn't
3. **Update Strategy**: Refine risk parameters based on results

## Common Errors and Solutions

### Error: "Order size exceeds available funds"
**Solution**: Reduce shares_to_trade or increase account funding

### Error: "No market data permissions"
**Solution**: Subscribe to market data for {symbol}

### Error: "Parent order not filled"
**Solution**: Wait for entry order to fill before placing child orders

### Error: "Stop price too close to market"
**Solution**: Widen stop loss distance (check minimum tick rules)

## Sample Bracket Order Calculation

```
Symbol: {symbol}
Entry Price: ${entry_price if entry_price > 0 else 'Market'}
Account Value: $100,000
Risk Per Trade: 2% = $2,000

Stop Loss: ${stop_loss if stop_loss > 0 else 'entry * 0.99'} (1% below entry)
Stop Distance: ${'calculated' if entry_price == 0 else f'{entry_price - stop_loss:.2f}'}

Position Size: $2,000 / Stop Distance = shares
Take Profit: Entry + (Stop Distance * 2) = ${take_profit if take_profit > 0 else 'calculated'}

Expected Risk: $2,000 (2% of account)
Expected Profit: $4,000 (4% of account)
Risk/Reward Ratio: 1:2
```

## Monitoring Checklist
- ✅ Entry order status (Filled/Pending)
- ✅ Take profit order active
- ✅ Stop loss order active  
- ✅ Position showing in portfolio
- ✅ Unrealized P&L tracking
- ✅ OCA group status (both orders linked)

## Exit Scenarios

### Scenario 1: Take Profit Hit
- ✅ Take profit order fills
- ✅ Stop loss automatically cancels (OCA group)
- ✅ Position closed with profit
- ✅ Record win in trading journal

### Scenario 2: Stop Loss Hit
- ✅ Stop loss order fills
- ✅ Take profit automatically cancels (OCA group)
- ✅ Position closed with small loss
- ✅ Record loss in trading journal
- ✅ Review trade for lessons

### Scenario 3: Manual Exit
If need to exit manually:
```
ibkr_cancel_order(orderId=take_profit_order_id)
ibkr_cancel_order(orderId=stop_loss_order_id)
ibkr_place_order(
    symbol="{symbol}",
    action="SELL",
    quantity=shares,
    orderType="MARKET"
)
```

## Performance Tracking
Track these metrics:
- Win rate (% of trades hitting take profit)
- Average win vs average loss
- Profit factor (gross profit / gross loss)
- Maximum drawdown
- Risk/reward ratio achieved vs planned

## Next Steps After Execution
1. Set price alerts for key levels
2. Monitor news for {symbol}
3. Review position before market close
4. Adjust stops to breakeven when appropriate
5. Document trade in journal with screenshots
"""

    @mcp.prompt()
    def execute_options_strategy(
        symbol: str = "AAPL",
        strategy_type: str = "covered_call"
    ) -> str:
        """Execute an options strategy for portfolio hedging or income generation.
        
        This prompt guides you through options-based portfolio strategies, drawing from TWS's
        OptionTrader for chains and spreads. It combines contract details, market data, and
        order tools to execute protective strategies like covered calls and collars.
        
        Args:
            symbol: Underlying stock symbol (default: AAPL)
            strategy_type: Strategy type - covered_call, protective_put, collar, iron_condor, etc.
            
        Returns:
            Step-by-step options strategy workflow
        """
        return f"""# Options Strategy Execution: {strategy_type.upper().replace('_', ' ')}

## Overview
Execute **{strategy_type.replace('_', ' ').title()}** strategy for {symbol}

Options strategies provide:
- **Income**: Covered calls, cash-secured puts
- **Protection**: Protective puts, collars
- **Speculation**: Spreads, straddles, strangles
- **Hedging**: Portfolio beta reduction

## Prerequisites
- Active TWS connection
- Options trading permissions
- Understanding of options risks
- Market data subscription for {symbol}
- For covered calls: Own 100 shares of {symbol} per contract

## Step-by-Step Workflow

### 1. Verify Current Position (For Covered Strategies)
**Tool**: `ibkr_get_positions`
```
ibkr_get_positions()
```
**Action**: Confirm you own shares of {symbol}
**Required for Covered Call**: 100 shares per contract (or multiples)

### 2. Get Current Stock Price and Volatility
**Tool**: `ibkr_get_market_data`
```
ibkr_get_market_data(
    symbol="{symbol}",
    exchange="SMART",
    genericTickList="100,101,104,105,106,165"  # Greeks and IV
)
```
**Key Metrics**:
- **Last Price**: Current stock price
- **Implied Volatility**: For option pricing
- **Historical Volatility**: Compare to IV for relative value

### 3. Retrieve Options Chain
**Tool**: `ibkr_get_option_chain`
```
ibkr_get_option_chain(
    symbol="{symbol}",
    secType="STK",
    exchange="SMART"
)
```
**Expected**: Available strikes and expirations

**Alternative - Get Specific Contract Details**:
**Tool**: `ibkr_search_contracts`
```
ibkr_search_contracts(
    symbol="{symbol}",
    secType="OPT",
    exchange="SMART"
)
```

### 4. Select Appropriate Strike and Expiration

#### For Covered Call:
```
Strategy: Sell out-of-money call against stock holdings

Strike Selection:
- Conservative: 5-10% above current price
- Moderate: 2-5% above current price  
- Aggressive: At-the-money or slightly above

Expiration Selection:
- Weekly: Higher annualized return, more management
- Monthly: Standard expiration (3rd Friday)
- 30-45 DTE: Optimal theta decay

Example:
Current {symbol} Price: $150
Select Call Strike: $155 (3.3% above)
Expiration: 30 days out
```

#### For Protective Put:
```
Strategy: Buy put to protect stock holdings

Strike Selection:
- 5-10% below current price for standard protection
- 10-15% below for cheaper protection (more risk)
- At-the-money for maximum protection (expensive)

Expiration Selection:
- Match to holding period
- Quarterly expirations for longer-term holds

Example:
Current {symbol} Price: $150
Select Put Strike: $145 (3.3% below)
Expiration: 90 days out
```

### 5. Get Real-Time Greeks and Pricing
**Tool**: `ibkr_get_market_data` (for specific option contract)

Once strike selected, get option pricing:
```
ibkr_get_market_data(
    symbol="{symbol} CALL/PUT",  # e.g., "AAPL 20251219 155 C"
    exchange="SMART",
    genericTickList="100,101,104,105,106"
)
```
**Key Greeks**:
- **Delta**: Probability of expiring ITM, directional exposure
- **Theta**: Time decay per day (income for sellers)
- **Vega**: Sensitivity to IV changes
- **Gamma**: Delta change rate

### 6. Calculate Strategy P&L Scenarios

#### Covered Call Example:
```python
# Parameters
stock_price = 150
shares_owned = 100
call_strike = 155
call_premium = 2.50  # Received when selling
total_premium = call_premium * 100 = $250

# Scenarios at expiration
Scenario 1: Stock at $148 (below strike)
- Stock P&L: -$200
- Option P&L: +$250 (expires worthless)
- Total: +$50

Scenario 2: Stock at $155 (at strike)
- Stock P&L: +$500
- Option P&L: +$250 (expires worthless)
- Total: +$750

Scenario 3: Stock at $160 (above strike)
- Stock P&L: +$1,000
- Option P&L: -$250 (assigned, capped at strike)
- Total: +$750 (max profit)

Max Profit: $750 (strike - entry + premium)
Max Loss: Unlimited on downside (same as stock)
Breakeven: $147.50 (entry - premium)
```

### 7. Place Options Order

#### Covered Call (Sell Call):
**Tool**: `ibkr_place_order`
```
ibkr_place_order(
    symbol="{symbol} 20251219 155 C",  # Contract symbol
    action="SELL",  # Sell to open
    quantity=1,  # 1 contract = 100 shares
    orderType="LIMIT",
    price=call_premium * 1.02,  # Slightly above mid for quick fill
    tif="DAY",
    transmit=true
)
```

#### Protective Put (Buy Put):
**Tool**: `ibkr_place_order`
```
ibkr_place_order(
    symbol="{symbol} 20251219 145 P",
    action="BUY",  # Buy to open
    quantity=1,
    orderType="LIMIT",
    price=put_premium * 0.98,  # Slightly below mid
    tif="DAY",
    transmit=true
)
```

### 8. Monitor Options Position
**Tool**: `ibkr_start_portfolio_resource`
```
ibkr_start_portfolio_resource(account="")
```
**Expected**: Real-time updates on option value and P&L

**Track Key Metrics**:
- **Days to Expiration** (DTE)
- **Theta Decay**: Income for sellers, cost for buyers
- **Delta Changes**: Directional exposure
- **Implied Volatility**: Changes affect option value

### 9. Manage Strategy Before Expiration

#### Early Assignment Risk (Covered Calls):
If stock price rises significantly above strike:
- Monitor for early assignment (especially before ex-dividend)
- Consider rolling up and out if bullish
- Let assignment happen if neutral/bearish

#### Roll Strategy (Extend Duration):
**Tool**: `ibkr_place_order` (combo order)

To roll covered call up and out:
```
# Step 1: Buy back current call
ibkr_place_order(
    symbol="{symbol} current_expiry current_strike C",
    action="BUY",  # Buy to close
    quantity=1
)

# Step 2: Sell new call (higher strike, later expiry)
ibkr_place_order(
    symbol="{symbol} new_expiry new_strike C",
    action="SELL",  # Sell to open
    quantity=1
)
```

#### Exit Early:
If profit target hit or risk increased:
```
# Close covered call
ibkr_place_order(
    symbol="{symbol} 20251219 155 C",
    action="BUY",  # Buy to close
    quantity=1,
    orderType="MARKET"
)
```

### 10. Handle Expiration

#### At Expiration (Options Expiring Worthless):
- **Covered Call**: Keep stock, keep premium (max profit)
- **Protective Put**: Expires worthless, protection cost realized

#### At Expiration (Options In-The-Money):
- **Covered Call**: Stock assigned at strike, realize max profit
- **Protective Put**: Exercise to sell stock at strike, limit loss

**Auto-Exercise**: IBKR auto-exercises ITM options at expiration

## Strategy-Specific Workflows

### Covered Call Strategy
**Goal**: Generate income on stock holdings

**Best When**:
- Neutral to slightly bullish on stock
- High implied volatility (higher premiums)
- Comfortable with capping upside

**Strike Selection**:
- **Conservative**: 10-15% OTM (low probability of assignment)
- **Moderate**: 5-10% OTM (balanced return/risk)
- **Aggressive**: ATM or ITM (max income, high assignment risk)

### Protective Put Strategy  
**Goal**: Limit downside risk on stock holdings

**Best When**:
- Holding stock through uncertain period
- Earnings announcement approaching
- Portfolio protection during volatility

**Strike Selection**:
- **5% OTM**: Moderate protection, lower cost
- **10% OTM**: Basic protection, cheapest
- **ATM**: Maximum protection, highest cost

### Collar Strategy (Covered Call + Protective Put)
**Goal**: Zero-cost protection with capped upside

**Workflow**:
```
1. Own {symbol} stock
2. Sell OTM call (generate premium)
3. Buy OTM put (use call premium to pay for put)
4. Net cost ≈ $0 (collar)

Result: Limited upside, limited downside
```

**Example**:
```
Stock: $150
Sell 155 Call for $3.00 credit
Buy 145 Put for $3.00 debit
Net Cost: $0

Max Profit: $5 (if stock at $155)
Max Loss: -$5 (if stock at $145)
Range: $145 - $155 (collared)
```

### Iron Condor (Advanced)
**Goal**: Profit from low volatility, range-bound stock

**Workflow**:
```
Sell OTM put spread + Sell OTM call spread

Example:
Sell 145 Put, Buy 140 Put (put credit spread)
Sell 155 Call, Buy 160 Call (call credit spread)

Max Profit: Net premium collected
Max Loss: Width of spread - premium
```

## Best Practices

### Options Selection
1. **Liquidity**: Choose options with tight bid/ask spreads
2. **Open Interest**: >100 for liquidity
3. **Volume**: Active trading indicates fair pricing
4. **Implied Volatility**: Sell when IV high, buy when IV low

### Risk Management
1. **Position Sizing**: Limit options to 5-10% of portfolio
2. **Diversification**: Don't sell calls on entire position
3. **Assignment Risk**: Monitor ITM options before expiration
4. **Greeks**: Understand delta, theta, vega exposure

### Execution
1. **Use Limit Orders**: Better fills than market orders
2. **Work the Spread**: Place order between bid/ask
3. **Time of Day**: Best fills during high volume periods
4. **Combo Orders**: Use for spreads to ensure fills

### Monitoring
1. **Daily**: Check P&L, days to expiration
2. **Weekly**: Review delta, theta decay
3. **Adjust**: Roll if needed before expiration
4. **Assignment**: Monitor ITM positions last week

## Common Errors and Solutions

### Error: "Not approved for options trading"
**Solution**: Apply for options approval in IBKR portal

### Error: "Insufficient margin for naked option"
**Solution**: Use covered/cash-secured strategies or increase margin

### Error: "Assignment after hours"
**Solution**: Normal for ITM options; check positions next morning

### Error: "Cannot roll - leg rejected"
**Solution**: Place combo order or roll legs separately

## Performance Metrics

### Covered Call Tracking
```
Metric | Target
━━━━━━━━━━━━━━━━━━━
Annualized Return | 8-12%
Assignment Rate | 20-30%
Avg Days Held | 30-45
Roll Success | 70%+
```

### Protective Put Tracking
```
Protection Cost | 2-4% per quarter
Breakeven Moves | <5% drops absorbed
Put Usage | Earnings, volatility events
```

## Advanced Techniques

### Delta-Neutral Portfolio
Use options to neutralize directional risk:
```
Portfolio Delta = Stock Delta + Options Delta
Target: Portfolio Delta ≈ 0 (market neutral)

Adjust with calls/puts to maintain neutrality
```

### Vega Hedging
Protect against IV changes:
```
Sell high vega options (short strangles)
Buy low vega options (deep ITM)
Net vega ≈ 0
```

### Theta Farming
Maximize time decay income:
```
Sell options with 30-45 DTE
Close at 50% profit
Reinvest in new positions
Target: Consistent theta decay collection
```

## Tax Considerations
- **Qualified Covered Calls**: Hold stock >1 year for long-term gains
- **Wash Sales**: Avoid if selling stock at loss and buying calls
- **1256 Contracts**: Index options get 60/40 tax treatment
- **Assignment**: Creates stock sale (track cost basis)

## Resources
- **Option Chain**: `ibkr_get_option_chain`
- **Greeks**: `ibkr_get_market_data` with genericTickList
- **Analysis**: `ibkr_get_historical_data` for IV trends
- **Positions**: `ibkr_get_positions` for current holdings

## Sample Options Strategy Summary
```
Strategy: Covered Call on {symbol}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Stock Position: 100 shares @ $150
Call Sold: 1x $155 Call (30 DTE)
Premium Received: $250
Max Profit: $750 (if assigned)
Max Loss: Unlimited (same as stock)
Breakeven: $147.50
Annualized Return: ~10% if not assigned
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
"""
