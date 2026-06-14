import pytest
from ecommerce_ops_skill import (
    Platform,
    RankParser,
    DataSource,
    RankingItem,
    PinduoduoClient,
    PinduoduoSalesEstimator,
    DouyinClient,
    DouyinLiveMetrics,
    DouyinTrafficSource,
    StrategyEngine,
)


SAMPLE_PDD_HTML = """
<html><body>
<div class="goods-list">
<div class="goods-item" data-active="goods">
    <span class="goods-title">夏季纯棉短袖T恤男士宽松潮流</span>
    <span class="goods-price"><span>9.90</span></span>
    <span class="goods-sales">已拼10万+件</span>
    <span class="goods-mall">品质男装</span>
</div>
<div class="goods-item" data-active="goods">
    <span class="goods-title">女士防晒衣UPF50+冰丝透气</span>
    <span class="goods-price"><span>15.80</span></span>
    <span class="goods-sales">已拼50万+件</span>
    <span class="mall-name pdd-brand">品牌旗舰店</span>
</div>
<div class="goods-item" data-active="goods">
    <span class="goods-title">2024新款无线蓝牙耳机降噪</span>
    <span class="goods-price"><span>29.99</span></span>
    <span class="goods-sales">已拼1.2万件</span>
</div>
</div>
</body></html>
"""


class TestPinduoduoClient:
    def test_extract_price(self):
        assert PinduoduoClient._extract_price("9.90") == 9.9
        assert PinduoduoClient._extract_price("￥29.99") == 29.99
        assert PinduoduoClient._extract_price("") is None

    def test_extract_pdd_sales(self):
        assert PinduoduoClient._extract_pdd_sales("已拼10万+件") == 100000
        assert PinduoduoClient._extract_pdd_sales("已拼50万+件") == 500000
        assert PinduoduoClient._extract_pdd_sales("已拼1.2万件") == 12000
        assert PinduoduoClient._extract_pdd_sales("") is None

    def test_analyze_price_competition(self):
        client = PinduoduoClient()
        items = [
            RankingItem(platform=Platform.PINDUODUO, rank=1, asin_or_id="1", title="A", price=9.9, data_source=DataSource.WEB_SCRAPING),
            RankingItem(platform=Platform.PINDUODUO, rank=2, asin_or_id="2", title="B", price=15.8, data_source=DataSource.WEB_SCRAPING),
            RankingItem(platform=Platform.PINDUODUO, rank=3, asin_or_id="3", title="C", price=29.99, is_bestseller=True, data_source=DataSource.WEB_SCRAPING),
        ]
        result = client.analyze_price_competition(items)
        assert result["total_items"] == 3
        assert "price_stats" in result
        assert result["price_competition_pressure"] in ("low", "medium", "high")

    def test_price_advice(self):
        assert "supply chain" in PinduoduoClient._price_advice("high")

    def test_trending_keywords(self):
        kw = PinduoduoClient().get_trending_keywords()
        assert len(kw) > 0
        kw_cloth = PinduoduoClient().get_trending_keywords("clothing")
        assert len(kw_cloth) > 0


class TestPinduoduoSalesEstimator:
    def test_two_point_estimation(self):
        est = PinduoduoSalesEstimator()
        daily = est.estimate_daily_from_two_points(100000, 100070, 1.0)
        assert daily == 1680

    def test_gmv_rank(self):
        est = PinduoduoSalesEstimator()
        result = est.estimate_gmv_rank(daily_sales_est=100, avg_price=50.0)
        assert result["tier"] == "A"
        result_b = est.estimate_gmv_rank(daily_sales_est=20, avg_price=30.0)
        assert result_b["tier"] == "C"

    def test_competitiveness(self):
        est = PinduoduoSalesEstimator()
        assert est.rank_product_competitiveness(200000, 30.0, [4.8, 4.7, 4.9], 365) == "explosive"
        assert est.rank_product_competitiveness(500, 20.0, [4.3, 4.2, 4.4], 100) == "cold"


class TestDouyinClient:
    def test_estimate_live_gmv(self):
        client = DouyinClient()
        result = client.estimate_live_gmv(avg_viewers=5000, duration_minutes=120, gpm=800)
        assert result["gpm"] == 800
        assert result["estimated_gmv_cny"] == pytest.approx(800 / 1000 * 5000 * 120, rel=0.01)

    def test_estimate_live_gmv_from_cvr(self):
        client = DouyinClient()
        result = client.estimate_live_gmv(avg_viewers=1000, duration_minutes=60, conversion_rate=0.03)
        assert result["estimated_gmv_cny"] > 0

    def test_analyze_short_video(self):
        client = DouyinClient()
        funnel = client.analyze_short_video(
            views=100000, completion_rate=0.45, interaction_rate=0.05,
            product_click_rate=0.08, conversion_rate=0.03,
        )
        assert funnel["views"] == 100000
        assert "content_tier" in funnel
        assert funnel["product_clicks"] == 8000

    def test_model_product_card(self):
        client = DouyinClient()
        perf = client.model_product_card_performance(
            impressions=50000, click_rate=0.10, add_to_cart_rate=0.30, order_rate=0.25,
        )
        assert perf["clicks"] == 5000
        assert perf["orders"] > 0
        assert perf["gpm"] > 0

    def test_estimate_brand_live_score(self):
        client = DouyinClient()
        score = client.estimate_brand_live_score(
            followers=100000, avg_live_viewers=5000, avg_live_gmv_per_hour=20000,
            video_avg_views=20000, post_frequency_per_week=4,
        )
        assert "tier" in score

    def test_estimate_sales_from_gpm(self):
        client = DouyinClient()
        est = client.estimate_sales_from_gpm(gpm=600, avg_daily_impressions=50000)
        assert est.estimated_monthly_revenue is not None
        assert est.estimated_monthly_revenue > 0

    def test_trending_categories(self):
        client = DouyinClient()
        cats = client.get_trending_categories()
        assert len(cats) >= 8


class TestDouyinLiveMetrics:
    def test_calculate_gpm(self):
        assert DouyinLiveMetrics.calculate_gpm(50000, 100000) == 500.0

    def test_calculate_opm(self):
        assert DouyinLiveMetrics.calculate_opm(120, 60) == 2.0

    def test_health_check_healthy(self):
        result = DouyinLiveMetrics.live_health_check(
            gpm=800, opm=2.5, avg_stay_minutes=2.0,
            interaction_rate=0.04, conversion_rate=0.03,
        )
        assert result["status"] == "healthy"

    def test_health_check_unhealthy(self):
        result = DouyinLiveMetrics.live_health_check(
            gpm=200, opm=0.5, avg_stay_minutes=0.5,
            interaction_rate=0.01, conversion_rate=0.005,
        )
        assert result["status"] == "needs_improvement"
        assert len(result["issues"]) > 0


class TestDouyinTrafficSource:
    def test_analyze_source_distribution(self):
        actual = {"recommendations": {"share": 0.45, "cvr": 0.03}, "search": {"share": 0.20, "cvr": 0.05}}
        result = DouyinTrafficSource.analyze_source_distribution(actual)
        assert "recommendations" in result
        assert "search" in result
        assert result["recommendations"]["status"] == "below"
        assert result["search"]["status"] == "above"

    def test_recommend_optimization(self):
        analysis = {"recommendations": {"status": "below", "current_share": 0.3, "benchmark_share": 0.5}}
        recs = DouyinTrafficSource.recommend_optimization(analysis)
        assert len(recs) >= 1


class TestRankParserPdd:
    def test_parse_pdd_search(self):
        items = RankParser.parse_pinduoduo_search_results(SAMPLE_PDD_HTML, "T恤", limit=10)
        assert len(items) == 3
        assert items[0].price == 9.9
        assert items[0].currency == "CNY"
        assert items[0].review_count == 100000
        assert items[0].platform == Platform.PINDUODUO

    def test_parse_pdd_mall_detection(self):
        items = RankParser.parse_pinduoduo_search_results(SAMPLE_PDD_HTML, "防晒衣", limit=10)
        assert items[1].is_bestseller is True

    def test_extract_pdd_sales_static(self):
        assert RankParser._extract_pdd_sales("已拼10万+件") == 100000
        assert RankParser._extract_pdd_sales("已拼50万+件") == 500000


class TestStrategyEngineV03:
    def test_pdd_full_strategy(self):
        engine = StrategyEngine(platform=Platform.PINDUODUO)
        phases = engine.full_strategy()
        assert len(phases) == 6
        assert "多多搜索" in str(phases[2].get("steps", []))
        assert "百亿补贴" in str(phases[2].get("steps", []))

    def test_douyin_full_strategy(self):
        engine = StrategyEngine(platform=Platform.DOUYIN)
        phases = engine.full_strategy()
        assert len(phases) == 6
        assert "千川" in str(phases[2].get("steps", []))
        assert "GPM" in str(phases[0].get("steps", []))

    def test_pdd_budget_levels(self):
        engine = StrategyEngine(platform=Platform.PINDUODUO)
        for budget in ["low", "medium", "high"]:
            traffic = engine.traffic_strategy(budget_level=budget)
            assert "daily_ppc" in traffic.get("budget_recommendation", {})

    def test_douyin_budget_levels(self):
        engine = StrategyEngine(platform=Platform.DOUYIN)
        for budget in ["low", "medium", "high"]:
            traffic = engine.traffic_strategy(budget_level=budget)
            assert "daily_ad_budget" in traffic.get("budget_recommendation", {})