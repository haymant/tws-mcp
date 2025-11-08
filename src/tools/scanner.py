"""Market scanner tools for IBKR TWS API."""

from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession
from ib_async import ScannerSubscription
from ..models import AppContext


def register_scanner_tools(mcp: FastMCP):
    """Register market scanner tools."""
    
    @mcp.tool()
    async def ibkr_get_scanner_parameters(
        ctx: Context[ServerSession, AppContext]
    ) -> Dict[str, Any]:
        """Get available scanner parameters and filter options.
        
        Returns:
            Scanner parameters XML with available scan types and filters
        """
        tws = ctx.request_context.lifespan_context.tws
        if not tws or not tws.is_connected():
            return {"error": "TWS client not connected"}
        
        params = await tws.ib.reqScannerParametersAsync()
        
        return {
            "parameters": params,
            "description": "Use XML to find available scan codes, instruments, locations, and filters"
        }
    
    @mcp.tool()
    async def ibkr_run_market_scanner(
        ctx: Context[ServerSession, AppContext],
        scanCode: str,
        instrument: str = "STK",
        locationCode: str = "STK.US.MAJOR",
        numberOfRows: int = 50,
        abovePrice: Optional[float] = None,
        belowPrice: Optional[float] = None,
        aboveVolume: Optional[int] = None,
        marketCapAbove: Optional[float] = None,
        marketCapBelow: Optional[float] = None,
        stockTypeFilter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run a market scanner to find securities matching criteria.
        
        Args:
            scanCode: Scanner type (e.g., 'TOP_PERC_GAIN', 'MOST_ACTIVE', 'HOT_BY_VOLUME')
            instrument: Security type (STK, ETF, etc.)
            locationCode: Market location (e.g., 'STK.US.MAJOR', 'STK.US')
            numberOfRows: Maximum results to return (default: 50)
            abovePrice: Filter: price above this value
            belowPrice: Filter: price below this value
            aboveVolume: Filter: volume above this value
            marketCapAbove: Filter: market cap above this value
            marketCapBelow: Filter: market cap below this value
            stockTypeFilter: Filter: CORP or ETF
            
        Returns:
            List of contracts matching scanner criteria with rank and details
        """
        tws = ctx.request_context.lifespan_context.tws
        if not tws or not tws.is_connected():
            return {"error": "TWS client not connected"}
        
        # Create scanner subscription
        sub = ScannerSubscription()
        sub.instrument = instrument
        sub.locationCode = locationCode
        sub.scanCode = scanCode
        sub.numberOfRows = numberOfRows
        
        # Apply filters
        if abovePrice is not None:
            sub.abovePrice = abovePrice
        if belowPrice is not None:
            sub.belowPrice = belowPrice
        if aboveVolume is not None:
            sub.aboveVolume = aboveVolume
        if marketCapAbove is not None:
            sub.marketCapAbove = marketCapAbove
        if marketCapBelow is not None:
            sub.marketCapBelow = marketCapBelow
        if stockTypeFilter is not None:
            sub.stockTypeFilter = stockTypeFilter
        
        # Run scanner
        scanData = await tws.ib.reqScannerDataAsync(sub)
        
        results = []
        for item in scanData:
            results.append({
                "rank": item.rank,
                "contract": {
                    "conId": item.contractDetails.contract.conId,
                    "symbol": item.contractDetails.contract.symbol,
                    "secType": item.contractDetails.contract.secType,
                    "exchange": item.contractDetails.contract.primaryExchange,
                    "currency": item.contractDetails.contract.currency,
                    "localSymbol": item.contractDetails.contract.localSymbol
                },
                "distance": item.distance,
                "benchmark": item.benchmark,
                "projection": item.projection,
                "legsStr": item.legsStr
            })
        
        return {
            "scanCode": scanCode,
            "instrument": instrument,
            "locationCode": locationCode,
            "results": results,
            "count": len(results)
        }
