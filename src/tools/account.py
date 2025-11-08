"""Account and portfolio management tools for IBKR TWS API."""

from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession
from ..models import AppContext


def register_account_tools(mcp: FastMCP):
    """Register account and portfolio management tools."""
    
    @mcp.tool()
    async def ibkr_get_account_summary(
        ctx: Context[ServerSession, AppContext],
        account: str = "",
        tags: str = "NetLiquidation,TotalCashValue,SettledCash,BuyingPower,GrossPositionValue"
    ) -> Dict[str, Any]:
        """Get account summary with key metrics.
        
        Args:
            account: Account ID (empty for all accounts)
            tags: Comma-separated list of tags to retrieve
            
        Returns:
            Account summary with requested metrics
        """
        tws = ctx.request_context.lifespan_context.tws
        if not tws or not tws.is_connected():
            return {"error": "TWS client not connected"}
        
        summary = await tws.ib.reqAccountSummaryAsync()
        
        result = {}
        for item in summary:
            if account and item.account != account:
                continue
            if item.tag not in result:
                result[item.tag] = {}
            result[item.tag] = {
                "value": item.value,
                "currency": item.currency,
                "account": item.account
            }
        
        return {"summary": result, "account": account or "All"}

    @mcp.tool()
    async def ibkr_get_positions(
        ctx: Context[ServerSession, AppContext],
        account: str = ""
    ) -> Dict[str, Any]:
        """Get current portfolio positions.
        
        Args:
            account: Account ID (empty for all accounts)
            
        Returns:
            List of positions with contract details and P&L
        """
        tws = ctx.request_context.lifespan_context.tws
        if not tws or not tws.is_connected():
            return {"error": "TWS client not connected"}
        
        positions = tws.ib.positions()
        
        results = []
        for pos in positions:
            if account and pos.account != account:
                continue
            results.append({
                "account": pos.account,
                "contract": {
                    "conId": pos.contract.conId,
                    "symbol": pos.contract.symbol,
                    "secType": pos.contract.secType,
                    "exchange": pos.contract.exchange,
                    "currency": pos.contract.currency,
                    "localSymbol": pos.contract.localSymbol
                },
                "position": pos.position,
                "avgCost": pos.avgCost
            })
        
        return {"positions": results, "count": len(results)}
    
    @mcp.tool()
    async def ibkr_get_account_values(
        ctx: Context[ServerSession, AppContext],
        account: str = ""
    ) -> Dict[str, Any]:
        """Get detailed account values and portfolio data.
        
        Args:
            account: Account ID (uses first available if not specified)
            
        Returns:
            Comprehensive account values including cash, margins, and portfolio
        """
        tws = ctx.request_context.lifespan_context.tws
        if not tws or not tws.is_connected():
            return {"error": "TWS client not connected"}
        
        if not account:
            accounts = tws.ib.managedAccounts()
            if not accounts:
                return {"error": "No managed accounts found"}
            account = accounts[0]
        
        # Subscribe to account updates
        tws.ib.reqAccountUpdates(account)
        await tws.ib.updateEvent
        
        account_values = tws.ib.accountValues(account)
        
        values = {}
        for av in account_values:
            key = f"{av.tag}_{av.currency}" if av.currency else av.tag
            values[key] = {
                "value": av.value,
                "currency": av.currency,
                "account": av.account
            }
        
        return {
            "account": account,
            "values": values,
            "count": len(values)
        }
    
    @mcp.tool()
    async def ibkr_get_pnl(
        ctx: Context[ServerSession, AppContext],
        account: str = ""
    ) -> Dict[str, Any]:
        """Get real-time P&L for account.
        
        Args:
            account: Account ID (uses first available if not specified)
            
        Returns:
            Daily and unrealized P&L
        """
        tws = ctx.request_context.lifespan_context.tws
        if not tws or not tws.is_connected():
            return {"error": "TWS client not connected"}
        
        if not account:
            accounts = tws.ib.managedAccounts()
            if not accounts:
                return {"error": "No managed accounts found"}
            account = accounts[0]
        
        pnl = await tws.ib.reqPnLAsync(account)
        
        return {
            "account": account,
            "dailyPnL": pnl.dailyPnL,
            "unrealizedPnL": pnl.unrealizedPnL,
            "realizedPnL": pnl.realizedPnL
        }
    
    @mcp.tool()
    async def ibkr_get_pnl_single(
        ctx: Context[ServerSession, AppContext],
        account: str,
        conId: int
    ) -> Dict[str, Any]:
        """Get real-time P&L for a single position.
        
        Args:
            account: Account ID
            conId: Contract ID
            
        Returns:
            Position-specific P&L details
        """
        tws = ctx.request_context.lifespan_context.tws
        if not tws or not tws.is_connected():
            return {"error": "TWS client not connected"}
        
        pnl = await tws.ib.reqPnLSingleAsync(account, "", conId)
        
        return {
            "account": account,
            "conId": conId,
            "position": pnl.position,
            "dailyPnL": pnl.dailyPnL,
            "unrealizedPnL": pnl.unrealizedPnL,
            "realizedPnL": pnl.realizedPnL,
            "value": pnl.value
        }
