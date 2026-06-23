import pytest
from ecommerce_ops_skill import (
    Platform,
    AmazonDomain,
    RankingItem,
    BestSellerList,
    RankParser,
    AmazonSalesEstimator,
    StrategyEngine,
)


SAMPLE_AMAZON_BSR_HTML = """
<html>
<body>
<div class="p13n-gridRow" data-asin="B0EXAMPLE1">
    <img src="https://example.com/img1.jpg" alt="Sample Product One">
    <div class="p13n-sc-truncate-desktop-type2">Sample Product One Title</div>
    <span class="p13n-sc-price">$19.99</span>
    <i class="a-icon-alt">4.5 out of 5 stars</i>
    <span class="a-size-small">12,345</span>
</div>
<div class="p13n-gridRow" data-asin="B0EXAMPLE2">
    <img src="https://example.com/img2.jpg" alt="Sample Product Two">
    <div class="p13n-sc-truncate-desktop-type2">Sample Product Two Title</div>
    <span class="p13n-sc-price">$29.99</span>
    <i class="a-icon-alt">4.2 out of 5 stars</i>
    <span class="a-size-small">5,678</span>
</div>
<div class="p13n-gridRow" data-asin="B0EXAMPLE3">
    <img src="https://example.com/img3.jpg" alt="Sample Product Three">
    <div class="p13n-sc-truncate-desktop-type2">Sample Product Three Title</div>
    <span class="p13n-sc-price">$9.99</span>
    <i class="a-icon-alt">4.7 out of 5 stars</i>
    <span class="a-size-small">25,000</span>
    <span class="sponsored-label">Sponsored</span>
</div>
</body>
</html>
"""


SAMPLE_AMAZON_PRODUCT_HTML = """
<html>
<body>
<span id="productTitle">Premium Widget - Professional Grade</span>
<span class="a-price-symbol">$</span>
<span class="a-price-whole">24</span>
<span class="a-price-fraction">99</span>
<span id="acrPopover" title="4.5 out of 5 stars"></span>
<span id="acrCustomerReviewText">3,421 ratings</span>
<span id="bylineInfo">Brand: TestBrand</span>
<div id="availability">
    <span>In Stock</span>
</div>
<ul id="feature-bullets">
    <li><span class="a-list-item">Feature 1: High durability</span></li>
    <li><span class="a-list-item">Feature 2: Lightweight design</span></li>
</ul>
<div id="detailBullets_feature_div">
    <li>Best Sellers Rank: #2,345 in Tools & Home Improvement</li>
</div>
</body>
</html>
"""


class TestRankParser:
    def test_parse_amazon_bestsellers_basic(self):
        items = RankParser.parse_amazon_bestsellers(
            SAMPLE_AMAZON_BSR_HTML,
            domain=AmazonDomain.US,
            category="Test",
            limit=10,
        )
        assert len(items) >= 1
        first = items[0]
        assert first.platform == Platform.AMAZON
        assert first.rank == 1
        assert first.asin_or_id == "B0EXAMPLE1"
        assert first.title == "Sample Product One Title"
        assert first.price == 19.99
        assert first.currency == "USD"
        assert first.rating == 4.5
        assert first.review_count == 12345

    def test_parse_amazon_bestsellers_sponsored(self):
        items = RankParser.parse_amazon_bestsellers(
            SAMPLE_AMAZON_BSR_HTML,
            domain=AmazonDomain.US,
            category="Test",
        )
        sponsored = [i for i in items if i.is_sponsored]
        assert len(sponsored) == 1
        assert sponsored[0].asin_or_id == "B0EXAMPLE3"

    def test_parse_amazon_product_page(self):
        data = RankParser.parse_amazon_product_page(
            SAMPLE_AMAZON_PRODUCT_HTML,
            domain=AmazonDomain.US,
        )
        assert data["title"] == "Premium Widget - Professional Grade"
        assert data["price"] == 24.99
        assert data["currency_symbol"] == "$"
        assert "In Stock" in data["availability"]
        assert len(data["features"]) == 2
        assert "Best Sellers Rank" in data.get("bsr_text", "")

    def test_format_bestseller_table(self):
        items = [
            RankingItem(
                platform=Platform.AMAZON,
                rank=1,
                asin_or_id="B0TEST1",
                title="Test Item",
                price=19.99,
                currency="USD",
                rating=4.5,
                review_count=1000,
            )
        ]
        table = RankParser.format_bestseller_table(items)
        assert "B0TEST1" in table
        assert "19.99" in table

    def test_extract_asin(self):
        assert RankParser._extract_asin("/dp/B0ABCDEFGH/ref=zg_bs") == "B0ABCDEFGH"
        assert RankParser._extract_asin("https://amazon.com/dp/B0XYZ12345") == "B0XYZ12345"
        assert RankParser._extract_asin("/gp/product/B0NOMATCH") == ""

    def test_parse_price(self):
        assert RankParser._parse_price("$19.99") == 19.99
        assert RankParser._parse_price("1,234.56") == 1234.56
        assert RankParser._parse_price("") is None

    def test_detect_currency(self):
        assert RankParser._detect_currency(AmazonDomain.US) == "USD"
        assert RankParser._detect_currency(AmazonDomain.JP) == "JPY"
        assert RankParser._detect_currency(AmazonDomain.UK) == "GBP"


class TestAmazonSalesEstimator:
    def test_estimate_from_bsr(self):
        estimator = AmazonSalesEstimator()
        high_rank = estimator.estimate_daily_sales("B0TEST1", 50)
        assert high_rank.estimated_daily_sales is not None
        assert high_rank.estimated_daily_sales > 0
        assert high_rank.confidence_level >= 0.3
        assert high_rank.estimation_method == "bsr_correlation_table"

    def test_estimate_low_rank(self):
        estimator = AmazonSalesEstimator()
        low_rank = estimator.estimate_daily_sales("B0TEST2", 150000)
        assert low_rank.estimated_daily_sales == 0

    def test_estimate_zero_bsr(self):
        estimator = AmazonSalesEstimator()
        zero_rank = estimator.estimate_daily_sales("B0TEST3", 0)
        assert zero_rank.estimated_daily_sales == 0

    def test_bsr_history_trend(self):
        estimator = AmazonSalesEstimator()
        estimator.add_bsr_snapshot("B0TREND", 500, "Test")
        estimator.add_bsr_snapshot("B0TREND", 400, "Test")
        estimator.add_bsr_snapshot("B0TREND", 300, "Test")
        est = estimator.estimate_daily_sales("B0TREND", 300)
        assert est.sales_trend == "rising"

    def test_review_velocity(self):
        estimator = AmazonSalesEstimator()
        result = estimator.estimate_from_review_velocity(
            review_count=100,
            days_since_first_review=200,
            category_avg_review_rate=0.02,
        )
        assert result > 0


class TestStrategyEngine:
    def test_full_strategy(self):
        engine = StrategyEngine(platform=Platform.AMAZON)
        phases = engine.full_strategy(product_category="Kitchen", budget_level="medium")
        assert len(phases) == 6
        phases_dict = {p["phase"]: p for p in phases}
        assert "selection" in phases_dict
        assert "listing" in phases_dict
        assert "traffic" in phases_dict
        assert "conversion" in phases_dict
        assert "retention" in phases_dict
        assert "review" in phases_dict

    def test_amazon_selection_strategy(self):
        engine = StrategyEngine(platform=Platform.AMAZON)
        result = engine.selection_strategy()
        assert result["platform"] == "amazon"
        assert len(result["steps"]) >= 5
        assert len(result["key_metrics"]) >= 3

    def test_unsupported_platform(self):
        engine = StrategyEngine(platform=Platform.XIAOHONGSHU)
        result = engine.selection_strategy()
        assert result["platform"] == "xiaohongshu"
        assert len(result["steps"]) >= 5

    def test_analyze_competitor(self):
        engine = StrategyEngine()
        items = [
            RankingItem(platform=Platform.AMAZON, rank=1, asin_or_id="B01", title="A", price=10.0, rating=4.5, review_count=100, brand="BrandA"),
            RankingItem(platform=Platform.AMAZON, rank=2, asin_or_id="B02", title="B", price=20.0, rating=4.0, review_count=200, brand="BrandA"),
            RankingItem(platform=Platform.AMAZON, rank=3, asin_or_id="B03", title="C", price=30.0, rating=4.8, review_count=300, brand="BrandB", is_sponsored=True),
        ]
        bl = BestSellerList(platform=Platform.AMAZON, category_id="test", category_name="Test", items=items)
        result = engine.analyze_competitor_from_bestseller(bl)
        assert result["total_items"] == 3
        assert result["avg_price"] == 20.0
        assert result["sponsored_ratio"] == pytest.approx(1/3)
        assert len(result["top_brands"]) == 2


class TestPlatform:
    def test_display_name(self):
        assert Platform.AMAZON.display_name == "Amazon"
        assert Platform.TAOBAO.display_name is not None

    def test_base_url(self):
        assert "amazon.com" in (Platform.AMAZON.base_url or "")
        assert "taobao.com" in (Platform.TAOBAO.base_url or "")

    def test_amazon_domain(self):
        assert AmazonDomain.US.country_code == "us"
        assert AmazonDomain.JP.country_code == "jp"
        assert "美国站" in AmazonDomain.US.locale_name

    def test_bestseller_urls(self):
        assert Platform.AMAZON.bestseller_url is not None
        assert Platform.JD.bestseller_url is not None
        assert Platform.DOUYIN.bestseller_url is None