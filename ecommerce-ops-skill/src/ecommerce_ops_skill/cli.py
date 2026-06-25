import argparse
import sys
from typing import Optional

from ecommerce_ops_skill.platform import Platform
from ecommerce_ops_skill.models import RankingItem, DataSource
from ecommerce_ops_skill.strategy_engine import StrategyEngine
from ecommerce_ops_skill.export_utils import DataExporter
from ecommerce_ops_skill.xiaohongshu import XiaohongshuClient


def _parse_platform(name: str) -> Optional[Platform]:
    name = name.strip().lower()
    for p in Platform:
        if p.value == name or p.display_name.lower() == name or p.name.lower() == name:
            return p
    return None


def _print_strategy(result: dict):
    print(f"\n=== {result.get('title', result.get('phase', '').title())} ===")
    print(f"平台: {result.get('platform', '?')}")
    steps = result.get("steps", [])
    if steps:
        print("\n步骤:")
        for i, step in enumerate(steps, 1):
            print(f"  {i}. {step}")
    metrics = result.get("key_metrics", [])
    if metrics:
        print(f"\n关键指标: {', '.join(metrics)}")
    warnings = result.get("risk_warnings", [])
    if warnings:
        print(f"\n风险提示: {', '.join(warnings)}")
    budget = result.get("budget_recommendation")
    if budget:
        for k, v in budget.items():
            print(f"\n预算建议 ({k}): {v}")


def cmd_strategy(args):
    platform = _parse_platform(args.platform)
    if not platform:
        print(f"错误: 不支持的平台 '{args.platform}'")
        sys.exit(1)
    engine = StrategyEngine(platform=platform)
    phases = ["selection", "listing", "traffic", "conversion", "retention"]
    methods = {
        "selection": engine.selection_strategy,
        "listing": engine.listing_strategy,
        "traffic": engine.traffic_strategy,
        "conversion": engine.conversion_strategy,
        "retention": engine.retention_strategy,
    }
    for phase_name in phases:
        result = methods[phase_name](budget_level=args.budget)
        _print_strategy(result)
        print()


def cmd_list_platforms(args):
    print("支持的电商平台:\n")
    for p in Platform:
        print(f"  {p.value:20s} {p.display_name}")
    print()


def _demo_items(platform: Platform, keyword: str, count: int = 3) -> list:
    return [
        RankingItem(
            platform=platform, rank=i + 1,
            asin_or_id=f"{platform.value}-demo-{i}",
            title=f"{keyword} 示例商品 {i+1}", price=99.0 * (i + 1),
            review_count=1000 * (i + 1), is_bestseller=(i == 0),
            data_source=DataSource.MODEL_ESTIMATION,
        )
        for i in range(count)
    ]


def cmd_export(args):
    fmt = args.format.lower()
    if fmt not in ("csv", "json", "xlsx"):
        print("格式支持: csv, json, xlsx")
        sys.exit(1)
    items = _demo_items(Platform.AMAZON, args.keyword)
    if fmt == "csv":
        output = DataExporter.to_csv(items, args.output)
    elif fmt == "json":
        output = DataExporter.to_json(items, args.output)
    else:
        output = DataExporter.to_excel(items, args.output)
        output = f"Exported {len(output)} bytes"
    if args.output:
        print(f"导出成功: {args.output}")
    else:
        print(output)


def cmd_report(args):
    data = {
        "taobao": _demo_items(Platform.TAOBAO, args.keyword, 3),
        "jd": _demo_items(Platform.JD, args.keyword, 2),
        "pdd": _demo_items(Platform.PINDUODUO, args.keyword, 1),
    }
    report = DataExporter.generate_daily_report(data)
    print(report)


def cmd_dashboard(args):
    products = [
        {"title": "爆款商品A", "monthly_gmv": 500000, "monthly_orders": 1000, "platform": "douyin"},
        {"title": "热销商品B", "monthly_gmv": 200000, "monthly_orders": 500, "platform": "taobao"},
        {"title": "潜力商品C", "monthly_gmv": 20000, "monthly_orders": 50, "platform": "pdd"},
    ]
    dashboard = DataExporter.generate_gmv_dashboard(products)
    print(f"\nGMV 经营看板\n{'='*40}")
    s = dashboard["summary"]
    print(f"总 GMV:      CNY {s['total_gmv_cny']:,.0f}")
    print(f"总订单量:     {s['total_monthly_orders']:,}")
    print(f"商品数:       {s['total_products']}")
    print(f"平均 GMV/品:  CNY {s['avg_gmv_per_product']:,.0f}")
    print("\n平台分布:")
    for plat, info in dashboard["by_platform"].items():
        print(f"  {plat:10s} CNY {info['gmv']:>8,.0f}  {info['orders']:>5}单")
    print("\nGMV 分层:")
    for tier, count in dashboard["gmv_tier_distribution"].items():
        if count:
            print(f"  {tier}: {count}品")


def cmd_compare(args):
    p1 = _parse_platform(args.p1)
    p2 = _parse_platform(args.p2)
    if not p1 or not p2:
        print("平台参数无效")
        sys.exit(1)
    data = {
        p1.value: _demo_items(p1, args.keyword, 3),
        p2.value: _demo_items(p2, args.keyword, 3),
    }
    table = DataExporter.create_comparison_table(data)
    print(table)


def cmd_xhs_note(args):
    client = XiaohongshuClient()
    result = client.analyze_note_performance(
        views=args.views, likes=args.likes, collects=args.collects,
        comments=args.comments, shares=args.shares,
        product_click_rate=args.click_rate, conversion_rate=args.cvr,
        avg_order_value=args.aov,
    )
    print(f"\n小红书笔记分析\n{'='*40}")
    print(f"曝光量:     {result['views']:,}")
    print(f"互动量:     {result['total_interactions']:,}")
    print(f"互动率:     {result['engagement_rate']:.2%}")
    print(f"爆文评分:   {result['quality_score']:.2f} ({result['content_tier']}级)")
    print(f"传播率:     {result['viral_score']:.4f}")
    f = result["conversion_funnel"]
    print("\n转化漏斗:")
    print(f"  商品点击:  {f['product_clicks']}")
    print(f"  订单数:    {f['orders']}")
    print(f"  GMV:      CNY {f['gmv_cny']:,.2f}")


def cmd_xhs_search(args):
    client = XiaohongshuClient()
    results = client.search_notes(args.keyword, page=args.page)
    source = "真实数据" if client.using_real_data else "模拟数据"
    print(f"\n小红书笔记搜索 — {args.keyword} (第{args.page}页) [{source}]\n{'='*50}")
    for item in results[:args.limit]:
        flags = " [笔记]" if item.data_source == DataSource.WEB_SCRAPING else ""
        print(f"  #{item.rank:3d}{flags} {item.title[:40]}")
    print(f"\n共 {len(results)} 条结果")


def cmd_xhs_detail(args):
    client = XiaohongshuClient()
    detail = client.get_note_detail(args.note_id)
    src = "真实" if detail.get("data_source") == "web_scraping" else "模拟"
    print(f"\n小红书笔记详情 — {args.note_id} [{src}]\n{'='*50}")
    print(f"标题:   {detail.get('title', 'N/A')}")
    print(f"作者:   {detail.get('user', {}).get('nickname', 'N/A')}")
    if "views" in detail:
        print(f"阅读:   {detail['views']:,}")
    if "likes" in detail:
        print(f"点赞:   {detail['likes']:,}")
    if "collects" in detail:
        print(f"收藏:   {detail['collects']:,}")
    if "comments" in detail:
        print(f"评论:   {detail['comments']:,}")
    if "shares" in detail:
        print(f"分享:   {detail['shares']:,}")
    print(f"数据源: {detail.get('data_source', 'N/A')}")


def main():
    parser = argparse.ArgumentParser(
        prog="ecommerce-ops",
        description="全平台电商运营策略命令行工具",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_strategy = sub.add_parser("strategy", help="获取平台运营策略")
    p_strategy.add_argument("platform", help="平台名称 (amazon/taobao/jd/pinduoduo/douyin/xiaohongshu)")
    p_strategy.add_argument("--budget", default="medium", choices=["low", "medium", "high"])

    p_export = sub.add_parser("export", help="导出示例数据")
    p_export.add_argument("format", choices=["csv", "json", "xlsx"])
    p_export.add_argument("keyword", default="蓝牙耳机", nargs="?")
    p_export.add_argument("--output", "-o", default=None, help="输出文件路径")

    p_report = sub.add_parser("report", help="生成运营日报")
    p_report.add_argument("keyword", default="蓝牙耳机", nargs="?")

    sub.add_parser("dashboard", help="生成 GMV 经营看板")

    p_compare = sub.add_parser("compare", help="跨平台对比")
    p_compare.add_argument("p1", help="平台1")
    p_compare.add_argument("p2", help="平台2")
    p_compare.add_argument("keyword", default="蓝牙耳机", nargs="?")

    p_xhs = sub.add_parser("xhs-note", help="分析小红书笔记表现")
    p_xhs.add_argument("views", type=int)
    p_xhs.add_argument("likes", type=int)
    p_xhs.add_argument("collects", type=int)
    p_xhs.add_argument("comments", type=int)
    p_xhs.add_argument("shares", type=int)
    p_xhs.add_argument("--click-rate", type=float, default=0.05)
    p_xhs.add_argument("--cvr", type=float, default=0.02)
    p_xhs.add_argument("--aov", type=float, default=50.0)

    p_xhs_search = sub.add_parser("xhs-search", help="搜索小红书笔记")
    p_xhs_search.add_argument("keyword", help="搜索关键词")
    p_xhs_search.add_argument("--page", type=int, default=1)
    p_xhs_search.add_argument("--limit", type=int, default=10)

    p_xhs_detail = sub.add_parser("xhs-detail", help="获取小红书笔记详情")
    p_xhs_detail.add_argument("note_id", help="笔记ID")

    sub.add_parser("list-platforms", help="列出支持的平台")

    args = parser.parse_args()

    commands = {
        "strategy": cmd_strategy,
        "export": cmd_export,
        "report": cmd_report,
        "dashboard": cmd_dashboard,
        "compare": cmd_compare,
        "xhs-note": cmd_xhs_note,
        "xhs-search": cmd_xhs_search,
        "xhs-detail": cmd_xhs_detail,
        "list-platforms": cmd_list_platforms,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
