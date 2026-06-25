from typing import Optional
import re

from bs4 import BeautifulSoup

from ecommerce_ops_skill.platform import Platform, RankingPeriod, DataSource
from ecommerce_ops_skill.models import (
    RankingItem,
    BestSellerList,
    SalesEstimate,
)


from ecommerce_ops_skill.http_client import BaseHttpClient


class JDClient(BaseHttpClient):
    """京东 搜索排名解析 + 热销榜 + 自营vs.POP分析"""

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
        limit: int = 60,
        sort: str = "default",
    ) -> list[RankingItem]:
        sort_params = {
            "default": "",
            "sales": "&psort=3",
            "price_asc": "&psort=1",
            "price_desc": "&psort=2",
            "comments": "&psort=4",
        }
        sort_param = sort_params.get(sort, "")

        url = f"https://search.jd.com/Search?keyword={keyword}&enc=utf-8{sort_param}"
        response = self.client.get(url)
        response.raise_for_status()

        return self._parse_search_results(response.text, keyword, limit)

    def _parse_search_results(self, html: str, keyword: str, limit: int) -> list[RankingItem]:
        soup = BeautifulSoup(html, "lxml")
        items: list[RankingItem] = []
        rank = 0

        cards = soup.select(".gl-item, li[data-sku], .goods-list li, .gl-warp li")
        if not cards:
            cards = soup.select("[data-sku]")

        for card in cards:
            rank += 1
            if rank > limit:
                break
            try:
                title_tag = card.select_one(
                    ".p-name a em, .p-name-type-2, [class*=\"name\"] a, .p-name a"
                )
                title = ""
                if title_tag:
                    title = title_tag.get("title", "") or title_tag.get_text(strip=True)

                price_tag = card.select_one(
                    ".p-price strong i, .p-price i, .J_price, [class*=\"price\"] strong, [class*=\"price\"] i"
                )
                price_text = price_tag.get_text(strip=True) if price_tag else ""
                price = self._extract_price(price_text)

                comment_tag = card.select_one(
                    ".p-commit a, .p-commit strong, [class*=\"commit\"] a, .p-review"
                )
                comment_text = comment_tag.get_text(strip=True) if comment_tag else ""
                comment_count = self._extract_number(comment_text)

                shop_tag = card.select_one(
                    ".p-shopnum a, .p-shopnum, [class*=\"shop\"] a, .curr-shop"
                )
                shop_name = shop_tag.get_text(strip=True) if shop_tag else ""
                if not shop_name:
                    shop_data = card.select_one("[data-shop_name], [data-shopname]")
                    if shop_data:
                        shop_name = shop_data.get("data-shop_name", "") or shop_data.get("data-shopname", "")

                is_jd_self = (
                    card.select_one("[class*=\"jd-ziying\"], .goods-icons i, [class*=\"self\"]")
                    is not None
                )
                if not is_jd_self:
                    jd_icon_text = str(card)
                    if "自营" in jd_icon_text:
                        is_jd_self = True

                data_sku = card.get("data-sku", "")
                img_tag = card.select_one("img[data-lazy-img], img[src]")
                img_url = ""
                if img_tag:
                    img_url = img_tag.get("data-lazy-img", "") or img_tag.get("src", "")

                items.append(RankingItem(
                    platform=Platform.JD,
                    rank=rank,
                    asin_or_id=data_sku or f"jd-{keyword}-{rank}",
                    title=title[:200] if title else f"JD Result #{rank}",
                    price=price,
                    currency="CNY",
                    rating=None,
                    review_count=comment_count,
                    image_url=img_url or "",
                    product_url=f"https://item.jd.com/{data_sku}.html" if data_sku else "",
                    brand=shop_name,
                    category=keyword,
                    is_bestseller=is_jd_self,
                    data_source=DataSource.WEB_SCRAPING,
                ))
            except Exception:
                continue

        return items

    def get_bestsellers(
        self,
        category_id: str = "",
        limit: int = 100,
    ) -> BestSellerList:
        url = "https://www.jd.com/phb/zhishi/"
        if category_id:
            url = f"https://www.jd.com/phb/zhishi/{category_id}.html"

        response = self.client.get(url)
        response.raise_for_status()

        items = self._parse_ranking_page(response.text, limit)

        return BestSellerList(
            platform=Platform.JD,
            category_id=category_id or "zhishi",
            category_name="京东排行榜",
            items=items,
            period=RankingPeriod.DAILY,
            total_items=limit,
        )

    def _parse_ranking_page(self, html: str, limit: int) -> list[RankingItem]:
        soup = BeautifulSoup(html, "lxml")
        items: list[RankingItem] = []
        rank = 0

        card_selectors = [
            ".floor-list li",
            ".mc-tab-con li",
            ".i_big_item",
            "[class*=\"rank\"] li",
            "li[data-sku]",
        ]

        for selector in card_selectors:
            cards = soup.select(selector)
            if cards:
                for card in cards:
                    rank += 1
                    if rank > limit:
                        break
                    try:
                        title_tag = card.select_one("[class*=\"name\"], [class*=\"title\"], a")
                        title = ""
                        if title_tag:
                            title = title_tag.get("title", "") or title_tag.get_text(strip=True)

                        price_tag = card.select_one("[class*=\"price\"], [class*=\"num\"]")
                        price_text = price_tag.get_text(strip=True) if price_tag else ""
                        price = self._extract_price(price_text)

                        data_sku = card.get("data-sku", "")

                        items.append(RankingItem(
                            platform=Platform.JD,
                            rank=rank,
                            asin_or_id=data_sku or f"jd-rank-{rank}",
                            title=title[:200],
                            price=price,
                            currency="CNY",
                            data_source=DataSource.WEB_SCRAPING,
                        ))
                    except Exception:
                        continue
                break

        return items

    def analyze_competition(self, items: list[RankingItem]) -> dict:
        jd_self_items = [i for i in items if i.is_bestseller]
        pop_items = [i for i in items if not i.is_bestseller]

        prices = [i.price for i in items if i.price and i.price > 0]
        comments = [i.review_count for i in items if i.review_count]

        return {
            "total_items": len(items),
            "jd_self_count": len(jd_self_items),
            "pop_count": len(pop_items),
            "jd_self_ratio": round(len(jd_self_items) / len(items), 2) if items else 0,
            "avg_price_cny": round(sum(prices) / len(prices), 2) if prices else 0,
            "avg_comments": int(sum(comments) / len(comments)) if comments else 0,
            "price_range": (min(prices), max(prices)) if len(prices) >= 2 else None,
            "advice": self._competition_advice(len(jd_self_items), len(items)),
        }

    def estiamte_from_comments(self, comment_count: int, days_since_launch: int = 365) -> SalesEstimate:
        if days_since_launch <= 0:
            days_since_launch = 365

        comment_rate = 0.025
        daily_sales_est = max(0, int(comment_count / days_since_launch / comment_rate))

        return SalesEstimate(
            asin="",
            platform=Platform.JD,
            estimated_daily_sales=daily_sales_est,
            estimated_monthly_sales=daily_sales_est * 30,
            confidence_level=0.4,
            estimation_method="comment_based",
            data_source=DataSource.MODEL_ESTIMATION,
        )

    @staticmethod
    def _extract_price(text: str) -> Optional[float]:
        if not text:
            return None
        match = re.search(r"(\d+\.?\d*)", text.replace(",", "").replace("￥", "").replace("¥", ""))
        return float(match.group(1)) if match else None

    @staticmethod
    def _extract_number(text: str) -> Optional[int]:
        if not text:
            return None

        text = text.replace("+", "").replace("万", "0000").replace("条评价", "").replace("评价", "")
        match = re.search(r"(\d+\.?\d*)", text.replace(",", ""))

        if not match:
            return None

        val = float(match.group(1))
        return int(val)

    @staticmethod
    def _competition_advice(jd_self_count: int, total: int) -> str:
        if total == 0:
            return "No data"
        ratio = jd_self_count / total
        if ratio > 0.6:
            return "JD self-operated dominates this category — difficult for POP sellers"
        elif ratio > 0.3:
            return "Moderate competition from JD self-operated — differentiate with pricing/service"
        else:
            return "POP-friendly category — low JD self-operated presence"


class JDCategoryRanking:
    """京东类目排行榜解析 —— 模拟京东商智行业分析"""

    CATEGORY_MAP = {
        "phone": "手机",
        "computer": "电脑办公",
        "appliance": "家用电器",
        "food": "食品饮料",
        "cosmetic": "个护化妆",
        "baby": "母婴",
        "fashion": "服饰内衣",
        "shoes": "鞋靴",
        "home": "家居家装",
        "auto": "汽车用品",
        "book": "图书文娱",
        "sport": "运动户外",
    }

    @classmethod
    def get_category_name(cls, category_key: str) -> str:
        return cls.CATEGORY_MAP.get(category_key, category_key)

    @classmethod
    def list_categories(cls) -> list[dict]:
        return [
            {"key": k, "name": v} for k, v in cls.CATEGORY_MAP.items()
        ]