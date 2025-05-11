# 目次

1. [ProjectX Gateway API | ProjectX API Documentation](#projectx-gateway-api-projectx-api-documentation)
2. [ProjectX Gateway API | ProjectX API Documentation](#projectx-gateway-api-projectx-api-documentation)
3. [Search for Account | ProjectX API Documentation](#search-for-account-projectx-api-documentation)
4. [Retrieve Bars | ProjectX API Documentation](#retrieve-bars-projectx-api-documentation)
5. [Search for Contracts | ProjectX API Documentation](#search-for-contracts-projectx-api-documentation)
6. [Search for Contract by Id | ProjectX API Documentation](#search-for-contract-by-id-projectx-api-documentation)
7. [Cancel an Order | ProjectX API Documentation](#cancel-an-order-projectx-api-documentation)
8. [Modify an Order | ProjectX API Documentation](#modify-an-order-projectx-api-documentation)
9. [Place an Order | ProjectX API Documentation](#place-an-order-projectx-api-documentation)
10. [Search for Orders | ProjectX API Documentation](#search-for-orders-projectx-api-documentation)
11. [Search for Open Orders | ProjectX API Documentation](#search-for-open-orders-projectx-api-documentation)
12. [Close Positions | ProjectX API Documentation](#close-positions-projectx-api-documentation)
13. [Partially Close Positions | ProjectX API Documentation](#partially-close-positions-projectx-api-documentation)
14. [Search for Positions | ProjectX API Documentation](#search-for-positions-projectx-api-documentation)
15. [Search for Trades | ProjectX API Documentation](#search-for-trades-projectx-api-documentation)
16. [Account | ProjectX API Documentation](#account-projectx-api-documentation)
17. [API Reference | ProjectX API Documentation](#api-reference-projectx-api-documentation)
18. [Authenticate | ProjectX API Documentation](#authenticate-projectx-api-documentation)
19. [Getting Started | ProjectX API Documentation](#getting-started-projectx-api-documentation)
20. [Market Data | ProjectX API Documentation](#market-data-projectx-api-documentation)
21. [Orders | ProjectX API Documentation](#orders-projectx-api-documentation)
22. [Positions | ProjectX API Documentation](#positions-projectx-api-documentation)
23. [Realtime Updates | ProjectX API Documentation](#realtime-updates-projectx-api-documentation)
24. [Trades | ProjectX API Documentation](#trades-projectx-api-documentation)
25. [Authenticate (with API key) | ProjectX API Documentation](#authenticate-with-api-key-projectx-api-documentation)
26. [Authenticate (for authorized applications) | ProjectX API Documentation](#authenticate-for-authorized-applications-projectx-api-documentation)
27. [Connection URLs | ProjectX API Documentation](#connection-urls-projectx-api-documentation)
28. [Placing Your First Order | ProjectX API Documentation](#placing-your-first-order-projectx-api-documentation)
29. [ProjectX Gateway API | ProjectX API Documentation](#projectx-gateway-api-projectx-api-documentation)
30. [Real Time Data Overview | ProjectX API Documentation](#real-time-data-overview-projectx-api-documentation)

---



---

# ProjectX Gateway API | ProjectX API Documentation

*Documentation for the ProjectX Gateway API*

*出典: https://gateway.docs.projectx.com*

[Skip to main content](https://gateway.docs.projectx.com#__docusaurus_skipToContent_fallback)


---

# ProjectX Gateway API | ProjectX API Documentation

*Documentation for the ProjectX Gateway API*

*出典: https://gateway.docs.projectx.com/*

[Skip to main content](https://gateway.docs.projectx.com/#__docusaurus_skipToContent_fallback)


---

# Search for Account | ProjectX API Documentation

*API URL:  /api/Account/search*

*出典: https://gateway.docs.projectx.com/docs/api-reference/account/search-accounts*

On this page
# Search for Account

**API URL** : POST https://gateway-api-demo.s2f.projectx.com/api/Account/search
**API Reference** : **[/api/account/search](https://gateway-api-demo.s2f.projectx.com/swagger/index.html#/Account/Account_SearchAccounts)**

## Description

* * *
Search for accounts.
## Parameters

* * *
Name| Type| Description| Required| Nullable 
---|---|---|---|--- 
onlyActiveAccounts| boolean| Whether to filter only active accounts.| Required| false 
## Example Usage

* * *
### Example Request

 * cURL Request

 
 curl -X 'POST' \ 
 'https://gateway-api-demo.s2f.projectx.com/api/Account/search' \ 
 -H 'accept: text/plain' \ 
 -H 'Content-Type: application/json' \ 
```json
 -d '{ 
 "onlyActiveAccounts": true 
 }' 
```
 
### Example Response

 * Success
 * Error

 
```json
 { 
 "accounts": [ { "id": 1, "name": "TEST_ACCOUNT_1", "balance": 50000, 
 "canTrade": true, 
 "isVisible": true 
 } 
```
 ], 
 "success": true, 
 "errorCode": 0, 
 "errorMessage": null 
 } 
 
 
 Error: response status is 401 
 
 * [Description](https://gateway.docs.projectx.com/docs/api-reference/account/search-accounts#description)
 * [Parameters](https://gateway.docs.projectx.com/docs/api-reference/account/search-accounts#parameters)
 * [Example Usage](https://gateway.docs.projectx.com/docs/api-reference/account/search-accounts#example-usage)
 * [Example Request](https://gateway.docs.projectx.com/docs/api-reference/account/search-accounts#example-request)
 * [Example Response](https://gateway.docs.projectx.com/docs/api-reference/account/search-accounts#example-response)


---

# Retrieve Bars | ProjectX API Documentation

*API URL:  /api/History/retrieveBars*

*出典: https://gateway.docs.projectx.com/docs/api-reference/market-data/retrieve-bars*

On this page
# Retrieve Bars

**API URL** : POST https://gateway-api-demo.s2f.projectx.com/api/History/retrieveBars
**API Reference** : **[/api/history/retrieveBars](https://gateway-api-demo.s2f.projectx.com/swagger/index.html#/History/History_GetBars)**

## Description

* * *
Retrieve bars.
## Parameters

* * *
Name| Type| Description| Required| Nullable 
---|---|---|---|--- 
contractId| integer| The contract ID.| Required| false 
live| boolean| Whether to retrieve bars using the sim or live data subscription.| Required| false 
startTime| datetime| The start time of the historical data.| Required| false 
endTime| datetime| The end time of the historical data.| Required| false 
unit| integer| The unit of aggregation for the historical data: 
`1` = Second 
`2` = Minute 
`3` = Hour 
`4` = Day 
`5` = Week 
`6` = Month| Required| false 
unitNumber| integer| The number of units to aggregate.| Required| false 
limit| integer| The maximum number of bars to retrieve.| Required| false 
includePartialBar| boolean| Whether to include a partial bar representing the current time unit.| Required| false 
## Example Usage

* * *
### Example Request

 * cURL Request

 
 curl -X 'POST' \ 
 'https://gateway-api-demo.s2f.projectx.com/api/History/retrieveBars' \ 
 -H 'accept: text/plain' \ 
 -H 'Content-Type: application/json' \ 
```json
 -d '{ 
 "contractId": "CON.F.US.RTY.Z24", 
 "live": false, 
 "startTime": "2024-12-01T00:00:00Z", 
 "endTime": "2024-12-31T21:00:00Z", 
 "unit": 3, 
 "unitNumber": 1, 
 "limit": 7, 
 "includePartialBar": false 
 }' 
```
 
### Example Response

 * Success
 * Error

 
```json
 { 
 "bars": [ { "t": "2024-12-20T14:00:00+00:00", "o": 2208.100000000, "h": 2217.000000000, 
 "l": 2206.700000000, 
 "c": 2210.100000000, 
 "v": 87 
 }, 
```
```json
 { 
 "t": "2024-12-20T13:00:00+00:00", 
 "o": 2195.800000000, 
 "h": 2215.000000000, 
 "l": 2192.900000000, 
 "c": 2209.800000000, 
 "v": 536 
 }, 
```
```json
 { 
 "t": "2024-12-20T12:00:00+00:00", 
 "o": 2193.600000000, 
 "h": 2200.300000000, 
 "l": 2192.000000000, 
 "c": 2198.000000000, 
 "v": 180 
 }, 
```
```json
 { 
 "t": "2024-12-20T11:00:00+00:00", 
 "o": 2192.200000000, 
 "h": 2194.800000000, 
 "l": 2189.900000000, 
 "c": 2194.800000000, 
 "v": 174 
 }, 
```
```json
 { 
 "t": "2024-12-20T10:00:00+00:00", 
 "o": 2200.400000000, 
 "h": 2200.400000000, 
 "l": 2191.000000000, 
 "c": 2193.100000000, 
 "v": 150 
 }, 
```
```json
 { 
 "t": "2024-12-20T09:00:00+00:00", 
 "o": 2205.000000000, 
 "h": 2205.800000000, 
 "l": 2198.900000000, 
 "c": 2200.500000000, 
 "v": 56 
 }, 
```
```json
{
  "t": "2024-12-20T08:00:00+00:00",
  "o": 2207.7,
  "h": 2210.1,
  "l": 2198.1,
  "c": 2204.9,
  "v": 144
}
```
 ], 
 "success": true, 
 "errorCode": 0, 
 "errorMessage": null 
 } 
 
 
 Error: response status is 401 
 
 * [Description](https://gateway.docs.projectx.com/docs/api-reference/market-data/retrieve-bars#description)
 * [Parameters](https://gateway.docs.projectx.com/docs/api-reference/market-data/retrieve-bars#parameters)
 * [Example Usage](https://gateway.docs.projectx.com/docs/api-reference/market-data/retrieve-bars#example-usage)
 * [Example Request](https://gateway.docs.projectx.com/docs/api-reference/market-data/retrieve-bars#example-request)
 * [Example Response](https://gateway.docs.projectx.com/docs/api-reference/market-data/retrieve-bars#example-response)


---

# Search for Contracts | ProjectX API Documentation

*API URL:  /api/Contract/search*

*出典: https://gateway.docs.projectx.com/docs/api-reference/market-data/search-contracts*

On this page
# Search for Contracts

**API URL** : POST https://gateway-api-demo.s2f.projectx.com/api/Contract/search
**API Reference** : **[/api/contract/search](https://gateway-api-demo.s2f.projectx.com/swagger/index.html#/Contract/Contract_SearchContracts)**

## Description

* * *
Search for contracts.
## Parameters

* * *
Name| Type| Description| Required| Nullable 
---|---|---|---|--- 
searchText| string| The name of the contract to search for.| Required| false 
live| boolean| Whether to search for contracts using the sim/live data subscription.| Required| false 
## Example Usage

* * *
### Example Request

 * cURL Request

 
 curl -X 'POST' \ 
 'https://gateway-api-demo.s2f.projectx.com/api/Contract/search' \ 
 -H 'accept: text/plain' \ 
 -H 'Content-Type: application/json' \ 
```json
 -d '{ 
 "live": false, 
 "searchText": "NQ" 
 }' 
```
 
### Example Response

 * Success
 * Error

 
```json
 { 
 "contracts": [ { "id": "CON.F.US.ENQ.H25", "name": "ENQH25", "description": "E-mini NASDAQ-100: March 2025", 
 "tickSize": 0.25, 
 "tickValue": 5, 
 "activeContract": true 
 }, 
```
```json
 { 
 "id": "CON.F.US.MNQ.H25", 
 "name": "MNQH25", 
 "description": "Micro E-mini Nasdaq-100: March 2025", 
 "tickSize": 0.25, 
 "tickValue": 0.5, 
 "activeContract": true 
 }, 
```
```json
 { 
 "id": "CON.F.US.NQG.G25", 
 "name": "NQGG25", 
 "description": "E-Mini Natural Gas: February 2025", 
 "tickSize": 0.005, 
 "tickValue": 12.5, 
 "activeContract": true 
 }, 
```
```json
{
  "id": "CON.F.US.NQM.G25",
  "name": "NQMG25",
  "description": "E-Mini Crude Oil: February 2025",
  "tickSize": 0.025,
  "tickValue": 12.5,
  "activeContract": true
}
```
 ], 
 "success": true, 
 "errorCode": 0, 
 "errorMessage": null 
 } 
 
 
 Error: response status is 401 
 
 * [Description](https://gateway.docs.projectx.com/docs/api-reference/market-data/search-contracts#description)
 * [Parameters](https://gateway.docs.projectx.com/docs/api-reference/market-data/search-contracts#parameters)
 * [Example Usage](https://gateway.docs.projectx.com/docs/api-reference/market-data/search-contracts#example-usage)
 * [Example Request](https://gateway.docs.projectx.com/docs/api-reference/market-data/search-contracts#example-request)
 * [Example Response](https://gateway.docs.projectx.com/docs/api-reference/market-data/search-contracts#example-response)


---

# Search for Contract by Id | ProjectX API Documentation

*API URL:  /api/Contract/searchById*

*出典: https://gateway.docs.projectx.com/docs/api-reference/market-data/search-contracts-by-id*

On this page
# Search for Contract by Id

**API URL** : POST https://gateway-api-demo.s2f.projectx.com/api/Contract/searchById
**API Reference** : **[/api/contract/searchbyid](https://gateway-api-demo.s2f.projectx.com/swagger/index.html#/Contract/Contract_SearchContractById)**

## Description

* * *
Search for contracts.
## Parameters

* * *
Name| Type| Description| Required| Nullable 
---|---|---|---|--- 
contractId| string| The id of the contract to search for.| Required| false 
## Example Usage

* * *
### Example Request

 * cURL Request

 
 curl -X 'POST' \ 
 'https://gateway-api-demo.s2f.projectx.com/api/Contract/searchById' \ 
 -H 'accept: text/plain' \ 
 -H 'Content-Type: application/json' \ 
```json
 -d '{ 
 "contractId": "CON.F.US.ENQ.H25" 
 }' 
```
 
### Example Response

 * Success
 * Error

 
```json
 { 
 "contracts": [ { "id": "CON.F.US.ENQ.H25", "name": "ENQH25", "description": "E-mini NASDAQ-100: March 2025", 
 "tickSize": 0.25, 
 "tickValue": 5, 
 "activeContract": true 
 } 
```
 ], 
 "success": true, 
 "errorCode": 0, 
 "errorMessage": null 
 } 
 
 
 Error: response status is 401 
 
 * [Description](https://gateway.docs.projectx.com/docs/api-reference/market-data/search-contracts-by-id#description)
 * [Parameters](https://gateway.docs.projectx.com/docs/api-reference/market-data/search-contracts-by-id#parameters)
 * [Example Usage](https://gateway.docs.projectx.com/docs/api-reference/market-data/search-contracts-by-id#example-usage)
 * [Example Request](https://gateway.docs.projectx.com/docs/api-reference/market-data/search-contracts-by-id#example-request)
 * [Example Response](https://gateway.docs.projectx.com/docs/api-reference/market-data/search-contracts-by-id#example-response)


---

# Cancel an Order | ProjectX API Documentation

*API URL:  /api/Order/cancel*

*出典: https://gateway.docs.projectx.com/docs/api-reference/order/order-cancel*

On this page
# Cancel an Order

**API URL** : POST https://gateway-api-demo.s2f.projectx.com/api/Order/cancel
**API Reference** : **[/api/order/cancel](https://gateway-api-demo.s2f.projectx.com/swagger/index.html#/Order/Order_CancelOrder)**

## Description

* * *
Cancel an order.
## Parameters

* * *
Name| Type| Description| Required| Nullable 
---|---|---|---|--- 
accountId| integer| The account ID.| Required| false 
orderId| integer| The order id.| Required| false 
## Example Usage

* * *
### Example Request

 * cURL Request

 
 curl -X 'POST' \ 
 'https://gateway-api-demo.s2f.projectx.com/api/Order/cancel' \ 
 -H 'accept: text/plain' \ 
 -H 'Content-Type: application/json' \ 
```json
 -d '{ 
 "accountId": 465, 
 "orderId": 26974 
 }' 
```
 
### Example Response

 * Success
 * Error

 
```json
{
  "success": true,
  "errorCode": 0,
  "errorMessage": null
}
```
 
 
 Error: response status is 401 
 
 * [Description](https://gateway.docs.projectx.com/docs/api-reference/order/order-cancel#description)
 * [Parameters](https://gateway.docs.projectx.com/docs/api-reference/order/order-cancel#parameters)
 * [Example Usage](https://gateway.docs.projectx.com/docs/api-reference/order/order-cancel#example-usage)
 * [Example Request](https://gateway.docs.projectx.com/docs/api-reference/order/order-cancel#example-request)
 * [Example Response](https://gateway.docs.projectx.com/docs/api-reference/order/order-cancel#example-response)


---

# Modify an Order | ProjectX API Documentation

*API URL:  /api/Order/modify*

*出典: https://gateway.docs.projectx.com/docs/api-reference/order/order-modify*

On this page
# Modify an Order

**API URL** : POST https://gateway-api-demo.s2f.projectx.com/api/Order/modify
**API Reference** : **[/api/order/modify](https://gateway-api-demo.s2f.projectx.com/swagger/index.html#/Order/Order_ModifyOrder)**

## Description

* * *
Modify an open order.
## Parameters

* * *
Name| Type| Description| Required| Nullable 
---|---|---|---|--- 
accountId| integer| The account ID.| Required| false 
orderId| integer| The order id.| Required| false 
size| integer| The size of the order.| Optional| true 
limitPrice| decimal| The limit price for the order, if applicable.| Optional| true 
stopPrice| decimal| The stop price for the order, if applicable.| Optional| true 
trailPrice| decimal| The trail price for the order, if applicable.| Optional| true 
## Example Usage

* * *
### Example Request

 * cURL Request

 
 curl -X 'POST' \ 
 'https://gateway-api-demo.s2f.projectx.com/api/Order/modify' \ 
 -H 'accept: text/plain' \ 
 -H 'Content-Type: application/json' \ 
```json
 -d '{ 
 "accountId": 465, 
 "orderId": 26974, 
 "size": 1, 
 "limitPrice": null, 
 "stopPrice": 1604, 
 "trailPrice": null 
 } 
```
 ' 
 
### Example Response

 * Success
 * Error

 
```json
{
  "success": true,
  "errorCode": 0,
  "errorMessage": null
}
```
 
 
 Error: response status is 401 
 
 * [Description](https://gateway.docs.projectx.com/docs/api-reference/order/order-modify#description)
 * [Parameters](https://gateway.docs.projectx.com/docs/api-reference/order/order-modify#parameters)
 * [Example Usage](https://gateway.docs.projectx.com/docs/api-reference/order/order-modify#example-usage)
 * [Example Request](https://gateway.docs.projectx.com/docs/api-reference/order/order-modify#example-request)
 * [Example Response](https://gateway.docs.projectx.com/docs/api-reference/order/order-modify#example-response)


---

# Place an Order | ProjectX API Documentation

*API URL:  /api/Order/place*

*出典: https://gateway.docs.projectx.com/docs/api-reference/order/order-place*

On this page
# Place an Order

**API URL** : POST https://gateway-api-demo.s2f.projectx.com/api/Order/place
**API Reference** : **[/api/order/place](https://gateway-api-demo.s2f.projectx.com/swagger/index.html#/Order/Order_PlaceOrder)**

## Description

* * *
Place an order.
## Parameters

* * *
Name| Type| Description| Required| Nullable 
---|---|---|---|--- 
accountId| integer| The account ID.| Required| false 
contractId| string| The contract ID.| Required| false 
type| integer| The order type: 
`1` = Limit 
`2` = Market 
`4` = Stop 
`5` = TrailingStop 
`6` = JoinBid 
`7` = JoinAsk| Required| false 
side| integer| The side of the order: 
`0` = Bid (buy) 
`1` = Ask (sell)| Required| false 
size| integer| The size of the order.| Required| false 
limitPrice| decimal| The limit price for the order, if applicable.| Optional| true 
stopPrice| decimal| The stop price for the order, if applicable.| Optional| true 
trailPrice| decimal| The trail price for the order, if applicable.| Optional| true 
customTag| string| An optional custom tag for the order.| Optional| true 
linkedOrderId| integer| The linked order id.| Optional| true 
## Example Usage

* * *
### Example Request

 * cURL Request

 
 curl -X 'POST' \ 
 'https://gateway-api-demo.s2f.projectx.com/api/Order/place' \ 
 -H 'accept: text/plain' \ 
 -H 'Content-Type: application/json' \ 
```json
 -d '{ 
 "accountId": 465, 
 "contractId": "CON.F.US.DA6.M25", 
 "type": 2, 
 "side": 1, 
 "size": 1, 
 "limitPrice": null, 
 "stopPrice": null, 
 "trailPrice": null, 
 "customTag": null, 
 "linkedOrderId": null 
 }' 
```
 
### Example Response

 * Success
 * Error

 
```json
{
  "orderId": 9056,
  "success": true,
  "errorCode": 0,
  "errorMessage": null
}
```
 
 
 Error: response status is 401 
 
 * [Description](https://gateway.docs.projectx.com/docs/api-reference/order/order-place#description)
 * [Parameters](https://gateway.docs.projectx.com/docs/api-reference/order/order-place#parameters)
 * [Example Usage](https://gateway.docs.projectx.com/docs/api-reference/order/order-place#example-usage)
 * [Example Request](https://gateway.docs.projectx.com/docs/api-reference/order/order-place#example-request)
 * [Example Response](https://gateway.docs.projectx.com/docs/api-reference/order/order-place#example-response)


---

# Search for Orders | ProjectX API Documentation

*API URL:  /api/Order/search*

*出典: https://gateway.docs.projectx.com/docs/api-reference/order/order-search*

On this page
# Search for Orders

**API URL** : POST https://gateway-api-demo.s2f.projectx.com/api/Order/search
**API Reference** : **[/api/order/search](https://gateway-api-demo.s2f.projectx.com/swagger/index.html#/Order/Order_SearchOrders)**

## Description

* * *
Search for orders.
## Parameters

* * *
Name| Type| Description| Required| Nullable 
---|---|---|---|--- 
accountId| integer| The account ID.| Required| false 
startTimestamp| datetime| The start of the timestamp filter.| Required| false 
endTimestamp| datetime| The end of the timestamp filter.| Optional| true 
## Example Usage

* * *
### Example Request

 * cURL Request

 
 curl -X 'POST' \ 
 'https://gateway-api-demo.s2f.projectx.com/api/Order/search' \ 
 -H 'accept: text/plain' \ 
 -H 'Content-Type: application/json' \ 
```json
 -d '{ 
 "accountId": 202, 
 "startTimestamp": "2024-12-30T16:48:16.003Z", 
 "endTimestamp": "2025-12-30T16:48:16.003Z" 
 }' 
```
 
### Example Response

 * Success
 * Error

 
```json
 { 
 "orders": [ { "id": 26060, "accountId": 545, "contractId": "CON.F.US.EP.M25", 
 "creationTimestamp": "2025-04-14T17:49:10.142532+00:00", 
 "updateTimestamp": null, 
 "status": 2, 
 "type": 2, 
 "side": 0, 
 "size": 1, 
 "limitPrice": null, 
 "stopPrice": null 
 }, 
```
```json
{
  "id": 26062,
  "accountId": 545,
  "contractId": "CON.F.US.EP.M25",
  "creationTimestamp": "2025-04-14T17:49:53.043234+00:00",
  "updateTimestamp": null,
  "status": 2,
  "type": 2,
  "side": 1,
  "size": 1,
  "limitPrice": null,
  "stopPrice": null
}
```
 ], 
 "success": true, 
 "errorCode": 0, 
 "errorMessage": null 
 } 
 
 
 Error: response status is 401 
 
 * [Description](https://gateway.docs.projectx.com/docs/api-reference/order/order-search#description)
 * [Parameters](https://gateway.docs.projectx.com/docs/api-reference/order/order-search#parameters)
 * [Example Usage](https://gateway.docs.projectx.com/docs/api-reference/order/order-search#example-usage)
 * [Example Request](https://gateway.docs.projectx.com/docs/api-reference/order/order-search#example-request)
 * [Example Response](https://gateway.docs.projectx.com/docs/api-reference/order/order-search#example-response)


---

# Search for Open Orders | ProjectX API Documentation

*API URL:  /api/Order/searchOpen*

*出典: https://gateway.docs.projectx.com/docs/api-reference/order/order-search-open*

On this page
# Search for Open Orders

**API URL** : POST https://gateway-api-demo.s2f.projectx.com/api/Order/searchOpen
**API Reference** : **[/api/order/searchopen](https://gateway-api-demo.s2f.projectx.com/swagger/index.html#/Order/Order_SearchOpenOrders)**

## Description

* * *
Search for open orders.
## Parameters

* * *
Name| Type| Description| Required| Nullable 
---|---|---|---|--- 
accountId| integer| The account ID.| Required| false 
## Example Usage

* * *
### Example Request

 * cURL Request

 
 curl -X 'POST' \ 
 'https://gateway-api-demo.s2f.projectx.com/api/Order/search' \ 
 -H 'accept: text/plain' \ 
 -H 'Content-Type: application/json' \ 
```json
 -d '{ 
 "accountId": 212 
 }' 
```
 
### Example Response

 * Success
 * Error

 
```json
 { 
 "orders": [ { "id": 26970, "accountId": 212, "contractId": "CON.F.US.EP.M25", 
 "creationTimestamp": "2025-04-21T19:45:52.105808+00:00", 
 "updateTimestamp": "2025-04-21T19:45:52.105808+00:00", 
 "status": 1, 
 "type": 4, 
 "side": 1, 
 "size": 1, 
 "limitPrice": null, 
 "stopPrice": 5138.000000000 
 } 
```
 ], 
 "success": true, 
 "errorCode": 0, 
 "errorMessage": null 
 } 
 
 
 Error: response status is 401 
 
 * [Description](https://gateway.docs.projectx.com/docs/api-reference/order/order-search-open#description)
 * [Parameters](https://gateway.docs.projectx.com/docs/api-reference/order/order-search-open#parameters)
 * [Example Usage](https://gateway.docs.projectx.com/docs/api-reference/order/order-search-open#example-usage)
 * [Example Request](https://gateway.docs.projectx.com/docs/api-reference/order/order-search-open#example-request)
 * [Example Response](https://gateway.docs.projectx.com/docs/api-reference/order/order-search-open#example-response)


---

# Close Positions | ProjectX API Documentation

*API URL:  /api/Position/closeContract*

*出典: https://gateway.docs.projectx.com/docs/api-reference/positions/close-positions*

On this page
# Close Positions

**API URL** : POST https://gateway-api-demo.s2f.projectx.com/api/Position/closeContract
**API Reference** : **[/api/position/closeContract](https://gateway-api-demo.s2f.projectx.com/swagger/index.html#/Position/Position_CloseContractPosition)**

## Description

* * *
Close a position.
## Parameters

* * *
Name| Type| Description| Required| Nullable 
---|---|---|---|--- 
accountId| integer| The account ID.| Required| false 
contractId| string| The contract ID.| Required| false 
## Example Usage

* * *
### Example Request

 * cURL Request

 
 curl -X 'POST' \ 
 'https://gateway-api-demo.s2f.projectx.com/api/Position/partialCloseContract' \ 
 -H 'accept: text/plain' \ 
 -H 'Content-Type: application/json' \ 
```json
 -d '{ 
 "accountId": 536, 
 "contractId": "CON.F.US.GMET.J25", 
 "size": 1 
 }' 
```
 
### Example Response

 * Success
 * Error

 
```json
{
  "success": true,
  "errorCode": 0,
  "errorMessage": null
}
```
 
 
 Error: response status is 401 
 
 * [Description](https://gateway.docs.projectx.com/docs/api-reference/positions/close-positions#description)
 * [Parameters](https://gateway.docs.projectx.com/docs/api-reference/positions/close-positions#parameters)
 * [Example Usage](https://gateway.docs.projectx.com/docs/api-reference/positions/close-positions#example-usage)
 * [Example Request](https://gateway.docs.projectx.com/docs/api-reference/positions/close-positions#example-request)
 * [Example Response](https://gateway.docs.projectx.com/docs/api-reference/positions/close-positions#example-response)


---

# Partially Close Positions | ProjectX API Documentation

*API URL:  /api/Position/partialCloseContract*

*出典: https://gateway.docs.projectx.com/docs/api-reference/positions/close-positions-partial*

On this page
# Partially Close Positions

**API URL** : POST https://gateway-api-demo.s2f.projectx.com/api/Position/partialCloseContract
**API Reference** : **[/api/position/partialclosecontract](https://gateway-api-demo.s2f.projectx.com/swagger/index.html#/Position/Position_PartialCloseContractPosition)**

## Description

* * *
Partially close a position.
## Parameters

* * *
Name| Type| Description| Required| Nullable 
---|---|---|---|--- 
accountId| integer| The account ID.| Required| false 
contractId| string| The contract ID.| Required| false 
size| integer| The size to close.| Required| false 
## Example Usage

* * *
### Example Request

 * cURL Request

 
 curl -X 'POST' \ 
 'https://gateway-api-demo.s2f.projectx.com/api/Position/closeContract' \ 
 -H 'accept: text/plain' \ 
 -H 'Content-Type: application/json' \ 
```json
 -d '{ 
 "accountId": 536, 
 "contractId": "CON.F.US.GMET.J25" 
 }' 
```
 
### Example Response

 * Success
 * Error

 
```json
{
  "success": true,
  "errorCode": 0,
  "errorMessage": null
}
```
 
 
 Error: response status is 401 
 
 * [Description](https://gateway.docs.projectx.com/docs/api-reference/positions/close-positions-partial#description)
 * [Parameters](https://gateway.docs.projectx.com/docs/api-reference/positions/close-positions-partial#parameters)
 * [Example Usage](https://gateway.docs.projectx.com/docs/api-reference/positions/close-positions-partial#example-usage)
 * [Example Request](https://gateway.docs.projectx.com/docs/api-reference/positions/close-positions-partial#example-request)
 * [Example Response](https://gateway.docs.projectx.com/docs/api-reference/positions/close-positions-partial#example-response)


---

# Search for Positions | ProjectX API Documentation

*API URL:  /api/Position/searchOpen*

*出典: https://gateway.docs.projectx.com/docs/api-reference/positions/search-open-positions*

On this page
# Search for Positions

**API URL** : POST https://gateway-api-demo.s2f.projectx.com/api/Position/searchOpen
**API Reference** : **[/api/position/searchOpen](https://gateway-api-demo.s2f.projectx.com/swagger/index.html#/Position/Position_SearchOpenPositions)**

## Description

* * *
Search for open positions.
## Parameters

* * *
Name| Type| Description| Required| Nullable 
---|---|---|---|--- 
accountId| integer| The account ID.| Required| false 
## Example Usage

* * *
### Example Request

 * cURL Request

 
 curl -X 'POST' \ 
 'https://gateway-api-demo.s2f.projectx.com/api/Position/searchOpen' \ 
 -H 'accept: text/plain' \ 
 -H 'Content-Type: application/json' \ 
```json
 -d '{ 
 "accountId": 536 
 }' 
```
 
### Example Response

 * Success
 * Error

 
```json
 { 
 "positions": [ { "id": 6124, "accountId": 536, "contractId": "CON.F.US.GMET.J25", 
 "creationTimestamp": "2025-04-21T19:52:32.175721+00:00", 
 "type": 1, 
 "size": 2, 
 "averagePrice": 1575.750000000 
 } 
```
 ], 
 "success": true, 
 "errorCode": 0, 
 "errorMessage": null 
 } 
 
 
 Error: response status is 401 
 
 * [Description](https://gateway.docs.projectx.com/docs/api-reference/positions/search-open-positions#description)
 * [Parameters](https://gateway.docs.projectx.com/docs/api-reference/positions/search-open-positions#parameters)
 * [Example Usage](https://gateway.docs.projectx.com/docs/api-reference/positions/search-open-positions#example-usage)
 * [Example Request](https://gateway.docs.projectx.com/docs/api-reference/positions/search-open-positions#example-request)
 * [Example Response](https://gateway.docs.projectx.com/docs/api-reference/positions/search-open-positions#example-response)


---

# Search for Trades | ProjectX API Documentation

*API URL:  /api/Trade/search*

*出典: https://gateway.docs.projectx.com/docs/api-reference/trade/trade-search*

On this page
# Search for Trades

**API URL** : POST https://gateway-api-demo.s2f.projectx.com/api/Trade/search
**API Reference** : **[/api/Trade/search](https://gateway-api-demo.s2f.projectx.com/swagger/index.html#/Trade/Trade_SearchFilledTrades)**

## Description

* * *
Search for trades from the request parameters.
## Parameters

* * *
Name| Type| Description| Required| Nullable 
---|---|---|---|--- 
accountId| integer| The account ID.| Required| false 
startTimestamp| datetime| The start of the timestamp filter.| Required| false 
endTimestamp| datetime| The end of the timestamp filter.| Optional| true 
## Example Usage

* * *
### Example Request

 * cURL Request

 
 curl -X 'POST' \ 
 'https://gateway-api-demo.s2f.projectx.com/api/Trade/search' \ 
 -H 'accept: text/plain' \ 
 -H 'Content-Type: application/json' \ 
```json
 -d '{ 
 "accountId": 203, 
 "startTimestamp": "2025-01-20T15:47:39.882Z", 
 "endTimestamp": "2025-01-30T15:47:39.882Z" 
 }' 
```
 
### Example Response

 * Success
 * Error

 
```json
 { 
 "trades": [ { "id": 8604, "accountId": 203, "contractId": "CON.F.US.EP.H25", 
 "creationTimestamp": "2025-01-21T16:13:52.523293+00:00", 
 "price": 6065.250000000, 
 "profitAndLoss": 50.000000000, 
 "fees": 1.4000, 
 "side": 1, 
 "size": 1, 
 "voided": false, 
 "orderId": 14328 
 }, 
```
```json
 { 
 "id": 8603, 
 "accountId": 203, 
 "contractId": "CON.F.US.EP.H25", 
 "creationTimestamp": "2025-01-21T16:13:04.142302+00:00", 
 "price": 6064.250000000, 
 "profitAndLoss": null, //a null value indicates a half-turn trade 
 "fees": 1.4000, 
 "side": 0, 
 "size": 1, 
 "voided": false, 
 "orderId": 14326 
 } 
```
 ], 
 "success": true, 
 "errorCode": 0, 
 "errorMessage": null 
 } 
 
 
 Error: response status is 401 
 
 * [Description](https://gateway.docs.projectx.com/docs/api-reference/trade/trade-search#description)
 * [Parameters](https://gateway.docs.projectx.com/docs/api-reference/trade/trade-search#parameters)
 * [Example Usage](https://gateway.docs.projectx.com/docs/api-reference/trade/trade-search#example-usage)
 * [Example Request](https://gateway.docs.projectx.com/docs/api-reference/trade/trade-search#example-request)
 * [Example Response](https://gateway.docs.projectx.com/docs/api-reference/trade/trade-search#example-response)


---

# Account | ProjectX API Documentation

*出典: https://gateway.docs.projectx.com/docs/category/account*

## [ï¸ Search for AccountAPI URL: /api/Account/search](https://gateway.docs.projectx.com/docs/api-reference/account/search-accounts)


---

# API Reference | ProjectX API Documentation

*出典: https://gateway.docs.projectx.com/docs/category/api-reference*

## [ï¸ Account](https://gateway.docs.projectx.com/docs/category/account)

## [ï¸ Market Data](https://gateway.docs.projectx.com/docs/category/market-data)

## [ï¸ Orders](https://gateway.docs.projectx.com/docs/category/orders)

## [ï¸ Positions](https://gateway.docs.projectx.com/docs/category/positions)

## [ï¸ Trades](https://gateway.docs.projectx.com/docs/category/trades)


---

# Authenticate | ProjectX API Documentation

*This section outlines the process of authenticating API requests using JSON Web Tokens.*

*出典: https://gateway.docs.projectx.com/docs/category/authenticate*

## [ï¸ Authenticate (with API key)We utilize JSON Web Tokens to authenticate all requests sent to the API. This process involves obtaining a session token, which is required for future requests.](https://gateway.docs.projectx.com/docs/getting-started/authenticate/authenticate-api-key)

## [ï¸ Authenticate (for authorized applications)We utilize JSON Web Tokens to authenticate all requests sent to the API.](https://gateway.docs.projectx.com/docs/getting-started/authenticate/authenticate-as-application)


---

# Getting Started | ProjectX API Documentation

*We've designed a very robust API for accessing and managing all aspects of your firm.*

*出典: https://gateway.docs.projectx.com/docs/category/getting-started*

## [ï¸ Authenticate](https://gateway.docs.projectx.com/docs/category/authenticate)

## [ï¸ Placing Your First OrderThis documentation outlines the process for placing your first order using our API. To successfully execute an order, you must have an active trading account associated with your user. Follow the steps below to retrieve your account details, browse available contracts, and place your order.](https://gateway.docs.projectx.com/docs/getting-started/placing-your-first-order)

## [ï¸ Connection URLs](https://gateway.docs.projectx.com/docs/getting-started/connection-urls)


---

# Market Data | ProjectX API Documentation

*Authorized users have access to order operations, allowing them to search for, modify, place, and cancel orders.*

*出典: https://gateway.docs.projectx.com/docs/category/market-data*

## [ï¸ Retrieve BarsAPI URL: /api/History/retrieveBars](https://gateway.docs.projectx.com/docs/api-reference/market-data/retrieve-bars)

## [ï¸ Search for ContractsAPI URL: /api/Contract/search](https://gateway.docs.projectx.com/docs/api-reference/market-data/search-contracts)

## [ï¸ Search for Contract by IdAPI URL: /api/Contract/searchById](https://gateway.docs.projectx.com/docs/api-reference/market-data/search-contracts-by-id)


---

# Orders | ProjectX API Documentation

*Authorized users have access to order operations, allowing them to search for, modify, place, and cancel orders.*

*出典: https://gateway.docs.projectx.com/docs/category/orders*

## [ï¸ Search for OrdersAPI URL: /api/Order/search](https://gateway.docs.projectx.com/docs/api-reference/order/order-search)

## [ï¸ Search for Open OrdersAPI URL: /api/Order/searchOpen](https://gateway.docs.projectx.com/docs/api-reference/order/order-search-open)

## [ï¸ Place an OrderAPI URL: /api/Order/place](https://gateway.docs.projectx.com/docs/api-reference/order/order-place)

## [ï¸ Cancel an OrderAPI URL: /api/Order/cancel](https://gateway.docs.projectx.com/docs/api-reference/order/order-cancel)

## [ï¸ Modify an OrderAPI URL: /api/Order/modify](https://gateway.docs.projectx.com/docs/api-reference/order/order-modify)


---

# Positions | ProjectX API Documentation

*Authorized users have access to position operations, allowing them to search for, and close positions.*

*出典: https://gateway.docs.projectx.com/docs/category/positions*

## [ï¸ Close PositionsAPI URL: /api/Position/closeContract](https://gateway.docs.projectx.com/docs/api-reference/positions/close-positions)

## [ï¸ Partially Close PositionsAPI URL: /api/Position/partialCloseContract](https://gateway.docs.projectx.com/docs/api-reference/positions/close-positions-partial)

## [ï¸ Search for PositionsAPI URL: /api/Position/searchOpen](https://gateway.docs.projectx.com/docs/api-reference/positions/search-open-positions)


---

# Realtime Updates | ProjectX API Documentation

*Realtime Updates for various events*

*出典: https://gateway.docs.projectx.com/docs/category/realtime-updates*

## [ï¸ Real Time Data OverviewThe ProjectX Real Time API utilizes SignalR library (via WebSocket) to provide real-time access to data updates involving accounts, orders, positions, balances and quotes.](https://gateway.docs.projectx.com/docs/realtime/)


---

# Trades | ProjectX API Documentation

*Authorized users have access to trade operations, allowing them to search for trades.*

*出典: https://gateway.docs.projectx.com/docs/category/trades*

## [ï¸ Search for TradesAPI URL: /api/Trade/search](https://gateway.docs.projectx.com/docs/api-reference/trade/trade-search)


---

# Authenticate (with API key) | ProjectX API Documentation

*We utilize JSON Web Tokens to authenticate all requests sent to the API. This process involves obtaining a session token, which is required for future requests.*

*出典: https://gateway.docs.projectx.com/docs/getting-started/authenticate/authenticate-api-key*

On this page
# Authenticate (with API key) We utilize JSON Web Tokens to authenticate all requests sent to the API. This process involves obtaining a session token, which is required for future requests.

## Step 1 To begin, ensure you have the following:

 * An API key obtained from your firm. If you do not have these credentials, please contact your firm.
 * The connection URLs, obtained **[here](https://gateway.docs.projectx.com/docs/getting-started/connection-urls)**.

## Step 2 API Reference: **[Login API](https://gateway-api-demo.s2f.projectx.com/swagger/index.html#/Auth/Auth_LoginKey)** Create a **POST** request with your username and API key.

 * cURL Request

 
 curl -X 'POST' \ 
 'https://gateway-api-demo.s2f.projectx.com/api/Auth/loginKey' \ 
 -H 'accept: text/plain' \ 
 -H 'Content-Type: application/json' \ 
```json
 -d '{ 
 "userName": "string", 
 "apiKey": "string" 
 }' 
```
 
## Step 3 Process the API response, and make sure the result is Success (0), then store your session token in a safe place. This session token will grant full access to the Gateway API.

 * Response

 
```json
{
  "token": "your_session_token_here",
  "success": true,
  "errorCode": 0,
  "errorMessage": null
}
```
 
## Notes All further requests will require you to provide the session token in the **"Authorization"** HTTP header using the `Bearer` method. Session tokens are only valid for 24 hours. You must revalidate your token to continue using the same session. The next step will explain how to extend / re-validate your session in case your token has expired.

 * [Step 1](https://gateway.docs.projectx.com/docs/getting-started/authenticate/authenticate-api-key#step-1)
 * [Step 2](https://gateway.docs.projectx.com/docs/getting-started/authenticate/authenticate-api-key#step-2)
 * [Step 3](https://gateway.docs.projectx.com/docs/getting-started/authenticate/authenticate-api-key#step-3)
 * [Notes](https://gateway.docs.projectx.com/docs/getting-started/authenticate/authenticate-api-key#notes)


---

# Authenticate (for authorized applications) | ProjectX API Documentation

*We utilize JSON Web Tokens to authenticate all requests sent to the API.*

*出典: https://gateway.docs.projectx.com/docs/getting-started/authenticate/authenticate-as-application*

On this page
# Authenticate (for authorized applications) We utilize JSON Web Tokens to authenticate all requests sent to the API.

## Step 1 Retrieve the admin credentials (username and password, appId, and verifyKey) that have been provided for your firm. You will need these credentials to authenticate with the API. If you do not have these credentials, please contact your Account Manager for more information.

## Step 2 API Reference: **[Login API](https://gateway-api-demo.s2f.projectx.com/swagger/index.html#/Auth/Auth_LoginApp)** Create a **POST** request with your username and password.

 * cURL Request

 
 curl -X 'POST' \ 
 'https://gateway-api-demo.s2f.projectx.com/api/Auth/loginApp' \ 
 -H 'accept: text/plain' \ 
 -H 'Content-Type: application/json' \ 
```json
 -d '{ 
 "userName": "yourUsername", 
 "password": "yourPassword", 
 "deviceId": "yourDeviceId", 
 "appId": "B76015F2-04D3-477E-9191-C5E22CB2C957", 
 "verifyKey": "yourVerifyKey" 
 }' 
```
 
## Step 3 Process the API response, and make sure the result is Success (0), then store your session token in a safe place. This session token will grant full access to the Gateway API.

 * Response

 
```json
{
  "token": "your_session_token_here",
  "success": true,
  "errorCode": 0,
  "errorMessage": null
}
```
 
## Notes All further requests will require you to provide the session token in the **"Authorization"** HTTP header using the `Bearer` method. Session tokens are only valid for 24 hours. You must revalidate your token to continue using the same session. The next step will explain how to extend / re-validate your session in case your token has expired.

 * [Step 1](https://gateway.docs.projectx.com/docs/getting-started/authenticate/authenticate-as-application#step-1)
 * [Step 2](https://gateway.docs.projectx.com/docs/getting-started/authenticate/authenticate-as-application#step-2)
 * [Step 3](https://gateway.docs.projectx.com/docs/getting-started/authenticate/authenticate-as-application#step-3)
 * [Notes](https://gateway.docs.projectx.com/docs/getting-started/authenticate/authenticate-as-application#notes)


---

# Connection URLs | ProjectX API Documentation

*出典: https://gateway.docs.projectx.com/docs/getting-started/connection-urls*

# Connection URLs

## Select an Environment Select environmentAlpha TicksBlue GuardianBluskyE8XFunding FuturesThe Futures DeskFutures EliteFXIFY FuturesGoatFundedTickTickTraderTopOneFuturesTopstepXTX3Funding


---

# Placing Your First Order | ProjectX API Documentation

*This documentation outlines the process for placing your first order using our API. To successfully execute an order, you must have an active trading account associated with your user. Follow the steps below to retrieve your account details, browse available contracts, and place your order.*

*出典: https://gateway.docs.projectx.com/docs/getting-started/placing-your-first-order*

On this page
# Placing Your First Order This documentation outlines the process for placing your first order using our API. To successfully execute an order, you must have an active trading account associated with your user. Follow the steps below to retrieve your account details, browse available contracts, and place your order.

## Step 1 To initiate the order process, you must first retrieve a list of active accounts linked to your user. This step is essential for confirming your account status before placing an order.

**API URL** : POST https://gateway-api-demo.s2f.projectx.com/api/account/search
**API Reference** : **[/api/account/search](https://gateway-api-demo.s2f.projectx.com/swagger/index.html#/Account/Account_SearchAccounts)**
 * Request
 * Response
 * cURL Request

 
```json
{
  "onlyActiveAccounts": true
}
```
 
 
```json
 { 
 "accounts": [ { "id": 1, "name": "TEST_ACCOUNT_1", "canTrade": true, 
 "isVisible": true 
 } 
```
 ], 
 "success": true, 
 "errorCode": 0, 
 "errorMessage": null 
 } 
 
 
 curl -X 'POST' \ 
 'https://gateway-api-demo.s2f.projectx.com/api/Account/search' \ 
 -H 'accept: text/plain' \ 
 -H 'Content-Type: application/json' \ 
```json
 -d '{ 
 "onlyActiveAccounts": true 
 }' 
```
 
## Step 2 Once you have identified your active accounts, the next step is to retrieve a list of contracts available for trading. This information will assist you in choosing the appropriate contracts for your order.

**API URL** : POST https://gateway-api-demo.s2f.projectx.com/api/contract/search
**API Reference** : **[/api/contract/search](https://gateway-api-demo.s2f.projectx.com/swagger/index.html#/Contract/Contract_SearchContracts)**
 * Request
 * Response
 * cURL Request

 
```json
{
  "live": false,
  "searchText": "NQ"
}
```
 
 
```json
 { 
 "contracts": [ { "id": "CON.F.US.ENQ.H25", "name": "ENQH25", "description": "E-mini NASDAQ-100: March 2025", 
 "tickSize": 0.25, 
 "tickValue": 5, 
 "activeContract": true 
 }, 
```
```json
 { 
 "id": "CON.F.US.MNQ.H25", 
 "name": "MNQH25", 
 "description": "Micro E-mini Nasdaq-100: March 2025", 
 "tickSize": 0.25, 
 "tickValue": 0.5, 
 "activeContract": true 
 }, 
```
```json
 { 
 "id": "CON.F.US.NQG.G25", 
 "name": "NQGG25", 
 "description": "E-Mini Natural Gas: February 2025", 
 "tickSize": 0.005, 
 "tickValue": 12.5, 
 "activeContract": true 
 }, 
```
```json
{
  "id": "CON.F.US.NQM.G25",
  "name": "NQMG25",
  "description": "E-Mini Crude Oil: February 2025",
  "tickSize": 0.025,
  "tickValue": 12.5,
  "activeContract": true
}
```
 ], 
 "success": true, 
 "errorCode": 0, 
 "errorMessage": null 
 } 
 
 
 curl -X 'POST' \ 
 'https://gateway-api-demo.s2f.projectx.com/api/Contract/search' \ 
 -H 'accept: text/plain' \ 
 -H 'Content-Type: application/json' \ 
```json
 -d '{ 
 "live": false, 
 "searchText": "NQ" 
 }' 
```
 
## Final Step Having noted your account ID and the selected contract ID, you are now ready to place your order. Ensure that you provide accurate details to facilitate a successful transaction.

**API URL** : POST https://gateway-api-demo.s2f.projectx.com/api/order/place
**API Reference** : **[/api/order/place](https://gateway-api-demo.s2f.projectx.com/swagger/index.html#/Order/Order_PlaceOrder)**

### Parameters Name| Type| Description| Required| Nullable 

---|---|---|---|--- 
accountId| integer| The account ID.| Required| false 
contractId| string| The contract ID.| Required| false 
type| integer| The order type: 
`1` = Limit 
`2` = Market 
`4` = Stop 
`5` = TrailingStop 
`6` = JoinBid 
`7` = JoinAsk| Required| false 
side| integer| The side of the order: 
`0` = Bid (buy) 
`1` = Ask (sell)| Required| false 
size| integer| The size of the order.| Required| false 
limitPrice| decimal| The limit price for the order, if applicable.| Optional| true 
stopPrice| decimal| The stop price for the order, if applicable.| Optional| true 
trailPrice| decimal| The trail price for the order, if applicable.| Optional| true 
customTag| string| An optional custom tag for the order.| Optional| true 
linkedOrderId| integer| The linked order id.| Optional| true 
 * Request
 * Response
 * cURL Request

 
```json
{
  "accountId": 1,
  "contractId": "CON.F.US.DA6.M25",
  "type": 2,
  "side": 1,
  "size": 1,
  "limitPrice": null,
  "stopPrice": null,
  "trailPrice": null,
  "customTag": null,
  "linkedOrderId": null
}
```
 
 
```json
{
  "orderId": 9056,
  "success": true,
  "errorCode": 0,
  "errorMessage": null
}
```
 
 
 curl -X 'POST' \ 
 'https://gateway-api-demo.s2f.projectx.com/api/Order/place' \ 
 -H 'accept: text/plain' \ 
 -H 'Content-Type: application/json' \ 
```json
 -d '{ 
 "accountId": 1, 
 "contractId": "CON.F.US.DA6.M25", 
 "type": 2, 
 "side": 1, 
 "size": 1, 
 "limitPrice": null, 
 "stopPrice": null, 
 "trailPrice": null, 
 "customTag": null, 
 "linkedOrderId": null 
 }' 
```
 
 * [Step 1](https://gateway.docs.projectx.com/docs/getting-started/placing-your-first-order#step-1)
 * [Step 2](https://gateway.docs.projectx.com/docs/getting-started/placing-your-first-order#step-2)
 * [Final Step](https://gateway.docs.projectx.com/docs/getting-started/placing-your-first-order#final-step)
 * [Parameters](https://gateway.docs.projectx.com/docs/getting-started/placing-your-first-order#parameters)


---

# ProjectX Gateway API | ProjectX API Documentation

*Getting Started*

*出典: https://gateway.docs.projectx.com/docs/intro*

On this page
# ProjectX Gateway API

## Getting Started

ProjectX Trading, LLC - through its trading platform **[ProjectX](https://www.projectx.com)** , offers a complete end-to-end solution for prop firms and evaluation providers. These features include account customization, risk rules & monitoring, liquidations, statistics and robust permissioning. Our API utilizes the REST API architecture for managing your prop firm trader operations.

### What you'll need

 * An understanding of REST API
 * cURL or Postman for making sample requests

 * [Getting Started](https://gateway.docs.projectx.com/docs/intro#getting-started)
 * [What you'll need](https://gateway.docs.projectx.com/docs/intro#what-youll-need)


---

# Real Time Data Overview | ProjectX API Documentation

*The ProjectX Real Time API utilizes SignalR library (via WebSocket) to provide real-time access to data updates involving accounts, orders, positions, balances and quotes.*

*出典: https://gateway.docs.projectx.com/docs/realtime*

On this page
# Real Time Data Overview The ProjectX Real Time API utilizes SignalR library (via WebSocket) to provide real-time access to data updates involving accounts, orders, positions, balances and quotes. There are two hubs: `user` and `market`.

 * The user hub will provide real-time updates to a user's accounts, orders, and positions.
 * The market hub will provide market data such as market trade events, DOM events, etc.

## What is SignalR? SignalR is a real-time web application framework developed by Microsoft that simplifies the process of adding real-time functionality to web applications. It allows for bidirectional communication between clients (such as web browsers) and servers, enabling features like live chat, notifications, and real-time updates without the need for constant client-side polling or manual handling of connections. SignalR abstracts away the complexities of real-time communication by providing high-level APIs for developers. It supports various transport protocols, including WebSockets, Server-Sent Events (SSE), Long Polling, and others, automatically selecting the most appropriate transport mechanism based on the capabilities of the client and server. The framework handles connection management, message routing, and scaling across multiple servers, making it easier for developers to build scalable and responsive web applications. SignalR is available for multiple platforms, including .NET and JavaScript, allowing developers to build real-time applications using their preferred programming languages and frameworks.

Further information on SignalR can be found [here](https://learn.microsoft.com/en-us/aspnet/signalr/overview/getting-started/introduction-to-signalr).
### Example Usage

* * *
 * User Hub
 * Market Hub

 
 // Import the necessary modules from @microsoft/signalr 
 const { HubConnectionBuilder, HttpTransportType } = require('@microsoft/signalr'); 
 
 // Function to set up and start the SignalR connection 
```javascript
 function setupSignalRConnection() { 
 const JWT_TOKEN = 'your_bearer_token'; 
 const SELECTED_ACCOUNT_ID = 123; //your currently selected/visible account ID 
 const userHubUrl = 'https://gateway-rtc-demo.s2f.projectx.com/hubs/user?access_token=' + JWT_TOKEN; 
 
 // Create the connection 
 const rtcConnection = new HubConnectionBuilder() 
 .withUrl(userHubUrl, { 
 skipNegotiation: true, 
 transport: HttpTransportType.WebSockets, 
 accessTokenFactory: () => JWT_TOKEN, // Replace with your current JWT token 
 timeout: 10000 // Optional timeout 
 }) 
```
 .withAutomaticReconnect() 
 .build(); 
 
 // Start the connection 
 rtcConnection.start() 
```javascript
 .then(() => { 
 // Function to subscribe to the necessary events 
 const subscribe = () => { 
 rtcConnection.invoke('SubscribeAccounts'); 
 rtcConnection.invoke('SubscribeOrders', SELECTED_ACCOUNT_ID); //you can call this function multiple times with different account IDs 
 rtcConnection.invoke('SubscribePositions', SELECTED_ACCOUNT_ID); //you can call this function multiple times with different account IDs 
 rtcConnection.invoke('SubscribeTrades', SELECTED_ACCOUNT_ID); //you can call this function multiple times with different account IDs 
 }; 
```
 
 // Functions to unsubscribe, if needed 
```javascript
 const unsubscribe = () => { 
 rtcConnection.invoke('UnsubscribeAccounts'); 
 rtcConnection.invoke('UnsubscribeOrders', SELECTED_ACCOUNT_ID); //you can call this function multiple times with different account IDs 
 rtcConnection.invoke('UnsubscribePositions', SELECTED_ACCOUNT_ID); //you can call this function multiple times with different account IDs 
 rtcConnection.invoke('UnsubscribeTrades', SELECTED_ACCOUNT_ID); //you can call this function multiple times with different account IDs 
 
 }; 
```
 
 // Set up the event listeners 
```
 rtcConnection.on('GatewayUserAccount', (data) => { 
 console.log('Received account update', data); 
 }); 
```
 
```
 rtcConnection.on('GatewayUserOrder', (data) => { 
 console.log('Received order update', data); 
 }); 
```
 
```
 rtcConnection.on('GatewayUserPosition', (data) => { 
 console.log('Received position update', data); 
 }); 
```
 
```
 rtcConnection.on('GatewayUserTrade', (data) => { 
 console.log('Received trade update', data); 
 }); 
```
 
 // Subscribe to the events 
 subscribe(); 
 
 // Handle reconnection 
```javascript
 rtcConnection.onreconnected((connectionId) => { 
 console.log('RTC Connection Reconnected'); 
 subscribe(); 
 }); 
```
 }) 
```
 .catch((err) => { 
 console.error('Error starting connection:', err); 
 }); 
```
 } 
 // Call the function to set up and start the connection 
 setupSignalRConnection(); 
 
 
 // Import the necessary modules from @microsoft/signalr 
 const { HubConnectionBuilder, HttpTransportType } = require('@microsoft/signalr'); 
 
 // Function to set up and start the SignalR connection 
```javascript
 function setupSignalRConnection() { 
 const JWT_TOKEN = 'your_bearer_token'; 
 const marketHubUrl = 'https://gateway-rtc-demo.s2f.projectx.com/hubs/market?access_token=' + JWT_TOKEN; 
 const CONTRACT_ID = 'CON.F.US.RTY.H25'; // Example contract ID 
 
 
 // Create the connection 
 const rtcConnection = new HubConnectionBuilder() 
 .withUrl(marketHubUrl, { 
 skipNegotiation: true, 
 transport: HttpTransportType.WebSockets, 
 accessTokenFactory: () => JWT_TOKEN, // Replace with your current JWT token 
 timeout: 10000 // Optional timeout 
 }) 
```
 .withAutomaticReconnect() 
 .build(); 
 
 // Start the connection 
 rtcConnection.start() 
```javascript
 .then(() => { 
 // Function to subscribe to the necessary events 
 const subscribe = () => { 
 rtcConnection.invoke('SubscribeContractQuotes', CONTRACT_ID); 
 rtcConnection.invoke('SubscribeContractTrades', CONTRACT_ID); 
 rtcConnection.invoke('SubscribeContractMarketDepth', CONTRACT_ID); 
 }; 
```
 
 // Functions to unsubscribe, if needed 
```javascript
 const unsubscribe = () => { 
 rtcConnection.invoke('UnsubscribeContractQuotes', CONTRACT_ID); 
 rtcConnection.invoke('UnsubscribeContractTrades', CONTRACT_ID); 
 rtcConnection.invoke('UnsubscribeContractMarketDepth', CONTRACT_ID); 
 }; 
```
 
 // Set up the event listeners 
```
 rtcConnection.on('GatewayQuote', (contractId, data) => { 
 console.log('Received market quote data', data); 
 }); 
```
 
```
 rtcConnection.on('GatewayTrade', (contractId, data) => { 
 console.log('Received market trade data', data); 
 }); 
```
 
```
 rtcConnection.on('GatewayDepth', (contractId, data) => { 
 console.log('Received market depth data', data); 
 }); 
```
 
 // Subscribe to the events 
 subscribe(); 
 
 // Handle reconnection 
```javascript
 rtcConnection.onreconnected((connectionId) => { 
 console.log('RTC Connection Reconnected'); 
 subscribe(); 
 }); 
```
 }) 
```
 .catch((err) => { 
 console.error('Error starting connection:', err); 
 }); 
```
 } 
 // Call the function to set up and start the connection 
 setupSignalRConnection(); 
 
 * [What is SignalR?](https://gateway.docs.projectx.com/docs/realtime#what-is-signalr)
 * [Example Usage](https://gateway.docs.projectx.com/docs/realtime#example-usage)
