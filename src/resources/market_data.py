"""Market data streaming resource."""

import asyncio
import json
from typing import Dict, Any, Set, Optional
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession
from ..models import AppContext, ContractRequest


# Global state for market data resources
_market_data_cache: Dict[str, Dict[str, Any]] = {}
_market_data_resource_subscriptions: Set[str] = set()
_resource_background_streams: Dict[str, asyncio.Task] = {}


def register_market_data_resource(mcp: FastMCP):
    """Register market data streaming resource."""
    
    @mcp.resource("ibkr://market-data/{resource_id}")
    async def get_market_data_resource(resource_id: str) -> str:
        """Get current market data snapshot for a symbol.
        
        This resource provides real-time market data that updates automatically.
        Subscribe to this resource to receive notifications when data changes.
        
        Resource ID format:
        - Stocks: Just the symbol (e.g., "AAPL", "MSFT")
        - Forex: symbol.currency (e.g., "USD.JPY", "EUR.USD", "USD.SGD")
        - Others: symbol or symbol.identifier as appropriate
        
        Usage:
            1. Call ibkr_start_market_data_resource tool to start streaming
            2. Subscribe to this resource: ibkr://market-data/{resource_id}
            3. Read resource to get current snapshot
            4. Receive notifications when data updates
            5. Re-read resource when notified to get latest data
        
        Args:
            resource_id: Resource identifier (e.g., "AAPL", "USD.JPY", "EUR.USD")
            
        Returns:
            JSON string with current market data or error message
        """
        print(f"[RESOURCE READ] Requested resource_id: '{resource_id}'")
        print(f"[RESOURCE READ] Cache keys: {list(_market_data_cache.keys())}")
        
        if resource_id not in _market_data_cache:
            return json.dumps({
                "error": f"No data for {resource_id}",
                "message": f"Call ibkr_start_market_data_resource() first to start streaming this resource",
                "subscribed": False
            })
        
        data = _market_data_cache[resource_id]
        return json.dumps({
            "resource_id": resource_id,
            "subscribed": True,
            "data": data.get("data", {}),
            "last_update": data.get("timestamp", 0),
            "contract": data.get("params", {})
        })
    
    @mcp.tool()
    async def ibkr_start_market_data_resource(
        ctx: Context[ServerSession, AppContext],
        symbol: str,
        secType: str = "STK",
        exchange: str = "SMART",
        currency: str = "USD"
    ) -> str:
        """Start streaming market data to a resource.
        
        This starts a background task that continuously updates the resource
        ibkr://market-data/{resource_id}. Clients can subscribe to the resource
        to receive notifications when data changes.
        
        Resource ID format:
        - Stocks (STK): Just the symbol (e.g., "AAPL" → ibkr://market-data/AAPL)
        - Forex (CASH): symbol.currency (e.g., "USD" + "JPY" → ibkr://market-data/USD.JPY)
        - Others: symbol or symbol.identifier
        
        This is the MCP-recommended pattern for streaming data - much more
        efficient than polling!
        
        Args:
            symbol: Stock/currency symbol (e.g., "AAPL", "USD", "EUR")
            secType: Security type (STK, OPT, FUT, CASH, BOND, etc.)
            exchange: Exchange (SMART for smart routing, IDEALPRO for forex, etc.)
            currency: Currency code (USD, EUR, GBP, JPY, SGD, etc.)
            
        Returns:
            JSON with resource URI and subscription status
            
        Example workflows:
            # Stock: Apple
            result = ibkr_start_market_data_resource("AAPL", "STK", "SMART", "USD")
            // Resource: ibkr://market-data/AAPL
            
            # Forex: USD/JPY
            result = ibkr_start_market_data_resource("USD", "CASH", "IDEALPRO", "JPY")
            // Resource: ibkr://market-data/USD.JPY
            
            # Forex: EUR/USD
            result = ibkr_start_market_data_resource("EUR", "CASH", "IDEALPRO", "USD")
            // Resource: ibkr://market-data/EUR.USD
        """
        tws = ctx.request_context.lifespan_context.tws
        
        if not tws or not tws.is_connected():
            return json.dumps({
                "error": "TWS client not connected",
                "message": "Call ibkr_connect first"
            })
        
        # Create resource ID: for CASH (forex), use symbol.currency format
        # For stocks and others, just use symbol
        if secType == "CASH":
            resource_id = f"{symbol}.{currency}"
        else:
            resource_id = symbol
        
        if resource_id in _market_data_resource_subscriptions:
            return json.dumps({
                "status": "already_subscribed",
                "resource_uri": f"ibkr://market-data/{resource_id}",
                "message": f"Market data already streaming for {resource_id}"
            })
        
        # Initialize cache
        _market_data_cache[resource_id] = {
            "data": {},
            "timestamp": 0,
            "params": {
                "symbol": symbol,
                "secType": secType,
                "exchange": exchange,
                "currency": currency
            }
        }
        
        # Start background streaming task
        async def stream_to_resource():
            """Background task that updates the resource and sends notifications."""
            req = ContractRequest(symbol=symbol, secType=secType, exchange=exchange, currency=currency)
            print(f"[RESOURCE] Starting market data stream for {resource_id} ({symbol}/{currency})")
            print(f"[RESOURCE] TWS connected: {tws.is_connected()}")
            
            try:
                print(f"[RESOURCE] Entering async for loop for {resource_id}")
                async for data in tws.stream_market_data(req):
                    print(f"[RESOURCE] Received data for {resource_id}: {data}")
                    if data:
                        # Update cache
                        _market_data_cache[resource_id]["data"] = data
                        _market_data_cache[resource_id]["timestamp"] = asyncio.get_event_loop().time()
                        
                        # Notify all subscribed clients that resource changed
                        await ctx.session.send_resource_updated(f"ibkr://market-data/{resource_id}")
                        
                        print(f"[RESOURCE] Updated {resource_id}: {list(data.keys())} - notification sent")
            except asyncio.CancelledError:
                print(f"[RESOURCE] Stream cancelled for {resource_id}")
            except Exception as e:
                print(f"[RESOURCE] Stream error for {resource_id}: {e}")
                import traceback
                traceback.print_exc()
        
        task = asyncio.create_task(stream_to_resource())
        _resource_background_streams[resource_id] = task
        _market_data_resource_subscriptions.add(resource_id)
        
        return json.dumps({
            "status": "subscribed",
            "resource_uri": f"ibkr://market-data/{resource_id}",
            "resource_id": resource_id,
            "message": f"Market data streaming started. Subscribe to resource 'ibkr://market-data/{resource_id}' to receive updates.",
            "contract": {
                "symbol": symbol,
                "secType": secType,
                "exchange": exchange,
                "currency": currency
            }
        })
    
    @mcp.tool()
    async def ibkr_stop_market_data_resource(resource_id: str) -> str:
        """Stop streaming market data to a resource.
        
        Cancels the background task and clears cached data for a resource.
        
        Args:
            resource_id: Resource identifier (e.g., "AAPL", "USD.JPY", "EUR.USD")
            
        Returns:
            JSON with status
        """
        if resource_id not in _resource_background_streams:
            return json.dumps({
                "error": f"No active stream for {resource_id}",
                "subscribed": False
            })
        
        # Cancel background task
        task = _resource_background_streams[resource_id]
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Cleanup
        del _resource_background_streams[resource_id]
        _market_data_resource_subscriptions.remove(resource_id)
        del _market_data_cache[resource_id]
        
        print(f"[RESOURCE] Stopped stream for {resource_id}")
        
        return json.dumps({
            "status": "stopped",
            "resource_id": resource_id,
            "message": f"Market data streaming stopped for {resource_id}"
        })
