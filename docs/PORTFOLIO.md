# Portfolio Streaming and Account Data

Complete guide to accessing account information, positions, and P&L through the IB TWS API.

## Overview

The TWS API provides several ways to access portfolio data:

1. **Account Summary** - Snapshot of account metrics (cash, buying power, etc.)
2. **Positions** - Current holdings with P&L
3. **Portfolio Streaming** - Real-time updates to positions and account values
4. **P&L Tracking** - Account and position-level profit/loss

## Quick Start

```javascript
// Connect first
await ibkr_connect();

// Get snapshot
const summary = await ibkr_get_account_summary({account: "U1234567"});
const positions = await ibkr_get_positions();

// Start streaming
await ibkr_start_portfolio_resource({account: "U1234567"});
subscribe("ibkr://portfolio/U1234567");

// Monitor P&L
const pnl = await ibkr_get_pnl({account: "U1234567"});
```

---

## Account Summary

### Get Account Metrics

**Request:**
```javascript
await ibkr_get_account_summary({
  account: "U1234567"  // optional, defaults to all accounts
});
```

**Response:**
```json
{
  "TotalCashValue": "50000.00",
  "NetLiquidation": "75000.00",
  "GrossPositionValue": "25000.00",
  "BuyingPower": "100000.00",
  "AvailableFunds": "50000.00",
  "ExcessLiquidity": "45000.00",
  "Cushion": "0.60"
}
```

### Available Tags

| Tag | Description |
|-----|-------------|
| `TotalCashValue` | Total cash in account |
| `NetLiquidation` | Total account value |
| `GrossPositionValue` | Total value of positions |
| `BuyingPower` | Available buying power |
| `AvailableFunds` | Funds available for withdrawal |
| `ExcessLiquidity` | Excess liquidity |
| `Cushion` | Equity with loan value / Net liquidation |

### Use Cases

- Account health checks
- Available cash for trading
- Margin calculations
- Risk assessment

---

## Positions

### Get Current Positions

**Request:**
```javascript
await ibkr_get_positions({
  account: "U1234567"  // optional
});
```

**Response:**
```json
[
  {
    "account": "U1234567",
    "symbol": "AAPL",
    "secType": "STK",
    "position": 100,
    "avgCost": 150.50,
    "marketPrice": 152.30,
    "marketValue": 15230.00,
    "unrealizedPNL": 180.00,
    "realizedPNL": 0.00
  },
  {
    "account": "U1234567",
    "symbol": "MSFT",
    "secType": "STK",
    "position": 50,
    "avgCost": 300.00,
    "marketPrice": 305.50,
    "marketValue": 15275.00,
    "unrealizedPNL": 275.00,
    "realizedPNL": 0.00
  }
]
```

### Position Fields

| Field | Description |
|-------|-------------|
| `account` | Account ID |
| `symbol` | Contract symbol |
| `secType` | Security type (STK, FUT, OPT, etc.) |
| `position` | Number of shares/contracts (negative = short) |
| `avgCost` | Average cost per share |
| `marketPrice` | Current market price |
| `marketValue` | Total position value |
| `unrealizedPNL` | Unrealized profit/loss |
| `realizedPNL` | Realized profit/loss for the day |

### Use Cases

- Portfolio analysis
- Rebalancing decisions
- Risk management
- Tax planning

---

## Portfolio Streaming

### Real-Time Updates

Stream live updates to positions and account values.

**Start:**
```javascript
await ibkr_start_portfolio_resource({
  account: "U1234567"  // required
});
```

**Response:**
```json
{
  "status": "subscribed",
  "resource_uri": "ibkr://portfolio/U1234567",
  "account": "U1234567",
  "message": "Portfolio streaming started"
}
```

**Subscribe:**
```javascript
subscribe("ibkr://portfolio/U1234567");
```

**Updates:**
```json
{
  "timestamp": 1697654321,
  "positions": [
    {
      "symbol": "AAPL",
      "position": 100,
      "avgCost": 150.50,
      "marketPrice": 152.50,  // Price changed
      "marketValue": 15250.00,
      "unrealizedPNL": 200.00  // P&L updated
    }
  ],
  "account_values": {
    "NetLiquidation": "75200.00",  // Account value changed
    "UnrealizedPnL": "200.00",
    "RealizedPnL": "0.00"
  }
}
```

**Stop:**
```javascript
await ibkr_stop_portfolio_resource({account: "U1234567"});
```

### What Triggers Updates

- Price changes (position values update)
- New trades (positions added/modified)
- Account deposits/withdrawals
- Dividends/interest
- Margin changes

### Event-Driven Architecture

Portfolio streaming uses IB's event system:

```python
# Setup
self.ib.client.reqAccountUpdates(True, account)

# Event handlers
self.ib.updatePortfolioEvent += on_portfolio_update
self.ib.accountValueEvent += on_account_value_update

# Main loop
while True:
    await self.ib.updateEvent  # Wait for IB events
    
    # Process updates
    await send_resource_updated(uri)
```

### Key Features

- **Non-blocking:** Event-driven, doesn't poll
- **Real-time:** Updates as they happen
- **Efficient:** Only changed data sent
- **Reliable:** Uses IB's native event system

### Use Cases

- Real-time portfolio monitoring
- Automated rebalancing triggers
- Risk management alerts
- Live P&L tracking

---

## P&L Tracking

### Account-Level P&L

**Request:**
```javascript
await ibkr_get_pnl({
  account: "U1234567"  // required
});
```

**Response:**
```json
{
  "account": "U1234567",
  "dailyPnL": 450.50,
  "unrealizedPnL": 1200.00,
  "realizedPnL": -100.25
}
```

### Position-Level P&L

**Request:**
```javascript
await ibkr_get_pnl_single({
  account: "U1234567",
  symbol: "AAPL",
  secType: "STK",      // optional
  exchange": "SMART",   // optional
  currency: "USD"       // optional
});
```

**Response:**
```json
{
  "account": "U1234567",
  "symbol": "AAPL",
  "position": 100,
  "dailyPnL": 200.00,
  "unrealizedPnL": 180.00,
  "realizedPnL": 20.00,
  "value": 15230.00
}
```

### P&L Fields

| Field | Description |
|-------|-------------|
| `dailyPnL` | Total P&L for the day (realized + unrealized) |
| `unrealizedPnL` | Open position P&L |
| `realizedPnL` | Closed position P&L for the day |
| `value` | Current market value |

### Use Cases

- Daily performance tracking
- Tax lot management
- Performance attribution
- Trading strategy evaluation

---

## Comparison: Snapshot vs Streaming

| Feature | Snapshot | Streaming |
|---------|----------|-----------|
| **Method** | `ibkr_get_positions` | `ibkr_start_portfolio_resource` |
| **Updates** | Manual (call each time) | Automatic (real-time) |
| **Overhead** | Higher (repeated calls) | Lower (one subscription) |
| **Use for** | Periodic checks | Continuous monitoring |
| **Latency** | On-demand | Real-time |

**Choose Streaming When:**
- Need real-time updates
- Monitoring active positions
- Automated systems
- Live dashboards

**Choose Snapshot When:**
- Periodic checks
- Historical analysis
- One-time queries
- Reporting

---

## Complete Example Workflow

### Initial Setup
```javascript
// 1. Connect
await ibkr_connect();

// 2. Get account snapshot
const summary = await ibkr_get_account_summary({
  account: "U1234567"
});

console.log(`Net Liquidation: $${summary.NetLiquidation}`);
console.log(`Buying Power: $${summary.BuyingPower}`);

// 3. Get positions
const positions = await ibkr_get_positions();

for (const pos of positions) {
  console.log(`${pos.symbol}: ${pos.position} shares @ $${pos.marketPrice}`);
  console.log(`  Unrealized P&L: $${pos.unrealizedPNL}`);
}
```

### Start Streaming
```javascript
// 4. Start portfolio streaming
await ibkr_start_portfolio_resource({account: "U1234567"});

// 5. Subscribe to resource
subscribe("ibkr://portfolio/U1234567");

// Now you'll receive real-time updates
```

### Monitor P&L
```javascript
// 6. Check account P&L
const accountPnL = await ibkr_get_pnl({account: "U1234567"});
console.log(`Daily P&L: $${accountPnL.dailyPnL}`);

// 7. Check position P&L
const applPnL = await ibkr_get_pnl_single({
  account: "U1234567",
  symbol: "AAPL"
});
console.log(`AAPL P&L: $${applPnL.dailyPnL}`);
```

### Cleanup
```javascript
// 8. Stop streaming when done
await ibkr_stop_portfolio_resource({account: "U1234567"});
```

---

## Multiple Accounts

### List All Accounts

```javascript
// Get all accounts
const summary = await ibkr_get_account_summary();  // No account param

// Returns data for all managed accounts
```

### Stream Multiple Accounts

```javascript
// Start streams for each account
const accounts = ["U1234567", "U7654321"];

for (const account of accounts) {
  await ibkr_start_portfolio_resource({account});
  subscribe(`ibkr://portfolio/${account}`);
}

// Monitor all accounts simultaneously
```

### Check Active Streams

```javascript
const streams = await ibkr_list_active_resource_streams();

console.log(streams.portfolio);
// [
//   {account: "U1234567", resource_uri: "ibkr://portfolio/U1234567", ...},
//   {account: "U7654321", resource_uri: "ibkr://portfolio/U7654321", ...}
// ]
```

---

## Troubleshooting

### No Portfolio Updates

**Check:**
1. Verify account ID correct
2. Ensure positions exist
3. Check connection status
4. Verify streaming started

**Solution:**
```javascript
// Verify connection
const status = await ibkr_get_status();

// Check active streams
const streams = await ibkr_list_active_resource_streams();

// Restart if needed
await ibkr_stop_portfolio_resource({account: "U1234567"});
await ibkr_start_portfolio_resource({account: "U1234567"});
```

### Incorrect P&L Values

**Causes:**
- Positions still settling
- Corporate actions not reflected
- Different base currency
- Commissions not included

**Solution:**
- Wait for settlement
- Check position details
- Verify currency settings
- Include commission in calculations

### Missing Positions

**Causes:**
- Position just opened (not settled)
- Different account
- Filtered by security type

**Solution:**
```javascript
// Get all positions (no filter)
const allPositions = await ibkr_get_positions();

// Check account summary
const summary = await ibkr_get_account_summary({account: "U1234567"});
```

---

## Best Practices

### Streaming
1. **One stream per account** - Don't start multiple streams for same account
2. **Stop when done** - Clean up unused streams
3. **Monitor status** - Use `ibkr_list_active_resource_streams`
4. **Handle disconnects** - Reconnect and restart streams

### Performance
1. **Use streaming for real-time** - More efficient than repeated snapshots
2. **Batch queries** - Get all positions at once, not one by one
3. **Cache data** - Store position snapshots, update from stream

### Risk Management
1. **Monitor margin** - Track cushion and excess liquidity
2. **Set P&L alerts** - Trigger on daily P&L thresholds
3. **Track exposure** - Monitor gross position value
4. **Verify orders** - Check positions after trades

### Reporting
1. **Daily snapshots** - Capture end-of-day positions
2. **P&L tracking** - Log daily P&L for records
3. **Performance attribution** - Track per-position P&L
4. **Tax reporting** - Monitor realized P&L

---

## Event Loop Fix (Technical Note)

Portfolio streaming uses `self.ib.client.reqAccountUpdates()` directly instead of async wrappers to avoid event loop conflicts:

```python
# ✅ CORRECT - Direct client API
self.ib.client.reqAccountUpdates(True, account)

# ❌ WRONG - Async wrapper causes event loop issues
await self.ib.reqAccountUpdatesAsync(True, account)
```

This ensures:
- No event loop blocking
- Proper event handler attachment
- Reliable streaming

---

## See Also

- [TOOLS.md](TOOLS.md) - Complete tools reference
- [DESIGN.md](DESIGN.md) - Architecture overview
- [MARKET_DATA.md](MARKET_DATA.md) - Market data streaming
- [NEWS.md](NEWS.md) - News streaming
- [IB Portfolio API](https://interactivebrokers.github.io/tws-api/account_updates.html)
