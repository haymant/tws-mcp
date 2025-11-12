"""
Integration test for IBKR TWS MCP Server E2E workflow.

NOTE: This test requires:
1. A running IBKR TWS MCP Server instance (started separately)
2. A running TWS/IB Gateway instance connected to a paper trading account
3. The MCP server must be accessible via the Claude Desktop MCP Inspector or similar client

This test is designed to be run manually with real MCP clients (like Claude Desktop),
not as an automated pytest. The pytest framework is used for structure, but execution
requires manual setup.

To run this test:
1. Start your TWS/IB Gateway
2. Start the MCP server: `uv run python main.py`
3. Connect using Claude Desktop or the MCP Inspector
4. Test the workflow manually by calling the tools in order

Automated E2E testing of MCP servers over SSE requires a proper MCP client implementation,
which is beyond the scope of simple pytest tests.
"""

import pytest
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

@pytest.mark.skip(reason="This is a manual test requiring running MCP server and TWS instance")
@pytest.mark.asyncio
async def test_portfolio_rebalancing_workflow():
    """
    Manual test workflow for portfolio rebalancing.
    
    This test documents the expected workflow but is marked as skip because:
    1. MCP tools are only accessible via SSE, not as REST endpoints
    2. Proper testing requires an MCP client implementation
    3. Integration testing is better done via Claude Desktop or MCP Inspector
    
    Workflow steps:
    1. Call ibkr_connect with TWS connection details
    2. Call ibkr_get_historical_data for symbols (e.g., VTI)
    3. Call ibkr_get_positions to see current holdings
    4. Call ibkr_get_account_summary for account info
    5. Call ibkr_place_order to place test orders (in paper trading!)
    6. Call ibkr_get_open_orders to verify orders
    7. Call ibkr_get_executions to see filled orders
    8. Call ibkr_disconnect to close connection
    """
    
    TWS_HOST = os.getenv("TWS_HOST", "127.0.0.1")
    TWS_PORT = int(os.getenv("TWS_PORT", 7497))
    TWS_CLIENT_ID = int(os.getenv("TWS_CLIENT_ID", 1))
    
    print("=" * 60)
    print("MANUAL E2E TEST WORKFLOW")
    print("=" * 60)
    print(f"\nTWS Configuration:")
    print(f"  Host: {TWS_HOST}")
    print(f"  Port: {TWS_PORT}")
    print(f"  Client ID: {TWS_CLIENT_ID}")
    print("\nTo test manually:")
    print("1. Start TWS/IB Gateway")
    print("2. Start MCP server: uv run python main.py")
    print("3. Connect using Claude Desktop or MCP Inspector")
    print("4. Follow the workflow steps documented in the test docstring")
    print("=" * 60)

