"""Portfolio streaming resource."""

import asyncio
import json
from typing import Dict, Any, Set, Optional
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession
from ..models import AppContext


# Global state for portfolio resources
_portfolio_cache: Dict[str, Dict[str, Any]] = {}
_portfolio_resource_subscriptions: Set[str] = set()
_portfolio_background_streams: Dict[str, asyncio.Task] = {}


def register_portfolio_resource(mcp: FastMCP):
    """Register portfolio streaming resource."""
    
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
