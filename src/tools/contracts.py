"""Contract and symbol search tools for IBKR TWS API."""

from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession
from ib_async import Stock, Contract
from ..models import AppContext


def register_contract_tools(mcp: FastMCP):
    """Register contract and symbol search tools."""
    
    @mcp.tool()
    async def ibkr_search_symbols(
        ctx: Context[ServerSession, AppContext],
        pattern: str
    ) -> Dict[str, Any]:
        """Search for symbols matching a pattern.
        
        Args:
            pattern: Symbol search pattern (e.g., 'AAPL', 'MSFT')
            
        Returns:
            List of matching contracts with symbol, name, and exchange
        """
        tws = ctx.request_context.lifespan_context.tws
        if not tws or not tws.is_connected():
            return {"error": "TWS client not connected"}
        
        contracts = await tws.ib.reqMatchingSymbolsAsync(pattern)
        
        results = []
        for contract_desc in contracts:
            c = contract_desc.contract
            results.append({
                "conId": c.conId,
                "symbol": c.symbol,
                "secType": c.secType,
                "primaryExchange": c.primaryExchange,
                "currency": c.currency,
                "description": contract_desc.derivativeSecTypes
            })
        
        return {"results": results, "count": len(results)}

    @mcp.tool()
    async def ibkr_get_contract_details(
        ctx: Context[ServerSession, AppContext],
        symbol: str,
        secType: str = "STK",
        exchange: str = "SMART",
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """Get detailed information about a contract.
        
        Args:
            symbol: Contract symbol (e.g., 'AAPL')
            secType: Security type (STK, OPT, FUT, CASH, etc.)
            exchange: Exchange (default: SMART)
            currency: Currency (default: USD)
            
        Returns:
            Detailed contract information including trading hours, lot size, etc.
        """
        tws = ctx.request_context.lifespan_context.tws
        if not tws or not tws.is_connected():
            return {"error": "TWS client not connected"}
        
        contract = Contract()
        contract.symbol = symbol
        contract.secType = secType
        contract.exchange = exchange
        contract.currency = currency
        
        details = await tws.ib.reqContractDetailsAsync(contract)
        
        if not details:
            return {"error": f"No contract details found for {symbol}"}
        
        detail = details[0]
        return {
            "contract": {
                "conId": detail.contract.conId,
                "symbol": detail.contract.symbol,
                "secType": detail.contract.secType,
                "exchange": detail.contract.exchange,
                "currency": detail.contract.currency,
                "localSymbol": detail.contract.localSymbol,
                "tradingClass": detail.contract.tradingClass
            },
            "marketName": detail.marketName,
            "minTick": detail.minTick,
            "priceMagnifier": detail.priceMagnifier,
            "orderTypes": detail.orderTypes.split(',') if detail.orderTypes else [],
            "validExchanges": detail.validExchanges.split(',') if detail.validExchanges else [],
            "underConId": detail.underConId,
            "longName": detail.longName,
            "contractMonth": detail.contractMonth,
            "industry": detail.industry,
            "category": detail.category,
            "subcategory": detail.subcategory,
            "timeZoneId": detail.timeZoneId,
            "tradingHours": detail.tradingHours,
            "liquidHours": detail.liquidHours
        }
    
    @mcp.tool()
    async def ibkr_get_market_rule(
        ctx: Context[ServerSession, AppContext],
        marketRuleId: int
    ) -> Dict[str, Any]:
        """Get price increment rules for a market.
        
        Args:
            marketRuleId: Market rule ID from contract details
            
        Returns:
            List of price increments with low/high edge and increment
        """
        tws = ctx.request_context.lifespan_context.tws
        if not tws or not tws.is_connected():
            return {"error": "TWS client not connected"}
        
        increments = await tws.ib.reqMarketRuleAsync(marketRuleId)
        
        result = []
        for inc in increments:
            result.append({
                "lowEdge": inc.lowEdge,
                "increment": inc.increment
            })
        
        return {
            "marketRuleId": marketRuleId,
            "priceIncrements": result
        }
    
    @mcp.tool()
    async def ibkr_get_option_chain_params(
        ctx: Context[ServerSession, AppContext],
        underlyingConId: int
    ) -> Dict[str, Any]:
        """Get option chain parameters for an underlying contract.
        
        Args:
            underlyingConId: Contract ID of the underlying
            
        Returns:
            Available exchanges, strikes, and expirations
        """
        tws = ctx.request_context.lifespan_context.tws
        if not tws or not tws.is_connected():
            return {"error": "TWS client not connected"}
        
        chains = await tws.ib.reqSecDefOptParamsAsync(
            underlyingSymbol="",
            futFopExchange="",
            underlyingSecType="STK",
            underlyingConId=underlyingConId
        )
        
        results = []
        for chain in chains:
            results.append({
                "exchange": chain.exchange,
                "underlyingConId": chain.underlyingConId,
                "tradingClass": chain.tradingClass,
                "multiplier": chain.multiplier,
                "expirations": sorted(chain.expirations),
                "strikes": sorted(chain.strikes)
            })
        
        return {
            "underlyingConId": underlyingConId,
            "chains": results,
            "count": len(results)
        }
