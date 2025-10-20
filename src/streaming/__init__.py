"""Streaming module for WebSocket-based real-time data subscriptions."""

from .websocket_manager import StreamingManager
from .market_data import market_data_stream
from .portfolio import portfolio_stream
from .news import news_stream

__all__ = [
    "StreamingManager",
    "market_data_stream",
    "portfolio_stream",
    "news_stream",
]
