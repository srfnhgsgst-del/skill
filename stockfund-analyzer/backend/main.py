from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import pandas as pd
import numpy as np
import logging
import time
import yfinance.exceptions as yf_err

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("stockfund")

app = FastAPI(title="StockFund-Analyzer API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CACHE_TTL = 60
_cache_store = {}

def safe_fetch(func, *args, retries=2, delay=3, **kwargs):
    for attempt in range(retries + 1):
        try:
            return func(*args, **kwargs)
        except yf_err.YFRateLimitError:
            if attempt < retries:
                logger.warning(f"Rate limited, retrying in {delay}s (attempt {attempt+1}/{retries})...")
                time.sleep(delay)
                delay *= 2
            else:
                raise
    return None

def compute_ma(series: pd.Series, window: int):
    result = series.rolling(window=window).mean()
    return [round(float(v), 2) if pd.notna(v) else None for v in result.tolist()]

def compute_rsi(series: pd.Series, period: int = 14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return [round(float(v), 2) if pd.notna(v) else None for v in rsi.tolist()]

def compute_bollinger(series: pd.Series, window: int = 20, num_std: float = 2.0):
    ma = series.rolling(window=window).mean()
    std = series.rolling(window=window).std()
    upper = ma + num_std * std
    lower = ma - num_std * std
    return (
        [round(float(v), 2) if pd.notna(v) else None for v in upper.tolist()],
        [round(float(v), 2) if pd.notna(v) else None for v in ma.tolist()],
        [round(float(v), 2) if pd.notna(v) else None for v in lower.tolist()],
    )

def compute_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False).mean()
    bar = 2 * (dif - dea)
    return (
        [round(float(v), 4) if pd.notna(v) else None for v in dif.tolist()],
        [round(float(v), 4) if pd.notna(v) else None for v in dea.tolist()],
        [round(float(v), 4) if pd.notna(v) else None for v in bar.tolist()],
    )


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "2.0", "timestamp": time.time()}

@app.get("/api/search")
async def search_symbol(q: str, limit: int = 10):
    popular = [
        ("AAPL", "Apple Inc.", "\u7f8e\u80a1"),
        ("MSFT", "Microsoft Corp.", "\u7f8e\u80a1"),
        ("GOOGL", "Alphabet Inc.", "\u7f8e\u80a1"),
        ("AMZN", "Amazon.com", "\u7f8e\u80a1"),
        ("TSLA", "Tesla Inc.", "\u7f8e\u80a1"),
        ("META", "Meta Platforms", "\u7f8e\u80a1"),
        ("NVDA", "NVIDIA Corp.", "\u7f8e\u80a1"),
        ("JPM", "JPMorgan Chase", "\u7f8e\u80a1"),
        ("V", "Visa Inc.", "\u7f8e\u80a1"),
        ("JNJ", "Johnson & Johnson", "\u7f8e\u80a1"),
        ("600519.SS", "\u8d35\u5dde\u8305\u53f0", "A\u80a1(\u6caa)"),
        ("601318.SS", "\u4e2d\u56fd\u5e73\u5b89", "A\u80a1(\u6caa)"),
        ("600036.SS", "\u62db\u5546\u94f6\u884c", "A\u80a1(\u6caa)"),
        ("600276.SS", "\u6052\u745e\u533b\u836f", "A\u80a1(\u6caa)"),
        ("600900.SS", "\u957f\u6c5f\u7535\u529b", "A\u80a1(\u6caa)"),
        ("000001.SZ", "\u5e73\u5b89\u94f6\u884c", "A\u80a1(\u6df1)"),
        ("000858.SZ", "\u4e94\u7cae\u6db2", "A\u80a1(\u6df1)"),
        ("000333.SZ", "\u7f8e\u7684\u96c6\u56e2", "A\u80a1(\u6df1)"),
        ("002415.SZ", "\u6d77\u5eb7\u5a01\u89c6", "A\u80a1(\u6df1)"),
        ("300750.SZ", "\u5b81\u5fb7\u65f6\u4ee3", "A\u80a1(\u6df1)"),
        ("0700.HK", "\u817e\u8baf\u63a7\u80a1", "\u6e2f\u80a1"),
        ("9988.HK", "\u963f\u91cc\u5df4\u5df4-SW", "\u6e2f\u80a1"),
        ("0941.HK", "\u4e2d\u56fd\u79fb\u52a8", "\u6e2f\u80a1"),
        ("2318.HK", "\u4e2d\u56fd\u5e73\u5b89", "\u6e2f\u80a1"),
        ("SPY", "SPDR S&P 500 ETF", "ETF"),
        ("QQQ", "Invesco QQQ Trust", "ETF"),
        ("IWM", "iShares Russell 2000 ETF", "ETF"),
        ("VOO", "Vanguard S&P 500 ETF", "ETF"),
        ("EEM", "iShares MSCI Emerging Markets", "ETF"),
        ("GLD", "SPDR Gold Shares", "ETF"),
        ("GBTC", "Grayscale Bitcoin Trust", "\u52a0\u5bc6"),
    ]
    q_lower = q.lower()
    results = []
    for sym, name, mkt in popular:
        if q_lower in sym.lower() or q_lower in name:
            results.append({"symbol": sym, "name": name, "market": mkt})
            if len(results) >= limit:
                break
    return results

@app.get("/api/stock/{symbol}")
async def get_stock_realtime(symbol: str):
    try:
        for attempt in range(3):
            try:
                ticker = yf.Ticker(symbol.upper())
                info = ticker.info
                break
            except yf_err.YFRateLimitError:
                if attempt < 2:
                    logger.warning(f"Rate limited for {symbol}, retrying...")
                    time.sleep(3)
                else:
                    raise

        price = (
            info.get("currentPrice")
            or info.get("regularMarketPrice")
            or info.get("navPrice")
            or info.get("bid")
        )
        prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose")

        if price is None:
            history_1d = ticker.history(period="1d")
            if not history_1d.empty:
                price = round(float(history_1d["Close"].iloc[-1]), 2)
        if prev_close is None:
            history_5d = ticker.history(period="5d")
            if len(history_5d) >= 2:
                prev_close = round(float(history_5d["Close"].iloc[-2]), 2)

        if price is None:
            raise HTTPException(status_code=404, detail=f"Cannot fetch price for {symbol}")

        change = price - prev_close if prev_close else 0
        change_percent = (change / prev_close * 100) if prev_close else 0

        return {
            "symbol": symbol.upper(),
            "name": info.get("longName") or info.get("shortName") or symbol,
            "price": price,
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "open": info.get("open") or info.get("regularMarketOpen"),
            "high": info.get("dayHigh") or info.get("regularMarketDayHigh"),
            "low": info.get("dayLow") or info.get("regularMarketDayLow"),
            "volume": info.get("volume") or info.get("regularMarketVolume"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE") or info.get("forwardPE"),
            "dividend_yield": info.get("dividendYield"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "currency": info.get("currency", "USD"),
            "market": info.get("market"),
        }
    except HTTPException:
        raise
    except yf_err.YFRateLimitError:
        raise HTTPException(status_code=429, detail="Yahoo Finance rate limit exceeded. Please wait 30s and try again.")
    except Exception as e:
        logger.error(f"Error fetching {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history/{symbol}")
async def get_stock_history(
    symbol: str,
    period: str = Query("1mo", pattern=r"^(1d|5d|1mo|3mo|6mo|1y|2y|5y|max)$"),
    interval: str = Query("1d", pattern=r"^(1m|5m|15m|30m|60m|1h|1d|1wk|1mo)$"),
    indicators: bool = Query(True),
):
    try:
        for attempt in range(3):
            try:
                ticker = yf.Ticker(symbol.upper())
                df = ticker.history(period=period, interval=interval)
                break
            except yf_err.YFRateLimitError:
                if attempt < 2:
                    logger.warning(f"Rate limited for {symbol} history, retrying...")
                    time.sleep(3)
                else:
                    raise
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No history for {symbol}")

        df.reset_index(inplace=True)
        date_col_name = None
        for col in df.columns:
            if col.lower() in ("date", "datetime", "index") or pd.api.types.is_datetime64_any_dtype(df[col]):
                date_col_name = col
                break
        if date_col_name is None:
            date_col_name = df.columns[0]
        date_col = df[date_col_name]
        fmt = "%Y-%m-%d %H:%M" if interval in ("1m", "5m", "15m", "30m", "60m", "1h") else "%Y-%m-%d"
        dates = date_col.dt.strftime(fmt)

        result = {"symbol": symbol.upper(), "period": period, "interval": interval, "data": []}

        closes = df["Close"]
        volumes = df["Volume"]

        if indicators and len(closes) >= 20:
            ma5 = compute_ma(closes, 5)
            ma10 = compute_ma(closes, 10)
            ma20 = compute_ma(closes, 20)
            ma60 = compute_ma(closes, 60) if len(closes) >= 60 else [None] * len(closes)
            rsi14 = compute_rsi(closes, 14)
            bb_upper, bb_mid, bb_lower = compute_bollinger(closes, 20, 2.0)
            macd_dif, macd_dea, macd_bar = compute_macd(closes, 12, 26, 9)
        else:
            ma5 = ma10 = ma20 = ma60 = [None] * len(closes)
            rsi14 = [None] * len(closes)
            bb_upper = bb_mid = bb_lower = [None] * len(closes)
            macd_dif = macd_dea = macd_bar = [None] * len(closes)

        for i in range(len(df)):
            record = {
                "date": dates.iloc[i] if hasattr(dates, "iloc") else dates[i],
                "open": round(float(df["Open"].iloc[i]), 2),
                "high": round(float(df["High"].iloc[i]), 2),
                "low": round(float(df["Low"].iloc[i]), 2),
                "close": round(float(closes.iloc[i]), 2),
                "volume": int(volumes.iloc[i]),
            }
            record.update({
                "ma5": ma5[i], "ma10": ma10[i], "ma20": ma20[i], "ma60": ma60[i],
                "rsi14": rsi14[i],
                "bb_upper": bb_upper[i], "bb_mid": bb_mid[i], "bb_lower": bb_lower[i],
                "macd_dif": macd_dif[i], "macd_dea": macd_dea[i], "macd_bar": macd_bar[i],
            })
            result["data"].append(record)

        result["latest_indicators"] = {
            "ma5": ma5[-1] if ma5 else None,
            "ma10": ma10[-1] if ma10 else None,
            "ma20": ma20[-1] if ma20 else None,
            "ma60": ma60[-1] if ma60 else None,
            "rsi14": rsi14[-1] if rsi14 else None,
            "bb_upper": bb_upper[-1] if bb_upper else None,
            "bb_mid": bb_mid[-1] if bb_mid else None,
            "bb_lower": bb_lower[-1] if bb_lower else None,
            "macd_dif": macd_dif[-1] if macd_dif else None,
            "macd_dea": macd_dea[-1] if macd_dea else None,
            "macd_bar": macd_bar[-1] if macd_bar else None,
        }

        return result
    except HTTPException:
        raise
    except yf_err.YFRateLimitError:
        raise HTTPException(status_code=429, detail="Rate limited by Yahoo Finance. Please wait.")
    except Exception as e:
        logger.error(f"Error fetching history for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/batch")
async def batch_query(symbols: str = Query(..., description="comma-separated symbols")):
    sym_list = [s.strip() for s in symbols.split(",") if s.strip()]
    if len(sym_list) > 10:
        raise HTTPException(status_code=400, detail="max 10 symbols")
    results = []
    for sym in sym_list:
        try:
            ticker = yf.Ticker(sym)
            info = ticker.info
            price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("navPrice")
            prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose")
            if price is None:
                h = ticker.history(period="1d")
                if not h.empty:
                    price = round(float(h["Close"].iloc[-1]), 2)
            change = price - prev_close if (price and prev_close) else 0
            change_pct = (change / prev_close * 100) if (price and prev_close) else 0
            results.append({
                "symbol": sym.upper(),
                "name": info.get("shortName") or info.get("longName") or sym,
                "price": price,
                "change": round(change, 2) if price else None,
                "change_percent": round(change_pct, 2) if price else None,
            })
        except Exception as e:
            results.append({"symbol": sym.upper(), "name": sym, "price": None, "change": None, "change_percent": None, "error": str(e)})
    return {"results": results}

@app.get("/api/fund/{symbol}")
async def get_fund_info(symbol: str):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return {
            "symbol": symbol.upper(),
            "name": info.get("longName") or info.get("shortName"),
            "category": info.get("category"),
            "fund_family": info.get("fundFamily"),
            "fund_type": info.get("quoteType"),
            "nav_price": info.get("navPrice") or info.get("currentPrice"),
            "previous_close": info.get("previousClose") or info.get("regularMarketPreviousClose"),
            "ytd_return": info.get("ytdReturn"),
            "three_year_return": info.get("threeYearAverageReturn"),
            "five_year_return": info.get("fiveYearAverageReturn"),
            "expense_ratio": info.get("annualReportExpenseRatio") or info.get("expenseRatio"),
            "total_assets": info.get("totalAssets"),
        }
    except Exception as e:
        logger.error(f"Error fetching fund {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/market_overview")
async def market_overview():
    indices = ["^GSPC", "^DJI", "^IXIC", "^HSI", "000001.SS", "399001.SZ"]
    results = []
    for idx in indices:
        try:
            ticker = yf.Ticker(idx)
            info = ticker.info
            price = info.get("regularMarketPrice") or info.get("currentPrice")
            prev = info.get("previousClose") or info.get("regularMarketPreviousClose")
            change = price - prev if (price and prev) else None
            change_pct = (change / prev * 100) if (price and prev and prev != 0) else None
            results.append({
                "symbol": idx,
                "name": info.get("shortName", idx),
                "price": price,
                "change": round(change, 2) if change else None,
                "change_percent": round(change_pct, 2) if change_pct else None,
            })
        except Exception as e:
            results.append({"symbol": idx, "name": idx, "error": str(e)})
    return {"indices": results}


if __name__ == "__main__":
    import uvicorn
    port = 9200
    logger.info(f"Starting StockFund-Analyzer API v2.0 on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)