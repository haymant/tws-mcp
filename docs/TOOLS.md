# IBKR TWS MCP Server - Tools Reference

Complete reference for all MCP tools provided by the IBKR TWS MCP Server.

## Quick Navigation

- [Connection](#connection) - Connect/disconnect from TWS
- [Contracts](#contracts) - Search symbols and get contract details  
- [Market Data](#market-data) - Historical and streaming market data
- [Portfolio](#portfolio) - Account summary, positions, P&L
- [Orders](#orders) - Place, cancel, and monitor orders
- [News](#news) - Bulletins, tick news, BroadTape, historical news
- [Resources](#resources) - Streaming data subscriptions

---

## Connection

### `ibkr_connect`
Connect to TWS or IB Gateway.

```json
{
  "host": "127.0.0.1",
  "port": 7497,
  "clientId": 1
}
```

### `ibkr_disconnect`
Disconnect from TWS/Gateway.

### `ibkr_get_status`
Get connection status.

---

## Contracts

### `ibkr_search_symbols`
Search for contracts by partial symbol.

```json
{
  "pattern": "AAPL"
}
```

### `ibkr_get_contract_details`
Get detailed contract information.

```json
{
  "symbol": "AAPL",
  "secType": "STK",
  "exchange": "SMART",
  "currency": "USD"
}
```

---

## Market Data

### `ibkr_get_historical_data`
Get historical bars.

```json
{
  "symbol": "AAPL",
  "durationStr": "5 D",
  "barSizeSetting": "1 hour",
  "whatToShow": "TRADES"
}
```

### `ibkr_start_market_data_resource`
Start real-time market data streaming.

```json
{
  "symbol": "AAPL"
}
```

Returns: `{"resource_uri": "ibkr://market-data/AAPL_STK_SMART_USD"}`

### `ibkr_stop_market_data_resource`
Stop market data streaming.

```json
{
  "resource_id": "AAPL_STK_SMART_USD"
}
```

**See [MARKET_DATA.md](MARKET_DATA.md) for details.**

---

## Portfolio

### `ibkr_get_account_summary`
Get account metrics (cash, buying power, etc.).

```json
{
  "account": "U1234567"
}
```

### `ibkr_get_positions`
Get current positions.

### `ibkr_start_portfolio_resource`
Start portfolio streaming (positions, P&L, account values).

```json
{
  "account": "U1234567"
}
```

Returns: `{"resource_uri": "ibkr://portfolio/U1234567"}`

### `ibkr_stop_portfolio_resource`
Stop portfolio streaming.

### `ibkr_get_pnl`
Get account-level P&L.

### `ibkr_get_pnl_single`
Get position-level P&L.

**See [PORTFOLIO.md](PORTFOLIO.md) for details.**

---

## Orders

### `ibkr_place_order`
Place a trade order.

**Market Order:**
```json
{
  "symbol": "AAPL",
  "action": "BUY",
  "quantity": 10,
  "orderType": "MKT"
}
```

**Limit Order:**
```json
{
  "symbol": "AAPL",
  "action": "SELL",
  "quantity": 10,
  "orderType": "LMT",
  "limitPrice": 155.00
}
```

### `ibkr_cancel_order`
Cancel an open order.

```json
{
  "orderId": 123
}
```

### `ibkr_get_open_orders`
Get all open orders.

### `ibkr_get_executions`
Get recent executions (fills).

```json
{
  "days": 1
}
```

---

## News

### News Bulletins (IB System Alerts)

#### `ibkr_start_news_resource`
Start streaming IB system bulletins.

```json
{
  "allMessages": true
}
```

Returns: `{"resource_uri": "ibkr://news-bulletins"}`

#### `ibkr_stop_news_resource`
Stop news bulletins.

---

### Tick News (Symbol-Specific)

#### `ibkr_start_tick_news_resource`
Start streaming news for specific symbols.

**Subscribe to symbols:**
```json
{"symbol": "AAPL"}
{"symbol": "MSFT"}
{"symbol": "TSLA"}
```

**Enable aggregation:**
```json
{"symbol": "*"}
```

**Important:** 
- `"*"` enables aggregation mode only
- You must subscribe to specific symbols first
- Then `"*"` aggregates news from all subscribed symbols

Returns: `{"resource_uri": "ibkr://tick-news/AAPL"}`

**Resource URIs:**
- `ibkr://tick-news/AAPL` - AAPL news only
- `ibkr://tick-news/*` - All news from subscribed symbols

#### `ibkr_stop_tick_news_resource`
Stop tick news for a symbol.

```json
{"symbol": "AAPL"}
```

---

### BroadTape News (All Market News)

#### `ibkr_start_broadtape_news_resource`
Start streaming ALL market news from all providers (BRF, BZ, FLY, DJ, etc.).

**No parameters** - automatically discovers and subscribes to all providers.

Returns: `{"resource_uri": "ibkr://broadtape-news"}`

**What You Get:**
- Headlines from ALL news providers your account has access to
- Aggregated into single stream
- Similar to TWS News tab

#### `ibkr_stop_broadtape_news_resource`
Stop BroadTape news.

---

### Historical News

#### `ibkr_get_news_providers`
Get list of available news providers.

Returns: `[{"code": "BRF", "name": "Briefing Trader"}, ...]`

#### `ibkr_get_historical_news`
Get past news headlines.

```json
{
  "symbol": "AAPL",
  "providerCodes": "BRF,BZ",
  "startDateTime": "20251001 00:00:00",
  "endDateTime": "20251018 23:59:59",
  "totalResults": 50
}
```

#### `ibkr_get_news_article`
Get full article text.

```json
{
  "providerCode": "BRF",
  "articleId": "BRF0000001234"
}
```

**See [NEWS.md](NEWS.md) for details.**

---

## Resources

Resources are **streaming endpoints** that send real-time updates.

### Workflow

1. **Start:** Call tool (e.g., `ibkr_start_market_data_resource`)
2. **Subscribe:** Subscribe to returned URI (e.g., `ibkr://market-data/AAPL_STK_SMART_USD`)
3. **Receive:** Get real-time notifications
4. **Stop:** Call stop tool

### Available Resources

| Resource URI | Tool | Description |
|--------------|------|-------------|
| `ibkr://market-data/{id}` | `ibkr_start_market_data_resource` | Real-time prices |
| `ibkr://portfolio/{account}` | `ibkr_start_portfolio_resource` | Portfolio updates |
| `ibkr://news-bulletins` | `ibkr_start_news_resource` | IB system bulletins |
| `ibkr://tick-news/{symbol}` | `ibkr_start_tick_news_resource` | Symbol news |
| `ibkr://tick-news/*` | (aggregation mode) | All symbol news |
| `ibkr://broadtape-news` | `ibkr_start_broadtape_news_resource` | All market news |

### `ibkr_list_active_resource_streams`
List all active streams.

Returns status of all running resources.

---

## News Quick Reference

**Choose the right tool:**

| What You Want | Use This |
|---------------|----------|
| IB system alerts | `ibkr_start_news_resource` → `ibkr://news-bulletins` |
| News for specific stock | `ibkr_start_tick_news_resource(symbol="AAPL")` → `ibkr://tick-news/AAPL` |
| News for multiple stocks | Start tick news for each, then read `ibkr://tick-news/*` |
| ALL market news (like TWS News tab) | `ibkr_start_broadtape_news_resource` → `ibkr://broadtape-news` |
| Historical news | `ibkr_get_historical_news` (not streaming) |
| Full article | `ibkr_get_news_article` (not streaming) |

---

## Best Practices

### Connection
- Call `ibkr_connect` first
- Verify with `ibkr_get_status`
- Handle disconnections

### Market Data
- Verify contracts with `ibkr_get_contract_details` first
- Stop unused streams
- Use appropriate bar sizes

### Portfolio
- One stream per account
- Stop when not needed
- Monitor with `ibkr_list_active_resource_streams`

### News
- **Specific stocks:** Tick news
- **Market-wide:** BroadTape
- **IB alerts:** News bulletins
- **Research:** Historical news

### Orders
- Verify contracts first
- Use limit orders for price control
- Monitor with `ibkr_get_open_orders`
- Check fills with `ibkr_get_executions`

---

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Error 162 | No historical data | Verify contract, date range |
| Error 10167 | Market data not subscribed | Subscribe in IB Client Portal |
| Error 321 | Invalid news source | Check `ibkr_get_news_providers` |
| Connection refused | TWS not running | Start TWS/Gateway |

---

## Requirements

### IB Account
- Active IB account (live or paper)
- TWS or IB Gateway running
- API enabled in settings
- Market data subscriptions

### TWS API Settings
1. File → Global Configuration → API → Settings
2. Enable "ActiveX and Socket Clients"
3. Add "127.0.0.1" to trusted IPs
4. Port: 7497 (TWS) or 4001 (Gateway)

### Market Data Subscriptions
- Real-time data requires subscriptions
- News requires provider subscriptions
- Configure in IB Client Portal

---

## See Also

- [DESIGN.md](DESIGN.md) - Architecture overview
- [MARKET_DATA.md](MARKET_DATA.md) - Market data guide
- [PORTFOLIO.md](PORTFOLIO.md) - Portfolio streaming
- [NEWS.md](NEWS.md) - News streaming details
