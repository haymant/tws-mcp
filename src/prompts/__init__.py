"""MCP Prompts for IBKR TWS workflows."""

from .portfolio import register_portfolio_prompts
from .trading import register_trading_prompts
from .analysis import register_analysis_prompts


def register_all_prompts(mcp):
    """Register all MCP prompts for guided workflows."""
    register_portfolio_prompts(mcp)
    register_trading_prompts(mcp)
    register_analysis_prompts(mcp)
