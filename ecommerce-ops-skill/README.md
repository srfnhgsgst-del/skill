# Ecommerce Ops Skill

Multi-platform ecommerce operations strategy tool — Amazon / Taobao / JD / Pinduoduo / Douyin sales rankings, competitor analysis, and full-cycle operational strategies.

## Platforms

| Platform | Ranking | Detail | Estimate | Strategy |
|----------|:---:|:---:|:---:|:---:|
| Amazon (10 domains) | Y | Y | Y | Y |
| Taobao / Tmall | Y | — | Y | Y |
| JD.com | Y | — | Y | Y |
| Pinduoduo | Y | — | Y | Y |
| Douyin E-commerce | Y | — | Y | Y |
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

### Pinduoduo
```python
from ecommerce_ops_skill import DataFetcher, Platform

fetcher = DataFetcher()

# Search products
items = fetcher.search_products(Platform.PINDUODUO, keyword="T恤", limit=20)
for item in items:
    label = "[旗舰店]" if item.is_bestseller else "[个人店]"
    print(f"#{item.rank} {label} {item.title} - ￥{item.price} | 已拼{item.review_count}件")

# Price competition analysis
comp = fetcher.analyze_pdd_price_competition("充电宝")
print(f"Competition pressure: {comp['price_competition_pressure']}")

# Sales snapshot tracking
fetcher.take_pdd_sales_snapshot("蓝牙耳机", limit=20)
# ... wait some time ...
fetcher.take_pdd_sales_snapshot("蓝牙耳机", limit=20)
est = fetcher.estimate_sales(Platform.PINDUODUO, goods_id="pdd-蓝牙耳机-1")
print(f"Daily: {est.estimated_daily_sales}, Monthly: {est.estimated_monthly_sales}")
fetcher.close()
```

### Douyin E-commerce
```python
from ecommerce_ops_skill import DouyinClient, DouyinLiveMetrics

client = DouyinClient()

# Estimate live-stream GMV by GPM
live = client.estimate_live_gmv(avg_viewers=5000, duration_minutes=120, gpm=800)
print(f"Estimated GMV: CNY {live['estimated_gmv_cny']:,.0f}")
print(f"GPM: {live['gpm']}, OPM: {live['opm']}")

# Short video conversion funnel
funnel = client.analyze_short_video(
    views=100000, completion_rate=0.45, interaction_rate=0.05,
    product_click_rate=0.08, conversion_rate=0.03,
)
print(f"Tier: {funnel['content_tier']}, GMV: CNY {funnel['gmv_cny']:,.0f}")

# Live room health check
health = DouyinLiveMetrics.live_health_check(
    gpm=800, opm=2.5, avg_stay_minutes=2.0,
    interaction_rate=0.04, conversion_rate=0.03,
)
print(f"Live status: {health['status']}")
client.close()
```

## Modules

| Module | Description |
|--------|-------------|
| `platform.py` | Platform/AmazonDomain enums |
| `models.py` | RankingItem / ProductDetail / SalesEstimate / CompetitorSnapshot |
| `rank_parser.py` | HTML parser: Amazon/淘宝/京东/拼多多 search results |
| `amazon.py` | Amazon BSR + 10-domain support + BSR/Review velocity estimator |
| `taobao.py` | Taobao/Tmall search + 月销量 estimator + DSR shop ranking |
| `jd.py` | JD search + self-operated detection + 排行榜 + comment estimator |
| `pinduoduo.py` | PDD search + snapshot-diff estimator + price competition analysis |
| `douyin.py` | Douyin live GPM/Opm + video funnel + product card + traffic source analysis |
| `data_fetcher.py` | Unified entry + cross-platform search + snapshot/workflow APIs |
| `strategy_engine.py` | 6-phase strategy: Selection/Listing/Traffic/Conversion/Retention for 5 platforms |

## Strategy Engine

```python
from ecommerce_ops_skill import StrategyEngine, Platform

# PDD strategy
phases = StrategyEngine(platform=Platform.PINDUODUO).full_strategy()

# Douyin strategy
phases = StrategyEngine(platform=Platform.DOUYIN).full_strategy()
```

## License

MIT