from datetime import datetime
from typing import Optional
import re
import httpx

from bs4 import BeautifulSoup, Tag

from ecommerce_ops_skill.platform import Platform, DataSource
from ecommerce_ops_skill.models import (
    RankingItem,
    SalesEstimate,
    KeywordData,
)


class PinduoduoClient:
    """拼多多 搜索排名解析 + 已拼件数差值法销量估算 + 价格竞争分析"""

    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    CATEGORY_MAP = {
        "phone": "手机",
        "appliance": "家电",
        "clothing": "服饰",
        "food": "食品",
        "baby": "母婴",
        "cosmetic": "美妆",
        "home": "家居",
        "shoes": "鞋包",
        "sport": "运动",
        "digital": "数码",
        "car": "汽配",
        "book": "图书",
    }

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self._client: Optional[httpx.Client] = None
        self._sales_snapshots: dict[str, list[dict]] = {}

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

    def search_products(
        self,
        keyword: str,
        limit: int = 40,
        sort: str = "default",
    ) -> list[RankingItem]:
        sort_params = {
            "default": "default",
            "sales": "_sale",
            "price_asc": "price",
            "price_desc": "price",
        }
        sort_val = sort_params.get(sort, "default")
        url = f"https://mobile.yangkeduo.com/search_result.html?search_key={keyword}&order={sort_val}"
        response = self.client.get(url)
        response.raise_for_status()

        return self._parse_search_results(response.text, keyword, limit)

    def _parse_search_results(self, html: str, keyword: str, limit: int) -> list[RankingItem]:
        soup = BeautifulSoup(html, "lxml")
        items: list[RankingItem] = []
        rank = 0

        card_selectors = [
            "[data-active=\"goods\"]",
            ".goods-list .goods-item",
            "[class*=\"goods\"]",
            ".search-result-item",
        ]

        cards: list[Tag] = []
        for sel in card_selectors:
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
                    ".goods-title, [class*=\"title\"] span, [class*=\"title\"], .name"
                )
                title = ""
                if title_tag:
                    title = title_tag.get("title", "") or title_tag.get_text(strip=True)

                price_tag = card.select_one(
                    ".goods-price, [class*=\"price\"] span, [class*=\"price\"]"
                )
                price_text = price_tag.get_text(strip=True) if price_tag else ""
                price = self._extract_price(price_text)

                sales_tag = card.select_one(
                    ".goods-sales, .sales, [class*=\"sales\"]"
                )
                sales_text = sales_tag.get_text(strip=True) if sales_tag else ""
                sales = self._extract_pdd_sales(sales_text)

                shop_tag = card.select_one(
                    ".mall-name, [class*=\"shop\"], .goods-mall"
                )
                shop = shop_tag.get_text(strip=True) if shop_tag else ""

                data_goods_id = card.get("data-goods-id", "") or card.get("data-pid", "")

                is_mall = card.select_one("[class*=\"mall\"], .pdd-brand") is not None

                img_tag = card.select_one("img[src], img[data-src]")
                img_url = ""
                if img_tag:
                    img_url = img_tag.get("data-src", "") or img_tag.get("src", "")

                items.append(RankingItem(
                    platform=Platform.PINDUODUO,
                    rank=rank,
                    asin_or_id=data_goods_id or f"pdd-{keyword}-{rank}",
                    title=title[:200] if title else f"PDD #{rank}",
                    price=price,
                    currency="CNY",
                    review_count=sales,
                    image_url=img_url or "",
                    brand=shop if shop else ("旗舰店" if is_mall else "个人店"),
                    category=keyword,
                    is_bestseller=is_mall,
                    data_source=DataSource.WEB_SCRAPING,
                ))
            except Exception:
                continue

        return items

    def take_sales_snapshot(self, items: list[RankingItem]):
        now = datetime.now()
        for item in items:
            key = item.asin_or_id
            if key not in self._sales_snapshots:
                self._sales_snapshots[key] = []
            self._sales_snapshots[key].append({
                "timestamp": now,
                "total_sales": item.review_count,
            })

    def estimate_sales_from_snapshots(self, goods_id: str) -> SalesEstimate:
        snaps = self._sales_snapshots.get(goods_id, [])
        if len(snaps) < 2:
            return SalesEstimate(
                asin=goods_id,
                platform=Platform.PINDUODUO,
                confidence_level=0.0,
                estimation_method="snapshot_difference",
            )

        snaps_sorted = sorted(snaps, key=lambda s: s["timestamp"])
        first = snaps_sorted[0]
        last = snaps_sorted[-1]

        first_sales = first["total_sales"] or 0
        last_sales = last["total_sales"] or 0

        hours_diff = (last["timestamp"] - first["timestamp"]).total_seconds() / 3600
        if hours_diff <= 0:
            hours_diff = 1

        sales_increment = last_sales - first_sales
        daily_est = max(0, int(sales_increment / hours_diff * 24))

        confidence = 0.6 if len(snaps) >= 4 else (0.35 if len(snaps) >= 2 else 0.15)

        return SalesEstimate(
            asin=goods_id,
            platform=Platform.PINDUODUO,
            estimated_daily_sales=daily_est,
            estimated_monthly_sales=daily_est * 30,
            confidence_level=confidence,
            estimation_method="snapshot_difference_v0.1",
            data_source=DataSource.MODEL_ESTIMATION,
        )

    def analyze_price_competition(self, items: list[RankingItem]) -> dict:
        prices = [i.price for i in items if i.price and i.price > 0]
        if not prices:
            return {"error": "No price data"}

        sorted_prices = sorted(prices)
        median_idx = len(sorted_prices) // 2

        quartiles = {
            "min": sorted_prices[0],
            "q1": sorted_prices[len(sorted_prices) // 4],
            "median": sorted_prices[median_idx],
            "q3": sorted_prices[len(sorted_prices) * 3 // 4],
            "max": sorted_prices[-1],
        }

        avg = sum(prices) / len(prices)
        lowest_prices = sorted_prices[:max(5, len(sorted_prices) // 10)]
        gap_to_lowest = avg - sum(lowest_prices) / len(lowest_prices)

        competitive_pressure = "high" if gap_to_lowest < avg * 0.1 else ("medium" if gap_to_lowest < avg * 0.3 else "low")

        mall_count = sum(1 for i in items if i.is_bestseller)

        return {
            "total_items": len(items),
            "price_stats": quartiles,
            "avg_price_cny": round(avg, 2),
            "price_competition_pressure": competitive_pressure,
            "top5_lowest_avg": round(sum(lowest_prices) / len(lowest_prices), 2),
            "brand_mall_ratio": round(mall_count / len(items), 2) if items else 0,
            "advice": self._price_advice(competitive_pressure),
        }

    def get_trending_keywords(self, category: str = "") -> list[KeywordData]:
        defaults = {
            "": ["纸巾", "垃圾袋", "手机壳", "收纳", "拖鞋", "袜子", "衣架", "充电线"],
            "clothing": ["连衣裙", "T恤男", "防晒衣", "阔腿裤", "睡衣"],
            "home": ["四件套", "收纳盒", "地垫", "毛巾", "抱枕"],
            "food": ["坚果", "辣条", "方便面", "饼干", "牛肉干"],
            "digital": ["手机壳", "充电线", "耳机", "充电宝", "钢化膜"],
        }
        kw_list = defaults.get(category, defaults[""])
        return [KeywordData(keyword=k, platform=Platform.PINDUODUO) for k in kw_list]

    @staticmethod
    def _extract_price(text: str) -> Optional[float]:
        if not text:
            return None
        match = re.search(r"(\d+\.?\d*)", text.replace(",", "").replace("￥", ""))
        return float(match.group(1)) if match else None

    @staticmethod
    def _extract_pdd_sales(text: str) -> Optional[int]:
        if not text:
            return None
        text = text.replace("已拼", "").replace("件", "").replace("万件", "万").replace("+", "")
        text = text.replace("拼", "").replace("件", "")
        if "万" in text:
            match = re.search(r"(\d+\.?\d*)", text)
            if match:
                return int(float(match.group(1)) * 10000)
        match = re.search(r"(\d+\.?\d*)", text.replace(",", ""))
        return int(float(match.group(1))) if match else None

    @staticmethod
    def _price_advice(pressure: str) -> str:
        if pressure == "high":
            return "Extreme price competition — need supply chain advantage or volume strategy"
        elif pressure == "medium":
            return "Moderate price competition — differentiate with packaging/bundling"
        else:
            return "Low price competition — potential blue ocean opportunity"


class PinduoduoSalesEstimator:
    """拼多多销量估算器 —— 基于已拼件数差值法 (模拟多多参谋数据模型)"""

    def __init__(self):
        self._baseline_data: dict[str, dict] = {}

    def record_baseline(self, goods_id: str, total_sales: int, price: float, dsr: list[float]):
        self._baseline_data[goods_id] = {
            "total_sales": total_sales,
            "price": price,
            "dsr": dsr,
            "recorded_at": datetime.now(),
        }

    def estimate_daily_from_two_points(
        self,
        total_sales_1: int,
        total_sales_2: int,
        hours_between: float,
    ) -> int:
        if hours_between <= 0:
            return 0
        increment = total_sales_2 - total_sales_1
        if increment <= 0:
            return 0
        return max(0, int(increment / hours_between * 24))

    def rank_product_competitiveness(
        self,
        total_sales: int,
        price: float,
        dsr_scores: list[float],
        days_since_launch: int,
    ) -> str:
        dsr_avg = sum(dsr_scores) / len(dsr_scores) if dsr_scores else 0
        daily_avg_sales = total_sales / max(1, days_since_launch)

        if total_sales >= 100000 and dsr_avg >= 4.7:
            return "explosive"
        elif total_sales >= 10000 and dsr_avg >= 4.5 and daily_avg_sales > 50:
            return "hot"
        elif total_sales >= 1000 and dsr_avg >= 4.3:
            return "growing"
        elif daily_avg_sales > 10:
            return "steady"
        else:
            return "cold"

    def estimate_gmv_rank(
        self,
        daily_sales_est: int,
        avg_price: float,
        category: str = "",
    ) -> dict:
        monthly_gmv = daily_sales_est * 30 * avg_price

        if monthly_gmv > 500000:
            tier = "S"
        elif monthly_gmv > 100000:
            tier = "A"
        elif monthly_gmv > 30000:
            tier = "B"
        elif monthly_gmv > 10000:
            tier = "C"
        else:
            tier = "D"

        return {
            "daily_sales_est": daily_sales_est,
            "monthly_gmv_est": monthly_gmv,
            "tier": tier,
            "category": category,
        }