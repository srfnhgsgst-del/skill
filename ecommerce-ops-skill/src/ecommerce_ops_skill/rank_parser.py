from typing import Optional

from bs4 import BeautifulSoup, Tag

import re as _re

from ecommerce_ops_skill.platform import Platform, AmazonDomain
from ecommerce_ops_skill.models import RankingItem, DataSource


class RankParser:
    """通用榜单 HTML 解析器"""

    @staticmethod
    def parse_amazon_bestsellers(
        html: str,
        domain: AmazonDomain = AmazonDomain.US,
        category: str = "General",
        limit: int = 100,
    ) -> list[RankingItem]:
        soup = BeautifulSoup(html, "lxml")
        items: list[RankingItem] = []
        rank = 0

        grid_items = soup.select("div[role=\"gridcell\"]")
        if grid_items:
            for cell in grid_items:
                rank += 1
                if rank > limit:
                    break
                item = RankParser._parse_amazon_grid_cell(cell, rank, domain, category)
                if item:
                    items.append(item)
            return items

        card_selectors = [
            ".p13n-gridRow",
            ".a-carousel-card",
            "div[data-asin]",
        ]
        seen_asins: set[str] = set()

        for selector in card_selectors:
            cards = soup.select(selector)
            for card in cards:
                asin = card.get("data-asin", "")
                if not asin or asin in seen_asins:
                    continue
                seen_asins.add(asin)
                rank += 1
                if rank > limit:
                    break
                item = RankParser._parse_amazon_card(card, rank, domain, category)
                if item:
                    items.append(item)
            if rank >= limit:
                break

        if not items:
            items = RankParser._parse_amazon_fallback(soup, limit, domain, category)

        return items

    @staticmethod
    def _parse_amazon_grid_cell(cell: Tag, rank: int, domain: AmazonDomain, category: str) -> Optional[RankingItem]:
        asin = cell.get("data-asin", "")
        if not asin:
            link = cell.select_one("a[href*=\"/dp/\"]")
            if link:
                href = link.get("href", "")
                asin = RankParser._extract_asin(href)
        if not asin:
            return None

        title = RankParser._find_title(cell)

        price_text = ""
        price_tag = cell.select_one(".p13n-sc-price")
        if price_tag:
            price_text = price_tag.get_text(strip=True)

        rating, review_count = RankParser._parse_rating(cell)

        img_tag = cell.select_one("img")
        img_url = img_tag.get("src", "") if img_tag else ""

        product_url = f"https://{domain.value}/dp/{asin}"
        price = RankParser._parse_price(price_text)
        currency = RankParser._detect_currency(domain)

        is_sponsored = cell.select_one(".sponsored-label") is not None
        is_bestseller = (
            cell.select_one(".a-badge-supplementary") is not None
            or cell.select_one(".a-badge-label-inner") is not None
            or cell.select_one(".p13n-best-seller") is not None
        )
        is_amazon_choice = cell.select_one(".a-badge-ac-label") is not None

        return RankingItem(
            platform=Platform.AMAZON,
            rank=rank,
            asin_or_id=asin,
            title=title,
            price=price,
            currency=currency,
            rating=rating,
            review_count=review_count,
            image_url=img_url,
            product_url=product_url,
            category=category,
            is_sponsored=is_sponsored,
            is_bestseller=is_bestseller,
            is_amazon_choice=is_amazon_choice,
            data_source=DataSource.WEB_SCRAPING,
        )

    @staticmethod
    def _parse_amazon_card(card: Tag, rank: int, domain: AmazonDomain, category: str) -> Optional[RankingItem]:
        asin = card.get("data-asin", "")
        if not asin:
            link = card.select_one("a[href*=\"/dp/\"]")
            if link:
                asin = RankParser._extract_asin(link.get("href", ""))
        if not asin:
            return None

        title = RankParser._find_title(card)

        price_tag = card.select_one(".p13n-sc-price, [class*=\"price\"]")
        price_text = price_tag.get_text(strip=True) if price_tag else ""

        rating, review_count = RankParser._parse_rating(card)

        img_tag = card.select_one("img")
        img_url = img_tag.get("src", "") if img_tag else ""

        price = RankParser._parse_price(price_text)
        currency = RankParser._detect_currency(domain)
        product_url = f"https://{domain.value}/dp/{asin}"

        is_sponsored = card.select_one(".sponsored-label, [class*=\"sponsored\"]") is not None
        is_bestseller = (
            card.select_one(".a-badge-supplementary") is not None
            or card.select_one(".a-badge-label-inner") is not None
            or card.select_one(".p13n-best-seller") is not None
        )
        is_amazon_choice = card.select_one(".a-badge-ac-label") is not None

        return RankingItem(
            platform=Platform.AMAZON,
            rank=rank,
            asin_or_id=asin,
            title=title,
            price=price,
            currency=currency,
            rating=rating,
            review_count=review_count,
            image_url=img_url,
            product_url=product_url,
            category=category,
            is_sponsored=is_sponsored,
            is_bestseller=is_bestseller,
            is_amazon_choice=is_amazon_choice,
            data_source=DataSource.WEB_SCRAPING,
        )

    @staticmethod
    def _find_title(element: Tag) -> str:
        selectors = [
            ".p13n-sc-truncate-desktop-type2",
            ".p13n-sc-truncated",
            "._cDEzb_p13n-sc-css-line-clamp-1",
            "._cDEzb_p13n-sc-css-line-clamp-2",
            "._cDEzb_p13n-sc-css-line-clamp-3",
            ".zg-text-center-align a",
            "a[title]",
            "h2 a",
            "h2",
            "[class*=\"title\"]",
        ]
        for sel in selectors:
            tag = element.select_one(sel)
            if tag:
                if tag.name == "a" or tag.name == "img":
                    text = tag.get("title", "") or tag.get("alt", "") or tag.get_text(strip=True)
                else:
                    text = tag.get_text(strip=True)
                if text:
                    return text

        img_tag = element.select_one("img")
        if img_tag:
            return img_tag.get("alt", "") or ""

        return ""

    @staticmethod
    def _parse_amazon_fallback(soup: BeautifulSoup, limit: int, domain: AmazonDomain, category: str) -> list[RankingItem]:
        items: list[RankingItem] = []
        rank = 0
        product_links = soup.select("a[href*=\"/dp/\"]")
        seen: set[str] = set()
        for link in product_links:
            href = link.get("href", "")
            asin = RankParser._extract_asin(href)
            if not asin or asin in seen:
                continue
            seen.add(asin)
            rank += 1
            if rank > limit:
                break
            parent = link.find_parent(["div", "li"])
            title = ""
            if parent:
                title_tag = parent.select_one("h2") or parent.select_one("[class*=\"title\"]")
                if title_tag:
                    title = title_tag.get_text(strip=True)
            if not title:
                title = link.get_text(strip=True)
            items.append(RankingItem(
                platform=Platform.AMAZON,
                rank=rank,
                asin_or_id=asin,
                title=title,
                product_url=f"https://{domain.value}/dp/{asin}",
                category=category,
                data_source=DataSource.WEB_SCRAPING,
            ))
        return items

    @staticmethod
    def parse_amazon_product_page(html: str, domain: AmazonDomain = AmazonDomain.US) -> dict:
        soup = BeautifulSoup(html, "lxml")
        data: dict = {}

        title_tag = soup.select_one("#productTitle")
        data["title"] = title_tag.get_text(strip=True) if title_tag else ""

        bsr_tag = soup.select_one("#productDetails_detailBullets_sections1 th, #detailBullets_feature_div li")
        if bsr_tag:
            text = bsr_tag.get_text(strip=True)
            if "Best Sellers Rank" in text:
                data["bsr_text"] = text

        price_whole = soup.select_one(".a-price-whole")
        price_fraction = soup.select_one(".a-price-fraction")
        price_symbol = soup.select_one(".a-price-symbol")
        if price_whole:
            whole = price_whole.get_text(strip=True).replace(",", "")
            fraction = price_fraction.get_text(strip=True) if price_fraction else "00"
            currency_symbol = price_symbol.get_text(strip=True) if price_symbol else "$"
            data["price"] = float(f"{whole}.{fraction}")
            data["currency_symbol"] = currency_symbol

        availability_tag = soup.select_one("#availability span")
        data["availability"] = availability_tag.get_text(strip=True) if availability_tag else "unknown"

        rating_tag = soup.select_one("#acrPopover")
        if rating_tag:
            data["rating_text"] = rating_tag.get("title", "")

        review_tag = soup.select_one("#acrCustomerReviewText")
        if review_tag:
            data["review_count_text"] = review_tag.get_text(strip=True)

        brand_tag = soup.select_one("#bylineInfo")
        if brand_tag:
            data["brand"] = brand_tag.get_text(strip=True).replace("Brand: ", "").replace("Visit the ", "")

        image_tags = soup.select("#altImages img, #landingImage, #imgTagWrapperId img")
        data["images"] = [img.get("src", "") for img in image_tags if img.get("src")]

        feature_bullets = soup.select("#feature-bullets li span.a-list-item")
        data["features"] = [li.get_text(strip=True) for li in feature_bullets]

        buybox_tag = soup.select_one("#merchant-info, #shipsFromSoldBy_feature_div")
        if buybox_tag:
            data["seller_info"] = buybox_tag.get_text(strip=True)

        return data

    @staticmethod
    def _extract_asin(href: str) -> str:
        import re
        match = re.search(r"/dp/([A-Z0-9]{10})", href)
        return match.group(1) if match else ""

    @staticmethod
    def _parse_price(price_text: str) -> Optional[float]:
        import re
        if not price_text:
            return None
        match = re.search(r"[\d,]+\.?\d*", price_text)
        if match:
            return float(match.group().replace(",", ""))
        return None

    @staticmethod
    def _parse_rating(element: Tag) -> tuple[Optional[float], Optional[int]]:
        import re

        rating = None
        icon_tag = element.select_one(".a-icon-alt, i[class*=\"star\"]")
        if icon_tag:
            text = icon_tag.get_text(strip=True)
            match = re.search(r"(\d+\.?\d*)", text)
            if match:
                rating = float(match.group(1))

        review_count = None
        review_candidates = element.select(".a-size-small, .a-size-base")
        for candidate in review_candidates:
            text = candidate.get_text(strip=True)
            if "$" in text:
                continue
            match = re.search(r"([\d,]+)", text)
            if match:
                review_count = int(match.group(1).replace(",", ""))
                break

        return rating, review_count

    @staticmethod
    def _detect_currency(domain: AmazonDomain) -> str:
        currencies = {
            AmazonDomain.US: "USD",
            AmazonDomain.JP: "JPY",
            AmazonDomain.UK: "GBP",
            AmazonDomain.DE: "EUR",
            AmazonDomain.FR: "EUR",
            AmazonDomain.IT: "EUR",
            AmazonDomain.ES: "EUR",
            AmazonDomain.CA: "CAD",
            AmazonDomain.IN: "INR",
            AmazonDomain.AU: "AUD",
        }
        return currencies.get(domain, "USD")

    @staticmethod
    def parse_taobao_search_results(html: str, keyword: str, limit: int = 40) -> list[RankingItem]:
        soup = BeautifulSoup(html, "lxml")
        items: list[RankingItem] = []
        rank = 0

        card_selectors = [
            ".item.J_MouserOnverReq",
            "[data-category=\"auctions\"] .item",
            ".grid-item .item-container",
            "[class*=\"item\"]",
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
                title_tag = card.select_one("[class*=\"title\"] a, a[title], h3 a")
                title = ""
                if title_tag:
                    title = title_tag.get("title", "") or title_tag.get_text(strip=True)

                price_el = card.select_one("[class*=\"price\"] em, [class*=\"price\"] strong, [class*=\"price\"]")
                price_text = price_el.get_text(strip=True) if price_el else ""
                price = RankParser._parse_price(price_text)

                sales_el = card.select_one("[class*=\"sale\"], [class*=\"deal\"], [class*=\"sales\"]")
                sales_text = sales_el.get_text(strip=True) if sales_el else ""
                monthly_sales = RankParser._extract_number_cn(sales_text)

                shop_el = card.select_one("[class*=\"shop\"] span, [class*=\"shop\"] a")
                shop = shop_el.get_text(strip=True) if shop_el else ""

                card_classes = card.get("class") or []
                is_tmall = any("tmall" in c for c in card_classes) or card.select_one("[class*=\"tmall\"], .tmall-icon") is not None

                img_el = card.select_one("img[data-src], img[src]")
                img_url = (img_el.get("data-src") or img_el.get("src") or "") if img_el else ""

                items.append(RankingItem(
                    platform=Platform.TMALL if is_tmall else Platform.TAOBAO,
                    rank=rank,
                    asin_or_id=f"tb-{keyword}-{rank}",
                    title=title[:200] if title else f"{keyword} #{rank}",
                    price=price,
                    currency="CNY",
                    review_count=monthly_sales,
                    image_url=img_url or "",
                    brand=shop,
                    category=keyword,
                    data_source=DataSource.WEB_SCRAPING,
                ))
            except Exception:
                continue

        return items

    @staticmethod
    def parse_jd_search_results(html: str, keyword: str, limit: int = 60) -> list[RankingItem]:
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
                title_tag = card.select_one("[class*=\"name\"] a, [class*=\"name\"] em, a[title]")
                title = ""
                if title_tag:
                    title = title_tag.get("title", "") or title_tag.get_text(strip=True)

                price_el = card.select_one("[class*=\"price\"] i, [class*=\"price\"] strong")
                price_text = price_el.get_text(strip=True) if price_el else ""
                price = RankParser._parse_price(price_text)

                comment_el = card.select_one("[class*=\"commit\"] a, .p-review")
                comment_text = comment_el.get_text(strip=True) if comment_el else ""
                comment_count = RankParser._extract_number_cn(comment_text)

                shop_el = card.select_one("[class*=\"shop\"] a, .curr-shop")
                shop = shop_el.get_text(strip=True) if shop_el else ""

                is_self = (
                    card.select_one("[class*=\"jd-ziying\"], .goods-icons i, [class*=\"self\"]")
                    is not None
                )
                if not is_self:
                    raw = str(card)
                    if "自营" in raw:
                        is_self = True

                data_sku = card.get("data-sku", "")

                items.append(RankingItem(
                    platform=Platform.JD,
                    rank=rank,
                    asin_or_id=data_sku or f"jd-{keyword}-{rank}",
                    title=title[:200] if title else f"JD #{rank}",
                    price=price,
                    currency="CNY",
                    review_count=comment_count,
                    brand=shop,
                    category=keyword,
                    is_bestseller=is_self,
                    data_source=DataSource.WEB_SCRAPING,
                ))
            except Exception:
                continue

        return items

    @staticmethod
    def _extract_number_cn(text: str) -> Optional[int]:
        if not text:
            return None
        text = text.replace("+", "").replace("人付款", "").replace("月销", "").replace("条评论", "")
        if "万" in text:
            m = _re.search(r"(\d+\.?\d*)", text)
            if m:
                return int(float(m.group(1)) * 10000)
        m = _re.search(r"(\d+)", text.replace(",", ""))
        return int(m.group(1)) if m else None

    @staticmethod
    def parse_pinduoduo_search_results(html: str, keyword: str, limit: int = 40) -> list[RankingItem]:
        soup = BeautifulSoup(html, "lxml")
        items: list[RankingItem] = []
        rank = 0

        card_selectors = [
            "[data-active=\"goods\"]",
            ".goods-list .goods-item",
            "[class*=\"goods\"]",
            ".index-list-page .list",
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
                title_tag = card.select_one("[class*=\"title\"] span, [class*=\"title\"], .name, [class*=\"goods-name\"]")
                title = ""
                if title_tag:
                    title = title_tag.get("title", "") or title_tag.get_text(strip=True)

                price_el = card.select_one("[class*=\"price\"] span, [class*=\"price\"]")
                price_text = price_el.get_text(strip=True) if price_el else ""
                price = RankParser._parse_price(price_text)

                sales_el = card.select_one("[class*=\"sales\"], [class*=\"sold\"]")
                sales_text = sales_el.get_text(strip=True) if sales_el else ""
                sales = RankParser._extract_pdd_sales(sales_text)

                shop_el = card.select_one("[class*=\"mall\"], [class*=\"shop\"], .mall-name")
                shop = shop_el.get_text(strip=True) if shop_el else ""

                is_mall = (
                    card.select_one("[class*=\"mall\"]") is not None
                    or "旗舰" in (card.get("class") or [])
                )

                img_el = card.select_one("img[src], img[data-src]")
                img_url = (img_el.get("data-src") or img_el.get("src") or "") if img_el else ""

                items.append(RankingItem(
                    platform=Platform.PINDUODUO,
                    rank=rank,
                    asin_or_id=f"pdd-{keyword}-{rank}",
                    title=title[:200] if title else f"PDD #{rank}",
                    price=price,
                    currency="CNY",
                    review_count=sales,
                    image_url=img_url or "",
                    brand=shop,
                    category=keyword,
                    is_bestseller=is_mall,
                    data_source=DataSource.WEB_SCRAPING,
                ))
            except Exception:
                continue

        return items

    @staticmethod
    def _extract_pdd_sales(text: str) -> Optional[int]:
        if not text:
            return None
        text = text.replace("已拼", "").replace("件", "").replace("+", "").replace("万件", "万")
        if "万" in text:
            m = _re.search(r"(\d+\.?\d*)", text)
            if m:
                return int(float(m.group(1)) * 10000)
        m = _re.search(r"(\d+\.?\d*)", text.replace(",", ""))
        return int(float(m.group(1))) if m else None

    @staticmethod
    def format_bestseller_table(items: list[RankingItem]) -> str:
        lines = []
        header = f"{'#':>4}  {'ASIN':>12}  {'Price':>10}  {'Rating':>6}  {'Reviews':>8}  {'Title'}"
        lines.append(header)
        lines.append("-" * len(header))
        for item in items:
            price_str = f"{item.currency} {item.price:.2f}" if item.price else "N/A"
            rating_str = f"{item.rating:.1f}" if item.rating else "N/A"
            reviews_str = str(item.review_count) if item.review_count else "N/A"
            title = item.title[:50] + "..." if len(item.title) > 50 else item.title
            flags = ""
            if item.is_bestseller:
                flags += "[B]"
            if item.is_sponsored:
                flags += "[AD]"
            if item.is_amazon_choice:
                flags += "[AC]"
            line = f"{item.rank:>4}  {item.asin_or_id:>12}  {price_str:>10}  {rating_str:>6}  {reviews_str:>8}  {title}{flags}"
            lines.append(line)
        return "\n".join(lines)
