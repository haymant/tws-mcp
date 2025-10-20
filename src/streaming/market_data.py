"""WebSocket endpoint for real-time market data streaming."""

import asyncio
from typing import Dict, Any
from starlette.websockets import WebSocket, WebSocketDisconnect

from ..models import ContractRequest
from ..tws_client import TWSClient
from .websocket_manager import StreamingManager


async def market_data_stream(websocket: WebSocket, tws: TWSClient, manager: StreamingManager):
    """WebSocket endpoint for real-time market data.
    
    Protocol:
    - Client → Server: {"action": "subscribe", "symbol": "AAPL", "secType": "STK", ...}
    - Server → Client: {"type": "market_data", "symbol": "AAPL", "data": {...}}
    - Client → Server: {"action": "unsubscribe", "symbol": "AAPL"}
    - Client → Server: {"action": "ping"} → Server responds: {"type": "pong"}
    
    Example:
        # JavaScript client
        const ws = new WebSocket('ws://localhost:8000/api/v1/stream/market-data');
        
        ws.onopen = () => {
            ws.send(JSON.stringify({
                action: 'subscribe',
                symbol: 'AAPL',
                secType: 'STK',
                exchange: 'SMART',
                currency: 'USD'
            }));
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'market_data') {
                console.log(`${data.symbol}: ${data.data.last}`);
            }
        };
    """
    await manager.connect(websocket, "market_data")
    
    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "stream": "market_data",
            "message": "Connected to market data stream. Send {\"action\": \"subscribe\", \"symbol\": \"AAPL\"} to start."
        })
        
        # Track active streaming tasks per symbol
        active_subscriptions: Dict[str, asyncio.Task] = {}
        
        while True:
            # Receive subscription commands from client
            data = await websocket.receive_json()
            action = data.get("action")
            
            if action == "subscribe":
                symbol = data.get("symbol")
                sec_type = data.get("secType", "STK")
                exchange = data.get("exchange", "SMART")
                currency = data.get("currency", "USD")
                
                # Check if already subscribed
                if symbol in active_subscriptions:
                    await websocket.send_json({
                        "type": "warning",
                        "symbol": symbol,
                        "message": f"Already subscribed to {symbol}"
                    })
                    continue
                
                # Check TWS connection
                if not tws or not tws.is_connected():
                    await websocket.send_json({
                        "type": "error",
                        "error": "Not connected to TWS. Call ibkr_connect first."
                    })
                    continue
                
                # Create contract request
                req = ContractRequest(
                    symbol=symbol,
                    secType=sec_type,
                    exchange=exchange,
                    currency=currency
                )
                
                # Start streaming in background task
                async def stream_data():
                    """Background task to stream market data for this symbol."""
                    try:
                        async for market_data in tws.stream_market_data(req):
                            if not market_data:
                                continue
                            
                            await websocket.send_json({
                                "type": "market_data",
                                "symbol": symbol,
                                "timestamp": asyncio.get_event_loop().time(),
                                "data": market_data
                            })
                    except asyncio.CancelledError:
                        # Clean cancellation
                        pass
                    except Exception as e:
                        await websocket.send_json({
                            "type": "error",
                            "symbol": symbol,
                            "error": f"Streaming error: {str(e)}"
                        })
                
                # Create and store task
                task = asyncio.create_task(stream_data())
                active_subscriptions[symbol] = task
                
                await websocket.send_json({
                    "type": "subscribed",
                    "symbol": symbol,
                    "message": f"Subscribed to {symbol} market data"
                })
            
            elif action == "unsubscribe":
                symbol = data.get("symbol")
                
                if symbol in active_subscriptions:
                    # Cancel the streaming task
                    active_subscriptions[symbol].cancel()
                    try:
                        await active_subscriptions[symbol]
                    except asyncio.CancelledError:
                        pass
                    
                    del active_subscriptions[symbol]
                    
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "symbol": symbol,
                        "message": f"Unsubscribed from {symbol}"
                    })
                else:
                    await websocket.send_json({
                        "type": "warning",
                        "symbol": symbol,
                        "message": f"Not subscribed to {symbol}"
                    })
            
            elif action == "list":
                # List active subscriptions
                await websocket.send_json({
                    "type": "subscriptions",
                    "symbols": list(active_subscriptions.keys()),
                    "count": len(active_subscriptions)
                })
            
            elif action == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": asyncio.get_event_loop().time()
                })
            
            else:
                await websocket.send_json({
                    "type": "error",
                    "error": f"Unknown action: {action}",
                    "valid_actions": ["subscribe", "unsubscribe", "list", "ping"]
                })
    
    except WebSocketDisconnect:
        # Client disconnected
        pass
    except Exception as e:
        # Unexpected error
        try:
            await websocket.send_json({
                "type": "error",
                "error": f"Server error: {str(e)}"
            })
        except:
            pass
    finally:
        # Cleanup: cancel all active subscriptions
        for task in active_subscriptions.values():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Disconnect from manager
        await manager.disconnect(websocket, "market_data")
