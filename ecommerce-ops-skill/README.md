# Ecommerce Ops Skill

Multi-platform ecommerce operations strategy tool — read sales rankings from Amazon, Taobao, Tmall, JD.com, analyze competitive landscape, and get actionable platform-specific operational advice.

## Platforms

| Platform | Sales Ranking | Product Detail | Sales Estimate | Strategy |
|----------|:---:|:---:|:---:|:---:|
| Amazon (10 domains) | Y | Y | Y | Y |
| Taobao / Tmall | Y | — | Y | Y |
| JD.com | Y | — | Y | Y |
| Pinduoduo | — | — | — | v0.3 |
| Douyin E-commerce | — | — | — | v0.3 |
| Xiaohongshu (RED) | — | — | — | v0.4 |

## Installation

```bash
pip install ecommerce-ops-skill
```

Or from source:

```bash
git clone https://github.com/srfnhgsgst-del/skill.git
cd skill/ecommerce-ops-skill
pip install -e .
```

## Quick Start

### Amazon
```python
from ecommerce_ops_skill import DataFetcher, Platform, AmazonDomain

fetcher = DataFetcher(amazon_domain=AmazonDomain.US)
bl = fetcher.get_bestsellers(Platform.AMAZON, category_id="zgbs/kitchen", limit=20)
for item in bl.items:
    print(f"#{item.rank}: {item.title} - ${item.price}")
fetcher.close()
```

### Taobao / JD Cross-platform Search
```python
fetcher = DataFetcher()

# Taobao search by keyword
items = fetcher.search_products(Platform.TAOBAO, keyword="连衣裙", limit=20)
for item in items:
    print(f"#{item.rank}: {item.title} - CNY {item.price} | 月销{item.review_count} | {item.brand}")

# JD search by keyword
items = fetcher.search_products(Platform.JD, keyword="手机", sort="sales", limit=20)
for item in items:
    label = "[京东自营]" if item.is_bestseller else "[POP]"
    print(f"#{item.rank} {label}: {item.title} - CNY {item.price}")

# Cross-platform comparison
results = fetcher.cross_platform_search("充电宝", platforms=[Platform.TAOBAO, Platform.JD])
for platform_name, items_list in results.items():
    print(f"{platform_name}: {len(items_list)} results")
fetcher.close()
```

## Modules

| Module | Description |
|--------|-------------|
| `platform.py` | Platform enums (Platform / AmazonDomain / RankingPeriod / StrategyPhase) |
| `models.py` | Data models (RankingItem / ProductDetail / BestSellerList / SalesEstimate / KeywordData / CompetitorSnapshot) |
| `rank_parser.py` | Universal HTML ranking parser: Amazon/淘宝/京东 Bestseller to structured data |
| `amazon.py` | Amazon BSR reader + sales estimator (BSR/Review velocity models) |
| `taobao.py` | Taobao/Tmall search parser + 月销量 estimator + shop competitiveness analysis |
| `jd.py` | JD search parser + 京东自营vs.POP detection + bestseller list + comment-based estimator |
| `data_fetcher.py` | Unified data entry, cross-platform routing, `cross_platform_search()` |
| `strategy_engine.py` | Cross-platform ops strategy: Selection -> Listing -> Traffic -> Conversion -> Retention -> Review |

## Strategy Engine

```python
from ecommerce_ops_skill import StrategyEngine, Platform

# Amazon strategy
engine = StrategyEngine(platform=Platform.AMAZON)
phases = engine.full_strategy(category="Kitchen", market="US", budget="medium")

# Taobao strategy
engine = StrategyEngine(platform=Platform.TAOBAO)
phases = engine.full_strategy()

# JD strategy
engine = StrategyEngine(platform=Platform.JD)
phases = engine.full_strategy()
```

## License

MIT