# Changelog

## v0.6.0 (2026-06-25)

### Added
- **小红书真实 HTTP 爬虫** (`XiaohongshuClient`)
  - `search_notes(keyword, page)` — 搜索小红书笔记，解析 `__INITIAL_STATE__` 数据
  - `get_note_detail(note_id)` — 获取单篇笔记详情（阅读/点赞/收藏/评论/分享）
  - `search_users(keyword)` — 搜索小红书用户/达人
  - 真实 API 失败时自动降级到模拟数据（mock fallback）
  - `using_real_data` 属性标识数据源
  - HTML 解析器：正则提取 React 初始化状态 JSON
- **CLI 新增命令**
  - `xhs-search <keyword>` — 搜索小红书笔记
  - `xhs-detail <note-id>` — 获取笔记详情
- 5 个新单元测试覆盖爬虫 mock 降级逻辑

### Changed
- 版本升至 0.6.0
- `__init__.py`: 导出 `cli_main`

## v0.5.0 (2026-06-25)

### Added
- **CLI 命令行工具** (`ecommerce-ops`)
  - `ecommerce-ops strategy <平台>` — 获取 6 阶段运营策略（选品→上架→流量→转化→复购）
  - `ecommerce-ops strategy <平台> --budget low|medium|high` — 按预算档位策略
  - `ecommerce-ops export csv|json <关键词>` — 导出示例数据到 CSV/JSON
  - `ecommerce-ops report <关键词>` — 生成多平台运营日报
  - `ecommerce-ops dashboard` — 生成 GMV 经营看板（总额/分布/分层）
  - `ecommerce-ops compare <平台1> <平台2>` — 跨平台比价表
  - `ecommerce-ops xhs-note <参数>` — 小红书笔记表现分析
  - `ecommerce-ops list-platforms` — 列出所有支持的平台
- 18 个 CLI 单元测试，覆盖所有子命令

### Changed
- 版本升至 0.5.0
- `pyproject.toml`: 注册 `[project.scripts]` 入口点
- `__init__.py`: 导出 `cli_main`

## v0.4.0 (2026-06-22)

### Added
- **小红书** 电商数据模型 (`XiaohongshuClient`)
  - 笔记表现分析：互动率/爆文评分/内容分级S-C / 转化漏斗
  - 达人画像分析：头腰尾KOL/KOC分层 + ROI预测 + 影响力评分
  - 品牌投放模型：预算→曝光→互动→订单→GMV全链路ROI
  - 笔记趋势分析：关键词竞争度 + 品类增长率检测
  - 内容趋势搜索：8大品类热门关键词（护肤/穿搭/家居/美食/数码等）
  - 热门话题标签：按品类获取小红书热门标签
  - 内容ROI计算：笔记成本→订单→收入→ROI
- **数据导出工具** (`DataExporter`)
  - CSV导出：18列完整排行数据（BOM头中文兼容）
  - JSON导出：结构化输出 + 文件持久化
  - 运营日报生成：多平台汇总 + 均价/旗舰占比/Top3 + 销量估算
  - GMV经营看板：总额/订单/客单价 + 平台分布 + Top5单品 + 五档GMV分层
  - 跨平台比价表：平台/商品数/均价/价格区间/爆款占比
- **StrategyEngine** 高级策略扩展
  - 跨平台SWOT分析 (`generate_cross_platform_swot`)
  - 价格弹性分析 (`analyze_price_elasticity`)
  - 季节性趋势预测 (`predict_seasonal_trend`) — 8大品类季节性模型
  - 小红书6阶段全链路策略（选品→笔记内容→流量→转化→复购→矩阵）
  - 全平台6端交叉策略矩阵 (`full_cross_platform_matrix`)
- 24个新增单元测试（XHS 8 + Export 8 + Strategy Advanced 5 + FileIO 2）
- 总计94个测试，覆盖6大平台 + 导出 + 高级策略

### Fixed
- `test_unsupported_platform`: 小红书已全面支持，更新断言
- `estimate_note_trend`: 增长率阈值 `>0.15` → `>=0.15`
- `estimate_content_roi`: ROI预期值修正为32.0
- `generate_daily_report`: 输出键大写 `TAOBAO`/`JD`
- `generate_gmv_dashboard`: S档阈值 `>=500000`，修正测试数据
- `predict_seasonal_trend`: 导入名 `_dt` 修正

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