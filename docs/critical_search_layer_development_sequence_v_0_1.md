# Critical Search Layer 开发顺序文档

版本：v0.1  
文档类型：开发执行顺序 / 模块拆分 / 阶段任务清单  
适用对象：Codex、Claude Code、开发者本人  

---

# 一、开发总原则

本项目不要一开始追求完整系统，而要先跑通最小闭环。

核心原则：

> 先让系统能完整走一遍“输入问题 → 搜索 → 抽证据 → 打分 → 返回证据包”，再逐步增强可信度、冲突检测、多领域支持和 MCP 工具化。

开发时必须避免以下错误：

1. 不要先做前端。
2. 不要先做数据库。
3. 不要先做复杂评分算法。
4. 不要一开始支持所有领域。
5. 不要一开始接多个搜索 API。
6. 不要一开始做 MCP。
7. 不要还没跑通 evidence package，就优化回答生成。

第一阶段只打穿一个样板场景：

```text
AI 模型信息核查
```

样板问题：

```text
MiroThinker 1.7 是不是开源模型？
```

---

# 二、最小可运行闭环

MVP 的最小闭环如下：

```text
输入 query
  ↓
识别 question_type
  ↓
拆 claim
  ↓
生成 search query
  ↓
拿搜索结果
  ↓
识别 source_type
  ↓
抓取正文或 fallback snippet
  ↓
抽 evidence
  ↓
计算 final_score
  ↓
聚合 claim status
  ↓
生成 answer_constraints
  ↓
返回 JSON
```

只要这个闭环跑通，项目就成立。

之后所有优化，都是在这个闭环上提高准确率、覆盖率和稳定性。

---

# 三、模块拆分

MVP 阶段拆为 12 个模块。

## 0. Project Skeleton 项目骨架

目标：让项目可以启动、测试和扩展。

内容：

```text
FastAPI 应用入口
配置管理
日志系统
基础异常处理
健康检查接口
pytest 测试框架
```

建议文件：

```text
app/
  main.py
  core/
    config.py
    logging.py
    exceptions.py
  api/
    routes/
      health.py
  tests/
    test_health.py
```

---

## 1. API Schema 接口与数据结构

目标：先确定 AI Agent 调用工具时的输入输出边界。

内容：

```text
TrustedSearchRequest
TrustedSearchResponse
ClaimSchema
SourceSchema
EvidenceSchema
AnswerConstraintsSchema
ErrorResponse
```

建议文件：

```text
app/schemas/
  trusted_search.py
  claim.py
  source.py
  evidence.py
  constraints.py
```

---

## 2. Question Classifier 问题分类器

目标：判断用户问题属于哪类。

MVP 支持类型：

```text
ai_model_info
tech_news
product_info
policy_legal
technical_doc
general_fact
unknown
```

第一版实现方式：规则判断。

示例：

```text
包含 模型 / LLM / Hugging Face / GitHub / 开源 / 参数 → ai_model_info
包含 发布 / 爆料 / 传言 / 新闻 / 最新 → tech_news
包含 价格 / 参数 / 显存 / 配置 / 商品 → product_info
包含 法规 / 政策 / 政府 / 监管 / 法律 → policy_legal
包含 Python / API / 报错 / 文档 / 函数 / 库 → technical_doc
```

---

## 3. Claim Decomposer 命题拆解器

目标：把复杂问题拆成可验证命题。

第一阶段只支持 AI 模型信息类问题。

输入：

```text
MiroThinker 1.7 是不是开源模型？
```

期望输出：

```text
1. MiroThinker 1.7 是否存在公开发布页面
2. MiroThinker 1.7 是否公开模型权重
3. MiroThinker 1.7 是否公开训练代码
4. MiroThinker 1.7 是否公开训练数据
5. MiroThinker 1.7 的许可证是否允许商用
6. MiroThinker 1.7 是否能严格称为开源模型
```

第一版实现方式：模板拆解。  
第二版再接入 LLM 灵活拆解。

---

## 4. Search Planner 搜索计划器

目标：根据 claim 生成搜索词和来源偏好。

AI 模型信息类搜索模板：

```text
{entity} Hugging Face
{entity} GitHub
{entity} paper
{entity} arXiv
{entity} license
{entity} official
```

输出内容：

```text
queries
preferred_source_types
```

---

## 5. Search Adapter 搜索适配器

目标：调用外部搜索 API，返回候选来源。

第一版只接一个搜索 API。

推荐优先级：

```text
1. Tavily
2. Brave Search API
3. SerpAPI
4. Bing Search API
```

输出字段：

```text
title
url
snippet
published_at 可选
```

要求：

```text
搜索失败不能导致整个流程崩溃
搜索结果需要去重
支持 max_results
```

---

## 6. Source Classifier 来源分类器

目标：识别搜索结果来源类型，并赋予基础可信度。

常见规则：

```text
huggingface.co       → official_model_card
modelscope.cn        → official_model_card
github.com           → source_code_repo
arxiv.org            → academic_paper
openreview.net       → academic_paper
sec.gov              → financial_filing
*.gov                → government_docs
reddit.com           → community_forum
zhihu.com            → community_forum
x.com                → community_forum
unknown              → unknown
```

需要配置文件：

```text
app/policies/source_policy.yml
```

---

## 7. Page Fetcher 网页抓取与正文解析

目标：从 URL 获取正文，为证据抽取做准备。

第一版实现：

```text
httpx 抓取网页
trafilatura 提取正文
失败时使用搜索 snippet fallback
设置 timeout
限制正文最大长度
```

输出字段：

```text
url
title
text
fetch_status
```

---

## 8. Evidence Extractor 证据抽取器

目标：从网页正文中抽取与 claim 相关的证据。

输出字段：

```text
evidence_text
support_type: support / oppose / partial / neutral
relevance_score
```

第一版建议使用 LLM，因为语义支持关系很难纯规则判断。

硬约束：

```text
只能从原文抽取，不允许编造
找不到证据时返回空数组
evidence_text 必须短，建议 1-3 句话
support_type 必须枚举化
```

这是项目从“普通搜索工具”变成“批判性搜索工具”的关键模块。

---

## 9. Reliability Scorer 可信度评分器

目标：给每条 evidence 计算 final_score。

第一版公式：

```text
final_score = relevance_score × source_base_score × primary_source_factor × recency_factor
```

输出字段：

```text
final_score
score_breakdown
```

score_breakdown 示例：

```json
{
  "relevance_score": 0.86,
  "source_base_score": 0.88,
  "primary_source_factor": 1.10,
  "recency_factor": 1.00,
  "final_score": 0.83
}
```

---

## 10. Claim Aggregator 命题聚合器

目标：根据多条 evidence 判断每个 claim 的最终状态。

状态枚举：

```text
confirmed
likely
uncertain
unsupported
conflicting
false_likely
```

第一版规则：

```text
confirmed:
  最高支持证据分数 >= 0.80，且无高分反对证据

likely:
  最高支持证据分数 >= 0.65，但不足以 confirmed

uncertain:
  有部分证据，但分数低或只部分支持

unsupported:
  没有有效支持证据

conflicting:
  同时存在高分支持证据和高分反对证据
```

输出字段：

```text
claim_id
status
confidence
reason
```

---

## 11. Answer Constraint Builder 回答约束生成器

目标：把证据状态转化为 AI 最终回答规则。

输出字段：

```text
can_answer_confidently
must_disclose_uncertainty
must_cite_sources
allowed_tone
required_phrases
forbidden_phrases
```

规则：

```text
所有核心 claim confirmed → 可以较确定回答
有 claim uncertain → 必须披露不确定性
有 claim conflicting → 必须说明来源冲突
有 claim unsupported → 禁止肯定表达
```

示例：

```json
{
  "can_answer_confidently": false,
  "must_disclose_uncertainty": true,
  "allowed_tone": "cautious",
  "required_phrases": [
    "可以确认部分信息",
    "但仍有部分信息无法确认"
  ],
  "forbidden_phrases": [
    "毫无疑问",
    "已经完全确认"
  ]
}
```

---

# 四、推荐开发顺序

## 阶段 0：项目基础设施

目标：项目能启动、能测试、能配置。

开发内容：

```text
1. 创建 FastAPI 项目结构
2. 添加 app/main.py
3. 添加配置管理 app/core/config.py
4. 添加日志基础结构
5. 添加基础异常处理
6. 添加 /health 接口
7. 添加 pytest
8. 添加 README 基础运行说明
```

验收标准：

```text
GET /health 返回 ok
pytest 通过
项目结构固定
```

建议 Git 标签：

```text
v0.1.0-skeleton
```

---

## 阶段 1：接口与 Schema 先行

目标：确定系统输入输出边界。

开发内容：

```text
1. 定义 TrustedSearchRequest
2. 定义 TrustedSearchResponse
3. 定义 Claim、Source、Evidence、AnswerConstraints schema
4. 建立 /api/v1/trusted-search 空接口
5. trusted-search 先返回 mock evidence package
6. 添加接口测试
```

验收标准：

```text
POST /api/v1/trusted-search 可以接收 query
接口返回符合 schema 的 mock JSON
测试覆盖基础输入输出
```

建议 Git 标签：

```text
v0.1.1-api-schema
```

---

## 阶段 2：问题分类 + 命题拆解

目标：让系统理解用户问题，并拆成可验证 claim。

开发内容：

```text
1. 实现 Question Classifier
2. 实现基础 question_type 规则
3. 实现 Claim Decomposer
4. AI 模型信息类问题先用模板拆解
5. 添加分类和拆解测试
```

验收标准：

```text
输入：MiroThinker 1.7 是不是开源模型？
输出：存在性、权重、代码、许可证、开源定义等 claim
```

建议 Git 标签：

```text
v0.1.2-question-claims
```

---

## 阶段 3：搜索计划器 + 搜索适配器

目标：根据 claim 生成搜索词，并调用搜索 API 拿候选来源。

开发内容：

```text
1. 实现 Search Planner
2. 为 ai_model_info 生成搜索查询
3. 接入一个搜索 API
4. 实现搜索结果去重
5. 搜索失败时返回可控错误
6. 添加搜索计划和搜索适配器测试
```

验收标准：

```text
每个 claim 能生成 query
query 能拿到搜索结果
搜索结果包含 title、url、snippet
```

建议 Git 标签：

```text
v0.1.3-search-adapter
```

---

## 阶段 4：来源分类器

目标：判断搜索结果来自什么来源，并给基础可信度。

开发内容：

```text
1. 添加 source_policy.yml
2. 实现 Source Classifier
3. 根据域名识别 source_type
4. 给每个 source_type 赋 base_reliability
5. 标记 is_primary_source
6. 添加来源分类测试
```

验收标准：

```text
huggingface.co → official_model_card
github.com → source_code_repo
arxiv.org → academic_paper
reddit.com → community_forum
unknown → unknown
```

建议 Git 标签：

```text
v0.1.4-source-classifier
```

---

## 阶段 5：网页抓取与正文解析

目标：从 URL 获取正文。

开发内容：

```text
1. 实现 Page Fetcher
2. 使用 httpx 抓取网页
3. 使用 trafilatura 提取正文
4. 设置 timeout
5. 失败时使用 snippet fallback
6. 限制正文最大长度
7. 添加网页抓取测试
```

验收标准：

```text
普通网页可以提取正文
抓取失败不会中断流程
返回 fetch_status
```

建议 Git 标签：

```text
v0.1.5-page-fetcher
```

---

## 阶段 6：证据抽取器

目标：从网页正文中抽出和 claim 相关的证据。

开发内容：

```text
1. 实现 Evidence Extractor
2. 第一版接入 LLM 或简单文本匹配 fallback
3. 输出 evidence_text
4. 判断 support_type
5. 给出 relevance_score
6. 无证据时返回空数组
7. 添加证据抽取测试
```

验收标准：

```text
每个 claim 可以从网页中抽出 support / oppose / partial / neutral 证据
无证据不编造
```

建议 Git 标签：

```text
v0.1.6-evidence-extractor
```

---

## 阶段 7：可信度评分器

目标：给每条 evidence 计算 final_score。

开发内容：

```text
1. 实现 Reliability Scorer
2. 使用 source_base_score
3. 使用 relevance_score
4. 使用 primary_source_factor
5. 使用 recency_factor
6. 输出 score_breakdown
7. 添加评分器测试
```

第一版评分公式：

```text
final_score = relevance_score × source_base_score × primary_source_factor × recency_factor
```

验收标准：

```text
每条 evidence 有 final_score
每个 final_score 可解释
不同来源分数不同
```

建议 Git 标签：

```text
v0.1.7-reliability-scorer
```

---

## 阶段 8：命题聚合器

目标：根据 evidence 判断每个 claim 的最终状态。

开发内容：

```text
1. 实现 Claim Aggregator
2. 聚合 support / oppose / partial 证据
3. 生成 status
4. 生成 confidence
5. 生成 reason
6. 添加命题聚合测试
```

验收标准：

```text
每个 claim 都有 confirmed / likely / uncertain / unsupported / conflicting 状态
```

建议 Git 标签：

```text
v0.1.8-claim-aggregator
```

---

## 阶段 9：回答约束生成器

目标：把证据状态转化为 AI 回答规则。

开发内容：

```text
1. 实现 Answer Constraint Builder
2. 根据 claim status 判断 can_answer_confidently
3. 生成 required_phrases
4. 生成 forbidden_phrases
5. 生成 allowed_tone
6. 添加回答约束测试
```

验收标准：

```text
有 uncertain 时，必须要求披露不确定性
有 conflicting 时，必须要求说明冲突
有 unsupported 时，禁止肯定表达
```

建议 Git 标签：

```text
v0.1.9-answer-constraints
```

---

## 阶段 10：端到端集成测试

目标：把所有模块串成完整可信搜索流程。

开发内容：

```text
1. 编写端到端测试
2. 使用固定测试问题
3. mock 搜索 API，保证测试稳定
4. 测试失败场景
5. 检查最终 JSON 是否符合预期
```

测试问题：

```text
MiroThinker 1.7 是不是开源模型？
OpenAI 下周会发布某个代号模型吗？
某款笔记本 RTX 5070 Ti 是不是 12GB 显存？
某项政策现在是否还有效？
```

验收标准：

```text
trusted-search 完整流程可运行
主要测试通过
失败场景可控
```

建议 Git 标签：

```text
v0.1.10-e2e-mvp
```

---

## 阶段 11：冲突检测增强

目标：识别同一 claim 下的高分支持证据和高分反对证据。

开发内容：

```text
1. 实现 Conflict Detector
2. 对 support / oppose 证据进行对比
3. 高分冲突时标记 claim 为 conflicting
4. 输出 conflict summary
5. 添加冲突检测测试
```

验收标准：

```text
高分支持证据和高分反对证据并存时，claim 必须为 conflicting
最终回答约束必须要求说明冲突
```

建议 Git 标签：

```text
v0.1.11-conflict-detector
```

---

## 阶段 12：MCP 工具封装

目标：让 Claude、Cursor、Codex、自建 Agent 可以调用 trusted_search。

开发内容：

```text
1. 定义 MCP tool schema
2. 封装 trusted_search 工具
3. 复用 REST API 内部服务逻辑
4. 返回标准 evidence package JSON
5. 添加 MCP 调用示例
```

验收标准：

```text
Agent 能通过 MCP 调用 trusted_search
返回内容与 REST API 一致
```

建议 Git 标签：

```text
v0.1.12-mcp-tool
```

---

# 五、开发优先级表

| 优先级 | 模块 | 是否必须 | 原因 |
|---|---|---|---|
| P0 | 项目骨架 | 必须 | 没有骨架无法开发 |
| P0 | Schema | 必须 | 决定工具输入输出边界 |
| P0 | 问题分类 | 必须 | 决定后续策略 |
| P0 | 命题拆解 | 必须 | 可信搜索的基本单位 |
| P0 | 搜索适配器 | 必须 | 获取外部信息 |
| P0 | 来源分类 | 必须 | 可信度判断第一层 |
| P0 | 证据抽取 | 必须 | 从网页转为证据 |
| P0 | 可信度评分 | 必须 | 核心产品价值 |
| P0 | 命题聚合 | 必须 | 得出 claim 状态 |
| P0 | 回答约束 | 必须 | 防止 AI 过度肯定 |
| P1 | 网页正文高级解析 | 重要 | 提高证据质量 |
| P1 | 冲突检测增强 | 重要 | 提高真实性 |
| P1 | 多搜索源接入 | 重要 | 提高覆盖率 |
| P1 | MCP 封装 | 重要 | 方便 Agent 调用 |
| P2 | 数据库存储 | 可后置 | MVP 可先无状态运行 |
| P2 | 前端页面 | 可后置 | 先做 API 工具即可 |
| P2 | 来源历史信誉系统 | 可后置 | 需要长期数据积累 |

---

# 六、第一轮开发任务清单

## 第一轮目标

完成项目骨架和 trusted-search mock 接口。

## 任务列表

```text
1. 创建 FastAPI 项目结构
2. 添加 app/main.py
3. 添加 app/core/config.py
4. 添加 /health 接口
5. 添加 pytest 测试
6. 添加 schemas/trusted_search.py
7. 添加 /api/v1/trusted-search 接口
8. trusted-search 先返回 mock evidence package
9. 添加 README 基础运行说明
10. git commit + tag v0.1.1-api-schema
```

## 第一轮不做

```text
不接搜索 API
不接 LLM
不做数据库
不做 MCP
不做前端
不做复杂评分
```

## 第一轮验收

```text
uvicorn 可以启动
/health 正常
/api/v1/trusted-search 可以接收 query
返回结构符合 PRD schema
pytest 通过
```

---

# 七、给开发 Agent 的第一条指令

可以直接给 Codex / Claude Code 使用：

```text
根据 PRD，为 Critical Search Layer 创建 FastAPI 项目骨架。先完成 /health 接口、/api/v1/trusted-search mock 接口、Pydantic schemas 和基础 pytest 测试。不要接搜索 API、不要接 LLM、不要做数据库。保证项目能启动、测试能通过、接口返回符合 PRD 的结构化 JSON。
```

---

# 八、Git 标签建议

```text
v0.1.0-skeleton
v0.1.1-api-schema
v0.1.2-question-claims
v0.1.3-search-adapter
v0.1.4-source-classifier
v0.1.5-page-fetcher
v0.1.6-evidence-extractor
v0.1.7-reliability-scorer
v0.1.8-claim-aggregator
v0.1.9-answer-constraints
v0.1.10-e2e-mvp
v0.1.11-conflict-detector
v0.1.12-mcp-tool
```

---

# 九、当前最应该执行的下一步

现在不要继续扩展需求。

下一步只做：

```text
FastAPI 骨架 + health + trusted-search mock 接口 + schema + pytest
```

原因：

```text
1. 先把项目跑起来
2. 先固定接口边界
3. 先让 AI Agent 未来知道怎么调用
4. 后续所有模块都可以逐个替换 mock
```

这一步完成后，再进入问题分类和命题拆解。

