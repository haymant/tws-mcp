# News Streaming and Historical News

Complete guide to accessing financial news through the IB TWS API.

## Overview

The TWS API provides multiple ways to access news:

1. **News Bulletins** - IB system alerts and market updates (not contract-specific)
2. **Tick News** - Real-time news for specific symbols (per-stock)
3. **BroadTape News** - Aggregated real-time news from ALL providers (market-wide)
4. **Historical News** - Past news headlines for research

## Quick Start

```javascript
// Connect first
await ibkr_connect();

// For specific stock news
await ibkr_start_tick_news_resource({symbol: "AAPL"});
subscribe("ibkr://tick-news/AAPL");

// For ALL market news (like TWS News tab)
await ibkr_start_broadtape_news_resource();
subscribe("ibkr://broadtape-news");

// For IB system alerts
await ibkr_start_news_resource({allMessages: true});
subscribe("ibkr://news-bulletins");
```

---

## News Bulletins (IB System Alerts)

### What Are News Bulletins?

IB's internal notifications:
- System maintenance alerts
- Exchange closures
- Market-wide notifications
- Account-specific alerts

### Streaming Bulletins

**Start:**
```javascript
await ibkr_start_news_resource({
  allMessages: true  // true = all bulletins, false = account-only
});
```

**Subscribe:**
```javascript
subscribe("ibkr://news-bulletins");
```

**Example Bulletin:**
```json
{
  "msgId": 1,
  "msgType": 1,
  "message": "TWS will be unavailable Sunday 2AM-4AM ET for maintenance",
  "origExchange": "IB"
}
```

**Stop:**
```javascript
await ibkr_stop_news_resource();
```

### Use Cases
- Monitor system maintenance windows
- Track exchange holidays
- Get account alerts

---

## Tick News (Symbol-Specific News)

### What Is Tick News?

Real-time news headlines for specific stocks/contracts, delivered via market data subscriptions.

### How It Works

1. **Subscribe to symbols** - You must explicitly subscribe to each symbol
2. **News arrives** - Headlines delivered via `tickNewsEvent`
3. **Aggregation** - Use `"*"` to view all subscribed symbols together

### Important: Understanding "*"

**The `"*"` symbol does NOT automatically subscribe to all stocks!**

- `"*"` enables **aggregation mode** only
- You must subscribe to specific symbols first
- Then `"*"` aggregates news from subscribed symbols

### Correct Usage

**✅ RIGHT:**
```javascript
// Step 1: Subscribe to specific symbols
await ibkr_start_tick_news_resource({symbol: "AAPL"});
await ibkr_start_tick_news_resource({symbol: "MSFT"});
await ibkr_start_tick_news_resource({symbol: "TSLA"});

// Step 2: Read symbol-specific news
await resources.read("ibkr://tick-news/AAPL");  // AAPL only

// Step 3: Or read all aggregated
await resources.read("ibkr://tick-news/*");  // All 3 stocks
```

**❌ WRONG:**
```javascript
// This won't work - no symbols subscribed yet!
await ibkr_start_tick_news_resource({symbol: "*"});
await resources.read("ibkr://tick-news/*");  // Returns empty
```

### Streaming Tick News

**Start:**
```javascript
// Subscribe to symbol
await ibkr_start_tick_news_resource({
  symbol: "AAPL",
  secType: "STK",    // optional
  exchange: "SMART", // optional
  currency: "USD"    // optional
});
```

**Subscribe:**
```javascript
// For specific symbol
subscribe("ibkr://tick-news/AAPL");

// For all subscribed symbols
subscribe("ibkr://tick-news/*");
```

**Example Headline:**
```json
{
  "timestamp": 1697654321,
  "time": "2025-10-18T14:30:00",
  "providerCode": "BRF",
  "articleId": "BRF0000001234",
  "headline": "Apple announces Q4 earnings beat",
  "extraData": null
}
```

**Stop:**
```javascript
await ibkr_stop_tick_news_resource({symbol: "AAPL"});
```

### Resource URIs

| URI | What It Returns |
|-----|-----------------|
| `ibkr://tick-news/AAPL` | AAPL news only |
| `ibkr://tick-news/MSFT` | MSFT news only |
| `ibkr://tick-news/*` | All news from ALL subscribed symbols |

### Why This Design?

**Technical:**
- IB API requires a contract for news subscription
- No "all news" subscription exists in IB API
- News delivered via market data per symbol

**Performance:**
- Subscribing to thousands of symbols would overload connection
- Hit IB subscription limits
- Generate massive data
- Cost significant fees

### Use Cases

- Track news for watchlist stocks
- Monitor specific positions
- Get alerts on symbol-specific events

---

## BroadTape News (All Market News)

### What Is BroadTape?

Aggregated news feeds from ALL available news providers, similar to the TWS News tab.

**BroadTape** = Provider-specific aggregated market news (not symbol-specific)

Examples:
- `BRF:BRF_ALL` - All Briefing Trader headlines
- `BZ:BZ_ALL` - All Benzinga headlines
- `FLY:FLY_ALL` - All Fly on the Wall headlines

### How It Works

1. **Auto-discovery** - Queries available providers via `reqNewsProviders()`
2. **Subscribes to all** - Creates NEWS contracts for each provider
3. **Aggregates** - Combines all headlines into single stream

### Streaming BroadTape

**Start (no parameters needed):**
```javascript
await ibkr_start_broadtape_news_resource();
```

Automatically:
- Discovers all providers
- Subscribes to each BroadTape feed
- Starts aggregation

**Subscribe:**
```javascript
subscribe("ibkr://broadtape-news");
```

**Example Headlines:**
```json
{
  "headlines": [
    {
      "timestamp": 1697654321,
      "providerCode": "BRF",
      "headline": "Fed signals rate hold",
      "articleId": "BRF0000001234"
    },
    {
      "timestamp": 1697654325,
      "providerCode": "BZ",
      "headline": "Tech stocks rally on earnings",
      "articleId": "BZ0000005678"
    }
  ]
}
```

**Stop:**
```javascript
await ibkr_stop_broadtape_news_resource();
```

### vs. Tick News

| Feature | Tick News | BroadTape |
|---------|-----------|-----------|
| Scope | Symbol-specific | Market-wide |
| Subscription | Per symbol | All providers |
| Setup | Manual per symbol | Automatic |
| Like TWS | Chart news | News tab |
| Use for | Watchlist | Market overview |

### Common Providers

| Code | Name |
|------|------|
| BRFG | Briefing.com General (free) |
| BRF | Briefing Trader |
| BRFUPDN | Briefing Upgrades/Downgrades |
| BZ | Benzinga Pro |
| FLY | Fly on the Wall |
| DJ | Dow Jones |
| DJNL | Dow Jones Newsletter |

### Use Cases

- Monitor overall market sentiment
- Track breaking news across all sectors
- Replicate TWS News tab functionality
- Get comprehensive market coverage

---

## Historical News

### Get Past Headlines

**Get Providers:**
```javascript
const providers = await ibkr_get_news_providers();
// Returns: [{code: "BRF", name: "Briefing Trader"}, ...]
```

**Get Headlines:**
```javascript
await ibkr_get_historical_news({
  symbol: "AAPL",
  providerCodes: "BRF,BZ",  // Comma-separated
  startDateTime: "20251001 00:00:00",
  endDateTime: "20251018 23:59:59",
  totalResults: 50
});
```

**Example Response:**
```json
[
  {
    "time": "2025-10-18 14:30:00",
    "providerCode": "BRF",
    "articleId": "BRF0000001234",
    "headline": "Apple Q4 earnings beat estimates"
  },
  {
    "time": "2025-10-17 09:15:00",
    "providerCode": "BZ",
    "articleId": "BZ0000005678",
    "headline": "Apple announces new product line"
  }
]
```

### Get Full Article

```javascript
await ibkr_get_news_article({
  providerCode: "BRF",
  articleId: "BRF0000001234"
});
```

**Response:**
```json
{
  "providerCode": "BRF",
  "articleId": "BRF0000001234",
  "headline": "Apple Q4 earnings beat",
  "articleText": "Full article content here...",
  "sentimentCategory": "positive",
  "language": "en"
}
```

### Use Cases

- Research before trades
- Sentiment analysis
- Historical event correlation
- Fundamental analysis

---

## Event-Driven Architecture

All streaming news uses event-driven pattern:

```python
# 1. Create queue
queue = asyncio.Queue()

# 2. Attach event handler
def on_news(ticker, news_tick):
    queue.put_nowait(news_tick)

ib.tickNewsEvent += on_news

# 3. Main loop
while True:
    await ib.updateEvent  # Wait for IB events
    
    # Drain queue
    while not queue.empty():
        news = queue.get_nowait()
        await send_resource_updated(uri)
```

This pattern:
- Non-blocking
- Event-driven
- Efficient
- Consistent across all resources

---

## Comparison Matrix

| Feature | News Bulletins | Tick News | BroadTape | Historical |
|---------|----------------|-----------|-----------|------------|
| **Type** | System alerts | Symbol news | Market news | Past headlines |
| **Streaming** | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No (on-demand) |
| **Scope** | IB-wide | Per symbol | All providers | Query-based |
| **Setup** | `start_news_resource` | `start_tick_news_resource` | `start_broadtape_news_resource` | `get_historical_news` |
| **URI** | `ibkr://news-bulletins` | `ibkr://tick-news/{symbol}` | `ibkr://broadtape-news` | N/A |
| **Use for** | System status | Watchlist | Market overview | Research |

---

## Requirements

### IB Subscriptions

News requires active subscriptions:
- Check: IB Client Portal → Settings → Market Data Subscriptions
- Free: Briefing.com General (BRFG)
- Paid: Briefing Trader (BRF), Benzinga (BZ), Fly (FLY), etc.

### API Settings

TWS → File → Global Configuration → API:
- Enable "ActiveX and Socket Clients"
- Add "127.0.0.1" to trusted IPs

---

## Troubleshooting

### No News Arriving

**Tick News:**
1. Verify you subscribed to specific symbols first
2. Check `"*"` is just for aggregation
3. Verify market hours (news flows when market active)
4. Check subscriptions in IB Client Portal

**BroadTape:**
1. Verify providers with `ibkr_get_news_providers`
2. Check subscriptions in IB Client Portal
3. Ensure NEWS contracts qualified

**News Bulletins:**
1. Verify `allMessages=true`
2. Check connection status

### Error 162 (No Historical News)

- Contract not found or invalid
- Date range too old
- No news for that contract
- Solution: Verify contract, check date range

### Error 321 (Invalid News Source)

- NEWS contract validation failed
- Provider not available
- Solution: Check available providers

### Empty Results

- No news during period
- Missing subscriptions
- Provider not active
- Solution: Expand date range, verify subscriptions

---

## Best Practices

1. **Choose Right Tool:**
   - Watchlist → Tick News
   - Market overview → BroadTape
   - System alerts → Bulletins
   - Research → Historical

2. **Subscription Management:**
   - Stop unused streams
   - Monitor with `ibkr_list_active_resource_streams`
   - Verify subscriptions in IB Portal

3. **Performance:**
   - Don't subscribe to hundreds of symbols
   - Use BroadTape for market-wide
   - Use Tick News for specific stocks

4. **Error Handling:**
   - Verify contracts first
   - Check providers before historical queries
   - Handle empty results gracefully

---

## Examples

### Example 1: Monitor Watchlist

```javascript
// Your watchlist
const symbols = ["AAPL", "MSFT", "GOOGL", "TSLA"];

// Subscribe to each
for (const symbol of symbols) {
  await ibkr_start_tick_news_resource({symbol});
}

// Read aggregated
await resources.read("ibkr://tick-news/*");
```

### Example 2: Market Overview

```javascript
// Start BroadTape (auto-discovers providers)
await ibkr_start_broadtape_news_resource();

// Subscribe to stream
subscribe("ibkr://broadtape-news");

// Receive all market news
```

### Example 3: Pre-Trade Research

```javascript
// Get providers
const providers = await ibkr_get_news_providers();
const codes = providers.map(p => p.code).join(',');

// Get recent news
const news = await ibkr_get_historical_news({
  symbol: "AAPL",
  providerCodes: codes,
  startDateTime: "20251015 00:00:00",
  endDateTime: "20251018 23:59:59"
});

// Read full articles
for (const headline of news.slice(0, 5)) {
  const article = await ibkr_get_news_article({
    providerCode: headline.providerCode,
    articleId: headline.articleId
  });
  // Analyze sentiment, etc.
}
```

---

## See Also

- [TOOLS.md](TOOLS.md) - Complete tools reference
- [DESIGN.md](DESIGN.md) - Architecture overview
- [IB News API Documentation](https://interactivebrokers.github.io/tws-api/news.html)
