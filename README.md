# DeepSeek Agent Skills — 智能体技能库

基于 DeepSeek 大语言模型生态的 Agent 技能（Skill）集合，提供开箱即用的能力模块，帮助开发者快速构建高效、低成本的智能体应用。

---

## Skills

### 1. deepseek-token-optimizer

**DeepSeek API Token 成本优化工具** — 通过缓存感知设计、Thinking Mode 控制、对话摘要和 Token 预算管理，最高降低 **70%** Token 消耗。

| 特性 | 说明 |
|------|------|
| Thinking Mode 控制 | 按任务类型自动匹配 disabled / low / high 三档 effort 级别 |
| Context Caching | 50x 价差（$0.0028 vs $0.14/M tokens）；CacheFriendlyBuilder 自动构建缓存友好前缀 |
| Token 追踪 | TokenTracker 多模型追踪 + 成本拆解 + 缓存命中率分析 |
| 消息优化 | 智能推理剥离（per-message tool-call 感知）、语义级系统提示词压缩 |
| 透明中间件 | DeepSeekMiddleware 零代码改动包裹 OpenAI-compatible 客户端 |
| 对话管理 | 超过 8 轮自动摘要截断、TokenBudget 预算检查 |

```python
from deepseek_token_optimizer import DeepSeekMiddleware
client = DeepSeekMiddleware(openai_client, auto_summarize=True)
response = client.chat.completions.create(model="deepseek-v4-flash", messages=[...])
wrapped.print_summary()  # 无需代码改动，自动追踪并输出优化建议
```

**适配场景**：AI Agent 编排、多轮对话、工具调用、代码助手

---

### 2. ecommerce-ops-skill

**多平台电商运营策略引擎** — 集成 Amazon / 淘宝 / 京东 / 拼多多 / 抖音电商五大平台的销量榜单读取、竞品分析和全链路运营策略。

| 平台 | 销量排名 | 商品详情 | 销量估算 | 运营策略 |
|------|:---:|:---:|:---:|:---:|
| Amazon（10 个站点） | Y | Y | BSR 分档模型 | 6 阶段（SP/SB/SD） |
| 淘宝 / 天猫 | Y | — | 月销量展示 ÷ 30 | 6 阶段（直通车/引力魔方/万相台） |
| 京东 | Y | — | 评价数推算法 | 6 阶段（京准通/购物触点/Plus） |
| 拼多多 | Y | — | 已拼件数差值法 | 6 阶段（多多搜索/全站推广/百亿补贴） |
| 抖音电商 | Y | — | GPM × 曝光推算法 | 6 阶段（千川/直播/短视频/达人矩阵） |

**核心能力**：

- **榜单读取**：通用 HTML 解析引擎，覆盖五大平台热销榜/搜索排行
- **销量估算**：BSR 分档、月销量快照差值、评价增速、GPM 推算等 5 种估算模型
- **跨平台比价**：同关键词多平台价格/销量/店铺对比
- **全链路策略**：选品 → 上架 → 流量 → 转化 → 复购 → 复盘，3 档预算全覆盖
- **直播电商**：抖音 GPM/Opm/UV 值计算 + 短视频转化漏斗 + 直播间健康诊断

```python
from ecommerce_ops_skill import DataFetcher, Platform, StrategyEngine

fetcher = DataFetcher()
# 跨平台搜索同款比价
results = fetcher.cross_platform_search("充电宝")

# 抖音直播 GMV 预估
live = fetcher.analyze_douyin_live(avg_viewers=5000, duration_minutes=120, gpm=800)

# 全链路运营策略
phases = StrategyEngine(platform=Platform.PINDUODUO).full_strategy()
fetcher.close()
```

**适配场景**：电商运营选品、竞品监控、广告投放优化、直播数据分析、跨平台定价策略

---

## 安装

每个 Skill 均可独立安装使用：

```bash
# Token 优化工具
pip install deepseek-token-optimizer

# 电商运营策略引擎
pip install ecommerce-ops-skill
```

或从源码按需安装：

```bash
git clone https://github.com/srfnhgsgst-del/skill.git
cd skill
pip install -e ./deepseek-token-optimizer
pip install -e ./ecommerce-ops-skill
```context-optimizer: 优化 Token 利用率，通过上下文压缩、状态追踪（MEMORY.md）和精简通信，解决长对话中的上下文丢失与 Token 浪费问题。

## 技术栈

Python · DeepSeek API · httpx · BeautifulSoup · Pydantic · pytest

## 许可

MIT
