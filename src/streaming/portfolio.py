"""WebSocket endpoint for real-time portfolio/account streaming."""

import asyncio
from typing import Dict
from starlette.websockets import WebSocket, WebSocketDisconnect

from ..tws_client import TWSClient
from .websocket_manager import StreamingManager


async def portfolio_stream(websocket: WebSocket, tws: TWSClient, manager: StreamingManager):
    """WebSocket endpoint for real-time portfolio and account updates.
    
    Protocol:
    - Client → Server: {"action": "subscribe", "account": "DU123456"}
    - Server → Client: {"type": "portfolio", "account": "DU123456", "data": {...}}
    - Client → Server: {"action": "unsubscribe", "account": "DU123456"}
    
    Updates include:
    - Position changes (new fills, closures)
    - Account value updates
    - Real-time P&L changes
    
    Example:
        # Python client
        import websockets
        import json
        
        async with websockets.connect('ws://localhost:8000/api/v1/stream/portfolio') as ws:
            await ws.send(json.dumps({
                'action': 'subscribe',
                'account': 'DU123456'
            }))
            
            async for message in ws:
                data = json.loads(message)
                if data['type'] == 'portfolio':
                    print(f"Portfolio update: {data['data']}")
    """
    await manager.connect(websocket, "portfolio")
    
    try:
        await websocket.send_json({
            "type": "connected",
            "stream": "portfolio",
            "message": "Connected to portfolio stream. Send {\"action\": \"subscribe\", \"account\": \"DU123456\"} to start."
        })
        
        # Track active streaming tasks per account
        active_subscriptions: Dict[str, asyncio.Task] = {}
        
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            
            if action == "subscribe":
                account = data.get("account")
                
                if not account:
                    await websocket.send_json({
                        "type": "error",
                        "error": "Missing 'account' parameter"
                    })
                    continue
                
                # Check if already subscribed
                if account in active_subscriptions:
                    await websocket.send_json({
                        "type": "warning",
                        "account": account,
                        "message": f"Already subscribed to account {account}"
                    })
                    continue
                
                # Check TWS connection
                if not tws or not tws.is_connected():
                    await websocket.send_json({
                        "type": "error",
                        "error": "Not connected to TWS. Call ibkr_connect first."
                    })
                    continue
                
                # Start streaming in background task
                async def stream_account():
                    """Background task to stream account/portfolio updates."""
                    try:
                        async for update in tws.stream_account_updates(account):
                            if not update:
                                continue
                            
                            await websocket.send_json({
                                "type": "portfolio",
                                "account": account,
                                "timestamp": asyncio.get_event_loop().time(),
                                "update": update
                            })
                    except asyncio.CancelledError:
                        pass
                    except Exception as e:
                        await websocket.send_json({
                            "type": "error",
                            "account": account,
                            "error": f"Streaming error: {str(e)}"
                        })
                
                # Create and store task
                task = asyncio.create_task(stream_account())
                active_subscriptions[account] = task
                
                await websocket.send_json({
                    "type": "subscribed",
                    "account": account,
                    "message": f"Subscribed to account {account} updates"
                })
            
            elif action == "unsubscribe":
                account = data.get("account")
                
                if account in active_subscriptions:
                    active_subscriptions[account].cancel()
                    try:
                        await active_subscriptions[account]
                    except asyncio.CancelledError:
                        pass
                    
                    del active_subscriptions[account]
                    
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "account": account,
                        "message": f"Unsubscribed from account {account}"
                    })
                else:
                    await websocket.send_json({
                        "type": "warning",
                        "account": account,
                        "message": f"Not subscribed to account {account}"
                    })
            
            elif action == "list":
                await websocket.send_json({
                    "type": "subscriptions",
                    "accounts": list(active_subscriptions.keys()),
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
        pass
    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "error": f"Server error: {str(e)}"
            })
        except:
            pass
    finally:
        # Cleanup all subscriptions
        for task in active_subscriptions.values():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        await manager.disconnect(websocket, "portfolio")
