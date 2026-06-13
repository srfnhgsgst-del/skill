from ecommerce_ops_skill.platform import Platform, StrategyPhase


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

    def _selection_phase(self, category: str, market: str, budget: str) -> dict:
        if self.platform == Platform.AMAZON:
            return self._amazon_selection(category, market, budget)
        elif self.platform in (Platform.TAOBAO, Platform.TMALL):
            return self._taobao_selection(category)
        elif self.platform == Platform.JD:
            return self._jd_selection(category)
        else:
            return {"phase": "selection", "platform": self.platform.value, "steps": ["to be refined"], "key_metrics": []}

    def _listing_phase(self, category: str, market: str, budget: str) -> dict:
        if self.platform == Platform.AMAZON:
            return self._amazon_listing()
        elif self.platform in (Platform.TAOBAO, Platform.TMALL):
            return self._taobao_listing()
        elif self.platform == Platform.JD:
            return self._jd_listing()
        else:
            return {"phase": "listing", "platform": self.platform.value, "steps": ["to be refined"], "key_metrics": []}

    def _traffic_phase(self, category: str, market: str, budget: str) -> dict:
        if self.platform == Platform.AMAZON:
            return self._amazon_traffic(budget)
        elif self.platform in (Platform.TAOBAO, Platform.TMALL):
            return self._taobao_traffic(budget)
        elif self.platform == Platform.JD:
            return self._jd_traffic(budget)
        else:
            return {"phase": "traffic", "platform": self.platform.value, "steps": ["to be refined"], "key_metrics": []}

    def _conversion_phase(self, category: str, market: str, budget: str) -> dict:
        if self.platform == Platform.AMAZON:
            return self._amazon_conversion()
        elif self.platform in (Platform.TAOBAO, Platform.TMALL):
            return self._taobao_conversion()
        elif self.platform == Platform.JD:
            return self._jd_conversion()
        else:
            return {"phase": "conversion", "platform": self.platform.value, "steps": ["to be refined"], "key_metrics": []}

    def _retention_phase(self, category: str, market: str, budget: str) -> dict:
        if self.platform == Platform.AMAZON:
            return self._amazon_retention()
        elif self.platform in (Platform.TAOBAO, Platform.TMALL):
            return self._taobao_retention()
        elif self.platform == Platform.JD:
            return self._jd_retention()
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