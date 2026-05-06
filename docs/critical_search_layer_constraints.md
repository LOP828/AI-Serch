# Critical Search Layer 约束文档

版本：v0.1  
文档类型：开发约束 / 架构边界 / Agent 执行纪律  
适用对象：Codex、Claude Code、开发者本人  
项目：Critical Search Layer / AI 批判性搜索层

---

# 一、文档目的

本约束文档用于限制 Critical Search Layer 的开发范围、模块边界、技术选择、质量标准和 AI Agent 执行行为。

它的作用不是继续扩展需求，而是防止开发过程失控。

如果把 PRD 看作“产品图纸”，把开发顺序看作“加工路线”，那么本文件就是“工艺约束和质量规范”。

核心目标：

```text
让项目先稳定打穿最小可信搜索闭环，而不是过早做复杂系统。
```

---

# 二、最高优先级原则

## 2.1 先闭环，后增强

任何开发决策都必须服务于第一个闭环：

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

如果某个功能不能帮助这个闭环跑通，默认后置。

## 2.2 先工具，后产品界面

Critical Search Layer 的第一形态是：

```text
AI Agent 可调用的可信搜索工具 / 插件 / 中间件
```

所以第一阶段优先级：

```text
API > Schema > Service > Test > MCP > Frontend
```

禁止一开始做前端页面。

## 2.3 证据包优先于自然语言答案

本项目的核心产物不是一段自然语言回答，而是结构化 evidence package。

系统可以生成回答约束，但不应在 MVP 阶段追求完整回答生成。

## 2.4 不确定性是能力，不是失败

系统必须允许返回：

```text
uncertain
unsupported
conflicting
```

不得为了“看起来聪明”强行输出 confirmed。

---

# 三、范围约束

## 3.1 MVP 必须做

MVP v0.1 必须完成：

```text
1. FastAPI 项目骨架
2. /health 接口
3. /api/v1/trusted-search 接口
4. Pydantic Schema
5. 问题类型识别
6. AI 模型信息类命题拆解
7. 搜索计划生成
8. 单一搜索 API 适配
9. 搜索结果去重
10. 来源类型识别
11. 网页正文抓取与 snippet fallback
12. 证据抽取
13. 可信度评分
14. 命题状态聚合
15. 回答约束生成
16. 端到端测试
```

## 3.2 MVP 禁止做

MVP 阶段禁止做以下事项：

```text
1. 不做前端页面
2. 不做用户账号系统
3. 不做数据库持久化
4. 不做复杂权限系统
5. 不做浏览器插件
6. 不做多搜索 API 聚合
7. 不做来源历史信誉系统
8. 不做证据图谱
9. 不做医学、金融、法律自动决策
10. 不训练新模型
11. 不自建搜索引擎
12. 不做复杂爬虫系统
13. 不做大规模并发抓取
14. 不做完整聊天机器人
```

## 3.3 可后置功能

以下功能可以设计接口时留扩展口，但不得在 MVP 阶段实现复杂版本：

```text
1. 数据库
2. Redis 缓存
3. 多搜索源
4. MCP 封装
5. PDF 专项解析
6. GitHub 专项解析
7. Hugging Face 专项解析
8. 论文可信度扩展
9. 企业内部知识库接入
10. 来源历史信誉系统
```

---

# 四、开发顺序约束

## 4.1 必须按阶段推进

开发必须按以下顺序推进：

```text
阶段 0：项目骨架
阶段 1：Schema + mock 接口
阶段 2：问题分类 + 命题拆解
阶段 3：搜索计划 + 搜索适配器
阶段 4：来源分类器
阶段 5：网页抓取与正文解析
阶段 6：证据抽取器
阶段 7：可信度评分器
阶段 8：命题聚合器
阶段 9：回答约束生成器
阶段 10：端到端集成测试
阶段 11：冲突检测增强
阶段 12：MCP 工具封装
```

不得跳过 Schema 直接写业务逻辑。

不得跳过测试直接进入下一阶段。

## 4.2 每个阶段必须可运行

每个阶段完成后必须满足：

```text
1. 项目可以启动
2. pytest 可以通过
3. 已完成模块有单元测试
4. 已完成接口有接口测试
5. 当前阶段代码可以独立 commit
6. 当前阶段可以打 git tag
```

## 4.3 每个阶段必须有明确不做项

开发 Agent 在执行任何阶段任务时，必须遵守该阶段的“不做项”。

例如阶段 1 只做 mock 接口，不得顺手接搜索 API。

---

# 五、架构约束

## 5.1 项目结构约束

MVP 推荐结构：

```text
app/
  main.py
  api/
    routes/
      health.py
      trusted_search.py
  core/
    config.py
    logging.py
    exceptions.py
  services/
    question_classifier.py
    claim_decomposer.py
    search_planner.py
    search_adapter.py
    page_fetcher.py
    source_classifier.py
    evidence_extractor.py
    reliability_scorer.py
    claim_aggregator.py
    answer_constraint_builder.py
    trusted_search_service.py
  schemas/
    trusted_search.py
    claim.py
    source.py
    evidence.py
    constraints.py
  policies/
    source_policy.yml
    question_policy.yml
  tests/
```

## 5.2 分层约束

系统必须保持以下分层：

```text
API Layer：只处理请求、响应、错误转换
Service Layer：处理业务流程和模块编排
Schema Layer：定义输入输出结构
Policy Layer：保存可配置规则
Adapter Layer：处理外部服务调用
```

API 路由中不得写复杂业务逻辑。

## 5.3 模块替换约束

以下模块必须保持可替换：

```text
search_adapter：Tavily / Brave / SerpAPI 可替换
evidence_extractor：LLM / 规则 fallback 可替换
page_fetcher：trafilatura / readability / BS4 可替换
claim_decomposer：模板 / LLM 可替换
reliability_scorer：简单公式 / 增强公式可替换
```

不得把外部 API 调用和业务逻辑硬耦合。

---

# 六、接口约束

## 6.1 核心接口

核心接口固定为：

```http
POST /api/v1/trusted-search
```

请求体：

```json
{
  "query": "MiroThinker 1.7 是不是开源模型？",
  "question_type": "auto",
  "strictness": "balanced",
  "max_sources": 8,
  "require_primary_source": false,
  "return_raw_evidence": true
}
```

## 6.2 请求字段约束

```text
query:
  必填，非空字符串

question_type:
  auto / ai_model_info / tech_news / product_info / policy_legal / technical_doc / general_fact / unknown

strictness:
  loose / balanced / strict

max_sources:
  正整数，MVP 默认 8，建议最大不超过 20

require_primary_source:
  bool

return_raw_evidence:
  bool
```

## 6.3 响应字段约束

响应必须至少包含：

```text
query
question_type
risk_level
overall_status
overall_confidence
claims
sources
conflicts
answer_constraints
```

每个 claim 必须包含：

```text
claim_id
claim_text
claim_type
status
confidence
reason
evidence
```

每个 source 必须包含：

```text
source_id
title
url
domain
source_type
base_reliability
is_primary_source
published_at
```

每个 evidence 必须包含：

```text
evidence_id
claim_id
source_id
evidence_text
support_type
relevance_score
final_score
score_breakdown
```

## 6.4 错误响应约束

错误响应必须结构化：

```json
{
  "error": {
    "code": "INVALID_QUERY",
    "message": "query must not be empty",
    "details": {}
  }
}
```

禁止直接返回未处理异常堆栈。

---

# 七、Schema 约束

## 7.1 枚举必须集中定义

以下字段必须使用枚举或 Literal 约束：

```text
question_type
risk_level
strictness
source_type
support_type
claim_status
allowed_tone
fetch_status
```

## 7.2 禁止自由字符串扩散

除非确实是用户输入或自然语言解释，否则不允许到处使用裸字符串状态。

例如不能在不同文件里手写：

```python
"confirmed"
"CONFIRMED"
"confirm"
```

必须统一为同一个枚举值。

## 7.3 ID 命名约束

MVP 可使用可读 ID：

```text
question_id: q1
claim_id: c1, c2, c3
source_id: s1, s2, s3
evidence_id: e1, e2, e3
```

后续接数据库时再替换为 UUID。

---

# 八、问题分类约束

## 8.1 第一版只用规则

Question Classifier 第一版必须使用规则判断，不接 LLM。

原因：

```text
1. 可控
2. 易测试
3. 便于快速闭环
4. 防止早期不稳定
```

## 8.2 unknown 是合法结果

识别失败时必须返回：

```text
unknown
```

不得强行归类。

## 8.3 高风险类型必须提高证据门槛

以下类型默认更高风险：

```text
policy_legal
medical_health 后续扩展
financial_info 后续扩展
```

MVP 暂不支持医学、金融自动决策。

---

# 九、命题拆解约束

## 9.1 第一阶段只精做 ai_model_info

Claim Decomposer 第一阶段只需要把 AI 模型信息类问题拆好。

其他类型可先返回较简单 claim，不追求完善。

## 9.2 claim 必须可验证

合格 claim 示例：

```text
MiroThinker 1.7 是否公开模型权重
MiroThinker 1.7 是否公开训练代码
MiroThinker 1.7 的许可证是否允许商用
```

不合格 claim 示例：

```text
MiroThinker 1.7 是否很厉害
MiroThinker 1.7 是否值得信赖
MiroThinker 1.7 是否有前途
```

## 9.3 复杂问题必须拆多个 claim

复杂问题不得只生成一个 claim。

例如：

```text
“某模型是不是开源？”
```

至少应拆为：

```text
模型是否存在
权重是否开放
代码是否开放
训练数据是否开放
许可证是否允许使用
是否能严格称为开源
```

---

# 十、搜索计划约束

## 10.1 搜索计划必须绑定 claim

每个搜索 query 必须知道自己服务于哪个 claim。

不得只对原始 query 做一次搜索后全局混用。

## 10.2 不同问题类型必须有不同来源偏好

例如：

```text
ai_model_info:
  official_model_card
  source_code_repo
  academic_paper
  official_blog

policy_legal:
  government_docs
  official_docs
  regulatory_docs

product_info:
  official_docs
  product_page
  mainstream_media
```

## 10.3 strictness 必须影响搜索行为

MVP 可先简单实现：

```text
loose:
  允许更多第三方来源

balanced:
  默认模式，优先一手来源，同时允许可信第三方

strict:
  强化官方、一手、论文、政府来源；弱化社区和 SEO
```

---

# 十一、搜索适配器约束

## 11.1 第一版只接一个搜索 API

MVP 只接一个搜索 API。

禁止同时接多个搜索源。

## 11.2 外部 API 必须可 mock

测试中不得真实调用搜索 API。

必须通过 mock 返回固定搜索结果。

## 11.3 搜索失败不得中断整个流程

搜索失败时应返回可控错误状态，并允许整体流程继续返回部分结果。

## 11.4 搜索结果必须去重

去重至少按 URL 处理：

```text
去除 fragment
去除 utm 参数
标准化尾部斜杠
同一 URL 只保留一次
```

---

# 十二、网页抓取约束

## 12.1 必须设置 timeout

任何网页请求都必须设置 timeout。

禁止无超时请求。

## 12.2 必须有 fallback

正文抓取失败时必须使用搜索 snippet fallback。

fetch_status 应明确标记：

```text
success
fallback_snippet
timeout
http_error
parse_error
blocked
```

## 12.3 必须限制正文长度

MVP 建议正文最大长度：

```text
20,000 - 50,000 characters
```

避免把超长网页直接塞给 LLM。

## 12.4 不做复杂反爬

MVP 不处理：

```text
登录页面
验证码
动态渲染
复杂反爬
浏览器自动化
```

---

# 十三、来源分类约束

## 13.1 第一版基于域名和 URL 规则

Source Classifier 第一版只做规则分类。

不得一开始引入复杂模型。

## 13.2 unknown 是合法来源类型

无法识别时返回：

```text
unknown
```

不得乱判为官方来源。

## 13.3 source_type 不等于绝对可信

source_type 只提供基础分，不代表事实一定正确。

例如：

```text
official_model_card 对“模型是否发布”可信度高
但对“模型是否最强”不一定可信
```

## 13.4 社区来源不能单独支撑 confirmed

以下来源不得单独支撑 confirmed：

```text
community_forum
seo_content
unknown
```

除非后续有强规则明确允许，否则默认禁止。

---

# 十四、证据抽取约束

## 14.1 证据只能来自原文

Evidence Extractor 不允许编造 evidence_text。

不允许把模型自己的推测写成证据。

## 14.2 找不到证据必须返回空数组

禁止为了凑结果生成弱证据。

正确行为：

```json
{
  "evidence": []
}
```

## 14.3 evidence_text 必须短

每条 evidence 建议：

```text
1-3 句话
不超过 500 字符
```

## 14.4 support_type 必须枚举

只能使用：

```text
support
oppose
partial
neutral
```

## 14.5 LLM 抽取必须有强约束提示词

提示词必须要求：

```text
只能引用原文
不能改写成原文没有的事实
不能补充外部知识
找不到证据返回空数组
必须输出 JSON
support_type 必须枚举化
relevance_score 必须是 0 到 1
```

## 14.6 neutral 证据默认不参与 confirmed

neutral evidence 可以保留，但不得用于支持 confirmed。

---

# 十五、可信度评分约束

## 15.1 第一版公式固定

MVP 第一版使用：

```text
final_score = relevance_score × source_base_score × primary_source_factor × recency_factor
```

不得一开始加入过复杂公式。

## 15.2 必须输出 score_breakdown

每条 evidence 都必须解释分数来源：

```json
{
  "relevance_score": 0.86,
  "source_base_score": 0.88,
  "primary_source_factor": 1.10,
  "recency_factor": 1.00,
  "final_score": 0.83
}
```

## 15.3 分数必须 clamp 到 0-1

final_score 最终必须限制在：

```text
0.0 <= final_score <= 1.0
```

## 15.4 低相关性不能被高来源分强行抬高

如果 relevance_score 很低，final_score 不应很高。

证据首先要相关，然后才谈来源可信度。

---

# 十六、命题聚合约束

## 16.1 每个 claim 必须有状态

状态只能是：

```text
confirmed
likely
uncertain
unsupported
conflicting
false_likely
```

## 16.2 unsupported 不是错误

没有证据时必须返回 unsupported，而不是报错，也不是编造证据。

## 16.3 conflicting 不能被压平

如果同一 claim 下同时存在高分 support 和高分 oppose，必须标记 conflicting。

不得自动选择一边。

## 16.4 confirmed 必须有足够证据

confirmed 至少需要：

```text
1. 高分 support evidence
2. 来源不能只是社区/SEO/unknown
3. 没有高分 oppose evidence
```

---

# 十七、回答约束生成约束

## 17.1 answer_constraints 必须始终返回

即使没有证据，也必须返回回答约束。

## 17.2 不确定时必须限制语气

如果存在：

```text
uncertain
unsupported
conflicting
```

则必须设置：

```text
can_answer_confidently = false
must_disclose_uncertainty = true
allowed_tone = cautious
```

## 17.3 必须生成 forbidden_phrases

对于证据不足的问题，必须禁止：

```text
毫无疑问
已经确定
官方确认
完全证实
可以肯定
```

## 17.4 必须生成 required_phrases

根据状态生成必要表达，例如：

```text
目前只能确认
现有证据不足以确认
来源之间存在冲突
只能说有传言称
仍需查看官方来源
```

---

# 十八、冲突检测约束

## 18.1 冲突检测后置

冲突检测增强属于阶段 11。

在阶段 10 之前可以只做 claim_aggregator 中的简单 conflicting 判断。

## 18.2 冲突必须绑定 claim

冲突不是全局概念，必须说明哪个 claim 发生冲突。

## 18.3 冲突摘要必须谨慎

conflict summary 不得替用户裁决事实，只说明：

```text
哪些来源支持
哪些来源反对
冲突严重程度
为什么不能直接 confirmed
```

---

# 十九、测试约束

## 19.1 每个模块必须有单元测试

至少包括：

```text
question_classifier
claim_decomposer
search_planner
search_adapter
source_classifier
page_fetcher
evidence_extractor
reliability_scorer
claim_aggregator
answer_constraint_builder
```

## 19.2 trusted-search 必须有接口测试

至少测试：

```text
正常 query
空 query
无搜索结果
搜索 API 失败
网页抓取失败
无证据
存在 uncertain
存在 conflicting
```

## 19.3 外部依赖必须 mock

以下内容测试中必须 mock：

```text
搜索 API
网页请求
LLM 调用
当前时间
```

## 19.4 端到端测试必须稳定

端到端测试不得依赖实时搜索结果。

必须使用固定 mock 数据。

---

# 二十、安全约束

## 20.1 高风险领域默认不自动下结论

以下领域不得仅凭普通网页或社区来源给出 confirmed：

```text
医学
金融
法律
政策有效性
人身安全
```

MVP 不主动支持医学、金融自动决策。

## 20.2 不提供高风险建议

系统可以做来源核查，但不应直接生成：

```text
医疗诊断建议
投资买卖建议
具体法律行动建议
危险操作指导
```

## 20.3 必须保留不确定性

证据不足时必须输出：

```text
uncertain
unsupported
must_disclose_uncertainty = true
```

---

# 二十一、配置约束

## 21.1 来源分数必须配置化

source_base_score 不得硬编码在业务逻辑里。

应放在：

```text
app/policies/source_policy.yml
```

## 21.2 问题类型策略必须配置化

不同 question_type 的来源偏好、确认阈值、新鲜度要求，应放在：

```text
app/policies/question_policy.yml
```

## 21.3 环境变量不得硬编码

API key、base URL、timeout 等必须通过配置读取。

禁止直接写死在代码里。

---

# 二十二、日志与错误处理约束

## 22.1 必须记录关键流程日志

建议记录：

```text
question_type 识别结果
claim 数量
search query 数量
source 数量
fetch 成功/失败数量
evidence 数量
claim status 分布
```

## 22.2 不记录敏感内容

日志中避免记录：

```text
完整 API key
过长网页正文
完整用户隐私内容
```

## 22.3 错误必须可定位

外部调用失败时，应记录：

```text
模块名
错误类型
URL 或 query
是否 fallback
```

但不要把内部堆栈直接暴露给 API 用户。

---

# 二十三、性能约束

## 23.1 MVP 不追求高并发

MVP 优先正确性和可控性，不追求高并发吞吐。

## 23.2 必须限制外部调用数量

默认：

```text
max_sources = 8
每个 claim 不应无限生成 query
每个 query 不应无限返回结果
```

## 23.3 必须避免无限等待

所有外部请求必须有 timeout。

LLM 调用也必须有超时或失败 fallback。

---

# 二十四、Git 与版本约束

## 24.1 每阶段一个 commit

每完成一个阶段，应至少提交一次 commit。

commit message 示例：

```text
feat(api): add trusted search mock endpoint
feat(classifier): add rule based question classifier
feat(search): add search planner and adapter
```

## 24.2 每阶段一个 tag

推荐 tag：

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

## 24.3 未通过测试不得打 tag

打 tag 前必须：

```text
pytest 通过
核心接口手动验证通过
README 如有必要已更新
```

---

# 二十五、AI Agent 执行约束

## 25.1 Agent 不得擅自扩展范围

给 Codex / Claude Code 执行某阶段任务时，必须明确：

```text
只做本阶段任务
不要做后续阶段
不要接未要求的外部服务
不要重构无关代码
```

## 25.2 Agent 必须先读文档

执行前必须读取：

```text
PRD
开发顺序文档
约束文档
```

## 25.3 Agent 输出必须包含

每次开发完成后，Agent 应输出：

```text
1. 修改了哪些文件
2. 新增了哪些测试
3. 如何运行测试
4. 哪些内容未做
5. 是否有风险或待确认项
```

## 25.4 禁止一次性大改

Agent 不应一次性实现多个阶段。

如果任务变大，必须拆成多个小 commit。

---

# 二十六、Definition of Done

一个阶段完成，必须同时满足：

```text
1. 代码实现完成
2. 单元测试完成
3. 接口测试完成，如果涉及 API
4. pytest 通过
5. README 或注释必要更新
6. 没有引入不必要依赖
7. 没有越界实现下一阶段功能
8. 可以 git commit
9. 可以打对应 tag
```

---

# 二十七、当前阶段约束

当前最应该执行的阶段是：

```text
阶段 0 + 阶段 1
```

即：

```text
FastAPI 骨架
/health 接口
/api/v1/trusted-search mock 接口
Pydantic schemas
pytest 测试
README 基础说明
```

当前禁止：

```text
不接搜索 API
不接 LLM
不做数据库
不做 MCP
不做前端
不做复杂评分
不做网页抓取
```

---

# 二十八、给 Codex 的约束版第一条指令

```text
请先阅读 PRD、开发顺序文档和约束文档。现在只执行阶段 0 + 阶段 1：创建 FastAPI 项目骨架、/health 接口、/api/v1/trusted-search mock 接口、Pydantic schemas 和基础 pytest 测试。

严格遵守以下约束：
1. 不接搜索 API。
2. 不接 LLM。
3. 不做数据库。
4. 不做 MCP。
5. 不做前端。
6. 不实现真实证据抽取和评分。
7. trusted-search 只返回符合 PRD schema 的 mock evidence package。
8. 所有新增功能必须有测试。
9. 保证 pytest 通过。
10. 完成后说明修改文件、测试方式、未做事项和下一步建议。
```

---

# 二十九、总结

Critical Search Layer 的开发纪律可以概括为一句话：

```text
先固定接口基准，再逐步替换 mock；先打穿证据闭环，再增强可信度；先做 Agent 工具，再考虑产品界面。
```

不要追求一步到位。

这个项目真正的价值不在于“搜得更多”，而在于：

```text
让 AI 在回答之前先知道哪些能信、哪些不能信、哪些必须保留不确定性。
```
