# Ecommerce Ops Skill

Multi-platform ecommerce operations strategy Skill — integrated Amazon / Taobao / JD / Pinduoduo / Douyin / Xiaohongshu sales ranking reading, competitor analysis, cross-platform comparison, full-cycle operational strategy, data export, and GMV dashboard.

## Activation

This skill activates when:
- User asks about hot-selling products or sales rankings on any ecommerce platform
- User needs competitor analysis, product selection advice, or operational strategy
- User asks about platform-specific advertising tools (直通车/京准通/多多搜索/千川/薯条/聚光)
- User wants to benchmark pricing, listing optimization, or live-commerce performance
- User inquires about cross-platform ecommerce operations best practices
- User needs data export (CSV/JSON), daily operations reports, or GMV dashboards
- User asks about KOL/KOC达人 selection, content marketing ROI, or brand campaign modeling

## Core Principles

### 1. Sales Ranking Data — Platform-Specific Methods

| Platform | Method | Key Metric |
|----------|--------|------------|
| Amazon | `get_bestsellers()` — BSR hourly rank | Sales velocity from BSR range |
| Taobao/Tmall | `search_products()` — search results | 月销量 display |
| JD.com | `search_products()` / `get_bestsellers()` | 评论数 + 自营vs.POP |
| Pinduoduo | `search_products()` + snapshot tracking | 已拼件数差值→日销 |
| Douyin | GPM/Opm models + funnel analysis | GPM × PV = GMV |
| Xiaohongshu | `analyze_note_performance()` + trend search | 互动率/爆文评分/趋势监测 |

### 2. Sales Estimation by Platform

| Platform | Method | Confidence |
|----------|--------|:---:|
| Amazon | BSR range → daily units table | 85% (BSR<100) |
| Taobao | Monthly sales display ÷ 30 | 70% |
| JD | Comment count ÷ days ÷ 2.5% | 40% |
| Pinduoduo | Snapshot difference: Δsold / hours × 24 | 60% (4+ snaps) |
| Douyin | GPM × daily impressions | 50% |
| Xiaohongshu | Note views × CTR × CVR × price | 45% (brand campaign) |

### 3. Advertising Tools by Platform

| Platform | Search Ads | Display/Recommend | Content/Live | Performance |
|----------|-----------|-------------------|-------------|-------------|
| Amazon | SP | SB + SD | Posts + Live | Brand metrics |
| Taobao | 直通车 | 引力魔方 | 淘宝直播+逛逛 | 万相台 |
| JD | 京东快车 | 购物触点 | 京东直播+发现 | DMP |
| Pinduoduo | 多多搜索 | 多多场景 | 多多视频+直播 | 全站推广 |
| Douyin | 千川搜索 | 千川信息流 | 直播+短视频 | 千川全域 |
| Xiaohongshu | 搜索广告 | 信息流广告 | 薯条+笔记+直播 | 聚光平台 |

### 4. Live Commerce Metrics (Douyin)

- **GPM** (千次观看成交额): Core metric — GMV ÷ PV × 1000
- **Opm** (每分钟订单量): Orders ÷ live duration minutes
- **UV Value**: GMV ÷ unique viewers
- **Health Check**: Auto-diagnose 5 dimensions (GPM/Opm/Stay/Interaction/CVR)

### 5. Content Commerce Metrics (Xiaohongshu)

- **互动率**: (赞+藏+评+分享) ÷ 曝光量 — 核心内容质量指标
- **爆文评分**: 互动率×10 + 传播率×50 + 收藏率×5 → S/A/B/C 四档
- **达人ROI**: 估计GMV ÷ 合作费用 → excellent/good/acceptable/poor
- **品牌投放模型**: 预算→KOL矩阵→曝光→互动→订单→GMV→ROI
- **内容ROI**: 笔记产出收入 ÷ (制作成本+达人费用)
- **趋势检测**: 关键词笔记数 + 品类增长率 → 竞争度 + 趋势判断

## Data Export & Reporting

| Feature | Format | Content |
|---------|--------|---------|
| CSV Export | `.csv` (BOM) | 18 columns: rank, platform, ASIN, title, price, rating, reviews, brand, category, flags |
| JSON Export | `.json` | Structured item list with all fields |
| Daily Report | plain text | Multi-platform summary: avg price, flagship ratio, Top 3, sales estimates |
| GMV Dashboard | dict/JSON | Total GMV, orders, by-platform, Top 5, 5-tier distribution (S/A/B/C/D) |
| Comparison Table | table text | Cross-platform: items, avg price, price range, bestseller% |

## v0.4 Platform Support

| Platform | Ranking | Detail | Estimate | Strategy | Export |
|----------|:---:|:---:|:---:|:---:|:---:|
| Amazon (10 domains) | Y | Y | Y | Y | Y |
| Taobao/Tmall | Y | — | Y | Y | Y |
| JD.com | Y | — | Y | Y | Y |
| Pinduoduo | Y | — | Y | Y | Y |
| Douyin E-commerce | Y | — | Y | Y | Y |
| Xiaohongshu | — | Y | Y | Y | Y |

## References

- Jungle Scout / Keepa / Helium 10 (Amazon)
- 生意参谋 (Taobao) / 京东商智 (JD)
- 多多参谋 (Pinduoduo) / 抖音罗盘 (Douyin)
- 千瓜数据 / 新红数据 (Xiaohongshu data platforms)
- 蝉妈妈 / 飞瓜数据 (Douyin data platforms)