"""Connection management tools for IBKR TWS API."""

import os
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession

try:
    from ..models import AppContext
except ImportError:
    from src.models import AppContext


def register_connection_tools(mcp: FastMCP):
    """Register connection management tools."""
    
    @mcp.tool()
    async def ibkr_connect(
        ctx: Context[ServerSession, AppContext],
        host: str = os.getenv("TWS_HOST", "127.0.0.1"),
        port: int = int(os.getenv("TWS_PORT", 7497)),
        clientId: int = int(os.getenv("TWS_CLIENT_ID", 1))
    ) -> Dict[str, Any]:
        """Connect to TWS/IB Gateway.
        
        Args:
            host: TWS/Gateway host (default: 127.0.0.1)
            port: TWS/Gateway port (7497 for TWS, 4001 for IB Gateway Paper, 4002 for Live)
            clientId: Unique client ID (default: 1)
            
        Returns:
            Connection status with host, port, and clientId
        """
        tws = ctx.request_context.lifespan_context.tws
        await tws.connect(host, port, clientId)
        return {"status": "connected", "host": host, "port": port, "clientId": clientId}

    @mcp.tool()
    async def ibkr_disconnect(
        ctx: Context[ServerSession, AppContext]
    ) -> Dict[str, Any]:
        """Disconnect from TWS/IB Gateway.
        
        Returns:
            Disconnection status
        """
        tws = ctx.request_context.lifespan_context.tws
        tws.disconnect()
        return {"status": "disconnected"}

    @mcp.tool()
    async def ibkr_get_status(
        ctx: Context[ServerSession, AppContext]
    ) -> Dict[str, Any]:
        """Get connection status.
        
        Returns:
            Current connection status (connected/disconnected)
        """
        tws = ctx.request_context.lifespan_context.tws
        return {"is_connected": tws.is_connected()}
    
    @mcp.tool()
    async def ibkr_get_current_time(
        ctx: Context[ServerSession, AppContext]
    ) -> Dict[str, Any]:
        """Get current server time from TWS/Gateway.
        
        Returns:
            Server time as ISO string
        """
        tws = ctx.request_context.lifespan_context.tws
        if not tws or not tws.is_connected():
            return {"error": "TWS client not connected"}
        
        current_time = await tws.ib.reqCurrentTimeAsync()
        return {
            "server_time": current_time.isoformat(),
            "timestamp": current_time.timestamp()
        }
    
    @mcp.tool()
    async def ibkr_get_managed_accounts(
        ctx: Context[ServerSession, AppContext]
    ) -> Dict[str, Any]:
        """Get list of managed accounts.
        
        Returns:
            List of account IDs accessible to this connection
        """
        tws = ctx.request_context.lifespan_context.tws
        if not tws or not tws.is_connected():
            return {"error": "TWS client not connected"}
        
        accounts = tws.ib.managedAccounts()
        return {
            "accounts": accounts,
            "count": len(accounts)
        }
