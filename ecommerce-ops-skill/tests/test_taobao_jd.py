import pytest
from ecommerce_ops_skill import (
    Platform,
    RankParser,
    TaobaoClient,
    TaobaoSalesEstimator,
    JDClient,
    JDCategoryRanking,
    StrategyEngine,
    RankingItem,
    DataSource,
)


SAMPLE_TAOBAO_HTML = """
<html><body>
<div class="item J_MouserOnverReq">
    <a class="title" title="夏季女士连衣裙 碎花显瘦中长款" href="#">夏季女士连衣裙</a>
    <div class="price"><strong>89.00</strong></div>
    <div class="deal-cnt">月销 1.2万+</div>
    <div class="shopname">韩范儿女装旗舰店</div>
</div>
<div class="item J_MouserOnverReq">
    <a class="title" title="男士纯棉短袖T恤 韩版宽松">男士纯棉短袖T恤</a>
    <div class="price"><strong>39.90</strong></div>
    <div class="deal-cnt">月销 5800</div>
    <div class="shopname">型男衣柜</div>
</div>
<div class="item J_MouserOnverReq tmall-icon">
    <a class="title" title="防晒衣女UPF50+冰丝透气">防晒衣女UPF50+</a>
    <div class="price"><strong>129.00</strong></div>
    <div class="deal-cnt">月销 3.5万+</div>
    <div class="shopname">运动户外旗舰店</div>
</div>
</body></html>
"""

SAMPLE_JD_HTML = """
<html><body>
<ul>
<li class="gl-item" data-sku="100012345">
    <div class="p-name"><a title="iPhone 15 Pro Max 256GB">iPhone 15 Pro Max</a></div>
    <div class="p-price"><strong><i>8999.00</i></strong></div>
    <div class="p-commit"><a>50万+条评价</a></div>
    <div class="p-shopnum"><a>Apple产品京东自营旗舰店</a></div>
    <div class="goods-icons"><i class="jd-ziying">京东自营</i></div>
</li>
<li class="gl-item" data-sku="100067890">
    <div class="p-name"><a title="华为Mate 60 Pro 12+512G">华为Mate 60 Pro</a></div>
    <div class="p-price"><strong><i>6999.00</i></strong></div>
    <div class="p-commit"><a>20万+条评价</a></div>
    <div class="p-shopnum"><a>华为官方旗舰店</a></div>
</li>
<li class="gl-item" data-sku="100099999">
    <div class="p-name"><a title="小米14 Ultra 摄影旗舰">小米14 Ultra</a></div>
    <div class="p-price"><strong><i>5999.00</i></strong></div>
    <div class="p-commit"><a>8万+条评价</a></div>
    <div class="p-shopnum"><a>小米京东自营旗舰店</a></div>
</li>
</ul>
</body></html>
"""


class TestTaobaoClient:
    def test_extract_price(self):
        assert TaobaoClient._extract_price("89.00") == 89.0
        assert TaobaoClient._extract_price("1,299.00") == 1299.0
        assert TaobaoClient._extract_price("") is None

    def test_extract_monthly_sales(self):
        assert TaobaoClient._extract_monthly_sales("月销 1.2万+") == 12000
        assert TaobaoClient._extract_monthly_sales("月销 5800") == 5800
        assert TaobaoClient._extract_monthly_sales("") is None

    def test_estimate_sales_from_display(self):
        client = TaobaoClient()
        est = client.estimate_sales_from_display(monthly_sales_display=10000, price=50.0)
        assert est.estimated_monthly_sales == 10000
        assert est.estimated_monthly_revenue == 500000.0

    def test_analyze_shop_from_search(self):
        client = TaobaoClient()
        items = [
            RankingItem(platform=Platform.TAOBAO, rank=1, asin_or_id="1", title="A", price=50.0, brand="ShopA", data_source=DataSource.WEB_SCRAPING),
            RankingItem(platform=Platform.TAOBAO, rank=2, asin_or_id="2", title="B", price=80.0, brand="ShopA", data_source=DataSource.WEB_SCRAPING),
            RankingItem(platform=Platform.TAOBAO, rank=3, asin_or_id="3", title="C", price=100.0, brand="ShopB", data_source=DataSource.WEB_SCRAPING),
        ]
        result = client.analyze_shop_from_search(items)
        assert result["total_items"] == 3
        assert result["avg_price_cny"] == pytest.approx(76.67, rel=0.01)
        assert len(result["top_shops"]) == 2

    def test_default_hot_keywords(self):
        keywords = TaobaoClient._default_hot_keywords()
        assert len(keywords) > 0


class TestTaobaoSalesEstimator:
    def test_daily_orders(self):
        estimator = TaobaoSalesEstimator()
        assert estimator.estimate_daily_orders(30000) == 1000
        assert estimator.estimate_daily_orders(0) == 0

    def test_monthly_gmv(self):
        estimator = TaobaoSalesEstimator()
        assert estimator.estimate_monthly_gmv(1000, 50.0) == 50000.0

    def test_rank_competitiveness(self):
        estimator = TaobaoSalesEstimator()
        assert estimator.rank_shop_competitiveness(10000, [4.9, 4.8, 4.9], 500) == "top"
        assert estimator.rank_shop_competitiveness(500, [4.5, 4.4, 4.4], 200) == "middle"
        assert estimator.rank_shop_competitiveness(100, [4.2, 4.1, 4.3], 30) == "entry"

    def test_conversion_estimate(self):
        estimator = TaobaoSalesEstimator()
        cvr = estimator.estimate_conversion(3000, avg_visits_per_day=200)
        assert 0 < cvr < 1.0


class TestJDClient:
    def test_extract_price(self):
        assert JDClient._extract_price("8999.00") == 8999.0
        assert JDClient._extract_price("￥5999.00") == 5999.0
        assert JDClient._extract_price("") is None

    def test_extract_number(self):
        assert JDClient._extract_number("50万+条评价") == 500000
        assert JDClient._extract_number("8万+条评价") == 80000
        assert JDClient._extract_number("") is None

    def test_estimate_from_comments(self):
        client = JDClient()
        est = client.estiamte_from_comments(comment_count=50000, days_since_launch=365)
        assert est.estimated_monthly_sales is not None
        assert est.estimated_monthly_sales > 0

    def test_competition_advice(self):
        assert "dominates" in JDClient._competition_advice(8, 10)
        assert "POP-friendly" in JDClient._competition_advice(2, 10)


class TestJDCategoryRanking:
    def test_category_name(self):
        assert JDCategoryRanking.get_category_name("phone") == "手机"

    def test_list_categories(self):
        cats = JDCategoryRanking.list_categories()
        assert len(cats) >= 10


class TestRankParserCN:
    def test_parse_taobao_search(self):
        items = RankParser.parse_taobao_search_results(SAMPLE_TAOBAO_HTML, "连衣裙", limit=10)
        assert len(items) == 3
        assert "夏季女士连衣裙" in items[0].title
        assert items[0].price == 89.0
        assert items[0].currency == "CNY"
        assert items[0].review_count == 12000

    def test_parse_taobao_tmall_detection(self):
        items = RankParser.parse_taobao_search_results(SAMPLE_TAOBAO_HTML, "test")
        assert items[2].platform == Platform.TMALL

    def test_parse_jd_search(self):
        items = RankParser.parse_jd_search_results(SAMPLE_JD_HTML, "手机", limit=10)
        assert len(items) == 3
        assert "iPhone 15 Pro Max" in items[0].title
        assert items[0].price == 8999.0
        assert items[0].currency == "CNY"
        assert items[0].is_bestseller is True

    def test_extract_number_cn(self):
        assert RankParser._extract_number_cn("1.2万+") == 12000
        assert RankParser._extract_number_cn("5800") == 5800
        assert RankParser._extract_number_cn("50万+条评价") == 500000


class TestStrategyEngineCN:
    def test_taobao_strategy(self):
        engine = StrategyEngine(platform=Platform.TAOBAO)
        phases = engine.full_strategy()
        assert len(phases) == 6

        sel = phases[0]
        assert "选品" in sel.get("title", "")
        assert len(sel["steps"]) >= 5

        traffic = phases[2]
        assert "直通车" in str(traffic["steps"])

    def test_jd_strategy(self):
        engine = StrategyEngine(platform=Platform.JD)
        phases = engine.full_strategy()
        assert len(phases) == 6

        traffic = phases[2]
        assert "京准通" in str(traffic["steps"])

    def test_tmall_strategy(self):
        engine = StrategyEngine(platform=Platform.TMALL)
        phases = engine.full_strategy()
        assert len(phases) == 6

    def test_cross_platform_compare(self):
        engine = StrategyEngine()
        data = {
            "taobao": [RankingItem(platform=Platform.TAOBAO, rank=1, asin_or_id="1", title="A", price=50.0, data_source=DataSource.WEB_SCRAPING)],
            "jd": [RankingItem(platform=Platform.JD, rank=1, asin_or_id="2", title="B", price=80.0, data_source=DataSource.WEB_SCRAPING)],
        }
        result = engine.cross_platform_compare(data)
        assert "taobao" in result
        assert "jd" in result

    def test_taobao_budget_levels(self):
        engine = StrategyEngine(platform=Platform.TAOBAO)
        for budget in ["low", "medium", "high"]:
            traffic = engine.traffic_strategy(budget_level=budget)
            assert "daily_ppc" in traffic.get("budget_recommendation", {})

    def test_jd_budget_levels(self):
        engine = StrategyEngine(platform=Platform.JD)
        for budget in ["low", "medium", "high"]:
            traffic = engine.traffic_strategy(budget_level=budget)
            assert "daily_ppc" in traffic.get("budget_recommendation", {})