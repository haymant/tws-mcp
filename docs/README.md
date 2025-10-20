# IBKR TWS MCP Server Documentation

This directory contains the essential documentation for the IBKR TWS MCP Server.

## Core Documentation

### [DESIGN.md](DESIGN.md)
**Architecture and Design**
- Overall system architecture
- Component interactions
- FastMCP framework usage
- ib_async integration
- Event-driven streaming pattern
- Lifespan management

**Read this first** to understand how the server works.

### [TOOLS.md](TOOLS.md)
**Complete Tools Reference**
- All available MCP tools
- Tool parameters and return values
- Usage examples
- Best practices
- Error handling
- Quick reference tables

**Use this** as your primary reference when calling tools.

### [MARKET_DATA.md](MARKET_DATA.md)
**Market Data Guide**
- Historical data retrieval
- Real-time streaming
- Contract definitions for various security types
- Bar sizes and durations
- Examples for stocks, forex, futures, options, etc.

**Reference this** for market data operations.

### [NEWS.md](NEWS.md)
**News Streaming Guide**
- News Bulletins (IB system alerts)
- Tick News (symbol-specific)
- BroadTape News (market-wide aggregation)
- Historical news queries
- Event-driven architecture
- Comparison matrix

**Reference this** for news operations.

### [PORTFOLIO.md](PORTFOLIO.md)
**Portfolio and Account Guide**
- Account summary
- Position tracking
- Portfolio streaming
- P&L monitoring
- Snapshot vs streaming comparison
- Multiple account handling

**Reference this** for portfolio operations.

---

## Quick Navigation

### By Task

**Getting Started:**
1. Read [DESIGN.md](DESIGN.md) for architecture
2. Check [TOOLS.md](TOOLS.md) for available tools
3. Follow examples in specific guides

**Trading Workflow:**
1. [MARKET_DATA.md](MARKET_DATA.md) - Research and price data
2. [NEWS.md](NEWS.md) - News and sentiment
3. [PORTFOLIO.md](PORTFOLIO.md) - Current positions
4. [TOOLS.md](TOOLS.md) - Place orders

**Monitoring:**
1. [PORTFOLIO.md](PORTFOLIO.md) - Real-time portfolio updates
2. [MARKET_DATA.md](MARKET_DATA.md) - Live prices
3. [NEWS.md](NEWS.md) - Breaking news

### By Feature

| Feature | Document |
|---------|----------|
| Connect/Disconnect | [TOOLS.md](TOOLS.md#connection) |
| Search Symbols | [TOOLS.md](TOOLS.md#contracts) |
| Historical Bars | [MARKET_DATA.md](MARKET_DATA.md#historical-data) |
| Real-Time Prices | [MARKET_DATA.md](MARKET_DATA.md#real-time-streaming) |
| Account Summary | [PORTFOLIO.md](PORTFOLIO.md#account-summary) |
| Positions | [PORTFOLIO.md](PORTFOLIO.md#positions) |
| Portfolio Streaming | [PORTFOLIO.md](PORTFOLIO.md#portfolio-streaming) |
| P&L Tracking | [PORTFOLIO.md](PORTFOLIO.md#pl-tracking) |
| Place Orders | [TOOLS.md](TOOLS.md#orders) |
| News Bulletins | [NEWS.md](NEWS.md#news-bulletins-ib-system-alerts) |
| Symbol News | [NEWS.md](NEWS.md#tick-news-symbol-specific-news) |
| Market News | [NEWS.md](NEWS.md#broadtape-news-all-market-news) |
| Historical News | [NEWS.md](NEWS.md#historical-news) |

---

## Event-Driven Streaming

All streaming resources (market data, portfolio, news) use a consistent event-driven pattern:

```python
# 1. Create queue for events
queue = asyncio.Queue()

# 2. Attach event handler
def on_event(data):
    queue.put_nowait(data)

ib.someEvent += on_event

# 3. Main loop
while True:
    await ib.updateEvent  # Wait for IB events
    
    # Drain queue
    while not queue.empty():
        data = queue.get_nowait()
        await send_resource_updated(uri)
```

This pattern is:
- **Non-blocking** - No polling loops
- **Event-driven** - Responds to IB events
- **Efficient** - Only processes actual updates
- **Consistent** - Used across all resources

See each guide for specific implementation details.

---

## Architecture Summary

```
┌─────────────────┐
│  MCP Client     │ (LLM Application)
└────────┬────────┘
         │ HTTP Streaming
         ▼
┌─────────────────┐
│  FastMCP Server │ (Python)
│  + Starlette    │
└────────┬────────┘
         │ ib_async
         ▼
┌─────────────────┐
│  TWS/Gateway    │ (IBKR)
└─────────────────┘
```

**Key Technologies:**
- **MCP Protocol** - Communication between client and server
- **FastMCP** - Python MCP framework
- **ib_async** - IB TWS API wrapper
- **Starlette** - ASGI web framework
- **asyncio** - Asynchronous I/O

---

## Resources

Streaming resources provide real-time updates:

| Resource | Started By | Updates |
|----------|-----------|---------|
| `ibkr://market-data/{id}` | `ibkr_start_market_data_resource` | Prices, volume |
| `ibkr://portfolio/{account}` | `ibkr_start_portfolio_resource` | Positions, P&L |
| `ibkr://news-bulletins` | `ibkr_start_news_resource` | IB alerts |
| `ibkr://tick-news/{symbol}` | `ibkr_start_tick_news_resource` | Symbol news |
| `ibkr://tick-news/*` | (aggregation) | All symbol news |
| `ibkr://broadtape-news` | `ibkr_start_broadtape_news_resource` | Market news |

**Workflow:**
1. Start with tool → 2. Subscribe to URI → 3. Receive updates → 4. Stop with tool

---

## Requirements

### IB Account
- Active IB account (live or paper)
- TWS or IB Gateway installed
- API connections enabled
- Market data subscriptions

### TWS Settings
File → Global Configuration → API → Settings:
- ✅ Enable "ActiveX and Socket Clients"
- ✅ Add "127.0.0.1" to trusted IPs
- ✅ Port: 7497 (TWS) or 4001 (Gateway)

### Python Environment
- Python 3.11+
- `uv` for environment management
- Dependencies in `pyproject.toml`

---

## Getting Help

1. **Check the docs** - Start with [TOOLS.md](TOOLS.md)
2. **Review examples** - Each guide has examples
3. **Check error messages** - Common errors documented
4. **IB API docs** - https://interactivebrokers.github.io/tws-api/

---

## Archive

The `archive/` directory contains old documentation files that have been consolidated into the 5 core documents above. These are kept for reference but should not be used for new development.

---

## Contributing

When updating documentation:
1. Keep information in the appropriate document
2. Update cross-references if needed
3. Maintain consistent formatting
4. Add examples for new features
5. Update this README if adding new docs

---

## Document Maintenance

Last major reorganization: October 20, 2025

**Changes:**
- Consolidated 50+ docs into 5 core documents
- Reorganized by topic (Tools, Market Data, News, Portfolio, Design)
- Removed outdated fix summaries and migration guides
- Added comprehensive examples
- Standardized formatting
- Improved navigation

**Core Philosophy:**
- **DESIGN.md** - How it works
- **TOOLS.md** - What you can do
- **MARKET_DATA.md** - Price data
- **NEWS.md** - News data
- **PORTFOLIO.md** - Account data

Everything else is obsolete or redundant.
