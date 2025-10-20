# Diagnostic Scripts

This directory contains diagnostic and testing scripts used during development and troubleshooting.

## TWS Connection Testing

### `test_tws_connection.py`
Full diagnostic tool for testing TWS/IB Gateway connections with verbose logging.
```bash
# Test with default settings (port 7496)
uv run python diagnostics/test_tws_connection.py

# Test with custom port (paper trading)
uv run python diagnostics/test_tws_connection.py --port 7497

# Test with specific client ID
uv run python diagnostics/test_tws_connection.py --client-id 2
```

### `test_minimal_tws.py`
Minimal TWS API connection test - simplest possible check.
```bash
uv run python diagnostics/test_minimal_tws.py
```

## Event Loop Debugging

These scripts were used to diagnose and fix event loop issues:

- **`check_ib_loop_attrs.py`** - Inspect IB instance for loop-related attributes
- **`check_ib_client_loop.py`** - Check IB.client for loop references
- **`inspect_ib_structure.py`** - Detailed inspection of IB instance structure
- **`verify_loop_fix.py`** - Verify the event loop fix works across different loops

## MCP Server Testing

Scripts for testing the FastMCP server setup:

- **`test_fastmcp_methods.py`** - Check available FastMCP methods
- **`test_mcp_http_app.py`** - Inspect FastMCP HTTP app structure
- **`test_sse_app.py`** - Check SSE app configuration
- **`test_server_endpoints.py`** - Test server endpoint availability
- **`quick_test.py`** - Quick endpoint availability test
- **`runtime_check.py`** - Runtime verification of server startup
- **`test_runtime_quick.py`** - Quick runtime test with connection attempt
- **`final_test.py`** - Final verification test
- **`verify_setup.py`** - Comprehensive setup verification

## Usage Notes

These scripts are primarily for:
1. **Troubleshooting** - Diagnosing connection or configuration issues
2. **Development** - Testing changes during development
3. **Documentation** - Examples of how to use ib_async and FastMCP APIs

Most users should use the main test suite instead:
```bash
# Run unit tests
uv run pytest tests/unit/ -v

# Run specific test
uv run pytest tests/unit/test_tws_client.py -v
```

For production testing, use the main server with Claude Desktop or MCP Inspector (see `docs/SETUP.md`).
