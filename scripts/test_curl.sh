#!/bin/bash

BASE_URL="http://localhost:8000/api/v1"

echo "=== Test 1: Connect to TWS ==="
curl -X POST $BASE_URL/ibkr_connect \
  -H "Content-Type: application/json" \
  -d '{"host": "127.0.0.1", "port": 7497, "clientId": 1}'

echo -e "\n\n=== Test 2: Get Positions ==="
curl -X POST $BASE_URL/ibkr_get_positions

echo -e "\n\n=== Test 3: Get Historical Data (VTI) ==="
curl -X POST $BASE_URL/ibkr_get_historical_data \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "VTI",
    "durationStr": "30 D",
    "barSizeSetting": "1 day"
  }'

echo -e "\n\n=== Test 4: Get Account Summary ==="
curl -X POST $BASE_URL/ibkr_get_account_summary

echo -e "\n\n=== Test 5: Place Market Order (AAPL) ==="
curl -X POST $BASE_URL/ibkr_place_order \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "action": "BUY",
    "totalQuantity": 1,
    "orderType": "MKT"
  }'

echo -e "\n\n=== Test 6: Get Open Orders ==="
curl -X POST $BASE_URL/ibkr_get_open_orders

echo -e "\n\n=== Test 7: Stream Market Data (5 seconds for SPY) ==="
# The -N flag is important for streaming (no buffering)
# The timeout command is used to limit the streaming duration for the test
timeout 5 curl -N -X POST $BASE_URL/ibkr_stream_market_data \
  -H "Content-Type: application/json" \
  -d '{"symbol": "SPY", "duration_seconds": 5}'

echo -e "\n\n=== Test 8: Disconnect from TWS ==="
curl -X POST $BASE_URL/ibkr_disconnect

echo -e "\n\nAll tests completed!"
