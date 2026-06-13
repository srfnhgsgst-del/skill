from ecommerce_ops_skill.platform import Platform, StrategyPhase


class StrategyEngine:
    def __init__(self, platform: Platform = Platform.AMAZON):
        self.platform = platform

    def full_strategy(
        self,
        product_category: str = "",
        target_market: str = "US",
        budget_level: str = "medium",
    ) -> list[dict]:
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
            "sponsored_ratio": sum(1 for i in items if i.is_sponsored) / len(items),
            "bestseller_count": sum(1 for i in items if i.is_bestseller),
        }

    def _selection_phase(self, category: str, market: str, budget: str) -> dict:
        if self.platform == Platform.AMAZON:
            return {
                "phase": StrategyPhase.SELECTION.value,
                "platform": Platform.AMAZON.value,
                "market": market,
                "title": "Amazon {} ".format(market) + "market selection strategy",
                "budget_level": budget,
                "steps": [
                    "Locate Top 100 hot-selling categories via Amazon Best Sellers list",
                    "Use BSR trend analysis to identify rising categories",
                    "Check category capacity and brand concentration via Jungle Scout / Keepa",
                    "Target price range $15-$40 for high conversion rate",
                    "Analyze competitor negative reviews to find consumer pain points",
                    "Calculate FBA fees and profit margin; ensure gross margin > 30%",
                    "Check patent/IP risks to avoid infringement categories",
                ],
                "key_metrics": [
                    "Category Top 100 average BSR",
                    "Average reviews / days since launch",
                    "Brand concentration (Top 10 brands share)",
                    "Average selling price / profit margin",
                    "Category traffic trend (Google Trends + ABA)",
                ],
                "risk_warnings": [
                    "Categories with 10k+ reviews per product: extremely hard to enter",
                    "Price war categories: low margin, high PPC cost",
                    "Seasonal categories: high inventory risk",
                    "Amazon Basics categories: unfair competition",
                ],
            }
        else:
            return {
                "phase": StrategyPhase.SELECTION.value,
                "platform": self.platform.value,
                "title": "{} selection strategy".format(self.platform.display_name),
                "steps": ["Selection strategy to be refined in future versions"],
                "key_metrics": [],
                "risk_warnings": [],
            }

    def _listing_phase(self, category: str, market: str, budget: str) -> dict:
        if self.platform == Platform.AMAZON:
            return {
                "phase": StrategyPhase.LISTING.value,
                "platform": Platform.AMAZON.value,
                "title": "Amazon Listing optimization strategy",
                "steps": [
                    "Title formula: Brand + Core Keyword + Attribute + Scenario + Spec (<200 chars)",
                    "Bullet points: one selling point each, embed high-search keywords in first 2",
                    "Product description: A+ Content (EBC) + Brand Story module",
                    "Search Terms backend: fill long-tail keywords not in title, avoid duplication",
                    "Main image: pure white background (255/255/255), product >85% fill",
                    "Video upload: product usage scenario video to boost CVR",
                    "Variation strategy: merge color/size variations into one listing for shared reviews",
                    "Pricing: slightly below market average at launch to accumulate initial sales",
                ],
                "key_metrics": [
                    "Title keyword coverage",
                    "Main image CTR",
                    "Detail page dwell time",
                    "Variation conversion comparison",
                ],
            }
        else:
            return {
                "phase": StrategyPhase.LISTING.value,
                "platform": self.platform.value,
                "title": "{} listing optimization strategy".format(self.platform.display_name),
                "steps": ["Listing strategy to be refined in future versions"],
                "key_metrics": [],
            }

    def _traffic_phase(self, category: str, market: str, budget: str) -> dict:
        budget_config = {
            "low": {"daily_ppc": "$10-$20", "total_monthly": "$300-$600"},
            "medium": {"daily_ppc": "$30-$80", "total_monthly": "$900-$2400"},
            "high": {"daily_ppc": "$100-$300", "total_monthly": "$3000-$9000"},
        }
        cfg = budget_config.get(budget, budget_config["medium"])
        if self.platform == Platform.AMAZON:
            return {
                "phase": StrategyPhase.TRAFFIC.value,
                "platform": Platform.AMAZON.value,
                "title": "Amazon traffic acquisition strategy",
                "budget_recommendation": cfg,
                "steps": [
                    "SP (Sponsored Products): auto campaign 7-14d -> manual targeting high-converting keywords",
                    "SB (Sponsored Brands): Brand Store traffic, defend brand keywords",
                    "SD (Sponsored Display): competitor detail page targeting + category targeting",
                    "Keyword ranking: long-tail -> short-tail, gradually build organic rank",
                    "Amazon Posts: free content traffic channel (like Instagram)",
                    "Off-Amazon traffic: social media + Influencer Program + deal sites",
                    "Coupon + LD/7DD: promotional events for traffic burst and BSR boost",
                    "New product daily PPC budget: {}".format(cfg["daily_ppc"]),
                ],
                "key_metrics": [
                    "ACoS (Advertising Cost of Sales)",
                    "TACoS (Total ACoS)",
                    "Keyword organic rank position",
                    "PPC impression share",
                    "CTR / CVR by campaign type",
                ],
            }
        else:
            return {
                "phase": StrategyPhase.TRAFFIC.value,
                "platform": self.platform.value,
                "title": "{} traffic strategy".format(self.platform.display_name),
                "steps": ["Traffic strategy to be refined in future versions"],
                "key_metrics": [],
            }

    def _conversion_phase(self, category: str, market: str, budget: str) -> dict:
        if self.platform == Platform.AMAZON:
            return {
                "phase": StrategyPhase.CONVERSION.value,
                "platform": Platform.AMAZON.value,
                "title": "Amazon conversion optimization strategy",
                "steps": [
                    "Price anchoring: show original + discounted price, high perceived value",
                    "Coupon + Promotions: Buy One Get One, percentage off, tiered discounts",
                    "Review management: proactively request reviews via Amazon Request a Review",
                    "Q&A section: seed 3-5 Q&As addressing common concerns",
                    "Trust signals: A+ Content, brand story, comparison charts",
                    "Shipping optimization: FBA Prime badge for trust and free shipping",
                    "Stock management: never stock out - BSR resets to zero on OOS",
                    "Price testing: A/B test price points to find optimal conversion price",
                ],
                "key_metrics": [
                    "Unit Session Percentage (CVR)",
                    "Cart abandonment rate",
                    "Average Order Value (AOV)",
                    "Customer acquisition cost (CAC)",
                ],
            }
        else:
            return {
                "phase": StrategyPhase.CONVERSION.value,
                "platform": self.platform.value,
                "title": "{} conversion strategy".format(self.platform.display_name),
                "steps": ["Conversion strategy to be refined in future versions"],
                "key_metrics": [],
            }

    def _retention_phase(self, category: str, market: str, budget: str) -> dict:
        if self.platform == Platform.AMAZON:
            return {
                "phase": StrategyPhase.RETENTION.value,
                "platform": Platform.AMAZON.value,
                "title": "Amazon customer retention strategy",
                "steps": [
                    "Subscribe & Save: encourage subscription for consumable products",
                    "Brand Store followers: build owned traffic via Brand Store",
                    "Post-purchase email: follow up with usage tips and complementary products",
                    "Product line expansion: cross-sell related SKUs within same category",
                    "Amazon Live: regular live streams to engage repeat customers",
                    "Customer feedback loop: address negative reviews quickly to retain trust",
                    "Bundle deals: increase AOV and lock in multi-product purchases",
                ],
                "key_metrics": [
                    "Repeat purchase rate",
                    "Customer Lifetime Value (LTV)",
                    "Subscribe & Save enrollment rate",
                    "Return/refund rate",
                ],
            }
        else:
            return {
                "phase": StrategyPhase.RETENTION.value,
                "platform": self.platform.value,
                "title": "{} retention strategy".format(self.platform.display_name),
                "steps": ["Retention strategy to be refined in future versions"],
                "key_metrics": [],
            }

    def _review_phase(self) -> dict:
        return {
            "phase": StrategyPhase.REVIEW.value,
            "platform": self.platform.value,
            "title": "Performance review & iteration",
            "steps": [
                "Weekly BSR trend check: is ranking improving or declining?",
                "PPC campaign audit: pause low-performing keywords, scale winners",
                "Competitor monitoring: track new entrants and price changes",
                "Review sentiment analysis: identify recurring issues in negative reviews",
                "Inventory forecast: align stock levels with sales velocity",
                "Seasonality planning: prepare inventory and campaigns 2-4 weeks ahead",
            ],
            "key_metrics": [
                "Weekly revenue growth rate",
                "Profit margin per SKU",
                "PPC ROAS trend",
                "Organic vs paid traffic ratio",
            ],
        }