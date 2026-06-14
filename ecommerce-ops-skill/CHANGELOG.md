# Changelog

## v0.3.0 (2026-06-13)

### Added
- **拼多多** 搜索排名解析 (`PinduoduoClient`)
  - 搜索页商品排名 + 已拼件数解析
  - 已拼件数差值法销量估算（模拟多多参谋数据模型）
  - 价格竞争分析（Q1/Q3/中位数/低价段竞争压力评估）
  - 品牌店旗舰店识别
  - 热搜词推荐（按类目）
- **拼多多销量估算器** (`PinduoduoSalesEstimator`)
  - 双时间点差值法：日销 = 增量/小时 × 24
  - 爆款等级分级：explosive/hot/growing/steady/cold
  - GMV层级划分：S/A/B/C/D 五档
- **抖音电商** 数据模型 (`DouyinClient`)
  - 直播GPM估算：GPM × 人数 × 时长 = 预估GMV
  - 直播Opm（每分钟订单量）计算
  - 短视频转化漏斗：完播率→互动率→商品点击→成交
  - 商品卡流量模型：曝光→点击→加购→成交→GPM
  - 达人账号评分：粉丝互动率+内容力+直播效率
  - GPM → 日销估算
- **抖音直播指标** (`DouyinLiveMetrics`)
  - GPM/Opm/UV价值/停留率计算
  - 直播间健康度诊断（5个维度自动检查）
- **抖音流量来源分析** (`DouyinTrafficSource`)
  - 推荐/搜索/关注/付费/直播短视频互导 五渠道对标
  - 渠道表现 vs 行业基准对比
  - 流量优化建议自动生成
- **RankParser** 扩展：`parse_pinduoduo_search_results` / `_extract_pdd_sales`
- **DataFetcher** 扩展：
  - PDD/Douyin sales estimation routing
  - `take_pdd_sales_snapshot()` 快照录制
  - `analyze_pdd_price_competition()` 价格竞争分析
  - `analyze_douyin_live()` / `analyze_douyin_video_funnel()`
- **StrategyEngine** 扩展：
  - 拼多多6阶段策略（选品→上架→多多搜索/场景/全站推广/进宝/拼团裂变→转化→复购）
  - 抖音电商6阶段策略（选品→内容上架→千川/达人矩阵/自播/短视频SEO→直播间转化→粉丝复购）
  - 3个预算档位全覆盖
- 30个新增单元测试（PDD 8 + Douyin 12 + RankParser 3 + StrategyEngine 4）

## v0.2.0 (2026-06-13)

### Added
- **淘宝/天猫** 搜索排名解析 (`TaobaoClient`)
- **京东** 搜索排名解析 (`JDClient`)
- 跨平台搜索 `cross_platform_search()`
- 淘宝/京东全链路策略引擎扩展

## v0.1.0 (2026-06-13)

### Added
- Amazon BSR 榜单读取 + 跨平台策略引擎骨架