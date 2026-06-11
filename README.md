
**DeepSeek Agent Skills — DeepSeek 智能体技能库**

本仓库聚焦 DeepSeek 大语言模型生态，专注于 AI Agent 智能体技能（Skill）的开发、沉淀与最佳实践分享。基于 DeepSeek API 的独特能力体系，系统化梳理 Agent 开发中的关键技能模块，帮助开发者快速构建高效、稳定、低成本的智能体应用。

**核心技能方向：**

一、Token 成本优化。DeepSeek 的计费机制与 OpenAI 等模型有显著差异，尤其体现在 Thinking Mode（思维链模式）和 Context Caching（上下文缓存）上。Thinking Mode 默认开启并产生大量不可见推理 Token，直接推高使用成本。本仓库提供完整的 Token 监控、缓存命中检测、成本核算能力，并沉淀了一套经过验证的优化策略：按任务类型动态控制思考模式开关与 effort 级别、设计缓存友好的消息前缀结构、压缩系统提示词、在长对话中自动摘要截断等。实测可将 Token 消耗降低最高 70%。

二、Thinking Mode 精细控制。DeepSeek 的 Thinking Mode 分为 disabled、low、high、max 等多个级别，不同任务需要差异化配置。本仓库整理出按任务复杂度（简单问答、代码生成、调试排查、架构设计、Agent 编排）的最佳 thinking 配置矩阵，并提供 API 封装工具，让开发者无需手动调整即可自动匹配最优模式。

三、Context Caching 深度利用。DeepSeek 的上下文缓存机制可实现缓存命中时输入成本降至 1/50（$0.0028 vs $0.14 每百万 Token）。但缓存命中依赖严格的前缀匹配规则。本仓库提供的 CacheFriendlyBuilder 工具可自动构建缓存友好的消息结构，确保系统提示词和首条消息在前缀位置稳定不变，新消息追加在后，从而最大化缓存命中率。

四、多轮对话管理与上下文窗口优化。Agent 应用中，对话轮次增长带来的上下文膨胀是成本飙升的核心原因之一。本仓库提供智能摘要引擎，支持在指定轮次后自动压缩历史对话；同时处理 Tool Call 场景下的 reasoning_content 剥离与保留策略，避免不必要的 Token 浪费。

五、Agent 工具调用编排。基于 DeepSeek 模型的 Function Calling / Tool Use 能力，提供可复用的工具调用技能模块，包括工具定义模板、调用链路追踪、错误重试策略、多工具并行调度等。

**适用人群：**

- 使用 DeepSeek API 构建 Agent 应用的开发者
- 关注大模型 Token 成本控制的技术团队
- AI Agent 框架（如 OpenCode、LangChain、AutoGen 等）的深度使用者
- 对 LLM 推理效率优化感兴趣的工程师

**技术栈：** Python、DeepSeek API、OpenAI-compatible SDK、Function Calling、Tool Use

持续更新中，欢迎贡献与交流。
温馨提示:该介绍由ai生成,如有错处请谅解
