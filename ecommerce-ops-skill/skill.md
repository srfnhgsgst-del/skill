# Ecommerce Ops Skill

Multi-platform ecommerce operations strategy Skill — integrated Amazon / Taobao / Tmall / JD.com sales ranking reading, competitor analysis, cross-platform comparison, and full-cycle operational strategy (Selection -> Listing -> Traffic -> Conversion -> Retention -> Review).

## Activation

This skill activates when:
- User asks about hot-selling products or sales rankings on any ecommerce platform
- User needs competitor analysis, product selection advice, or operational strategy
- User asks about Amazon BSR, Taobao search ranking, JD.com self-operated vs POP
- User wants to benchmark pricing, listing optimization, or PPC strategy across platforms
- User inquires about cross-platform ecommerce operations best practices
- User asks about 淘宝直通车, 京东京准通, 引力魔方, 万相台, or other platform advertising tools

## Core Principles

### 1. Sales Ranking Data — Platform-Specific Methods

- **Amazon BSR**: `DataFetcher.get_bestsellers(Platform.AMAZON)` — hourly-updated Best Sellers list. BSR logarithmic to actual sales velocity.
- **Taobao/Tmall**: `DataFetcher.search_products(Platform.TAOBAO, keyword)` — search results parse. Monthly sales displayed as "月销X件" or "X万+".
- **JD.com**: `DataFetcher.search_products(Platform.JD, keyword)` or `get_bestsellers(Platform.JD)` — search results + JD排行榜. Self-operated (京东自营) vs POP seller identification.

### 2. Sales Estimation by Platform

| Platform | Method | Confidence |
|----------|--------|:---:|
| Amazon | BSR range → daily units table | 85% (BSR<100), 40% (BSR>10k) |
| Taobao | Displayed monthly sales ÷ 30 | 70% |
| JD | Comment count ÷ days ÷ 2.5% comment rate | 40% |

### 3. Strategy by Platform

| Phase | Amazon | Taobao/Tmall | JD |
|-------|--------|-------------|-----|
| **Traffic** | SP/SB/SD PPC | 直通车/引力魔方/万相台/直播/逛逛 | 京准通(快车+触点)/秒杀/直播 |
| **Content** | Amazon Posts | 逛逛短视频+图文 | 京东发现+短视频 |
| **Live** | Amazon Live | 淘宝直播 | 京东直播 |
| **External** | Social + Influencer | 抖音/小红书种草 | 微信小程序+社交媒体 |
| **Membership** | Subscribe & Save | 店铺粉丝群+会员 | Plus会员+店铺会员 |

### 4. Cross-Platform Competitive Analysis

```python
fetcher = DataFetcher()
results = fetcher.cross_platform_search("蓝牙耳机", platforms=[Platform.TAOBAO, Platform.JD, Platform.AMAZON])

engine = StrategyEngine()
comparison = engine.cross_platform_compare(results)
```

## v0.2 Platform Support

| Platform | Sales Ranking | Product Detail | Sales Estimate | Strategy |
|----------|:---:|:---:|:---:|:---:|
| Amazon (10 domains) | Y | Y | Y | Y |
| Taobao/Tmall | Y | — | Y | Y |
| JD.com | Y | — | Y | Y |
| Pinduoduo | — | — | — | — |
| Douyin E-commerce | — | — | — | — |
| Xiaohongshu | — | — | — | — |

## References

- Amazon BSR: [Seller Central Help](https://sellercentral.amazon.com/help/hub/reference/G201648110)
- Jungle Scout: [Amazon Sales Estimator](https://www.junglescout.com/estimator/)
- Keepa: [Amazon Price & BSR Tracking](https://keepa.com/)
- Helium 10: [Amazon Product Research Suite](https://www.helium10.com/)
- 淘宝生意参谋: [商家数据中心](https://sycm.taobao.com/)
- 京东商智: [京东商家数据平台](https://sz.jd.com/)
- 蝉妈妈: [抖音数据分析平台](https://www.chanmama.com/)