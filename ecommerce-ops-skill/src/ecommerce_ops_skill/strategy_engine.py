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
                "BSR Top 100 + Brand Analytics data: identify hot categories with low brand concentration",
                "Product Opportunity Explorer: find unmet demand niches with high clicks but low conversion",
                "Jungle Scout / Keepa for category capacity & demand trend analysis (6-12 month lookback)",
                "Target $15-$40 price band for high CVR, $40-$80 for high AOV differentiated products",
                "Analyze competitor negative reviews (top 3 pain points) → product improvement opportunities",
                "FBA fee calculator + margin simulator: ensure gross margin > 35%, net > 15%",
                "Check patent/IP risk via USPTO search + competitor patent analysis",
                "Seasonal timing: launch 8-12 weeks before peak season for keyword ranking building",
            ],
            "key_metrics": ["Avg BSR Top 100", "Category demand trend", "Avg reviews/launch", "Brand concentration ratio", "Avg price/margin", "Seasonal index"],
            "risk_warnings": ["10k+ reviews per product → hard entry", "Price war categories (<20% margin)", "Amazon Basics direct competition", "Heavy seasonal risk (>60% annual sales in 3 months)"],
        }

    def _amazon_listing(self) -> dict:
        return {
            "phase": "listing", "platform": "amazon",
            "title": "Amazon Listing optimization",
            "steps": [
                "Title: Brand + Core Keyword + Key Feature + Scenario/Use Case (<200 chars)",
                "Bullets: 5 points — top 2 must contain core keywords + benefits, include comparison data",
                "A+ Content Premium: brand story + comparison chart + 4 modules minimum",
                "Search Terms backend: long-tail keywords + misspellings + synonyms (not in title)",
                "Main image: pure white 255/255/255, >85% fill, lifestyle alternative image recommended",
                "Video upload: 30-60 sec product demo, auto-play on desktop, +15% CVR vs no video",
                "Variation theme: size/color/capacity merge for shared reviews & improved discoverability",
                "Pricing strategy: launch 5-10% below avg market → after 10+ reviews increase to target",
                "AI image generation: use AI tools for lifestyle scenes, A/B test main image variations",
                "Brand Registry: A+ Content + Brand Story + Sponsored Brands + Brand Analytics access",
            ],
            "key_metrics": ["Title keyword coverage", "Main image CTR", "A+ Content conversion lift", "Video view rate", "Variation CVR"],
        }

    def _amazon_traffic(self, budget: str) -> dict:
        cfg = {"low": "$10-20/d", "medium": "$30-80/d", "high": "$100-300/d"}.get(budget, "$30-80/d")
        return {
            "phase": "traffic", "platform": "amazon",
            "title": "Amazon traffic acquisition (PPC + organic + off-Amazon)",
            "budget_recommendation": {"daily_ppc": cfg},
            "steps": [
                "SP auto 7-14d → manual keyword targeting: identify high-CVR search terms, negative low performers",
                "SP manual: exact match high-conversion keywords + phrase match 2nd tier + broad match discovery",
                "SB: Brand Store entry + brand keyword defense + category ASIN targeting",
                "SD: competitor detail page targeting + category targeting + ASIN audience retargeting",
                "DSP (Amazon Demand-Side Platform): programmatic display across Amazon + 3rd party sites",
                "Amazon Posts: free influencer-style social feed on product detail pages, drive organic discovery",
                "Amazon Live: live stream product demos, pin to product detail page for ongoing views",
                "Coupon + LD (Lightning Deal) + 7DD (7-Day Deal) for BSR burst and keyword ranking push",
                "Off-Amazon traffic: TikTok/Instagram influencer → Amazon Store link + deal sites + email list",
                "Long-tail keyword rank building → short-tail defense: incremental keyword strategy",
                "Brand Tailored Audiences: retarget shoppers who viewed but didn't purchase",
                "New product daily PPC: {} (recommend 70% SP + 20% SB + 10% SD)".format(cfg),
            ],
            "key_metrics": ["ACoS/TACoS", "Organic + paid keyword rank", "Impression share", "CTR/CVR by campaign type", "DSP ROAS", "New-to-brand rate"],
        }

    def _amazon_conversion(self) -> dict:
        return {
            "phase": "conversion", "platform": "amazon",
            "title": "Amazon CVR optimization",
            "steps": [
                "Price anchoring: was-price + current price (30-50% off perception) + coupon badge overlay",
                "Coupon strategy: green coupon badge (high-CVR visual) + BOGO + volume discounts (tiered)",
                "Review seeding: Amazon Request a Review (automated email) + Vine Program (early reviews)",
                "Q&A seeding: seed 3-5 Q&As addressing top concerns from competitor negative reviews",
                "A+ Content Premium: brand story module + comparison chart + 4K lifestyle images",
                "FBA Prime badge: highest trust signal → 15-25% CVR uplift vs FBM",
                "Inventory management: never stock out — BSR resets to zero, rank recovery takes 1-3 weeks",
                "A/B test: price points, main image, bullet order, A+ modules for statistical significance",
                "Brand Tailored Promotions: exclusive discount to Followers + past purchasers",
                "Post-purchase insert: quality check + review incentive + cross-sell QR code",
            ],
            "key_metrics": ["Unit Session % (CVR)", "Cart abandonment rate", "AOV", "CAC", "New-to-brand OPM"],
        }

    def _amazon_retention(self) -> dict:
        return {
            "phase": "retention", "platform": "amazon",
            "title": "Amazon retention & brand loyalty",
            "steps": [
                "Subscribe & Save: consumables/replenishables enrollment, recurring revenue + brand loyalty",
                "Brand Store followers: drive followers via Posts + Sponsored Brands → owned traffic channel",
                "Post-purchase email sequence: order confirmation (1d) → delivery (3d) → review request (7d) → cross-sell (14d)",
                "Cross-sell bundles: frequently bought together + bundle deals (15-20% discount on bundle)",
                "Amazon Live for repeat engagement: weekly live stream for existing brand customers",
                "Brand Tailored Audience: retarget past purchasers with new product launches + exclusive deals",
                "Negative review management: respond within 24h, offer replacement/refund → Amazon will remove upon resolution",
                "Product insert: QR code to Brand Store + cross-sell category + review incentive (compliant)",
                "Variant upsell: email/notification on new color/size/capacity launch to past purchasers",
            ],
            "key_metrics": ["Repeat purchase rate", "Customer LTV", "S&S enrollment rate", "Return rate", "Brand follower growth"],
        }

    def _taobao_selection(self, category: str) -> dict:
        return {
            "phase": "selection", "platform": "taobao",
            "title": "淘宝/天猫选品策略",
            "steps": [
                "通过生意参谋市场排行分析：锁定搜索人气高、在线商品少的蓝海品类",
                "对比天猫和C店价格带分布：寻找天猫占比<60%且C店有生存空间的区间",
                "分析月销量≥1000的商品特征矩阵：标题关键词/主图风格/定价策略/店铺DSR/客群画像",
                "识别搜索词竞争度：直通车市场平均CPC+头部商品收藏加购率+品牌集中度",
                "利用AI工具分析1688跨境/产业带供应端：筛选供应充足+品质稳定+毛利>45%的品类",
                "结合小红书/抖音内容趋势：提前识别热门话题+种草品类，抢占时间窗口",
                "季节性产品提前4-6周布局（上架→测款→推广→爆发的4周节奏）",
                "关注平台扶持品类：淘宝产业带/天猫新品/天猫国际等政策红利方向",
            ],
            "key_metrics": ["搜索人气/在线商品比", "天猫占比", "平均售价/毛利", "DSR均值", "直通车CPC", "内容热度趋势"],
            "risk_warnings": ["天猫旗舰店垄断品类(TOP10天猫>80%)", "价格战品类(平均毛利<20%)", "高退货率品类(服饰>30%)", "品牌侵权高风险品类"],
        }

    def _taobao_listing(self) -> dict:
        return {
            "phase": "listing", "platform": "taobao",
            "title": "淘宝/天猫商品上架与内容优化",
            "steps": [
                "标题公式：核心词+属性词+场景词+促销词（30字），核心词前置+紧密排列加权搜索权重",
                "主图差异化：首图避免纯白底→功能卖点图/场景图/对比图/AIGC生成创意图",
                "5张主图策略：首图(吸引点击)→场景图(带入感)→细节图(产品力)→对比图(差异)→促销图(促转化)",
                "详情页前三屏：痛点引入→解决方案→产品核心卖点→信任背书(品牌/资质/检测报告)",
                "SKU命名引流+利润：引流SKU(最低价)→主销SKU(标准版)→利润SKU(套装版)，梯度定价",
                "视频矩阵：15-30秒产品展示+使用教程+开箱视频+买家秀合集，视频加权搜索排名",
                "AIGC内容生成：AI生成标题/卖点/场景图/短视频，大幅降低内容生产成本",
                "手机端优先优化：>80%流量来自手淘，逐屏检查手机端展示效果(字体/图片/排版)",
                "上架时间策略：工作日10:00-11:00或20:00-22:00黄金时段，提前加入淘宝天猫新品池",
                "直播切片二次利用：直播精彩片段剪辑成商品详情视频+短视频内容，一鱼多吃",
            ],
            "key_metrics": ["搜索曝光量", "主图点击率", "加购率", "详情页跳失率", "手淘首页推荐占比", "视频完播率"],
        }

    def _taobao_traffic(self, budget: str) -> dict:
        cfg = {"low": "￥50-100/天", "medium": "￥200-500/天", "high": "￥800-2000/天"}.get(budget, "￥200-500/天")
        return {
            "phase": "traffic", "platform": "taobao",
            "title": "淘宝/天猫流量获取（搜索+推荐+内容三引擎）",
            "budget_recommendation": {"daily_ppc": cfg},
            "steps": [
                "【搜索】直通车：广泛匹配测词7天→精准匹配高转化词→智能出价优化ROI→降低弱词出价",
                "【推荐】引力魔方：首页猜你喜欢+购物中+支付后资源位，适合标品爆款拉推荐流量",
                "【智能】万相台无界版：AI全智能投放(搜索+推荐+内容一体化)，一键投放+系统自动优化",
                "【内容】淘宝逛逛：短视频+图文种草内容，可挂商品链接，优质内容获取手淘首页免费流量",
                "【直播】淘宝直播：店铺自播(日播4-8h)+达人带货(头部/腰部/KOC)，直播GMV占比持续上升",
                "【CPS】淘客推广：设置阶梯佣金(基础5-15%+冲量30%)，团长渠道合作快速起量",
                "【活动】活动报名：天天特卖→淘宝好价→聚划算→百亿补贴，阶梯式活动叠加爆发",
                "【站外】跨平台引流：抖音短视频挂跳转链接+小红书笔记种草→淘宝搜索/直播转化",
                "【推荐】AI智能投放：万相台无界版全店智投，适合中小卖家低门槛高效投放",
                "每日预算建议：{}（搜索50% + 推荐30% + 内容20%）".format(cfg),
            ],
            "key_metrics": ["直通车ROI", "万相台ROI", "引力魔方CTR", "直播GMV占比", "淘客成交占比", "免费/付费流量比"],
        }

    def _taobao_conversion(self) -> dict:
        return {
            "phase": "conversion", "platform": "taobao",
            "title": "淘宝/天猫转化优化",
            "steps": [
                "价格锚定：划线原价+促销到手价，营造高折扣感知(建议划线价/实际价≥1.5x)",
                "优惠券组合：店铺券+商品券+平台券三券叠加 + 限时领券弹窗(新客/加购/收藏触发)",
                "评价管理：好评返现(合规方式：晒图返红包)，引导图文+视频评价，前10条评价关键",
                "问大家：主动回答高频疑问(产品/物流/售后)，消除犹豫→转化提升10-15%",
                "服务承诺：7天无理由+运费险+顺丰/极速达，降低决策门槛→CVR提升5-10%",
                "关联营销：详情页顶部(搭配推荐)+底部(看了又看)+购物车(凑单推荐)，提升AOV",
                "限时促销：倒计时+库存进度条+已售XX件+限量XX份，社会证明+稀缺双驱动",
                "AI智能客服：7x24小时自动回复常见问题+主动催付(加购未下单/提交未支付)",
                "直播转化：直播间专享价+直播限时券+直播限量赠品，直播间CVR通常>图文3x",
                "售后闭环：24h客服响应+主动联系差评处理+物流跟进+复购券发放",
            ],
            "key_metrics": ["转化率(CVR)", "客单价(AOV)", "DSR评分", "退货率", "店铺复购率", "AI客服转化率"],
        }

    def _taobao_retention(self) -> dict:
        return {
            "phase": "retention", "platform": "taobao",
            "title": "淘宝私域与复购运营",
            "steps": [
                "店铺粉丝群精细化：上新提醒+粉丝专享价+群内秒杀+互动有奖，保持社群活跃度",
                "品牌会员体系：免费入会→消费积分→等级权益(普通/高级/VIP)→生日礼+会员日专属折扣",
                "淘宝订阅内容运营：每周2-4条内容推送(新品/教程/生活方式)，保持粉丝触达率",
                "CRM自动化营销：新客7天复购券+30天沉睡唤醒券+60天流失召回大额券+生日/节日营销",
                "微信私域沉淀：包裹卡引导+售后评价引导+会员专属加微信福利，构建复购闭环",
                "组合SKU套餐：热销款+关联款组合装(满减/优惠)，提升客单价20-30%",
                "上新节奏：每月2-4款持续上新，配合订阅+粉丝群通知，保持店铺活跃与搜索权重",
                "老客户专享：老客专享价+老客专享品+老客积分加倍，提升复购率",
                "数据驱动的客户分层：高价值客户(1v1维护)/活跃客户(复购券)/沉睡客户(大额唤醒)/流失客户(召回)",
            ],
            "key_metrics": ["复购率", "粉丝增长率", "会员GMV占比", "老客流失率", "客单价提升率", "微信私域人数"],
        }

    def _jd_selection(self, category: str) -> dict:
        return {
            "phase": "selection", "platform": "jd",
            "title": "京东选品策略",
            "steps": [
                "京东商智品类分析：搜索点击指数+访客指数+加购指数，锁定蓝海三级类目",
                "评估自营占比：自营>60%的品类POP商家突破难度大，选择自营<40%的品类",
                "分析搜索结果前三页品牌分布：品牌集中度——TOP5品牌>70%的品类难进入",
                "京东物流打标溢价空间：入仓商品平均溢价10-15%，但占用资金需计算周转",
                "评估京东好店门槛：DSR≥9.38+物流≥9.5+服务≥9.3，未达标品类需慎重",
                "分析京准通CPC水平：品类大词CPC+转化率→估算获客成本是否可接受",
                "关注京东新百货/京东超市等频道扶持方向，优先选择平台主推品类",
                "选择POP卖家竞争相对小的长尾品类，或有一定品牌/供应链壁垒的方向",
            ],
            "key_metrics": ["自营/三方占比", "TOP5品牌集中度", "京东好店达标率", "京准通CPC", "入仓资金周转"],
            "risk_warnings": ["京东自营垄断品类(>60%自营)", "3C数码高退货品类(退货率>25%)", "需入仓品类(资金占用高)", "品牌授权严格品类"],
        }

    def _jd_listing(self) -> dict:
        return {
            "phase": "listing", "platform": "jd",
            "title": "京东商品上架与内容优化",
            "steps": [
                "标题：品牌+核心词+属性/规格+场景词+服务承诺（50字内），核心关键词前置",
                "主图策略：白底首图(搜索展示)+场景图(带入感)+卖点图(差异化)+促销图+规格对比图(≥5张)",
                "商详页面结构：关联版式(TOP)→规格参数→场景痛点→产品展示→质检/资质→品牌故事→售后承诺",
                "京东主图视频+商详视频：15-30秒产品展示+使用教程，视频加权搜索排名+提升转化",
                "SPU聚合管理：同款不同规格聚合SPU，减少SKU分散，提升搜索权重+共享评价",
                "京东好店打标：DSR≥9.38+物流≥9.5+服务≥9.3=搜索加权+活动优先",
                "入仓京东物流：搜索加权(约+5-10%)+产品页时效标签+转化率提升10-15%",
                "3D/AR展示：京东3D购物+AR试用，适合家居/数码/美妆品类，差异化竞争力",
                "AI智能生成内容：AI生成标题/卖点/场景图，降低内容生产成本，快速上架",
            ],
            "key_metrics": ["标题关键词权重", "主图点击率", "商详停留时间", "SPU转化率", "物流时效评分", "视频完播率"],
        }

    def _jd_traffic(self, budget: str) -> dict:
        cfg = {"low": "￥80-150/天", "medium": "￥300-600/天", "high": "￥1000-2500/天"}.get(budget, "￥300-600/天")
        return {
            "phase": "traffic", "platform": "jd",
            "title": "京东流量获取（搜索+推荐+内容+微信生态）",
            "budget_recommendation": {"daily_ppc": cfg},
            "steps": [
                "【搜索】京准通-京东快车：品类大词(精准匹配)+品牌词(防守)+长尾词(低CPC高转化)",
                "【推荐】京准通-购物触点：首页推荐(拉新)+商详底部(拦截)+购物车(促转化)+支付页(再营销)",
                "【智能】京准通-全站推广：AI智能投放搜索+推荐全渠道，一键托管适合新手卖家",
                "【内容】京东发现+京东短视频：种草内容布局，优质内容可获得京东首页推荐流量",
                "【直播】京东直播：店铺自播(日播4-8h)+达人直播合作(头部背书+腰部铺量)",
                "【活动】京东秒杀+品牌闪购+百亿补贴：大促爆发流量，需要提前报名+价格优势",
                "【会员】京东Plus会员专享价：Plus用户消费力≥普通用户3倍，Plus专享标签提升点击率",
                "【微信生态】京东小程序+微信搜一搜+朋友圈广告：利用腾讯社交资源引流",
                "【站外】抖音/小红书种草→京东搜索转化：跨平台内容引流策略",
                "每日预算建议：{}（搜索50% + 推荐30% + 内容20%）".format(cfg),
            ],
            "key_metrics": ["京东快车ROI", "购物触点CTR", "全站推广ROI", "秒杀GMV", "Plus用户占比", "免费/付费流量比"],
        }

    def _jd_conversion(self) -> dict:
        return {
            "phase": "conversion", "platform": "jd",
            "title": "京东转化优化",
            "steps": [
                "京东物流打标：搜索加权+时效(当日/次日达)标签+转化率提升10-15%",
                "京东好店认证：DSR≥9.38+物流≥9.5+服务≥9.3=搜索加权+活动优先+消费者信任",
                "价格锚定：京东价划线+到手价(券后)+Plus专享价，三重价格感知",
                "评价管理：30字+3图+视频评价获得高权重，置顶优质评价+差评24h内回复",
                "京东Plus会员深度运营：Plus价+Plus券+Plus专享礼包，Plus用户转化率>普通用户2x",
                "售后服务承诺：闪电退款+上门取件+以换代修+延长质保→降低决策门槛",
                "关联推荐：商详页搭配购+购物车凑单+下单页加购，提升AOV 15-25%",
                "白条/金条分期：3/6/12期免息或低息，降低支付压力→高客单品类CVR提升20%+",
                "京东秒杀标签：商品页打上秒杀/百亿补贴/Plus专享标，提升紧迫感和点击率",
                "AI智能定价：基于竞品价格/库存/销量数据动态调整售价+优惠券力度",
            ],
            "key_metrics": ["商详转化率", "客单价", "Plus订单占比", "DSR均值", "物流时效达成率", "白条使用占比"],
        }

    def _jd_retention(self) -> dict:
        return {
            "phase": "retention", "platform": "jd",
            "title": "京东复购与会员运营",
            "steps": [
                "店铺会员体系：免费入会→消费积分→等级权益(普通/银卡/金卡/钻石)→会员日+生日礼+专享价",
                "关注店铺引导：下单页+详情页+售后页多重引导关注→搜索加权+粉丝触达渠道",
                "Plus会员联合运营：Plus专享品+Plus专享券+Plus会员日→Plus用户LTV=普通用户3x",
                "CRM自动化营销：下单后7天复购券+30天沉睡唤醒+60天流失召回+生日/节日营销",
                "跨品类联动：基于购买历史推荐关联品类(买手机→推荐耳机/壳膜)，提升客户生命周期",
                "订阅型商品(定期购)：日用消耗品定期购模式→稳定复购+可预测库存",
                "服务增值：延保服务+配件组合+以旧换新连接新机购买→服务驱动的复购增长",
                "京东健康标签：为健康/滋补品类建立定期服用提醒+周期性复购机制",
                "企业微信私域：京东订单→企业微信社群→1v1服务+专属福利→复购+转介绍",
            ],
            "key_metrics": ["复购率", "Plus会员复购率", "客单价提升率", "店铺粉丝数", "会员活跃度", "LTV"],
        }

    def _pdd_selection(self, category: str) -> dict:
        return {
            "phase": "selection", "platform": "pinduoduo",
            "title": "拼多多选品策略",
            "steps": [
                "分析类目价格带金字塔：0-20(引流)/20-50(主销)/50-100(利润)/100+(品牌)，定位自己的价格区间",
                "查看已拼10万+爆款特征矩阵：价格/主图风格/标题关键词/DSR/发货地，提炼爆款公式",
                "供应链深度评估：是否能做到类目价格前30%+品质前50%？不能则需差异化或放弃",
                "避开品牌旗舰店/黑标品牌密集品类(白牌无竞争优势)，选择白牌有机会的民生品类",
                "关注百亿补贴+秒杀频道+9.9特卖：平台扶持的高流量频道，报名门槛和ROI",
                "测算全链路ROI：多多进宝佣金(30-50%)+多多搜索CPC+平台佣金(0.6-5%)+补贴成本",
                "低客单(￥0-20)走量策略 vs 中客单(￥20-80)利润策略 vs 高客单(￥80+)品质策略，三选一聚焦",
                "关注多多跨境Temu机会：同供应链可同时做Temu跨境分销，降低库存风险",
            ],
            "key_metrics": ["类目价格带分布", "头部已拼件数", "品牌/白牌占比", "多多搜索CPC", "全链路利润率"],
            "risk_warnings": ["超低价品类(均价<￥10)：毛利率极低(<10%)", "品牌高度集中品类(TOP5>60%)", "高退货率品类(服饰>35%)", "竞品快速跟卖风险"],
        }

    def _pdd_listing(self) -> dict:
        return {
            "phase": "listing", "platform": "pinduoduo",
            "title": "拼多多商品上架优化",
            "steps": [
                "标题公式：促销词+核心关键词+属性词+场景词（30字充分利用），促销词前置提升点击率",
                "主图核心：低价标签(价格标)+卖点图标+场景图，拼多多首图CTR决定流量天花板",
                "10张主图全部使用：首图(价格吸睛)→第2-3张(场景展示)→第4-5张(细节/对比)→第6-7张(功能)→第8-9张(活动/赠品)→第10张(售后承诺)",
                "SKU布局：引流款(最低价拉点击)+主销款(标准价走量)+利润款(高配版赚利润)+活动款(报名活动)",
                "拼单价 vs 单买价策略：拼单价低25-40%驱动拼团动力，单买价作为价格锚点",
                "详情页结构：前3屏(痛点+解决方案+效果对比)→中间(产品参数+买家秀)→底部(品牌+售后)",
                "服务标签：极速退款(提升CVR)+退货包运费(降决策门槛)+48小时发货(平台加权)",
                "AI生成素材：用AI批量生成主图/详情图/短视频，高频测试找到最优素材组合",
                "低价SKU注意：最低价SKU需保证不亏钱，可通过低配版/简装版实现",
            ],
            "key_metrics": ["曝光量", "主图点击率", "转化率", "收藏率", "DSR评分", "引流款点击占比"],
        }

    def _pdd_traffic(self, budget: str) -> dict:
        cfg = {"low": "￥50-100/天", "medium": "￥200-500/天", "high": "￥800-2000/天"}.get(budget, "￥200-500/天")
        return {
            "phase": "traffic", "platform": "pinduoduo",
            "title": "拼多多流量获取（搜索+场景+社交+内容）",
            "budget_recommendation": {"daily_ppc": cfg},
            "steps": [
                "【搜索】多多搜索：类目大词(精准匹配曝光)+精准长尾词(低CPC高转化)+智能词包",
                "【推荐】多多场景：首页推荐(拉新)+活动页(精准人群)+支付页(高转化)+多多果园(下沉)",
                "【智能】全站推广：AI自动优化搜索+场景全渠道投放，一键托管适合新手卖家",
                "【CPS】多多进宝：设置30-50%高佣金吸引推手冲量，团长渠道合作快速起量",
                "【活动】阶梯式报名：9.9特卖→限时秒杀→品牌清仓→百亿补贴，逐级解锁活动门槛",
                "【社交】拼团裂变：2人团基础→3人团提速→分享助力券→砍价免费拿，社交裂变获取自然流量",
                "【内容】多多视频：15-30秒短视频种草带货，挂商品链接，类抖音模式获取内容流量",
                "【站外】跨平台引流：微信社群分享+朋友圈广告+抖音种草→拼多多搜索/直播间转化",
                "每日预算建议：{}（搜索40% + 场景30% + 全站30%）".format(cfg),
            ],
            "key_metrics": ["多多搜索ROI", "场景曝光CTR", "全站推广ROI", "活动GMV占比", "拼团成功率", "多多进宝转化率"],
        }

    def _pdd_conversion(self) -> dict:
        return {
            "phase": "conversion", "platform": "pinduoduo",
            "title": "拼多多转化优化",
            "steps": [
                "价格竞争力为王：同款商品价格需在类目前30%（拼多多用户极度价格敏感，价格是CVR第一因子）",
                "拼单价vs单买价：拼单价低25-40%制造强烈感知差，拼团进度条展示增强社会证明",
                "限时限量优惠：倒计时+库存余量+已拼XX万件+XX人正在拼，多重紧迫感+社会证明驱动",
                "评价体系管理：前10条评价重点维护带图+视频评价，置顶优质评价，差评24h内处理",
                "DSR评分护城河：描述/物流/服务三维平衡，DSR<4.3平台限流，DSR>4.6活动优先",
                "退货包运费+极速退款：降低用户决策门槛，CVR提升5-15%+提升店铺评分",
                "店铺满减策略：满2件减X元/满3件打折/X元凑单提醒，提升客单价20-30%",
                "拼多多直播转化：直播间专享价+限时限量+互动抽奖，直播间CVR通常是图文2-3x",
                "百亿补贴/秒杀标签：商品页打标百亿补贴/限时秒杀→提升信任+紧迫感+点击率",
            ],
            "key_metrics": ["转化率(CVR)", "客单价(AOV)", "DSR均值", "退货率", "店铺评分", "拼团成功率"],
        }

    def _pdd_retention(self) -> dict:
        return {
            "phase": "retention", "platform": "pinduoduo",
            "title": "拼多多复购与店铺运营",
            "steps": [
                "关注店铺引导：首页+详情页+下单后弹窗+评价页多重引导关注→关注即领X元券",
                "复购自动化：下单后72h推送复购券(3-7天有效)+新品上新通知+关联商品推荐弹窗",
                "拼团裂变复购：老客发起拼团享额外折扣→邀请新客拼团→老客复购+新客拉新双赢",
                "新品快讯：店铺上新+活动预告主动通知收藏/关注用户，保持店铺活跃度",
                "评价有礼：好评返现(合规方式：晒图返小额红包)，提升评价质量→提升转化→提升复购",
                "多SKU关联组合：同品类组合装/家庭装/套装，提升客单价+消耗品周期性复购",
                "微信私域沉淀：包裹卡+客服引导→添加企业微信→私域社群→专属福利复购",
                "供应链持续优化：成本降低→价格优势更大→复购率提升→形成正向飞轮",
                "多多买菜/批发渠道复用：同一供应链可扩展到多多买菜/多多批发/跨境Temu",
            ],
            "key_metrics": ["复购率", "粉丝数", "店铺收藏数", "客户留存率(30d/60d)", "客单价趋势", "私域社群人数"],
        }

    def _douyin_selection(self, category: str) -> dict:
        return {
            "phase": "selection", "platform": "douyin",
            "title": "抖音电商选品策略",
            "steps": [
                "双场适配选品：产品需同时适配内容场(短视频/直播)和货架场(搜索/商城)",
                "抖音电商罗盘品类分析：搜索热度环比>20%的品类有蓝海机会",
                "测算GPM(千次观看成交额)+OPM(千次观看订单数)：GPM>800且OPM>15为优质品类",
                "商品卡流量占比：品类商品卡曝光>30%说明货架需求强，可持续获利",
                "高毛利(>55%)覆盖达人佣金(20-40%)+全域推广投放+平台服务费",
                "C2M选品：从用户评论/搜索词/达人爆款中反推产品卖点和差异化方向",
                "产品视觉冲击力+使用场景可视化：抖音用户决策靠视觉和场景代入",
                "季节性产品提前4-6周布局内容矩阵，预热期短视频+预售期直播",
                "避开供应链高度集中的品类（如手机/大家电），选择非标品机会赛道",
            ],
            "key_metrics": ["类目GPM/OPM", "商品卡搜索热度", "带货达人数", "佣金比例", "毛利率", "品类竞争度"],
            "risk_warnings": [
                "标品(白牌优势弱)：内容生产成本高且达人合作门槛低，竞品容易复制",
                "达人佣金>45%品类：利润空间被严重挤压，需强供应链支撑",
                "商品卡流量<15%品类：过度依赖内容场，流量不稳定",
                "头部达人垄断品类(TOP3达人占比>60%)：中小商家破局难度大",
            ],
        }

    def _douyin_listing(self) -> dict:
        return {
            "phase": "listing", "platform": "douyin",
            "title": "抖音商品上架与内容策略",
            "steps": [
                "商品标题SEO：核心词+属性词+场景词+人群词(30字) + 填写卖点标签(10个)",
                "商品主图：1张白底图(搜索展示)+4张场景图(推荐流展示) + 第5张促销信息图",
                "商品详情页：前三屏(痛点+方案+产品)→中间(规格+买家秀+QA)→底部(品牌故事+关联推荐)",
                "商详视频：15-30秒产品使用视频，前3秒展示效果，完播率影响商品卡权重",
                "属性100%填写：品牌+材质+规格+适用人群+使用场景，每多一个属性增加搜索曝光",
                "商品体验分：发货时效+品质退货率+投诉率，体验分<4.4会被限制",
                "短视频内容矩阵：品牌号日更1-2条(品宣/测评/使用教程)，每周至少1条爆款潜力视频",
                "达人短视频：头部达人品牌背书(1-2人)+腰部达人深度种草(5-10人)+KOC素人铺量(50+人)",
                "直播脚本：5分钟讲品循环(30秒开场钩子→1分钟痛点场景→1分钟产品演示→1分钟逼单促单→30秒过渡下一品)",
                "商品卡优化：标题完整度100% + 10张图全传 + 首条评价带图+视频 → 搜索推荐双引擎",
            ],
            "key_metrics": ["商品卡曝光量", "短视频完播率", "直播间GPM", "商品点击率", "加购率", "体验分"],
        }

    def _douyin_traffic(self, budget: str) -> dict:
        cfg = {"low": "￥100-300/天", "medium": "￥500-1500/天", "high": "￥3000-10000/天"}.get(budget, "￥500-1500/天")
        return {
            "phase": "traffic", "platform": "douyin",
            "title": "抖音电商流量获取（内容场+货架场双引擎）",
            "budget_recommendation": {"daily_ad_budget": cfg},
            "steps": [
                "【内容场】千川全域推广：平台AI自动优化人群和出价，适合稳定直播间扩量",
                "【内容场】千川标准推广（短视频引流直播间）：投放高完播率视频→直播间，测素材→稳ROI→放量",
                "【内容场】千川标准推广（直投直播间）：实时直播间画面投放，对主播能力要求高",
                "【货架场】千川搜索广告：抢占品类大词+品牌词搜索第一屏位置",
                "【货架场】商品卡免佣优化：标题SEO+属性完整+评价积累，获取自然搜索+推荐商城流量",
                "巨量星图达人合作：品牌种草(种草任务)+效果带货(带货任务)两用，头部背书+腰部铺量",
                "品牌广告：开屏(TopView)+信息流(FeedsLive)+搜索品专(品牌专区)",
                "短直联动：每天发布2-3条短视频预热线，开播前1小时发布预告视频→开播后千川加热短视频引流直播间",
                "店铺自播常态化：日播6-12小时，稳定开播时长+在线人数是系统推流核心信号",
                "抖音商城活动提报：超值购/品牌馆/秒杀频道/大促会场，抢占货架场坑位",
                "平台大促爆发：618/双11/年货节/抖音好物节→提前15天蓄水+大促期冲量",
                "每日投放预算建议：{}".format(cfg),
            ],
            "key_metrics": ["全域推广ROI", "直播间GPM/OPM", "短视频播放量", "商品卡搜索排名", "商品卡GMV占比", "达人带货GMV"],
        }

    def _douyin_conversion(self) -> dict:
        return {
            "phase": "conversion", "platform": "douyin",
            "title": "抖音电商转化策略（直播间+商品卡双链路）",
            "steps": [
                "【直播间】5分钟讲品循环节奏：开场钩子(30s)→痛点场景(60s)→产品演示(60s)→逼单促单(90s)→过渡下一品(60s)",
                "【直播间】黄金前3分钟：快速锁定用户注意力(悬念/痛点/效果对比)，平均停留<2分钟需优化话术",
                "【直播间】互动提权：点赞抽奖→评论关键词→福袋留人→关注领券→加粉丝团专属价",
                "【直播间】逼单组合拳：限时限量+库存倒数+已售XX件+即将涨价+赠品加码",
                "【直播间】信任体系：品牌授权展示+质检报告+达人同款背书+买家秀滚动+7天无理由+运费险",
                "【直播间】价格策略：直播间专享价(比日常低15-30%)+满减(满2件8折)+赠品(前100名加赠)",
                "【商品卡】商品主图：第1张白底图(搜索展示)+信息图(卖点突出)→提升搜索点击率",
                "【商品卡】详情页转化：前三屏说服力(痛点+方案+对比图)+买家秀+QA+限时优惠标签",
                "【商品卡】评价维护：好评置顶+差评24小时内回复+引导带图视频评价→评价影响搜索排名",
                "搜索承接优化：品牌词+核心品类词的搜索结果显示商品卡(带优惠标签)+达人视频+直播间",
            ],
            "key_metrics": ["直播间CVR", "平均停留时长(>2min)", "互动率(>3%)", "GPM(>1000)", "退单率", "商品卡CVR", "搜索点击率"],
        }

    def _douyin_retention(self) -> dict:
        return {
            "phase": "retention", "platform": "douyin",
            "title": "抖音电商复购与私域运营",
            "steps": [
                "粉丝群精细化运营：新品体验官招募+粉丝专属折扣+直播优先通知+群内专属秒杀",
                "品牌会员体系：免费入会→消费积分→等级权益(银卡/金卡/钻石)→生日礼+会员日专属折扣",
                "店铺自播常态化：固定每日开播时段(如19:00-23:00)，培养用户定时观看习惯，粉丝回访率提升30%+",
                "短视频日更策略：每天1-3条(产品使用+客户见证+行业知识+幕后花絮)，保持账号活跃度",
                "售后体验闭环：24小时发货+7天无理由+极速退款+破损包赔，体验分>4.7获得流量加权",
                "复购触发机制：下单后72小时推送复购券(7天有效)+关联商品推荐+直播间复购专享福利",
                "CRM全链路追踪：直播间观看→互动→商品点击→下单→收货→评价→复购，数据驱动精准触达",
                "私域沉淀路径：抖音粉丝群→引导关注企业微信→企微社群→1v1服务→复购+转介绍",
                "云图数据应用：基于A1-A5人群资产分析，制定拉新/种草/转化/复购各阶段精细化策略",
                "客户分层运营：新客(首单优惠)→活跃客(复购券)→沉睡客(大额券唤醒)→流失客(专属福利召回)",
            ],
            "key_metrics": ["粉丝复购率", "粉丝月增长率", "店铺会员数", "直播场均观看", "LTV(客户终身价值)", "体验分"],
        }

    def _xhs_selection(self, category: str) -> dict:
        return {
            "phase": "selection", "platform": "xiaohongshu",
            "title": "小红书选品策略",
            "steps": [
                "关键词笔记饱和度分析：笔记<5k=蓝海/5k-5w=成长/5w-20w=成熟/>20w=红海，选择蓝海-成长的品类",
                "互动率分析：高收藏率(>5%)表明强购买意图→适合卖货；高点赞率(>10%)表明娱乐性强→适合品牌曝光",
                "\"大牌平替\"搜索趋势监控：小红书核心购买心智，寻找优质供应链+品牌溢价的平替空间",
                "笔记互动率与品类匹配：美妆/穿搭/家居(高互动) vs 数码/电器(低互动)→内容成本回收率",
                "视觉冲击力品类优先：小红书是图文+视频种草平台，产品需有视觉差异化卖点",
                "达人生态评估：品类头部KOL数量+平均CPE(互动成本)+带货转化率→判断投入产出",
                "季节性热点预判：提前4-8周布局内容，结合小红书季节话题标签和搜索趋势",
                "内容场景化品类：产品能自然融入穿搭/家居/美妆/母婴/美食/旅行等场景的品类",
            ],
            "key_metrics": ["品类笔记饱和度", "平均互动率/收藏率", "种草达人密度", "CPE(单互动成本)", "CPM(千次曝光)"],
            "risk_warnings": ["笔记高度饱和品类(>20万篇)", "低互动率品类(<2%)", "内容生产门槛高品类(视频/教程成本高)", "品牌敏感品类(用户不信任白牌)"],
        }

    def _xhs_listing(self) -> dict:
        return {
            "phase": "listing", "platform": "xiaohongshu",
            "title": "小红书笔记内容策略",
            "steps": [
                "笔记标题公式：数字+痛点/效果+解决方案+关键词(20字内)，如\"3步搞定XX问题\"",
                "封面图策略：高颜值(第一眼吸睛)+对比效果(使用前后)+文字标签(卖点概括)",
                "笔记结构：开头钩子(0-3s)→痛点场景→产品解决方案→使用效果展示→购买引导→互动引导",
                "标签策略：3-5个精准话题标签(1个大词+2个长尾词+1个场景词+1个品牌词)",
                "发布时间：工作日12:00-13:00/18:00-20:00(通勤高峰)，周末9:00-11:00/21:00-23:00(睡前刷)",
                "评论区运营：置顶购买链接/口令+FAQ(高频问题)+引导互动(问体验/问建议)",
                "笔记合集：按品类/场景/疗程创建合集，延长笔记曝光周期+提升账号专业度",
                "AIGC辅助内容：AI辅助生成标题/文案/标签建议，但内容质量需人工把控保证真实性",
                "多图布局：6-12张图(首图吸睛→过程记录→效果展示→购买/收藏引导)，图文结合最佳",
                "发布频率：品牌号每天1-2条+达人矩阵每周15-30条=稳定流量增长",
            ],
            "key_metrics": ["笔记曝光量", "点击率(封面CTR)", "互动率(赞藏评)", "收藏率(>5%)", "商品点击率", "CPE"],
        }

    def _xhs_traffic(self, budget: str) -> dict:
        cfg = {"low": "￥200-500/篇", "medium": "￥1000-3000/篇", "high": "￥5000-15000/篇"}.get(budget, "￥1000-3000/篇")
        return {
            "phase": "traffic", "platform": "xiaohongshu",
            "title": "小红书流量获取（内容+搜索+广告三引擎）",
            "budget_recommendation": {"per_content_kol": cfg},
            "steps": [
                "【内容】达人矩阵分层运营：KOC素人(50-100人铺量)+尾部KOL(20-30人种草)+腰部KOL(5-10人深度)+头部KOL(1-2人背书)",
                "【内容】品牌号自运营：日常笔记日更1-2条，内容方向(产品测评+使用教程+生活方式+用户故事)",
                "【付费】薯条推广：加热优质笔记(100元起投，CPM约30-50元)，测数据→放量爆文",
                "【付费】聚光平台信息流广告：精准定向(年龄/地域/兴趣/行为)，CPM约50-100元",
                "【付费】搜索广告：抢占品类词+品牌词的搜索结果第一屏位置，CPC约2-8元",
                "【品牌】品牌专区：品牌词搜索结果专属页面，提升品牌信任+搜索转化率",
                "【品牌】话题营销+UGC激励：创建品牌话题，激励用户UGC产生大量内容铺量",
                "【直播】小红书直播：店铺自播(日播2-4h)+达人直播合作，直播间专属价促转化",
                "【搜索】搜索卡位：优化笔记标题+首图+标签，触达搜索流量(小红书搜索占比>30%)",
                "单篇内容投入预算参考：{}（含达人合作+薯条加热）".format(cfg),
            ],
            "key_metrics": ["CPM", "CPE(单互动成本)", "笔记ROI", "搜索SOV(曝光占比)", "话题浏览量", "达人合作转化率"],
        }

    def _xhs_conversion(self) -> dict:
        return {
            "phase": "conversion", "platform": "xiaohongshu",
            "title": "小红书转化策略（笔记+直播+商城+私域）",
            "steps": [
                "【笔记挂链】商品笔记直接挂载小红书商城链接，首条建议为购买引导+优惠信息",
                "【评论区】置顶评论设置购买链接/优惠口令+FAQ+互动引导，评论区是第二转化阵地",
                "【私信】自动回复+关键词触发：发送购买链接、优惠券、加微信/进群引导",
                "【直播】直播转化：直播间专享价+限时限量+互动抽奖+福袋留人，直播间CVR>图文2x",
                "【信任】素人真实测评+使用前后对比+成分/材质解读+品牌故事→建立消费信任",
                "【商城】小红书商城店铺装修：品牌调性统一的店铺首页+商品详情页优化+品牌故事",
                "【活动】限时活动：新品首发价+粉丝专享价+节日特惠+满减券+赠品限量",
                "【口碑】KOC真实体验+大量买家秀+好评晒单：小红书用户极度依赖口碑评价",
                "【跨平台】小红书种草→淘宝/京东搜索转化：外链跳转+搜索词承接+直播间跳转",
            ],
            "key_metrics": ["笔记挂链CTR", "商城CVR", "私域导流率", "直播间CVR", "客单价", "ROI(笔记+投流)"],
        }

    def _xhs_retention(self) -> dict:
        return {
            "phase": "retention", "platform": "xiaohongshu",
            "title": "小红书复购与社群运营",
            "steps": [
                "笔记矩阵持续输出：品牌号日更1-2条+达人矩阵月产30-50条，保持品牌搜索热度",
                "粉丝群精细化运营：专属福利+新品试用+直播预告+互动有奖，提升粉丝粘性和复购",
                "UGC激励机制：晒单返现(红包)+新品体验官(免费试用+产出笔记)+种草有礼(积分/优惠券)",
                "私域沉淀路径：小红书粉丝群/私信→企业微信社群→1v1服务→复购+转介绍闭环",
                "品牌号深度运营：企业号认证+品牌故事+店铺活动+粉丝互动，提升品牌搜索量",
                "会员体系：小红书商城会员=积分+等级+会员价，提升老客复购率",
                "数据复盘：月度笔记数据(曝光/互动/转化)+达人数据(CPE/ROI)+竞品动态分析",
                "AIGC提效：AI辅助生成内容创意/复盘报告/达人brief，提高运营效率",
                "跨平台联动：小红书种草→微信复购闭环，通过私域降低获客成本+提升LTV",
            ],
            "key_metrics": ["粉丝增长率", "笔记月均互动", "复购率", "私域社群人数", "品牌搜索量", "LTV"],
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