"""News and market information tools for IBKR TWS API."""

from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession
from ib_async import Stock
from ..models import AppContext


def register_news_tools(mcp: FastMCP):
    """Register news and market information tools."""
    
    @mcp.tool()
    async def ibkr_get_news_providers(
        ctx: Context[ServerSession, AppContext]
    ) -> Dict[str, Any]:
        """Get list of available news providers.
        
        Returns:
            List of news providers with codes and names
        """
        tws = ctx.request_context.lifespan_context.tws
        if not tws or not tws.is_connected():
            return {"error": "TWS client not connected"}
        
        providers = await tws.ib.reqNewsProvidersAsync()
        
        return {
            "providers": [
                {
                    "code": provider.code,
                    "name": provider.name
                }
                for provider in providers
            ],
            "count": len(providers)
        }
    
    @mcp.tool()
    async def ibkr_get_news_articles(
        ctx: Context[ServerSession, AppContext],
        symbol: str,
        providerCodes: str = "BRFUPDN",
        totalResults: int = 10,
        exchange: str = "SMART",
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """Get news articles for a contract.
        
        Args:
            symbol: Contract symbol
            providerCodes: News provider codes (e.g., 'BRFUPDN', 'DJNL')
            totalResults: Maximum number of articles to retrieve
            exchange: Exchange (default: SMART)
            currency: Currency (default: USD)
            
        Returns:
            List of news articles with headlines and timestamps
        """
        tws = ctx.request_context.lifespan_context.tws
        if not tws or not tws.is_connected():
            return {"error": "TWS client not connected"}
        
        contract = Stock(symbol, exchange, currency)
        
        articles = await tws.ib.reqHistoricalNewsAsync(
            conId=contract.conId,
            providerCodes=providerCodes,
            startDateTime="",
            endDateTime="",
            totalResults=totalResults
        )
        
        return {
            "symbol": symbol,
            "articles": [
                {
                    "time": article.time,
                    "providerCode": article.providerCode,
                    "articleId": article.articleId,
                    "headline": article.headline
                }
                for article in articles
            ],
            "count": len(articles)
        }
    
    @mcp.tool()
    async def ibkr_get_news_article(
        ctx: Context[ServerSession, AppContext],
        providerCode: str,
        articleId: str
    ) -> Dict[str, Any]:
        """Get full text of a news article.
        
        Args:
            providerCode: News provider code
            articleId: Article ID from news article list
            
        Returns:
            Full article text
        """
        tws = ctx.request_context.lifespan_context.tws
        if not tws or not tws.is_connected():
            return {"error": "TWS client not connected"}
        
        article = await tws.ib.reqNewsArticleAsync(providerCode, articleId)
        
        return {
            "providerCode": providerCode,
            "articleId": articleId,
            "articleType": article.articleType,
            "articleText": article.articleText
        }
