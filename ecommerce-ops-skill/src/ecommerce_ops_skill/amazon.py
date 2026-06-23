from datetime import datetime
from typing import Optional

import httpx

from ecommerce_ops_skill.platform import Platform, AmazonDomain, RankingPeriod
from ecommerce_ops_skill.models import (
    BestSellerList,
    ProductDetail,
    SalesEstimate,
    BSRHistory,
    DataSource,
)
from ecommerce_ops_skill.rank_parser import RankParser


class AmazonClient:
    """Amazon 销量榜单读取客户端，覆盖 BSR 榜单、产品详情、销量估算"""

    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
    }

    def __init__(self, domain: AmazonDomain = AmazonDomain.US, timeout: float = 30.0):
        self.domain = domain
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

    def get_bestsellers(
        self,
        category_id: str = "zgbs",
        limit: int = 100,
    ) -> BestSellerList:
        url = f"https://{self.domain.value}/Best-Sellers/{category_id}/zgbs"
        if category_id == "zgbs":
            url = f"https://{self.domain.value}/Best-Sellers/zgbs"

        response = self.client.get(url)
        response.raise_for_status()

        items = RankParser.parse_amazon_bestsellers(
            response.text,
            domain=self.domain,
            category=category_id,
            limit=limit,
        )

        category_name = self._extract_category_name(response.text)

        return BestSellerList(
            platform=Platform.AMAZON,
            category_id=category_id,
            category_name=category_name,
            amazon_domain=self.domain,
            items=items,
            period=RankingPeriod.HOURLY,
            total_items=limit,
        )

    def get_bestsellers_by_department(
        self,
        department_url: str,
        limit: int = 100,
    ) -> BestSellerList:
        full_url = f"https://{self.domain.value}{department_url}"
        if full_url.startswith("http"):
            pass
        else:
            full_url = f"https://{self.domain.value}{department_url}"

        response = self.client.get(full_url)
        response.raise_for_status()

        items = RankParser.parse_amazon_bestsellers(
            response.text,
            domain=self.domain,
            category=department_url,
            limit=limit,
        )

        category_name = self._extract_category_name(response.text)

        return BestSellerList(
            platform=Platform.AMAZON,
            category_id=department_url,
            category_name=category_name,
            amazon_domain=self.domain,
            items=items,
            period=RankingPeriod.HOURLY,
            total_items=limit,
        )

    def get_product_detail(self, asin: str) -> ProductDetail:
        url = f"https://{self.domain.value}/dp/{asin}"
        response = self.client.get(url)
        response.raise_for_status()

        raw_data = RankParser.parse_amazon_product_page(response.text, self.domain)

        bsr = self._extract_bsr(raw_data.get("bsr_text", ""))
        rating = self._extract_rating(raw_data.get("rating_text", ""))
        review_count = self._extract_review_count(raw_data.get("review_count_text", ""))
        availability = raw_data.get("availability", "unknown")
        seller = self._extract_seller_info(raw_data.get("seller_info", ""))

        return ProductDetail(
            platform=Platform.AMAZON,
            asin_or_id=asin,
            title=raw_data.get("title", ""),
            brand=raw_data.get("brand"),
            price=raw_data.get("price"),
            currency=raw_data.get("currency_symbol", "USD"),
            rating=rating,
            review_count=review_count,
            bsr=bsr,
            bsr_category=raw_data.get("bsr_text"),
            buy_box_owner=seller,
            availability=availability,
            images=raw_data.get("images", []),
            features=raw_data.get("features", []),
            data_source=DataSource.WEB_SCRAPING,
        )

    def get_products_batch(self, asins: list[str]) -> list[ProductDetail]:
        results: list[ProductDetail] = []
        for asin in asins:
            try:
                detail = self.get_product_detail(asin)
                results.append(detail)
            except Exception as e:
                results.append(ProductDetail(
                    platform=Platform.AMAZON,
                    asin_or_id=asin,
                    title=f"[ERROR] {e}",
                    availability="error",
                ))
        return results

    def estimate_sales_from_bsr(self, bsr: int, category: str = "general") -> SalesEstimate:
        if bsr <= 0:
            return SalesEstimate(asin="", platform=Platform.AMAZON, confidence_level=0.0)

        if bsr <= 100:
            daily = max(10, int(1000000 / bsr * 0.03))
        elif bsr <= 1000:
            daily = max(5, int(1000000 / bsr * 0.02))
        elif bsr <= 10000:
            daily = max(2, int(1000000 / bsr * 0.015))
        elif bsr <= 50000:
            daily = max(1, int(1000000 / bsr * 0.01))
        elif bsr <= 100000:
            daily = max(0, int(1000000 / bsr * 0.005))
        else:
            daily = 0

        confidence = 0.85 if bsr <= 100 else (0.6 if bsr <= 1000 else 0.4)

        return SalesEstimate(
            asin="",
            platform=Platform.AMAZON,
            estimated_daily_sales=daily,
            estimated_monthly_sales=daily * 30,
            sales_rank_30d=bsr,
            confidence_level=confidence,
            estimation_method="bsr_correlation_v0.1",
        )

    def get_category_list(self) -> list[dict]:
        url = f"https://{self.domain.value}/Best-Sellers/zgbs"
        response = self.client.get(url)
        response.raise_for_status()

        categories = self._extract_categories(response.text)
        return categories

    def _extract_category_name(self, html: str) -> str:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        title_tag = soup.select_one("#zg_banner_text, .zg-banner-text, h1")
        if title_tag:
            return title_tag.get_text(strip=True)
        return "Unknown Category"

    def _extract_bsr(self, bsr_text: str) -> Optional[int]:
        import re
        match = re.search(r"#([\d,]+)", bsr_text)
        if match:
            return int(match.group(1).replace(",", ""))
        return None

    def _extract_rating(self, rating_text: str) -> Optional[float]:
        import re
        match = re.search(r"(\d+\.?\d*)", rating_text)
        if match:
            return float(match.group(1))
        return None

    def _extract_review_count(self, review_text: str) -> Optional[int]:
        import re
        match = re.search(r"([\d,]+)", review_text)
        if match:
            return int(match.group(1).replace(",", ""))
        return None

    def _extract_seller_info(self, seller_text: str) -> Optional[str]:
        if not seller_text:
            return None
        text = seller_text.strip()
        text = text.replace("Sold by ", "").replace("Ships from ", "")
        text = text.replace("Fulfilled by ", "")
        return text[:100] if len(text) > 100 else text

    def _extract_categories(self, html: str) -> list[dict]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")
        categories: list[dict] = []

        cat_links = soup.select("#zg_browseRoot ul li a, .zg_browseUp a, .zg_browseRoot a")
        seen: set[str] = set()
        for link in cat_links:
            href = link.get("href", "")
            name = link.get_text(strip=True)
            if name and href not in seen:
                seen.add(href)
                categories.append({"name": name, "url": href})

        return categories


class AmazonSalesEstimator:
    """基于 BSR 和相关信号的销量估算器，模拟 Jungle Scout/Keepa 的数据模型"""

    BSR_SALES_TABLE = {
        range(1, 101): 30,
        range(101, 501): 15,
        range(501, 1001): 10,
        range(1001, 5001): 5,
        range(5001, 10001): 2,
        range(10001, 20001): 1,
        range(20001, 50001): 0.5,
        range(50001, 100001): 0.2,
    }

    def __init__(self):
        self._bsr_history: dict[str, list[BSRHistory]] = {}

    def add_bsr_snapshot(self, asin: str, bsr: int, category: str):
        if asin not in self._bsr_history:
            self._bsr_history[asin] = []
        self._bsr_history[asin].append(BSRHistory(
            asin=asin,
            category=category,
            rank=bsr,
            timestamp=datetime.now(),
        ))

    def estimate_daily_sales(self, asin: str, bsr: int) -> SalesEstimate:
        daily = 0
        for rank_range, estimate in self.BSR_SALES_TABLE.items():
            if bsr in rank_range:
                daily = estimate
                break

        if bsr > 100000:
            daily = 0
        elif bsr == 0:
            daily = 0

        history = self._bsr_history.get(asin, [])
        trend = self._calculate_trend(history)

        return SalesEstimate(
            asin=asin,
            platform=Platform.AMAZON,
            estimated_daily_sales=daily,
            estimated_monthly_sales=daily * 30,
            estimated_monthly_revenue=None,
            sales_rank_30d=bsr,
            sales_trend=trend,
            confidence_level=0.6 if len(history) >= 3 else 0.3,
            estimation_method="bsr_correlation_table",
        )

    def estimate_from_review_velocity(
        self,
        review_count: int,
        days_since_first_review: int,
        category_avg_review_rate: float = 0.02,
    ) -> int:
        if days_since_first_review <= 0:
            return 0
        reviews_per_day = review_count / days_since_first_review
        estimated_sales_per_day = reviews_per_day / category_avg_review_rate
        return int(estimated_sales_per_day)

    @staticmethod
    def _calculate_trend(history: list[BSRHistory]) -> Optional[str]:
        if len(history) < 2:
            return None
        first = history[0].rank
        last = history[-1].rank
        if last < first * 0.8:
            return "rising"
        elif last > first * 1.2:
            return "falling"
        return "stable"
