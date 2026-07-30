# yfinance v1.5.1 — Complete API Reference

> **AI coding agents:** This doc is structured for quick lookup. Each API entry shows signature, parameter types, return type, and a runnable example. Return types are precise (DataFrame columns, dict keys, list shapes).

---

## Table of Contents

1. [Installation & Setup](#1-installation--setup)
2. [Quick Start](#2-quick-start)
3. [Ticker](#3-ticker)
4. [download() — Multi-Ticker Historical Data](#4-download--multi-ticker-historical-data)
5. [Tickers — Named Ticker Collection](#5-tickers--named-ticker-collection)
6. [Search](#6-search)
7. [Lookup — Type-Filtered Symbol Resolution](#7-lookup--type-filtered-symbol-resolution)
8. [Market — Market Summary & Status](#8-market--market-summary--status)
9. [Sector & Industry](#9-sector--industry)
10. [Calendars — Earnings, IPOs, Economic Events, Splits](#10-calendars--earnings-ipos-economic-events-splits)
11. [Screener — Screen Equities, Funds, ETFs](#11-screener--screen-equities-funds-etfs)
12. [Live WebSocket — Real-Time Quotes](#12-live-websocket--real-time-quotes)
13. [Auth & Login](#13-auth--login)
14. [Configuration](#14-configuration)
15. [Cache & Persistence](#15-cache--persistence)
16. [Exceptions](#16-exceptions)
17. [Internal Architecture](#17-internal-architecture)
18. [Testing](#18-testing)

---

## 1. Installation & Setup

```bash
pip install yfinance
```

### Dependencies (auto-installed)

| Package | Version | Purpose |
|---|---|---|
| `pandas` | >=1.3.0 | DataFrame core |
| `numpy` | >=1.16.5 | Numeric ops |
| `requests` | >=2.31 | HTTP (fallback) |
| `curl_cffi` | >=0.15 | HTTP with TLS impersonation **(preferred)** |
| `multitasking` | >=0.0.7 | Parallel downloads |
| `platformdirs` | >=2.0.0 | Cache directory paths |
| `pytz` | >=2022.5 | Timezone handling |
| `beautifulsoup4` | >=4.11.1 | HTML parsing (earnings calendar) |
| `lxml` | >=4.9.0 | XML/HTML parser |
| `peewee` | >=3.16.2 | SQLite cache backend |
| `requests_cache` | >=1.0 | HTTP caching (optional, nospam extra) |
| `requests_ratelimiter` | >=0.3.1 | Rate limiting (optional, nospam extra) |
| `scipy` | >=1.6.3 | Price repair (optional, repair extra) |
| `protobuf` | >=3.19.0 | WebSocket message decoding |
| `websockets` | >=13.0 | WebSocket client |

### Verify install

```python
import yfinance as yf
print(yf.__version__)  # "1.5.1"
```

### Disable curl_cffi (fallback to requests)

```bash
export YF_DISABLE_CURL_CFFI=1
# or set before import:
import os; os.environ["YF_DISABLE_CURL_CFFI"] = "1"
```

---

## 2. Quick Start

```python
import yfinance as yf

# --- Single ticker ---
aapl = yf.Ticker("AAPL")

# --- Historical prices ---
hist = aapl.history(period="1mo")           # DataFrame: Open, High, Low, Close, Volume, Dividends, Stock Splits
hist_5y = aapl.history(start="2021-01-01", end="2026-01-01", interval="1wk")

# --- Company info (dict) ---
info = aapl.info
print(info["longName"], info["sector"], info["marketCap"])

# --- Fast info (lazy, lightweight) ---
fast = aapl.fast_info
print(fast.last_price, fast.currency, fast.market_cap)

# --- Financial statements ---
income = aapl.income_stmt        # yearly income statement
bs = aapl.balance_sheet           # yearly balance sheet
cf = aapl.cash_flow              # yearly cash flow
quarterly_income = aapl.quarterly_income_stmt

# --- Dividends, splits ---
div = aapl.dividends              # Series, index=datetime
splits = aapl.splits              # Series
actions = aapl.actions            # DataFrame

# --- Holders ---
major = aapl.major_holders        # DataFrame
inst = aapl.institutional_holders
insider = aapl.insider_transactions

# --- Analyst data ---
targets = aapl.analyst_price_targets  # dict: current, low, high, mean, median
earnings_est = aapl.earnings_estimate  # DataFrame
recs = aapl.recommendations           # DataFrame

# --- Options ---
aapl.options                          # tuple of expiration date strings
opt = aapl.option_chain("2026-01-16")  # namedtuple: calls, puts (DataFrames), underlying (dict)

# --- News ---
news = aapl.news  # list of articles

# --- ESG ---
esg = aapl.sustainability  # DataFrame

# --- Multiple tickers ---
data = yf.download("AAPL MSFT GOOG", period="6mo")

# --- Live streaming ---
ws = yf.WebSocket()
ws.subscribe("AAPL")
ws.listen(lambda msg: print(msg))
```

---

## 3. Ticker

```python
class yfinance.Ticker(ticker: str | tuple[str, str], session=None)
```

- `ticker`: Yahoo Finance symbol (e.g. "AAPL") or tuple `(symbol, MIC_code)` e.g. `('OR', 'XPAR')`
- `session`: optional pre-configured `requests.Session` or `curl_cffi.Session`

### 3.1 Historical Data

```python
ticker.history(
    period: str = '1mo' (if start/end both None),
    interval: str = "1d",
    start: str | datetime | None = None,
    end: str | datetime | None = None,
    prepost: bool = False,
    actions: bool = True,
    auto_adjust: bool = True,
    back_adjust: bool = False,
    repair: bool = False,
    keepna: bool = False,
    rounding: bool = False,
    timeout: float | None = 10,
) -> pd.DataFrame
```

**Period values:** `1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `10y`, `ytd`, `max`

**Interval values:** `1m`, `2m`, `5m`, `15m`, `30m`, `60m`, `90m`, `1h`, `1d`, `5d`, `1wk`, `1mo`, `3mo`

> Intraday data limited to last 60 days.

**Returns DataFrame columns:**

| Column | Type | Description |
|---|---|---|
| `Open` | float64 | Opening price |
| `High` | float64 | High price |
| `Low` | float64 | Low price |
| `Close` | float64 | Closing price |
| `Volume` | int64 | Trading volume |
| `Dividends` | float64 | Dividend paid (0 if none) |
| `Stock Splits` | float64 | Split ratio (0 if none) |

**Index:** `DatetimeIndex` (timezone-aware, ticker's exchange timezone)

#### `repair=True` behavior

Detects and fixes 100x currency unit errors, missing data, and bad dividend adjustments. Requires `scipy` (`pip install yfinance[repair]`).

### 3.2 Info & Fast Info

```python
ticker.info -> dict
```

Returns full company profile dict from Yahoo's `quoteSummary` endpoint. Keys include: `longName`, `shortName`, `sector`, `industry`, `marketCap`, `enterpriseValue`, `trailingPE`, `forwardPE`, `pegRatio`, `psRatio`, `pbRatio`, `revenue`, `grossProfits`, `ebitda`, `beta`, `fiftyTwoWeekHigh`, `fiftyTwoWeekLow`, `dividendYield`, `payoutRatio`, `bookValue`, `priceToBook`, `earningsPerShare`, `currentPrice`, `targetMeanPrice`, `totalRevenue`, `freeCashflow`, `operatingCashflow`, `debtToEquity`, `returnOnEquity`, `returnOnAssets`, `shortRatio`, `shortPercentOfFloat`, `heldPercentInstitutions`, etc.

> ⚠️ Some price-related fields moved to `fast_info`; falling back triggers a deprecation warning.

```python
ticker.fast_info -> FastInfo (dict-like)
```

**FastInfo keys (accessible as attributes or dict-style):**

| Key | Return Type | Description |
|---|---|---|
| `currency` | str | Trading currency |
| `quote_type` | str | `EQUITY`, `ETF`, `MUTUALFUND`, `INDEX`, `CURRENCY`, `CRYPTOCURRENCY`, `FUTURE` |
| `exchange` | str | Exchange name |
| `timezone` | str | IANA timezone (e.g. `America/New_York`) |
| `shares` | int | Shares outstanding |
| `market_cap` | float | Market cap (shares × last_price) |
| `last_price` | float | Most recent closing price |
| `previous_close` | float | Previous day's close |
| `regular_market_previous_close` | float | Regular market previous close |
| `open` | float | Today's open |
| `day_high` | float | Today's high |
| `day_low` | float | Today's low |
| `last_volume` | int | Last day's volume |
| `fifty_day_average` | float | 50-day SMA |
| `two_hundred_day_average` | float | 200-day SMA |
| `ten_day_average_volume` | int | 10-day avg volume |
| `three_month_average_volume` | int | 3-month avg volume |
| `year_high` | float | 52-week high |
| `year_low` | float | 52-week low |
| `year_change` | float | YTD price change fraction |

Both camelCase (`fiftyDayAverage`) and snake_case (`fifty_day_average`) keys work.

### 3.3 Financial Statements

```python
ticker.income_stmt                    -> pd.DataFrame  # yearly
ticker.quarterly_income_stmt          -> pd.DataFrame  # quarterly
ticker.ttm_income_stmt                -> pd.DataFrame  # trailing 12 months
ticker.financials                     -> pd.DataFrame  # alias for income_stmt
ticker.balance_sheet                  -> pd.DataFrame  # yearly
ticker.quarterly_balance_sheet        -> pd.DataFrame  # quarterly
ticker.cash_flow                      -> pd.DataFrame  # yearly
ticker.quarterly_cash_flow            -> pd.DataFrame  # quarterly
ticker.ttm_cash_flow                  -> pd.DataFrame  # trailing 12 months
```

Also available as explicit methods:

```python
ticker.get_income_stmt(freq="yearly", as_dict=False, pretty=False)   -> pd.DataFrame | dict
ticker.get_balance_sheet(freq="yearly", as_dict=False, pretty=False) -> pd.DataFrame | dict
ticker.get_cash_flow(freq="yearly", as_dict=False, pretty=False)     -> pd.DataFrame | dict
ticker.get_earnings(freq="yearly", as_dict=False)                    -> pd.DataFrame | dict
ticker.get_shares(as_dict=False)                                     -> pd.DataFrame | dict
ticker.get_shares_full(start=None, end=None)                         -> pd.Series
```

- `freq`: `"yearly"`, `"quarterly"`, `"trailing"`
- `pretty`: format row index labels as readable titles
- Rows are financial line items (e.g. `TotalRevenue`, `NetIncome`, `TotalAssets`); columns are period end dates

### 3.4 Valuation Measures

```python
ticker.get_valuation_measures(freq="quarterly", periods=5) -> pd.DataFrame
ticker.valuation                                            -> pd.DataFrame  # same, default args
```

Returns valuation metrics as rows: `Market Cap`, `Enterprise Value`, `Trailing P/E`, `Forward P/E`, `PEG Ratio (5yr expected)`, `Price/Sales`, `Price/Book`, `Enterprise Value/Revenue`, `Enterprise Value/EBITDA`.

- `freq`: `"quarterly"`, `"monthly"`, `"yearly"`, `"trailing"`
- `periods`: max date columns (newest first); `0` = only `Current` column; `None` = all

### 3.5 Dividends, Splits, Actions

```python
ticker.dividends       -> pd.Series  # index=DatetimeIndex, values=dividend per share
ticker.capital_gains   -> pd.Series
ticker.splits          -> pd.Series  # index=DatetimeIndex, values=split ratio
ticker.actions         -> pd.DataFrame  # Dividends + Stock Splits columns
ticker.get_dividends(period="max")     -> pd.Series
ticker.get_capital_gains(period="max") -> pd.Series
ticker.get_splits(period="max")        -> pd.Series
ticker.get_actions(period="max")       -> pd.DataFrame
```

### 3.6 Holders

```python
ticker.major_holders                      -> pd.DataFrame
ticker.institutional_holders              -> pd.DataFrame
ticker.mutualfund_holders                 -> pd.DataFrame
ticker.insider_transactions               -> pd.DataFrame
ticker.insider_purchases                  -> pd.DataFrame
ticker.insider_roster_holders             -> pd.DataFrame

# Also as methods:
ticker.get_major_holders(as_dict=False)         -> pd.DataFrame | dict
ticker.get_institutional_holders(as_dict=False)  -> pd.DataFrame | dict
ticker.get_mutualfund_holders(as_dict=False)     -> pd.DataFrame | dict
ticker.get_insider_transactions(as_dict=False)   -> pd.DataFrame | dict
ticker.get_insider_purchases(as_dict=False)      -> pd.DataFrame | dict
ticker.get_insider_roster_holders(as_dict=False) -> pd.DataFrame | dict
```

### 3.7 Analyst Data

```python
ticker.analyst_price_targets       -> dict  # keys: current, low, high, mean, median
ticker.earnings_estimate           -> pd.DataFrame  # index: 0q, +1q, 0y, +1y
ticker.revenue_estimate            -> pd.DataFrame
ticker.earnings_history            -> pd.DataFrame  # index=DatetimeIndex
ticker.eps_trend                   -> pd.DataFrame
ticker.eps_revisions               -> pd.DataFrame
ticker.growth_estimates            -> pd.DataFrame  # index: 0q, +1q, 0y, +1y, +5y, -5y
ticker.recommendations             -> pd.DataFrame  # columns: period, strongBuy, buy, hold, sell, strongSell
ticker.recommendations_summary     -> pd.DataFrame  # alias
ticker.upgrades_downgrades         -> pd.DataFrame
ticker.get_recommendations(as_dict=False)              -> pd.DataFrame | dict
ticker.get_recommendations_summary(as_dict=False)       -> pd.DataFrame | dict
ticker.get_upgrades_downgrades(as_dict=False)           -> pd.DataFrame | dict
ticker.get_analyst_price_targets()                       -> dict
ticker.get_earnings_estimate(as_dict=False)              -> pd.DataFrame | dict
ticker.get_revenue_estimate(as_dict=False)               -> pd.DataFrame | dict
ticker.get_earnings_history(as_dict=False)               -> pd.DataFrame | dict
ticker.get_eps_trend(as_dict=False)                      -> pd.DataFrame | dict
ticker.get_eps_revisions(as_dict=False)                  -> pd.DataFrame | dict
ticker.get_growth_estimates(as_dict=False)               -> pd.DataFrame | dict
```

### 3.8 Calendar & Events

```python
ticker.calendar            -> dict  # earnings date, ex-dividend date, dividend date
ticker.earnings_dates      -> pd.DataFrame  # columns: EPS Estimate, Reported EPS, Surprise(%)
ticker.sec_filings         -> dict  # SEC filings
ticker.history_metadata    -> dict  # exchange, timezone, trading periods, instrument type

ticker.get_calendar()                       -> dict
ticker.get_sec_filings()                    -> dict
ticker.get_earnings_dates(limit=12, offset=0) -> pd.DataFrame
ticker.get_history_metadata()               -> dict
```

### 3.9 News

```python
ticker.news           -> list[dict]  # each dict: title, publisher, link, type, summary, relatedTickers
ticker.get_news(count=10, tab="news") -> list[dict]
```

`tab`: `"news"`, `"all"`, `"press releases"`

### 3.10 Options

```python
ticker.options                            -> tuple[str, ...]  # expiration dates (YYYY-MM-DD)
ticker.option_chain(date=None, tz=None)   -> Options namedtuple:
                                            .calls -> DataFrame
                                            .puts  -> DataFrame
                                            .underlying -> dict
```

**Options DataFrame columns:**

| Column | Type |
|---|---|
| `contractSymbol` | str |
| `lastTradeDate` | datetime |
| `strike` | float |
| `lastPrice` | float |
| `bid` | float |
| `ask` | float |
| `change` | float |
| `percentChange` | float |
| `volume` | int |
| `openInterest` | int |
| `impliedVolatility` | float |
| `inTheMoney` | bool |
| `contractSize` | str |
| `currency` | str |

### 3.11 ISIN

```python
ticker.get_isin()    -> str | None  # "-" if not found
ticker.isin          -> str | None  # property
```

### 3.12 Fund Data (ETF/Mutual Fund Specific)

```python
ticker.funds_data -> FundsData | None

# FundsData properties:
funds = ticker.funds_data
funds.description               -> str
funds.fund_overview              -> dict
funds.fund_operations            -> dict
funds.asset_classes              -> dict
funds.top_holdings               -> DataFrame
funds.equity_holdings            -> dict
funds.bond_holdings              -> dict
funds.bond_ratings               -> dict
funds.sector_weightings          -> dict
funds.quote_type()               -> str
```

### 3.13 Sustainability (ESG)

```python
ticker.sustainability                  -> pd.DataFrame
ticker.get_sustainability(as_dict=False) -> pd.DataFrame | dict
```

### 3.14 Live Feed from Ticker

```python
ticker.live(message_handler=print, verbose=True)
# Starts blocking WebSocket listener on this ticker.
```

---

## 4. `download()` — Multi-Ticker Historical Data

```python
yfinance.download(
    tickers: str | list,
    period: str = '1mo' if start & end both None,
    interval: str = "1d",
    start: str | datetime | None = None,
    end: str | datetime | None = None,
    actions: bool = False,
    threads: bool | int = True,
    ignore_tz: bool = None,       # auto: intraday=False, daily+=True
    group_by: str = 'column',     # 'column' or 'ticker'
    auto_adjust: bool = True,
    back_adjust: bool = False,
    repair: bool = False,
    keepna: bool = False,
    progress: bool = True,
    prepost: bool = False,
    rounding: bool = False,
    timeout: float | None = 10,
    session=None,
    multi_level_index: bool = True,
) -> pd.DataFrame | None
```

**Returns:**

- `multi_level_index=True` (default): MultiIndex DataFrame — level 0 = Ticker, level 1 = Price column
- `group_by='column'`: columns are `(Price, Ticker)` pairs
- `group_by='ticker'`: columns are `(Ticker, Price)` pairs
- Single ticker with `multi_level_index=False`: single-level columns

**Example:**

```python
import yfinance as yf

# Multiple tickers, default grouping
data = yf.download("AAPL MSFT GOOG", start="2025-01-01", end="2025-12-31")
# data.columns -> MultiIndex: ('AAPL', 'Open'), ('AAPL', 'High'), ... ('GOOG', 'Close')

# Group by ticker
data = yf.download("AAPL MSFT", period="1mo", group_by='ticker')
# data['AAPL'] -> DataFrame with Open/High/Low/Close/Volume

# Single ticker, flat index
aapl = yf.download("AAPL", period="1mo", multi_level_index=False)
# aapl.columns -> ['Open', 'High', 'Low', 'Close', 'Volume']
```

**Threading:** `threads=True` (default) uses `multitasking` for parallel fetches. Set `threads=False` or to an integer to control concurrency.

**Performance note:** `progress=True` gives a progress bar. Disable in production.

---

## 5. Tickers — Named Ticker Collection

```python
class yfinance.Tickers(tickers: str | list, session=None)
```

Groups multiple tickers with convenient property access + batch download.

```python
tickers = yf.Tickers("AAPL MSFT GOOG")
# or: yf.Tickers(["AAPL", "MSFT", "GOOG"])

# Access individual tickers:
tickers.tickers["AAPL"]   -> Ticker
tickers.tickers["MSFT"]   -> Ticker

# Batch download:
data = tickers.history(period="1mo")
# or: tickers.download(period="1mo")

# Batch news:
news = tickers.news()     # dict: {ticker: [articles]}

# Live streaming all:
tickers.live(print)
```

---

## 6. Search

```python
class yfinance.Search(
    query: str,
    max_results: int = 8,
    news_count: int = 8,
    lists_count: int = 8,
    include_cb: bool = True,
    include_nav_links: bool = False,
    include_research: bool = False,
    include_cultural_assets: bool = False,
    enable_fuzzy_query: bool = False,
    recommended: int = 8,
    session=None,
    timeout: int = 30,
    raise_errors: bool = True,
)
```

**Properties (all lists of dicts):**

```python
s = yf.Search("Apple")

s.quotes      -> list[dict]  # matching tickers with symbol, name, exchange, type
s.news        -> list[dict]  # news articles
s.lists       -> list[dict]
s.research    -> list[dict]  # research reports
s.nav         -> list[dict]  # navigation links
s.all         -> dict[str, list]  # all above combined in one dict
s.response    -> dict        # raw JSON response
s.query       -> str         # the original query
```

---

## 7. Lookup — Type-Filtered Symbol Resolution

```python
class yfinance.Lookup(query: str, session=None, timeout=30, raise_errors=True)
```

Returns `pd.DataFrame` indexed by symbol.

```python
l = yf.Lookup("Apple")

l.all              -> DataFrame  # all instrument types
l.stock            -> DataFrame  # equities only
l.mutualfund       -> DataFrame  # mutual funds only
l.etf              -> DataFrame  # ETFs only
l.index            -> DataFrame  # indices only
l.future           -> DataFrame  # futures only
l.currency         -> DataFrame  # currencies only
l.cryptocurrency   -> DataFrame  # cryptocurrencies only

# Also methods with count param:
l.get_all(count=25)           -> DataFrame
l.get_stock(count=25)         -> DataFrame
l.get_mutualfund(count=25)    -> DataFrame
l.get_etf(count=25)           -> DataFrame
l.get_index(count=25)         -> DataFrame
l.get_future(count=25)        -> DataFrame
l.get_currency(count=25)      -> DataFrame
l.get_cryptocurrency(count=25) -> DataFrame
```

---

## 8. Market — Market Summary & Status

```python
class yfinance.Market(market: str | MarketRegion, session=None, timeout=30)
```

**MarketRegion enum values:**
`US`, `GB`, `ASIA`, `EUROPE`, `RATES`, `COMMODITIES`, `CURRENCIES`, `CRYPTOCURRENCIES`

```python
us = yf.Market(yf.MarketRegion.US)
# or: yf.Market("US")

us.status    -> dict  # market open/close times, timezone, current status
us.summary   -> dict  # key market indices summary (symbol, price, change, change%)

# Access specific summary:
us.summary["^GSPC"]  # S&P 500 summary
```

---

## 9. Sector & Industry

### 9.1 Sector

```python
class yfinance.Sector(key: str, session=None, region: str = "US")

s = yf.Sector("technology")

s.name               -> str                     # e.g. "Technology"
s.symbol             -> str                     # e.g. "TECH"
s.overview           -> dict                    # description, exchange, etc.
s.top_companies     -> DataFrame               # top companies in sector
s.top_etfs           -> dict[str, str]          # {symbol: name}
s.top_mutual_funds   -> dict[str, str]          # {symbol: name}
s.industries         -> DataFrame               # industries within sector
s.research_reports   -> list[dict]              # research reports
```

### 9.2 Industry

```python
class yfinance.Industry(key: str, session=None, region: str = "US")

ind = yf.Industry("technology-software")

ind.name                       -> str
ind.symbol                     -> str
ind.overview                   -> dict
ind.top_companies              -> DataFrame
ind.research_reports           -> list[dict]
ind.sector_key                 -> str           # parent sector key
ind.sector_name                -> str           # parent sector name
ind.top_performing_companies   -> DataFrame     # columns: symbol, name, ytd return, last price, target price
ind.top_growth_companies       -> DataFrame     # columns: symbol, name, ytd return, growth estimate
```

### Known Sector Keys

| Key | Sector |
|---|---|
| `basic-materials` | Basic Materials |
| `communication-services` | Communication Services |
| `consumer-cyclical` | Consumer Cyclical |
| `consumer-defensive` | Consumer Defensive |
| `energy` | Energy |
| `financial-services` | Financial Services |
| `healthcare` | Healthcare |
| `industrials` | Industrials |
| `real-estate` | Real Estate |
| `technology` | Technology |
| `utilities` | Utilities |

---

## 10. Calendars — Earnings, IPOs, Economic Events, Splits

```python
class yfinance.Calendars(
    start: str | datetime | date | None = None,   # default: today
    end: str | datetime | date | None = None,     # default: start + 7 days
    session=None,
)
```

### Earnings Calendar

```python
cal = yf.Calendars()

# Default getter:
cal.get_earnings_calendar(
    market_cap: float | None = None,
    filter_most_active: bool = True,
    start=None, end=None,
    limit=12, offset=0,
    force=False,
) -> pd.DataFrame

# Property (cached):
cal.earnings_calendar -> pd.DataFrame
```

**Returns DataFrame columns:** Symbol, Company, Event Type, EPS Estimate, Reported EPS, Surprise(%), Marketcap, Event Start Date, Timing

### IPO Calendar

```python
cal.get_ipo_info_calendar(start=None, end=None, limit=12, offset=0, force=False) -> pd.DataFrame
cal.ipo_info_calendar -> pd.DataFrame
```

**Returns DataFrame columns:** Symbol, Company, Exchange, Filing Date, Date, Amended Date, Price From, Price To, Price, Shares, Deal Type, Currency

### Economic Events Calendar

```python
cal.get_economic_events_calendar(start=None, end=None, limit=12, offset=0, force=False) -> pd.DataFrame
cal.economic_events_calendar -> pd.DataFrame
```

**Returns DataFrame columns:** Event, Region, Event Time, Period, Actual, Expected, Last, Revised

### Splits Calendar

```python
cal.get_splits_calendar(start=None, end=None, limit=12, offset=0, force=False) -> pd.DataFrame
cal.splits_calendar -> pd.DataFrame
```

**Returns DataFrame columns:** Symbol, Company, Payable On, Optionable, Old Share Worth, New Share Worth

### CalendarQuery (for custom queries)

```python
class yfinance.CalendarQuery(operator: str, operand: list)

# Operators: eq, gte, lte, gt, lt, and, or, gtelt
# Nest them for complex filters:

from yfinance import CalendarQuery

q = CalendarQuery("and", [
    CalendarQuery("eq", ["region", "us"]),
    CalendarQuery("gte", ["startdatetime", "2025-06-01"]),
])
```

---

## 11. Screener — Screen Equities, Funds, ETFs

```python
yfinance.screen(
    query: str | EquityQuery | FundQuery | ETFQuery | dict,
    count: int = 25,
    offset: int = 0,
    region: str = "us",
    lang: str = "en-US",
) -> dict
```

### Predefined Screeners

```python
from yfinance import screen, PREDEFINED_SCREENER_QUERIES

# Available presets (keys of PREDEFINED_SCREENER_QUERIES):
# 'aggressive_small_caps', 'day_gainers', 'day_losers',
# 'growth_technology_stocks', 'most_actives', 'most_shorted_stocks',
# 'small_cap_gainers', 'undervalued_growth_stocks', 'undervalued_large_caps',
# 'conservative_foreign_funds', 'high_yield_bond', 'portfolio_anchors',
# 'solid_large_growth_funds', 'solid_midcap_growth_funds'

result = screen("MOST_ACTIVES", count=50)
# result -> dict with "quotes" list
```

### EquityQuery, FundQuery, ETFQuery

Build custom screener queries:

```python
from yfinance import EquityQuery, FundQuery, ETFQuery

# Operators: eq, is-in, btwn, gt, lt, gte, lte
# Logical: and, or

q = EquityQuery('and', [
    EquityQuery('eq', ['region', 'us']),
    EquityQuery('gte', ['intradaymarketcap', 10_000_000_000]),
    EquityQuery('btwn', ['peratio.lasttwelvemonths', 0, 20]),
])

result = screen(q, count=25)
```

**EquityQuery valid values** (restricted sets for certain fields):

- `exchange`: see `EQUITY_SCREENER_EQ_MAP` in source
- `region`: country code keys from exchange map
- `sector`, `industry`: standard sector/industry names
- `peer_group`: fund peer group names

**FundQuery valid fields:** `categoryname`, `performanceratingoverall`, `initialinvestment`, `annualreturnnavy1categoryrank`, `riskratingoverall`, `exchange`, `eodprice`

**ETFQuery valid fields:** `categoryname`, `fundfamilyname`, `region`, `primary_sector`, `morningstar_economic_moat`, `morningstar_stewardship`, `morningstar_uncertainty`, `morningstar_moat_trend`, `morningstar_rating_change`, `fundnetassets`, `annualreportgrossexpenseratio`, `annualreportnetexpenseratio`, `turnoverratio`, `annualreturnnavy1`, etc.

### Screener Response Format

```python
{
    "quotes": [
        {
            "symbol": str,
            "shortName": str,
            "regularMarketPrice": float,
            "regularMarketChange": float,
            "regularMarketChangePercent": float,
            # ... plus requested fields
        }
    ],
    "totalCount": int,
    "status": str
}
```

---

## 12. Live WebSocket — Real-Time Quotes

### 12.1 Sync WebSocket

```python
class yfinance.WebSocket(url: str = "wss://streamer.finance.yahoo.com/?version=2", verbose=True)

ws = yf.WebSocket()

ws.subscribe("AAPL")                          # subscribe one symbol
ws.subscribe(["AAPL", "MSFT", "GOOG"])        # subscribe multiple
ws.unsubscribe("MSFT")                        # unsubscribe

# Blocking listener:
ws.listen(lambda msg: print(msg))             # callback receives decoded dict

# Context manager:
with yf.WebSocket() as ws:
    ws.subscribe("AAPL")
    ws.listen(print)

ws.close()                                    # close connection
```

### 12.2 Async WebSocket

```python
class yfinance.AsyncWebSocket(url: str = "wss://streamer.finance.yahoo.com/?version=2", verbose=True)

aws = yf.AsyncWebSocket()
await aws.subscribe("AAPL")
await aws.listen(print)
await aws.close()
```

### Streaming Message Format

Each decoded message is a dict with fields:

```python
{
    "id": str,            # subscription ID
    "type": str,          # event type (e.g. "quote")
    "symbol": str,        # ticker symbol
    "price": float,       # current price
    "time": int,          # Unix timestamp (ms)
    "volume": int,
    "bid": float,
    "ask": float,
    "bidSize": int,
    "askSize": int,
    # ... other fields defined in pricing.proto
}
```

---

## 13. Auth & Login

```python
class yfinance.Auth(session=None)

auth = yf.Auth()

# Set login cookies (from browser Developer Tools → Application → Cookies):
#   Cookie T: value from finance.yahoo.com
#   Cookie Y: value from finance.yahoo.com
auth.set_login_cookies(cookie_t="...", cookie_y="...") -> bool  # True if valid

auth.check_login()                     -> bool   # verify login state
auth.subscription_tier()               -> str | None  # "gold", "silver", "bronze", "free", None
auth.user                               -> dict | None  # {"guid": "..."} or None
```

Also accessible from package:

```python
yf.Auth  # = yfinance.Auth
```

---

## 14. Configuration

```python
yfinance.config  # singleton YfConfig object (ConfigMgr)
```

### Config Sections

```python
# Network settings:
yf.config.network.proxy = "http://proxy:8080"   # set HTTP proxy
yf.config.network.retries = 3                    # max HTTP retries (default: 0)

# Debug settings:
yf.config.debug.hide_exceptions = True           # suppress exceptions, log instead (default: True)
yf.config.debug.logging = False                  # enable verbose debug logging

# Locale settings (for Yahoo API lang/region params):
yf.config.locale.lang = "en-US"                  # BCP-47 language tag (default: en-US)
yf.config.locale.region = "US"                   # ISO 3166-1 alpha-2 (default: US)

# Legacy helper (triggers DeprecationWarning, routes to config):
yf.set_config(proxy="http://proxy:8080", retries=3)

# Debug mode toggle:
yf.enable_debug_mode()  # sets logging to DEBUG level
```

---

## 15. Cache & Persistence

yfinance uses SQLite caches via `peewee` for performance:

| Cache | Location | Purpose |
|---|---|---|
| Timezone cache | `~/.cache/py-yfinance/tkr-tz.db` | Maps ticker → IANA timezone |
| ISIN cache | `~/.cache/py-yfinance/isin-tkr.db` | Maps ISIN → ticker symbol |
| Cookie cache | `~/.cache/py-yfinance/cookies.db` | Persists Yahoo auth cookies |
| HTTP cache | `requests_cache` (optional) | Caches HTTP responses (nospam extra) |

```python
# Custom cache location (call before first ticker fetch):
yf.set_tz_cache_location("/custom/path")
yf.set_cache_location("/custom/path")  # sets all three caches
```

**Cache can be disabled** by setting location to a read-only path; yfinance degrades gracefully.

---

## 16. Exceptions

```python
yfinance.exceptions.YFException                    # Base exception
yfinance.exceptions.YFDataException                # Data fetch/parse failure
yfinance.exceptions.YFNotImplementedError          # Feature not yet implemented
yfinance.exceptions.YFTickerMissingError           # Ticker not found / delisted
yfinance.exceptions.YFTzMissingError               # No timezone found for ticker
yfinance.exceptions.YFPricesMissingError           # No price data found
yfinance.exceptions.YFEarningsDateMissing          # No earnings dates found
yfinance.exceptions.YFInvalidPeriodError           # Invalid period string
yfinance.exceptions.YFRateLimitError               # 429 Too Many Requests
```

```python
# Control exception behavior:
yf.config.debug.hide_exceptions = False  # raise exceptions instead of logging
```

---

## 17. Internal Architecture

### Package Layers

```
User code (your script)
    │
    ▼
yfinance/__init__.py    ← Public exports (Ticker, download, Search, Market, etc.)
    │
    ├── Ticker (ticker.py, base.py)
    │       ├── delegates to scrapers/quote.py     → info, sustainability, calendar, recommendations, sec_filings
    │       ├── delegates to scrapers/history.py   → historical OHLCV prices
    │       ├── delegates to scrapers/fundamentals.py → financial statements, shares
    │       ├── delegates to scrapers/analysis.py  → analyst estimates, price targets, trends
    │       ├── delegates to scrapers/holders.py   → major/institutional/insider holders
    │       └── delegates to scrapers/funds.py     → ETF/mutual fund specific data
    │
    ├── download() (multi.py)  → parallel multi-ticker history via multitasking
    ├── Tickers (tickers.py)   → ticker collection with batch ops
    ├── Search (search.py)     → ticker/news search
    ├── Lookup (lookup.py)     → type-filtered symbol lookup
    ├── Market (domain/market.py) → market summary & status
    ├── Sector (domain/sector.py) → sector data
    ├── Industry (domain/industry.py) → industry data
    ├── Calendars (calendars.py) → earnings/IPO/economic event/split calendars
    ├── Screener (screener/)   → market screening with query DSL
    ├── WebSocket (live.py)    → real-time streaming via Yahoo Finance websocket
    ├── Auth (data.py)         → login cookie management
    │
    ├── data.py    → YfData (Singleton HTTP layer: cookie/crumb management, caching, retry)
    ├── _http.py   → Low-level HTTP backend (curl_cffi with requests fallback)
    ├── cache.py   → SQLite caches (TZ, ISIN, cookies) via peewee
    ├── config.py  → Global config singleton
    ├── const.py   → URLs, MIC mappings, field names, screener maps
    ├── utils.py   → Logging, timezone validation, formatting helpers
    └── exceptions.py → Exception hierarchy
```

### Data Flow

```
User calls Ticker.info
    → TickerBase.get_info()
        → Quote._fetch_info()
            → Analysis._fetch() or Quote._fetch()
                → YfData.get_raw_json() or YfData.cache_get()
                    → _http (curl_cffi.Session.get or requests.Session.get)
                        → Yahoo Finance API
                    ← JSON response
                ← parsed dict/DataFrame
            ← cached in scraper object
        ← returned to user
```

### Session & Cookie Management

- `YfData` is a singleton: one session, one cookie crumb shared across all threads.
- Two cookie strategies: `basic` (fc.yahoo.com + crumb) and `csrf` (consent form + crumb).
- Auto-fallback if one strategy fails.
- Cookies persisted to SQLite for reuse across sessions.
- On 4xx responses, switches cookie strategy and retries.

---

## 18. Testing

```bash
# Install test dependencies
pip install -e ".[repair]"

# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_ticker.py

# Run with verbose output
pytest tests/ -v

# Type checking
pyright yfinance/

# Linting
ruff check yfinance/
```

### Test Files

| File | Tests |
|---|---|
| `tests/test_ticker.py` | Ticker methods (info, history, financials, options) |
| `tests/test_prices.py` | Price data integrity |
| `tests/test_multi.py` | Multi-ticker download |
| `tests/test_utils.py` | Utility functions |
| `tests/test_price_repair.py` | Price repair logic |
| `tests/test_screener.py` | Screener queries |
| `tests/test_search.py` | Search functionality |
| `tests/test_ticker_locale.py` | Locale-specific behavior |
| `tests/test_sector_region.py` | Sector/region data |

---

## Quick Reference Card (for AI agents)

### Most Common Operations

| Task | Code |
|---|---|
| Get ticker object | `yf.Ticker("AAPL")` |
| Get price history | `ticker.history(period="1mo")` |
| Get all info | `ticker.info` |
| Get fast price snapshot | `ticker.fast_info.last_price` |
| Get income statement | `ticker.income_stmt` |
| Get balance sheet | `ticker.balance_sheet` |
| Get cash flow | `ticker.cash_flow` |
| Get dividends | `ticker.dividends` |
| Get institutional holders | `ticker.institutional_holders` |
| Get analyst targets | `ticker.analyst_price_targets` |
| Get recommendations | `ticker.recommendations` |
| Get options chain | `ticker.option_chain("2026-01-16")` |
| Get news | `ticker.news` |
| Download multiple | `yf.download("AAPL MSFT", period="1y")` |
| Search tickers | `yf.Search("Apple").quotes` |
| Lookup instruments | `yf.Lookup("Apple").stock` |
| Screen market | `yf.screen("MOST_ACTIVES", count=50)` |
| Get earnings calendar | `yf.Calendars().earnings_calendar` |
| Live stream quotes | `yf.WebSocket().subscribe("AAPL").listen(print)` |
| Configure proxy | `yf.config.network.proxy = "http://..."` |
| Login with cookies | `yf.Auth().set_login_cookies("T_val", "Y_val")` |
