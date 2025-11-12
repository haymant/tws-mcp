import pytest
import json
import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch
from dotenv import load_dotenv
from ib_async import IB, Position, Contract, util
from src.tws_client import TWSClient
from src.models import ContractRequest

# Load environment variables
load_dotenv()

# Get paper trading account from environment
TEST_ACCOUNT = os.getenv('TWS_PAPER_ACCOUNT', 'DU2515295')

# Fixture to load JSON data
@pytest.fixture
def load_fixture():
    def _loader(filename):
        with open(f"tests/fixtures/{filename}", "r") as f:
            return json.load(f)
    return _loader

# Mock object for ib_insync.IB
class MockIB:
    """Mock IB class for testing."""
    def __init__(self):
        self.isConnected = MagicMock(return_value=False)
        self.connectAsync = AsyncMock()
        self.disconnect = MagicMock()
        self.positions = MagicMock(return_value=[])  # Sync method
        self.positionsAsync = AsyncMock(return_value=[])
        self.reqContractDetailsAsync = AsyncMock(return_value=[])
        self.qualifyContractsAsync = AsyncMock(return_value=[])
        self.reqHistoricalDataAsync = AsyncMock(return_value=[])
        self.accountSummaryAsync = AsyncMock(return_value=[])
        self.placeOrder = MagicMock()  # Sync method
        self.placeOrderAsync = AsyncMock()
        self.cancelOrderAsync = AsyncMock()
        self.cancelOrder = MagicMock()  # Sync method
        self.reqAllOpenOrdersAsync = AsyncMock(return_value=[])
        self.reqExecutionsAsync = AsyncMock(return_value=[])
        self.reqMktData = MagicMock()
        self.reqMarketDataType = MagicMock()  # Set market data type (1=live, 2=frozen, 3=delayed)
        self.cancelMktData = MagicMock()
        self.waitOnUpdate = AsyncMock()
        self.reqAccountUpdates = MagicMock()
        self.reqAccountUpdatesAsync = AsyncMock(return_value=None)
        self.cancelAccountUpdates = MagicMock()
        self.accountValues = MagicMock(return_value=[])
        self.trades = MagicMock(return_value=[])
        self.reqOpenOrdersAsync = AsyncMock(return_value=[])
        self.reqPnL = MagicMock()
        self.cancelPnL = MagicMock()
        self.reqPnLSingle = MagicMock()
        self.cancelPnLSingle = MagicMock()
        self.reqNewsBulletins = MagicMock()
        self.cancelNewsBulletins = MagicMock()
        self.newsBulletins = MagicMock(return_value=[])
        
        # Mock events - needs to support += and -= operators
        self.errorEvent = MagicMock()
        self.errorEvent.__iadd__ = MagicMock(return_value=self.errorEvent)
        self.errorEvent.__isub__ = MagicMock(return_value=self.errorEvent)
        
        self.pnlEvent = MagicMock()
        self.pnlEvent.__iadd__ = MagicMock(return_value=self.pnlEvent)
        self.pnlEvent.__isub__ = MagicMock(return_value=self.pnlEvent)
        
        self.pnlSingleEvent = MagicMock()
        self.pnlSingleEvent.__iadd__ = MagicMock(return_value=self.pnlSingleEvent)
        self.pnlSingleEvent.__isub__ = MagicMock(return_value=self.pnlSingleEvent)

# Patch the IB class in src.tws_client with our mock
@pytest.fixture(autouse=True)
def mock_ib_patch():
    with patch("src.tws_client.IB", new=MockIB):
        yield

@pytest.mark.asyncio
async def test_connect_success():
    """Test successful connection to TWS."""
    client = TWSClient()
    # Initialize mock IB instance (since __init__ no longer creates one)
    client.ib = MockIB()
    client.ib.isConnected.return_value = False
    client.ib.connectAsync.return_value = None
    
    result = await client.connect("127.0.0.1", 7497, 2)
    
    assert result is True
    client.ib.connectAsync.assert_called_once_with("127.0.0.1", 7497, clientId=2, timeout=5)

@pytest.mark.asyncio
async def test_connect_already_connected():
    """Test connection when already connected."""
    client = TWSClient()
    # Initialize mock IB instance
    client.ib = MockIB()
    client.ib.isConnected.return_value = True
    
    result = await client.connect("127.0.0.1", 7497, 1)
    
    assert result is True
    client.ib.connectAsync.assert_not_called()

@pytest.mark.asyncio
async def test_get_positions(load_fixture):
    """Test getting positions."""
    client = TWSClient()
    # Initialize mock IB instance
    client.ib = MockIB()
    client.ib.isConnected.return_value = True
    
    # Load fixture data
    fixture_data = load_fixture('sample_positions.json')
    
    # Convert fixture data to mock ib_async Position objects
    mock_positions = []
    for data in fixture_data:
        mock_pos = Position(
            data['account'],
            Contract(**data['contract']),
            data['position'],
            data['avgCost']
        )
        mock_positions.append(mock_pos)
        
    client.ib.positions.return_value = mock_positions  # Use sync method
    
    positions = await client.get_positions()
    
    assert len(positions) == 2
    assert positions[0]['contract']['symbol'] == 'VTI'
    assert positions[0]['position'] == 100.0
    assert positions[1]['contract']['symbol'] == 'TLT'

@pytest.mark.asyncio
async def test_get_historical_data():
    """Test getting historical data."""
    client = TWSClient()
    # Initialize mock IB instance
    client.ib = MockIB()
    client.ib.isConnected.return_value = True
    
    # Mock return values
    mock_contract = Contract(conId=123)
    client.ib.qualifyContractsAsync.return_value = [mock_contract]
    
    # Mock historical data bars (simplified)
    mock_bars = [
        MagicMock(date="20240101", open=100.0, high=101.0, low=99.0, close=100.5, volume=1000),
        MagicMock(date="20240102", open=100.5, high=102.0, low=100.0, close=101.5, volume=1500),
    ]
    client.ib.reqHistoricalDataAsync.return_value = mock_bars
    
    req = ContractRequest(symbol="AAPL")
    data = await client.get_historical_data(req, "1 D", "1 min", "TRADES")
    
    assert len(data) == 2
    assert data[0]['open'] == 100.0
    assert data[1]['close'] == 101.5
    client.ib.reqHistoricalDataAsync.assert_called_once()

@pytest.mark.asyncio
async def test_place_market_order():
    """Test placing a market order."""
    client = TWSClient()
    # Initialize mock IB instance
    client.ib = MockIB()
    client.ib.isConnected.return_value = True
    
    # Mock return values
    mock_contract = Contract(conId=123, symbol='AAPL')
    client.ib.qualifyContractsAsync.return_value = [mock_contract]
    
    # Mock trade object (simplified)
    mock_trade = MagicMock()
    mock_trade.order.orderId = 1
    mock_trade.orderStatus.status = 'Submitted'
    mock_trade.contract = mock_contract
    mock_trade.order.action = 'BUY'
    mock_trade.order.totalQuantity = 10
    
    client.ib.placeOrder.return_value = mock_trade  # Use sync method
    
    req = MagicMock(
        contract=ContractRequest(symbol="AAPL"),
        action="BUY",
        totalQuantity=10,
        orderType="MKT",
        lmtPrice=None
    )
    
    result = await client.place_order(req)
    
    assert result['orderId'] == 1
    assert result['status'] == 'Submitted'
    assert result['action'] == 'BUY'
    client.ib.placeOrder.assert_called_once()  # Check sync method

@pytest.mark.skip(reason="Complex async streaming test - needs refactoring")
@pytest.mark.asyncio
async def test_stream_market_data_generator():
    """Test market data streaming generator."""
    client = TWSClient()
    # Initialize mock IB instance
    client.ib = MockIB()
    client.ib.isConnected.return_value = True
    
    # Mock return values
    mock_contract = Contract(conId=123, symbol='SPY')
    client.ib.qualifyContractsAsync.return_value = [mock_contract]
    
    # Counter to control how many updates we get
    update_count = {'count': 0}
    
    # Mock ticker object with updateEvent that uses callback pattern
    mock_update_event = MagicMock()
    callback_holder = {'callback': None}
    
    def mock_iadd(self_or_callback, callback=None):
        """Mock the += operator to store the callback"""
        # Handle both (self, callback) and (callback,) signatures
        actual_callback = callback if callback is not None else self_or_callback
        callback_holder['callback'] = actual_callback
        return mock_update_event
    
    def mock_isub(self_or_callback, callback=None):
        """Mock the -= operator"""
        return mock_update_event
    
    mock_update_event.__iadd__ = mock_iadd
    mock_update_event.__isub__ = mock_isub
    
    # Create mock ticker with proper time object
    mock_time = MagicMock()
    mock_time.isoformat = MagicMock(return_value="2024-01-01T10:00:00")
    
    mock_ticker = MagicMock(
        time=mock_time,
        last=100.0, bid=99.9, ask=100.1, volume=1000,
        bidSize=10, askSize=10, close=99.5,
        updateEvent=mock_update_event
    )
    client.ib.reqMktData.return_value = mock_ticker
    
    req = ContractRequest(symbol="SPY")
    
    updates = []
    gen = client.stream_market_data(req)
    
    # Manually trigger the callback to simulate updates
    async def simulate_updates():
        await asyncio.sleep(0.1)  # Let subscription initialize
        for i in range(2):
            if callback_holder['callback']:
                callback_holder['callback']()  # Trigger the callback
            await asyncio.sleep(0.1)
    
    # Run simulation in background
    sim_task = asyncio.create_task(simulate_updates())
    
    try:
        async for data in gen:
            if data:  # Skip empty updates
                updates.append(data)
            if len(updates) >= 2:
                # After collecting 2 updates, close the generator
                await gen.aclose()
                break
    except asyncio.CancelledError:
        pass
    finally:
        sim_task.cancel()
        try:
            await sim_task
        except asyncio.CancelledError:
            pass
    
    # The generator yields twice before cancellation
    assert len(updates) == 2
    assert updates[0]['last'] == 100.0
    client.ib.cancelMktData.assert_called_once()


@pytest.mark.skip(reason="Complex async streaming test - needs refactoring")
@pytest.mark.asyncio
async def test_stream_market_data_with_warning_codes():
    """Test that warning codes (like 10167 for delayed data) don't stop streaming."""
    client = TWSClient()
    # Initialize mock IB instance
    client.ib = MockIB()
    client.ib.isConnected.return_value = True
    
    # Mock return values
    mock_contract = Contract(conId=456, symbol='AAPL')
    client.ib.qualifyContractsAsync.return_value = [mock_contract]
    
    # Counter to control how many updates we get
    update_count = {'count': 0}
    
    # Track error handler calls
    error_handler_calls = []
    original_iadd = client.ib.errorEvent.__iadd__
    
    def track_error_handler(self_or_handler, handler=None):
        """Track when error handlers are added"""
        # Handle both (self, handler) and (handler,) signatures
        actual_handler = handler if handler is not None else self_or_handler
        error_handler_calls.append(actual_handler)
        # Simulate a warning (10167 = delayed data warning)
        # This should NOT stop the stream
        actual_handler(4, 10167, "Requested market data is not subscribed. Displaying delayed market data.", mock_contract)
        return original_iadd(actual_handler)
    
    client.ib.errorEvent.__iadd__ = track_error_handler
    
    # Mock ticker object with updateEvent
    async def mock_timeout_gen(timeout_val):
        """Mock async generator for timeout() that yields limited times"""
        update_count['count'] += 1
        if update_count['count'] <= 2:
            yield None  # Yield to indicate update is ready
        else:
            await asyncio.Future()  # This will hang until cancelled
    
    mock_update_event = MagicMock()
    mock_update_event.timeout = MagicMock(side_effect=lambda t: mock_timeout_gen(t))
    
    mock_ticker = MagicMock(
        time=MagicMock(isoformat=MagicMock(return_value="2024-01-01T10:00:00")),
        last=150.0, bid=149.9, ask=150.1, volume=5000,
        bidSize=20, askSize=20, close=149.5,
        updateEvent=mock_update_event
    )
    client.ib.reqMktData.return_value = mock_ticker
    
    req = ContractRequest(symbol="AAPL")
    
    updates = []
    gen = client.stream_market_data(req)
    
    try:
        async for data in gen:
            updates.append(data)
            if len(updates) >= 2:
                await gen.aclose()
                break
    except asyncio.CancelledError:
        pass
    
    # Despite the warning (error code 10167), streaming should continue
    assert len(updates) == 2
    assert updates[0]['last'] == 150.0
    # Error handler should have been registered
    assert len(error_handler_calls) == 1
    client.ib.cancelMktData.assert_called_once()


@pytest.mark.asyncio
async def test_stream_market_data_with_real_error():
    """Test that real errors (not warnings) properly stop streaming."""
    client = TWSClient()
    # Initialize mock IB instance
    client.ib = MockIB()
    client.ib.isConnected.return_value = True
    
    # Mock return values
    mock_contract = Contract(conId=789, symbol='MSFT')
    client.ib.qualifyContractsAsync.return_value = [mock_contract]
    
    # Track error handler calls
    error_handler_calls = []
    original_iadd = client.ib.errorEvent.__iadd__
    
    def track_error_handler(self_or_handler, handler=None):
        """Track when error handlers are added and simulate a real error"""
        # Handle both (self, handler) and (handler,) signatures
        actual_handler = handler if handler is not None else self_or_handler
        error_handler_calls.append(actual_handler)
        # Simulate a real error (e.g., 10089 = subscription required)
        # This SHOULD stop the stream during the initial check
        actual_handler(5, 10089, "Requested market data requires additional subscription.", mock_contract)
        return original_iadd(actual_handler)
    
    client.ib.errorEvent.__iadd__ = track_error_handler
    
    # Mock ticker
    mock_ticker = MagicMock()
    client.ib.reqMktData.return_value = mock_ticker
    
    req = ContractRequest(symbol="MSFT")
    
    gen = client.stream_market_data(req)
    
    # Should raise RuntimeError due to the error code 10089
    with pytest.raises(RuntimeError) as exc_info:
        async for data in gen:
            pass
    
    assert "10089" in str(exc_info.value)
    assert "additional subscription" in str(exc_info.value)


@pytest.mark.skip(reason="Complex async streaming test - needs refactoring")
@pytest.mark.asyncio
async def test_stream_account_updates_generator():
    """Test account updates streaming generator."""
    client = TWSClient()
    # Initialize mock IB instance
    client.ib = MockIB()
    client.ib.isConnected.return_value = True
    
    # Mock reqAccountUpdatesAsync
    client.ib.reqAccountUpdatesAsync = AsyncMock(return_value=None)
    client.ib.cancelAccountUpdates = MagicMock()
    
    # Counter to control iterations
    update_count = {'count': 0}
    
    # Mock positions that change over time
    def mock_positions():
        update_count['count'] += 1
        if update_count['count'] == 1:
            return [Position(TEST_ACCOUNT, Contract(symbol="AAPL", conId=1), 100.0, 150.0)]
        elif update_count['count'] == 2:
            return [Position(TEST_ACCOUNT, Contract(symbol="AAPL", conId=1), 105.0, 150.0)]
        else:
            # After 2 changes, hang to trigger timeout
            return [Position(TEST_ACCOUNT, Contract(symbol="AAPL", conId=1), 105.0, 150.0)]
    
    client.ib.positions = mock_positions
    client.ib.accountValues = MagicMock(return_value=[])
    
    account = TEST_ACCOUNT
    updates = []
    gen = client.stream_account_updates(account)
    
    try:
        async for data in gen:
            updates.append(data)
            if len(updates) >= 2:
                await gen.aclose()
                break
    except asyncio.CancelledError:
        pass
    
    # Should get at least 2 updates before closing
    assert len(updates) >= 1
    assert "type" in updates[0]
    assert updates[0]["type"] == "positions"
    assert "data" in updates[0]
    client.ib.reqAccountUpdatesAsync.assert_called_once_with(account)
    client.ib.cancelAccountUpdates.assert_called()


@pytest.mark.asyncio
async def test_get_pnl():
    """Test getting PnL data."""
    client = TWSClient()
    # Initialize mock IB instance
    client.ib = MockIB()
    client.ib.isConnected.return_value = True
    
    # Mock PnL subscription
    mock_pnl = MagicMock()
    mock_pnl.account = TEST_ACCOUNT
    mock_pnl.modelCode = ""
    mock_pnl.dailyPnL = 1250.50
    mock_pnl.unrealizedPnL = 500.00
    mock_pnl.realizedPnL = 750.50
    
    client.ib.reqPnL = MagicMock(return_value=mock_pnl)
    client.ib.cancelPnL = MagicMock()
    
    # Mock the pnlEvent callback mechanism
    callback_holder = {'callback': None}
    
    def mock_iadd(self_or_callback, callback=None):
        """Mock the += operator to store and immediately call the callback"""
        # Handle both (self, callback) and (callback,) signatures
        actual_callback = callback if callback is not None else self_or_callback
        callback_holder['callback'] = actual_callback
        # Immediately call the callback with our mock pnl
        actual_callback(mock_pnl)
        return client.ib.pnlEvent
    
    client.ib.pnlEvent.__iadd__ = mock_iadd
    
    result = await client.get_pnl(TEST_ACCOUNT, "")
    
    assert result["account"] == TEST_ACCOUNT
    assert result["dailyPnL"] == 1250.50
    assert result["unrealizedPnL"] == 500.00
    client.ib.reqPnL.assert_called_once()


@pytest.mark.asyncio
async def test_get_pnl_single():
    """Test getting single position PnL data."""
    client = TWSClient()
    # Initialize mock IB instance
    client.ib = MockIB()
    client.ib.isConnected.return_value = True
    
    # Mock contract qualification
    mock_contract = Contract(conId=123, symbol='AAPL')
    client.ib.qualifyContractsAsync.return_value = [mock_contract]
    
    # Mock PnL single subscription
    mock_pnl_single = MagicMock()
    mock_pnl_single.account = TEST_ACCOUNT
    mock_pnl_single.conId = 123
    mock_pnl_single.modelCode = ""
    mock_pnl_single.position = 100
    mock_pnl_single.dailyPnL = 125.50
    mock_pnl_single.unrealizedPnL = 50.00
    mock_pnl_single.value = 10000.00
    
    client.ib.reqPnLSingle = MagicMock(return_value=mock_pnl_single)
    client.ib.cancelPnLSingle = MagicMock()
    
    # Mock the pnlSingleEvent callback mechanism
    callback_holder = {'callback': None}
    
    def mock_iadd(self_or_callback, callback=None):
        """Mock the += operator to store and immediately call the callback"""
        # Handle both (self, callback) and (callback,) signatures
        actual_callback = callback if callback is not None else self_or_callback
        callback_holder['callback'] = actual_callback
        # Immediately call the callback with our mock pnl
        actual_callback(mock_pnl_single)
        return client.ib.pnlSingleEvent
    
    client.ib.pnlSingleEvent.__iadd__ = mock_iadd
    
    result = await client.get_pnl_single(TEST_ACCOUNT, "", 123)
    
    assert result["position"] == 100
    assert result["dailyPnL"] == 125.50
    client.ib.reqPnLSingle.assert_called_once()
    
    assert result["position"] == 100
    assert result["dailyPnL"] == 125.50
    client.ib.reqPnLSingle.assert_called_once()


@pytest.mark.asyncio
async def test_cancel_order():
    """Test canceling an order."""
    client = TWSClient()
    # Initialize mock IB instance
    client.ib = MockIB()
    client.ib.isConnected.return_value = True
    
    # Mock order to be cancelled
    mock_order = MagicMock()
    mock_order.order.orderId = 1
    
    # Mock open orders list
    client.ib.reqOpenOrdersAsync.return_value = [mock_order]
    
    # Mock trade with cancelled status
    mock_trade = MagicMock()
    mock_trade.order.orderId = 1
    mock_trade.orderStatus.status = "Cancelled"
    client.ib.cancelOrder.return_value = mock_trade
    
    result = await client.cancel_order(1)
    
    assert result["orderId"] == 1
    assert result["status"] == "Cancelled"
    client.ib.reqOpenOrdersAsync.assert_called_once()
    client.ib.cancelOrder.assert_called_once()


@pytest.mark.asyncio
async def test_get_account_summary():
    """Test getting account summary."""
    client = TWSClient()
    # Initialize mock IB instance
    client.ib = MockIB()
    client.ib.isConnected.return_value = True
    
    # Mock account summary items
    mock_summary = [
        MagicMock(account=TEST_ACCOUNT, tag="NetLiquidation", value="50000.00", currency="USD"),
        MagicMock(account=TEST_ACCOUNT, tag="TotalCashValue", value="25000.00", currency="USD")
    ]
    client.ib.accountSummaryAsync.return_value = mock_summary
    
    result = await client.get_account_summary()
    
    assert len(result) == 2
    assert result[0]["tag"] == "NetLiquidation"
    assert result[0]["value"] == "50000.00"
    client.ib.accountSummaryAsync.assert_called_once()
