import pytest
from ecommerce_ops_skill import (
    Platform, RankingItem, DataSource, DataExporter,
    XiaohongshuClient, StrategyEngine,
)


class TestXiaohongshuClient:
    def test_analyze_note_performance(self):
        client = XiaohongshuClient()
        result = client.analyze_note_performance(
            views=50000, likes=2500, collects=3000, comments=500, shares=200,
            product_click_rate=0.08, conversion_rate=0.03, avg_order_value=50.0,
        )
        assert result["views"] == 50000
        assert result["total_interactions"] == 6200
        assert "content_tier" in result
        assert result["conversion_funnel"]["orders"] == pytest.approx(120, rel=0.1)
        assert result["conversion_funnel"]["gmv_cny"] > 0

    def test_analyze_note_s_tier(self):
        client = XiaohongshuClient()
        result = client.analyze_note_performance(
            views=100000, likes=15000, collects=10000, comments=3000, shares=5000,
            product_click_rate=0.10, conversion_rate=0.05,
        )
        assert result["content_tier"] == "S"

    def test_analyze_kol_head(self):
        client = XiaohongshuClient()
        result = client.analyze_kol_profile(
            followers=500000, avg_note_views=60000, avg_note_likes=8000,
            avg_note_collects=12000, total_notes=200, verified=True,
            avg_conversion_rate=0.03, avg_order_value=80.0,
        )
        assert result["kol_tier"] == "头部KOL"

    def test_analyze_kol_koc(self):
        client = XiaohongshuClient()
        result = client.analyze_kol_profile(
            followers=5000, avg_note_views=800, avg_note_likes=100,
            avg_note_collects=200, total_notes=30,
            avg_conversion_rate=0.03, avg_order_value=50.0,
            cooperation_price=2000,
        )
        assert result["kol_tier"] == "KOC素人"

    def test_model_brand_campaign(self):
        client = XiaohongshuClient()
        result = client.model_brand_campaign(
            budget=50000, kol_count=20, avg_kol_followers=50000,
            avg_kol_views=5000, avg_note_engagement=0.05,
            product_price=100.0, additional_ad_spend=20000,
        )
        assert result["total_spend_cny"] == 70000
        assert result["total_gmv_cny"] > 0
        assert "overall_roi" in result

    def test_estimate_note_trend(self):
        client = XiaohongshuClient()
        result = client.estimate_note_trend("护肤品", note_count=5000, avg_views_per_note=2000, category_growth_rate=0.15)
        assert result["competition_level"] == "low_competition"
        assert result["trend"] == "surging"

    def test_search_content_trends(self):
        client = XiaohongshuClient()
        result = client.search_content_trends()
        assert len(result) > 0
        filtered = client.search_content_trends("护肤")
        assert len(filtered) >= 1

    def test_trending_tags(self):
        client = XiaohongshuClient()
        tags = client.get_trending_notes_tags()
        assert len(tags) > 0
        beauty_tags = client.get_trending_notes_tags("beauty")
        assert len(beauty_tags) > 0

    def test_content_roi(self):
        client = XiaohongshuClient()
        result = client.estimate_content_roi(
            note_views=50000, product_price=80.0,
            note_production_cost=500, influencer_cost=2000,
        )
        assert result["roi"] == pytest.approx(32.0, rel=0.05)

    # ---- Real HTTP scraping tests ----

    def test_search_notes_fallback_to_mock(self):
        client = XiaohongshuClient()
        results = client.search_notes("护肤", page=1)
        assert len(results) == 10
        assert results[0].platform == Platform.XIAOHONGSHU
        assert results[0].rank == 1
        assert "护肤" in results[0].title
        assert results[0].data_source == DataSource.MODEL_ESTIMATION

    def test_search_notes_page_2(self):
        client = XiaohongshuClient()
        results = client.search_notes("穿搭", page=2)
        assert len(results) == 10
        assert results[0].rank == 11

    def test_get_note_detail_fallback(self):
        client = XiaohongshuClient()
        detail = client.get_note_detail("test-note-123")
        assert detail["note_id"] == "test-note-123"
        assert detail["data_source"] == "mock_fallback"
        assert "title" in detail
        assert "user" in detail

    def test_search_users_fallback(self):
        client = XiaohongshuClient()
        users = client.search_users("美妆")
        assert len(users) >= 3
        assert "nickname" in users[0]
        assert "followers" in users[0]

    def test_using_real_data_flag_false(self):
        client = XiaohongshuClient()
        assert client.using_real_data is False
        client.search_notes("test")
        assert client.using_real_data is False


class TestDataExporter:
    def test_to_csv(self):
        items = [
            RankingItem(platform=Platform.AMAZON, rank=1, asin_or_id="B01", title="Test", price=9.99,
                       currency="USD", rating=4.5, review_count=100, brand="BrandA", is_bestseller=True,
                       data_source=DataSource.WEB_SCRAPING),
        ]
        csv_content = DataExporter.to_csv(items)
        assert "B01" in csv_content
        assert "Test" in csv_content
        assert "9.99" in csv_content
        assert "Y" in csv_content

    def test_to_json(self):
        items = [
            RankingItem(platform=Platform.PINDUODUO, rank=1, asin_or_id="pdd-1", title="PDD Test", price=5.0,
                       currency="CNY", data_source=DataSource.WEB_SCRAPING),
        ]
        json_content = DataExporter.to_json(items)
        assert "pdd-1" in json_content
        assert "PDD Test" in json_content

    def test_generate_daily_report(self):
        items = {
            "taobao": [
                RankingItem(platform=Platform.TAOBAO, rank=1, asin_or_id="tb-1", title="连衣裙", price=89.0,
                           review_count=5000, brand="韩范", data_source=DataSource.WEB_SCRAPING),
            ],
            "jd": [
                RankingItem(platform=Platform.JD, rank=1, asin_or_id="jd-1", title="手机", price=6999.0,
                           review_count=200000, is_bestseller=True, data_source=DataSource.WEB_SCRAPING),
            ],
        }
        report = DataExporter.generate_daily_report(items)
        assert "TAOBAO" in report
        assert "JD" in report
        assert "全平台总计" in report

    def test_gmv_dashboard(self):
        products = [
            {"title": "A", "monthly_gmv": 500000, "monthly_orders": 1000, "platform": "douyin"},
            {"title": "B", "monthly_gmv": 200000, "monthly_orders": 500, "platform": "taobao"},
            {"title": "C", "monthly_gmv": 20000, "monthly_orders": 50, "platform": "pdd"},
        ]
        dashboard = DataExporter.generate_gmv_dashboard(products)
        assert dashboard["summary"]["total_gmv_cny"] == 720000
        assert len(dashboard["top_5_by_gmv"]) == 3
        assert dashboard["gmv_tier_distribution"]["S(>50万)"] >= 1
        assert dashboard["gmv_tier_distribution"]["C(1-3万)"] >= 1

    def test_comparison_table(self):
        data = {
            "taobao": [RankingItem(platform=Platform.TAOBAO, rank=1, asin_or_id="1", title="A", price=50.0, is_bestseller=True, data_source=DataSource.WEB_SCRAPING)],
            "jd": [RankingItem(platform=Platform.JD, rank=1, asin_or_id="2", title="B", price=80.0, data_source=DataSource.WEB_SCRAPING)],
        }
        table = DataExporter.create_comparison_table(data)
        assert "taobao" in table
        assert "jd" in table
        assert "50.00" in table


class TestStrategyAdvanced:
    def test_generate_cross_platform_swot(self):
        engine = StrategyEngine()
        data = {
            "pdd": [
                RankingItem(platform=Platform.PINDUODUO, rank=1, asin_or_id="1", title="LowPrice", price=5.0, review_count=10000, is_bestseller=True, data_source=DataSource.WEB_SCRAPING),
                RankingItem(platform=Platform.PINDUODUO, rank=2, asin_or_id="2", title="MidPrice", price=15.0, review_count=2000, data_source=DataSource.WEB_SCRAPING),
            ],
        }
        swot = engine.generate_cross_platform_swot(data)
        assert "pdd" in swot
        assert len(swot["pdd"]["strengths"]) >= 1
        assert len(swot["pdd"]["weaknesses"]) >= 1

    def test_analyze_price_elasticity(self):
        engine = StrategyEngine()
        items = [
            RankingItem(platform=Platform.JD, rank=i, asin_or_id=str(i), title=f"P{i*10}", price=i*10, review_count=i*5, data_source=DataSource.WEB_SCRAPING)
            for i in range(1, 11)
        ]
        result = engine.analyze_price_elasticity(items)
        assert len(result["price_bands"]) > 0
        assert "sweet_spot" in result

    def test_predict_seasonal_trend(self):
        engine = StrategyEngine()
        result = engine.predict_seasonal_trend("clothing")
        assert "peak_months" in result
        assert "trough_months" in result
        assert "next_peak" in result

    def test_full_cross_platform_matrix(self):
        engine = StrategyEngine()
        data = {
            "pdd": [RankingItem(platform=Platform.PINDUODUO, rank=1, asin_or_id="1", title="A", price=10.0, is_bestseller=True, data_source=DataSource.WEB_SCRAPING)],
            "jd": [RankingItem(platform=Platform.JD, rank=1, asin_or_id="2", title="B", price=100.0, data_source=DataSource.WEB_SCRAPING)],
        }
        matrix = engine.full_cross_platform_matrix(data)
        assert "pdd" in matrix
        assert "jd" in matrix

    def test_xhs_strategy(self):
        engine = StrategyEngine(platform=Platform.XIAOHONGSHU)
        phases = engine.full_strategy()
        assert len(phases) == 6
        assert "达" in str(phases[2].get("steps", []))


class TestDataExporterFileIO:
    def test_csv_to_file(self, tmp_path):
        items = [RankingItem(platform=Platform.AMAZON, rank=1, asin_or_id="B01", title="Test", data_source=DataSource.WEB_SCRAPING)]
        fp = str(tmp_path / "test.csv")
        DataExporter.to_csv(items, filepath=fp)
        with open(fp, "r", encoding="utf-8-sig") as f:
            assert "B01" in f.read()

    def test_json_to_file(self, tmp_path):
        items = [RankingItem(platform=Platform.AMAZON, rank=1, asin_or_id="B01", title="Test", data_source=DataSource.WEB_SCRAPING)]
        fp = str(tmp_path / "test.json")
        DataExporter.to_json(items, filepath=fp)
        with open(fp, "r", encoding="utf-8") as f:
            assert "B01" in f.read()