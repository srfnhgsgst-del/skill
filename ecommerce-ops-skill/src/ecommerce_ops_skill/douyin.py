from typing import Optional
import httpx

from ecommerce_ops_skill.platform import Platform, DataSource
from ecommerce_ops_skill.models import (
    SalesEstimate,
)


class DouyinClient:
    """抖音电商 数据模型 —— 直播/短视频/商品卡的 GPM/Opm/转化漏斗分析"""

    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.douyin.com/",
    }

    CATEGORY_MAP = {
        "apparel": "服饰内衣",
        "beauty": "美妆护肤",
        "food": "食品饮料",
        "home": "家居家装",
        "baby": "母婴用品",
        "digital": "3C数码",
        "sport": "运动户外",
        "pet": "宠物用品",
        "books": "图书教育",
        "jewelry": "珠宝文玩",
    }

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self._client: Optional[httpx.Client] = None

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                headers=self.DEFAULT_HEADERS,
                timeout=self.timeout,
                follow_redirects=True,
            )
        return self._client

    def close(self):
        if self._client:
            self._client.close()
            self._client = None

    def estimate_live_gmv(
        self,
        avg_viewers: int,
        duration_minutes: int,
        gpm: Optional[float] = None,
        conversion_rate: float = 0.03,
        avg_order_value: float = 50.0,
    ) -> dict:
        if gpm:
            estimated_gmv = gpm / 1000 * avg_viewers * duration_minutes
            orders = int(estimated_gmv / max(1, avg_order_value))
        else:
            total_views = avg_viewers * duration_minutes
            orders = int(total_views * conversion_rate)
            estimated_gmv = orders * avg_order_value
            gpm = estimated_gmv / (avg_viewers * duration_minutes) * 1000 if avg_viewers > 0 else 0

        omp = orders / max(1, duration_minutes)
        uv_value = estimated_gmv / max(1, avg_viewers)

        return {
            "estimated_gmv_cny": round(estimated_gmv, 2),
            "gpm": round(gpm, 2),
            "opm": round(omp, 2),
            "avg_viewers": avg_viewers,
            "duration_minutes": duration_minutes,
            "uv_value_cny": round(uv_value, 2),
            "confidence": "estimate based on input params",
        }

    def analyze_short_video(
        self,
        views: int,
        completion_rate: float,
        interaction_rate: float,
        product_click_rate: float,
        conversion_rate: float,
        avg_order_value: float = 50.0,
    ) -> dict:
        product_clicks = int(views * product_click_rate)
        orders = int(product_clicks * conversion_rate)
        gmv = orders * avg_order_value

        funnel = {
            "views": views,
            "completion_rate": completion_rate,
            "viewers_completed": int(views * completion_rate),
            "interactions": int(views * interaction_rate),
            "interaction_rate": interaction_rate,
            "product_clicks": product_clicks,
            "product_click_rate": product_click_rate,
            "orders": orders,
            "conversion_rate": conversion_rate,
            "gmv_cny": round(gmv, 2),
        }

        quality_score = (completion_rate * 0.3 + interaction_rate * 5 * 0.3 + product_click_rate * 10 * 0.2 + conversion_rate * 10 * 0.2)
        funnel["quality_score"] = round(quality_score, 4)

        if quality_score > 0.7:
            funnel["content_tier"] = "S"
        elif quality_score > 0.4:
            funnel["content_tier"] = "A"
        elif quality_score > 0.2:
            funnel["content_tier"] = "B"
        else:
            funnel["content_tier"] = "C"

        return funnel

    def model_product_card_performance(
        self,
        impressions: int,
        click_rate: float,
        add_to_cart_rate: float,
        order_rate: float,
        avg_price: float = 50.0,
    ) -> dict:
        clicks = int(impressions * click_rate)
        add_to_carts = int(clicks * add_to_cart_rate)
        orders = int(add_to_carts * order_rate)
        gmv = orders * avg_price

        gpm = gmv / max(1, impressions) * 1000
        ctr_product_clicks = click_rate
        cvr_impression_to_order = orders / max(1, impressions)

        return {
            "impressions": impressions,
            "clicks": clicks,
            "ctr": round(ctr_product_clicks, 4),
            "add_to_carts": add_to_carts,
            "add_to_cart_rate": round(add_to_cart_rate, 4),
            "orders": orders,
            "order_rate": round(order_rate, 4),
            "cvr": round(cvr_impression_to_order, 4),
            "gmv_cny": round(gmv, 2),
            "gpm": round(gpm, 2),
        }

    def estimate_brand_live_score(
        self,
        followers: int,
        avg_live_viewers: int,
        avg_live_gmv_per_hour: float,
        video_avg_views: int,
        post_frequency_per_week: int,
    ) -> dict:
        fan_engagement = avg_live_viewers / max(1, followers)

        daily_video_views = video_avg_views * (post_frequency_per_week / 7)
        content_power = daily_video_views / max(1, followers)

        composite = fan_engagement * 100 * 0.3 + (avg_live_gmv_per_hour / max(1, avg_live_viewers)) * 0.4 + min(content_power * 1000, 1) * 0.3

        if composite > 50:
            tier = "头部达人"
        elif composite > 15:
            tier = "腰部达人"
        elif composite > 5:
            tier = "尾部达人"
        else:
            tier = "新手/低活跃"

        return {
            "fan_engagement_rate": round(fan_engagement, 4),
            "content_power_index": round(content_power, 4),
            "composite_score": round(composite, 2),
            "tier": tier,
        }

    def get_trending_categories(self) -> list[dict]:
        return [
            {"key": k, "name": v, "gpm_trend": "rising" if i % 2 == 0 else "stable"}
            for i, (k, v) in enumerate(self.CATEGORY_MAP.items())
        ]

    def estimate_sales_from_gpm(
        self,
        gpm: float,
        avg_daily_impressions: int,
    ) -> SalesEstimate:
        daily_gmv = gpm / 1000 * avg_daily_impressions
        return SalesEstimate(
            asin="",
            platform=Platform.DOUYIN,
            estimated_daily_sales=None,
            estimated_monthly_revenue=round(daily_gmv * 30, 2),
            confidence_level=0.5,
            estimation_method="gpm_based",
            data_source=DataSource.MODEL_ESTIMATION,
        )


class DouyinLiveMetrics:
    """抖音直播核心指标模型 —— 模拟抖音罗盘直播分析"""

    @staticmethod
    def calculate_gpm(gmv: float, pv: int) -> float:
        return gmv / max(1, pv) * 1000

    @staticmethod
    def calculate_opm(orders: int, duration_minutes: float) -> float:
        return orders / max(1, duration_minutes)

    @staticmethod
    def calculate_uv_value(gmv: float, uv: int) -> float:
        return gmv / max(1, uv)

    @staticmethod
    def calculate_stay_rate(avg_stay_seconds: float, total_duration_seconds: float) -> float:
        return avg_stay_seconds / max(1, total_duration_seconds)

    @staticmethod
    def live_health_check(
        gpm: float,
        opm: float,
        avg_stay_minutes: float,
        interaction_rate: float,
        conversion_rate: float,
    ) -> dict:
        issues: list[str] = []
        if gpm < 500:
            issues.append("GPM < 500, consider optimizing products or pricing")
        if opm < 1:
            issues.append("OPM < 1, improve anchor sales technique")
        if avg_stay_minutes < 1:
            issues.append("Avg stay < 1min, improve content engagement")
        if interaction_rate < 0.02:
            issues.append("Low interaction, add Q&A/sweepstakes")
        if conversion_rate < 0.01:
            issues.append("CVR < 1%, review product-market fit")

        if not issues:
            return {"status": "healthy", "gpm": gpm, "opm": opm}
        else:
            return {"status": "needs_improvement", "issues": issues}


class DouyinTrafficSource:
    """抖音电商流量来源分析 —— 推荐/搜索/关注/付费/直播-短视频互导"""

    SOURCE_BENCHMARKS = {
        "recommendations": {"share": 0.50, "cvr": 0.025},
        "search": {"share": 0.15, "cvr": 0.04},
        "following": {"share": 0.10, "cvr": 0.05},
        "paid": {"share": 0.20, "cvr": 0.03},
        "live_to_video": {"share": 0.05, "cvr": 0.02},
    }

    @classmethod
    def analyze_source_distribution(cls, actual_distribution: dict) -> dict:
        result = {}
        for source, data in actual_distribution.items():
            benchmark = cls.SOURCE_BENCHMARKS.get(source, {})
            result[source] = {
                "current_share": data.get("share", 0),
                "benchmark_share": benchmark.get("share", 0),
                "current_cvr": data.get("cvr", 0),
                "benchmark_cvr": benchmark.get("cvr", 0),
                "status": "above" if data.get("share", 0) > benchmark.get("share", 0) else "below",
            }
        return result

    @classmethod
    def recommend_optimization(cls, analysis: dict) -> list[str]:
        recs: list[str] = []
        for source, data in analysis.items():
            if data["status"] == "below":
                recs.append(f"Boost {source}: currently {data['current_share']:.0%} vs benchmark {data['benchmark_share']:.0%}")
        return recs