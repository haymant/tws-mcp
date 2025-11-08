"""Options trading tools for IBKR TWS API."""

from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession
from ib_async import Option, Stock
from ..models import AppContext


def register_options_tools(mcp: FastMCP):
    """Register options trading tools."""
    
    @mcp.tool()
    async def ibkr_calculate_option_price(
        ctx: Context[ServerSession, AppContext],
        symbol: str,
        expiration: str,
        strike: float,
        right: str,
        underlyingPrice: float,
        volatility: Optional[float] = None,
        exchange: str = "SMART",
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """Calculate option price and greeks.
        
        Args:
            symbol: Underlying symbol
            expiration: Option expiration (YYYYMMDD format)
            strike: Strike price
            right: Call ('C') or Put ('P')
            underlyingPrice: Current underlying price for calculation
            volatility: Implied volatility (optional, will be calculated if not provided)
            exchange: Exchange (default: SMART)
            currency: Currency (default: USD)
            
        Returns:
            Option price, implied volatility, and greeks
        """
        tws = ctx.request_context.lifespan_context.tws
        if not tws or not tws.is_connected():
            return {"error": "TWS client not connected"}
        
        option = Option(symbol, expiration, strike, right, exchange, currency=currency)
        
        # Qualify contract
        await tws.ib.qualifyContractsAsync(option)
        
        # Calculate option price
        if volatility:
            # Calculate option price from volatility
            calc = await tws.ib.calculateOptionPriceAsync(
                option,
                volatility=volatility,
                underPrice=underlyingPrice
            )
            
            return {
                "contract": {
                    "symbol": symbol,
                    "expiration": expiration,
                    "strike": strike,
                    "right": right
                },
                "optionPrice": calc.optPrice,
                "impliedVolatility": volatility,
                "delta": calc.delta,
                "gamma": calc.gamma,
                "vega": calc.vega,
                "theta": calc.theta,
                "underlyingPrice": underlyingPrice
            }
        else:
            # Get market price and calculate IV
            ticker = tws.ib.reqMktData(option)
            await tws.ib.sleep(2)  # Wait for market data
            
            if ticker.last and ticker.last > 0:
                optionPrice = ticker.last
            elif ticker.close and ticker.close > 0:
                optionPrice = ticker.close
            else:
                return {"error": "Unable to get option price"}
            
            tws.ib.cancelMktData(option)
            
            # Calculate IV from option price
            calc = await tws.ib.calculateImpliedVolatilityAsync(
                option,
                optionPrice=optionPrice,
                underPrice=underlyingPrice
            )
            
            return {
                "contract": {
                    "symbol": symbol,
                    "expiration": expiration,
                    "strike": strike,
                    "right": right
                },
                "optionPrice": optionPrice,
                "impliedVolatility": calc.impliedVolatility,
                "delta": calc.delta,
                "gamma": calc.gamma,
                "vega": calc.vega,
                "theta": calc.theta,
                "underlyingPrice": underlyingPrice
            }
    
    @mcp.tool()
    async def ibkr_get_option_chain(
        ctx: Context[ServerSession, AppContext],
        symbol: str,
        expiration: str,
        exchange: str = "SMART",
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """Get option chain for a specific expiration.
        
        Args:
            symbol: Underlying symbol
            expiration: Option expiration (YYYYMMDD format)
            exchange: Exchange (default: SMART)
            currency: Currency (default: USD)
            
        Returns:
            Full option chain with calls and puts
        """
        tws = ctx.request_context.lifespan_context.tws
        if not tws or not tws.is_connected():
            return {"error": "TWS client not connected"}
        
        # Get underlying contract
        stock = Stock(symbol, exchange, currency)
        await tws.ib.qualifyContractsAsync(stock)
        
        # Get option chain parameters
        chains = await tws.ib.reqSecDefOptParamsAsync(
            underlyingSymbol=symbol,
            futFopExchange="",
            underlyingSecType="STK",
            underlyingConId=stock.conId
        )
        
        if not chains:
            return {"error": f"No option chains found for {symbol}"}
        
        # Find matching expiration
        strikes = None
        for chain in chains:
            if expiration in chain.expirations:
                strikes = sorted(chain.strikes)
                break
        
        if not strikes:
            return {"error": f"Expiration {expiration} not found"}
        
        # Request market data for all options
        calls = []
        puts = []
        
        for strike in strikes:
            # Call option
            call = Option(symbol, expiration, strike, 'C', exchange, currency=currency)
            # Put option
            put = Option(symbol, expiration, strike, 'P', exchange, currency=currency)
            
            calls.append(call)
            puts.append(put)
        
        # Qualify all contracts
        all_options = calls + puts
        await tws.ib.qualifyContractsAsync(*all_options)
        
        # Request market data
        call_tickers = [tws.ib.reqMktData(opt) for opt in calls]
        put_tickers = [tws.ib.reqMktData(opt) for opt in puts]
        
        await tws.ib.sleep(2)  # Wait for market data
        
        # Build results
        chain_data = []
        for i, strike in enumerate(strikes):
            call_ticker = call_tickers[i]
            put_ticker = put_tickers[i]
            
            chain_data.append({
                "strike": strike,
                "call": {
                    "bid": call_ticker.bid,
                    "ask": call_ticker.ask,
                    "last": call_ticker.last,
                    "volume": call_ticker.volume,
                    "openInterest": call_ticker.openInterest
                },
                "put": {
                    "bid": put_ticker.bid,
                    "ask": put_ticker.ask,
                    "last": put_ticker.last,
                    "volume": put_ticker.volume,
                    "openInterest": put_ticker.openInterest
                }
            })
        
        # Cancel market data
        for ticker in call_tickers + put_tickers:
            tws.ib.cancelMktData(ticker.contract)
        
        return {
            "symbol": symbol,
            "expiration": expiration,
            "chain": chain_data,
            "strikeCount": len(strikes)
        }
    
    @mcp.tool()
    async def ibkr_place_option_order(
        ctx: Context[ServerSession, AppContext],
        symbol: str,
        expiration: str,
        strike: float,
        right: str,
        action: str,
        quantity: int,
        orderType: str = "MKT",
        limitPrice: Optional[float] = None,
        exchange: str = "SMART",
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """Place an option order.
        
        Args:
            symbol: Underlying symbol
            expiration: Option expiration (YYYYMMDD format)
            strike: Strike price
            right: Call ('C') or Put ('P')
            action: BUY or SELL
            quantity: Number of contracts
            orderType: MKT, LMT, etc. (default: MKT)
            limitPrice: Limit price (required for LMT orders)
            exchange: Exchange (default: SMART)
            currency: Currency (default: USD)
            
        Returns:
            Order confirmation with orderId
        """
        tws = ctx.request_context.lifespan_context.tws
        if not tws or not tws.is_connected():
            return {"error": "TWS client not connected"}
        
        from ib_async import MarketOrder, LimitOrder
        
        option = Option(symbol, expiration, strike, right, exchange, currency=currency)
        
        # Qualify contract
        await tws.ib.qualifyContractsAsync(option)
        
        if orderType == "MKT":
            order = MarketOrder(action, quantity)
        elif orderType == "LMT":
            if limitPrice is None:
                return {"error": "limitPrice required for LMT orders"}
            order = LimitOrder(action, quantity, limitPrice)
        else:
            return {"error": f"Unsupported order type: {orderType}"}
        
        trade = tws.ib.placeOrder(option, order)
        
        return {
            "orderId": trade.order.orderId,
            "contract": {
                "symbol": symbol,
                "expiration": expiration,
                "strike": strike,
                "right": right
            },
            "action": action,
            "quantity": quantity,
            "orderType": orderType,
            "status": trade.orderStatus.status if trade.orderStatus else "Submitted"
        }
