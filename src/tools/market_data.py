"""Market data tools for IBKR TWS API."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession
from ib_async import Stock, Contract
from ..models import AppContext


def register_market_data_tools(mcp: FastMCP):
    """Register market data tools."""
    
    @mcp.tool()
    async def ibkr_get_historical_data(
        ctx: Context[ServerSession, AppContext],
        symbol: str,
        duration: str = "1 D",
        barSize: str = "1 hour",
        whatToShow: str = "TRADES",
        useRTH: bool = True,
        exchange: str = "SMART",
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """Get historical market data.
        
        Args:
            symbol: Contract symbol (e.g., 'AAPL')
            duration: Time span (e.g., '1 D', '1 W', '1 M', '1 Y')
            barSize: Bar size (1 min, 5 mins, 15 mins, 1 hour, 1 day, etc.)
            whatToShow: Data type (TRADES, MIDPOINT, BID, ASK, etc.)
            useRTH: Use regular trading hours only (default: True)
            exchange: Exchange (default: SMART)
            currency: Currency (default: USD)
            
        Returns:
            Historical bars with OHLCV data
        """
        tws = ctx.request_context.lifespan_context.tws
        if not tws or not tws.is_connected():
            return {"error": "TWS client not connected"}
        
        contract = Stock(symbol, exchange, currency)
        
        bars = await tws.ib.reqHistoricalDataAsync(
            contract,
            endDateTime='',
            durationStr=duration,
            barSizeSetting=barSize,
            whatToShow=whatToShow,
            useRTH=useRTH,
            formatDate=1
        )
        
        return {
            "symbol": symbol,
            "bars": [
                {
                    "date": bar.date.isoformat() if hasattr(bar.date, 'isoformat') else str(bar.date),
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "volume": bar.volume,
                    "average": bar.average,
                    "barCount": bar.barCount
                }
                for bar in bars
            ],
            "count": len(bars)
        }
    
    @mcp.tool()
    async def ibkr_get_head_timestamp(
        ctx: Context[ServerSession, AppContext],
        symbol: str,
        whatToShow: str = "TRADES",
        useRTH: bool = True,
        exchange: str = "SMART",
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """Get earliest available data point for a contract.
        
        Args:
            symbol: Contract symbol
            whatToShow: Data type (TRADES, MIDPOINT, BID, ASK, etc.)
            useRTH: Use regular trading hours only
            exchange: Exchange (default: SMART)
            currency: Currency (default: USD)
            
        Returns:
            Earliest timestamp for which data is available
        """
        tws = ctx.request_context.lifespan_context.tws
        if not tws or not tws.is_connected():
            return {"error": "TWS client not connected"}
        
        contract = Stock(symbol, exchange, currency)
        
        head_timestamp = await tws.ib.reqHeadTimeStampAsync(
            contract,
            whatToShow=whatToShow,
            useRTH=useRTH,
            formatDate=1
        )
        
        return {
            "symbol": symbol,
            "headTimestamp": head_timestamp.isoformat() if head_timestamp else None,
            "whatToShow": whatToShow,
            "useRTH": useRTH
        }
    
    @mcp.tool()
    async def ibkr_set_market_data_type(
        ctx: Context[ServerSession, AppContext],
        marketDataType: int
    ) -> Dict[str, Any]:
        """Set market data type for streaming quotes.
        
        Args:
            marketDataType: 1=Live, 2=Frozen, 3=Delayed, 4=Delayed-Frozen
            
        Returns:
            Confirmation of market data type setting
        """
        tws = ctx.request_context.lifespan_context.tws
        if not tws or not tws.is_connected():
            return {"error": "TWS client not connected"}
        
        tws.ib.reqMarketDataType(marketDataType)
        
        type_names = {
            1: "Live",
            2: "Frozen",
            3: "Delayed",
            4: "Delayed-Frozen"
        }
        
        return {
            "marketDataType": marketDataType,
            "description": type_names.get(marketDataType, "Unknown")
        }
    
    @mcp.tool()
    async def ibkr_get_histogram_data(
        ctx: Context[ServerSession, AppContext],
        symbol: str,
        duration: str = "1 day",
        useRTH: bool = True,
        exchange: str = "SMART",
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """Get histogram data showing price distribution.
        
        Args:
            symbol: Contract symbol
            duration: Time period (e.g., '1 day', '1 week')
            useRTH: Use regular trading hours only
            exchange: Exchange (default: SMART)
            currency: Currency (default: USD)
            
        Returns:
            Price histogram showing volume at each price level
        """
        tws = ctx.request_context.lifespan_context.tws
        if not tws or not tws.is_connected():
            return {"error": "TWS client not connected"}
        
        contract = Stock(symbol, exchange, currency)
        
        histogram = await tws.ib.reqHistogramDataAsync(
            contract,
            useRTH=useRTH,
            period=duration
        )
        
        return {
            "symbol": symbol,
            "histogram": [
                {
                    "price": item.price,
                    "count": item.count
                }
                for item in histogram
            ],
            "count": len(histogram)
        }
    
    @mcp.tool()
    async def ibkr_get_fundamental_data(
        ctx: Context[ServerSession, AppContext],
        symbol: str,
        reportType: str = "ReportsFinSummary",
        exchange: str = "SMART",
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """Get fundamental data for a contract.
        
        Args:
            symbol: Contract symbol
            reportType: Type of report (ReportsFinSummary, ReportSnapshot, ReportRatios, ReportsFinStatements, RESC, CalendarReport)
            exchange: Exchange (default: SMART)
            currency: Currency (default: USD)
            
        Returns:
            Fundamental data in XML format
        """
        tws = ctx.request_context.lifespan_context.tws
        if not tws or not tws.is_connected():
            return {"error": "TWS client not connected"}
        
        contract = Stock(symbol, exchange, currency)
        
        data = await tws.ib.reqFundamentalDataAsync(contract, reportType)
        
        return {
            "symbol": symbol,
            "reportType": reportType,
            "data": data
        }
