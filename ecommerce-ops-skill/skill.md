# Ecommerce Ops Skill

Multi-platform ecommerce operations strategy Skill — integrated Amazon / Taobao / JD / Pinduoduo / Douyin sales ranking reading, competitor analysis, cross-platform comparison, and full-cycle operational strategy.

## Activation

This skill activates when:
- User asks about hot-selling products or sales rankings on any ecommerce platform
- User needs competitor analysis, product selection advice, or operational strategy
- User asks about platform-specific advertising tools (直通车/京准通/多多搜索/千川)
- User wants to benchmark pricing, listing optimization, or live-commerce performance
- User inquires about cross-platform ecommerce operations best practices

## Core Principles

### 1. Sales Ranking Data — Platform-Specific Methods

| Platform | Method | Key Metric |
|----------|--------|------------|
| Amazon | `get_bestsellers()` — BSR hourly rank | Sales velocity from BSR range |
| Taobao/Tmall | `search_products()` — search results | 月销量 display |
| JD.com | `search_products()` / `get_bestsellers()` | 评论数 + 自营vs.POP |
| Pinduoduo | `search_products()` + snapshot tracking | 已拼件数差值→日销 |
| Douyin | GPM/Opm models + funnel analysis | GPM × PV = GMV |

### 2. Sales Estimation by Platform

| Platform | Method | Confidence |
|----------|--------|:---:|
| Amazon | BSR range → daily units table | 85% (BSR<100) |
| Taobao | Monthly sales display ÷ 30 | 70% |
| JD | Comment count ÷ days ÷ 2.5% | 40% |
| Pinduoduo | Snapshot difference: Δsold / hours × 24 | 60% (4+ snaps) |
| Douyin | GPM × daily impressions | 50% |

### 3. Advertising Tools by Platform

| Platform | Search Ads | Display/Recommend | Content/Live | Performance |
|----------|-----------|-------------------|-------------|-------------|
| Amazon | SP | SB + SD | Posts + Live | Brand metrics |
| Taobao | 直通车 | 引力魔方 | 淘宝直播+逛逛 | 万相台 |
| JD | 京东快车 | 购物触点 | 京东直播+发现 | DMP |
| Pinduoduo | 多多搜索 | 多多场景 | 多多视频+直播 | 全站推广 |
| Douyin | 千川搜索 | 千川信息流 | 直播+短视频 | 千川全域 |

### 4. Live Commerce Metrics (Douyin)

- **GPM** (千次观看成交额): Core metric — GMV ÷ PV × 1000
- **Opm** (每分钟订单量): Orders ÷ live duration minutes
- **UV Value**: GMV ÷ unique viewers
- **Health Check**: Auto-diagnose 5 dimensions (GPM/Opm/Stay/Interaction/CVR)

## v0.3 Platform Support

| Platform | Ranking | Detail | Estimate | Strategy |
|----------|:---:|:---:|:---:|:---:|
| Amazon (10 domains) | Y | Y | Y | Y |
| Taobao/Tmall | Y | — | Y | Y |
| JD.com | Y | — | Y | Y |
| Pinduoduo | Y | — | Y | Y |
| Douyin E-commerce | Y | — | Y | Y |
| Xiaohongshu | — | — | — | — |

## References

- Jungle Scout / Keepa / Helium 10 (Amazon)
- 生意参谋 (Taobao) / 京东商智 (JD)
- 多多参谋 (Pinduoduo) / 抖音罗盘 (Douyin)
- 蝉妈妈 / 飞瓜数据 (Douyin data platforms)