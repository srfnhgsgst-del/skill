from typing import Optional
import re

from bs4 import BeautifulSoup, Tag

from ecommerce_ops_skill.platform import Platform, DataSource
from ecommerce_ops_skill.models import (
    RankingItem,
    SalesEstimate,
    KeywordData,
)


from ecommerce_ops_skill.http_client import BaseHttpClient


class TaobaoClient(BaseHttpClient):
    """淘宝/天猫 搜索排名解析 + 热销榜 + 销量估算"""

    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def __init__(self, timeout: float = 30.0):
        super().__init__(timeout=timeout)

    def search_products(
        self,
        keyword: str,
        limit: int = 40,
        sort: str = "default",
    ) -> list[RankingItem]:
        sort_map = {
            "default": "default",
            "sales": "sale-desc",
            "price_asc": "price-asc",
            "price_desc": "price-desc",
            "credit": "credit-desc",
        }
        sort_param = sort_map.get(sort, sort)

        url = f"https://s.taobao.com/search?q={keyword}&sort={sort_param}"
        response = self.client.get(url)
        response.raise_for_status()

        return self._parse_search_results(response.text, keyword, limit)

    def search_tmall(
        self,
        keyword: str,
        limit: int = 40,
    ) -> list[RankingItem]:
        url = f"https://list.tmall.com/search_product.htm?q={keyword}"
        response = self.client.get(url)
        response.raise_for_status()

        return self._parse_tmall_results(response.text, keyword, limit)

    def _parse_search_results(self, html: str, keyword: str, limit: int) -> list[RankingItem]:
        soup = BeautifulSoup(html, "lxml")
        items: list[RankingItem] = []
        rank = 0

        item_selectors = [
            ".item.J_MouserOnverReq",
            "[data-category=\"auctions\"] .item",
            ".grid-item .item-container",
            "[class*=\"item\"] .title a",
        ]

        card = None
        cards: list[Tag] = []
        for sel in item_selectors:
            matched = soup.select(sel)
            if matched:
                cards = matched
                break

        for card in cards:
            rank += 1
            if rank > limit:
                break

            try:
                title_tag = card.select_one(
                    ".title a, .J_ClickStat, a[title], h3 a, [class*=\"title\"] a"
                )
                title = ""
                if title_tag:
                    title = title_tag.get("title", "") or title_tag.get_text(strip=True)

                price_tag = card.select_one(
                    ".price em, .price strong, .price .num, [class*=\"price\"] span, [class*=\"price\"]"
                )
                price_text = price_tag.get_text(strip=True) if price_tag else ""
                price = self._extract_price(price_text)

                sales_tag = card.select_one(
                    ".deal-cnt, .sale, [class*=\"sale\"], [class*=\"deal\"], .sales-amount"
                )
                sales_text = sales_tag.get_text(strip=True) if sales_tag else ""
                monthly_sales = self._extract_monthly_sales(sales_text)

                shop_tag = card.select_one(
                    ".shopname, .seller, [class*=\"shop\"] span, [class*=\"shop\"] a"
                )
                shop_name = shop_tag.get_text(strip=True) if shop_tag else ""

                tmall_icon = card.select_one(".tmall-icon, .icon-tmall, [class*=\"tmall\"]")
                is_tmall = tmall_icon is not None

                location_tag = card.select_one(".location, .item-location")
                _ = location_tag.get_text(strip=True) if location_tag else ""

                img_tag = card.select_one("img[data-src], img[src]")
                img_url = ""
                if img_tag:
                    img_url = img_tag.get("data-src", "") or img_tag.get("src", "")

                item_id = ""
                data_id = card.get("data-id", "") or card.get("data-nid", "")
                if data_id:
                    item_id = data_id

                items.append(RankingItem(
                    platform=Platform.TMALL if is_tmall else Platform.TAOBAO,
                    rank=rank,
                    asin_or_id=item_id or f"{keyword}-{rank}",
                    title=title[:200] if title else f"{keyword} #{rank}",
                    price=price,
                    currency="CNY",
                    rating=None,
                    review_count=monthly_sales,
                    image_url=img_url or "",
                    product_url=f"https://item.taobao.com/item.htm?id={item_id}" if item_id else "",
                    brand=shop_name,
                    category=keyword,
                    data_source=DataSource.WEB_SCRAPING,
                ))
            except Exception:
                continue

        return items

    def _parse_tmall_results(self, html: str, keyword: str, limit: int) -> list[RankingItem]:
        soup = BeautifulSoup(html, "lxml")
        items: list[RankingItem] = []
        rank = 0

        cards = soup.select(".product, .product-item, .item, [class*=\"product\"]")
        for card in cards:
            rank += 1
            if rank > limit:
                break
            try:
                title_tag = card.select_one(".productTitle, .product-title, a[title]")
                title = title_tag.get("title", "") or title_tag.get_text(strip=True) if title_tag else ""

                price_tag = card.select_one(".productPrice, .product-price, [class*=\"price\"]")
                price_text = price_tag.get_text(strip=True) if price_tag else ""
                price = self._extract_price(price_text)

                sales_tag = card.select_one(".productStatus, .product-sales, [class*=\"sales\"]")
                sales_text = sales_tag.get_text(strip=True) if sales_tag else ""
                monthly_sales = self._extract_monthly_sales(sales_text)

                shop_tag = card.select_one(".productShop, .product-shop, [class*=\"shop\"]")
                shop_name = shop_tag.get_text(strip=True) if shop_tag else ""

                items.append(RankingItem(
                    platform=Platform.TMALL,
                    rank=rank,
                    asin_or_id=f"tmall-{keyword}-{rank}",
                    title=title[:200] if title else f"Tmall #{rank}",
                    price=price,
                    currency="CNY",
                    review_count=monthly_sales,
                    brand=shop_name,
                    category=keyword,
                    data_source=DataSource.WEB_SCRAPING,
                ))
            except Exception:
                continue

        return items

    def get_hot_keywords(self, category: str = "") -> list[KeywordData]:
        url = "https://re.taobao.com/search"
        try:
            response = self.client.get(url)
            response.raise_for_status()
        except Exception:
            return self._default_hot_keywords()

        soup = BeautifulSoup(response.text, "lxml")
        keywords: list[KeywordData] = []

        kw_tags = soup.select("[class*=\"hot\"], [class*=\"keyword\"], [class*=\"tag\"]")
        for tag in kw_tags:
            text = tag.get_text(strip=True)
            if text and len(text) >= 2:
                keywords.append(KeywordData(
                    keyword=text,
                    platform=Platform.TAOBAO,
                ))

        return keywords if keywords else self._default_hot_keywords()

    def estimate_sales_from_display(
        self,
        monthly_sales_display: int,
        price: float,
        category: str = "",
    ) -> SalesEstimate:
        confidence = 0.7
        estimated_monthly_revenue = monthly_sales_display * price

        return SalesEstimate(
            asin="",
            platform=Platform.TAOBAO,
            estimated_daily_sales=int(monthly_sales_display / 30),
            estimated_monthly_sales=monthly_sales_display,
            estimated_monthly_revenue=estimated_monthly_revenue,
            confidence_level=confidence,
            estimation_method="displayed_monthly_sales",
            data_source=DataSource.MODEL_ESTIMATION,
        )

    def analyze_shop_from_search(self, items: list[RankingItem]) -> dict:
        shop_counts: dict[str, int] = {}
        for item in items:
            brand = item.brand if item.brand else "(unknown)"
            shop_counts[brand] = shop_counts.get(brand, 0) + 1

        prices = [i.price for i in items if i.price and i.price > 0]
        avg_price = sum(prices) / len(prices) if prices else 0

        return {
            "total_items": len(items),
            "avg_price_cny": round(avg_price, 2),
            "price_range": (min(prices), max(prices)) if len(prices) >= 2 else None,
            "top_shops": sorted(shop_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            "shop_count": len(shop_counts),
            "keyword_concentration": round(max(shop_counts.values()) / len(items), 2) if items else 0,
        }

    @staticmethod
    def _extract_price(text: str) -> Optional[float]:
        if not text:
            return None
        match = re.search(r"(\d+\.?\d*)", text.replace(",", ""))
        return float(match.group(1)) if match else None

    @staticmethod
    def _extract_monthly_sales(text: str) -> Optional[int]:
        if not text:
            return None

        if "万" in text or "万+" in text:
            match = re.search(r"(\d+\.?\d*)", text)
            if match:
                return int(float(match.group(1)) * 10000)

        match = re.search(r"(\d+)", text.replace(",", ""))
        return int(match.group(1)) if match else None

    @staticmethod
    def _default_hot_keywords() -> list[KeywordData]:
        defaults = [
            "连衣裙", "T恤", "手机壳", "充电宝", "耳机",
            "零食", "面膜", "收纳盒", "水杯", "拖鞋",
        ]
        return [KeywordData(keyword=k, platform=Platform.TAOBAO) for k in defaults]


class TaobaoSalesEstimator:
    """淘宝/天猫 销量估算器 —— 基于月销量显示 + 价格 + 店铺层级"""

    def estimate_monthly_gmv(self, monthly_sales: int, avg_price: float) -> float:
        return monthly_sales * avg_price

    def estimate_daily_orders(self, monthly_sales: int) -> int:
        return max(0, int(monthly_sales / 30))

    def estimate_conversion(
        self,
        monthly_sales: int,
        avg_visits_per_day: int = 200,
    ) -> float:
        daily_orders = self.estimate_daily_orders(monthly_sales)
        if avg_visits_per_day <= 0:
            return 0.0
        return daily_orders / avg_visits_per_day

    def rank_shop_competitiveness(
        self,
        shop_sales: int,
        shop_dsr: list[float],
        shop_age_days: int,
    ) -> str:
        dsr_avg = sum(shop_dsr) / len(shop_dsr) if shop_dsr else 0

        if shop_sales >= 10000 and dsr_avg >= 4.8 and shop_age_days > 365:
            return "top"
        elif shop_sales >= 3000 and dsr_avg >= 4.6:
            return "upper"
        elif shop_sales >= 500 and dsr_avg >= 4.4:
            return "middle"
        else:
            return "entry"