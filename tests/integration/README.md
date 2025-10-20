# Integration Tests

## Important: MCP Protocol vs REST API

**The IBKR TWS MCP Server tools are NOT exposed as REST endpoints.** They are only accessible via the Model Context Protocol (MCP) using Server-Sent Events (SSE) transport at `/api/v1/sse`.

This means you cannot call tools like this:
```python
# ❌ This will return 404 - tools are not REST endpoints
response = await client.post("/ibkr_connect", json={...})
```

## How to Test the MCP Server

### Option 1: Claude Desktop (Recommended)

1. Start your TWS/IB Gateway
2. Start the MCP server: `uv run python main.py`
3. Configure Claude Desktop to connect to the MCP server (see `docs/SETUP.md`)
4. Test the tools interactively through Claude Desktop

### Option 2: Claude MCP Inspector

1. Start your TWS/IB Gateway
2. Start the MCP server: `uv run python main.py`
3. Visit https://www.claudemcp.com/inspector
4. Connect to `http://localhost:8000/api/v1/sse`
5. Test the tools through the Inspector UI

### Option 3: Custom MCP Client

To programmatically test the server, you would need to:

1. Implement an MCP client using the `mcp` Python package
2. Connect to the SSE endpoint at `/api/v1/sse`
3. Follow the MCP protocol specification for tool calls

Example structure (not implemented):
```python
from mcp import ClientSession
from mcp.client.sse import sse_client

async with sse_client("http://localhost:8000/api/v1/sse") as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool("ibkr_connect", arguments={...})
```

## Current Test Files

### `test_e2e_workflow.py`

This file contains a **manual test workflow** that documents the expected E2E testing process. It is marked with `@pytest.mark.skip` because:

1. MCP tools cannot be called as REST endpoints
2. Proper automated testing requires a full MCP client implementation
3. Manual testing via Claude Desktop or MCP Inspector is more practical

The test serves as **documentation** of the expected workflow:
1. Connect to TWS
2. Get historical data
3. Get positions
4. Get account summary
5. Place orders (paper trading only!)
6. Verify orders and executions
7. Disconnect

## Recommendation

For integration testing of this MCP server:

1. **Unit tests** (in `tests/unit/`) test the TWSClient logic with mocks - these run automatically
2. **Integration tests** should be done manually via Claude Desktop or MCP Inspector
3. If you need automated integration tests, you'll need to implement a proper MCP client

The current approach of using `httpx` to POST to endpoints won't work because FastMCP doesn't expose tools as REST APIs.
