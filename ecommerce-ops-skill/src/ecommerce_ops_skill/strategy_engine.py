from datetime import datetime as _dt
from typing import Optional

from ecommerce_ops_skill.platform import Platform, StrategyPhase
from ecommerce_ops_skill.web_search import WebSearchClient, MockWebSearchClient


class StrategyEngine:
    def __init__(self, platform: Platform = Platform.AMAZON):
        self.platform = platform

    def full_strategy(self, product_category: str = "", target_market: str = "US", budget_level: str = "medium") -> list[dict]:
        return [
            self._selection_phase(product_category, target_market, budget_level),
            self._listing_phase(product_category, target_market, budget_level),
            self._traffic_phase(product_category, target_market, budget_level),
            self._conversion_phase(product_category, target_market, budget_level),
            self._retention_phase(product_category, target_market, budget_level),
            self._review_phase(),
        ]

    def selection_strategy(self, product_category: str = "", target_market: str = "US", budget_level: str = "medium") -> dict:
        return self._selection_phase(product_category, target_market, budget_level)

    def listing_strategy(self, product_category: str = "", target_market: str = "US", budget_level: str = "medium") -> dict:
        return self._listing_phase(product_category, target_market, budget_level)

    def traffic_strategy(self, product_category: str = "", target_market: str = "US", budget_level: str = "medium") -> dict:
        return self._traffic_phase(product_category, target_market, budget_level)

    def conversion_strategy(self, product_category: str = "", target_market: str = "US", budget_level: str = "medium") -> dict:
        return self._conversion_phase(product_category, target_market, budget_level)

    def retention_strategy(self, product_category: str = "", target_market: str = "US", budget_level: str = "medium") -> dict:
        return self._retention_phase(product_category, target_market, budget_level)

    def analyze_competitor_from_bestseller(self, bestseller_list) -> dict:
        if not bestseller_list or not bestseller_list.items:
            return {"error": "No data to analyze"}

        items = bestseller_list.items
        prices = [i.price for i in items if i.price]
        ratings = [i.rating for i in items if i.rating]
        reviews = [i.review_count for i in items if i.review_count]
        brands: dict[str, int] = {}
        for i in items:
            if i.brand:
                brands[i.brand] = brands.get(i.brand, 0) + 1

        return {
            "total_items": len(items),
            "avg_price": sum(prices) / len(prices) if prices else None,
            "price_range": (min(prices), max(prices)) if len(prices) >= 2 else None,
            "avg_rating": sum(ratings) / len(ratings) if ratings else None,
            "avg_reviews": sum(reviews) / len(reviews) if reviews else None,
            "top_brands": sorted(brands.items(), key=lambda x: x[1], reverse=True)[:10],
            "sponsored_ratio": sum(1 for i in items if i.is_sponsored) / len(items) if items else 0,
            "bestseller_count": sum(1 for i in items if i.is_bestseller),
        }

    def cross_platform_compare(self, data_by_platform: dict[str, list]) -> dict:
        comparison = {}
        for platform_name, items in data_by_platform.items():
            if isinstance(items, list) and items:
                avg_price = sum(i.price for i in items if i.price) / max(1, len([i for i in items if i.price]))
                comparison[platform_name] = {
                    "count": len(items),
                    "avg_price_cny": round(avg_price, 2) if avg_price else None,
                }
        return comparison

    def market_insights(self, keyword: str, client: Optional[WebSearchClient] = None) -> dict:
        client = client or MockWebSearchClient()
        news = client.search_news(keyword)
        products = client.search_products(keyword)
        trends = client.search_trends(keyword)

        snippets = [r["snippet"] for r in news.get("results", [])]
        product_titles = [r["title"] for r in products.get("results", [])]
        trend_snippets = [r["snippet"] for r in trends.get("results", [])]
        combined = snippets + trend_snippets

        sentiment = "positive"
        positive_words = ["增长", "rise", "growth", "hot", "trending", "爆发", "热销"]
        negative_words = ["下滑", "decline", "drop", "危机", "衰退", "下降", "饱和"]
        pos = sum(1 for s in combined for w in positive_words if w in s.lower())
        neg = sum(1 for s in combined for w in negative_words if w in s.lower())
        if pos > neg * 2:
            sentiment = "positive"
        elif neg > pos * 2:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        return {
            "keyword": keyword,
            "sentiment": sentiment,
            "news_count": len(news.get("results", [])),
            "product_count": len(products.get("results", [])),
            "sample_products": product_titles[:5],
            "sample_headlines": snippets[:3],
            "source_type": news.get("source_type", "mock"),
            "using_real_data": news.get("using_real_data", False),
        }

    def enrich_competitor_analysis(self, items: list, client: Optional[WebSearchClient] = None) -> dict:
        client = client or MockWebSearchClient()
        base = self.analyze_competitor_from_bestseller(type("BList", (), {"items": items})())
        if not items:
            return base

        keyword = items[0].title or ""
        news = client.search_news(keyword, max_results=5)
        products = client.search_products(keyword, max_results=5)

        web_snippets = [r["snippet"] for r in news.get("results", [])]
        web_prices = []
        for r in products.get("results", []):
            import re
            nums = re.findall(r"[\d.]+", r.get("snippet", ""))
            if nums:
                try:
                    web_prices.append(float(nums[0]))
                except ValueError:
                    pass

        base["web_enrichment"] = {
            "web_news_snippets": web_snippets[:3],
            "web_price_indicators": web_prices[:5],
            "avg_web_price": round(sum(web_prices) / max(1, len(web_prices)), 2) if web_prices else None,
            "source_type": news.get("source_type", "mock"),
            "using_real_data": news.get("using_real_data", False),
        }
        return base

    def enriched_strategy(self, keyword: str, client: Optional[WebSearchClient] = None,
                          product_category: str = "", target_market: str = "US",
                          budget_level: str = "medium") -> dict:
        client = client or MockWebSearchClient()
        insights = self.market_insights(keyword, client)
        phases = self.full_strategy(product_category, target_market, budget_level)
        seasonal = self.predict_seasonal_trend(product_category or keyword)

        return {
            "keyword": keyword,
            "market_insights": insights,
            "seasonal_info": seasonal,
            "strategy_phases": phases,
            "source_type": insights["source_type"],
            "using_real_data": insights["using_real_data"],
        }

    def _selection_phase(self, category: str, market: str, budget: str) -> dict:
        if self.platform == Platform.AMAZON:
            return self._amazon_selection(category, market, budget)
        elif self.platform in (Platform.TAOBAO, Platform.TMALL):
            return self._taobao_selection(category)
        elif self.platform == Platform.JD:
            return self._jd_selection(category)
        elif self.platform == Platform.PINDUODUO:
            return self._pdd_selection(category)
        elif self.platform == Platform.DOUYIN:
            return self._douyin_selection(category)
        elif self.platform == Platform.XIAOHONGSHU:
            return self._xhs_selection(category)
        else:
            return {"phase": "selection", "platform": self.platform.value, "steps": ["to be refined"], "key_metrics": []}

    def _listing_phase(self, category: str, market: str, budget: str) -> dict:
        if self.platform == Platform.AMAZON:
            return self._amazon_listing()
        elif self.platform in (Platform.TAOBAO, Platform.TMALL):
            return self._taobao_listing()
        elif self.platform == Platform.JD:
            return self._jd_listing()
        elif self.platform == Platform.PINDUODUO:
            return self._pdd_listing()
        elif self.platform == Platform.DOUYIN:
            return self._douyin_listing()
        elif self.platform == Platform.XIAOHONGSHU:
            return self._xhs_listing()
        else:
            return {"phase": "listing", "platform": self.platform.value, "steps": ["to be refined"], "key_metrics": []}

    def _traffic_phase(self, category: str, market: str, budget: str) -> dict:
        if self.platform == Platform.AMAZON:
            return self._amazon_traffic(budget)
        elif self.platform in (Platform.TAOBAO, Platform.TMALL):
            return self._taobao_traffic(budget)
        elif self.platform == Platform.JD:
            return self._jd_traffic(budget)
        elif self.platform == Platform.PINDUODUO:
            return self._pdd_traffic(budget)
        elif self.platform == Platform.DOUYIN:
            return self._douyin_traffic(budget)
        elif self.platform == Platform.XIAOHONGSHU:
            return self._xhs_traffic(budget)
        else:
            return {"phase": "traffic", "platform": self.platform.value, "steps": ["to be refined"], "key_metrics": []}

    def _conversion_phase(self, category: str, market: str, budget: str) -> dict:
        if self.platform == Platform.AMAZON:
            return self._amazon_conversion()
        elif self.platform in (Platform.TAOBAO, Platform.TMALL):
            return self._taobao_conversion()
        elif self.platform == Platform.JD:
            return self._jd_conversion()
        elif self.platform == Platform.PINDUODUO:
            return self._pdd_conversion()
        elif self.platform == Platform.DOUYIN:
            return self._douyin_conversion()
        elif self.platform == Platform.XIAOHONGSHU:
            return self._xhs_conversion()
        else:
            return {"phase": "conversion", "platform": self.platform.value, "steps": ["to be refined"], "key_metrics": []}

    def _retention_phase(self, category: str, market: str, budget: str) -> dict:
        if self.platform == Platform.AMAZON:
            return self._amazon_retention()
        elif self.platform in (Platform.TAOBAO, Platform.TMALL):
            return self._taobao_retention()
        elif self.platform == Platform.JD:
            return self._jd_retention()
        elif self.platform == Platform.PINDUODUO:
            return self._pdd_retention()
        elif self.platform == Platform.DOUYIN:
            return self._douyin_retention()
        elif self.platform == Platform.XIAOHONGSHU:
            return self._xhs_retention()
        else:
            return {"phase": "retention", "platform": self.platform.value, "steps": ["to be refined"], "key_metrics": []}

    def _review_phase(self) -> dict:
        return {
            "phase": StrategyPhase.REVIEW.value,
            "platform": self.platform.value,
            "title": "Performance review",
            "steps": [
                "Weekly ranking trend check",
                "PPC campaign audit: pause losers, scale winners",
                "Competitor monitoring: new entrants, price changes",
                "Review sentiment analysis",
                "Inventory forecast vs sales velocity",
                "Seasonality planning 2-4 weeks ahead",
            ],
            "key_metrics": ["Revenue growth rate", "Profit margin", "PPC ROAS", "Organic vs paid traffic ratio"],
        }

    def _amazon_selection(self, category: str, market: str, budget: str) -> dict:
        return {
            "phase": "selection", "platform": "amazon", "market": market,
            "title": "Amazon {} selection".format(market),
            "steps": [
                "BSR Top 100 to find hot categories",
                "BSR trend analysis for rising categories",
                "Jungle Scout / Keepa for category capacity",
                "Target $15-$40 price band for high CVR",
                "Analyze competitor negative reviews for pain points",
                "FBA fee + margin: ensure gross > 30%",
                "Check patent/IP risk",
            ],
            "key_metrics": ["Avg BSR Top 100", "Avg reviews/launch", "Brand concentration", "Avg price/margin"],
            "risk_warnings": ["10k+ reviews per product → hard entry", "Price war categories", "Seasonal risk", "Amazon Basics competition"],
        }

    def _amazon_listing(self) -> dict:
        return {
            "phase": "listing", "platform": "amazon",
            "title": "Amazon Listing optimization",
            "steps": [
                "Title: Brand + Core Keyword + Attribute + Scenario (<200 chars)",
                "Bullets: one selling point each, keywords in first 2",
                "A+ Content + Brand Story module",
                "Search Terms: long-tail keywords not in title",
                "Main image: pure white 255/255/255, >85% fill",
                "Video upload for CVR boost",
                "Variation merge for shared reviews",
                "Launch pricing slightly below market average",
            ],
            "key_metrics": ["Title keyword coverage", "Main image CTR", "Dwell time", "Variation CVR"],
        }

    def _amazon_traffic(self, budget: str) -> dict:
        cfg = {"low": "$10-20/d", "medium": "$30-80/d", "high": "$100-300/d"}.get(budget, "$30-80/d")
        return {
            "phase": "traffic", "platform": "amazon",
            "title": "Amazon traffic acquisition",
            "budget_recommendation": {"daily_ppc": cfg},
            "steps": [
                "SP auto 7-14d → manual targeting high-CVR keywords",
                "SB: Brand Store traffic, defend brand keywords",
                "SD: competitor detail page + category targeting",
                "Long-tail → short-tail keyword rank strategy",
                "Amazon Posts free content channel",
                "Off-Amazon: social + Influencer + deal sites",
                "Coupon + LD/7DD for BSR burst",
                "New product daily PPC: {}".format(cfg),
            ],
            "key_metrics": ["ACoS", "TACoS", "Keyword organic rank", "Impression share", "CTR/CVR by campaign"],
        }

    def _amazon_conversion(self) -> dict:
        return {
            "phase": "conversion", "platform": "amazon",
            "title": "Amazon CVR optimization",
            "steps": [
                "Price anchoring: original + discounted price",
                "Coupon + BOGO + tiered discounts",
                "Review seeding via Amazon Request a Review",
                "Seed 3-5 Q&As addressing concerns",
                "A+ Content + brand story trust signals",
                "FBA Prime badge for trust",
                "Never stock out — BSR resets to zero",
                "A/B test price points for optimal CVR",
            ],
            "key_metrics": ["Unit Session %", "Cart abandonment", "AOV", "CAC"],
        }

    def _amazon_retention(self) -> dict:
        return {
            "phase": "retention", "platform": "amazon",
            "title": "Amazon retention",
            "steps": [
                "Subscribe & Save for consumables",
                "Brand Store followers for owned traffic",
                "Post-purchase follow-up emails",
                "Cross-sell related SKUs",
                "Amazon Live for repeat engagement",
                "Address negative reviews quickly",
                "Bundle deals to increase AOV",
            ],
            "key_metrics": ["Repeat purchase rate", "LTV", "S&S enrollment", "Return rate"],
        }

    def _taobao_selection(self, category: str) -> dict:
        return {
            "phase": "selection", "platform": "taobao",
            "title": "淘宝/天猫选品策略",
            "steps": [
                "通过淘宝搜索按销量排序，锁定热销品类 Top 50",
                "对比天猫和C店的价格带分布，找到蓝海价格带",
                "分析月销量≥1000 的商品特征（标题/主图/定价/店铺DSR）",
                "识别搜索词竞争度：看直通车参考价和头部商品销量",
                "避开品牌旗舰店垄断品类，选择C店有机会的价格段",
                "检查1688同款供应价，确保毛利率 ≥ 40%",
                "关注季节性产品的切入时间（提前 2-4 周上架）",
            ],
            "key_metrics": ["类目头部月销量", "天猫占比", "平均售价/毛利", "DSR均值", "直通车CPC"],
            "risk_warnings": ["天猫旗舰店垄断品类（TOP10天猫>80%）", "价格战品类（平均毛利<20%）", "高退货率品类"],
        }

    def _taobao_listing(self) -> dict:
        return {
            "phase": "listing", "platform": "taobao",
            "title": "淘宝/天猫标题与主图优化",
            "steps": [
                "标题公式：核心词 + 属性词 + 场景词 + 长尾词（30字充分利用）",
                "首图差异化：避免白底，凸显卖点（功能/场景/对比）",
                "5张主图：首图吸引点击→场景图→细节图→对比图→促销图",
                "详情页前三屏决定转化：痛点→解决方案→产品展示→信任背书",
                "SKU命名：标准版/升级版/套装，引导高价SKU",
                "视频上传：15-30秒产品展示+使用场景视频",
                "手机端优先：移动端流量 > 80%，检查手机端展示效果",
                "上架时间：工作日10:00-11:00或20:00-22:00黄金时段",
            ],
            "key_metrics": ["搜索曝光量", "主图点击率", "加购率", "详情页跳失率", "手淘首页推荐占比"],
        }

    def _taobao_traffic(self, budget: str) -> dict:
        cfg = {"low": "￥50-100/天", "medium": "￥200-500/天", "high": "￥800-2000/天"}.get(budget, "￥200-500/天")
        return {
            "phase": "traffic", "platform": "taobao",
            "title": "淘宝/天猫流量获取",
            "budget_recommendation": {"daily_ppc": cfg},
            "steps": [
                "直通车：先开广泛匹配测词 7 天→精准匹配高转化词→逐步降低出价",
                "引力魔方：首页猜你喜欢推荐流量，适合标品爆款",
                "万相台：AI 智能投放，适合中小卖家省力投放",
                "淘宝直播：店铺自播+达人带货双轨并行",
                "逛逛内容：短视频+图文种草，免费流量入口",
                "淘客推广：设置合理佣金（5%-30%），团长合作冲量",
                "活动报名：天天特卖→淘抢购→聚划算，阶梯式促销",
                "站外引流：抖音/小红书种草→淘宝搜索转化",
                "每日预算建议：{}".format(cfg),
            ],
            "key_metrics": ["直通车ROI", "引力魔方点击率", "直播GMV占比", "淘客成交占比", "免费/付费流量比"],
        }

    def _taobao_conversion(self) -> dict:
        return {
            "phase": "conversion", "platform": "taobao",
            "title": "淘宝/天猫转化优化",
            "steps": [
                "价格锚定：划线原价+促销价，高感知折扣力度",
                "优惠券组合：店铺券+商品券+平台券，三券叠加",
                "评价管理：好评返现卡（合规方式），引导图文+视频评价",
                "问大家：人工介入回答高频问题，消除购买疑虑",
                "服务承诺：7天无理由+运费险+顺丰包邮，降低决策门槛",
                "关联营销：详情页顶部+底部推荐，提升客单价",
                "限时促销：倒计时+库存进度条，制造稀缺感",
                "售后服务：24小时客服响应，差评主动联系修改",
            ],
            "key_metrics": ["转化率(CVR)", "客单价(AOV)", "DSR评分", "退货率", "店铺复购率"],
        }

    def _taobao_retention(self) -> dict:
        return {
            "phase": "retention", "platform": "taobao",
            "title": "淘宝私域与复购",
            "steps": [
                "店铺粉丝群：上新通知+粉丝专享价+群内互动",
                "会员体系：积分商城+会员折扣+生日权益",
                "淘宝订阅：定期推送内容，保持粉丝活跃度",
                "CRM短信营销：老客户短信+优惠券，复购唤醒",
                "微信私域导流：包裹卡+售后引导添加微信",
                "组合SKU套餐：关联产品打包，提高客单价",
                "上新节奏：每月2-4款持续上新，保持店铺活跃",
            ],
            "key_metrics": ["复购率", "粉丝增长率", "会员GMV占比", "老客流失率", "客单价提升率"],
        }

    def _jd_selection(self, category: str) -> dict:
        return {
            "phase": "selection", "platform": "jd",
            "title": "京东选品策略",
            "steps": [
                "确定京东自营占比：自营>50%的品类POP难度大",
                "分析京东搜索结果前三页的品牌分布",
                "关注京东物流打标商品的溢价空间（京东物流=溢价10-15%）",
                "筛选京东好店门槛可达到的品类",
                "分析京准通CPC水平，评估广告成本",
                "选择POP卖家竞争相对小的长尾品类",
            ],
            "key_metrics": ["京东自营占比", "TOP10品牌GMV", "京东好店比例", "京准通CPC", "POP卖家月GMV"],
            "risk_warnings": ["京东自营垄断品类(>60%自营)", "3C数码等高退货率品类", "需入仓品类(资金占用高)"],
        }

    def _jd_listing(self) -> dict:
        return {
            "phase": "listing", "platform": "jd",
            "title": "京东商详优化",
            "steps": [
                "标题：品牌 + 核心词 + 属性/规格 + 场景词（50字内）",
                "主图：白底首图 + 场景图 + 卖点图 + 促销图（至少5张）",
                "商详页面：关联版式+商品介绍+规格参数+售后承诺",
                "京东视频：主图视频+详情页视频，加权搜索排名",
                "SPU聚合：同款不同规格聚合，减少SKU分散",
                "京东好店打标：DSR达标+物流达标=搜索加权",
                "入仓京东物流：搜索加权+时效标签+转化率提升",
            ],
            "key_metrics": ["标题关键词权重", "主图点击率", "商详停留时间", "SPU转化率", "物流时效评分"],
        }

    def _jd_traffic(self, budget: str) -> dict:
        cfg = {"low": "￥80-150/天", "medium": "￥300-600/天", "high": "￥1000-2500/天"}.get(budget, "￥300-600/天")
        return {
            "phase": "traffic", "platform": "jd",
            "title": "京东流量获取",
            "budget_recommendation": {"daily_ppc": cfg},
            "steps": [
                "京准通-京东快车：搜索广告，关键词投放",
                "京准通-购物触点：推荐位广告（首页+商详底部）",
                "京东直播：店铺自播+达人合作带货",
                "京东秒杀+品牌闪购：促销活动爆发流量",
                "京东内容：京东发现+短视频种草",
                "京东Plus会员专享价：吸引高价值用户",
                "站外引流：微信小程序+抖音/小红书→京东搜索",
                "每日预算建议：{}".format(cfg),
            ],
            "key_metrics": ["京东快车ROI", "购物触点CTR", "秒杀GMV", "PLUS用户占比", "免费/付费流量比"],
        }

    def _jd_conversion(self) -> dict:
        return {
            "phase": "conversion", "platform": "jd",
            "title": "京东转化优化",
            "steps": [
                "京东物流打标：搜索加权+时效标签+高转化率",
                "京东好店认证：DSR≥9.38，获得搜索+活动加权",
                "价格锚定：京东价+到手价，叠加Plus专享价",
                "评价管理：30字+3图+视频评价，高权重留评",
                "京东Plus会员：Plus价+Plus券，锁定高净值用户",
                "售后服务：闪电退款/上门取件/以换代修",
                "关联推荐：详情页+购物车，提升客单价",
                "白条分期：降低支付门槛，提升转化",
            ],
            "key_metrics": ["商详转化率", "客单价", "Plus订单占比", "DSR均值", "物流时效达成率"],
        }

    def _jd_retention(self) -> dict:
        return {
            "phase": "retention", "platform": "jd",
            "title": "京东复购与会员",
            "steps": [
                "京东店铺会员：积分+等级+会员专享价",
                "关注店铺引导：搜索加权+粉丝触达",
                "京东Plus联合营销：Plus专属活动+商品",
                "CRM客户管理：精准营销短信+PUSH",
                "跨品类联动：关联品类组合推荐",
                "订阅型商品：定期购/周期购",
                "服务增值：延保+配件+增值服务提高复购",
            ],
            "key_metrics": ["复购率", "Plus会员复购率", "客单价提升率", "店铺粉丝数", "会员活跃度"],
        }

    def _pdd_selection(self, category: str) -> dict:
        return {
            "phase": "selection", "platform": "pinduoduo",
            "title": "拼多多选品策略",
            "steps": [
                "分析类目价格带：拼多多消费者高度价格敏感，找准低价爆款价格段",
                "查看已拼10万+的爆款特征：价格/主图/标题/DSR",
                "供应链评估：能否做到类目最低价前20%？不能则考虑差异化",
                "避开品牌旗舰店密集品类，选择白牌有机会的赛道",
                "关注百亿补贴品类：平台扶持的高流量品类",
                "测算多多进宝佣金+多多搜索CPC，预估ROI",
                "低客单(<￥30)走量策略 vs 中客单(￥50-150)利润策略选其一",
            ],
            "key_metrics": ["类目均价", "头部已拼件数", "品牌店铺占比", "多多搜索CPC", "利润率"],
            "risk_warnings": ["超低价品类(均价<￥10)：毛利率极低", "品牌高度集中品类", "高退货率品类(服饰>30%)"],
        }

    def _pdd_listing(self) -> dict:
        return {
            "phase": "listing", "platform": "pinduoduo",
            "title": "拼多多商品上架优化",
            "steps": [
                "标题公式：促销词+核心关键词+属性词+场景词（30字充分利用）",
                "主图核心：价格标/卖点图标/场景图，突出性价比",
                "10张主图全利用：首图吸睛→场景→细节→对比→活动→服务承诺",
                "SKU布局引流款+利润款+活动款，引流款定最低价",
                "拼单价 vs 单买价差策略：拼单价低15-30%驱动拼团",
                "详情页突出痛点+解决方案+产品对比+买家秀",
                "服务标签：极速退款/退货包运费/顺丰包邮/48小时发货",
            ],
            "key_metrics": ["曝光量", "点击率", "转化率", "收藏率", "DSR评分"],
        }

    def _pdd_traffic(self, budget: str) -> dict:
        cfg = {"low": "￥50-100/天", "medium": "￥200-500/天", "high": "￥800-2000/天"}.get(budget, "￥200-500/天")
        return {
            "phase": "traffic", "platform": "pinduoduo",
            "title": "拼多多流量获取",
            "budget_recommendation": {"daily_ppc": cfg},
            "steps": [
                "多多搜索：关键词搜索广告，类目大词+精准长尾词组合",
                "多多场景：首页推荐/活动页/支付页等场景资源位",
                "全站推广：AI智能投放，适合新手中小卖家",
                "多多进宝：CPS按成交付费，设置30-50%高佣冲量",
                "活动报名：9.9特卖→限时秒杀→品牌清仓→百亿补贴（阶梯式）",
                "拼团裂变：2人拼团机制+分享优惠券，社交裂变自然流量",
                "多多视频：短视频种草带货，类抖音模式",
                "每日预算建议：{}".format(cfg),
            ],
            "key_metrics": ["多多搜索ROI", "场景曝光量", "活动GMV占比", "拼团成功率", "多多进宝转化率"],
        }

    def _pdd_conversion(self) -> dict:
        return {
            "phase": "conversion", "platform": "pinduoduo",
            "title": "拼多多转化优化",
            "steps": [
                "价格竞争力：同款商品价格需在类目前30%（拼多多核心转化因素）",
                "拼单价：拼单价设置比单买价低20-40%，强化拼团动力",
                "限量/限时优惠：倒计时+库存余量+已拼人数，社会证明驱动",
                "评价管理：带图评价+追加评价，前10条评价重点维护",
                "DSR评分：描述相符/物流服务/服务态度三维平衡，DSR<4.3限流",
                "退货包运费：降低决策门槛，提升转化5-15%",
                "店铺满减：满2件减X元/满X元减X元，提升客单价",
            ],
            "key_metrics": ["转化率", "客单价", "DSR均值", "退货率", "店铺评分"],
        }

    def _pdd_retention(self) -> dict:
        return {
            "phase": "retention", "platform": "pinduoduo",
            "title": "拼多多复购与店铺运营",
            "steps": [
                "关注店铺优惠券：关注即领X元券，积累粉丝池",
                "店铺收藏引导：首页+详情页+下单后弹窗引导收藏",
                "复购优惠券：下单后送复购券（3-7天有效期）",
                "新品快讯：店铺上新通知老客户",
                "评价有礼：好评返现引导复购（合规方式）",
                "多SKU关联：同品类组合装/套装提升客单价",
                "供应链持续优化：降低成本→提价空间→利润增长",
            ],
            "key_metrics": ["复购率", "粉丝数", "店铺收藏数", "客户留存率", "客单价趋势"],
        }

    def _douyin_selection(self, category: str) -> dict:
        return {
            "phase": "selection", "platform": "douyin",
            "title": "抖音电商选品策略",
            "steps": [
                "选择\"内容可视化\"品类：产品卖点能用15-60秒短视频清晰展示",
                "关注抖音电商排行榜：实时热销榜+飙升榜+品牌榜",
                "测算GPM(千次观看成交额)：选择GPM>500的潜力品类",
                "分析品类的内容生态：相关达人数量+爆款视频特征+带货转化",
                "高毛利(>50%)才能覆盖达人佣金(20-40%)+千川投放成本",
                "新奇特产品(视觉冲击力强)比标品更适合抖音生态",
                "季节性产品提前2-3周布局短视频内容矩阵",
            ],
            "key_metrics": ["类目GPM", "带货达人数", "爆款视频播放量", "佣金比例", "毛利率"],
            "risk_warnings": ["标品(无内容可视化空间)：内容生产成本高", "过气品类：流量红利消退", "达人佣金>50%品类"],
        }

    def _douyin_listing(self) -> dict:
        return {
            "phase": "listing", "platform": "douyin",
            "title": "抖音商品上架与内容策略",
            "steps": [
                "商品标题：核心关键词+场景词+人群标签词(30字内)",
                "商品主图：信息图+场景图+使用效果前后对比",
                "商品详情页：前三屏决定转化(痛点+解决方案+产品展示+买家秀)",
                "短视频种草：15-60秒，前3秒黄金开头(悬念/痛点/效果展示)",
                "直播话术脚本：开场→痛点→产品展示→限时优惠→逼单转化",
                "达人矩阵：头部(1-2个)+腰部(5-10个)+尾部(50+个)KOC铺量",
                "商品卡优化：标题+主图+详情页+评价=搜索推荐双引擎",
            ],
            "key_metrics": ["商品卡曝光", "短视频完播率", "直播间GPM", "商品点击率", "加购率"],
        }

    def _douyin_traffic(self, budget: str) -> dict:
        cfg = {"low": "￥100-300/天", "medium": "￥500-1500/天", "high": "￥3000-10000/天"}.get(budget, "￥500-1500/天")
        return {
            "phase": "traffic", "platform": "douyin",
            "title": "抖音电商流量获取",
            "budget_recommendation": {"daily_ad_budget": cfg},
            "steps": [
                "千川短视频引流：投放爆款视频→商品卡/直播间，测素材ROI",
                "千川直播引流：直播间实时投放，直投直播间+短视频引流直播",
                "达人矩阵带货：纯佣合作+坑位费+佣金混合模式",
                "店铺自播：日播4-8小时积累权重，稳定GPM",
                "短视频矩阵：品牌号+员工号+分销号多账号铺量",
                "抖音SEO：标题+话题标签+搜索词布局，获取搜索流量",
                "平台活动：抖音好物节/年货节/618/双11等大促爆发",
                "每日投放预算建议：{}".format(cfg),
            ],
            "key_metrics": ["千川ROI", "直播间GPM", "短视频播放量", "达人带货GMV", "商品卡搜索排名"],
        }

    def _douyin_conversion(self) -> dict:
        return {
            "phase": "conversion", "platform": "douyin",
            "title": "抖音电商转化策略",
            "steps": [
                "直播间停留时长：前3秒钩子话术，平均停留>2分钟为优",
                "互动引导：点赞截图抽奖/福袋/限时优惠码",
                "逼单话术：限时限量+库存倒数+已卖出展示+涨价预告",
                "直播间优惠：直播间专享价/直播间满减/运费险",
                "信任建立：品牌资质展示+达人背书+买家秀+售后承诺",
                "短视频挂车：视频内容→商品链接无缝跳转",
                "搜索承接：品牌词+品类词的搜索页优化",
            ],
            "key_metrics": ["直播间CVR", "平均停留时长", "互动率", "GPM", "退单率"],
        }

    def _douyin_retention(self) -> dict:
        return {
            "phase": "retention", "platform": "douyin",
            "title": "抖音电商复购与粉丝运营",
            "steps": [
                "粉丝群运营：粉丝群专属优惠+上新通知+直播预告",
                "会员体系：抖音店铺会员=积分+等级+会员价",
                "店铺自播常态化：固定日播时段，培养粉丝观看习惯",
                "短视频内容节奏：每周3-7条，保持账号活跃度",
                "售后服务：48小时发货+7天无理由+极速退款",
                "复购券：下单后自动发放X天内有效复购券",
                "CRM数据：直播间观看→互动→下单→复购全链路追踪",
            ],
            "key_metrics": ["粉丝复购率", "粉丝增长率", "店铺会员数", "直播场均观看", "LTV"],
        }

    def _xhs_selection(self, category: str) -> dict:
        return {
            "phase": "selection", "platform": "xiaohongshu",
            "title": "小红书选品策略",
            "steps": [
                "搜索关键词笔记数分析：笔记数<1万为蓝海，>10万为红海",
                "分析品类笔记互动率：高收藏率=强购买意图品类",
                "关注\"大牌平替\"搜索趋势：小红书用户对性价比高度敏感",
                "选择视觉冲击力强的品类：小红书是图文种草平台",
                "分析达人带货数据：品类头部达人数量+平均带货转化",
                "产品需适配\"场景化\"内容：穿搭/家居/美妆/母婴/美食",
            ],
            "key_metrics": ["品类笔记数", "平均互动率", "收藏率", "种草达人数量", "CPM(千次曝光成本)"],
            "risk_warnings": ["笔记高度饱和品类(>50万)", "低互动率品类(<2%)", "内容生产门槛高的品类"],
        }

    def _xhs_listing(self) -> dict:
        return {
            "phase": "listing", "platform": "xiaohongshu",
            "title": "小红书笔记内容策略",
            "steps": [
                "笔记标题：数字+痛点+解决方案+关键词（20字内）",
                "封面图：高颜值+对比效果+文字标签（第一吸引力）",
                "笔记结构：开头钩子→痛点展示→产品解决方案→使用效果→购买引导",
                "标签策略：3-5个精准话题标签（大词+长尾词组合）",
                "发布时间：工作日12:00-13:00/18:00-20:00，周末9:00-11:00",
                "评论区运营：置顶购买链接+FAQ+引导互动",
                "合集创建：按品类/场景创建笔记合集，延长曝光周期",
            ],
            "key_metrics": ["笔记曝光量", "点击率", "互动率(赞藏评)", "收藏率", "商品点击率"],
        }

    def _xhs_traffic(self, budget: str) -> dict:
        cfg = {"low": "￥200-500/篇", "medium": "￥1000-3000/篇", "high": "￥5000-15000/篇"}.get(budget, "￥1000-3000/篇")
        return {
            "phase": "traffic", "platform": "xiaohongshu",
            "title": "小红书流量获取",
            "budget_recommendation": {"per_content_kol": cfg},
            "steps": [
                "达人矩阵：KOC素人(50+)+尾部KOL(20+)+腰部KOL(5+)+头部KOL(1-2)",
                "薯条推广：加热优质笔记，100元起投，CPM约30-50元",
                "信息流广告：精准人群定向（年龄/地域/兴趣标签）",
                "搜索广告：抢占品类关键词第一屏位置",
                "品牌专区：品牌词搜索结果专属页面",
                "话题营销：创建品牌话题+UGC激励机制",
                "直播带货：店铺自播+达人直播双轨",
                "单篇内容预算参考：{}".format(cfg),
            ],
            "key_metrics": ["CPM", "CPE(单互动成本)", "笔记ROI", "搜索SOV", "话题浏览量"],
        }

    def _xhs_conversion(self) -> dict:
        return {
            "phase": "conversion", "platform": "xiaohongshu",
            "title": "小红书转化策略",
            "steps": [
                "笔记挂链：商品笔记直接挂载小红书商城链接",
                "评论区引导：置顶购买链接+优惠口令",
                "私信转化：自动回复设置+引导添加微信/进群",
                "直播转化：直播间专属优惠+限时限量",
                "信任背书：素人真实测评+使用前后对比",
                "小红书商城：店铺装修+商品详情页优化",
                "限时活动：新品首发价/粉丝专享价/节日特惠",
            ],
            "key_metrics": ["笔记挂链CTR", "商城转化率", "私域导流率", "直播间CVR", "客单价"],
        }

    def _xhs_retention(self) -> dict:
        return {
            "phase": "retention", "platform": "xiaohongshu",
            "title": "小红书复购与社群运营",
            "steps": [
                "笔记矩阵持续输出：每月15-30篇品牌+达人+素人笔记",
                "粉丝群运营：小红书粉丝群专属福利+新品试用",
                "UGC激励：晒单返现/新品体验官活动",
                "私域沉淀：小红书→微信社群→复购闭环",
                "品牌号运营：企业号认证+品牌故事+店铺活动",
                "数据复盘：月度笔记数据+转化数据分析优化",
            ],
            "key_metrics": ["粉丝增长率", "笔记月均互动", "复购率", "私域社群人数", "品牌搜索量"],
        }

    def generate_cross_platform_swot(self, platform_data: dict[str, list]) -> dict:
        swot = {}
        for platform_name, items in platform_data.items():
            if not isinstance(items, list) or not items:
                continue

            prices = [i.price for i in items if i.price]
            reviews = [i.review_count for i in items if i.review_count]
            bs_count = sum(1 for i in items if i.is_bestseller)

            avg_price = sum(prices) / len(prices) if prices else 0
            avg_reviews = sum(reviews) / len(reviews) if reviews else 0

            strength_points = []
            if prices and min(prices) < avg_price * 0.7:
                strength_points.append(f"Lowest price advantage ({min(prices)} vs avg {avg_price:.0f})")
            if avg_reviews > 1000:
                strength_points.append(f"High review volume ({avg_reviews:.0f} avg)")
            if bs_count / len(items) > 0.5:
                strength_points.append(f"Strong brand presence ({bs_count}/{len(items)} brand stores)")

            weakness_points = []
            if avg_price > sum(prices) / len(prices) * 1.3 and prices:
                weakness_points.append("Priced above category average")
            if avg_reviews < 100 and reviews:
                weakness_points.append("Low review volume — weak social proof")

            opportunity_points = [
                f"Price gap: {min(prices)}-{max(prices)} range" if len(prices) >= 2 else "",
                f"{platform_name} market expanding — content/live commerce opportunities",
            ]
            opportunity_points = [o for o in opportunity_points if o]

            threat_points = []
            if bs_count / len(items) > 0.7 and items:
                threat_points.append("Brand store monopoly threat")
            if len(items) > 20:
                threat_points.append("High seller density — intense competition")

            swot[platform_name] = {
                "strengths": strength_points or ["Competitive pricing position"],
                "weaknesses": weakness_points or ["Limited differentiation signals"],
                "opportunities": opportunity_points or ["Market growth potential"],
                "threats": threat_points or ["New entrants risk"],
                "summary": {
                    "items_analyzed": len(items),
                    "avg_price": round(avg_price, 2),
                    "brand_store_ratio": round(bs_count / len(items), 2) if items else 0,
                },
            }
        return swot

    def analyze_price_elasticity(self, items: list) -> dict:
        if not items:
            return {"error": "No data"}

        prices = sorted([i.price for i in items if i.price])
        if len(prices) < 5:
            return {"error": "Need at least 5 items with prices"}

        sales = [i.review_count or 0 for i in items if i.price]
        if sum(sales) == 0:
            sales = None

        n = len(prices)
        bins = 5
        bin_size = (prices[-1] - prices[0]) / bins if prices[-1] > prices[0] else 1

        price_bands = []
        for b in range(bins):
            lo = prices[0] + b * bin_size
            hi = lo + bin_size
            items_in_band = [i for i in items if i.price and lo <= i.price <= hi]
            band_sales = sum(i.review_count or 0 for i in items_in_band)
            price_bands.append({
                "range": f"{lo:.0f}-{hi:.0f}",
                "count": len(items_in_band),
                "avg_price": round(sum(i.price for i in items_in_band) / max(1, len(items_in_band)), 2),
                "total_sales": band_sales,
                "concentration": round(len(items_in_band) / max(1, len(items)), 2),
            })

        mid_idx = n // 2
        median_price = prices[mid_idx]
        q1_price = prices[n // 4]
        q3_price = prices[n * 3 // 4]

        sweet_spot = None
        max_items_band = max(price_bands, key=lambda b: b["count"])
        if max_items_band["count"] >= 3:
            sweet_spot = f"{max_items_band['range']} CNY ({max_items_band['count']} items)"

        return {
            "price_range": {"min": prices[0], "q1": q1_price, "median": median_price, "q3": q3_price, "max": prices[-1]},
            "price_bands": price_bands,
            "sweet_spot": sweet_spot,
            "advice": (
                f"Optimal price zone: {sweet_spot}" if sweet_spot
                else f"Consider positioning between {q1_price:.0f}-{q3_price:.0f} CNY"
            ),
        }

    def predict_seasonal_trend(self, category: str, historical_months: Optional[list[dict]] = None) -> dict:
        seasonal_patterns = {
            "clothing": {"peak": [3, 4, 9, 10], "trough": [1, 7, 12], "growth": "stable"},
            "beauty": {"peak": [11, 12, 1], "trough": [6, 7, 8], "growth": "growing"},
            "electronics": {"peak": [11, 12, 6], "trough": [2, 3, 4], "growth": "stable"},
            "home": {"peak": [3, 4, 10, 11], "trough": [1, 2, 7], "growth": "growing"},
            "food": {"peak": [1, 11, 12], "trough": [6, 7, 8], "growth": "stable"},
            "baby": {"peak": [5, 6, 11], "trough": [2, 3, 8], "growth": "stable"},
            "sport": {"peak": [3, 4, 5, 10], "trough": [1, 2, 7, 12], "growth": "growing"},
            "general": {"peak": [11, 12], "trough": [6, 7], "growth": "stable"},
        }

        pattern = seasonal_patterns.get(category, seasonal_patterns["general"])
        month_names = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
                       7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}
        current_month = _dt.now().month

        next_peak = [m for m in sorted(pattern["peak"]) if m > current_month]
        if not next_peak:
            next_peak = [min(pattern["peak"])]
        days_to_peak = (next_peak[0] - current_month) * 30 if next_peak[0] > current_month else (12 - current_month + next_peak[0]) * 30

        return {
            "category": category,
            "peak_months": [month_names[m] for m in pattern["peak"]],
            "trough_months": [month_names[m] for m in pattern["trough"]],
            "growth_trend": pattern["growth"],
            "next_peak": f"{month_names[next_peak[0]]} (in ~{days_to_peak} days)",
            "advice": (
                f"Prepare inventory and campaigns now for {month_names[next_peak[0]]} peak (est. {days_to_peak} days)"
                if days_to_peak < 90
                else f"Plan ahead for {month_names[next_peak[0]]} peak season"
            ),
        }

    def full_cross_platform_matrix(self, data_by_platform: dict[str, list]) -> str:
        matrix: list[list[str]] = []
        header = ["Metric"] + list(data_by_platform.keys())
        matrix.append(header)

        metrics = [
            ("Items", lambda items: str(len(items))),
            ("Avg Price", lambda items: f"{sum(i.price for i in items if i.price)/max(1,len([1 for i in items if i.price])):.2f}" if any(i.price for i in items) else "N/A"),
            ("Price Range", lambda items: f"{min(i.price for i in items if i.price)}-{max(i.price for i in items if i.price)}" if len([i.price for i in items if i.price])>=2 else "N/A"),
            ("Bestseller%", lambda items: f"{sum(1 for i in items if i.is_bestseller)/max(1,len(items))*100:.0f}%"),
            ("Avg Reviews", lambda items: f"{int(sum(i.review_count or 0 for i in items)/max(1,len(items))):,}"),
        ]

        for metric_name, fn in metrics:
            row = [metric_name]
            for items in data_by_platform.values():
                row.append(fn(items) if isinstance(items, list) else str(items))
            matrix.append(row)

        col_widths = [max(len(str(row[i])) for row in matrix) for i in range(len(header))]
        lines = []
        for row in matrix:
            line = " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))
            lines.append(line)
            if row == matrix[0]:
                lines.append("-+-".join("-" * w for w in col_widths))
        return "\n".join(lines)