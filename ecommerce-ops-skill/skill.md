# Ecommerce Ops Skill

多平台电商运营策略 Skill —— 集成 Amazon / 淘宝 / 京东 / 拼多多 / 抖音 / 小红书六大平台的销量榜单读取与竞品分析能力，提供选品→上架→流量→转化→复购→复盘的全链路运营策略建议。

## Activation

This skill activates when:
- User asks about hot-selling products or sales rankings on any ecommerce platform
- User needs competitor analysis, product selection advice, or operational strategy
- User asks about Amazon BSR, sales estimation, or ranking mechanisms
- User wants to benchmark pricing, listing optimization, or PPC strategy
- User inquires about cross-platform ecommerce operations best practices

## Core Principles

### 1. Sales Ranking Data — Read, Never Guess

When the user needs sales ranking data:

- **Amazon BSR**: Use `DataFetcher.get_bestsellers()` to pull hourly-updated Best Sellers list. BSR reflects recent sales velocity (not total lifetime sales). Lower BSR = stronger current sales momentum.
- **Sales Estimation**: BSR is logarithmic to actual sales. `AmazonSalesEstimator` maps BSR ranges to daily-unit estimates. BSR < 100 = strong (>10+ daily units). BSR > 100k = slow-moving (<1 unit/day).
- **Product Detail**: Use `AmazonClient.get_product_detail()` for on-page data: title, price, rating, review count, availability, features, images, seller info.

### 2. Data-Driven Strategy

The `StrategyEngine` covers six phases of ecommerce operations:

| Phase | Focus | Key Decisions |
|-------|-------|---------------|
| **Selection** | Which product? | Category BSR analysis, competition density, price-band gap, margin calculation |
| **Listing** | How to present? | Title keyword formula, bullet points, A+/EBC content, image/video optimization |
| **Traffic** | How to get visits? | SP/SB/SD PPC pyramid, keyword ranking strategy, external traffic channels |
| **Conversion** | How to close? | Price anchoring, coupon/promotion, review/Q&A seeding, Prime badge |
| **Retention** | How to repeat? | Subscribe & Save, brand followers, post-purchase email, product line expansion |
| **Review** | How to iterate? | Weekly BSR trend, PPC audit, competitor monitoring, inventory forecasting |

### 3. Competitive Analysis Flow

```
1. Pull Best Seller list for target category
2. Parse Top 5-20 ranking items (price, rating, review count, brand)
3. Calculate category benchmarks (avg price, avg reviews, brand concentration)
4. Identify gaps: price-band white space, underserved needs (from negative reviews)
5. StrategyEngine.analyze_competitor_from_bestseller() for automated analysis
```

### 4. Budget-Aware Recommendations

Strategy engine tailors advice to three budget levels:

- **Low** ($300-$600/month PPC): Focus on long-tail keywords, organic SEO, Amazon Posts
- **Medium** ($900-$2400/month PPC): Balanced SP + SB, category targeting, LD campaigns
- **High** ($3000-$9000/month PPC): Aggressive SP/SB/SD, 7DD, influencer + external traffic

## v0.1 Supported Platforms

| Platform | Sales Ranking | Product Detail | Sales Estimate | Strategy |
|----------|:---:|:---:|:---:|:---:|
| Amazon (10 domains) | Y | Y | Y | Y |
| Taobao/Tmall | — | — | — | — |
| JD.com | — | — | — | — |
| Pinduoduo | — | — | — | — |
| Douyin E-commerce | — | — | — | — |
| Xiaohongshu | — | — | — | — |

## References

- Amazon BSR explained: [Amazon Seller Central - Best Seller Rank](https://sellercentral.amazon.com/help/hub/reference/G201648110)
- Jungle Scout: [Amazon Sales Estimator](https://www.junglescout.com/estimator/)
- Keepa: [Amazon Price History & BSR Tracking](https://keepa.com/)
- Helium 10: [Amazon Product Research Suite](https://www.helium10.com/)