"""Order management tools for IBKR TWS API."""

from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession
from ib_async import Stock, Contract, Order, LimitOrder, MarketOrder, StopOrder
from ..models import AppContext


def register_order_tools(mcp: FastMCP):
    """Register order management tools."""
    
    @mcp.tool()
    async def ibkr_place_order(
        ctx: Context[ServerSession, AppContext],
        symbol: str,
        action: str,
        quantity: int,
        orderType: str = "MKT",
        limitPrice: Optional[float] = None,
        exchange: str = "SMART",
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """Place a stock order.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            action: BUY or SELL
            quantity: Number of shares
            orderType: MKT, LMT, STP, etc. (default: MKT)
            limitPrice: Limit price (required for LMT orders)
            exchange: Exchange (default: SMART)
            currency: Currency (default: USD)
            
        Returns:
            Order details with orderId and status
        """
        tws = ctx.request_context.lifespan_context.tws
        if not tws or not tws.is_connected():
            return {"error": "TWS client not connected"}
        
        contract = Stock(symbol, exchange, currency)
        
        if orderType == "MKT":
            order = MarketOrder(action, quantity)
        elif orderType == "LMT":
            if limitPrice is None:
                return {"error": "limitPrice required for LMT orders"}
            order = LimitOrder(action, quantity, limitPrice)
        elif orderType == "STP":
            if limitPrice is None:
                return {"error": "limitPrice (stop price) required for STP orders"}
            order = StopOrder(action, quantity, limitPrice)
        else:
            order = Order()
            order.action = action
            order.totalQuantity = quantity
            order.orderType = orderType
            if limitPrice:
                order.lmtPrice = limitPrice
        
        trade = tws.ib.placeOrder(contract, order)
        
        return {
            "orderId": trade.order.orderId,
            "symbol": symbol,
            "action": action,
            "quantity": quantity,
            "orderType": orderType,
            "status": trade.orderStatus.status if trade.orderStatus else "Submitted"
        }

    @mcp.tool()
    async def ibkr_cancel_order(
        ctx: Context[ServerSession, AppContext],
        orderId: int
    ) -> Dict[str, Any]:
        """Cancel an order.
        
        Args:
            orderId: Order ID to cancel
            
        Returns:
            Cancellation confirmation
        """
        tws = ctx.request_context.lifespan_context.tws
        if not tws or not tws.is_connected():
            return {"error": "TWS client not connected"}
        
        # Find the trade
        trade = None
        for t in tws.ib.trades():
            if t.order.orderId == orderId:
                trade = t
                break
        
        if not trade:
            return {"error": f"Order {orderId} not found"}
        
        tws.ib.cancelOrder(trade.order)
        
        return {
            "orderId": orderId,
            "status": "Cancellation requested"
        }

    @mcp.tool()
    async def ibkr_get_open_orders(
        ctx: Context[ServerSession, AppContext]
    ) -> Dict[str, Any]:
        """Get all open orders.
        
        Returns:
            List of open orders with details
        """
        tws = ctx.request_context.lifespan_context.tws
        if not tws or not tws.is_connected():
            return {"error": "TWS client not connected"}
        
        trades = tws.ib.openTrades()
        
        orders = []
        for trade in trades:
            orders.append({
                "orderId": trade.order.orderId,
                "contract": {
                    "symbol": trade.contract.symbol,
                    "secType": trade.contract.secType,
                    "exchange": trade.contract.exchange,
                    "currency": trade.contract.currency
                },
                "order": {
                    "action": trade.order.action,
                    "totalQuantity": trade.order.totalQuantity,
                    "orderType": trade.order.orderType,
                    "lmtPrice": trade.order.lmtPrice,
                    "auxPrice": trade.order.auxPrice
                },
                "status": trade.orderStatus.status if trade.orderStatus else "Unknown",
                "filled": trade.orderStatus.filled if trade.orderStatus else 0,
                "remaining": trade.orderStatus.remaining if trade.orderStatus else trade.order.totalQuantity
            })
        
        return {"orders": orders, "count": len(orders)}

    @mcp.tool()
    async def ibkr_get_all_orders(
        ctx: Context[ServerSession, AppContext]
    ) -> Dict[str, Any]:
        """Get all orders (including filled and cancelled).
        
        Returns:
            List of all orders with details
        """
        tws = ctx.request_context.lifespan_context.tws
        if not tws or not tws.is_connected():
            return {"error": "TWS client not connected"}
        
        trades = tws.ib.trades()
        
        orders = []
        for trade in trades:
            orders.append({
                "orderId": trade.order.orderId,
                "contract": {
                    "symbol": trade.contract.symbol,
                    "secType": trade.contract.secType,
                    "exchange": trade.contract.exchange,
                    "currency": trade.contract.currency
                },
                "order": {
                    "action": trade.order.action,
                    "totalQuantity": trade.order.totalQuantity,
                    "orderType": trade.order.orderType,
                    "lmtPrice": trade.order.lmtPrice,
                    "auxPrice": trade.order.auxPrice
                },
                "status": trade.orderStatus.status if trade.orderStatus else "Unknown",
                "filled": trade.orderStatus.filled if trade.orderStatus else 0,
                "remaining": trade.orderStatus.remaining if trade.orderStatus else trade.order.totalQuantity,
                "avgFillPrice": trade.orderStatus.avgFillPrice if trade.orderStatus else 0
            })
        
        return {"orders": orders, "count": len(orders)}
    
    @mcp.tool()
    async def ibkr_modify_order(
        ctx: Context[ServerSession, AppContext],
        orderId: int,
        quantity: Optional[int] = None,
        limitPrice: Optional[float] = None,
        auxPrice: Optional[float] = None
    ) -> Dict[str, Any]:
        """Modify an existing order.
        
        Args:
            orderId: Order ID to modify
            quantity: New quantity (optional)
            limitPrice: New limit price (optional)
            auxPrice: New aux price for stop orders (optional)
            
        Returns:
            Modified order confirmation
        """
        tws = ctx.request_context.lifespan_context.tws
        if not tws or not tws.is_connected():
            return {"error": "TWS client not connected"}
        
        # Find the trade
        trade = None
        for t in tws.ib.trades():
            if t.order.orderId == orderId:
                trade = t
                break
        
        if not trade:
            return {"error": f"Order {orderId} not found"}
        
        # Modify order
        if quantity is not None:
            trade.order.totalQuantity = quantity
        if limitPrice is not None:
            trade.order.lmtPrice = limitPrice
        if auxPrice is not None:
            trade.order.auxPrice = auxPrice
        
        # Replace order
        tws.ib.placeOrder(trade.contract, trade.order)
        
        return {
            "orderId": orderId,
            "status": "Modified",
            "quantity": trade.order.totalQuantity,
            "limitPrice": trade.order.lmtPrice,
            "auxPrice": trade.order.auxPrice
        }
    
    @mcp.tool()
    async def ibkr_get_executions(
        ctx: Context[ServerSession, AppContext],
        symbol: Optional[str] = None,
        secType: Optional[str] = None,
        exchange: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get execution history.
        
        Args:
            symbol: Filter by symbol (optional)
            secType: Filter by security type (optional)
            exchange: Filter by exchange (optional)
            
        Returns:
            List of executions with fill details
        """
        tws = ctx.request_context.lifespan_context.tws
        if not tws or not tws.is_connected():
            return {"error": "TWS client not connected"}
        
        from ib_async import ExecutionFilter
        filter = ExecutionFilter()
        if symbol:
            filter.symbol = symbol
        if secType:
            filter.secType = secType
        if exchange:
            filter.exchange = exchange
        
        executions = await tws.ib.reqExecutionsAsync(filter)
        
        results = []
        for fill in executions:
            results.append({
                "execId": fill.execution.execId,
                "orderId": fill.execution.orderId,
                "time": fill.execution.time,
                "contract": {
                    "symbol": fill.contract.symbol,
                    "secType": fill.contract.secType,
                    "exchange": fill.contract.exchange,
                    "currency": fill.contract.currency
                },
                "execution": {
                    "shares": fill.execution.shares,
                    "price": fill.execution.price,
                    "side": fill.execution.side,
                    "cumQty": fill.execution.cumQty,
                    "avgPrice": fill.execution.avgPrice
                },
                "commissionReport": {
                    "commission": fill.commissionReport.commission if fill.commissionReport else 0,
                    "realizedPNL": fill.commissionReport.realizedPNL if fill.commissionReport else 0
                } if fill.commissionReport else None
            })
        
        return {"executions": results, "count": len(results)}
    
    @mcp.tool()
    async def ibkr_place_bracket_order(
        ctx: Context[ServerSession, AppContext],
        symbol: str,
        action: str,
        quantity: int,
        entryPrice: float,
        takeProfitPrice: float,
        stopLossPrice: float,
        exchange: str = "SMART",
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """Place a bracket order (entry + take profit + stop loss).
        
        Args:
            symbol: Stock symbol
            action: BUY or SELL
            quantity: Number of shares
            entryPrice: Entry limit price
            takeProfitPrice: Take profit limit price
            stopLossPrice: Stop loss price
            exchange: Exchange (default: SMART)
            currency: Currency (default: USD)
            
        Returns:
            All three order IDs (parent, takeProfit, stopLoss)
        """
        tws = ctx.request_context.lifespan_context.tws
        if not tws or not tws.is_connected():
            return {"error": "TWS client not connected"}
        
        from ib_async import Order
        contract = Stock(symbol, exchange, currency)
        
        # Parent order
        parent = Order()
        parent.orderId = tws.ib.client.getReqId()
        parent.action = action
        parent.orderType = "LMT"
        parent.totalQuantity = quantity
        parent.lmtPrice = entryPrice
        parent.transmit = False
        
        # Take profit order
        takeProfit = Order()
        takeProfit.orderId = parent.orderId + 1
        takeProfit.action = "SELL" if action == "BUY" else "BUY"
        takeProfit.orderType = "LMT"
        takeProfit.totalQuantity = quantity
        takeProfit.lmtPrice = takeProfitPrice
        takeProfit.parentId = parent.orderId
        takeProfit.transmit = False
        
        # Stop loss order
        stopLoss = Order()
        stopLoss.orderId = parent.orderId + 2
        stopLoss.action = "SELL" if action == "BUY" else "BUY"
        stopLoss.orderType = "STP"
        stopLoss.totalQuantity = quantity
        stopLoss.auxPrice = stopLossPrice
        stopLoss.parentId = parent.orderId
        stopLoss.transmit = True
        
        # Place orders
        for order in [parent, takeProfit, stopLoss]:
            tws.ib.placeOrder(contract, order)
        
        return {
            "symbol": symbol,
            "parentOrderId": parent.orderId,
            "takeProfitOrderId": takeProfit.orderId,
            "stopLossOrderId": stopLoss.orderId,
            "status": "Bracket order submitted"
        }
    
    @mcp.tool()
    async def ibkr_get_order_status(
        ctx: Context[ServerSession, AppContext],
        orderId: int
    ) -> Dict[str, Any]:
        """Get status of a specific order.
        
        Args:
            orderId: Order ID to query
            
        Returns:
            Current order status and fill details
        """
        tws = ctx.request_context.lifespan_context.tws
        if not tws or not tws.is_connected():
            return {"error": "TWS client not connected"}
        
        # Find the trade
        trade = None
        for t in tws.ib.trades():
            if t.order.orderId == orderId:
                trade = t
                break
        
        if not trade:
            return {"error": f"Order {orderId} not found"}
        
        return {
            "orderId": orderId,
            "contract": {
                "symbol": trade.contract.symbol,
                "secType": trade.contract.secType,
                "exchange": trade.contract.exchange,
                "currency": trade.contract.currency
            },
            "order": {
                "action": trade.order.action,
                "totalQuantity": trade.order.totalQuantity,
                "orderType": trade.order.orderType,
                "lmtPrice": trade.order.lmtPrice,
                "auxPrice": trade.order.auxPrice
            },
            "status": trade.orderStatus.status if trade.orderStatus else "Unknown",
            "filled": trade.orderStatus.filled if trade.orderStatus else 0,
            "remaining": trade.orderStatus.remaining if trade.orderStatus else trade.order.totalQuantity,
            "avgFillPrice": trade.orderStatus.avgFillPrice if trade.orderStatus else 0,
            "lastFillPrice": trade.orderStatus.lastFillPrice if trade.orderStatus else 0,
            "whyHeld": trade.orderStatus.whyHeld if trade.orderStatus else ""
        }
