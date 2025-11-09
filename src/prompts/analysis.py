"""Market analysis prompts for IBKR TWS."""

from mcp.server.fastmcp import FastMCP


def register_analysis_prompts(mcp: FastMCP):
    """Register analysis-related prompts."""
    
    @mcp.prompt()
    def analyze_market_conditions(
        symbol: str = "AAPL",
        benchmark: str = "SPX"
    ) -> str:
        """Perform comprehensive market analysis combining real-time data, historical trends, 
        news sentiment, and options activity.
        
        This prompt guides you through multi-dimensional market analysis using TWS's suite
        of tools: real-time quotes, historical data, news feeds, and options chains. It
        provides a systematic approach to understanding market conditions before making
        trading decisions.
        
        Args:
            symbol: Stock symbol to analyze (default: AAPL)
            benchmark: Benchmark index for comparison (default: SPX)
            
        Returns:
            Step-by-step market analysis workflow
        """
        return f"""# Comprehensive Market Analysis for {symbol}

## Overview
Perform multi-dimensional analysis of {symbol} including:
- Real-time market data and technical indicators
- Historical price trends and volatility
- News sentiment and fundamental events
- Options market signals (implied volatility, put/call ratios)
- Comparative analysis vs {benchmark}
- Trading recommendations with risk assessment

## Prerequisites
- Active TWS connection
- Market data subscription for {symbol}
- News feed subscription
- Options data subscription
- Understanding of technical and fundamental analysis

## Step-by-Step Analysis Workflow

### 1. Real-Time Market Snapshot
**Tool**: `ibkr_get_market_data`
```
ibkr_get_market_data(
    symbol="{symbol}",
    exchange="SMART",
    genericTickList="100,101,104,105,106,165,221,225,233,236,258,411"
)
```

**Key Metrics to Record**:
```
Price Action:
- Last Price: $___
- Bid/Ask: $___ / $___
- Spread: $___
- Change: ___% (vs previous close)

Volume & Liquidity:
- Volume: ___ shares
- Average Volume (3mo): ___ shares
- Relative Volume: ___x (current vs average)

Volatility:
- Implied Volatility (IV): ___%
- Historical Volatility (HV): ___%
- IV Rank: ___ (current IV vs 52-week range)
- IV Percentile: ___%

Options Activity:
- Put/Call Ratio: ___
- Put/Call Volume Ratio: ___
```

**Real-Time Analysis**:
```
✅ High Volume + Up Move = Strong bullish momentum
⚠️ Low Volume + Up Move = Weak rally, possible reversal
✅ IV < HV = Options relatively cheap (good for buyers)
⚠️ IV > HV = Options expensive (good for sellers)
```

### 2. Historical Price Analysis
**Tool**: `ibkr_get_historical_data`

#### Short-Term Trend (5 days, 5-minute bars):
```
ibkr_get_historical_data(
    symbol="{symbol}",
    duration="5 D",
    barSize="5 mins",
    whatToShow="TRADES"
)
```

**Calculate Intraday Metrics**:
```python
# From 5-day intraday data
recent_high = max(bars.high)
recent_low = min(bars.low)
current_price = last_bar.close

# Position in range
range_position = (current_price - recent_low) / (recent_high - recent_low)
# 0.0 = at low, 0.5 = mid-range, 1.0 = at high

# Intraday momentum
sma_20 = average(last 20 bars)
if current_price > sma_20:
    trend = "Bullish (above 20-bar SMA)"
else:
    trend = "Bearish (below 20-bar SMA)"
```

#### Medium-Term Trend (6 months, daily bars):
```
ibkr_get_historical_data(
    symbol="{symbol}",
    duration="6 M",
    barSize="1 day",
    whatToShow="TRADES"
)
```

**Calculate Technical Indicators**:
```python
# Moving averages
sma_50 = average(last 50 days)
sma_200 = average(last 200 days)

# Trend classification
if sma_50 > sma_200 and price > sma_50:
    trend = "Strong Uptrend (Golden Cross)"
elif sma_50 < sma_200 and price < sma_50:
    trend = "Strong Downtrend (Death Cross)"
else:
    trend = "Consolidation or Transition"

# Support and resistance
support = recent_swing_low
resistance = recent_swing_high

# Average True Range (ATR) for volatility
atr_14 = average(true_range for last 14 days)
volatility_percent = (atr_14 / current_price) * 100
```

#### Long-Term Trend (2 years, weekly bars):
```
ibkr_get_historical_data(
    symbol="{symbol}",
    duration="2 Y",
    barSize="1 week",
    whatToShow="TRADES"
)
```

**Identify Major Patterns**:
```
- Multi-month channels
- Key breakout/breakdown levels
- Seasonal trends
- Long-term momentum (52-week high/low)
```

### 3. Volatility Analysis
**Tool**: `ibkr_get_histogram_data`
```
ibkr_get_histogram_data(
    symbol="{symbol}",
    period="3 months",
    barCount=100
)
```

**Volatility Metrics**:
```python
# Historical volatility
std_dev = standard_deviation(returns)
hist_vol_annual = std_dev * sqrt(252) * 100

# Compare to implied volatility
iv_current = from market_data
vol_spread = iv_current - hist_vol_annual

# Interpretation
if vol_spread > 5:
    signal = "IV elevated - consider selling options"
elif vol_spread < -5:
    signal = "IV depressed - consider buying options"
else:
    signal = "IV fairly priced"

# VIX-style volatility regime
if hist_vol_annual < 15:
    regime = "Low volatility - range-bound expected"
elif hist_vol_annual < 25:
    regime = "Normal volatility"
else:
    regime = "High volatility - elevated risk"
```

### 4. News and Sentiment Analysis
**Tool**: `ibkr_get_news_articles`
```
ibkr_get_news_articles(
    symbol="{symbol}",
    providerCodes="BRFUPDN+BRFG"  # Briefing.com + general news
)
```

**Analyze Recent News**:
```
Review headlines from last 24-48 hours:
1. Earnings announcements
2. Product launches
3. Regulatory news
4. Analyst upgrades/downgrades
5. Sector rotation news

Sentiment Score:
- Count positive headlines: ___
- Count negative headlines: ___
- Net sentiment: Bullish/Neutral/Bearish
```

**Tool**: `ibkr_start_news_resource`

For continuous monitoring:
```
ibkr_start_news_resource(
    symbol="{symbol}",
    providerCodes="BRFUPDN"
)
```
**Resource URI**: `ibkr://tick-news/{symbol}`

### 5. Options Market Analysis
**Tool**: `ibkr_get_option_chain`
```
ibkr_get_option_chain(
    symbol="{symbol}",
    secType="STK",
    exchange="SMART"
)
```

**Analyze Options Data**:

#### Implied Volatility Term Structure:
```
Get IV for different expirations:
- 1 week: ___%
- 1 month: ___%
- 3 months: ___%

Upward sloping = Market expects increasing volatility
Downward sloping = Market expects decreasing volatility
Flat = Stable volatility expectations
```

#### Put/Call Skew:
```
Compare ATM put IV vs ATM call IV:
- ATM Put IV: ___%
- ATM Call IV: ___%
- Skew: ___ (Put IV - Call IV)

Positive skew = Downside protection demand (bearish)
Negative skew = Upside speculation (bullish)
```

#### Open Interest Analysis:
```
# Get specific strikes with high OI
Max Call OI Strike: $___ (resistance level)
Max Put OI Strike: $___ (support level)

Heavy OI = Magnetic price level (dealers hedge)
```

**Tool**: `ibkr_get_market_data` (for specific options)

Get detailed Greeks for ATM options:
```
ibkr_get_market_data(
    symbol="{symbol} ATM_Call",
    exchange="SMART",
    genericTickList="100,101,104,105,106"
)
```

**Key Greeks**:
```
Delta: Directional bias
Gamma: Acceleration potential
Vega: Volatility sensitivity
Theta: Time decay rate
```

### 6. Fundamental Check
**Tool**: `ibkr_get_fundamental_data`
```
ibkr_get_fundamental_data(
    symbol="{symbol}",
    reportType="RESC"  # Analyst estimates
)
```

**Key Fundamental Metrics**:
```
Valuation:
- P/E Ratio: ___
- Forward P/E: ___
- PEG Ratio: ___
- Price/Book: ___

Growth:
- Revenue Growth: ___%
- Earnings Growth: ___%
- Analyst Target Price: $___

Financial Health:
- Debt/Equity: ___
- Current Ratio: ___
- Free Cash Flow: $___
```

**Upcoming Events**:
```
- Next Earnings Date: ___
- Ex-Dividend Date: ___
- Analyst Meetings: ___
```

### 7. Benchmark Comparison
**Tool**: `ibkr_get_market_data` (for benchmark)
```
ibkr_get_market_data(
    symbol="{benchmark}",
    exchange="SMART",
    genericTickList="100,101,104,105,106"
)
```

**Relative Performance**:
```python
# Get historical data for both
symbol_returns = calculate_returns("{symbol}")
benchmark_returns = calculate_returns("{benchmark}")

# Beta calculation
covariance = cov(symbol_returns, benchmark_returns)
variance = var(benchmark_returns)
beta = covariance / variance

# Alpha calculation
expected_return = risk_free_rate + beta * (benchmark_return - risk_free_rate)
alpha = actual_return - expected_return

# Correlation
correlation = corr(symbol_returns, benchmark_returns)
```

**Interpretation**:
```
Beta > 1: More volatile than {benchmark}
Beta < 1: Less volatile than {benchmark}
Alpha > 0: Outperforming expectations
Correlation < 0.7: Diversification benefit
```

### 8. Sector and Industry Analysis
**Tool**: `ibkr_get_scanner_results`

Find similar stocks and sector trends:
```
ibkr_get_scanner_results(
    scanCode="TOP_PERC_GAIN",
    instrument="STK",
    locationCode="STK.US",
    numberOfRows=50
)
```

**Sector Rotation Check**:
```
1. Identify {symbol}'s sector
2. Compare sector performance vs SPX
3. Check if sector is in/out of favor
4. Analyze sector rotation trends
```

### 9. Technical Setup Summary
Compile technical signals:

**Trend Signals**:
```
□ Price above 50-day SMA (Bullish)
□ Price above 200-day SMA (Bullish)
□ 50-day above 200-day (Golden Cross - Bullish)
□ Rising volume on up days (Bullish)
□ Price near 52-week high (Bullish)

Score: ___/5 bullish signals
```

**Momentum Indicators**:
```
RSI (14): ___ (>70 overbought, <30 oversold)
MACD: ___ (above/below signal line)
Stochastic: ___ (>80 overbought, <20 oversold)
```

**Support/Resistance Levels**:
```
Major Resistance: $___
Minor Resistance: $___
Current Price: $___
Minor Support: $___
Major Support: $___
```

### 10. Risk Assessment

**Volatility Risk**:
```
Historical Volatility: ___%
Implied Volatility: ___%
ATR (14-day): $___
Daily Range: ___% (ATR / price)

Risk Level: Low / Medium / High
```

**Event Risk**:
```
□ Earnings in next 2 weeks
□ Fed meeting this week
□ Dividend ex-date soon
□ Product launch scheduled
□ Regulatory decision pending

Event Risk: Low / Medium / High
```

**Liquidity Risk**:
```
Average Volume: ___ shares
Bid/Ask Spread: ___% of price
Options OI: ___ contracts

Liquidity: Excellent / Good / Fair / Poor
```

**Market Risk (Beta)**:
```
{symbol} Beta: ___
Systematic Risk: ___% (beta * SPX volatility)
Idiosyncratic Risk: ___% (total vol - systematic)

If {benchmark} drops 10%, {symbol} expected drop: ___%
```

## Synthesis: Trading Recommendation

### Overall Market Assessment
```
Direction: Bullish / Neutral / Bearish
Conviction: High / Medium / Low
Time Horizon: Short-term / Medium-term / Long-term
```

### Signal Strength
```
Technical Score: ___/10
Fundamental Score: ___/10
Sentiment Score: ___/10
Options Signal: Bullish / Neutral / Bearish

Overall Score: ___/10
```

### Trading Ideas

#### If Bullish Signal:
```
Strategy: Long stock or call options

Entry: $___
Stop Loss: $___ (below support)
Target 1: $___ (first resistance)
Target 2: $___ (second resistance)

Position Size: ___% of portfolio
Risk/Reward: 1:___

Alternative: Sell cash-secured puts to enter lower
```

#### If Bearish Signal:
```
Strategy: Short stock, buy puts, or sell calls

Entry: $___
Stop Loss: $___ (above resistance)
Target 1: $___ (first support)
Target 2: $___ (second support)

Position Size: ___% of portfolio
Risk/Reward: 1:___

Alternative: Buy protective puts on existing holdings
```

#### If Neutral Signal:
```
Strategy: Iron condor, covered call, or wait

Range: $___ to $___
Sell OTM call at: $___
Sell OTM put at: $___

Alternative: Wait for clearer signal
```

### Catalysts to Watch
```
Positive Catalysts:
1. ___
2. ___
3. ___

Negative Catalysts:
1. ___
2. ___
3. ___
```

### Best Practices

#### Analysis Workflow
1. **Top-Down**: Start with macro (SPX), then sector, then stock
2. **Multiple Timeframes**: Check daily, weekly, monthly charts
3. **Confirm Signals**: Look for multiple indicators agreeing
4. **Fresh Eyes**: Re-analyze before every trade

#### Data Interpretation
1. **Context Matters**: Compare to historical norms
2. **Relative Analysis**: Compare to sector/benchmark
3. **Volume Confirms**: Price moves need volume
4. **News Impact**: Understand why price is moving

#### Risk Management
1. **Position Sizing**: Larger positions for high-conviction setups
2. **Diversification**: Don't concentrate in one name
3. **Stop Losses**: Define exit before entry
4. **Time Decay**: Factor in for options positions

#### Continuous Monitoring
1. **Set Alerts**: Price, volume, news alerts
2. **Review Daily**: Check for new developments
3. **Update Thesis**: Adjust as new data arrives
4. **Journal Trades**: Record analysis and outcomes

## Sample Analysis Output

```
═══════════════════════════════════════════════════════════
MARKET ANALYSIS REPORT: {symbol}
Generated: [Current Date/Time]
═══════════════════════════════════════════════════════════

PRICE ACTION
Current Price: $___
Daily Change: ___% (___pts)
52-Week Range: $___ - $___
Position in Range: ___%

TECHNICAL SUMMARY
Trend: Bullish (price > SMA50 > SMA200)
Momentum: RSI 65 (neutral), MACD bullish crossover
Support: $___ (50-day SMA), $___ (200-day SMA)
Resistance: $___ (recent high), $___ (all-time high)

VOLATILITY ANALYSIS
Historical Vol: 25% (elevated)
Implied Vol: 28% (slightly high)
IV Rank: 60% (above average)
Signal: Consider selling options (IV > HV)

OPTIONS MARKET
Put/Call Ratio: 0.85 (neutral to bullish)
Max Pain: $___ (dealers want price here)
Skew: Puts more expensive (bearish tilt)
Term Structure: Upward sloping (event ahead)

NEWS SENTIMENT
Last 24h: 3 positive, 1 negative
Key Events: Analyst upgrade to Outperform
Upcoming: Earnings in 12 days
Sentiment: Bullish

FUNDAMENTAL SNAPSHOT
P/E: ___ (vs sector avg ___)
Growth: Revenue +___%, EPS +___%
Target Price: $___ (___% upside)
Rating: Buy (__ analysts)

RELATIVE PERFORMANCE
vs {benchmark}: +___% (1 month)
Beta: ___ (moderate volatility)
Correlation: ___ (diversification benefit)

RISK ASSESSMENT
Volatility Risk: Medium (HV 25%)
Event Risk: High (earnings soon)
Liquidity Risk: Low (tight spreads)
Overall Risk: Medium

═══════════════════════════════════════════════════════════
RECOMMENDATION: BUY
Confidence: 7/10
Target Entry: $___
Stop Loss: $___
Price Target: $___ (___% upside)
Time Horizon: 3-6 months
═══════════════════════════════════════════════════════════

RATIONALE:
- Strong technical setup with bullish trend
- Positive momentum and volume confirmation
- Options market shows moderate bullishness
- Analyst sentiment improving
- Approaching earnings (could be catalyst)

RISKS:
- Elevated volatility ahead of earnings
- Potential resistance at recent highs
- Broader market uncertainty

ACTION PLAN:
1. Build 50% position now at market
2. Add 25% on dip to support ($__)
3. Add final 25% on breakout above resistance ($__)
4. Set stop loss at $___ (below 50-day SMA)
5. Take profits at $___ (first target)
6. Trail stop to breakeven after +5%

═══════════════════════════════════════════════════════════
```

## Advanced Analysis Techniques

### Multi-Factor Scoring System
```python
# Weight different factors
technical_score = 7  # 0-10
fundamental_score = 6
sentiment_score = 8
options_score = 7

# Weighted average (adjust weights as needed)
weights = {{
    'technical': 0.3,
    'fundamental': 0.3,
    'sentiment': 0.2,
    'options': 0.2
}}

overall_score = (
    technical_score * 0.3 +
    fundamental_score * 0.3 +
    sentiment_score * 0.2 +
    options_score * 0.2
)
# Result: 7.0/10 = Moderately bullish
```

### Regime Detection
```
Identify market regime:
1. Bull Market: Uptrend + Low VIX + Positive breadth
2. Bear Market: Downtrend + High VIX + Negative breadth
3. Consolidation: Sideways + Medium VIX + Mixed breadth
4. Crisis: Sharp drop + Extreme VIX + Panic selling

Current Regime: ___
Strategy Adjustment: ___
```

### Correlation Analysis
```
Check correlations with:
- {benchmark} (market correlation)
- VIX (inverse correlation expected)
- Sector ETF (sector correlation)
- Competitors (industry correlation)

Low correlation = Good diversifier
High correlation = Redundant exposure
```

## Tools Reference Summary
```
Real-Time Data:
├─ ibkr_get_market_data (quotes, Greeks, volume)
├─ ibkr_start_market_data_resource (streaming)
└─ ibkr_get_scanner_results (market movers)

Historical Data:
├─ ibkr_get_historical_data (price bars)
├─ ibkr_get_histogram_data (distribution)
└─ ibkr_get_head_timestamp (data availability)

News & Sentiment:
├─ ibkr_get_news_articles (headlines)
├─ ibkr_start_news_resource (streaming)
└─ ibkr_get_news_providers (sources)

Options Analysis:
├─ ibkr_get_option_chain (strikes/expirations)
├─ ibkr_calculate_option_price (theoretical)
└─ ibkr_calculate_implied_volatility (IV calc)

Fundamentals:
└─ ibkr_get_fundamental_data (financials, estimates)
```

## Next Steps After Analysis
1. **Document Findings**: Save analysis report
2. **Set Alerts**: Price, volume, news triggers
3. **Plan Entry**: Wait for setup or enter now
4. **Define Risk**: Stop loss and position size
5. **Monitor**: Track for changes to thesis
6. **Review**: Compare actual vs expected outcomes
"""
