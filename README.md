# IBKR TWS MCP Server

This project implements a Model Context Protocol (MCP) server for the Interactive Brokers (IBKR) Trader Workstation (TWS) API. It uses the official `modelcontextprotocol/python-sdk` and `ib_async` to expose key TWS functionalities as MCP tools, enabling seamless integration with LLM clients for automated financial workflows, such as portfolio rebalancing.

The server supports **HTTP Streaming** for MCP protocol and **WebSocket streaming** for real-time data subscriptions (market data, portfolio updates, news bulletins).

## Features

*   **MCP Compliance:** Built with FastMCP for full adherence to the Model Context Protocol with HTTP streaming support.
*   **Asynchronous TWS Integration:** Leverages `ib_async` (maintained fork of ib-insync) for non-blocking, asynchronous interaction with the TWS API.
*   **Comprehensive Toolset:** 51+ tools for connection management, market data retrieval (historical and streaming), account and portfolio querying, and order management (placing and canceling orders).
*   **MCP Prompts:** 6 guided workflows that combine multiple tools into expert-level trading strategies (bracket orders, portfolio rebalancing, risk assessment, options strategies, market analysis, and workspace setup).
*   **Real-time WebSocket Streaming:** Three dedicated WebSocket endpoints for continuous real-time data:
    - **Market Data Stream** - Real-time quotes for multiple symbols
    - **Portfolio Stream** - Live portfolio and account updates
    - **News Stream** - IBKR news bulletins and system messages
*   **HTTP Streaming Transport:** Uses chunked transfer encoding for efficient MCP tool responses.
*   **CORS Support:** Configured to allow cross-origin requests from browser-based MCP clients (e.g., Goflow, web applications).
*   **Containerized Deployment:** Ready-to-use Docker and Docker Compose configuration.

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Client Application                              │
├─────────────────────────────────────────────────┤
│  1. MCP Client (HTTP Streaming)                 │
│     POST /api/v1/mcp                             │
│     - Tool calls: connect, orders, positions     │
│                                                   │
│  2. WebSocket Clients (real-time streams)       │
│     WS /api/v1/stream/market-data                │
│     WS /api/v1/stream/portfolio                  │
│     WS /api/v1/stream/news                       │
└─────────────────────────────────────────────────┘
         │                           │
         │ HTTP POST                 │ WebSocket
         ▼                           ▼
┌─────────────────────────────────────────────────┐
│  IBKR TWS MCP Server                             │
├─────────────────────────────────────────────────┤
│  • FastMCP Server (HTTP streaming)               │
│  • WebSocket Handlers (real-time streaming)     │
│  • Shared TWS Client (ib_async)                  │
└─────────────────────────────────────────────────┘
         │
         │ IB Client Protocol
         ▼
┌─────────────────────────────────────────────────┐
│  TWS / IB Gateway                                │
│  (127.0.0.1:7496 or :4001)                      │
└─────────────────────────────────────────────────┘
```

## Quick Start

### 1. Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
TWS_HOST=127.0.0.1
TWS_PORT=7496
TWS_CLIENT_ID=1
TWS_PAPER_ACCOUNT=DU2515295
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
```

### 3. CORS Configuration (Browser Clients)

The server is configured to allow cross-origin requests from browser-based MCP clients:

- **Allowed Origins:** All origins (`*`) - supports external domains like `https://test.lizhao.net`
- **Allowed Methods:** GET, POST, PUT, DELETE, OPTIONS, HEAD
- **Allowed Headers:** All headers including MCP-specific headers (`Mcp-Session-Id`, `Mcp-Initialize-Request`)
- **Credentials:** Enabled for authenticated requests
- **Preflight Cache:** 24 hours

This enables integration with browser-based MCP clients like Goflow without CORS restrictions.

### 4. Start TWS/Gateway

Launch Interactive Brokers TWS or IB Gateway and enable API connections.

### 5. Run the Server

```bash
uv run python main.py
```

### 5. Test the Server

```bash
# Health check
curl http://localhost:8000/health

# MCP tool call (connect to TWS)
curl -X POST http://localhost:8000/api/v1/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "ibkr_connect",
      "arguments": {"host": "127.0.0.1", "port": 7496, "clientId": 1}
    },
    "id": 1
  }'
```

## WebSocket Streaming Examples

### Market Data Stream (Python)

```python
import websockets
import json
import asyncio

async def stream_quotes():
    async with websockets.connect('ws://localhost:8000/api/v1/stream/market-data') as ws:
        # Subscribe to AAPL
        await ws.send(json.dumps({
            "action": "subscribe",
            "symbol": "AAPL",
            "secType": "STK",
            "exchange": "SMART",
            "currency": "USD"
        }))
        
        # Receive real-time updates
        async for message in ws:
            data = json.loads(message)
            if data["type"] == "market_data":
                print(f"{data['symbol']}: ${data['data']['last']}")

asyncio.run(stream_quotes())
```

### Market Data Stream (JavaScript/Browser)

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/stream/market-data');

ws.onopen = () => {
    ws.send(JSON.stringify({
        action: 'subscribe',
        symbol: 'AAPL',
        secType: 'STK'
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'market_data') {
        console.log(`${data.symbol}: $${data.data.last}`);
    }
};
```

For complete examples including portfolio streams and news bulletins, see [HTTP Streaming Examples](./docs/HTTP_STREAMING_EXAMPLES.md).

## MCP Prompts

The server includes 6 comprehensive prompts that provide guided workflows for complex trading operations:

### Portfolio Management
- **setup_trading_workspace** - Complete workspace setup with streaming resources
- **rebalance_portfolio** - Portfolio rebalancing with tax optimization and OCA groups
- **assess_portfolio_risk** - Risk analysis with beta weighting, VaR, and stress testing

### Trading Execution  
- **execute_bracket_order** - Bracket orders with take-profit and stop-loss automation
- **execute_options_strategy** - Options strategies (covered calls, protective puts, collars, etc.)

### Market Analysis
- **analyze_market_conditions** - Multi-dimensional analysis combining technicals, fundamentals, news, and options

Each prompt provides step-by-step workflows with tool call examples, best practices, risk warnings, and sample calculations. See [Prompts Guide](./docs/PROMPTS_GUIDE.md) for details.

## Getting Started

Please refer to the [Setup Guide](./docs/SETUP.md) for detailed instructions on prerequisites, environment configuration, and running the server locally or in a container.

## API Reference

A complete list of all exposed MCP tools, their parameters, and return types can be found in the [API Reference](./docs/API.md).

## Streaming Documentation

- **[HTTP Streaming Migration](./docs/HTTP_STREAMING_MIGRATION.md)** - Migration plan and architecture
- **[HTTP Streaming Examples](./docs/HTTP_STREAMING_EXAMPLES.md)** - Complete client examples
- **[HTTP Streaming Summary](./docs/HTTP_STREAMING_SUMMARY.md)** - Changes and best practices

## End-to-End Testing

The server is designed to support the portfolio rebalancing E2E case. You can test all functionalities using the **Claude MCP Inspector**.

See the dedicated section in the [API Reference](./docs/API.md#2-end-to-end-testing-with-claude-mcp-inspector) for a step-by-step guide on how to use the Inspector to interact with your running server.

## Project Structure

For a detailed explanation of the project organization, see [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md).

```
ibkr-tws-mcp-server/
├── src/                   # Source code
│   ├── server.py          # FastMCP server and tool definitions
│   ├── tws_client.py      # TWS client wrapper using ib_async
│   ├── models.py          # Pydantic data models
│   └── streaming/         # WebSocket streaming handlers
│       ├── websocket_manager.py
│       ├── market_data.py
│       ├── portfolio.py
│       └── news.py
├── tests/                 # Test suite
│   ├── unit/              # Unit tests with mocks
│   └── integration/       # Integration test documentation
├── docs/                  # Documentation
│   ├── API.md             # MCP tools API reference
│   ├── SETUP.md           # Setup and deployment guide
│   ├── HTTP_STREAMING_MIGRATION.md  # Streaming migration plan
│   ├── HTTP_STREAMING_EXAMPLES.md   # Streaming examples
│   ├── HTTP_STREAMING_SUMMARY.md    # Streaming summary
│   └── ...                # Additional guides and troubleshooting
├── diagnostics/           # Diagnostic and testing scripts
├── scripts/               # Utility scripts
├── main.py                # Application entry point
├── pyproject.toml         # Project dependencies
└── README.md              # This file
```

## Documentation

- **[Setup Guide](./docs/SETUP.md)** - Installation and configuration
- **[API Reference](./docs/API.md)** - Complete tool documentation
- **[Prompts Guide](./docs/PROMPTS_GUIDE.md)** - MCP prompts quick reference
- **[Design Document](./docs/Design.md)** - Architecture and design decisions
- **[HTTP Streaming Guide](./docs/HTTP_STREAMING_MIGRATION.md)** - Real-time streaming architecture
- **[Streaming Examples](./docs/HTTP_STREAMING_EXAMPLES.md)** - Client code examples
- **[Project Structure](./PROJECT_STRUCTURE.md)** - Detailed project organization
- **[Migration Guide](./docs/MIGRATION_TO_IB_ASYNC.md)** - ib-insync to ib_async migration
