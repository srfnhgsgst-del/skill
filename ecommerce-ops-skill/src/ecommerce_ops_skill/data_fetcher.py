from typing import Optional

from ecommerce_ops_skill.platform import Platform, AmazonDomain
from ecommerce_ops_skill.models import BestSellerList, ProductDetail, SalesEstimate
from ecommerce_ops_skill.amazon import AmazonClient, AmazonSalesEstimator


class DataFetcher:
    """统一数据获取入口，根据平台路由到对应的数据源模块"""

    def __init__(self, amazon_domain: AmazonDomain = AmazonDomain.US, timeout: float = 30.0):
        self._amazon: Optional[AmazonClient] = None
        self._amazon_estimator: Optional[AmazonSalesEstimator] = None
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

    def get_bestsellers(
        self,
        platform: Platform = Platform.AMAZON,
        category_id: str = "zgbs",
        limit: int = 100,
    ) -> BestSellerList:
        if platform == Platform.AMAZON:
            return self.amazon.get_bestsellers(category_id=category_id, limit=limit)
        else:
            raise NotImplementedError(f"Platform {platform} is not yet supported in v0.1")

    def get_product_detail(self, platform: Platform, product_id: str) -> ProductDetail:
        if platform == Platform.AMAZON:
            return self.amazon.get_product_detail(asin=product_id)
        else:
            raise NotImplementedError(f"Platform {platform} is not yet supported in v0.1")

    def get_products_batch(self, platform: Platform, product_ids: list[str]) -> list[ProductDetail]:
        if platform == Platform.AMAZON:
            return self.amazon.get_products_batch(asins=product_ids)
        else:
            raise NotImplementedError(f"Platform {platform} is not yet supported in v0.1")

    def estimate_sales(
        self,
        platform: Platform,
        bsr: int = 0,
        product_id: str = "",
        review_count: int = 0,
        days_since_first_review: int = 0,
    ) -> SalesEstimate:
        if platform == Platform.AMAZON:
            if bsr > 0:
                return self.amazon_estimator.estimate_daily_sales(product_id, bsr)
            elif review_count > 0 and days_since_first_review > 0:
                est = self.amazon_estimator.estimate_from_review_velocity(
                    review_count, days_since_first_review
                )
                return SalesEstimate(
                    asin=product_id,
                    platform=Platform.AMAZON,
                    estimated_daily_sales=est,
                    estimated_monthly_sales=est * 30,
                    estimation_method="review_velocity",
                )
            else:
                return SalesEstimate(
                    asin=product_id,
                    platform=Platform.AMAZON,
                    confidence_level=0.0,
                )
        else:
            raise NotImplementedError(f"Platform {platform} is not yet supported in v0.1")

    def get_amazon_categories(self) -> list[dict]:
        return self.amazon.get_category_list()

    def close(self):
        if self._amazon:
            self._amazon.close()
