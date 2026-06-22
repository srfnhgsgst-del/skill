from typing import Optional

from ecommerce_ops_skill.platform import Platform, AmazonDomain
from ecommerce_ops_skill.models import BestSellerList, ProductDetail, SalesEstimate
from ecommerce_ops_skill.amazon import AmazonClient, AmazonSalesEstimator
from ecommerce_ops_skill.taobao import TaobaoClient, TaobaoSalesEstimator
from ecommerce_ops_skill.jd import JDClient
from ecommerce_ops_skill.pinduoduo import PinduoduoClient, PinduoduoSalesEstimator
from ecommerce_ops_skill.douyin import DouyinClient
from ecommerce_ops_skill.xiaohongshu import XiaohongshuClient


class DataFetcher:
    """统一数据获取入口"""

    def __init__(self, amazon_domain: AmazonDomain = AmazonDomain.US, timeout: float = 30.0):
        self._amazon: Optional[AmazonClient] = None
        self._amazon_estimator: Optional[AmazonSalesEstimator] = None
        self._taobao: Optional[TaobaoClient] = None
        self._taobao_estimator: Optional[TaobaoSalesEstimator] = None
        self._jd: Optional[JDClient] = None
        self._pdd: Optional[PinduoduoClient] = None
        self._pdd_estimator: Optional[PinduoduoSalesEstimator] = None
        self._douyin: Optional[DouyinClient] = None
        self._xhs: Optional[XiaohongshuClient] = None
        self._amazon_domain = amazon_domain
        self._timeout = timeout

    @property
    def amazon(self) -> AmazonClient:
        if self._amazon is None:
            self._amazon = AmazonClient(domain=self._amazon_domain, timeout=self._timeout)
        return self._amazon

    @property
    def amazon_estimator(self) -> AmazonSalesEstimator:
        if self._amazon_estimator is None:
            self._amazon_estimator = AmazonSalesEstimator()
        return self._amazon_estimator

    @property
    def taobao(self) -> TaobaoClient:
        if self._taobao is None:
            self._taobao = TaobaoClient(timeout=self._timeout)
        return self._taobao

    @property
    def taobao_estimator(self) -> TaobaoSalesEstimator:
        if self._taobao_estimator is None:
            self._taobao_estimator = TaobaoSalesEstimator()
        return self._taobao_estimator

    @property
    def jd(self) -> JDClient:
        if self._jd is None:
            self._jd = JDClient(timeout=self._timeout)
        return self._jd

    @property
    def pdd(self) -> PinduoduoClient:
        if self._pdd is None:
            self._pdd = PinduoduoClient(timeout=self._timeout)
        return self._pdd

    @property
    def pdd_estimator(self) -> PinduoduoSalesEstimator:
        if self._pdd_estimator is None:
            self._pdd_estimator = PinduoduoSalesEstimator()
        return self._pdd_estimator

    @property
    def douyin(self) -> DouyinClient:
        if self._douyin is None:
            self._douyin = DouyinClient(timeout=self._timeout)
        return self._douyin

    @property
    def xhs(self) -> XiaohongshuClient:
        if self._xhs is None:
            self._xhs = XiaohongshuClient(timeout=self._timeout)
        return self._xhs

    def get_bestsellers(self, platform: Platform = Platform.AMAZON, category_id: str = "zgbs", limit: int = 100) -> BestSellerList:
        if platform == Platform.AMAZON:
            return self.amazon.get_bestsellers(category_id=category_id, limit=limit)
        elif platform == Platform.JD:
            return self.jd.get_bestsellers(category_id=category_id, limit=limit)
        else:
            raise NotImplementedError(f"Bestseller list not available for {platform} in v0.3")

    def search_products(self, platform: Platform, keyword: str, limit: int = 40, sort: str = "default") -> list:
        if platform in (Platform.TAOBAO, Platform.TMALL):
            return self.taobao.search_products(keyword=keyword, limit=limit, sort=sort)
        elif platform == Platform.JD:
            return self.jd.search_products(keyword=keyword, limit=limit, sort=sort)
        elif platform == Platform.PINDUODUO:
            return self.pdd.search_products(keyword=keyword, limit=limit, sort=sort)
        else:
            raise NotImplementedError(f"Search not available for {platform} in v0.3")

    def get_product_detail(self, platform: Platform, product_id: str) -> ProductDetail:
        if platform == Platform.AMAZON:
            return self.amazon.get_product_detail(asin=product_id)
        else:
            raise NotImplementedError(f"Product detail not available for {platform} in v0.3")

    def get_products_batch(self, platform: Platform, product_ids: list[str]) -> list[ProductDetail]:
        if platform == Platform.AMAZON:
            return self.amazon.get_products_batch(asins=product_ids)
        else:
            raise NotImplementedError(f"Batch detail not available for {platform} in v0.3")

    def estimate_sales(
        self, platform: Platform, bsr: int = 0, product_id: str = "", review_count: int = 0,
        days_since_first_review: int = 0, monthly_sales_display: int = 0, avg_price: float = 0.0,
        goods_id: str = "", gpm: float = 0.0, avg_daily_impressions: int = 0,
    ) -> SalesEstimate:
        if platform == Platform.AMAZON:
            if bsr > 0:
                return self.amazon_estimator.estimate_daily_sales(product_id, bsr)
            elif review_count > 0 and days_since_first_review > 0:
                est = self.amazon_estimator.estimate_from_review_velocity(review_count, days_since_first_review)
                return SalesEstimate(asin=product_id, platform=Platform.AMAZON, estimated_daily_sales=est, estimated_monthly_sales=est * 30, estimation_method="review_velocity")
            else:
                return SalesEstimate(asin=product_id, platform=Platform.AMAZON, confidence_level=0.0)

        elif platform in (Platform.TAOBAO, Platform.TMALL):
            if monthly_sales_display > 0 and avg_price > 0:
                return self.taobao.estimate_sales_from_display(monthly_sales_display, avg_price)
            elif monthly_sales_display > 0:
                est = self.taobao_estimator.estimate_daily_orders(monthly_sales_display)
                return SalesEstimate(asin=product_id, platform=platform, estimated_daily_sales=est, estimated_monthly_sales=monthly_sales_display, confidence_level=0.6, estimation_method="displayed_monthly_sales")
            else:
                return SalesEstimate(asin=product_id, platform=platform, confidence_level=0.0)

        elif platform == Platform.JD:
            if review_count > 0 and days_since_first_review > 0:
                return self.jd.estiamte_from_comments(review_count, days_since_first_review)
            elif bsr > 0:
                daily = max(0, int(100000 / bsr * 0.02))
                return SalesEstimate(asin=product_id, platform=Platform.JD, estimated_daily_sales=daily, estimated_monthly_sales=daily * 30, confidence_level=0.3, estimation_method="rank_correlation")
            else:
                return SalesEstimate(asin=product_id, platform=Platform.JD, confidence_level=0.0)

        elif platform == Platform.PINDUODUO:
            if goods_id:
                return self.pdd.estimate_sales_from_snapshots(goods_id)
            else:
                return SalesEstimate(asin=product_id, platform=Platform.PINDUODUO, confidence_level=0.0)

        elif platform == Platform.DOUYIN:
            if gpm > 0 and avg_daily_impressions > 0:
                return self.douyin.estimate_sales_from_gpm(gpm, avg_daily_impressions)
            else:
                return SalesEstimate(asin=product_id, platform=Platform.DOUYIN, confidence_level=0.0)

        else:
            raise NotImplementedError(f"Sales estimate not available for {platform} in v0.4")

    def get_amazon_categories(self) -> list[dict]:
        return self.amazon.get_category_list()

    def cross_platform_search(self, keyword: str, platforms: Optional[list[Platform]] = None, limit: int = 20) -> dict:
        if platforms is None:
            platforms = [Platform.TAOBAO, Platform.JD, Platform.PINDUODUO, Platform.DOUYIN, Platform.XIAOHONGSHU]
        results: dict = {}
        for p in platforms:
            try:
                if p == Platform.AMAZON:
                    items = self.amazon.get_bestsellers(category_id=keyword, limit=limit)
                    results[p.value] = items.items
                elif p in (Platform.TAOBAO, Platform.TMALL):
                    results[p.value] = self.taobao.search_products(keyword=keyword, limit=limit)
                elif p == Platform.JD:
                    results[p.value] = self.jd.search_products(keyword=keyword, limit=limit)
                elif p == Platform.PINDUODUO:
                    results[p.value] = self.pdd.search_products(keyword=keyword, limit=limit)
                elif p == Platform.DOUYIN:
                    results[p.value] = f"Douyin {keyword} — GPM/Content model available"
                elif p == Platform.XIAOHONGSHU:
                    results[p.value] = f"XHS {keyword} — Note engagement/KOL model available"
                    results[p.value] = self.jd.search_products(keyword=keyword, limit=limit)
                elif p == Platform.PINDUODUO:
                    results[p.value] = self.pdd.search_products(keyword=keyword, limit=limit)
                elif p == Platform.DOUYIN:
                    results[p.value] = f"Douyin {keyword} — GPM/Content model available (no page scraping)"
            except NotImplementedError:
                results[p.value] = []
            except Exception as e:
                results[p.value] = f"Error: {e}"
        return results

    def take_pdd_sales_snapshot(self, keyword: str, limit: int = 20):
        items = self.pdd.search_products(keyword=keyword, limit=limit)
        self.pdd.take_sales_snapshot(items)

    def analyze_pdd_price_competition(self, keyword: str, limit: int = 20) -> dict:
        items = self.pdd.search_products(keyword=keyword, limit=limit)
        return self.pdd.analyze_price_competition(items)

    def analyze_douyin_live(self, avg_viewers: int, duration_minutes: int, gpm: Optional[float] = None) -> dict:
        return self.douyin.estimate_live_gmv(avg_viewers, duration_minutes, gpm)

    def analyze_douyin_video_funnel(self, views: int, completion: float, interaction: float, click: float, cvr: float) -> dict:
        return self.douyin.analyze_short_video(views, completion, interaction, click, cvr)

    def close(self):
        for client in [self._amazon, self._taobao, self._jd, self._pdd, self._douyin, self._xhs]:
            if client:
                client.close()

    def analyze_xhs_note(self, views: int, likes: int, collects: int, comments: int, shares: int, **kwargs) -> dict:
        return self.xhs.analyze_note_performance(views, likes, collects, comments, shares, **kwargs)

    def analyze_xhs_kol(self, followers: int, avg_views: int, avg_likes: int, avg_collects: int, total_notes: int, **kwargs) -> dict:
        return self.xhs.analyze_kol_profile(followers, avg_views, avg_likes, avg_collects, total_notes, **kwargs)

    def model_xhs_campaign(self, budget: float, kol_count: int, avg_kol_followers: int, avg_kol_views: int, avg_engagement: float, product_price: float, **kwargs) -> dict:
        return self.xhs.model_brand_campaign(budget, kol_count, avg_kol_followers, avg_kol_views, avg_engagement, product_price, **kwargs)