"""News streaming resources."""

import asyncio
import json
import time
from typing import Dict, Any, List, Set, Optional
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession
from ib_async import Contract
from ..models import AppContext, ContractRequest


# Global state for news bulletins resource
_news_cache: Dict[str, Any] = {"bulletins": [], "timestamp": 0}
_news_resource_subscription: bool = False
_news_background_stream: Optional[asyncio.Task] = None

# Global state for tick news
_tick_news_cache: Dict[str, List[dict]] = {}  # symbol -> list of news items
_tick_news_subscriptions: Set[str] = set()  # Set of subscribed symbols
_tick_news_background_tasks: Dict[str, asyncio.Task] = {}  # symbol -> background task
_tick_news_all_stream: bool = False  # Whether we're streaming all news

# Global state for broadtape news
_broadtape_news_cache: List[Dict[str, Any]] = []
_broadtape_news_subscribed: bool = False
_broadtape_news_task: Optional[asyncio.Task] = None
_broadtape_provider_tickers: List[Any] = []


def register_news_resource(mcp: FastMCP):
    """Register news streaming resources."""
    
    # --- News Bulletins Resource ---
    
    @mcp.resource("ibkr://news-bulletins")
    async def get_news_bulletins_resource() -> str:
        """Get current news bulletins from TWS/IB Gateway.
        
        This resource provides TWS system messages, trading alerts, and account notifications.
        
        Usage:
            1. Call ibkr_start_news_resource tool to start streaming
            2. Subscribe to this resource: ibkr://news-bulletins
            3. Read resource to get current bulletins
            4. Receive notifications when new bulletins arrive
        
        Returns:
            JSON string with news bulletins
        """
        if not _news_resource_subscription:
            return json.dumps({
                "error": "News bulletins not subscribed",
                "message": "Call ibkr_start_news_resource() first to start streaming",
                "subscribed": False
            })
        
        return json.dumps({
            "subscribed": True,
            "bulletins": _news_cache.get("bulletins", []),
            "last_update": _news_cache.get("timestamp", 0),
            "count": len(_news_cache.get("bulletins", []))
        })
    
    @mcp.tool()
    async def ibkr_start_news_resource(
        ctx: Context[ServerSession, AppContext],
        allMessages: bool = True
    ) -> str:
        """Start streaming news bulletins to a resource.
        
        This starts a background task that updates the resource ibkr://news-bulletins
        with TWS/IB Gateway system messages and trading alerts.
        
        Args:
            allMessages: True for all bulletins, False for account-specific only
            
        Returns:
            JSON with resource URI and subscription status
        """
        global _news_resource_subscription, _news_background_stream
        
        tws = ctx.request_context.lifespan_context.tws
        
        if not tws or not tws.is_connected():
            return json.dumps({
                "error": "TWS client not connected",
                "message": "Call ibkr_connect first"
            })
        
        if _news_resource_subscription:
            return json.dumps({
                "status": "already_subscribed",
                "resource_uri": "ibkr://news-bulletins",
                "message": "News bulletins already streaming"
            })
        
        # Initialize cache
        _news_cache["bulletins"] = []
        _news_cache["timestamp"] = 0
        
        # Start background streaming task
        async def stream_to_resource():
            """Background task that updates the news resource."""
            print(f"[NEWS RESOURCE] Starting news bulletins stream (allMessages={allMessages})")
            
            try:
                # Subscribe to news bulletins
                await tws.subscribe_news_bulletins(allMessages)
                
                # Use event-driven approach instead of polling
                # Wait for newsBulletinEvent which fires when news arrives
                while True:
                    # Wait for any news bulletin event
                    await tws.ib.newsBulletinEvent
                    
                    # Get all current bulletins
                    if hasattr(tws.ib, 'newsBulletins') and tws.ib.newsBulletins():
                        bulletins = list(tws.ib.newsBulletins())
                        
                        # Update cache with all bulletins
                        _news_cache["bulletins"] = [
                            {
                                "msgId": b.msgId,
                                "msgType": b.msgType,
                                "message": b.message,
                                "origExchange": b.origExchange
                            }
                            for b in bulletins
                        ]
                        _news_cache["timestamp"] = asyncio.get_event_loop().time()
                        
                        # Notify clients
                        await ctx.session.send_resource_updated("ibkr://news-bulletins")
                        print(f"[NEWS RESOURCE] Updated with {len(bulletins)} bulletins - notification sent")
                    
            except asyncio.CancelledError:
                print(f"[NEWS RESOURCE] Stream cancelled")
            except Exception as e:
                print(f"[NEWS RESOURCE] Stream error: {e}")
                import traceback
                traceback.print_exc()
        
        task = asyncio.create_task(stream_to_resource())
        _news_background_stream = task
        _news_resource_subscription = True
        
        return json.dumps({
            "status": "subscribed",
            "resource_uri": "ibkr://news-bulletins",
            "message": "News bulletins streaming started",
            "allMessages": allMessages
        })
    
    @mcp.tool()
    async def ibkr_stop_news_resource() -> str:
        """Stop streaming news bulletins to a resource.
        
        Returns:
            JSON with status
        """
        global _news_resource_subscription, _news_background_stream
        
        if not _news_resource_subscription:
            return json.dumps({
                "error": "No active news bulletins stream",
                "subscribed": False
            })
        
        # Cancel background task
        if _news_background_stream:
            _news_background_stream.cancel()
            try:
                await _news_background_stream
            except asyncio.CancelledError:
                pass
        
        # Cleanup
        _news_background_stream = None
        _news_resource_subscription = False
        _news_cache["bulletins"] = []
        _news_cache["timestamp"] = 0
        
        print(f"[NEWS RESOURCE] Stopped stream")
        
        return json.dumps({
            "status": "stopped",
            "message": "News bulletins streaming stopped"
        })
    
    # --- Tick News Resource ---
    
    @mcp.resource("ibkr://tick-news/{symbol}")
    async def get_tick_news_resource(symbol: str) -> str:
        """Get real-time news headlines for a symbol.
        
        This provides the same news you see in TWS Station's News tab.
        Streams breaking news, company announcements, and market-moving headlines.
        
        Special symbol: Use '*' to get all tick news across all subscribed symbols.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'MSFT') or '*' for all news
            
        Usage:
            1. Call ibkr_start_tick_news_resource tool to subscribe
            2. Subscribe to this resource: ibkr://tick-news/AAPL
            3. Read resource to get recent headlines
            4. Receive notifications when new headlines arrive
        
        Returns:
            JSON string with news headlines
        """
        if symbol == "*":
            # Return all news from all subscribed symbols
            if not _tick_news_all_stream and not _tick_news_subscriptions:
                return json.dumps({
                    "error": "No tick news subscriptions active",
                    "message": "Call ibkr_start_tick_news_resource() first",
                    "subscribed": False
                })
            
            # Aggregate all news
            all_news = []
            for sym, news_list in _tick_news_cache.items():
                for item in news_list:
                    item_with_symbol = item.copy()
                    item_with_symbol["symbol"] = sym
                    all_news.append(item_with_symbol)
            
            # Sort by timestamp descending
            all_news.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
            
            return json.dumps({
                "subscribed": True,
                "symbol": "*",
                "news_items": all_news[:100],  # Last 100 items
                "total_count": len(all_news),
                "subscribed_symbols": list(_tick_news_subscriptions)
            })
        
        # Symbol-specific news
        if symbol not in _tick_news_subscriptions:
            return json.dumps({
                "error": f"Not subscribed to tick news for {symbol}",
                "message": f"Call ibkr_start_tick_news_resource(symbol='{symbol}') first",
                "subscribed": False
            })
        
        news_items = _tick_news_cache.get(symbol, [])
        
        return json.dumps({
            "subscribed": True,
            "symbol": symbol,
            "news_items": news_items[-50:],  # Last 50 items
            "count": len(news_items)
        })
    
    @mcp.tool()
    async def ibkr_start_tick_news_resource(
        ctx: Context[ServerSession, AppContext],
        symbol: str = "*",
        secType: str = "STK",
        exchange: str = "SMART",
        currency: str = "USD"
    ) -> str:
        """Start streaming real-time news headlines (like TWS News tab).
        
        This streams breaking news, company announcements, and market headlines.
        Different from news-bulletins which are system messages.
        
        IMPORTANT: symbol='*' only enables aggregation mode. To receive news, you must
        subscribe to actual symbols first (e.g., 'AAPL', 'MSFT'). The '*' aggregates
        news from all subscribed symbols.
        
        Example usage:
            1. ibkr_start_tick_news_resource(symbol='AAPL')  # Subscribe to AAPL
            2. ibkr_start_tick_news_resource(symbol='MSFT')  # Subscribe to MSFT
            3. ibkr_start_tick_news_resource(symbol='*')     # Enable aggregation (optional)
            4. Read ibkr://tick-news/* to get all news from AAPL and MSFT
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'MSFT') or '*' to enable aggregation
            secType: Security type (default: STK)
            exchange: Exchange (default: SMART)
            currency: Currency (default: USD)
            
        Returns:
            JSON with resource URI and subscription status
        """
        global _tick_news_all_stream
        
        tws = ctx.request_context.lifespan_context.tws
        
        if not tws or not tws.is_connected():
            return json.dumps({
                "error": "TWS client not connected",
                "message": "Call ibkr_connect first"
            })
        
        # Handle "all news" subscription
        if symbol == "*":
            if _tick_news_all_stream:
                return json.dumps({
                    "status": "already_subscribed",
                    "resource_uri": "ibkr://tick-news/*",
                    "message": "All tick news aggregation already enabled",
                    "subscribed_symbols": list(_tick_news_subscriptions),
                    "note": "This aggregates news from subscribed symbols. No new subscriptions created."
                })
            
            _tick_news_all_stream = True
            
            return json.dumps({
                "status": "subscribed",
                "resource_uri": "ibkr://tick-news/*",
                "message": "Aggregation mode enabled. This collects news from all subscribed symbols.",
                "subscribed_symbols": list(_tick_news_subscriptions),
                "note": "To receive news, subscribe to actual symbols: ibkr_start_tick_news_resource(symbol='AAPL')",
                "warning": "No new symbol subscriptions created. Use specific symbols (e.g. 'AAPL') to subscribe."
            })
        
        # Symbol-specific subscription
        if symbol in _tick_news_subscriptions:
            return json.dumps({
                "status": "already_subscribed",
                "resource_uri": f"ibkr://tick-news/{symbol}",
                "message": f"Tick news for {symbol} already streaming"
            })
        
        # Initialize cache for this symbol
        _tick_news_cache[symbol] = []
        
        # Start background streaming task
        async def stream_tick_news():
            """Background task that streams tick news for a symbol."""
            print(f"[TICK NEWS] Starting tick news stream for {symbol}")
            
            ticker = None
            try:
                from ib_async import Stock, Forex
                
                # Create IB contract
                if secType == "STK":
                    contract = Stock(symbol, exchange, currency)
                elif secType == "CASH":
                    contract = Forex(symbol)
                else:
                    contract = Contract(
                        symbol=symbol,
                        secType=secType,
                        exchange=exchange,
                        currency=currency
                    )
                
                # Qualify contract
                qualified = await tws.ib.qualifyContractsAsync(contract)
                if not qualified:
                    print(f"[TICK NEWS] Failed to qualify contract for {symbol}")
                    return
                
                contract = qualified[0]
                
                # Subscribe to market data with news tick
                # genericTickList 292 = news
                ticker = tws.ib.reqMktData(contract, genericTickList='292')
                
                # Set up an asyncio queue and event-driven loop
                news_queue: asyncio.Queue = asyncio.Queue()
                
                def on_tick_news(news_tick):
                    """Handle incoming tick news by enqueueing it for the loop to process."""
                    news_item = {
                        "timestamp": int(time.time()),
                        "time": news_tick.time.isoformat() if hasattr(news_tick, 'time') else None,
                        "providerCode": getattr(news_tick, 'providerCode', None),
                        "articleId": getattr(news_tick, 'articleId', None),
                        "headline": getattr(news_tick, 'headline', None),
                        "extraData": getattr(news_tick, 'extraData', None)
                    }
                    
                    # Add to cache immediately
                    if symbol not in _tick_news_cache:
                        _tick_news_cache[symbol] = []
                    _tick_news_cache[symbol].append(news_item)
                    if len(_tick_news_cache[symbol]) > 100:
                        _tick_news_cache[symbol] = _tick_news_cache[symbol][-100:]
                    
                    # Enqueue for processing
                    try:
                        news_queue.put_nowait(news_item)
                    except Exception:
                        pass
                    
                    print(f"[TICK NEWS] {symbol}: {news_item.get('headline', '')[:80]}...")
                
                # Attach event handler
                ticker.tickNewsEvent += on_tick_news
                
                # Event-driven processing loop
                while True:
                    # Wait for IB to process events
                    await tws.ib.updateEvent
                    
                    # Drain the queue
                    drained = False
                    while not news_queue.empty():
                        item = news_queue.get_nowait()
                        drained = True
                        # Notify subscribed clients
                        await ctx.session.send_resource_updated(f"ibkr://tick-news/{symbol}")
                        if _tick_news_all_stream:
                            await ctx.session.send_resource_updated("ibkr://tick-news/*")
                    
                    # If drained anything, small sleep to batch notifications
                    if drained:
                        await asyncio.sleep(0.01)
                    
            except asyncio.CancelledError:
                print(f"[TICK NEWS] Stream cancelled for {symbol}")
                if ticker:
                    tws.ib.cancelMktData(contract)
            except Exception as e:
                print(f"[TICK NEWS] Stream error for {symbol}: {e}")
                import traceback
                traceback.print_exc()
        
        task = asyncio.create_task(stream_tick_news())
        _tick_news_background_tasks[symbol] = task
        _tick_news_subscriptions.add(symbol)
        
        return json.dumps({
            "status": "subscribed",
            "resource_uri": f"ibkr://tick-news/{symbol}",
            "message": f"Tick news streaming started for {symbol}",
            "contract": {
                "symbol": symbol,
                "secType": secType,
                "exchange": exchange,
                "currency": currency
            }
        })
    
    @mcp.tool()
    async def ibkr_stop_tick_news_resource(symbol: str) -> str:
        """Stop streaming tick news for a symbol.
        
        Args:
            symbol: Stock symbol or '*' to stop all
            
        Returns:
            JSON with status
        """
        global _tick_news_all_stream
        
        if symbol == "*":
            # Stop all subscriptions
            for sym in list(_tick_news_subscriptions):
                if sym in _tick_news_background_tasks:
                    task = _tick_news_background_tasks[sym]
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                    del _tick_news_background_tasks[sym]
                
                _tick_news_subscriptions.discard(sym)
                if sym in _tick_news_cache:
                    del _tick_news_cache[sym]
            
            _tick_news_all_stream = False
            
            return json.dumps({
                "status": "stopped",
                "message": "All tick news streams stopped"
            })
        
        if symbol not in _tick_news_subscriptions:
            return json.dumps({
                "error": f"No active tick news stream for {symbol}",
                "subscribed": False
            })
        
        # Cancel background task
        if symbol in _tick_news_background_tasks:
            task = _tick_news_background_tasks[symbol]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del _tick_news_background_tasks[symbol]
        
        # Cleanup
        _tick_news_subscriptions.discard(symbol)
        if symbol in _tick_news_cache:
            del _tick_news_cache[symbol]
        
        print(f"[TICK NEWS] Stopped stream for {symbol}")
        
        return json.dumps({
            "status": "stopped",
            "message": f"Tick news streaming stopped for {symbol}"
        })
    
    # --- BroadTape News Resource ---
    
    @mcp.resource("ibkr://broadtape-news")
    async def get_broadtape_news_resource() -> str:
        """Get aggregated real-time news headlines from all subscribed providers.
        
        This resource streams news from ALL available news providers (like BRF, BZ, FLY)
        similar to the TWS News tab. It aggregates BroadTape feeds from all providers
        your account has access to.
        
        Usage:
            1. Call ibkr_start_broadtape_news_resource tool to start streaming
            2. Subscribe to this resource: ibkr://broadtape-news
            3. Read resource to get current headlines
            4. Receive notifications when new headlines arrive from any provider
        
        Returns:
            JSON string with aggregated news headlines from all providers
        """
        if not _broadtape_news_subscribed:
            return json.dumps({
                "error": "BroadTape news not streaming",
                "message": "Call ibkr_start_broadtape_news_resource() first to start streaming",
                "subscribed": False
            })
        
        return json.dumps({
            "subscribed": True,
            "news_items": _broadtape_news_cache[-100:],  # Last 100 headlines
            "total_count": len(_broadtape_news_cache),
            "provider_count": len(_broadtape_provider_tickers)
        })
    
    @mcp.tool()
    async def ibkr_start_broadtape_news_resource(
        ctx: Context[ServerSession, AppContext]
    ) -> str:
        """Start streaming aggregated news headlines from all available providers.
        
        This subscribes to BroadTape feeds from ALL news providers your IB account
        has access to (e.g., Briefing Trader, Benzinga, Fly on the Wall).
        
        Note: This requires active news subscriptions in your IB account.
        
        Returns:
            JSON with resource URI and subscription status
        """
        global _broadtape_news_subscribed, _broadtape_news_task, _broadtape_provider_tickers, _broadtape_news_cache
        
        tws = ctx.request_context.lifespan_context.tws
        
        if not tws or not tws.is_connected():
            return json.dumps({
                "error": "TWS client not connected",
                "message": "Call ibkr_connect first"
            })
        
        if _broadtape_news_subscribed:
            return json.dumps({
                "status": "already_subscribed",
                "resource_uri": "ibkr://broadtape-news",
                "message": "BroadTape news already streaming",
                "provider_count": len(_broadtape_provider_tickers)
            })
        
        # Start background streaming task
        async def stream_to_resource():
            """Background task that streams news from all providers."""
            global _broadtape_provider_tickers
            
            print(f"[BROADTAPE NEWS] Starting aggregated news stream")
            
            try:
                # Get available news providers
                print(f"[BROADTAPE NEWS] Fetching news providers...")
                providers = await tws.ib.reqNewsProvidersAsync()
                print(f"[BROADTAPE NEWS] Found {len(providers)} providers: {[p.code for p in providers]}")
                
                if not providers:
                    print(f"[BROADTAPE NEWS] No news providers available!")
                    return
                
                # Create event queue
                event_queue: asyncio.Queue = asyncio.Queue()
                
                # Subscribe to BroadTape feed for each provider
                tickers = []
                for provider in providers:
                    if provider.code.strip() not in ["BRFG", "FLY", "BZ", "DJ", "DJNL", "DJTOP"]:
                        continue
                    try:
                        contract = Contract()
                        contract.symbol = f"{provider.code}:{provider.code}_ALL"
                        contract.secType = "NEWS"
                        contract.exchange = provider.code
                        
                        print(f"[BROADTAPE NEWS] Subscribing to provider {provider.code}...")
                        
                        qualified = await tws.ib.qualifyContractsAsync(contract)
                        if qualified:
                            contract = qualified[0]
                            contract.exchange = provider.code
                            print(f"[BROADTAPE NEWS] Qualified {provider.code}: conId={contract.conId}")
                        
                        ticker = tws.ib.reqMktData(contract, genericTickList='292', snapshot=False, regulatorySnapshot=False)
                        tickers.append((provider.code, ticker))
                        
                        print(f"[BROADTAPE NEWS] Subscribed to {provider.code}")
                        
                    except Exception as e:
                        print(f"[BROADTAPE NEWS] Failed to subscribe to {provider.code}: {e}")
                
                if not tickers:
                    print(f"[BROADTAPE NEWS] Failed to subscribe to any providers!")
                    return
                
                _broadtape_provider_tickers = [t[1] for t in tickers]
                
                # Set up event handler
                def on_tick_news(ticker, news_tick):
                    """Called when news headline arrives from any provider."""
                    try:
                        provider_code = None
                        for pcode, pticker in tickers:
                            if pticker == ticker:
                                provider_code = pcode
                                break
                        
                        news_item = {
                            "timestamp": int(time.time()),
                            "providerCode": news_tick.providerCode,
                            "articleId": news_tick.articleId,
                            "headline": news_tick.headline,
                            "source": provider_code or news_tick.providerCode,
                            "time": news_tick.time.isoformat() if news_tick.time else None
                        }
                        
                        event_queue.put_nowait(news_item)
                        print(f"[BROADTAPE NEWS] Queued headline from {provider_code}: {news_tick.headline[:60]}...")
                        
                    except Exception as e:
                        print(f"[BROADTAPE NEWS] Error handling news: {e}")
                
                ticker_map = {ticker.contract.conId: (provider_code, ticker) for provider_code, ticker in tickers}
                
                def global_news_handler(ticker, news_tick):
                    if ticker.contract.conId in ticker_map:
                        provider_code, _ = ticker_map[ticker.contract.conId]
                        on_tick_news(ticker, news_tick)
                
                tws.ib.tickNewsEvent += global_news_handler
                print(f"[BROADTAPE NEWS] Attached global news handler for {len(tickers)} providers")
                
                await asyncio.sleep(1.0)
                
                # Process initial queued events
                while not event_queue.empty():
                    news_item = event_queue.get_nowait()
                    _broadtape_news_cache.append(news_item)
                    await ctx.session.send_resource_updated("ibkr://broadtape-news")
                    print(f"[BROADTAPE NEWS] Initial headline: {news_item['headline'][:60]}...")
                
                # Enter main streaming loop
                while True:
                    await tws.ib.updateEvent
                    
                    while not event_queue.empty():
                        news_item = event_queue.get_nowait()
                        _broadtape_news_cache.append(news_item)
                        
                        if len(_broadtape_news_cache) > 1000:
                            _broadtape_news_cache = _broadtape_news_cache[-500:]
                        
                        await ctx.session.send_resource_updated("ibkr://broadtape-news")
                        print(f"[BROADTAPE NEWS] New headline from {news_item['source']}: {news_item['headline'][:60]}... - notification sent")
            
            except asyncio.CancelledError:
                print(f"[BROADTAPE NEWS] Stream cancelled")
                for ticker in _broadtape_provider_tickers:
                    try:
                        tws.ib.cancelMktData(ticker)
                    except:
                        pass
            except Exception as e:
                print(f"[BROADTAPE NEWS] Stream error: {e}")
                import traceback
                traceback.print_exc()
        
        _broadtape_news_cache = []
        _broadtape_news_task = asyncio.create_task(stream_to_resource())
        _broadtape_news_subscribed = True
        
        return json.dumps({
            "status": "subscribed",
            "resource_uri": "ibkr://broadtape-news",
            "message": "BroadTape news streaming started. Headlines from all providers will be aggregated.",
            "note": "Providers will be discovered automatically. Ensure you have news subscriptions enabled in IB Client Portal."
        })
    
    @mcp.tool()
    async def ibkr_stop_broadtape_news_resource(
        ctx: Context[ServerSession, AppContext]
    ) -> str:
        """Stop streaming aggregated BroadTape news.
        
        Returns:
            JSON with status
        """
        global _broadtape_news_subscribed, _broadtape_news_task, _broadtape_provider_tickers, _broadtape_news_cache
        
        if not _broadtape_news_subscribed:
            return json.dumps({
                "error": "BroadTape news not streaming",
                "subscribed": False
            })
        
        tws = ctx.request_context.lifespan_context.tws
        
        # Cancel background task
        if _broadtape_news_task:
            _broadtape_news_task.cancel()
            try:
                await _broadtape_news_task
            except asyncio.CancelledError:
                pass
            _broadtape_news_task = None
        
        # Cancel all ticker subscriptions
        for ticker in _broadtape_provider_tickers:
            try:
                tws.ib.cancelMktData(ticker)
            except:
                pass
        
        # Cleanup
        _broadtape_news_subscribed = False
        _broadtape_provider_tickers = []
        _broadtape_news_cache = []
        
        print(f"[BROADTAPE NEWS] Stopped stream")
        
        return json.dumps({
            "status": "stopped",
            "message": "BroadTape news streaming stopped"
        })
