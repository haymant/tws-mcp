# Market Data Streaming and Historical Data

Complete guide to accessing market data through the IB TWS API.

## Overview

The TWS API provides two ways to access market data:

1. **Historical Data** - Past price bars for analysis
2. **Real-Time Streaming** - Live price updates

## Quick Start

```javascript
// Connect first
await ibkr_connect();

// Get historical data
const history = await ibkr_get_historical_data({
  symbol: "AAPL",
  durationStr: "5 D",
  barSizeSetting: "1 hour"
});

// Start real-time streaming
await ibkr_start_market_data_resource({symbol: "AAPL"});
subscribe("ibkr://market-data/AAPL_STK_SMART_USD");
```

---

## Historical Data

### Get Historical Bars

**Request:**
```javascript
await ibkr_get_historical_data({
  symbol: "AAPL",
  secType: "STK",           // optional, default: "STK"
  exchange: "SMART",         // optional, default: "SMART"
  currency: "USD",           // optional, default: "USD"
  durationStr: "5 D",        // required
  barSizeSetting: "1 hour",  // required
  whatToShow: "TRADES"       // optional, default: "TRADES"
});
```

**Response:**
```json
[
  {
    "date": "2025-10-18 09:30:00",
    "open": 150.25,
    "high": 151.00,
    "low": 150.10,
    "close": 150.80,
    "volume": 1250000,
    "average": 150.65,
    "barCount": 5000
  }
]
```

### Duration Strings

| String | Description |
|--------|-------------|
| `"60 S"` | 60 seconds |
| `"30 D"` | 30 days |
| `"1 W"` | 1 week |
| `"1 M"` | 1 month |
| `"1 Y"` | 1 year |

### Bar Sizes

| Size | Description |
|------|-------------|
| `"1 secs"` | 1 second bars |
| `"5 secs"` | 5 second bars |
| `"1 min"` | 1 minute bars |
| `"5 mins"` | 5 minute bars |
| `"1 hour"` | 1 hour bars |
| `"1 day"` | Daily bars |

### What To Show

| Value | Description |
|-------|-------------|
| `"TRADES"` | Actual trades |
| `"MIDPOINT"` | Bid/ask midpoint |
| `"BID"` | Bid prices only |
| `"ASK"` | Ask prices only |
| `"HISTORICAL_VOLATILITY"` | Historical volatility |
| `"OPTION_IMPLIED_VOLATILITY"` | Implied volatility |

---

## Real-Time Streaming

### Start Streaming

**Request:**
```javascript
await ibkr_start_market_data_resource({
  symbol: "AAPL",
  secType: "STK",      // optional
  exchange: "SMART",   // optional
  currency: "USD"      // optional
});
```

**Response:**
```json
{
  "status": "subscribed",
  "resource_uri": "ibkr://market-data/AAPL_STK_SMART_USD",
  "resource_id": "AAPL_STK_SMART_USD",
  "message": "Market data streaming started"
}
```

**Subscribe:**
```javascript
subscribe("ibkr://market-data/AAPL_STK_SMART_USD");
```

**Updates:**
```json
{
  "timestamp": 1697654321,
  "symbol": "AAPL",
  "last": 152.50,
  "bid": 152.48,
  "ask": 152.52,
  "bidSize": 100,
  "askSize": 200,
  "volume": 15234567,
  "high": 153.00,
  "low": 151.50,
  "close": 152.30
}
```

**Stop:**
```javascript
await ibkr_stop_market_data_resource({
  resource_id: "AAPL_STK_SMART_USD"
});
```

### Update Frequency

- **Tick-by-tick:** Every price change
- **Throttled:** IB may throttle high-frequency updates
- **Delayed:** Free accounts get delayed data

---

## Contract Examples

Below are examples of contract definitions for various security types.

## References
1. https://www.interactivebrokers.com/campus/trading-lessons/defining-contracts-in-the-tws-api/
2. https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-doc/#hist-aggtrades

FX Pairs
========

*   Contract contract = new Contract(); contract.Symbol = "EUR"; contract.SecType = "CASH"; contract.Currency = "GBP"; contract.Exchange = "IDEALPRO";
    
```json
{"symbol":"USD","secType":"CASH","exchange":"IDEALPRO","currency":"SGD","durationStr":"1 W","barSizeSetting":"1 day","whatToShow":"MIDPOINT"}
```

Cryptocurrency
==============

*   Contract contract = new Contract(); contract.Symbol = "ETH"; contract.SecType = "CRYPTO"; contract.Exchange = "PAXOS"; contract.Currency = "USD";
    
```json
{"symbol":"ETH","secType":"CRYPTO","exchange":"PAXOS","currency":"USD","durationStr":"1 W","barSizeSetting":"1 day","whatToShow":"AGGTRADES"}
```

Stocks
======

*   Contract contract = new Contract(); contract.Symbol = "SPY"; contract.SecType = "STK"; contract.Currency = "USD"; contract.Exchange = "ARCA";
    
```json
{"symbol":"FLCH","secType":"STK","exchange":"SMART","currency":"USD","durationStr":"1 W","barSizeSetting":"1 day","whatToShow":"TRADES"}
{"symbol":"700","secType":"STK","exchange":"SEHK","currency":"HKD","durationStr":"1 W","barSizeSetting":"1 day","whatToShow":"TRADES"}
```

For certain smart-routed stock contracts that have the same **symbol**, **currency** and **exchange**, you would also need to specify the **primary exchange** attribute to uniquely define the contract. This should be defined as the native exchange of a contract, and is good practice to include for all stocks:

*   Contract contract = new Contract(); contract.Symbol = "SPY"; contract.SecType = "STK"; contract.Currency = "USD"; contract.Exchange = "SMART"; contract.PrimaryExch = "ARCA";
    

For the purpose of requesting market data, the routing exchange and primary exchange can be specified in a single 'exchange' field if they are separated by a valid component exchange separator, for instance exchange = "SMART:ARCA". The default separators available are colon ":" and slash "/". Other component exchange separators can be defined using the field defined in TWS Global Configuration under API -> Settings. The component exchange separator syntax in TWS versions prior to 971 can only be used to request market data and not to place orders.

Contracts specified by FIGI
===========================

Contracts could also be defined by FIGI. In the example below, FIGI code specifies AAPL STK contract.

*   Contract contract = new Contract(); contract.SecIdType = "FIGI"; contract.SecId = "BBG000B9XRY4"; contract.Exchange = "SMART";
    

Stock Contract with IPO price
=============================

An example Stock contract with IPO price.

*   Contract contract = new Contract(); contract.Symbol = "EMCGU"; contract.SecType = "STK"; contract.Exchange = "SMART"; contract.Currency = "USD";
    

Indexes
=======

ISINs for indices which are available in IB's database are available in the API as of TWS 965+.

*   Contract contract = new Contract(); contract.Symbol = "DAX"; contract.SecType = "IND"; contract.Currency = "EUR"; contract.Exchange = "EUREX";

```json
{"symbol":"DAX","secType":"IND","exchange":"EUREX","currency":"EUR","durationStr":"1 W","barSizeSetting":"1 day","whatToShow":"TRADES"}
```

CFDs
====

*   Contract contract = new Contract(); contract.Symbol = "IBDE30"; contract.SecType = "CFD"; contract.Currency = "EUR"; contract.Exchange = "SMART";
    

Futures
=======

A regular futures contract is commonly defined using an expiry and the symbol field defined as the symbol of the underlying. Historical data for futures is available up to 2 years after they expire by setting the includeExpired flag within the Contract class to True.

*   Contract contract = new Contract(); contract.Symbol = "GBL"; contract.SecType = "FUT"; contract.Exchange = "EUREX"; contract.Currency = "EUR"; contract.LastTradeDateOrContractMonth = "202303";
    

By contract the 'local symbol' field is IB's symbol for the future itself (the Symbol within the TWS' Contract Description dialog). Since a local symbol uniquely defines a future, an expiry is not necessary.

*   Contract contract = new Contract(); contract.SecType = "FUT"; contract.Exchange = "EUREX"; contract.Currency = "EUR"; contract.LocalSymbol = "FGBL MAR 23";
    

Occasionally, you can expect to have more than a single future contract for the same underlying with the same expiry. To rule out the ambiguity, the contract's **multiplier** can be given as shown below:

*   Contract contract = new Contract(); contract.Symbol = "DAX"; contract.SecType = "FUT"; contract.Exchange = "EUREX"; contract.Currency = "EUR"; contract.LastTradeDateOrContractMonth = "202303"; contract.Multiplier = "1";
    

Continuous futures are available from the API with **TWS v971** and higher. Continuous futures cannot be used with real time data or to place orders, but only for historical data.

*   Contract contract = new Contract(); contract.Symbol = "GBL"; contract.SecType = "CONTFUT"; contract.Exchange = "EUREX";
    

The security type "FUT+CONTFUT" can be used to request contract details about the futures and continuous futures on an underlying. This security type cannot be used with other functionality.

*   Contract contract = new Contract(); contract.Symbol = "GBL"; contract.SecType = "FUT+CONTFUT"; contract.Exchange = "EUREX";
    

Options
=======

Options, like futures, also require an expiration date plus a **strike** and a **multiplier**:

*   Contract contract = new Contract(); contract.Symbol = "GOOG"; contract.SecType = "OPT"; contract.Exchange = "BOX"; contract.Currency = "USD"; contract.LastTradeDateOrContractMonth = "20170120"; contract.Strike = 615; contract.Right = "C"; contract.Multiplier = "100";
    

It is not unusual to find many option contracts with an almost identical description (i.e. underlying symbol, strike, last trading date, multiplier, etc.). Adding more details such as the **trading class** will help:

*   Contract contract = new Contract(); contract.Symbol = "SANT"; contract.SecType = "OPT"; contract.Exchange = "MEFFRV"; contract.Currency = "EUR"; contract.LastTradeDateOrContractMonth = "20190621"; contract.Strike = 7.5; contract.Right = "C"; contract.Multiplier = "100"; contract.TradingClass = "SANEU";
    

The OCC options symbol can be used to define an option contract in the API through the option's 'local symbol' field.

*   Contract contract = new Contract(); //Watch out for the spaces within the local symbol! contract.LocalSymbol = "P BMW 20221216 72 M"; contract.SecType = "OPT"; contract.Exchange = "EUREX"; contract.Currency = "EUR";
    

```json
{"symbol":"AAPL","secType":"STK","exchange":"SMART","currency":"USD","durationStr":"1 Y","barSizeSetting":"1 month","whatToShow":"HISTORICAL_VOLATILITY"}
```

Futures Options
===============

**Important: In TWS versions prior to 972**, if defining a futures option that has a price magnifier using the strike price, the strike will be the strike price displayed in TWS divided by the price magnifier. (e.g. displayed in dollars not cents for ZW)In **TWS versions 972 and greater**, the strike prices will be shown in TWS and the API the same way (without a price magnifier applied)For some futures options (e.g GE) it will be necessary to define a trading class, or use the local symbol, or conId.

*   Contract contract = new Contract(); contract.Symbol = "GBL"; contract.SecType = "FOP"; contract.Exchange = "EUREX"; contract.Currency = "EUR"; contract.LastTradeDateOrContractMonth = "20230224"; contract.Strike = 138; contract.Right = "C"; contract.Multiplier = "1000";
    

Bonds
=====

Bonds can be specified by defining the symbol as the CUSIP or ISIN.

*   Contract contract = new Contract(); // enter CUSIP as symbol contract.Symbol = "912828C57"; contract.SecType = "BOND"; contract.Exchange = "SMART"; contract.Currency = "USD";
    

Bonds can also be defined with the conId and exchange as with any security type.

*   Contract contract = new Contract(); contract.ConId = 456467716; contract.Exchange = "SMART";
    

Mutual Funds
============

Order placement for Mutual Funds is currently supported from the API both in paper account and live account. Note: It is recommended to understand mutual fund orders on TWS UI before implementing via API due to restrictions enforced on trading mutual funds. For example to buy ARBIX one requires to use cash quantity i.e. cashQty while selling ARBIX can be implemented using total quantity i.e. totalQuantity.

*   Contract contract = new Contract(); contract.Symbol = "VINIX"; contract.SecType = "FUND"; contract.Exchange = "FUNDSERV"; contract.Currency = "USD";
    

Commodities
===========

*   Contract contract = new Contract(); contract.Symbol = "XAUUSD"; contract.SecType = "CMDTY"; contract.Exchange = "SMART"; contract.Currency = "USD";
    
```json
{"symbol":"XAUUSD","secType":"CMDTY","exchange":"SMART","currency":"USD","durationStr":"1 W","barSizeSetting":"1 day","whatToShow":"MIDPOINT"}
```

Standard Warrants
=================

Warrants, like options, require an **expiration date**, a **right**, a **strike** and a **multiplier**. For some warrants it will be necessary to define a localSymbol or conId to uniquely identify the contract.

*   Contract contract = new Contract(); contract.Symbol = "GOOG"; contract.SecType = "WAR"; contract.Exchange = "FWB"; contract.Currency = "EUR"; contract.LastTradeDateOrContractMonth = "20201117"; contract.Strike = 1500.0; contract.Right = "C"; contract.Multiplier = "0.01";
    

Dutch Warrants and Structured Products
======================================

To unambiguously define a Dutch Warrant or Structured Product (IOPTs) the conId or localSymbol field must be used.

*   It is important to note that if reqContractDetails is used with an incompletely-defined IOPT contract definition, that thousands of results can be returned and the API connection broken.
    
*   IOPT contract definitions will often change and it will be necessary to restart TWS or IB Gateway to download the new contract definition.
    
*   Contract contract = new Contract(); contract.LocalSymbol = "B881G"; contract.SecType = "IOPT"; contract.Exchange = "SBF"; contract.Currency = "EUR";



Build Yield Curve
======================================

To build a yield curve, you'll typically use a combination of instruments to derive yields across maturities: short-term rates from money market instruments (e.g., Treasury Bills for spot yields or SOFR futures for implied forward rates), medium-term from interest rate futures (e.g., Treasury note futures), and longer-term from bonds or derived from futures. Interest rate swaps (IRS) can provide par swap rates for the swap curve, but Interactive Brokers (IB) TWS API does not support direct trading or contract-based requests for IRS like futures; instead, swap rates can be approximated from futures chains or fetched as index data (e.g., Term SOFR rates). Yields are often calculated from prices (e.g., using bond pricing formulas or futures implied rates), as the API provides price data.

You'll need market data subscriptions (e.g., US Bonds, CME Futures) enabled in your IB account. Use `reqContractDetails` to resolve ambiguities or find specific conIds/CUSIPs. Then, request data with `reqMktData` for real-time prices/yields or `reqHistoricalData` for historical (e.g., to bootstrap the curve). For bonds, use `whatToShow='YIELD_BID'`, `'YIELD_ASK'`, `'YIELD_LAST'`, or `'YIELD_MID'` in `reqHistoricalData` to get direct yield bars (OHLC represents yields, not prices). For futures, use `'TRADES'` and calculate implied yields (e.g., 100 - futures price for SOFR/Eurodollar).

Below is a list of key instruments, their typical maturities/contributions to the yield curve, contract parameters, and Python examples using ib_insync (adapt for other languages). Replace expiries with current ones (e.g., via TWS search). Test in a paper account.

### 1. US Treasury Bills (Money Market - Short-Term: 1-12 Months)
   - **Role**: Provides spot yields for the short end. Use T-Bill prices to calculate discount yields or request yield data directly.
   - **Contract Parameters**:
     - `symbol`: CUSIP (e.g., '912797FN0' for a 4-week T-Bill; find current via `reqMatchingSymbolsAsync` with partial contract: secType='US-T', symbol='BILL'). Or, find following https://www.interactivebrokers.com/campus/trading-lessons/enter-us-treasury-orders-in-tws/
     - `secType`: "BOND"
     - `exchange`: "SMART"
     - `currency`: "USD"
   - **How to Request**: Use `reqHistoricalData` with yield-specific `whatToShow` for historical yields, or `reqMktData` with genericTickList="100,101,104" (bid/ask yield, historical vol).
   - **Example (Historical Yields)**:
     ```python
     from ib_insync import *

     ib = IB()
     ib.connect('127.0.0.1', 7497, clientId=1)

     contract = Contract()
     contract.symbol = "912797FN0"  # Replace with current CUSIP
     contract.secType = "BOND"
     contract.exchange = "SMART"
     contract.currency = "USD"

     bars = ib.reqHistoricalData(
         contract=contract,
         endDateTime='',
         durationStr='1 M',  # 1 month
         barSizeSetting='1 day',
         whatToShow='YIELD_MID',  # Or 'YIELD_BID', etc., for yield bars
         useRTH=True,
         formatDate=1
     )

     print(bars)  # OHLC = yields (e.g., close = ending yield)
     ib.disconnect()
     ```

### 2. SOFR Futures (Money Market/Short-Term: 1-3 Months, Implied Forward Rates Up to 5 Years)
   - **Role**: Implied forward rates for short-medium term (post-LIBOR benchmark). Yield = 100 - futures price.
   - **Contract Parameters**:
     - `symbol`: "SR3" (3-month) or "SR1" (1-month)
     - `secType`: "FUT"
     - `exchange`: "CME"
     - `currency`: "USD"
     - `lastTradeDateOrContractMonth`: e.g., "202512" (December 2025; chain for curve)
   - **How to Request**: Use `reqHistoricalData` with `'TRADES'` for prices, then compute yields.
   - **Example (Historical Prices)**:
     ```python
     from ib_insync import *

     ib = IB()
     ib.connect('127.0.0.1', 7497, clientId=1)

     contract = Contract()
     contract.symbol = "SR3"
     contract.secType = "FUT"
     contract.exchange = "CME"
     contract.currency = "USD"
     contract.lastTradeDateOrContractMonth = "202512"

     bars = ib.reqHistoricalData(
         contract=contract,
         endDateTime='',
         durationStr='1 Y',
         barSizeSetting='1 day',
         whatToShow='TRADES',
         useRTH=True,
         formatDate=1
     )

     print(bars)  # Calculate yield: 100 - close price
     ib.disconnect()
     ```

### 3. Federal Funds Futures (Money Market - Short-Term: 1 Month)
   - **Role**: Implied overnight rates for policy expectations (30-day average).
   - **Contract Parameters**:
     - `symbol`: "ZQ"
     - `secType`: "FUT"
     - `exchange`: "CBOT"
     - `currency`: "USD"
     - `lastTradeDateOrContractMonth`: e.g., "202512"
   - **How to Request**: Similar to SOFR futures; compute rate as 100 - price.
   - **Example**: Same as SOFR, but change `symbol="ZQ"`, `exchange="CBOT"`.

### 4. Eurodollar Futures (Short-Medium Term: 3 Months to 10 Years)
   - **Role**: Legacy LIBOR-based implied rates (phasing out, but still available for comparison). Use for forward curve.
   - **Contract Parameters**:
     - `symbol`: "GE"
     - `secType`: "FUT"
     - `exchange`: "GLOBEX"
     - `currency`: "USD"
     - `lastTradeDateOrContractMonth`: e.g., "202512"
   - **How to Request**: Same as SOFR; yield = 100 - price.
   - **Example**: Same as SOFR, but change `symbol="GE"`, `exchange="GLOBEX"`.

### 5. US Treasury Note/Bond Futures (Medium-Long Term: 2-30 Years)
   - **Role**: Cheapest-to-deliver (CTD) bond implies yields for benchmark maturities. Use chains for the curve.
   - **Contract Parameters** (examples for different maturities):
     - 2-Year (ZT): `symbol="ZT"`
     - 5-Year (ZF): `symbol="ZF"`
     - 10-Year (ZN): `symbol="ZN"`
     - 30-Year (ZB): `symbol="ZB"`
     - `secType`: "FUT"
     - `exchange`: "CBOT"
     - `currency`: "USD"
     - `lastTradeDateOrContractMonth`: e.g., "202512"
   - **How to Request**: Use `'TRADES'`; calculate yield from price using CTD bond details (fetch via `reqContractDetails`).
   - **Example (10-Year)**:
     ```python
     from ib_insync import *

     ib = IB()
     ib.connect('127.0.0.1', 7497, clientId=1)

     contract = Contract()
     contract.symbol = "ZN"
     contract.secType = "FUT"
     contract.exchange = "CBOT"
     contract.currency = "USD"
     contract.lastTradeDateOrContractMonth = "202512"

     bars = ib.reqHistoricalData(
         contract=contract,
         endDateTime='',
         durationStr='1 Y',
         barSizeSetting='1 day',
         whatToShow='TRADES',
         useRTH=True,
         formatDate=1
     )

     print(bars)  # Use price to derive yield via CTD
     ib.disconnect()
     ```

### 6. US Treasury Notes/Bonds (Medium-Long Term: 2-30 Years)
   - **Role**: Direct spot yields for government curve (alternative to futures for precision).
   - **Contract Parameters**:
     - `symbol`: CUSIP (e.g., '91282CJV2' for a 10-Year Note; find via `reqContractDetails`)
     - `secType`: "BOND"
     - `exchange`: "SMART"
     - `currency`: "USD"
   - **How to Request**: Use yield-specific `whatToShow` for direct yields.
   - **Example**: Same as T-Bills, but with Note/Bond CUSIP and longer duration (e.g., '5 Y').

### 7. Interest Rate Swaps (Medium-Long Term: 1-30 Years)
   - **Role**: Par swap rates for the risk-free or swap curve (e.g., SOFR-based).
   - **Contract Parameters**: No direct IRS secType; approximate with Term SOFR indices for forward rates.
     - `symbol`: "SOFR" (or "SOFR1M", "SOFR3M" for term rates)
     - `secType`: "IND"
     - `exchange`: "CME"
     - `currency`: "USD"
   - **How to Request**: Use `reqMktData` for real-time rate (as index value); historical via `'TRADES'`.
   - **Example (Real-Time Term SOFR)**:
     ```python
     from ib_insync import *

     ib = IB()
     ib.connect('127.0.0.1', 7497, clientId=1)

     contract = Contract()
     contract.symbol = "SOFR"
     contract.secType = "IND"
     contract.exchange = "CME"
     contract.currency = "USD"

     ticker = ib.reqMktData(contract=contract, genericTickList="", snapshot=False)

     # Handle in callback (e.g., tickPrice for last rate)
     def onTickPrice(ticker, field, price, attribs):
         if field == 4:  # Last price = rate
             print(f"SOFR Rate: {price}%")

     ib.tickPriceEvent += onTickPrice
     ib.sleep(30)  # Wait for data
     ib.disconnect()
     ```
   - **Note**: For full IRS curves, derive from SOFR futures strips or use external libraries (e.g., QuantLib) with API data. IB doesn't provide direct swap contract trading via API.

To bootstrap the curve, fetch data for a chain of maturities, adjust for convexity/basis, and interpolate (e.g., using cubic splines in code). Consult IB's API docs for limits (e.g., pacing) and formulas for yield calculations.