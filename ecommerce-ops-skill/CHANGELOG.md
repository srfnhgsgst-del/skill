# Changelog

## v0.2.0 (2026-06-13)

### Added
- **淘宝/天猫** 搜索排名解析 (`TaobaoClient`)
  - 搜索结果页关键词排名抓取
  - 月销量(月销X万+)解析与估算
  - 天猫店铺识别、热词推荐
  - 销量估算器 (`TaobaoSalesEstimator`)：日均订单、转化率估算、店铺竞争力分级
- **京东** 搜索排名解析 (`JDClient`)
  - 搜索结果页排名 + 京东自营vs.POP识别
  - 京东排行榜(phb)榜单抓取
  - 评价数→销量换算估算模型
  - 类目排行索引 (`JDCategoryRanking`)
- **RankParser** 扩展：`parse_taobao_search_results` / `parse_jd_search_results` / `_extract_number_cn`
- **DataFetcher** 扩展：
  - `search_products(platform, keyword)` 统一搜索接口
  - `cross_platform_search(keyword)` 同关键词跨平台比价
  - 淘宝/京东 `estimate_sales` 路由
- **StrategyEngine** 扩展：
  - 淘宝/天猫六阶段策略（选品→上架→直通车/引力魔方/万相台/直播/逛逛→转化→私域复购）
  - 京东六阶段策略（选品→商详→京准通/购物触点/秒杀→转化→PLUS会员/自营）
  - `cross_platform_compare()` 跨平台数据对比
  - 三个预算档位全覆盖（low/medium/high）
- 38 个新增测试（淘宝 8 + 京东 5 + RankParser CN 4 + StrategyEngine CN 7）

## v0.1.0 (2026-06-13)

### Added
- Amazon Best Sellers Rank (BSR) 榜单读取能力
- 产品页详情解析（价格/评论/BuyBox/库存状态）
- 通用榜单解析引擎 `rank_parser.py`
- 跨平台运营策略引擎骨架 `strategy_engine.py`
- 数据模型层 `models.py` + 平台枚举 `platform.py`
- 统一数据获取入口 `data_fetcher.py`
- 基础项目结构