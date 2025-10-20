import pytest
import asyncio
import os
import json
from unittest.mock import AsyncMock, MagicMock, patch
from dotenv import load_dotenv
from src.server import (
    ibkr_connect, ibkr_disconnect, ibkr_get_status, ibkr_get_positions,
    ibkr_get_account_summary, 
    ibkr_start_market_data_resource, ibkr_stop_market_data_resource, ibkr_list_active_resource_streams,
    ibkr_start_portfolio_resource, ibkr_stop_portfolio_resource,
    ibkr_start_news_resource, ibkr_stop_news_resource,
    ibkr_get_pnl, ibkr_get_pnl_single, ibkr_place_order, ibkr_cancel_order,
    ibkr_get_open_orders, ibkr_get_executions, ibkr_get_news_providers
)
from src.tws_client import TWSClient
from src.models import ContractRequest, OrderRequest

# Load environment variables
load_dotenv()

# Get paper trading account from environment
TEST_ACCOUNT = os.getenv('TWS_PAPER_ACCOUNT', 'DU2515295')

# Mock the AppContext for the MCP context
@pytest.fixture
def mock_app_context():
    mock_tws_client = MagicMock(spec=TWSClient)
    
    # Mock connection methods
    mock_tws_client.connect = AsyncMock(return_value=True)
    mock_tws_client.disconnect = AsyncMock(return_value=None)
    mock_tws_client.is_connected = MagicMock(return_value=True)
    
    # Mock account/position methods
    mock_tws_client.get_positions = AsyncMock(return_value=[
        {"account": TEST_ACCOUNT, "contract": {"symbol": "VTI"}, "position": 100.0, "avgCost": 200.50}
    ])
    mock_tws_client.get_account_summary = AsyncMock(return_value=[
        {"account": TEST_ACCOUNT, "tag": "NetLiquidation", "value": "50000.00", "currency": "USD"}
    ])
    mock_tws_client.get_pnl = AsyncMock(return_value={
        "dailyPnL": 1250.50, "unrealizedPnL": 500.00, "realizedPnL": 750.50
    })
    mock_tws_client.get_pnl_single = AsyncMock(return_value={
        "position": 100, "dailyPnL": 125.50, "unrealizedPnL": 50.00, "value": 10000.00
    })
    
    # Mock order methods
    mock_tws_client.place_order = AsyncMock(return_value={
        "orderId": 1, "status": "Submitted", "action": "BUY", "totalQuantity": 10
    })
    mock_tws_client.cancel_order = AsyncMock(return_value={"orderId": 1, "status": "Cancelled"})
    mock_tws_client.get_open_orders = AsyncMock(return_value=[
        {"orderId": 1, "action": "BUY", "totalQuantity": 10, "status": "Submitted"}
    ])
    mock_tws_client.get_executions = AsyncMock(return_value=[
        {"execId": "001", "orderId": 1, "shares": 10, "price": 100.50}
    ])
    
    # Mock news methods
    mock_tws_client.get_news_providers = AsyncMock(return_value=[
        {"code": "BRFG", "name": "Briefing.com"}
    ])
    
    # Mock streaming methods (return async generators)
    async def mock_stream_account():
        yield {"positions": [{"symbol": "VTI", "position": 100}]}
        yield {"positions": [{"symbol": "VTI", "position": 105}]}
    
    async def mock_stream_news():
        yield {"msgId": 1, "msgType": 1, "message": "Market Update"}
        yield {"msgId": 2, "msgType": 1, "message": "Trading Alert"}
    
    mock_tws_client.stream_account_updates = MagicMock(return_value=mock_stream_account())
    mock_tws_client.stream_news_bulletins = MagicMock(return_value=mock_stream_news())
    
    # Mock the full context object structure
    mock_ctx = MagicMock()
    mock_ctx.request_context.lifespan_context.tws = mock_tws_client
    
    return mock_ctx

@pytest.mark.asyncio
async def test_ibkr_connect_tool(mock_app_context):
    """Test the ibkr_connect MCP tool."""
    host = "127.0.0.1"
    port = 7496
    clientId = 1
    
    result = await ibkr_connect(mock_app_context, host, port, clientId)
    
    assert result['status'] == 'connected'
    assert result['host'] == host
    assert result['port'] == port
    
    # Verify that the TWS client's connect method was called correctly
    mock_app_context.request_context.lifespan_context.tws.connect.assert_called_once_with(host, port, clientId)

@pytest.mark.asyncio
async def test_ibkr_disconnect_tool(mock_app_context):
    """Test the ibkr_disconnect MCP tool."""
    
    result = await ibkr_disconnect(mock_app_context)
    
    assert result['status'] == 'disconnected'
    mock_app_context.request_context.lifespan_context.tws.disconnect.assert_called_once()

@pytest.mark.asyncio
async def test_ibkr_get_status_tool(mock_app_context):
    """Test the ibkr_get_status MCP tool."""
    
    result = await ibkr_get_status(mock_app_context)
    
    assert result['is_connected'] is True
    mock_app_context.request_context.lifespan_context.tws.is_connected.assert_called_once()

@pytest.mark.asyncio
async def test_ibkr_get_positions_tool(mock_app_context):
    """Test the ibkr_get_positions MCP tool."""
    
    result = await ibkr_get_positions(mock_app_context)
    
    # Verify the result structure and content
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]['contract']['symbol'] == 'VTI'
    
    # Verify that the TWS client's get_positions method was called
    mock_app_context.request_context.lifespan_context.tws.get_positions.assert_called_once()

@pytest.mark.asyncio
async def test_ibkr_get_account_summary_tool(mock_app_context):
    """Test the ibkr_get_account_summary MCP tool."""
    
    result = await ibkr_get_account_summary(mock_app_context)
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]['tag'] == 'NetLiquidation'
    assert result[0]['value'] == '50000.00'
    mock_app_context.request_context.lifespan_context.tws.get_account_summary.assert_called_once()

@pytest.mark.asyncio
async def test_ibkr_start_market_data_resource(mock_app_context):
    """Test starting a market data resource stream."""
    # Mock the session for send_resource_updated
    mock_app_context.session = MagicMock()
    mock_app_context.session.send_resource_updated = AsyncMock()
    
    # Mock stream_market_data to return async generator
    async def mock_market_data_stream(req):
        yield {"time": "2025-10-20T10:00:00", "last": 150.50, "bid": 150.49, "ask": 150.51}
        yield {"time": "2025-10-20T10:00:01", "last": 150.52, "bid": 150.51, "ask": 150.53}
    
    mock_app_context.request_context.lifespan_context.tws.stream_market_data = MagicMock(
        return_value=mock_market_data_stream(None)
    )
    
    result_json = await ibkr_start_market_data_resource(
        mock_app_context,
        symbol="AAPL",
        secType="STK",
        exchange="SMART",
        currency="USD"
    )
    
    result = json.loads(result_json)
    
    assert result["status"] == "subscribed"
    assert result["resource_uri"] == "ibkr://market-data/AAPL"
    assert "contract" in result

@pytest.mark.asyncio
async def test_ibkr_start_market_data_resource_forex(mock_app_context):
    """Test starting a forex market data resource stream with currency differentiation."""
    # Mock the session
    mock_app_context.session = MagicMock()
    mock_app_context.session.send_resource_updated = AsyncMock()
    
    # Mock stream_market_data
    async def mock_market_data_stream(req):
        yield {"time": "2025-10-20T10:00:00", "bid": 150.50, "ask": 150.52}
    
    mock_app_context.request_context.lifespan_context.tws.stream_market_data = MagicMock(
        return_value=mock_market_data_stream(None)
    )
    
    result_json = await ibkr_start_market_data_resource(
        mock_app_context,
        symbol="USD",
        secType="CASH",
        exchange="IDEALPRO",
        currency="JPY"
    )
    
    result = json.loads(result_json)
    
    assert result["status"] == "subscribed"
    assert result["resource_uri"] == "ibkr://market-data/USD.JPY"  # Should include currency
    assert result["contract"]["currency"] == "JPY"

@pytest.mark.asyncio
async def test_ibkr_stop_market_data_resource(mock_app_context):
    """Test stopping a market data resource stream."""
    # First start a stream
    from src.server import _market_data_resource_subscriptions, _resource_background_streams, _market_data_cache
    
    # Create a real asyncio task that we can cancel
    async def dummy_task():
        await asyncio.sleep(10)
    
    mock_task = asyncio.create_task(dummy_task())
    
    _market_data_resource_subscriptions.add("AAPL")
    _resource_background_streams["AAPL"] = mock_task
    _market_data_cache["AAPL"] = {"data": {}, "timestamp": 0, "params": {}}
    
    result_json = await ibkr_stop_market_data_resource("AAPL")
    result = json.loads(result_json)
    
    assert result["status"] == "stopped"
    assert "AAPL" not in _market_data_resource_subscriptions
    
    # Clean up
    try:
        mock_task.cancel()
        await mock_task
    except asyncio.CancelledError:
        pass

@pytest.mark.asyncio
async def test_ibkr_list_active_resource_streams(mock_app_context):
    """Test listing active resource streams."""
    from src.server import (
        _market_data_resource_subscriptions, _market_data_cache,
        _portfolio_resource_subscriptions, _portfolio_cache,
        _news_resource_subscription, _news_cache
    )
    import src.server as server_module
    
    # Clean up any existing state first
    _market_data_resource_subscriptions.clear()
    _market_data_cache.clear()
    _portfolio_resource_subscriptions.clear()
    _portfolio_cache.clear()
    
    # Mock market data stream
    _market_data_resource_subscriptions.add("AAPL")
    _market_data_cache["AAPL"] = {
        "data": {"last": 150.50},
        "timestamp": 123456.789,
        "params": {"symbol": "AAPL", "secType": "STK", "exchange": "SMART", "currency": "USD"}
    }
    
    # Mock portfolio stream
    _portfolio_resource_subscriptions.add("U123456")
    _portfolio_cache["U123456"] = {
        "positions": [{"symbol": "AAPL", "position": 100}],
        "values": [],
        "timestamp": 123456.789
    }
    
    # Mock news stream
    server_module._news_resource_subscription = True
    server_module._news_cache = {
        "bulletins": [{"msgId": 1, "message": "Test bulletin"}],
        "timestamp": 123456.789
    }
    
    result_json = await ibkr_list_active_resource_streams()
    result = json.loads(result_json)
    
    assert "market_data" in result
    assert result["market_data"]["count"] == 1
    assert result["market_data"]["streams"][0]["resource_id"] == "AAPL"
    
    assert "portfolio" in result
    assert result["portfolio"]["count"] == 1
    assert result["portfolio"]["streams"][0]["account"] == "U123456"
    
    assert "news" in result
    assert result["news"]["count"] == 1
    assert result["news"]["streams"][0]["resource_uri"] == "ibkr://news-bulletins"
    
    # Clean up
    server_module._news_resource_subscription = False

@pytest.mark.asyncio
async def test_ibkr_start_portfolio_resource(mock_app_context):
    """Test starting a portfolio resource stream."""
    from src.server import _portfolio_resource_subscriptions, _portfolio_cache
    
    # Clean up any existing state
    _portfolio_resource_subscriptions.clear()
    _portfolio_cache.clear()
    
    mock_app_context.session = MagicMock()
    mock_app_context.session.send_resource_updated = AsyncMock()
    
    # Mock stream_account_updates
    async def mock_account_stream(account):
        yield {"type": "position", "data": {"symbol": "AAPL", "position": 100}}
        yield {"type": "accountValue", "data": {"tag": "NetLiquidation", "value": 50000}}
    
    mock_app_context.request_context.lifespan_context.tws.stream_account_updates = MagicMock(
        return_value=mock_account_stream("U123456")
    )
    
    result_json = await ibkr_start_portfolio_resource(
        mock_app_context,
        account="U123456"
    )
    
    result = json.loads(result_json)
    
    assert result["status"] == "subscribed"
    assert result["resource_uri"] == "ibkr://portfolio/U123456"
    assert result["account"] == "U123456"

@pytest.mark.asyncio
async def test_ibkr_stop_portfolio_resource(mock_app_context):
    """Test stopping a portfolio resource stream."""
    from src.server import _portfolio_resource_subscriptions, _portfolio_background_streams, _portfolio_cache
    
    # Create a real asyncio task
    async def dummy_task():
        await asyncio.sleep(10)
    
    mock_task = asyncio.create_task(dummy_task())
    
    _portfolio_resource_subscriptions.add("U123456")
    _portfolio_background_streams["U123456"] = mock_task
    _portfolio_cache["U123456"] = {"positions": [], "values": [], "timestamp": 0}
    
    result_json = await ibkr_stop_portfolio_resource("U123456")
    result = json.loads(result_json)
    
    assert result["status"] == "stopped"
    assert "U123456" not in _portfolio_resource_subscriptions
    
    # Clean up
    try:
        mock_task.cancel()
        await mock_task
    except asyncio.CancelledError:
        pass

@pytest.mark.asyncio
async def test_ibkr_get_news_bulletins_resource(mock_app_context):
    """Test reading the news bulletins resource."""
    from src.server import get_news_bulletins_resource, _news_cache
    import src.server as server_module
    
    # Test when not subscribed
    server_module._news_resource_subscription = False
    result_json = await get_news_bulletins_resource()
    result = json.loads(result_json)
    
    assert "error" in result
    assert result["subscribed"] is False
    
    # Test when subscribed with bulletins
    server_module._news_resource_subscription = True
    server_module._news_cache = {
        "bulletins": [
            {"msgId": 1, "msgType": 1, "message": "Market Update", "time": "2025-10-20T10:00:00"},
            {"msgId": 2, "msgType": 1, "message": "Trading Alert", "time": "2025-10-20T10:05:00"}
        ],
        "timestamp": 123456.789
    }
    
    result_json = await get_news_bulletins_resource()
    result = json.loads(result_json)
    
    assert result["subscribed"] is True
    assert result["count"] == 2
    assert len(result["bulletins"]) == 2
    assert result["bulletins"][0]["message"] == "Market Update"
    assert result["last_update"] == 123456.789
    
    # Clean up
    server_module._news_resource_subscription = False

@pytest.mark.asyncio
async def test_ibkr_stop_news_resource(mock_app_context):
    """Test stopping a news bulletins resource stream."""
    from src.server import _news_resource_subscription, _news_background_stream, _news_cache
    import src.server as server_module
    
    # Create a real asyncio task
    async def dummy_task():
        await asyncio.sleep(10)
    
    mock_task = asyncio.create_task(dummy_task())
    
    # Set the global variables directly on the module
    server_module._news_resource_subscription = True
    server_module._news_background_stream = mock_task
    
    result_json = await ibkr_stop_news_resource()
    result = json.loads(result_json)
    
    assert result["status"] == "stopped"
    assert server_module._news_resource_subscription is False
    
    # Clean up
    try:
        if not mock_task.done():
            mock_task.cancel()
            await mock_task
    except asyncio.CancelledError:
        pass

@pytest.mark.asyncio
async def test_ibkr_start_news_resource(mock_app_context):
    """Test starting a news bulletins resource stream."""
    mock_app_context.session = MagicMock()
    mock_app_context.session.send_resource_updated = AsyncMock()
    
    # Mock subscribe_news_bulletins
    mock_app_context.request_context.lifespan_context.tws.subscribe_news_bulletins = AsyncMock()
    
    result_json = await ibkr_start_news_resource(
        mock_app_context,
        allMessages=True
    )
    
    result = json.loads(result_json)
    
    assert result["status"] == "subscribed"
    assert result["resource_uri"] == "ibkr://news-bulletins"

@pytest.mark.asyncio
async def test_ibkr_get_pnl_tool(mock_app_context):
    """Test the ibkr_get_pnl MCP tool."""
    
    result = await ibkr_get_pnl(mock_app_context, account=TEST_ACCOUNT, modelCode="")
    
    assert "dailyPnL" in result
    assert result["dailyPnL"] == 1250.50
    mock_app_context.request_context.lifespan_context.tws.get_pnl.assert_called_once()

@pytest.mark.asyncio
async def test_ibkr_get_pnl_single_tool(mock_app_context):
    """Test the ibkr_get_pnl_single MCP tool."""
    
    result = await ibkr_get_pnl_single(mock_app_context, account=TEST_ACCOUNT, modelCode="", conId=123)
    
    assert "position" in result
    assert result["position"] == 100
    mock_app_context.request_context.lifespan_context.tws.get_pnl_single.assert_called_once()

@pytest.mark.asyncio
async def test_ibkr_place_order_tool(mock_app_context):
    """Test the ibkr_place_order MCP tool."""
    
    result = await ibkr_place_order(
        mock_app_context, 
        symbol="AAPL",
        action="BUY",
        totalQuantity=10,
        orderType="MKT"
    )
    
    assert result["orderId"] == 1
    assert result["status"] == "Submitted"
    mock_app_context.request_context.lifespan_context.tws.place_order.assert_called_once()

@pytest.mark.asyncio
async def test_ibkr_cancel_order_tool(mock_app_context):
    """Test the ibkr_cancel_order MCP tool."""
    
    result = await ibkr_cancel_order(mock_app_context, orderId=1)
    
    assert result["orderId"] == 1
    assert result["status"] == "Cancelled"
    mock_app_context.request_context.lifespan_context.tws.cancel_order.assert_called_once_with(1)

@pytest.mark.asyncio
async def test_ibkr_get_open_orders_tool(mock_app_context):
    """Test the ibkr_get_open_orders MCP tool."""
    
    result = await ibkr_get_open_orders(mock_app_context)
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["orderId"] == 1
    mock_app_context.request_context.lifespan_context.tws.get_open_orders.assert_called_once()

@pytest.mark.asyncio
async def test_ibkr_get_executions_tool(mock_app_context):
    """Test the ibkr_get_executions MCP tool."""
    
    result = await ibkr_get_executions(mock_app_context)
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["execId"] == "001"
    mock_app_context.request_context.lifespan_context.tws.get_executions.assert_called_once()

@pytest.mark.asyncio
async def test_ibkr_get_news_providers_tool(mock_app_context):
    """Test the ibkr_get_news_providers MCP tool."""
    
    result = await ibkr_get_news_providers(mock_app_context)
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["code"] == "BRFG"
    mock_app_context.request_context.lifespan_context.tws.get_news_providers.assert_called_once()

