# Ecommerce Ops Skill

Multi-platform ecommerce operations strategy tool - read sales rankings from Amazon, analyze BSR trends, estimate competitor sales, and get actionable cross-platform operational advice.

## Platforms (v0.1)

| Platform | Status |
|----------|--------|
| Amazon (US/JP/UK/DE/FR/IT/ES/CA/IN/AU) | Ready |
| Taobao / Tmall | v0.2 |
| JD.com | v0.2 |
| Pinduoduo | v0.3 |
| Douyin E-commerce | v0.3 |
| Xiaohongshu (RED) | v0.4 |

## Installation

```bash
pip install ecommerce-ops-skill
```

Or from source:

```bash
git clone https://github.com/yourname/ecommerce-ops-skill.git
cd ecommerce-ops-skill
pip install -e .
```

## Quick Start

```python
from ecommerce_ops_skill import DataFetcher, AmazonDomain, Platform

fetcher = DataFetcher(amazon_domain=AmazonDomain.US)

# Get Amazon Best Sellers
bl = fetcher.get_bestsellers(Platform.AMAZON, category_id="zgbs/kitchen", limit=20)
for item in bl.items:
    print(f"#{item.rank}: {item.title} - ${item.price}")

# Get product details
detail = fetcher.get_product_detail(Platform.AMAZON, "B0EXAMPLE1")
print(f"BSR: {detail.bsr}, Rating: {detail.rating}")

# Estimate sales from BSR
est = fetcher.estimate_sales(Platform.AMAZON, bsr=500, product_id="B0EXAMPLE1")
print(f"Daily: {est.estimated_daily_sales}, Monthly: {est.estimated_monthly_sales}")

fetcher.close()
```

## Modules

| Module | Description |
|--------|-------------|
| `platform.py` | Platform enums (Platform / AmazonDomain / RankingPeriod / StrategyPhase) |
| `models.py` | Data models (RankingItem / ProductDetail / BestSellerList / SalesEstimate / CompetitorSnapshot) |
| `rank_parser.py` | Universal HTML ranking parser, bestseller list to structured data |
| `amazon.py` | Amazon BSR reader + sales estimator with BSR/Review velocity models |
| `data_fetcher.py` | Unified data entry, routes to platform-specific modules |
| `strategy_engine.py` | Cross-platform ops strategy: Selection -> Listing -> Traffic -> Conversion -> Retention -> Review |

## Strategy Engine

```python
from ecommerce_ops_skill import StrategyEngine, Platform

engine = StrategyEngine(platform=Platform.AMAZON)
phases = engine.full_strategy(category="Kitchen", market="US", budget="medium")

for p in phases:
    print(f"[{p['phase']}] {p['title']}")
    for step in p['steps']:
        print(f"  - {step}")
```

## License

MIT