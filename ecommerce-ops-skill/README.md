# Ecommerce Ops Skill

6-platform ecommerce operations strategy tool — Amazon / Taobao / JD / Pinduoduo / Douyin / Xiaohongshu rankings, competitor SWOT analysis, price elasticity modeling, seasonal prediction, data export.

## Platforms (v0.4 — All 6 Complete)

| Platform | Ranking | Estimate | SWOT | Strategy |
|----------|:---:|:---:|:---:|:---:|
| Amazon (10 domains) | Y | BSR model | Y | 6-phase |
| Taobao / Tmall | Y | 月销量 | Y | 6-phase |
| JD.com | Y | Comment model | Y | 6-phase |
| Pinduoduo | Y | Snapshot-diff | Y | 6-phase |
| Douyin E-commerce | Y | GPM model | Y | 6-phase |
| Xiaohongshu | Y | Content ROI | Y | 6-phase |

## Installation

```bash
pip install ecommerce-ops-skill
# or from source:
git clone https://github.com/srfnhgsgst-del/skill.git
cd skill/ecommerce-ops-skill && pip install -e .
```

## Quick Start

### Analyze XHS Note Performance
```python
from ecommerce_ops_skill import XiaohongshuClient
client = XiaohongshuClient()
note = client.analyze_note_performance(
    views=50000, likes=2500, collects=3000, comments=500, shares=200,
    product_click_rate=0.08, conversion_rate=0.03,
)
print(f"Tier: {note['content_tier']}, GMV: CNY {note['conversion_funnel']['gmv_cny']:,.0f}")
```

### Cross-Platform SWOT + Price Elasticity
```python
from ecommerce_ops_skill import DataFetcher, StrategyEngine, DataExporter, Platform

fetcher = DataFetcher()
# Cross-platform search
results = fetcher.cross_platform_search("充电宝")
# SWOT auto-generation
engine = StrategyEngine()
swot = engine.generate_cross_platform_swot(results)
# Price elasticity
items = fetcher.search_products(Platform.PINDUODUO, "T恤", limit=50)
bands = engine.analyze_price_elasticity(items)
print(f"Sweet spot: {bands['sweet_spot']}")
# Seasonal prediction
season = engine.predict_seasonal_trend("clothing")
print(f"Next peak: {season['next_peak']}")
# Export
csv = DataExporter.to_csv(items)
report = DataExporter.generate_daily_report(results)
fetcher.close()
```

## Modules

| Module | New in v0.4 |
|--------|-------------|
| `xiaohongshu.py` | Note performance / KOL profiling / Brand campaign ROI / Content trends |
| `export_utils.py` | CSV/JSON export / Daily report / GMV dashboard / Cross-platform comparison table |
| `strategy_engine.py` | +Cross-platform SWOT / +Price elasticity / +Seasonal prediction / +Full matrix / +XHS strategy |

## License

MIT