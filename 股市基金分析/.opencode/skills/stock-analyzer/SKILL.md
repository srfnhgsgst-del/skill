---
name: stock-analyzer
description: Use ONLY when working on the StockFund Analyzer platform — a real-time stock/fund analysis tool with FastAPI backend and React/Recharts frontend. Covers adding API endpoints, technical indicators, chart components, candlestick mode, MACD, localStorage, CSV export, and more. Trigger keywords: stock, fund, 股票, 基金, 分析, yfinance, 行情, 技术指标, MA, RSI, Bollinger, MACD, K-line, candlestick, CSV.
---

# StockFund Analyzer v3.0

## Architecture

| Layer | Technology | File |
|-------|-----------|------|
| Backend | FastAPI + Uvicorn (port 8000) | `backend/main.py` |
| Data | yfinance (Yahoo Finance) | via `yf.Ticker()` |
| Frontend | Single-page HTML, React 18 CDN, Recharts, JSX (Babel standalone) | `frontend/index.html` |
| Deps | fastapi, uvicorn, yfinance, pandas, numpy, pydantic | `backend/requirements.txt` |
| Skill | opencode skill | `.opencode/skills/stock-analyzer/SKILL.md` |

## Quick Start

```powershell
cd backend
pip install -r requirements.txt
python main.py           # → http://localhost:8000
# Open frontend/index.html in a browser
```

## API Reference

### `GET /api/health`
Returns `{"status":"ok","version":"2.0"}`.

### `GET /api/search?q=<query>&limit=10`
Search ~35 popular US/CN/HK stocks and ETFs by symbol or name.

### `GET /api/stock/{symbol}`
Real-time quote: price, change%, OHLCV, market cap, PE, dividend yield, 52-week range, currency.

### `GET /api/history/{symbol}?period=1mo&interval=1h&indicators=true`
OHLCV history + computed indicators:
- MA5 / MA10 / MA20 / MA60
- RSI(14)
- Bollinger Bands (upper, mid, lower)
- **MACD** (DIF, DEA, histogram bar)

Periods: `1d|5d|1mo|3mo|6mo|1y|2y|5y|max`
Intervals: `1m|5m|15m|30m|60m|1h|1d|1wk|1mo`

### `GET /api/batch?symbols=AAPL,TSLA,NVDA`
Batch up to 10 symbols.

### `GET /api/fund/{symbol}`
Fund/ETF: NAV, YTD/3yr/5yr returns, expense ratio, total assets.

### `GET /api/market_overview`
6 major indices: S&P 500, DJIA, NASDAQ, HSI, SSE, SZSE.

## Symbol Formats

| Market | Format | Example |
|--------|--------|---------|
| US Stock | TICKER | `AAPL` |
| Shanghai | TICKER.SS | `600519.SS` |
| Shenzhen | TICKER.SZ | `000001.SZ` |
| Hong Kong | TICKER.HK | `0700.HK` |
| ETF | TICKER | `SPY`, `QQQ` |
| Index | ^TICKER | `^GSPC` |

## Technical Indicators (server-side)

Computed in `backend/main.py`:

```python
compute_ma(series, window)        # rolling mean → MA5/10/20/60
compute_rsi(series, period=14)    # EMA-based → RSI(14)
compute_bollinger(series, 20, 2)  # Bollinger Bands (upper/mid/lower)
compute_macd(series, 12, 26, 9)   # MACD DIF, DEA, bar
```

To add a new indicator:
1. Add function in `backend/main.py` (mirror existing function pattern)
2. Compute in `/api/history` endpoint (in the `indicators` block)
3. Add to `record.update()` for each data point
4. Add to `latest_indicators` dict
5. Display in frontend via badges and/or chart panel

## Frontend Component Tree (v3.0)

```
App
├── MarketTicker (6 indices, top bar)
├── Sidebar (180px)
│   ├── SearchBox (autocomplete via /api/search)
│   └── WatchlistComp (localStorage-persisted, remove button)
└── Main
    ├── StockHeader (symbol, name, price, change%)
    ├── StatsGrid (8 cards: O, H, L, Vol, MktCap, PE, Div, 52W)
    ├── IndicatorBadges (RSI, MA5/10/20, MACD, [Export CSV button])
    ├── PeriodSelector + CandleMode toggle
    ├── PriceChart (ComposedChart, syncId="s")
    │   ├── Area mode (gradient fill) + MA/BB indicator lines
    │   └── Candle mode (Customized + CandleOverlay SVG) + MA/BB lines
    ├── MACDChart (ComposedChart: Bar histogram + DIF/DEA lines)
    ├── VolumeChart (BarChart, synced)
    └── RSIChart (LineChart, ReferenceLine at 70/30)
```

## v3.0 New Features

### Candlestick (OHLC) Mode
- Toggle button (`Candle`/`Area`) in period toolbar
- Uses Recharts `<Customized>` component to render SVG rects + line wicks
- `CandleOverlay` component accesses `xAxisMap[0].scale` for coordinate mapping
- Green body for up days, red for down days

### MACD Indicator
- Backend: `compute_macd()` → EMA12, EMA26, DIF = EMA12 - EMA26, DEA = 9-period EMA of DIF, MACD bar = 2×(DIF - DEA)
- Frontend: Dedicated MACD panel with colored histogram, DIF line (blue), DEA line (gold)
- Bar colors: green if MACD bar ≥ 0, red if < 0 (uses `R.Cell` per-bar coloring)

### localStorage Watchlist Persistence
- Watchlist saved to `localStorage` key `stockfund_watchlist` on every change
- Loaded on app mount via `loadWatchlist()` → `JSON.parse`
- Fallback to `DEFAULT_WATCHLIST` on parse failure
- Remove button (×) on each watchlist item

### CSV Export
- `exportCSV()` function in App component
- Generates CSV with headers: date, open, high, low, close, volume, ma5, ma10, ma20, ma60, rsi14
- Triggers browser download via `Blob` + `URL.createObjectURL`

## Auto-Refresh

- Frontend polls every 30 seconds (countdown displayed in sidebar)
- Watchlist updates via `/api/batch` (single request)
- Backend in-memory cache with 30s TTL

## Common Issues

- **Empty price**: Fallback chain: `currentPrice` → `regularMarketPrice` → `navPrice` → `bid` → history close
- **A-share delay**: Yahoo China data delayed ~15 min
- **yfinance rate limiting**: Increase cache TTL or add retry logic
- **CORS**: Backend on port 8000 with CORS `allow_origins=["*"]`
- **CDN**: jsdelivr CDN used for all frontend dependencies (React 18.3.1, Recharts 2.12.0, Babel 7.24)
- **Candlestick not rendering**: Check if `Customized` component receives valid `xAxisMap[0].scale` — the scale must be a d3 scale function returning pixel positions for date values

## Adding a Feature

### New API Endpoint
1. Add endpoint in `backend/main.py` with `try/except HTTPException`
2. Test with `curl http://localhost:8000/api/<endpoint>`
3. Consume in frontend via `fetch(API+"/<endpoint>")`

### New Chart Panel
1. Add Recharts component with `syncId="s"` for crosshair sync
2. Wrap in `ResponsiveContainer` with percentage height
3. Add condition `histData.length > 0 && histData.some(...)` for empty state

### New Technical Indicator
1. Backend: Add function, compute in `/api/history`, include in response
2. Frontend: Add to indicator badges and/or create new chart panel