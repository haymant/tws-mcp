"""WebSocket endpoint for real-time news bulletins streaming."""

import asyncio
from starlette.websockets import WebSocket, WebSocketDisconnect

from ..tws_client import TWSClient
from .websocket_manager import StreamingManager


async def news_stream(websocket: WebSocket, tws: TWSClient, manager: StreamingManager):
    """WebSocket endpoint for real-time news bulletins from Interactive Brokers.
    
    Protocol:
    - Client → Server: {"action": "subscribe", "allMessages": true}
    - Server → Client: {"type": "news", "data": {...}}
    - Client → Server: {"action": "unsubscribe"}
    
    News bulletins include:
    - System messages (maintenance, upgrades)
    - Trading alerts (halts, circuit breakers)
    - Margin changes
    - Account notifications
    
    Note: News bulletins are typically very infrequent (hours apart).
    
    Example:
        # JavaScript client
        const ws = new WebSocket('ws://localhost:8000/api/v1/stream/news');
        
        ws.onopen = () => {
            ws.send(JSON.stringify({
                action: 'subscribe',
                allMessages: true  // or false for account-specific only
            }));
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'news') {
                console.log('News bulletin:', data.data.message);
            }
        };
    """
    await manager.connect(websocket, "news")
    
    try:
        await websocket.send_json({
            "type": "connected",
            "stream": "news",
            "message": "Connected to news stream. Send {\"action\": \"subscribe\", \"allMessages\": true} to start."
        })
        
        subscription_task = None
        
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            
            if action == "subscribe":
                if subscription_task:
                    await websocket.send_json({
                        "type": "warning",
                        "message": "Already subscribed to news bulletins"
                    })
                    continue
                
                # Check TWS connection
                if not tws or not tws.is_connected():
                    await websocket.send_json({
                        "type": "error",
                        "error": "Not connected to TWS. Call ibkr_connect first."
                    })
                    continue
                
                all_messages = data.get("allMessages", True)
                
                # Start streaming in background task
                async def stream_news():
                    """Background task to stream news bulletins."""
                    try:
                        # Subscribe to news bulletins
                        await tws.subscribe_news_bulletins(all_messages)
                        
                        # Monitor for new bulletins
                        while True:
                            # Check for new bulletins every second
                            await asyncio.sleep(1.0)
                            
                            if hasattr(tws.ib, 'newsBulletins') and tws.ib.newsBulletins():
                                for bulletin in tws.ib.newsBulletins():
                                    await websocket.send_json({
                                        "type": "news",
                                        "timestamp": asyncio.get_event_loop().time(),
                                        "data": {
                                            "msgId": bulletin.msgId,
                                            "msgType": bulletin.msgType,
                                            "message": bulletin.message,
                                            "origin": bulletin.origin
                                        }
                                    })
                                
                                # Clear processed bulletins
                                tws.ib.newsBulletins().clear()
                    
                    except asyncio.CancelledError:
                        # Unsubscribe from news bulletins
                        try:
                            if hasattr(tws.ib, 'cancelNewsBulletins'):
                                tws.ib.cancelNewsBulletins()
                        except:
                            pass
                    except Exception as e:
                        await websocket.send_json({
                            "type": "error",
                            "error": f"Streaming error: {str(e)}"
                        })
                
                # Create and store task
                subscription_task = asyncio.create_task(stream_news())
                
                await websocket.send_json({
                    "type": "subscribed",
                    "allMessages": all_messages,
                    "message": "Subscribed to news bulletins. Note: Bulletins are typically infrequent."
                })
            
            elif action == "unsubscribe":
                if subscription_task:
                    subscription_task.cancel()
                    try:
                        await subscription_task
                    except asyncio.CancelledError:
                        pass
                    
                    subscription_task = None
                    
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "message": "Unsubscribed from news bulletins"
                    })
                else:
                    await websocket.send_json({
                        "type": "warning",
                        "message": "Not subscribed to news bulletins"
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
                    "valid_actions": ["subscribe", "unsubscribe", "ping"]
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
        # Cleanup subscription
        if subscription_task:
            subscription_task.cancel()
            try:
                await subscription_task
            except asyncio.CancelledError:
                pass
        
        await manager.disconnect(websocket, "news")
