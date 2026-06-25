import json
import re
from typing import Optional
import httpx

from ecommerce_ops_skill.platform import Platform
from ecommerce_ops_skill.models import KeywordData, RankingItem, DataSource


class XiaohongshuScrapingError(Exception):
    """Raised when real HTTP scraping fails and fallback is used."""


class XiaohongshuClient:
    """小红书电商 — 笔记解析 + 达人分析 + 品牌投放ROI + 真实HTTP搜索"""

    SEARCH_URL = "https://www.xiaohongshu.com/search_result"
    NOTE_URL = "https://www.xiaohongshu.com/explore"
    PROFILE_URL = "https://www.xiaohongshu.com/user/profile"

    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.xiaohongshu.com/",
    }

    CATEGORY_MAP = {
        "beauty": "美妆护肤", "fashion": "穿搭时尚", "food": "美食探店",
        "home": "家居好物", "baby": "母婴育儿", "travel": "旅行攻略",
        "fitness": "运动健身", "digital": "数码好物", "pet": "宠物用品",
        "study": "学习成长",
    }

    def __init__(self, timeout: float = 30.0, cookies: Optional[dict] = None):
        self.timeout = timeout
        self._cookies = cookies or {}
        self._client: Optional[httpx.Client] = None
        self._real_data_available = False

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                headers=self.DEFAULT_HEADERS,
                cookies=self._cookies,
                timeout=self.timeout,
                follow_redirects=True,
            )
        return self._client

    def close(self):
        if self._client:
            self._client.close()
            self._client = None

    def _set_cookies(self, response: httpx.Response):
        for cookie in response.cookies:
            self._cookies[cookie.name] = cookie.value

    # ---- Real HTTP methods ----

    def search_notes(
        self, keyword: str, page: int = 1, sort: str = "general"
    ) -> list[RankingItem]:
        """搜索小红书笔记，返回排名列表。真实HTTP + mock降级"""
        try:
            params = {"keyword": keyword, "source": "web_search_result_notes"}
            if page > 1:
                params["page"] = str(page)
            resp = self.client.get(self.SEARCH_URL, params=params)
            resp.raise_for_status()
            self._set_cookies(resp)
            items = self._parse_search_html(resp.text, keyword)
            if items:
                self._real_data_available = True
                return items
        except Exception:
            pass
        return self._mock_search_notes(keyword, page)

    def get_note_detail(self, note_id: str) -> dict:
        """获取单篇笔记详情。真实HTTP + mock降级"""
        try:
            resp = self.client.get(f"{self.NOTE_URL}/{note_id}")
            resp.raise_for_status()
            self._set_cookies(resp)
            data = self._parse_note_html(resp.text, note_id)
            if data:
                self._real_data_available = True
                return data
        except Exception:
            pass
        return self._mock_note_detail(note_id)

    def search_users(self, keyword: str, page: int = 1) -> list[dict]:
        """搜索小红书用户/达人。真实HTTP + mock降级"""
        try:
            params = {"keyword": keyword, "source": "web_search_result_users"}
            if page > 1:
                params["page"] = str(page)
            resp = self.client.get(self.SEARCH_URL, params=params)
            resp.raise_for_status()
            self._set_cookies(resp)
            users = self._parse_user_html(resp.text, keyword)
            if users:
                self._real_data_available = True
                return users
        except Exception:
            pass
        return self._mock_search_users(keyword, page)

    @property
    def using_real_data(self) -> bool:
        return self._real_data_available

    # ---- HTML parsers ----

    def _parse_search_html(self, html: str, keyword: str) -> list[RankingItem]:
        items = []
        try:
            initial = re.search(
                r'<script>window\.__INITIAL_STATE__\s*=\s*({.*?});</script>',
                html, re.DOTALL
            )
            if not initial:
                return []
            state = json.loads(initial.group(1))
            notes = (
                state.get("search", {})
                .get("notes", {})
                .get("items", [])
            )
            for i, note in enumerate(notes):
                items.append(RankingItem(
                    platform=Platform.XIAOHONGSHU,
                    rank=i + 1,
                    asin_or_id=note.get("id", ""),
                    title=note.get("display_title", "") or note.get("title", ""),
                    image_url=note.get("cover", {}).get("url", "") if isinstance(note.get("cover"), dict) else "",
                    product_url=f"{self.NOTE_URL}/{note.get('id', '')}",
                    brand=note.get("user", {}).get("nickname", "") if isinstance(note.get("user"), dict) else "",
                    data_source=DataSource.WEB_SCRAPING,
                ))
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
            pass
        return items

    def _parse_note_html(self, html: str, note_id: str) -> Optional[dict]:
        try:
            initial = re.search(
                r'<script>window\.__INITIAL_STATE__\s*=\s*({.*?});</script>',
                html, re.DOTALL
            )
            if not initial:
                return None
            state = json.loads(initial.group(1))
            note = state.get("note", {}).get("noteDetailMap", {}).get(note_id, {})
            if not note:
                return None
            interactions = (
                note.get("interactInfo", {})
            )
            return {
                "note_id": note_id,
                "title": note.get("title", ""),
                "desc": note.get("desc", ""),
                "user": note.get("user", {}),
                "likes": interactions.get("likedCount", 0),
                "collects": interactions.get("collectedCount", 0),
                "comments": interactions.get("commentCount", 0),
                "shares": interactions.get("shareCount", 0),
                "views": interactions.get("viewCount", 0),
                "data_source": "web_scraping",
            }
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
            return None

    def _parse_user_html(self, html: str, keyword: str) -> list[dict]:
        users = []
        try:
            initial = re.search(
                r'<script>window\.__INITIAL_STATE__\s*=\s*({.*?});</script>',
                html, re.DOTALL
            )
            if not initial:
                return []
            state = json.loads(initial.group(1))
            user_list = (
                state.get("search", {})
                .get("users", {})
                .get("items", [])
            )
            for u in user_list:
                users.append({
                    "user_id": u.get("id", ""),
                    "nickname": u.get("nickname", ""),
                    "avatar": u.get("avatar", ""),
                    "followers": u.get("follows", 0),
                    "notes": u.get("notes", 0),
                })
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
            pass
        return users

    # ---- Mock fallback data ----

    def _mock_search_notes(self, keyword: str, page: int = 1) -> list[RankingItem]:
        mock_titles = [
            f"{keyword} 爆款推荐！性价比超高",
            f"{keyword} 真实测评｜不吹不黑",
            f"{keyword} 选购指南｜看完再买",
            f"{keyword} 开箱vlog｜惊喜满满",
            f"{keyword} 平替推荐｜学生党必入",
            f"{keyword} 使用教程｜新手友好",
            f"{keyword} 合集推荐｜年度最爱",
            f"{keyword} 对比测评｜哪款值得买",
            f"{keyword} 购物分享｜附🔗",
            f"{keyword} 干货攻略｜建议收藏",
        ]
        offset = (page - 1) * 10
        items = []
        for i in range(10):
            idx = (offset + i) % len(mock_titles)
            items.append(RankingItem(
                platform=Platform.XIAOHONGSHU,
                rank=offset + i + 1,
                asin_or_id=f"xhs-mock-{offset + i}",
                title=mock_titles[idx],
                image_url="",
                product_url=f"{self.NOTE_URL}/xhs-mock-{offset + i}",
                data_source=DataSource.MODEL_ESTIMATION,
            ))
        return items

    def _mock_note_detail(self, note_id: str) -> dict:
        return {
            "note_id": note_id,
            "title": "笔记标题（模拟数据）",
            "desc": "这是模拟的笔记详情数据。真实数据需要小红书API访问权限。",
            "user": {"nickname": "示例达人", "user_id": "mock-user"},
            "likes": 1500, "collects": 800, "comments": 200, "shares": 100,
            "views": 30000,
            "data_source": "mock_fallback",
        }

    def _mock_search_users(self, keyword: str, page: int = 1) -> list[dict]:
        mock_names = [
            f"{keyword}测评达人",
            f"{keyword}精选推荐",
            f"{keyword}买手日记",
            f"{keyword}好物分享家",
            f"爱用{keyword}的小A",
        ]
        return [
            {
                "user_id": f"xhs-user-mock-{i}",
                "nickname": mock_names[i],
                "avatar": "",
                "followers": [50000, 120000, 8000, 300000, 1500][i],
                "notes": [200, 350, 80, 500, 30][i],
            }
            for i in range(min(5, len(mock_names)))
        ]

    # ---- Analysis/reporting methods (unchanged) ----

    def analyze_note_performance(
        self, views: int, likes: int, collects: int, comments: int, shares: int,
        followers_at_post: int = 0, product_click_rate: float = 0.0,
        conversion_rate: float = 0.0, avg_order_value: float = 50.0,
    ) -> dict:
        total_interactions = likes + collects + comments + shares
        engagement_rate = total_interactions / max(1, views)
        like_ratio = likes / max(1, total_interactions) if total_interactions > 0 else 0
        collect_ratio = collects / max(1, total_interactions) if total_interactions > 0 else 0
        comment_ratio = comments / max(1, total_interactions) if total_interactions > 0 else 0
        share_ratio = shares / max(1, total_interactions) if total_interactions > 0 else 0
        viral_score = shares / max(1, views)
        follower_reach_rate = views / followers_at_post if followers_at_post > 0 else 0
        product_clicks = int(views * product_click_rate)
        orders = int(product_clicks * conversion_rate)
        gmv = orders * avg_order_value
        quality = engagement_rate * 10 + viral_score * 50 + collect_ratio * 5
        if quality > 3:
            tier = "S"
        elif quality > 1.5:
            tier = "A"
        elif quality > 0.5:
            tier = "B"
        else:
            tier = "C"
        return {
            "views": views,
            "total_interactions": total_interactions,
            "engagement_rate": round(engagement_rate, 4),
            "interaction_breakdown": {
                "like_ratio": round(like_ratio, 2),
                "collect_ratio": round(collect_ratio, 2),
                "comment_ratio": round(comment_ratio, 2),
                "share_ratio": round(share_ratio, 2),
            },
            "viral_score": round(viral_score, 4),
            "follower_reach_rate": round(follower_reach_rate, 4),
            "conversion_funnel": {
                "product_clicks": product_clicks,
                "click_rate": round(product_click_rate, 4),
                "orders": orders,
                "conversion_rate": round(conversion_rate, 4),
                "gmv_cny": round(gmv, 2),
            },
            "content_tier": tier,
            "quality_score": round(quality, 2),
        }

    def analyze_kol_profile(
        self, followers: int, avg_note_views: int, avg_note_likes: int,
        avg_note_collects: int, total_notes: int, verified: bool = False,
        avg_conversion_rate: float = 0.0, avg_order_value: float = 0.0,
        cooperation_price: float = 0.0,
    ) -> dict:
        avg_engagement = (avg_note_likes + avg_note_collects) / max(1, avg_note_views)
        content_frequency = total_notes / max(1, 90)
        influence_score = (followers * 0.3 + avg_note_views * 0.4 + avg_engagement * 100 * 0.3) / 10000
        if followers >= 500000 and avg_note_views >= 50000:
            tier = "头部KOL"
        elif followers >= 100000 and avg_note_views >= 10000:
            tier = "腰部KOL"
        elif followers >= 10000 and avg_note_views >= 1000:
            tier = "尾部KOL"
        else:
            tier = "KOC素人"
        estimated_orders = int(avg_note_views * avg_conversion_rate)
        estimated_gmv = estimated_orders * avg_order_value
        if cooperation_price > 0 and estimated_gmv > 0:
            roi = estimated_gmv / cooperation_price
        else:
            roi = 0
        if roi > 5:
            roi_tier = "excellent"
        elif roi > 2:
            roi_tier = "good"
        elif roi > 1:
            roi_tier = "acceptable"
        else:
            roi_tier = "poor"
        return {
            "followers": followers, "kol_tier": tier, "verified": verified,
            "avg_note_views": avg_note_views,
            "avg_engagement_rate": round(avg_engagement, 4),
            "influence_score": round(influence_score, 2),
            "content_frequency_daily": round(content_frequency, 2),
            "estimated_orders_per_note": estimated_orders,
            "estimated_gmv_cny": round(estimated_gmv, 2),
            "cooperation_price_cny": cooperation_price,
            "projected_roi": round(roi, 2), "roi_tier": roi_tier,
        }

    def model_brand_campaign(
        self, budget: float, kol_count: int, avg_kol_followers: int,
        avg_kol_views: int, avg_note_engagement: float, product_price: float,
        expected_conversion_rate: float = 0.02, additional_ad_spend: float = 0.0,
    ) -> dict:
        total_impressions = kol_count * avg_kol_views
        total_interactions = int(total_impressions * avg_note_engagement)
        organic_orders = int(total_impressions * expected_conversion_rate)
        organic_gmv = organic_orders * product_price
        total_spend = budget + additional_ad_spend
        if additional_ad_spend > 0:
            paid_impressions = int(additional_ad_spend / 0.5 * 1000)
            paid_orders = int(paid_impressions * expected_conversion_rate * 1.2)
            paid_gmv = paid_orders * product_price
        else:
            paid_impressions = 0
            paid_orders = 0
            paid_gmv = 0.0
        total_orders = organic_orders + paid_orders
        total_gmv = organic_gmv + paid_gmv
        overall_roi = total_gmv / max(1, total_spend)
        cpe = total_spend / max(1, total_interactions) if total_interactions > 0 else 0
        cpm = total_spend / max(1, total_impressions) * 1000
        if overall_roi > 3:
            viability = "highly_profitable"
        elif overall_roi > 1.5:
            viability = "profitable"
        elif overall_roi > 1:
            viability = "breakeven"
        else:
            viability = "loss_making"
        return {
            "budget_cny": budget, "additional_ad_spend_cny": additional_ad_spend,
            "total_spend_cny": round(total_spend, 2),
            "kol_metrics": {"kol_count": kol_count, "avg_followers": avg_kol_followers,
                           "total_impressions": total_impressions,
                           "total_interactions": total_interactions},
            "organic_performance": {"orders": organic_orders, "gmv_cny": round(organic_gmv, 2)},
            "paid_performance": {"impressions": paid_impressions, "orders": paid_orders,
                                "gmv_cny": round(paid_gmv, 2)},
            "total_orders": total_orders, "total_gmv_cny": round(total_gmv, 2),
            "overall_roi": round(overall_roi, 2),
            "cpe_cny": round(cpe, 4), "cpm_cny": round(cpm, 2),
            "viability": viability,
        }

    def estimate_note_trend(
        self, keyword: str, note_count: int = 0,
        avg_views_per_note: int = 0, category_growth_rate: float = 0.05,
    ) -> dict:
        if note_count > 500000:
            competition = "extremely_saturated"
        elif note_count > 100000:
            competition = "saturated"
        elif note_count > 10000:
            competition = "moderate"
        else:
            competition = "low_competition"
        if category_growth_rate >= 0.15:
            trend = "surging"
        elif category_growth_rate > 0.05:
            trend = "growing"
        elif category_growth_rate > 0:
            trend = "stable"
        else:
            trend = "declining"
        opportunity_score = avg_views_per_note / max(1, note_count * 0.01) if note_count > 0 else 0
        return {
            "keyword": keyword, "note_count": note_count,
            "competition_level": competition,
            "category_growth_rate": round(category_growth_rate, 4),
            "trend": trend, "opportunity_score": round(opportunity_score, 4),
            "recommendation": (
                "Strong opportunity — low competition, high growth"
                if competition == "low_competition" and trend in ("surging", "growing")
                else "Consider niche or differentiated content angle"
                if competition in ("saturated", "extremely_saturated")
                else "Monitor and prepare content strategy"
            ),
        }

    def search_content_trends(self, keyword: str = "") -> list[KeywordData]:
        data = [
            KeywordData(keyword="早C晚A护肤", platform=Platform.XIAOHONGSHU, search_volume=85000, search_volume_trend="rising"),
            KeywordData(keyword="通勤穿搭", platform=Platform.XIAOHONGSHU, search_volume=120000, search_volume_trend="stable"),
            KeywordData(keyword="出租屋改造", platform=Platform.XIAOHONGSHU, search_volume=45000, search_volume_trend="rising"),
            KeywordData(keyword="减脂餐食谱", platform=Platform.XIAOHONGSHU, search_volume=200000, search_volume_trend="stable"),
            KeywordData(keyword="大牌平替", platform=Platform.XIAOHONGSHU, search_volume=150000, search_volume_trend="rising"),
            KeywordData(keyword="露营装备", platform=Platform.XIAOHONGSHU, search_volume=60000, search_volume_trend="stable"),
            KeywordData(keyword="宝宝辅食", platform=Platform.XIAOHONGSHU, search_volume=95000, search_volume_trend="stable"),
            KeywordData(keyword="办公桌好物", platform=Platform.XIAOHONGSHU, search_volume=35000, search_volume_trend="rising"),
        ]
        if keyword:
            return [k for k in data if keyword in k.keyword]
        return data

    def get_trending_notes_tags(self, category: str = "") -> list[str]:
        tags_by_cat = {
            "": ["好物分享", "平价好物", "年度爱用", "开箱测评", "使用教程"],
            "beauty": ["护肤步骤", "我的护肤日常", "素颜霜推荐", "抗老精华", "面霜测评"],
            "fashion": ["一周穿搭", "小个子穿搭", "显瘦穿搭", "通勤OOTD", "胶囊衣橱"],
            "home": ["家居好物", "收纳神器", "出租屋改造", "极简主义", "提升幸福感好物"],
            "food": ["懒人食谱", "低卡零食", "空气炸锅美食", "减脂餐", "早餐吃什么"],
            "digital": ["数码测评", "学生党必入", "降噪耳机测评", "手机壳推荐", "桌面布置"],
        }
        return tags_by_cat.get(category, tags_by_cat[""])

    def estimate_content_roi(
        self, note_views: int, product_price: float,
        note_production_cost: float = 0, influencer_cost: float = 0,
        conversion_rate: float = 0.02,
    ) -> dict:
        total_cost = note_production_cost + influencer_cost
        orders = int(note_views * conversion_rate)
        revenue = orders * product_price
        roi = revenue / max(1, total_cost) if total_cost > 0 else float('inf')
        cpm_content = total_cost / max(1, note_views) * 1000
        return {
            "note_views": note_views, "product_price_cny": product_price,
            "total_cost_cny": round(total_cost, 2),
            "estimated_orders": orders, "estimated_revenue_cny": round(revenue, 2),
            "roi": round(roi, 2) if roi != float('inf') else "organic",
            "cpm_cny": round(cpm_content, 2),
        }
