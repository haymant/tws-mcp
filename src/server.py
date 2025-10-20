import os
import asyncio
import json
import uuid
import time
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator, AsyncGenerator, Dict, Any, List, Optional, Set
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.middleware.cors import CORSMiddleware
from ib_async import Contract

from .tws_client import TWSClient
from .models import ContractRequest, OrderRequest

# Load environment variables from .env file
load_dotenv()

@dataclass
class AppContext:
    """Application context with TWS client."""
    tws: TWSClient

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage TWS client lifecycle."""
    tws = TWSClient()
    try:
        # TWS client is initialized but not connected here. Connection is done via the ibkr_connect tool.
        yield AppContext(tws=tws)
    finally:
        # Ensure TWS client is disconnected on shutdown
        if tws.is_connected():
            tws.disconnect()

# Create MCP server with custom streamable HTTP path
mcp = FastMCP(
    "IBKR TWS MCP Server", 
    lifespan=app_lifespan,
    streamable_http_path="/api/v1/mcp"  # Configure the MCP endpoint path
)

# --- Connection Management Tools ---

@mcp.tool()
async def ibkr_connect(
    ctx: Context[ServerSession, AppContext],
    host: str = os.getenv("TWS_HOST", "127.0.0.1"),
    port: int = int(os.getenv("TWS_PORT", 7496)),
    clientId: int = int(os.getenv("TWS_CLIENT_ID", 1))
) -> Dict[str, Any]:
    """Connect to TWS/IB Gateway."""
    tws = ctx.request_context.lifespan_context.tws
    await tws.connect(host, port, clientId)
    return {"status": "connected", "host": host, "port": port, "clientId": clientId}

@mcp.tool()
async def ibkr_disconnect(
    ctx: Context[ServerSession, AppContext]
) -> Dict[str, Any]:
    """Disconnect from TWS/IB Gateway."""
    tws = ctx.request_context.lifespan_context.tws
    tws.disconnect()
    return {"status": "disconnected"}

@mcp.tool()
async def ibkr_get_status(
    ctx: Context[ServerSession, AppContext]
) -> Dict[str, Any]:
    """Get connection status."""
    tws = ctx.request_context.lifespan_context.tws
    return {"is_connected": tws.is_connected()}

# --- Contract and Market Data Tools ---

@mcp.tool()
async def ibkr_search_symbols(
    ctx: Context[ServerSession, AppContext],
    pattern: str
) -> List[Dict[str, Any]]:
    """Search for contracts by partial symbol match.
    
    This uses the TWS symbol search (reqMatchingSymbols) to find contracts
    that match the given pattern. Best for stocks and simple searches.
    
    CUSIP BEHAVIOR:
    - ✅ Works for STOCKS: pattern="037833100" finds AAPL
    - ❌ Doesn't work for BONDS: pattern="912797QF7" returns empty
    - For bonds, use ibkr_get_contract_details with CUSIP instead
    
    LIMITATIONS:
    - Multi-word searches often fail (e.g., "US-T GOVT" returns empty)
    - Keep patterns short and simple (e.g., "US-T" works, "US-T GOVT" doesn't)
    - For bonds, use ibkr_get_contract_details with CUSIP or exact symbol instead
    
    Examples:
    - pattern="AAP" returns contracts like "AAPL", "AAP", etc.
    - pattern="MSFT" returns "MSFT" and related contracts
    - pattern="US-T" returns US Treasury instruments
    - pattern="037833100" returns AAPL (CUSIP works for stocks)
    
    For Treasury Bills/Bonds with known CUSIP, use ibkr_get_contract_details:
    - secType="BOND"
    - symbol=CUSIP (e.g., "912797QF7" for T-Bills)
    
    Args:
        pattern: Partial symbol, company name, or CUSIP (CUSIP only works for stocks)
    
    Returns:
        List of matching contract descriptions with symbol, name, and contract details
    """
    tws = ctx.request_context.lifespan_context.tws
    return await tws.search_symbols(pattern)

@mcp.tool()
async def ibkr_get_contract_details(
    ctx: Context[ServerSession, AppContext],
    symbol: str,
    secType: str = "STK",
    exchange: str = "SMART",
    currency: str = "USD"
) -> List[Dict[str, Any]]:
    """Get detailed contract specifications for an exact symbol.
    
    This retrieves the full contract details for a specific symbol.
    Use ibkr_search_symbols for partial symbol searches.
    
    Args:
        symbol: Exact stock symbol (e.g., "AAPL", "MSFT")
        secType: Security type (STK, OPT, FUT, CASH, BOND, etc.)
        exchange: Exchange (SMART, NYSE, NASDAQ, etc.)
        currency: Currency code (USD, EUR, GBP, etc.)
    
    Returns:
        List of contract details matching the exact symbol
    """
    tws = ctx.request_context.lifespan_context.tws
    req = ContractRequest(symbol=symbol, secType=secType, exchange=exchange, currency=currency)
    return await tws.get_contract_details(req)

@mcp.tool()
async def ibkr_get_historical_data(
    ctx: Context[ServerSession, AppContext],
    symbol: str,
    secType: str = "STK",
    exchange: str = "SMART",
    currency: str = "USD",
    durationStr: str = "1 Y",
    barSizeSetting: str = "1 day",
    whatToShow: str = "TRADES"
) -> List[Dict[str, Any]]:
    """Get historical market data (OHLCV bars) for a contract.
    
    This retrieves historical price bars for technical analysis, backtesting, or charting.
    
    Args:
        symbol: Stock symbol (e.g., "AAPL", "MSFT")
        secType: Security type (STK for stocks, OPT for options, FUT for futures, etc.)
        exchange: Exchange (SMART for smart routing, NYSE, NASDAQ, etc.)
        currency: Currency code (USD, EUR, GBP, etc.)
        durationStr: How far back to retrieve data. Format: "<integer> <unit>"
                     Units: S (seconds), D (days), W (weeks), M (months), Y (years)
                     Examples: "1 D" (1 day), "5 D" (5 days), "1 M" (1 month), "1 Y" (1 year)
        barSizeSetting: Size of each bar. Options include:
                        "1 sec", "5 secs", "10 secs", "15 secs", "30 secs",
                        "1 min", "2 mins", "3 mins", "5 mins", "10 mins", "15 mins", "20 mins", "30 mins",
                        "1 hour", "2 hours", "3 hours", "4 hours", "8 hours",
                        "1 day", "1 week", "1 month"
        whatToShow: Data type to retrieve. Options:
                    "TRADES" (actual trades), "MIDPOINT" (bid-ask midpoint),
                    "BID" (bid prices), "ASK" (ask prices),
                    "BID_ASK" (bid and ask), "HISTORICAL_VOLATILITY",
                    "OPTION_IMPLIED_VOLATILITY"
    
    Returns:
        List of bars with fields: date, open, high, low, close, volume
        
    Example:
        Get daily bars for AAPL for the past year:
        ibkr_get_historical_data("AAPL", "STK", "SMART", "USD", "1 Y", "1 day", "TRADES")
    """
    tws = ctx.request_context.lifespan_context.tws
    req = ContractRequest(symbol=symbol, secType=secType, exchange=exchange, currency=currency)
    return await tws.get_historical_data(req, durationStr, barSizeSetting, whatToShow)

# Long-polling tools removed - use resource-based streaming instead
# See ibkr_start_market_data_resource, ibkr_start_portfolio_resource, ibkr_start_news_resource


# --- Resource-Based Streaming (MCP-Recommended Pattern) ---

# Global state for resource-based market data
_market_data_cache: Dict[str, dict] = {}
_market_data_resource_subscriptions: Set[str] = set()
_resource_background_streams: Dict[str, asyncio.Task] = {}


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


@mcp.tool()
async def ibkr_list_active_resource_streams() -> str:
    """List all active resource-based streams (market data, portfolio, news).
    
    Returns information about all currently streaming resources.
    
    Returns:
        JSON with list of active streams by type
    """
    market_streams = []
    for resource_id in _market_data_resource_subscriptions:
        cache = _market_data_cache.get(resource_id, {})
        task = _resource_background_streams.get(resource_id)
        
        task_status = "unknown"
        if task:
            if task.done():
                task_status = "done"
            elif task.cancelled():
                task_status = "cancelled"
            else:
                task_status = "running"
        
        market_streams.append({
            "resource_id": resource_id,
            "resource_uri": f"ibkr://market-data/{resource_id}",
            "task_status": task_status,
            "last_update": cache.get("timestamp", 0),
            "has_data": bool(cache.get("data")),
            "contract": cache.get("params", {})
        })
    
    portfolio_streams = []
    for account in _portfolio_resource_subscriptions:
        cache = _portfolio_cache.get(account, {})
        task = _portfolio_background_streams.get(account)
        
        task_status = "unknown"
        if task:
            if task.done():
                task_status = "done"
            elif task.cancelled():
                task_status = "cancelled"
            else:
                task_status = "running"
        
        portfolio_streams.append({
            "account": account,
            "resource_uri": f"ibkr://portfolio/{account}",
            "task_status": task_status,
            "last_update": cache.get("timestamp", 0),
            "has_data": bool(cache.get("data"))
        })
    
    news_streams = []
    if _news_resource_subscription:
        cache = _news_cache
        task = _news_background_stream
        
        task_status = "unknown"
        if task:
            if task.done():
                task_status = "done"
            elif task.cancelled():
                task_status = "cancelled"
            else:
                task_status = "running"
        
        news_streams.append({
            "resource_uri": "ibkr://news-bulletins",
            "task_status": task_status,
            "last_update": cache.get("timestamp", 0),
            "bulletin_count": len(cache.get("bulletins", []))
        })
    
    # Tick news streams
    tick_news_streams = []
    for symbol in _tick_news_subscriptions:
        cache = _tick_news_cache.get(symbol, [])
        task = _tick_news_background_tasks.get(symbol)
        
        task_status = "unknown"
        if task:
            if task.done():
                task_status = "done"
            elif task.cancelled():
                task_status = "cancelled"
            else:
                task_status = "running"
        
        tick_news_streams.append({
            "symbol": symbol,
            "resource_uri": f"ibkr://tick-news/{symbol}",
            "task_status": task_status,
            "news_count": len(cache)
        })
    
    # Add "all news" stream if enabled
    if _tick_news_all_stream:
        total_news = sum(len(items) for items in _tick_news_cache.values())
        tick_news_streams.append({
            "symbol": "*",
            "resource_uri": "ibkr://tick-news/*",
            "task_status": "aggregator",
            "news_count": total_news,
            "subscribed_symbols": list(_tick_news_subscriptions)
        })
    
    return json.dumps({
        "market_data": {
            "streams": market_streams,
            "count": len(market_streams)
        },
        "portfolio": {
            "streams": portfolio_streams,
            "count": len(portfolio_streams)
        },
        "news": {
            "streams": news_streams,
            "count": len(news_streams)
        },
        "tick_news": {
            "streams": tick_news_streams,
            "count": len(tick_news_streams)
        },
        "broadtape_news": {
            "subscribed": _broadtape_news_subscribed,
            "resource_uri": "ibkr://broadtape-news" if _broadtape_news_subscribed else None,
            "provider_count": len(_broadtape_provider_tickers),
            "headline_count": len(_broadtape_news_cache),
            "task_status": "running" if _broadtape_news_task and not _broadtape_news_task.done() else "stopped"
        }
    })


# --- Portfolio/Account Resource ---

# Global state for portfolio resources
_portfolio_cache: Dict[str, dict] = {}
_portfolio_resource_subscriptions: Set[str] = set()
_portfolio_background_streams: Dict[str, asyncio.Task] = {}


@mcp.resource("ibkr://portfolio/{account}")
async def get_portfolio_resource(account: str) -> str:
    """Get current portfolio/account updates for an account.
    
    This resource provides real-time portfolio and account value updates.
    
    Usage:
        1. Call ibkr_start_portfolio_resource tool to start streaming
        2. Subscribe to this resource: ibkr://portfolio/{account}
        3. Read resource to get current snapshot
        4. Receive notifications when portfolio/account updates
    
    Args:
        account: Account identifier (e.g., "DU1234567", "U6162000")
        
    Returns:
        JSON string with current portfolio/account data
    """
    if account not in _portfolio_cache:
        return json.dumps({
            "error": f"No data for account {account}",
            "message": f"Call ibkr_start_portfolio_resource('{account}') first to start streaming",
            "subscribed": False
        })
    
    data = _portfolio_cache[account]
    return json.dumps({
        "account": account,
        "subscribed": True,
        "data": data.get("data", {}),
        "last_update": data.get("timestamp", 0)
    })


@mcp.tool()
async def ibkr_start_portfolio_resource(
    ctx: Context[ServerSession, AppContext],
    account: str
) -> str:
    """Start streaming portfolio/account updates to a resource.
    
    This starts a background task that continuously updates the resource
    ibkr://portfolio/{account} with position and account value changes.
    
    Args:
        account: Account identifier (e.g., "DU1234567", "U6162000")
        
    Returns:
        JSON with resource URI and subscription status
    """
    print(f"[PORTFOLIO TOOL] ibkr_start_portfolio_resource called for account: {account}")
    
    tws = ctx.request_context.lifespan_context.tws
    
    if not tws or not tws.is_connected():
        print(f"[PORTFOLIO TOOL] TWS not connected")
        return json.dumps({
            "error": "TWS client not connected",
            "message": "Call ibkr_connect first"
        })
    
    if account in _portfolio_resource_subscriptions:
        print(f"[PORTFOLIO TOOL] Already subscribed to {account}")
        return json.dumps({
            "status": "already_subscribed",
            "resource_uri": f"ibkr://portfolio/{account}",
            "message": f"Portfolio already streaming for {account}"
        })
    
    print(f"[PORTFOLIO TOOL] Initializing cache and starting stream for {account}")
    
    # Initialize cache
    _portfolio_cache[account] = {
        "data": {},
        "timestamp": 0
    }
    
    # Start background streaming task
    async def stream_to_resource():
        """Background task that updates the portfolio resource."""
        print(f"[PORTFOLIO RESOURCE] Starting portfolio stream for {account}")
        
        try:
            async for data in tws.stream_account_updates(account):
                # Log all data received, even empty ones
                print(f"[PORTFOLIO RESOURCE] Received data for {account}: {data}")
                
                if data:
                    # Update cache
                    _portfolio_cache[account]["data"] = data
                    _portfolio_cache[account]["timestamp"] = asyncio.get_event_loop().time()
                    
                    # Notify all subscribed clients
                    await ctx.session.send_resource_updated(f"ibkr://portfolio/{account}")
                    
                    print(f"[PORTFOLIO RESOURCE] Updated {account}: {data.get('type', 'unknown')} - notification sent")
        except asyncio.CancelledError:
            print(f"[PORTFOLIO RESOURCE] Stream cancelled for {account}")
        except Exception as e:
            print(f"[PORTFOLIO RESOURCE] Stream error for {account}: {e}")
            import traceback
            traceback.print_exc()
    
    task = asyncio.create_task(stream_to_resource())
    _portfolio_background_streams[account] = task
    _portfolio_resource_subscriptions.add(account)
    
    print(f"[PORTFOLIO TOOL] Task created and subscribed for {account}")
    
    return json.dumps({
        "status": "subscribed",
        "resource_uri": f"ibkr://portfolio/{account}",
        "message": f"Portfolio streaming started for {account}",
        "account": account
    })


@mcp.tool()
async def ibkr_stop_portfolio_resource(account: str) -> str:
    """Stop streaming portfolio updates to a resource.
    
    Args:
        account: Account identifier to stop streaming
        
    Returns:
        JSON with status
    """
    if account not in _portfolio_background_streams:
        return json.dumps({
            "error": f"No active stream for account {account}",
            "subscribed": False
        })
    
    # Cancel background task
    task = _portfolio_background_streams[account]
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    
    # Cleanup
    del _portfolio_background_streams[account]
    _portfolio_resource_subscriptions.remove(account)
    del _portfolio_cache[account]
    
    print(f"[PORTFOLIO RESOURCE] Stopped stream for {account}")
    
    return json.dumps({
        "status": "stopped",
        "account": account,
        "message": f"Portfolio streaming stopped for {account}"
    })


# --- News Bulletins Resource ---

# Global state for news resource (single instance)
_news_cache: Dict[str, Any] = {"bulletins": [], "timestamp": 0}
_news_resource_subscription: bool = False
_news_background_stream: Optional[asyncio.Task] = None


@mcp.resource("ibkr://news-bulletins")
async def get_news_bulletins_resource() -> str:
    """Get current news bulletins from TWS/IB Gateway.
    
    This resource provides TWS system messages, trading alerts, and account notifications.
    
    Usage:
        1. Call ibkr_start_news_resource tool to start streaming
        2. Subscribe to this resource: ibkr://news-bulletins
        3. Read resource to get current bulletins
        4. Receive notifications when new bulletins arrive
    
    Returns:
        JSON string with news bulletins
    """
    if not _news_resource_subscription:
        return json.dumps({
            "error": "News bulletins not subscribed",
            "message": "Call ibkr_start_news_resource() first to start streaming",
            "subscribed": False
        })
    
    return json.dumps({
        "subscribed": True,
        "bulletins": _news_cache.get("bulletins", []),
        "last_update": _news_cache.get("timestamp", 0),
        "count": len(_news_cache.get("bulletins", []))
    })


@mcp.tool()
async def ibkr_start_news_resource(
    ctx: Context[ServerSession, AppContext],
    allMessages: bool = True
) -> str:
    """Start streaming news bulletins to a resource.
    
    This starts a background task that updates the resource ibkr://news-bulletins
    with TWS/IB Gateway system messages and trading alerts.
    
    Args:
        allMessages: True for all bulletins, False for account-specific only
        
    Returns:
        JSON with resource URI and subscription status
    """
    global _news_resource_subscription, _news_background_stream
    
    tws = ctx.request_context.lifespan_context.tws
    
    if not tws or not tws.is_connected():
        return json.dumps({
            "error": "TWS client not connected",
            "message": "Call ibkr_connect first"
        })
    
    if _news_resource_subscription:
        return json.dumps({
            "status": "already_subscribed",
            "resource_uri": "ibkr://news-bulletins",
            "message": "News bulletins already streaming"
        })
    
    # Initialize cache
    _news_cache["bulletins"] = []
    _news_cache["timestamp"] = 0
    
    # Start background streaming task
    async def stream_to_resource():
        """Background task that updates the news resource."""
        print(f"[NEWS RESOURCE] Starting news bulletins stream (allMessages={allMessages})")
        
        try:
            # Subscribe to news bulletins
            await tws.subscribe_news_bulletins(allMessages)
            
            # Use event-driven approach instead of polling
            # Wait for newsBulletinEvent which fires when news arrives
            while True:
                # Wait for any news bulletin event
                await tws.ib.newsBulletinEvent
                
                # Get all current bulletins
                if hasattr(tws.ib, 'newsBulletins') and tws.ib.newsBulletins():
                    bulletins = list(tws.ib.newsBulletins())
                    
                    # Update cache with all bulletins
                    _news_cache["bulletins"] = [
                        {
                            "msgId": b.msgId,
                            "msgType": b.msgType,
                            "message": b.message,
                            "origExchange": b.origExchange
                        }
                        for b in bulletins
                    ]
                    _news_cache["timestamp"] = asyncio.get_event_loop().time()
                    
                    # Notify clients
                    await ctx.session.send_resource_updated("ibkr://news-bulletins")
                    print(f"[NEWS RESOURCE] Updated with {len(bulletins)} bulletins - notification sent")
                
        except asyncio.CancelledError:
            print(f"[NEWS RESOURCE] Stream cancelled")
        except Exception as e:
            print(f"[NEWS RESOURCE] Stream error: {e}")
            import traceback
            traceback.print_exc()
    
    task = asyncio.create_task(stream_to_resource())
    _news_background_stream = task
    _news_resource_subscription = True
    
    return json.dumps({
        "status": "subscribed",
        "resource_uri": "ibkr://news-bulletins",
        "message": "News bulletins streaming started",
        "allMessages": allMessages
    })


@mcp.tool()
async def ibkr_stop_news_resource() -> str:
    """Stop streaming news bulletins to a resource.
    
    Returns:
        JSON with status
    """
    global _news_resource_subscription, _news_background_stream
    
    if not _news_resource_subscription:
        return json.dumps({
            "error": "No active news bulletins stream",
            "subscribed": False
        })
    
    # Cancel background task
    if _news_background_stream:
        _news_background_stream.cancel()
        try:
            await _news_background_stream
        except asyncio.CancelledError:
            pass
    
    # Cleanup
    _news_background_stream = None
    _news_resource_subscription = False
    _news_cache["bulletins"] = []
    _news_cache["timestamp"] = 0
    
    print(f"[NEWS RESOURCE] Stopped stream")
    
    return json.dumps({
        "status": "stopped",
        "message": "News bulletins streaming stopped"
    })


# --- Tick News (Real-Time Headlines) ---

# Global state for tick news
_tick_news_cache: Dict[str, List[dict]] = {}  # symbol -> list of news items
_tick_news_subscriptions: Set[str] = set()  # Set of subscribed symbols
_tick_news_background_tasks: Dict[str, asyncio.Task] = {}  # symbol -> background task
_tick_news_all_stream: bool = False  # Whether we're streaming all news

@mcp.resource("ibkr://tick-news/{symbol}")
async def get_tick_news_resource(symbol: str) -> str:
    """Get real-time news headlines for a symbol.
    
    This provides the same news you see in TWS Station's News tab.
    Streams breaking news, company announcements, and market-moving headlines.
    
    Special symbol: Use '*' to get all tick news across all subscribed symbols.
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL', 'MSFT') or '*' for all news
        
    Usage:
        1. Call ibkr_start_tick_news_resource tool to subscribe
        2. Subscribe to this resource: ibkr://tick-news/AAPL
        3. Read resource to get recent headlines
        4. Receive notifications when new headlines arrive
    
    Returns:
        JSON string with news headlines
    """
    if symbol == "*":
        # Return all news from all subscribed symbols
        if not _tick_news_all_stream and not _tick_news_subscriptions:
            return json.dumps({
                "error": "No tick news subscriptions active",
                "message": "Call ibkr_start_tick_news_resource() first",
                "subscribed": False
            })
        
        # Aggregate all news
        all_news = []
        for sym, news_list in _tick_news_cache.items():
            for item in news_list:
                item_with_symbol = item.copy()
                item_with_symbol["symbol"] = sym
                all_news.append(item_with_symbol)
        
        # Sort by timestamp descending
        all_news.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        
        return json.dumps({
            "subscribed": True,
            "symbol": "*",
            "news_items": all_news[:100],  # Last 100 items
            "total_count": len(all_news),
            "subscribed_symbols": list(_tick_news_subscriptions)
        })
    
    # Symbol-specific news
    if symbol not in _tick_news_subscriptions:
        return json.dumps({
            "error": f"Not subscribed to tick news for {symbol}",
            "message": f"Call ibkr_start_tick_news_resource(symbol='{symbol}') first",
            "subscribed": False
        })
    
    news_items = _tick_news_cache.get(symbol, [])
    
    return json.dumps({
        "subscribed": True,
        "symbol": symbol,
        "news_items": news_items[-50:],  # Last 50 items
        "count": len(news_items)
    })


@mcp.tool()
async def ibkr_start_tick_news_resource(
    ctx: Context[ServerSession, AppContext],
    symbol: str = "*",
    secType: str = "STK",
    exchange: str = "SMART",
    currency: str = "USD"
) -> str:
    """Start streaming real-time news headlines (like TWS News tab).
    
    This streams breaking news, company announcements, and market headlines.
    Different from news-bulletins which are system messages.
    
    IMPORTANT: symbol='*' only enables aggregation mode. To receive news, you must
    subscribe to actual symbols first (e.g., 'AAPL', 'MSFT'). The '*' aggregates
    news from all subscribed symbols.
    
    Example usage:
        1. ibkr_start_tick_news_resource(symbol='AAPL')  # Subscribe to AAPL
        2. ibkr_start_tick_news_resource(symbol='MSFT')  # Subscribe to MSFT
        3. ibkr_start_tick_news_resource(symbol='*')     # Enable aggregation (optional)
        4. Read ibkr://tick-news/* to get all news from AAPL and MSFT
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL', 'MSFT') or '*' to enable aggregation
        secType: Security type (default: STK)
        exchange: Exchange (default: SMART)
        currency: Currency (default: USD)
        
    Returns:
        JSON with resource URI and subscription status
    """
    global _tick_news_all_stream
    
    tws = ctx.request_context.lifespan_context.tws
    
    if not tws or not tws.is_connected():
        return json.dumps({
            "error": "TWS client not connected",
            "message": "Call ibkr_connect first"
        })
    
    # Handle "all news" subscription
    if symbol == "*":
        if _tick_news_all_stream:
            return json.dumps({
                "status": "already_subscribed",
                "resource_uri": "ibkr://tick-news/*",
                "message": "All tick news aggregation already enabled",
                "subscribed_symbols": list(_tick_news_subscriptions),
                "note": "This aggregates news from subscribed symbols. No new subscriptions created."
            })
        
        _tick_news_all_stream = True
        
        return json.dumps({
            "status": "subscribed",
            "resource_uri": "ibkr://tick-news/*",
            "message": "Aggregation mode enabled. This collects news from all subscribed symbols.",
            "subscribed_symbols": list(_tick_news_subscriptions),
            "note": "To receive news, subscribe to actual symbols: ibkr_start_tick_news_resource(symbol='AAPL')",
            "warning": "No new symbol subscriptions created. Use specific symbols (e.g. 'AAPL') to subscribe."
        })
    
    # Symbol-specific subscription
    if symbol in _tick_news_subscriptions:
        return json.dumps({
            "status": "already_subscribed",
            "resource_uri": f"ibkr://tick-news/{symbol}",
            "message": f"Tick news for {symbol} already streaming"
        })
    
    # Initialize cache for this symbol
    _tick_news_cache[symbol] = []
    
    # Create contract
    from src.models import ContractRequest
    contract_req = ContractRequest(
        symbol=symbol,
        secType=secType,
        exchange=exchange,
        currency=currency
    )
    
    # Start background streaming task
    async def stream_tick_news():
        """Background task that streams tick news for a symbol."""
        print(f"[TICK NEWS] Starting tick news stream for {symbol}")
        
        ticker = None
        try:
            from ib_async import Stock, Forex, Contract
            
            # Create IB contract
            if secType == "STK":
                contract = Stock(symbol, exchange, currency)
            elif secType == "CASH":
                contract = Forex(symbol)
            else:
                contract = Contract(
                    symbol=symbol,
                    secType=secType,
                    exchange=exchange,
                    currency=currency
                )
            
            # Qualify contract
            qualified = await tws.ib.qualifyContractsAsync(contract)
            if not qualified:
                print(f"[TICK NEWS] Failed to qualify contract for {symbol}")
                return
            
            contract = qualified[0]
            
            # Subscribe to market data with news tick
            # genericTickList 292 = news
            ticker = tws.ib.reqMktData(contract, genericTickList='292')
            
            # Set up an asyncio queue and event-driven loop so we behave like
            # the market-data and portfolio streamers (use self.ib.updateEvent)
            news_queue: asyncio.Queue = asyncio.Queue()

            def on_tick_news(news_tick):
                """Handle incoming tick news by enqueueing it for the loop to process."""
                import time

                news_item = {
                    "timestamp": int(time.time()),
                    "time": news_tick.time.isoformat() if hasattr(news_tick, 'time') else None,
                    "providerCode": getattr(news_tick, 'providerCode', None),
                    "articleId": getattr(news_tick, 'articleId', None),
                    "headline": getattr(news_tick, 'headline', None),
                    "extraData": getattr(news_tick, 'extraData', None)
                }

                # Add to cache immediately (helps read resource return latest)
                if symbol not in _tick_news_cache:
                    _tick_news_cache[symbol] = []
                _tick_news_cache[symbol].append(news_item)
                if len(_tick_news_cache[symbol]) > 100:
                    _tick_news_cache[symbol] = _tick_news_cache[symbol][-100:]

                # Enqueue for processing by the async loop
                try:
                    news_queue.put_nowait(news_item)
                except Exception:
                    # If queue is full or closed, drop the item (best-effort)
                    pass

                print(f"[TICK NEWS] {symbol}: {news_item.get('headline', '')[:80]}...")

            # Attach event handler
            ticker.tickNewsEvent += on_tick_news

            # Event-driven processing loop (use same pattern as market data)
            last_notify = 0
            while True:
                # Wait for IB to process events
                await tws.ib.updateEvent

                # Drain the queue
                drained = False
                while not news_queue.empty():
                    item = news_queue.get_nowait()
                    drained = True
                    # Notify subscribed clients (await to ensure errors bubble)
                    await ctx.session.send_resource_updated(f"ibkr://tick-news/{symbol}")
                    if _tick_news_all_stream:
                        await ctx.session.send_resource_updated("ibkr://tick-news/*")

                # If drained anything, small sleep to batch notifications
                if drained:
                    await asyncio.sleep(0.01)
                
        except asyncio.CancelledError:
            print(f"[TICK NEWS] Stream cancelled for {symbol}")
            # Clean up
            if ticker:
                tws.ib.cancelMktData(contract)
        except Exception as e:
            print(f"[TICK NEWS] Stream error for {symbol}: {e}")
            import traceback
            traceback.print_exc()
    
    task = asyncio.create_task(stream_tick_news())
    _tick_news_background_tasks[symbol] = task
    _tick_news_subscriptions.add(symbol)
    
    return json.dumps({
        "status": "subscribed",
        "resource_uri": f"ibkr://tick-news/{symbol}",
        "message": f"Tick news streaming started for {symbol}",
        "contract": {
            "symbol": symbol,
            "secType": secType,
            "exchange": exchange,
            "currency": currency
        }
    })


@mcp.tool()
async def ibkr_stop_tick_news_resource(symbol: str) -> str:
    """Stop streaming tick news for a symbol.
    
    Args:
        symbol: Stock symbol or '*' to stop all
        
    Returns:
        JSON with status
    """
    global _tick_news_all_stream
    
    if symbol == "*":
        # Stop all subscriptions
        for sym in list(_tick_news_subscriptions):
            if sym in _tick_news_background_tasks:
                task = _tick_news_background_tasks[sym]
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                del _tick_news_background_tasks[sym]
            
            _tick_news_subscriptions.discard(sym)
            if sym in _tick_news_cache:
                del _tick_news_cache[sym]
        
        _tick_news_all_stream = False
        
        return json.dumps({
            "status": "stopped",
            "message": "All tick news streams stopped"
        })
    
    if symbol not in _tick_news_subscriptions:
        return json.dumps({
            "error": f"No active tick news stream for {symbol}",
            "subscribed": False
        })
    
    # Cancel background task
    if symbol in _tick_news_background_tasks:
        task = _tick_news_background_tasks[symbol]
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        del _tick_news_background_tasks[symbol]
    
    # Cleanup
    _tick_news_subscriptions.discard(symbol)
    if symbol in _tick_news_cache:
        del _tick_news_cache[symbol]
    
    print(f"[TICK NEWS] Stopped stream for {symbol}")
    
    return json.dumps({
        "status": "stopped",
        "message": f"Tick news streaming stopped for {symbol}"
    })


# --- BroadTape News Resource (All Providers Aggregated) ---

# Global state for broadtape news
_broadtape_news_cache: List[Dict[str, Any]] = []
_broadtape_news_subscribed: bool = False
_broadtape_news_task: Optional[asyncio.Task] = None
_broadtape_provider_tickers: List[Any] = []


@mcp.resource("ibkr://broadtape-news")
async def get_broadtape_news_resource() -> str:
    """Get aggregated real-time news headlines from all subscribed providers.
    
    This resource streams news from ALL available news providers (like BRF, BZ, FLY)
    similar to the TWS News tab. It aggregates BroadTape feeds from all providers
    your account has access to.
    
    Usage:
        1. Call ibkr_start_broadtape_news_resource tool to start streaming
        2. Subscribe to this resource: ibkr://broadtape-news
        3. Read resource to get current headlines
        4. Receive notifications when new headlines arrive from any provider
    
    Returns:
        JSON string with aggregated news headlines from all providers
    """
    if not _broadtape_news_subscribed:
        return json.dumps({
            "error": "BroadTape news not streaming",
            "message": "Call ibkr_start_broadtape_news_resource() first to start streaming",
            "subscribed": False
        })
    
    return json.dumps({
        "subscribed": True,
        "news_items": _broadtape_news_cache[-100:],  # Last 100 headlines
        "total_count": len(_broadtape_news_cache),
        "provider_count": len(_broadtape_provider_tickers)
    })


@mcp.tool()
async def ibkr_start_broadtape_news_resource(
    ctx: Context[ServerSession, AppContext]
) -> str:
    """Start streaming aggregated news headlines from all available providers.
    
    This subscribes to BroadTape feeds from ALL news providers your IB account
    has access to (e.g., Briefing Trader, Benzinga, Fly on the Wall). It mimics
    the TWS News tab by aggregating headlines from all providers into a single stream.
    
    The implementation follows the pattern from NEWS.md:
    1. Query available news providers using reqNewsProviders
    2. Create NEWS contracts for each provider's BroadTape feed (e.g., "BRF:BRF_ALL")
    3. Subscribe via reqMktData with genericTickList="292" for news headlines
    4. Handle tickNewsEvent to capture incoming headlines
    
    Note: This requires active news subscriptions in your IB account.
    Check Client Portal > Settings > Market Data Subscriptions.
    Some providers like BRFG (Briefing.com General) are free by default.
    
    Returns:
        JSON with resource URI and subscription status
    """
    global _broadtape_news_subscribed, _broadtape_news_task, _broadtape_provider_tickers, _broadtape_news_cache
    
    tws = ctx.request_context.lifespan_context.tws
    
    if not tws or not tws.is_connected():
        return json.dumps({
            "error": "TWS client not connected",
            "message": "Call ibkr_connect first"
        })
    
    if _broadtape_news_subscribed:
        return json.dumps({
            "status": "already_subscribed",
            "resource_uri": "ibkr://broadtape-news",
            "message": "BroadTape news already streaming",
            "provider_count": len(_broadtape_provider_tickers)
        })
    
    # Start background streaming task
    async def stream_to_resource():
        """Background task that streams news from all providers."""
        global _broadtape_provider_tickers
        
        print(f"[BROADTAPE NEWS] Starting aggregated news stream")
        
        try:
            # Step 1: Get available news providers
            print(f"[BROADTAPE NEWS] Fetching news providers...")
            providers = await tws.ib.reqNewsProvidersAsync()
            print(f"[BROADTAPE NEWS] Found {len(providers)} providers: {[p.code for p in providers]}")
            
            if not providers:
                print(f"[BROADTAPE NEWS] No news providers available!")
                return
            
            # Create event queue
            event_queue: asyncio.Queue = asyncio.Queue()
            
            # Step 2: Subscribe to BroadTape feed for each provider
            tickers = []
            for provider in providers:
                if provider.code.strip() not in ["BRFG", "FLY", "BZ", "DJ", "DJNL", "DJTOP"]:
                    continue  # For testing, only subscribe to FLY; remove this line to enable all
                try:
                    # For NEWS contracts, use the provider code directly as symbol
                    # Valid codes from IB: BRFG, BRFUPDN, DJ, DJNL, FLY, BZ, DJTOP
                    contract = Contract()
                    contract.symbol = f"{provider.code}:{provider.code}_ALL"  
                    contract.secType = "NEWS"
                    contract.exchange = provider.code
                    
                    print(f"[BROADTAPE NEWS] Subscribing to provider {provider.code}...")
                    
                    # Qualify contract (optional but recommended)
                    qualified = await tws.ib.qualifyContractsAsync(contract)
                    if qualified:
                        contract = qualified[0]
                        contract.exchange = provider.code
                        print(f"[BROADTAPE NEWS] Qualified {provider.code}: conId={contract.conId}, exchange={contract.exchange}")
                    else:
                        print(f"[BROADTAPE NEWS] Could not qualify {provider.code}, trying anyway...")
                    
                    # Subscribe with news tick type (292)
                    ticker = tws.ib.reqMktData(contract, genericTickList='292', snapshot=False, regulatorySnapshot=False)
                    tickers.append((provider.code, ticker))
                    
                    print(f"[BROADTAPE NEWS] Subscribed to {provider.code}")
                    
                except Exception as e:
                    print(f"[BROADTAPE NEWS] Failed to subscribe to {provider.code}: {e}")
            
            if not tickers:
                print(f"[BROADTAPE NEWS] Failed to subscribe to any providers!")
                return
            
            # Store globally for cleanup
            _broadtape_provider_tickers = [t[1] for t in tickers]
            
            # Step 3: Set up event handler for incoming news
            def on_tick_news(ticker, news_tick):
                """Called when news headline arrives from any provider."""
                try:
                    # Find which provider this is from
                    provider_code = None
                    for pcode, pticker in tickers:
                        if pticker == ticker:
                            provider_code = pcode
                            break
                    
                    news_item = {
                        "timestamp": int(time.time()),
                        "providerCode": news_tick.providerCode,
                        "articleId": news_tick.articleId,
                        "headline": news_tick.headline,
                        "source": provider_code or news_tick.providerCode,
                        "time": news_tick.time.isoformat() if news_tick.time else None
                    }
                    
                    event_queue.put_nowait(news_item)
                    print(f"[BROADTAPE NEWS] Queued headline from {provider_code}: {news_tick.headline[:60]}...")
                    
                except Exception as e:
                    print(f"[BROADTAPE NEWS] Error handling news: {e}")
            
            # Create a map of contract IDs to provider codes for filtering
            ticker_map = {ticker.contract.conId: (provider_code, ticker) for provider_code, ticker in tickers}
            
            # Attach single handler to global tickNewsEvent that filters for our contracts
            def global_news_handler(ticker, news_tick):
                if ticker.contract.conId in ticker_map:
                    provider_code, _ = ticker_map[ticker.contract.conId]
                    on_tick_news(ticker, news_tick)
            
            tws.ib.tickNewsEvent += global_news_handler
            print(f"[BROADTAPE NEWS] Attached global news handler for {len(tickers)} providers")
            
            # Step 4: Main event loop
            await asyncio.sleep(1.0)  # Let initial events fire
            
            # Process initial queued events
            while not event_queue.empty():
                news_item = event_queue.get_nowait()
                _broadtape_news_cache.append(news_item)
                await ctx.session.send_resource_updated("ibkr://broadtape-news")
                print(f"[BROADTAPE NEWS] Initial headline: {news_item['headline'][:60]}...")
            
            # Enter main streaming loop
            while True:
                # Wait for IB to process updates
                await tws.ib.updateEvent
                
                # Drain queue and notify
                while not event_queue.empty():
                    news_item = event_queue.get_nowait()
                    _broadtape_news_cache.append(news_item)
                    
                    # Keep cache manageable
                    if len(_broadtape_news_cache) > 1000:
                        _broadtape_news_cache = _broadtape_news_cache[-500:]
                    
                    # Send notification
                    await ctx.session.send_resource_updated("ibkr://broadtape-news")
                    print(f"[BROADTAPE NEWS] New headline from {news_item['source']}: {news_item['headline'][:60]}... - notification sent")
        
        except asyncio.CancelledError:
            print(f"[BROADTAPE NEWS] Stream cancelled")
            # Cleanup tickers
            for ticker in _broadtape_provider_tickers:
                try:
                    tws.ib.cancelMktData(ticker)
                except:
                    pass
        except Exception as e:
            print(f"[BROADTAPE NEWS] Stream error: {e}")
            import traceback
            traceback.print_exc()
    
    # Create and start task
    _broadtape_news_cache = []
    _broadtape_news_task = asyncio.create_task(stream_to_resource())
    _broadtape_news_subscribed = True
    
    return json.dumps({
        "status": "subscribed",
        "resource_uri": "ibkr://broadtape-news",
        "message": "BroadTape news streaming started. Headlines from all providers will be aggregated.",
        "note": "Providers will be discovered automatically. Ensure you have news subscriptions enabled in IB Client Portal."
    })


@mcp.tool()
async def ibkr_stop_broadtape_news_resource(
    ctx: Context[ServerSession, AppContext]
) -> str:
    """Stop streaming aggregated BroadTape news.
    
    Returns:
        JSON with status
    """
    global _broadtape_news_subscribed, _broadtape_news_task, _broadtape_provider_tickers, _broadtape_news_cache
    
    if not _broadtape_news_subscribed:
        return json.dumps({
            "error": "BroadTape news not streaming",
            "subscribed": False
        })
    
    tws = ctx.request_context.lifespan_context.tws
    
    # Cancel background task
    if _broadtape_news_task:
        _broadtape_news_task.cancel()
        try:
            await _broadtape_news_task
        except asyncio.CancelledError:
            pass
        _broadtape_news_task = None
    
    # Cancel all ticker subscriptions
    for ticker in _broadtape_provider_tickers:
        try:
            tws.ib.cancelMktData(ticker)
        except:
            pass
    
    # Cleanup
    _broadtape_news_subscribed = False
    _broadtape_provider_tickers = []
    _broadtape_news_cache = []
    
    print(f"[BROADTAPE NEWS] Stopped stream")
    
    return json.dumps({
        "status": "stopped",
        "message": "BroadTape news streaming stopped"
    })


# --- Account and Portfolio Tools ---

@mcp.tool()
async def ibkr_get_account_summary(
    ctx: Context[ServerSession, AppContext]
) -> List[Dict[str, Any]]:
    """Get overall account summary with key financial metrics.
    
    This retrieves high-level account information including total cash, net liquidation value,
    buying power, margin requirements, and other account-level metrics across all accounts.
    
    Returns:
        List of account summary items, each containing:
        - account: Account identifier
        - tag: Metric name (e.g., "NetLiquidation", "TotalCashValue", "BuyingPower")
        - value: Current value
        - currency: Currency for the value
        
    Common tags returned:
        - NetLiquidation: Total account value
        - TotalCashValue: Total cash balance
        - BuyingPower: Available buying power
        - GrossPositionValue: Total value of all positions
        - AvailableFunds: Funds available for trading
        
    Example use cases:
        - Check account balance before placing orders
        - Monitor margin requirements
        - Calculate portfolio allocation percentages
        - Risk management checks
    """
    tws = ctx.request_context.lifespan_context.tws
    return await tws.get_account_summary()

@mcp.tool()
async def ibkr_get_positions(
    ctx: Context[ServerSession, AppContext]
) -> List[Dict[str, Any]]:
    """Get current portfolio positions across all accounts.
    
    This retrieves all open positions with details about holdings, entry costs, and unrealized P&L.
    Essential for portfolio analysis, rebalancing, and position management.
    
    Returns:
        List of positions, each containing:
        - account: Account holding the position
        - contract: Full contract details (symbol, secType, conId, exchange, currency, etc.)
        - position: Number of shares/contracts held (positive for long, negative for short)
        - avgCost: Average cost per share/contract
        
    Use cases:
        - Portfolio rebalancing: Check current allocations
        - Risk assessment: Identify concentrated positions
        - Tax planning: Review cost basis
        - Order planning: Determine position sizes before closing trades
        - Multi-account management: See positions across all accounts
        
    Example:
        positions = ibkr_get_positions()
        # Filter for AAPL positions
        aapl_positions = [p for p in positions if p['contract']['symbol'] == 'AAPL']
    """
    tws = ctx.request_context.lifespan_context.tws
    return await tws.get_positions()

# Account updates polling tools removed - use resource-based streaming instead


@mcp.tool()
async def ibkr_get_pnl(
    ctx: Context[ServerSession, AppContext],
    account: str,
    modelCode: str = ''
) -> Dict[str, Any]:
    """Get overall Profit and Loss for an entire account.
    
    This retrieves aggregated P&L metrics across all positions in the account.
    Provides real-time unrealized P&L, daily realized P&L, and total P&L.
    
    Args:
        account: Account identifier (e.g., "DU1234567", "U6162000")
        modelCode: Optional model code for multi-model accounts (default: '' for all models)
        
    Returns:
        Dict containing P&L metrics:
        - account: Account identifier
        - modelCode: Model code (if applicable)
        - dailyPnL: Realized + unrealized P&L for today
        - unrealizedPnL: Current unrealized profit/loss
        - realizedPnL: Today's realized profit/loss from closed trades
        
    Use cases:
        - Daily performance monitoring
        - Risk management: Check if losses exceed limits
        - Trading journal: Record daily P&L
        - Dashboard displays: Show real-time account performance
        
    Important:
        - Subscribes to P&L updates and waits for initial data (5 second timeout)
        - Requires the account to have open positions for P&L data
        - If account has no positions, will timeout with an error
        - Use ibkr_get_positions() first to verify positions exist
        - Use ibkr_get_pnl_single() for position-specific P&L
        
    Example:
        # Check if account has positions first
        positions = ibkr_get_positions()
        if positions:
            pnl = ibkr_get_pnl("U6162000")
            if pnl['dailyPnL'] and pnl['dailyPnL'] < -1000:
                # Alert: Daily loss exceeds $1000
    """
    tws = ctx.request_context.lifespan_context.tws
    return await tws.get_pnl(account, modelCode)

@mcp.tool()
async def ibkr_get_pnl_single(
    ctx: Context[ServerSession, AppContext],
    account: str,
    modelCode: str = '',
    conId: int = 0
) -> Dict[str, Any]:
    """Get Profit and Loss for a specific position (contract).
    
    This retrieves detailed P&L metrics for a single position identified by contract ID.
    More granular than ibkr_get_pnl(), useful for position-level performance tracking.
    
    Args:
        account: Account identifier (e.g., "DU1234567", "U6162000")
        modelCode: Optional model code for multi-model accounts (default: '' for all models)
        conId: Contract ID (conId) of the position to query
                MUST be a contract you currently hold a position in
                Get conId from ibkr_get_positions() or ibkr_get_contract_details()
        
    Returns:
        Dict containing position-specific P&L:
        - account: Account identifier
        - modelCode: Model code (if applicable)
        - conId: Contract ID
        - position: Current position size (shares/contracts held)
        - dailyPnL: Today's realized + unrealized P&L for this position
        - unrealizedPnL: Current unrealized profit/loss
        - realizedPnL: Today's realized P&L from partial closes
        - value: Current market value of the position
        
    Use cases:
        - Track performance of individual holdings
        - Identify best/worst performers
        - Calculate position-level returns
        - Trigger exit rules based on position P&L (stop-loss, take-profit)
        
    Important:
        - Subscribes to P&L updates and waits for initial data (5 second timeout)
        - MUST provide conId for a position you currently hold
        - If no position exists for conId, will timeout with an error
        - Use ibkr_get_positions() first to get valid conIds
        - Position value of 0 means no active position for this contract
        
    Example:
        # Get conId from positions
        positions = ibkr_get_positions()
        if positions:
            aapl_pos = next((p for p in positions 
                           if p['contract']['symbol'] == 'AAPL'), None)
            if aapl_pos:
                aapl_conId = aapl_pos['contract']['conId']
                # Get P&L for AAPL position
                aapl_pnl = ibkr_get_pnl_single("U6162000", "", aapl_conId)
                print(f"AAPL unrealized P&L: ${aapl_pnl['unrealizedPnL']}")
    """
    tws = ctx.request_context.lifespan_context.tws
    return await tws.get_pnl_single(account, modelCode, conId)

# --- Order Management Tools ---

@mcp.tool()
async def ibkr_place_order(
    ctx: Context[ServerSession, AppContext],
    symbol: str,
    action: str,
    totalQuantity: int,
    orderType: str = "MKT",
    lmtPrice: Optional[float] = None,
    secType: str = "STK",
    exchange: str = "SMART",
    currency: str = "USD"
) -> Dict[str, Any]:
    """Place a buy or sell order for a security.
    
    This submits an order to TWS/Gateway for execution. Supports market and limit orders.
    Returns order details including assigned order ID for tracking and cancellation.
    
    Args:
        symbol: Stock symbol (e.g., "AAPL", "MSFT")
        action: Order side - "BUY" or "SELL"
        totalQuantity: Number of shares/contracts to trade
        orderType: "MKT" for market order, "LMT" for limit order (default: "MKT")
        lmtPrice: Limit price (required for "LMT" orders, ignored for "MKT")
        secType: Security type (STK for stocks, OPT for options, etc.)
        exchange: Exchange (SMART for smart routing, NYSE, NASDAQ, etc.)
        currency: Currency code (USD, EUR, GBP, etc.)
        
    Returns:
        Dict with order confirmation:
        - orderId: Unique order ID for tracking/cancellation
        - status: Order status (e.g., "Submitted", "Filled", "Cancelled")
        - contract: Contract details
        - action: BUY or SELL
        - quantity: Order size
        
    Use cases:
        - Portfolio rebalancing: Execute buy/sell orders to target allocations
        - Automated trading: Place orders based on signals
        - Manual trading: Execute planned trades
        - Liquidation: Close positions
        
    Important:
        - Orders are LIVE and will execute in your account
        - Use ibkr_get_account_summary() to check buying power first
        - Market orders execute immediately at current market price
        - Limit orders only fill at specified price or better
        - Save orderId to cancel or track the order later
        
    Examples:
        # Market order: Buy 100 shares of AAPL
        ibkr_place_order("AAPL", "BUY", 100, "MKT")
        
        # Limit order: Sell 50 shares of MSFT at $350
        ibkr_place_order("MSFT", "SELL", 50, "LMT", lmtPrice=350.0)
    """
    tws = ctx.request_context.lifespan_context.tws
    order_req = OrderRequest(
        contract=ContractRequest(
            symbol=symbol,
            secType=secType,
            exchange=exchange,
            currency=currency
        ),
        action=action,
        totalQuantity=totalQuantity,
        orderType=orderType,
        lmtPrice=lmtPrice
    )
    return await tws.place_order(order_req)

@mcp.tool()
async def ibkr_cancel_order(
    ctx: Context[ServerSession, AppContext],
    orderId: int
) -> Dict[str, Any]:
    """Cancel a pending order by its order ID.
    
    This sends a cancellation request for an open order. Only works for orders
    that have not yet been filled or already cancelled.
    
    Args:
        orderId: The order ID returned from ibkr_place_order() or ibkr_get_open_orders()
        
    Returns:
        Dict with cancellation status:
        - orderId: The cancelled order's ID
        - status: New order status (e.g., "Cancelled", "PendingCancel")
        - message: Confirmation message
        
    Use cases:
        - Cancel orders that are no longer needed
        - Replace orders: Cancel old order, place new one
        - Risk management: Cancel all orders in emergencies
        - Strategy adjustment: Cancel unfilled limit orders
        
    Important:
        - Only unfilled or partially filled orders can be cancelled
        - Fully filled orders cannot be cancelled (use reverse order to exit)
        - Cancellation is not instant - check status with ibkr_get_open_orders()
        - "PendingCancel" means cancellation is processing
        
    Workflow:
        1. Get order ID from ibkr_place_order() or ibkr_get_open_orders()
        2. Call ibkr_cancel_order(orderId)
        3. Verify cancellation with ibkr_get_open_orders()
        
    Example:
        # Cancel order 12345
        result = ibkr_cancel_order(12345)
        print(f"Order {result['orderId']} status: {result['status']}")
    """
    tws = ctx.request_context.lifespan_context.tws
    return await tws.cancel_order(orderId)

@mcp.tool()
async def ibkr_get_open_orders(
    ctx: Context[ServerSession, AppContext]
) -> List[Dict[str, Any]]:
    """Get all currently open (active) orders across all accounts.
    
    This retrieves all orders that have been submitted but not yet filled or cancelled.
    Essential for order management, monitoring, and preventing duplicate orders.
    
    Returns:
        List of open orders, each containing:
        - orderId: Unique order identifier (use for cancellation)
        - status: Current status (e.g., "Submitted", "PreSubmitted", "PendingSubmit")
        - contract: Full contract details (symbol, secType, exchange, etc.)
        - action: BUY or SELL
        - quantity: Order size
        
    Order statuses:
        - "PreSubmitted": Order created but not yet sent to exchange
        - "Submitted": Order active on exchange
        - "Filled": Fully executed (won't appear in results)
        - "Cancelled": Cancelled (won't appear in results)
        - "PendingSubmit": Order being submitted
        - "PendingCancel": Cancellation in progress
        
    Use cases:
        - Check if orders are still active before placing duplicates
        - Monitor unfilled limit orders
        - Cancel all orders: iterate and call ibkr_cancel_order()
        - Reconcile trading strategy: verify expected orders exist
        - Debug: Check why orders aren't filling
        
    Important:
        - Only returns OPEN orders (excludes filled and cancelled)
        - Returns orders from ALL accounts accessible in session
        - Order IDs are unique and never reused
        
    Example:
        orders = ibkr_get_open_orders()
        # Find all AAPL buy orders
        aapl_buys = [o for o in orders 
                     if o['contract']['symbol'] == 'AAPL' and o['action'] == 'BUY']
        
        # Cancel all open orders
        for order in orders:
            ibkr_cancel_order(order['orderId'])
    """
    tws = ctx.request_context.lifespan_context.tws
    return await tws.get_open_orders()

@mcp.tool()
async def ibkr_get_executions(
    ctx: Context[ServerSession, AppContext]
) -> List[Dict[str, Any]]:
    """Get all trade executions (fills) for the current session.
    
    This retrieves the execution history showing when and how orders were filled.
    Each execution represents an actual trade that occurred on the exchange.
    One order can result in multiple executions if filled in parts.
    
    Returns:
        List of executions, each containing:
        - execId: Unique execution identifier
        - orderId: Associated order ID
        - time: Execution timestamp
        - symbol: Symbol traded
        - side: BUY or SELL
        - shares: Number of shares filled
        - price: Execution price
        - exchange: Exchange where trade occurred
        - cumQty: Cumulative quantity filled for the order
        - avgPrice: Average fill price across all executions
        
    Use cases:
        - Verify order fills: Confirm trades executed as expected
        - Calculate transaction costs: Sum execution prices and fees
        - Trading journal: Record all trades with exact fill details
        - Performance analysis: Track actual fill prices vs expected
        - Reconciliation: Match executions to position changes
        - Audit trail: Document all trading activity
        
    Important:
        - Returns executions from current TWS/Gateway session only
        - Historical executions from previous sessions not included
        - Partial fills create multiple execution records
        - Use orderId to group executions belonging to same order
        
    Example:
        executions = ibkr_get_executions()
        
        # Calculate total shares bought today
        total_bought = sum(e['shares'] for e in executions if e['side'] == 'BUY')
        
        # Find executions for a specific order
        order_fills = [e for e in executions if e['orderId'] == 12345]
        avg_price = sum(e['price'] * e['shares'] for e in order_fills) / sum(e['shares'] for e in order_fills)
    """
    tws = ctx.request_context.lifespan_context.tws
    return await tws.get_executions()

# --- News Tools ---

@mcp.tool()
async def ibkr_get_news_providers(
    ctx: Context[ServerSession, AppContext]
) -> List[Dict[str, Any]]:
    """Get available news providers.
    
    Returns a list of news provider codes (e.g., 'DJ' for Dow Jones, 'REU' for Reuters)
    that can be used with ibkr_get_historical_news.
    
    Returns:
        List of news providers with code and name
    """
    tws = ctx.request_context.lifespan_context.tws
    return await tws.get_news_providers()

@mcp.tool()
async def ibkr_get_historical_news(
    ctx: Context[ServerSession, AppContext],
    symbol: str,
    providerCodes: str,
    startDateTime: str,
    endDateTime: str,
    totalResults: int = 100,
    secType: str = "STK",
    exchange: str = "SMART",
    currency: str = "USD"
) -> List[Dict[str, Any]]:
    """Get historical news headlines for a contract.
    
    Requires news subscriptions (e.g., Reuters, Dow Jones) in your IB account.
    Check available providers using ibkr_get_news_providers first.
    
    Args:
        symbol: Stock/commodity symbol (e.g., "AAPL", "XAUUSD")
        providerCodes: Comma-separated provider codes (e.g., "DJ-N,FLY,BRFG" or "DJ-N")
        startDateTime: Start date/time in format "YYYYMMDD HH:MM:SS" (e.g., "20251001 00:00:00")
        endDateTime: End date/time in format "YYYYMMDD HH:MM:SS" (e.g., "20251018 23:59:59")
        totalResults: Maximum number of headlines to return (default 100)
        secType: Security type (STK, CMDTY, etc.)
        exchange: Exchange (SMART, etc.)
        currency: Currency code
    
    Returns:
        List of historical news headlines with time, provider, headline, and article ID
    """
    tws = ctx.request_context.lifespan_context.tws
    req = ContractRequest(symbol=symbol, secType=secType, exchange=exchange, currency=currency)
    return await tws.get_historical_news(req, providerCodes, startDateTime, endDateTime, totalResults)

@mcp.tool()
async def ibkr_get_news_article(
    ctx: Context[ServerSession, AppContext],
    providerCode: str,
    articleId: str
) -> Dict[str, Any]:
    """Get the full text of a news article.
    
    Use the articleId from ibkr_get_historical_news or real-time news updates.
    
    Args:
        providerCode: News provider code (e.g., "REU", "DJ")
        articleId: Article ID from news headline
    
    Returns:
        Full article with headline and body text
    """
    tws = ctx.request_context.lifespan_context.tws
    return await tws.get_news_article(providerCode, articleId)

# News bulletins polling tools removed - use resource-based streaming instead



# --- Starlette App Setup ---

# Import streaming modules
from starlette.websockets import WebSocket
from starlette.responses import JSONResponse
from starlette.routing import WebSocketRoute, Route
from .streaming import StreamingManager, market_data_stream, portfolio_stream, news_stream

# Old long-polling infrastructure removed - using MCP Resources pattern instead

# Create streaming manager
streaming_manager = StreamingManager()

# Store TWS client reference for streaming endpoints (accessed via app state)
_tws_client: TWSClient = None

def set_tws_client(tws: TWSClient):
    """Set the TWS client for streaming endpoints."""
    global _tws_client
    _tws_client = tws

def get_tws_client() -> TWSClient:
    """Get the TWS client for streaming endpoints."""
    return _tws_client

# WebSocket wrapper functions that inject dependencies
async def _market_data_ws(websocket: WebSocket):
    """WebSocket handler for market data with dependency injection."""
    await market_data_stream(websocket, get_tws_client(), streaming_manager)

async def _portfolio_ws(websocket: WebSocket):
    """WebSocket handler for portfolio with dependency injection."""
    await portfolio_stream(websocket, get_tws_client(), streaming_manager)

async def _news_ws(websocket: WebSocket):
    """WebSocket handler for news with dependency injection."""
    await news_stream(websocket, get_tws_client(), streaming_manager)

# Health check endpoint
async def health_check(request):
    """Health check endpoint."""
    tws = get_tws_client()
    is_connected = tws.is_connected() if tws else False
    
    return JSONResponse({
        "status": "healthy",
        "service": "IBKR TWS MCP Server",
        "tws_connected": is_connected,
        "endpoints": {
            "mcp": "POST /api/v1/mcp",
            "health": "GET /health",
            "streaming": {
                "market_data": "ws://host:port/api/v1/stream/market-data",
                "portfolio": "ws://host:port/api/v1/stream/portfolio",
                "news": "ws://host:port/api/v1/stream/news"
            }
        },
        "usage": {
            "mcp_tools": "Use MCP client to call tools via POST /api/v1/mcp (supports streaming responses)",
            "streaming": "Use WebSocket clients to connect to /api/v1/stream/* endpoints"
        }
    })

# Get the MCP Streamable HTTP app
# This returns a Starlette app with its own lifespan that initializes the task group
# We'll use this as the base and add our custom routes to it
mcp_base_app = mcp.streamable_http_app()

# Add our custom routes to the MCP app
# The MCP app already has the /mcp endpoint configured
mcp_base_app.routes.extend([
    # Health check
    Route("/health", health_check),
    
    # WebSocket streaming endpoints
    WebSocketRoute("/api/v1/stream/market-data", _market_data_ws),
    WebSocketRoute("/api/v1/stream/portfolio", _portfolio_ws),
    WebSocketRoute("/api/v1/stream/news", _news_ws),
])

# Enhanced lifespan that combines MCP's task group initialization with our TWS setup
@asynccontextmanager
async def combined_lifespan(app_instance):
    """Combined lifespan that initializes both MCP task group and TWS client."""
    tws = TWSClient()
    try:
        # Set TWS client for streaming endpoints
        set_tws_client(tws)
        
        # Get the MCP session manager and run it (initializes task group)
        async with mcp.session_manager.run():
            yield
    finally:
        # Ensure TWS client is disconnected on shutdown
        if tws.is_connected():
            tws.disconnect()

# Replace the lifespan context - this combines MCP's task group init with our TWS setup
mcp_base_app.router.lifespan_context = combined_lifespan

# Use the MCP base app as wrapped_app (no need for additional wrapping)
wrapped_app = mcp_base_app

# Add CORS middleware
app = CORSMiddleware(
    wrapped_app,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Mcp-Session-Id"],
)

# Main entry point for uvicorn
if __name__ == "__main__":
    import uvicorn
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", 8000))
    uvicorn.run(app, host=host, port=port)
