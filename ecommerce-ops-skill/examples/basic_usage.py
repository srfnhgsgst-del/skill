"""
Ecommerce Ops Skill - Amazon Best Sellers Rank 快速上手

演示如何使用 DataFetcher 获取 Amazon 销量榜单数据
"""
from ecommerce_ops_skill import (
    DataFetcher,
    AmazonDomain,
    Platform,
    RankParser,
    AmazonSalesEstimator,
    StrategyEngine,
)


def print_banner(text: str):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def demo_rank_parser():
    print_banner("1. HTML Parse - RankParser")
    sample_html = """
    <div class="p13n-gridRow" data-asin="B0EXAMPLE1">
        <div class="p13n-sc-truncate-desktop-type2">Sample Product</div>
        <span class="p13n-sc-price">$24.99</span>
        <i class="a-icon-alt">4.5 out of 5 stars</i>
        <span class="a-size-small">1,234</span>
    </div>
    """
    items = RankParser.parse_amazon_bestsellers(sample_html, AmazonDomain.US, "Test")
    print(RankParser.format_bestseller_table(items))


def demo_sales_estimator():
    print_banner("2. Sales Estimate - AmazonSalesEstimator")
    estimator = AmazonSalesEstimator()

    estimator.add_bsr_snapshot("B0TEST", 800, "Kitchen")
    estimator.add_bsr_snapshot("B0TEST", 650, "Kitchen")
    estimator.add_bsr_snapshot("B0TEST", 500, "Kitchen")

    est = estimator.estimate_daily_sales("B0TEST", 500)
    print(f"  ASIN: {est.asin}")
    print(f"  Daily sales: {est.estimated_daily_sales}")
    print(f"  Monthly sales: {est.estimated_monthly_sales}")
    print(f"  Trend: {est.sales_trend}")
    print(f"  Confidence: {est.confidence_level:.0%}")

    velocity = estimator.estimate_from_review_velocity(100, 200, 0.02)
    print(f"\n  Review velocity estimate (100 reviews / 200d): {velocity}/day")


def demo_strategy_engine():
    print_banner("3. Strategy Engine")
    engine = StrategyEngine(platform=Platform.AMAZON)

    phases = engine.full_strategy(
        product_category="Kitchen & Dining",
        target_market="US",
        budget_level="medium",
    )

    for p in phases:
        title = p.get("title", "N/A")
        steps = p.get("steps", [])
        print(f"\n  [{p['phase'].upper()}] {title}")
        for s in steps[:3]:
            print(f"    - {s}")
        if len(steps) > 3:
            print(f"    ... ({len(steps)} steps total)")


def demo_live_fetch():
    print_banner("4. Live Fetch - Amazon Best Sellers (Kitchen & Dining)")
    try:
        fetcher = DataFetcher(amazon_domain=AmazonDomain.US)
        bl = fetcher.get_bestsellers(
            platform=Platform.AMAZON,
            category_id="zgbs/kitchen",
            limit=10,
        )
        print(f"  Category: {bl.category_name}")
        print(f"  Total: {len(bl.items)} items\n")
        for item in bl.items[:5]:
            print(f"  #{item.rank} {item.title[:60]}")
            print(f"      Price: {item.currency} {item.price} | Rating: {item.rating} | Reviews: {item.review_count}")
        fetcher.close()
    except Exception as e:
        print(f"  [Network unavailable - using offline mode] {e}")


def main():
    print_banner("ECOMMERCE-OPS-SKILL v0.1 - Quick Start")
    print("  Amazon BSR rank reader + cross-platform strategy engine")

    demo_rank_parser()
    demo_sales_estimator()
    demo_strategy_engine()
    demo_live_fetch()

    print_banner("DONE")


if __name__ == "__main__":
    main()