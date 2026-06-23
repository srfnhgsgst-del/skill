import csv
import json
import io
from datetime import datetime
from typing import Optional

from ecommerce_ops_skill.models import RankingItem, BestSellerList, SalesEstimate


class DataExporter:
    """数据导出工具 — CSV/Excel/JSON 导出 + 运营日报生成 + GMV 看板"""

    @staticmethod
    def to_csv(items: list[RankingItem], filepath: Optional[str] = None) -> str:
        output = io.StringIO()
        writer = csv.writer(output)

        headers = ["Rank", "Platform", "ASIN/ID", "Title", "Price", "Currency",
                   "Rating", "Reviews/Sales", "Brand/Shop", "Category",
                   "Bestseller", "Sponsored", "Fetched At"]
        writer.writerow(headers)

        for item in items:
            writer.writerow([
                item.rank,
                item.platform.value if item.platform else "",
                item.asin_or_id,
                item.title[:100] if item.title else "",
                item.price if item.price else "",
                item.currency,
                item.rating if item.rating else "",
                item.review_count if item.review_count else "",
                item.brand if item.brand else "",
                item.category if item.category else "",
                "Y" if item.is_bestseller else "",
                "Y" if item.is_sponsored else "",
                item.fetched_at.isoformat() if item.fetched_at else "",
            ])

        csv_content = output.getvalue()
        output.close()

        if filepath:
            with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
                f.write(csv_content)

        return csv_content

    @staticmethod
    def to_json(items: list[RankingItem], filepath: Optional[str] = None, pretty: bool = True) -> str:
        data_list = [
            {
                "rank": item.rank,
                "platform": item.platform.value if item.platform else "",
                "asin_or_id": item.asin_or_id,
                "title": item.title,
                "price": item.price,
                "currency": item.currency,
                "rating": item.rating,
                "review_count": item.review_count,
                "brand": item.brand,
                "category": item.category,
                "is_bestseller": item.is_bestseller,
                "is_sponsored": item.is_sponsored,
                "product_url": item.product_url,
                "fetched_at": item.fetched_at.isoformat() if item.fetched_at else "",
            }
            for item in items
        ]

        indent = 2 if pretty else None
        json_content = json.dumps(data_list, ensure_ascii=False, indent=indent)

        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(json_content)

        return json_content

    @staticmethod
    def generate_daily_report(
        platform_data: dict[str, list[RankingItem]],
        sales_estimates: Optional[dict[str, SalesEstimate]] = None,
    ) -> str:
        lines = []
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        lines.append(f"{'='*60}")
        lines.append(f"  电商运营日报 — {now}")
        lines.append(f"{'='*60}")

        total_products = 0
        for platform_name, items in platform_data.items():
            total_products += len(items)
            if not items:
                continue

            prices = [i.price for i in items if i.price]
            sales = [i.review_count for i in items if i.review_count]
            bestsellers = sum(1 for i in items if i.is_bestseller)

            lines.append(f"\n  [{platform_name.upper()}] {len(items)} items")
            lines.append(f"    均价: CNY {sum(prices)/len(prices):.2f}" if prices else "    均价: N/A")
            lines.append(f"    旗舰/自营占比: {bestsellers}/{len(items)}")

            if sales:
                lines.append(f"    平均销量/评论: {int(sum(sales)/len(sales)):,}")

            lines.append("    Top 3:")
            for item in items[:3]:
                price_str = f"CNY{item.price}" if item.price else "N/A"
                flags = " [B]" if item.is_bestseller else ""
                lines.append(f"      #{item.rank}{flags} {item.title[:50]}  {price_str}")

        lines.append(f"\n  {'—'*50}")
        lines.append(f"  全平台总计: {total_products} 条商品")

        if sales_estimates:
            lines.append("\n  [销量估算]")
            for pid, est in list(sales_estimates.items())[:5]:
                lines.append(f"    {pid}: 日销~{est.estimated_daily_sales or 'N/A'} "
                           f"月销~{est.estimated_monthly_sales or 'N/A'} "
                           f"月GMV~CNY{est.estimated_monthly_revenue or 'N/A':,.0f}")

        lines.append(f"\n{'='*60}")
        return "\n".join(lines)

    @staticmethod
    def generate_gmv_dashboard(
        products: list[dict],
    ) -> dict:
        if not products:
            return {"error": "No data"}

        total_gmv = sum(p.get("monthly_gmv", 0) for p in products)
        total_orders = sum(p.get("monthly_orders", 0) for p in products)
        total_products_count = len(products)

        platforms: dict[str, dict] = {}
        for p in products:
            plat = p.get("platform", "unknown")
            if plat not in platforms:
                platforms[plat] = {"gmv": 0, "orders": 0, "count": 0}
            platforms[plat]["gmv"] += p.get("monthly_gmv", 0)
            platforms[plat]["orders"] += p.get("monthly_orders", 0)
            platforms[plat]["count"] += 1

        sorted_by_gmv = sorted(products, key=lambda x: x.get("monthly_gmv", 0), reverse=True)

        gmv_tiers = {"S(>50万)": 0, "A(10-50万)": 0, "B(3-10万)": 0, "C(1-3万)": 0, "D(<1万)": 0}
        for p in products:
            gmv = p.get("monthly_gmv", 0)
            if gmv >= 500000:
                gmv_tiers["S(>50万)"] += 1
            elif gmv > 100000:
                gmv_tiers["A(10-50万)"] += 1
            elif gmv > 30000:
                gmv_tiers["B(3-10万)"] += 1
            elif gmv > 10000:
                gmv_tiers["C(1-3万)"] += 1
            else:
                gmv_tiers["D(<1万)"] += 1

        return {
            "summary": {
                "total_gmv_cny": round(total_gmv, 2),
                "total_monthly_orders": total_orders,
                "total_products": total_products_count,
                "avg_gmv_per_product": round(total_gmv / total_products_count, 2) if total_products_count > 0 else 0,
            },
            "by_platform": platforms,
            "top_5_by_gmv": [
                {"title": p.get("title", "")[:50], "monthly_gmv": p.get("monthly_gmv", 0),
                 "monthly_orders": p.get("monthly_orders", 0), "platform": p.get("platform", "")}
                for p in sorted_by_gmv[:5]
            ],
            "gmv_tier_distribution": gmv_tiers,
        }

    @staticmethod
    def export_bestseller_list(bl: BestSellerList, format: str = "csv", filepath: Optional[str] = None) -> str:
        if format == "csv":
            return DataExporter.to_csv(bl.items, filepath)
        elif format == "json":
            return DataExporter.to_json(bl.items, filepath)
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'csv' or 'json'.")

    @staticmethod
    def create_comparison_table(cross_platform_data: dict[str, list]) -> str:
        rows = [["Platform", "Items", "Avg Price", "Price Range", "BestSeller%"]]

        for platform_name, items in cross_platform_data.items():
            if not isinstance(items, list) or not items:
                rows.append([platform_name, "0", "N/A", "N/A", "N/A"])
                continue

            prices = [i.price for i in items if i.price]
            bestsellers = sum(1 for i in items if i.is_bestseller)

            rows.append([
                platform_name,
                str(len(items)),
                f"{sum(prices)/len(prices):.2f}" if prices else "N/A",
                f"{min(prices)}-{max(prices)}" if len(prices) >= 2 else "N/A",
                f"{bestsellers/len(items)*100:.0f}%" if items else "N/A",
            ])

        col_widths = [max(len(str(row[i])) for row in rows) for i in range(5)]
        lines = []
        for row in rows:
            line = " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))
            lines.append(line)
            if row == rows[0]:
                lines.append("-+-".join("-" * w for w in col_widths))

        return "\n".join(lines)