# StockFund Analyzer v3.0 — 股市基金实时分析平台

## 技术架构

| 层级 | 技术栈 | 文件 |
|------|--------|------|
| 后端 API | FastAPI + Uvicorn (Python 3.8+) | `backend/main.py` |
| 数据源 | yfinance (Yahoo Finance 实时行情) | — |
| 前端 | React 18 + Recharts 2.12 + Babel JSX | `frontend/index.html` |
| CDN | jsdelivr (React/Recharts/Babel/Tailwind) | — |
| Skill | OpenCode Skill | `.opencode/skills/stock-analyzer/SKILL.md` |

## 快速启动

```powershell
# 1. 启动后端（双击 backend\run.bat 也可）
cd stockfund-analyzer\backend
pip install -r requirements.txt
python main.py    # → http://localhost:9200

# 2. 浏览器打开 frontend/index.html
```

或双击 `start.ps1` 一键启动。

## v3.0 新功能

| 功能 | 说明 |
|------|------|
| **K线图 (OHLC)** | 切换 Area/Candle 模式，自定义 SVG 渲染 |
| **MACD 指标** | DIF/DEA 线 + 彩色柱状图 (12,26,9) |
| **自选股持久化** | localStorage 存储，刷新不丢失 |
| **CSV 导出** | 一键下载历史数据为 CSV 格式 |
| **看盘工具提示** | 鼠标悬浮显示 O/H/L/C + 所有技术指标值 |

### 后端 API (7 个端点)
- `/api/health` — 健康检查
- `/api/search?q=` — 搜索代码/名称 (35+ 内置热门标的)
- `/api/stock/{symbol}` — 实时行情 (价格/涨跌幅/OHLCV/PE/市值/股息率/52周高低)
- `/api/history/{symbol}?period=&interval=&indicators=` — 历史 OHLCV + **MA5/10/20/60 + RSI(14) + 布林带 + MACD**
- `/api/batch?symbols=` — 批量查询 (最多10只)
- `/api/fund/{symbol}` — 基金分析 (NAV/费率/年化收益/总资产)
- `/api/market_overview` — 六大指数行情 (标普/道指/纳指/恒生/上证/深证)

### 前端面板
- **顶部指数条**：实时滚动展示 6 大指数涨跌
- **自选列表**：侧边栏持久化存储，支持删除单只
- **搜索补全**：输入即时匹配，Enter 直接搜索
- **8 项关键指标卡**：开盘/最高/最低/成交量/市值/PE/股息率/52周范围
- **7 档时间周期**：1天 ~ 2年
- **价格/OHLC 图**：面积图 ↔ K 线图一键切换，叠加 MA/布林带
- **成交量图**：同步联动
- **MACD 面板**：DIF + DEA + 柱状线
- **RSI 面板**：超买(70)/超卖(30)参考线
- **30 秒自动刷新**：倒计时显示
- **导出 CSV**：一键下载

## 支持的交易代码

| 市场 | 格式 | 示例 |
|------|------|------|
| 美股 | TICKER | `AAPL`, `TSLA`, `NVDA` |
| 沪A | TICKER.SS | `600519.SS` (茅台) |
| 深A | TICKER.SZ | `000001.SZ` (平安银行) |
| 港股 | TICKER.HK | `0700.HK` (腾讯) |
| ETF | TICKER | `SPY`, `QQQ`, `VOO` |
| 指数 | ^TICKER | `^GSPC` (标普500) |