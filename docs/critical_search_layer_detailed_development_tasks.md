# Critical Search Layer 详细开发任务拆解

版本：v0.1-detailed  
文档类型：阶段开发任务 / 工序卡 / Agent 执行清单  
适用对象：Codex、Claude Code、开发者本人  
项目形态：AI Agent 可调用的可信搜索工具 / 插件 / 中间件

---

# 一、总开发思想

这个项目不要一开始追求完整系统，而要像加工机械零件一样：

> 先确定基准面，再粗加工，再半精加工，再精加工，最后总装验收。

对应到 Critical Search Layer：

```text
毛坯：一个想法 + PRD + 开发顺序文档

工序 0：项目基准面
工序 1：接口基准和数据结构
工序 2：问题分类 + 命题拆解
工序 3：搜索计划 + 搜索适配器
工序 4：来源分类
工序 5：网页抓取和正文解析
工序 6：证据抽取
工序 7：可信度评分
工序 8：命题状态聚合
工序 9：回答约束生成
工序 10：端到端闭环
工序 11：冲突检测增强
工序 12：MCP 工具化
```

核心原则：

```text
每个阶段都必须留下一个可以运行、可以测试、可以回退的小成品。
```

不要一开始做数据库、前端、多搜索源、复杂评分、MCP、证据图谱。  
先跑通最小闭环：

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

---

# 二、推荐三轮开发闭环

## 第一轮：把零件毛坯做出来

目标：

```text
项目能启动
接口能调用
mock JSON 能返回
```

包含阶段：

```text
阶段 0：项目骨架
阶段 1：Schema 和 mock 接口
```

产物：

```text
FastAPI skeleton
health 接口
trusted-search mock 接口
Pydantic schemas
pytest 基础测试
```

这是当前最应该先做的。

---

## 第二轮：打穿最小功能闭环

目标：

```text
输入问题后，能得到 claims、sources、evidence、scores、constraints
```

包含阶段：

```text
阶段 2：问题分类 + 命题拆解
阶段 3：搜索计划 + 搜索适配器
阶段 4：来源分类
阶段 5：网页抓取和正文解析
阶段 6：证据抽取
阶段 7：可信度评分
阶段 8：命题状态聚合
阶段 9：回答约束生成
阶段 10：端到端集成测试
```

产物：

```text
v0.1 最小可信搜索闭环
```

这时项目已经成立。

---

## 第三轮：增强可信度和工具化

目标：

```text
处理冲突
支持 Agent 调用
扩展领域策略
```

包含阶段：

```text
阶段 11：冲突检测增强
阶段 12：MCP 工具封装
后续领域扩展
```

产物：

```text
可被 Claude / Cursor / Codex / 自建 Agent 调用的可信搜索工具
```

---

# 三、阶段 0：项目骨架，先加工基准面

## 阶段目标

让项目能启动、能测试、能扩展。

这一步不是做业务，而是像加工零件前先铣一个基准面。没有基准面，后面所有尺寸都会乱。

## 开发任务

```text
1. 创建 FastAPI 项目结构
2. 创建 app/main.py
3. 创建 app/core/config.py
4. 创建 app/core/logging.py
5. 创建 app/core/exceptions.py
6. 创建 app/api/routes/health.py
7. 配置 pytest
8. 创建基础健康检查测试
9. 创建 README 基础运行说明
```

## 建议目录结构

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

README.md
```

## 本阶段不做

```text
不做搜索
不做 LLM
不做数据库
不做证据抽取
不做复杂配置
不做 MCP
不做前端
```

## 验收标准

```text
uvicorn app.main:app --reload 可以启动
GET /health 返回 {"status": "ok"}
pytest 能跑通
项目结构固定下来
```

## 建议 Git 标签

```text
v0.1.0-skeleton
```

## 给 Codex / Claude Code 的指令

```text
创建 Critical Search Layer 的 FastAPI 项目骨架，只完成 app/main.py、配置模块、日志模块、基础异常处理、/health 接口和 pytest 测试。不要实现业务逻辑，保证项目能启动且测试通过。
```

---

# 四、阶段 1：Schema 和 mock 接口，确定装夹基准

## 阶段目标

固定系统输入输出边界。

这一步相当于确定零件总尺寸、公差、定位孔。后面内部模块怎么换，都不能破坏这个接口。

## 开发任务

```text
1. 定义 TrustedSearchRequest
2. 定义 TrustedSearchResponse
3. 定义 ClaimSchema
4. 定义 SourceSchema
5. 定义 EvidenceSchema
6. 定义 AnswerConstraintsSchema
7. 定义 ErrorResponse
8. 创建 /api/v1/trusted-search 路由
9. trusted-search 先返回 mock evidence package
10. 写接口测试
```

## 建议目录结构

```text
app/
  api/
    routes/
      trusted_search.py
  schemas/
    trusted_search.py
    claim.py
    source.py
    evidence.py
    constraints.py

tests/
  api/
    test_trusted_search_mock.py
```

## TrustedSearchRequest 建议字段

```text
query: string，必填
question_type: auto / ai_model_info / tech_news / product_info / policy_legal / technical_doc / general_fact / unknown，默认 auto
strictness: loose / balanced / strict，默认 balanced
max_sources: int，默认 8
require_primary_source: bool，默认 false
return_raw_evidence: bool，默认 true
```

## TrustedSearchResponse 必须包含

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

## ClaimSchema 建议字段

```text
claim_id
claim_text
claim_type
status
confidence
reason
evidence
```

## SourceSchema 建议字段

```text
source_id
title
url
domain
source_type
base_reliability
is_primary_source
published_at
author
fetched_at
```

## EvidenceSchema 建议字段

```text
evidence_id
claim_id
source_id
evidence_text
support_type
relevance_score
source_score
primary_source_factor
recency_factor
cross_check_factor
conflict_penalty
interest_conflict_penalty
final_score
score_breakdown
```

## AnswerConstraintsSchema 建议字段

```text
can_answer_confidently
must_disclose_uncertainty
must_cite_sources
allowed_tone
required_phrases
forbidden_phrases
```

## 本阶段不做

```text
不做真实搜索
不做真实分类
不做真实评分
不接 LLM
不做数据库
```

## 验收标准

```text
POST /api/v1/trusted-search 可以接收 query
接口返回结构符合 schema
query 为空时返回参数错误
pytest 通过
```

## 建议 Git 标签

```text
v0.1.1-api-schema
```

## 给 Codex / Claude Code 的指令

```text
为 Critical Search Layer 添加 trusted-search 的 Pydantic schemas 和 /api/v1/trusted-search mock 接口。接口接收 query、question_type、strictness、max_sources 等字段，返回符合 PRD 的结构化 JSON。不要接搜索 API 和 LLM，补充接口测试。
```

---

# 五、阶段 2：问题分类 + 命题拆解，开始粗加工轮廓

## 阶段目标

让系统知道用户问的是什么，以及应该拆成哪些可验证命题。

这一阶段先用规则和模板，不追求智能。

## 2.1 Question Classifier

### 开发任务

```text
1. 创建 app/services/question_classifier.py
2. 定义 classify_question(query: str) 方法
3. 返回 question_type 和 risk_level
4. 写规则分类逻辑
5. 写单元测试
```

### 第一版分类规则

```text
ai_model_info:
  模型、LLM、Hugging Face、开源、权重、license、GitHub、模型卡、参数量

tech_news:
  发布、爆料、传言、最新、下周、消息、官宣、泄露

product_info:
  参数、价格、显存、配置、商品、京东、天猫、型号、评测

policy_legal:
  政策、法规、法律、监管、政府、是否有效、条例、办法

technical_doc:
  Python、API、报错、函数、库、文档、SDK、框架

general_fact:
  普通事实类问题

unknown:
  无法判断
```

### risk_level 建议规则

```text
policy_legal: high
product_info: medium
tech_news: medium
ai_model_info: medium
technical_doc: low / medium
general_fact: low
unknown: medium
```

## 2.2 Claim Decomposer

### 开发任务

```text
1. 创建 app/services/claim_decomposer.py
2. 定义 decompose(query, question_type) 方法
3. 第一版只重点支持 ai_model_info
4. 对其他类型返回简单通用 claim 或暂时 fallback
5. 写单元测试
```

### AI 模型信息类模板

输入：

```text
MiroThinker 1.7 是不是开源模型？
```

输出：

```text
c1: MiroThinker 1.7 是否存在公开发布页面
c2: MiroThinker 1.7 是否公开模型权重
c3: MiroThinker 1.7 是否公开训练代码
c4: MiroThinker 1.7 是否公开训练数据
c5: MiroThinker 1.7 的许可证是否允许商用
c6: MiroThinker 1.7 是否能严格称为开源模型
```

### claim_type 建议枚举

```text
existence
model_weights
source_code
training_data
license
interpretation
release_status
product_spec
policy_validity
general_fact
```

## 建议目录结构

```text
app/services/
  question_classifier.py
  claim_decomposer.py

tests/services/
  test_question_classifier.py
  test_claim_decomposer.py
```

## 本阶段不做

```text
不调用搜索
不接 LLM
不做复杂自然语言理解
不支持所有问题类型的精细拆解
```

## 验收标准

```text
AI 模型问题能识别为 ai_model_info
产品参数问题能识别为 product_info
政策问题能识别为 policy_legal
无法识别时返回 unknown
MiroThinker 问题能拆出 5-6 个 claim
每个 claim 有 claim_id、claim_text、claim_type
```

## 建议 Git 标签

```text
v0.1.2-question-claims
```

## 给 Codex / Claude Code 的指令

```text
实现 question_classifier 和 claim_decomposer。分类先用规则，命题拆解第一版只支持 ai_model_info，用模板拆出模型存在、权重开放、代码开放、训练数据、许可证、是否严格开源等 claim。补充单元测试。
```

---

# 六、阶段 3：搜索计划 + 搜索适配器，开粗外形

## 阶段目标

把 claim 变成搜索词，并且能拿到候选来源。

这一阶段只负责找材料，不负责判断真假。

## 3.1 Search Planner

### 开发任务

```text
1. 创建 app/services/search_planner.py
2. 根据 question_type 和 claims 生成 search_plan
3. 第一版重点支持 ai_model_info
4. 每个 claim 至少生成 1 个 query
5. 每个 query 附带 preferred_source_types
6. 写测试
```

### AI 模型信息类搜索模板

```text
{entity} Hugging Face
{entity} GitHub
{entity} paper
{entity} arXiv
{entity} license
{entity} official
{entity} model card
{entity} weights
```

### 输出示例

```json
{
  "claim_id": "c2",
  "queries": [
    "MiroThinker 1.7 Hugging Face",
    "MiroThinker 1.7 model weights",
    "MiroThinker 1.7 license"
  ],
  "preferred_source_types": [
    "official_model_card",
    "source_code_repo",
    "academic_paper"
  ]
}
```

## 3.2 Search Adapter

### 开发任务

```text
1. 创建 app/services/search_adapter.py
2. 第一版只接一个搜索 API
3. 支持 max_results
4. 统一搜索结果结构
5. 实现 URL 去重
6. 搜索失败返回可控错误，不中断总流程
7. 外部 API 测试必须 mock
```

### 搜索 API 推荐顺序

```text
1. Tavily
2. Brave Search API
3. SerpAPI
4. Bing Search API
```

### SearchResult 字段

```text
title
url
snippet
published_at
```

### URL 去重规则

```text
去掉 fragment
去掉常见 tracking 参数
同一 url 只保留一次
```

## 建议目录结构

```text
app/services/
  search_planner.py
  search_adapter.py

tests/services/
  test_search_planner.py
  test_search_adapter.py
```

## 本阶段不做

```text
不做网页抓取
不做来源可信度评分
不做多搜索 API
不做复杂 rerank
```

## 验收标准

```text
每个 claim 至少生成 1 个 query
ai_model_info 有 Hugging Face / GitHub / paper / license 查询
搜索失败不会让接口崩溃
搜索结果有 title、url、snippet
搜索结果去重
```

## 建议 Git 标签

```text
v0.1.3-search-adapter
```

## 给 Codex / Claude Code 的指令

```text
实现 search_planner 和 search_adapter。search_planner 根据 ai_model_info 的 claim 生成 Hugging Face、GitHub、paper、arXiv、license、official 等搜索词。search_adapter 先接入一个搜索 API，统一返回 title、url、snippet、published_at，并实现 URL 去重和失败降级。补充测试，外部 API 用 mock。
```

---

# 七、阶段 4：来源分类器，给材料分等级

## 阶段目标

判断每个来源属于什么材料。

就像加工时要分清楚：这是 45 钢、铝合金、铸铁，还是来路不明的材料。来源类型会直接影响可信度评分。

## 开发任务

```text
1. 创建 app/policies/source_policy.yml
2. 写 source_type 基础分
3. 创建 app/services/source_classifier.py
4. 根据域名识别 source_type
5. 判断 is_primary_source
6. 返回 base_reliability
7. 写来源分类测试
```

## source_policy.yml 建议内容

```yaml
source_types:
  official_docs:
    base_score: 0.95
    description: "官方文档、产品说明、平台文档"

  official_blog:
    base_score: 0.90
    description: "公司或项目官方博客"

  official_model_card:
    base_score: 0.88
    description: "Hugging Face、ModelScope 等模型卡"

  source_code_repo:
    base_score: 0.88
    description: "GitHub/GitLab 源码仓库"

  academic_paper:
    base_score: 0.90
    description: "论文、预印本、学术出版物"

  government_docs:
    base_score: 0.95
    description: "政府文件、法规、监管公告"

  financial_filing:
    base_score: 0.95
    description: "财报、SEC 文件、交易所公告"

  mainstream_media:
    base_score: 0.75
    description: "主流媒体报道"

  expert_blog:
    base_score: 0.65
    description: "领域专家博客"

  community_forum:
    base_score: 0.40
    description: "论坛、Reddit、知乎、X 等社区内容"

  product_page:
    base_score: 0.80
    description: "商品页、厂商参数页"

  seo_content:
    base_score: 0.20
    description: "SEO 聚合站、无署名搬运站"

  unknown:
    base_score: 0.30
    description: "未知来源"
```

## 域名规则第一版

```text
huggingface.co    → official_model_card
modelscope.cn     → official_model_card
github.com        → source_code_repo
gitlab.com        → source_code_repo
arxiv.org         → academic_paper
openreview.net    → academic_paper
sec.gov           → financial_filing
*.gov             → government_docs
reddit.com        → community_forum
zhihu.com         → community_forum
x.com             → community_forum
docs.*            → official_docs 候选
*/docs/*          → official_docs 候选
unknown           → unknown
```

## 建议目录结构

```text
app/policies/
  source_policy.yml

app/services/
  source_classifier.py

tests/services/
  test_source_classifier.py
```

## 本阶段不做

```text
不判断网页内容真假
不做复杂来源历史信誉
不做转载链识别
不做人工校正系统
```

## 验收标准

```text
常见域名分类准确
无法识别返回 unknown
每个 source_type 有 base_reliability
primary source 能被标记
```

## 建议 Git 标签

```text
v0.1.4-source-classifier
```

## 给 Codex / Claude Code 的指令

```text
添加 source_policy.yml，并实现 source_classifier。根据域名规则识别 official_model_card、source_code_repo、academic_paper、government_docs、community_forum、unknown 等类型，返回 base_reliability 和 is_primary_source。补充单元测试。
```

---

# 八、阶段 5：网页抓取与正文解析，开始取有效加工面

## 阶段目标

从 URL 拿到正文，而不是只看搜索摘要。

搜索摘要只是毛坯表面，正文才是可加工材料。正文质量决定后面的证据抽取质量。

## 开发任务

```text
1. 创建 app/services/page_fetcher.py
2. 用 httpx 请求网页
3. 设置 timeout
4. 设置 user-agent
5. 用 trafilatura 提取正文
6. 提取失败时 fallback 到 snippet
7. 限制正文最大长度
8. 返回 fetch_status
9. 写抓取测试
```

## 输出字段

```text
url
title
text
fetch_status
metadata.published_at
metadata.author
```

## fetch_status 建议枚举

```text
success
fallback_snippet
timeout
http_error
parse_error
blocked
```

## 正文长度限制建议

```text
默认最大 12000 - 20000 字符
超过则截断
保留截断标记
```

## 建议目录结构

```text
app/services/
  page_fetcher.py

tests/services/
  test_page_fetcher.py
```

## 本阶段不做

```text
不做浏览器渲染
不处理登录页面
不做 PDF 特殊解析
不做 GitHub / HuggingFace 专项适配
```

## 验收标准

```text
普通网页能拿到正文
失败时使用 snippet
超时不会卡死
正文长度被限制
fetch_status 明确
```

## 建议 Git 标签

```text
v0.1.5-page-fetcher
```

## 给 Codex / Claude Code 的指令

```text
实现 page_fetcher。使用 httpx 抓取网页，用 trafilatura 提取正文，设置 timeout 和正文最大长度。抓取或解析失败时使用搜索 snippet fallback，并返回 fetch_status。补充 mock 测试。
```

---

# 九、阶段 6：证据抽取器，从材料里切出有效特征

## 阶段目标

从正文中抽出能支持或反驳 claim 的短证据。

这是项目从“普通搜索工具”变成“批判性搜索工具”的关键模块。

普通搜索工具返回网页。  
Critical Search Layer 必须返回证据。

## 开发任务

```text
1. 创建 app/services/evidence_extractor.py
2. 定义 EvidenceExtractor 接口
3. 第一版支持 LLM 抽取接口
4. 增加简单关键词 fallback
5. 限制 evidence_text 只能来自原文
6. 判断 support_type
7. 生成 relevance_score
8. 无证据时返回空数组
9. 写测试
```

## support_type 枚举

```text
support   支持
oppose    反驳
partial   部分支持
neutral   中立 / 无关
```

## LLM 抽取硬约束

```text
只能引用原文
不能总结成原文没有的话
找不到证据返回 []
每条证据 1-3 句话
support_type 只能是 support / oppose / partial / neutral
relevance_score 必须是 0-1
```

## LLM 提示词骨架

```text
你是证据抽取器。你的任务是从 document_text 中抽取与 claim 相关的原文证据。

要求：
1. evidence_text 必须来自 document_text，不能编造。
2. 如果找不到相关证据，返回空数组 []。
3. 每条证据控制在 1-3 句话。
4. support_type 只能是 support、oppose、partial、neutral。
5. relevance_score 范围为 0.0 到 1.0。
6. 不要输出自然语言解释，只输出 JSON。

claim:
{claim}

document_text:
{document_text}
```

## fallback 关键词规则第一版

```text
权重:
  weights / model weights / safetensors / checkpoint / 权重 / 模型权重

许可证:
  license / apache / mit / commercial / 商用 / 许可证

代码:
  code / training code / github / repository / 代码 / 训练代码

训练数据:
  dataset / training data / data / 训练数据 / 数据集

发布页面:
  model card / release / official / 发布 / 模型卡
```

## 建议目录结构

```text
app/services/
  evidence_extractor.py

tests/services/
  test_evidence_extractor.py
```

## 本阶段不做

```text
不追求 100% 准确
不做复杂事实推理
不让 LLM 自由发挥
不允许编造证据
```

## 验收标准

```text
每条 evidence 绑定 claim_id
证据文本短
support_type 枚举正确
无证据返回 []
不能从空正文里编造 evidence
```

## 建议 Git 标签

```text
v0.1.6-evidence-extractor
```

## 给 Codex / Claude Code 的指令

```text
实现 evidence_extractor。第一版支持 LLM 抽取接口，同时提供简单关键词 fallback。抽取结果必须包含 claim_id、evidence_text、support_type、relevance_score。证据只能来自原文，找不到证据返回空数组。补充测试覆盖 support、partial、neutral 和无证据场景。
```

---

# 十、阶段 7：可信度评分器，做尺寸检测和材料加权

## 阶段目标

给每条证据算 final_score。

注意：这不是判断绝对真理，而是判断“这条证据对这个命题有多值得信”。

第一版不要把公式做复杂，先用简化公式：

```text
final_score = relevance_score × source_base_score × primary_source_factor × recency_factor
```

## 开发任务

```text
1. 创建 app/services/reliability_scorer.py
2. 读取 source_base_score
3. 使用 relevance_score
4. 判断 primary_source_factor
5. 判断 recency_factor
6. 计算 final_score
7. 返回 score_breakdown
8. 写评分测试
```

## score_breakdown 示例

```json
{
  "relevance_score": 0.86,
  "source_base_score": 0.88,
  "primary_source_factor": 1.10,
  "recency_factor": 1.00,
  "final_score": 0.83
}
```

## primary_source_factor 第一版规则

```text
primary source:      1.10
secondary source:    1.00
unclear source:      0.90
```

## recency_factor 第一版规则

```text
没有日期:       1.00
一年内:         1.05
1-3 年:         1.00
3 年以上:       0.80
明显过期:       0.60
```

对于以下问题类型，应更重视新鲜度：

```text
ai_model_info
tech_news
product_info
policy_legal
technical_doc
```

## 本阶段暂不做的因子

```text
cross_check_factor
conflict_penalty
interest_conflict_penalty
```

这些留到后续增强。

## 建议目录结构

```text
app/services/
  reliability_scorer.py

tests/services/
  test_reliability_scorer.py
```

## 验收标准

```text
每条 evidence 有 final_score
每条 evidence 有 score_breakdown
官方来源分数高于社区来源
低 relevance 不能因为来源强就变 confirmed
```

## 建议 Git 标签

```text
v0.1.7-reliability-scorer
```

## 给 Codex / Claude Code 的指令

```text
实现 reliability_scorer。第一版公式为 final_score = relevance_score × source_base_score × primary_source_factor × recency_factor。输出 score_breakdown。不同 source_type 使用 source_policy.yml 的 base_score。补充测试。
```

---

# 十一、阶段 8：命题聚合器，把局部尺寸汇总成零件状态

## 阶段目标

根据 evidence 判断每个 claim 的状态。

这一步相当于质检：这个孔合格、那个面欠加工、这里有冲突、那里没有材料。

## 开发任务

```text
1. 创建 app/services/claim_aggregator.py
2. 收集同一 claim 下的 evidence
3. 区分 support / oppose / partial / neutral
4. 找最高支持分
5. 找最高反对分
6. 判断 status
7. 生成 confidence
8. 生成 reason
9. 写聚合测试
```

## claim status 枚举

```text
confirmed     高可信证据支持
likely        有较强证据支持，但仍有不足
uncertain     证据不足，无法确认
unsupported   未找到可靠证据支持
conflicting   存在明显冲突
false_likely  有较强证据反驳
```

## 第一版规则

```text
confirmed:
  最高 support 分数 >= 0.80
  且最高 oppose 分数 < 0.70

likely:
  最高 support 分数 >= 0.65
  且不足 confirmed

uncertain:
  有 partial 或低分 support
  但不足 likely

unsupported:
  没有 support 或 partial evidence

false_likely:
  最高 oppose 分数 >= 0.75
  且 support 很弱

conflicting:
  最高 support 分数 >= 0.75
  且最高 oppose 分数 >= 0.75
```

## 输出示例

```json
{
  "claim_id": "c2",
  "status": "confirmed",
  "confidence": 0.86,
  "reason": "官方模型卡提供了与该命题直接相关的高分支持证据。"
}
```

## 建议目录结构

```text
app/services/
  claim_aggregator.py

tests/services/
  test_claim_aggregator.py
```

## 本阶段不做

```text
不生成最终自然语言回答
不隐藏冲突
不强行把所有 claim 合成一个肯定结论
```

## 验收标准

```text
每个 claim 都有 status
每个 claim 都有 confidence
没有证据时是 unsupported
有高分支持和高分反对时是 conflicting
```

## 建议 Git 标签

```text
v0.1.8-claim-aggregator
```

## 给 Codex / Claude Code 的指令

```text
实现 claim_aggregator。根据每个 claim 下 evidence 的 support_type 和 final_score 聚合出 confirmed、likely、uncertain、unsupported、false_likely、conflicting 状态，并生成 confidence 和 reason。补充测试。
```

---

# 十二、阶段 9：回答约束生成器，限制 AI 的加工误差

## 阶段目标

把 claim 状态转成 AI 回答时必须遵守的规则。

这就是 Critical Search Layer 和普通搜索增强的关键差异：不是只给信息，而是约束 AI 不能胡说。

## 开发任务

```text
1. 创建 app/services/answer_constraint_builder.py
2. 根据所有 claim status 判断 overall_status
3. 生成 can_answer_confidently
4. 生成 must_disclose_uncertainty
5. 生成 must_cite_sources
6. 生成 allowed_tone
7. 生成 required_phrases
8. 生成 forbidden_phrases
9. 写测试
```

## 规则第一版

```text
所有核心 claim confirmed:
  can_answer_confidently = true
  allowed_tone = "confident"

存在 uncertain:
  must_disclose_uncertainty = true
  allowed_tone = "cautious"

存在 unsupported:
  禁止肯定表达

存在 conflicting:
  必须说明来源冲突

只有社区来源:
  禁止说“已确认”“官方确认”
```

## forbidden_phrases 建议

```text
毫无疑问
已经确定
官方确认
完全证实
一定是
已经完全开源
没有任何问题
```

## required_phrases 建议

```text
目前只能确认部分信息
仍需进一步核查
现有证据不足以确认
需要区分权重开放、代码开放、训练数据开放和许可证限制
存在来源冲突
不能仅凭社区传言下结论
```

## 输出示例

```json
{
  "can_answer_confidently": false,
  "must_disclose_uncertainty": true,
  "must_cite_sources": true,
  "allowed_tone": "cautious",
  "required_phrases": [
    "目前只能确认部分信息",
    "仍需区分权重开放、代码开放、训练数据开放和许可证限制"
  ],
  "forbidden_phrases": [
    "毫无疑问",
    "已经完全开源",
    "官方已经确认"
  ]
}
```

## 建议目录结构

```text
app/services/
  answer_constraint_builder.py

tests/services/
  test_answer_constraint_builder.py
```

## 本阶段不做

```text
不生成完整回答
不做聊天机器人
不做前端展示
```

## 验收标准

```text
uncertain 必须触发不确定性披露
unsupported 禁止肯定表达
conflicting 必须要求说明冲突
confirmed 才允许较确定语气
```

## 建议 Git 标签

```text
v0.1.9-answer-constraints
```

## 给 Codex / Claude Code 的指令

```text
实现 answer_constraint_builder。根据 claim status 生成 can_answer_confidently、must_disclose_uncertainty、must_cite_sources、allowed_tone、required_phrases、forbidden_phrases。确保 uncertain、unsupported、conflicting 不会允许高确定性表达。补充测试。
```

---

# 十三、阶段 10：端到端集成，第一次总装

## 阶段目标

把前面所有模块串起来，形成完整 trusted-search 流程。

这一步不是继续加功能，而是检查主轴、夹具、刀路、尺寸链有没有闭合。

## 开发任务

```text
1. 创建 app/services/trusted_search_service.py
2. 串联 question_classifier
3. 串联 claim_decomposer
4. 串联 search_planner
5. 串联 search_adapter
6. 串联 source_classifier
7. 串联 page_fetcher
8. 串联 evidence_extractor
9. 串联 reliability_scorer
10. 串联 claim_aggregator
11. 串联 answer_constraint_builder
12. trusted-search 接口调用 TrustedSearchService
13. 返回最终 JSON
14. 写端到端测试
15. 写失败场景测试
```

## 主流程

```text
query
  → classify
  → decompose claims
  → plan searches
  → search
  → classify sources
  → fetch pages
  → extract evidence
  → score evidence
  → aggregate claims
  → build constraints
  → response
```

## 端到端测试必须 mock

必须 mock：

```text
搜索 API
网页正文
LLM 证据抽取
```

否则测试会受网络、API、网页变动影响。

## 测试用例

```text
1. MiroThinker 1.7 是不是开源模型？
2. OpenAI 下周会发布某个代号模型吗？
3. 某款笔记本 RTX 5070 Ti 是不是 12GB 显存？
4. 某项政策现在是否还有效？
```

## 失败场景测试

```text
搜索 API 失败
网页抓取超时
网页正文为空
LLM 抽取返回空数组
只有低可信来源
支持和反对证据冲突
```

## 建议目录结构

```text
app/services/
  trusted_search_service.py

tests/e2e/
  test_trusted_search_flow.py
```

## 本阶段不做

```text
不优化算法
不新增数据库
不做 MCP
不做前端
```

## 验收标准

```text
POST /api/v1/trusted-search 能跑完整流程
正常场景返回 evidence package
搜索失败也能返回可控结果
抓取失败使用 snippet fallback
没有证据时 claim 是 unsupported
pytest 通过
```

## 建议 Git 标签

```text
v0.1.10-e2e-mvp
```

## 给 Codex / Claude Code 的指令

```text
创建 TrustedSearchService，把 question_classifier、claim_decomposer、search_planner、search_adapter、source_classifier、page_fetcher、evidence_extractor、reliability_scorer、claim_aggregator、answer_constraint_builder 串成完整流程。trusted-search 接口调用该 service。端到端测试使用 mock 搜索结果和 mock 网页正文。
```

---

# 十四、阶段 11：冲突检测增强，做精加工和缺陷检测

## 阶段目标

识别同一 claim 下的高分支持证据和高分反对证据。

冲突不能被系统压平。出现冲突时，系统必须暴露冲突，并约束 AI 谨慎回答。

## 开发任务

```text
1. 创建 app/services/conflict_detector.py
2. 找出同一 claim 下 support 和 oppose evidence
3. 判断冲突严重程度
4. 生成 conflict summary
5. 更新 claim status 为 conflicting
6. 更新 answer_constraints
7. 写冲突检测测试
```

## 冲突等级

```text
minor_conflict:
  低分反对证据 vs 高分支持证据

major_conflict:
  高分支持证据 vs 高分反对证据

source_conflict:
  两个高可信来源直接矛盾
```

## 输出示例

```json
{
  "claim_id": "c2",
  "severity": "major",
  "summary": "一个官方来源显示该模型提供权重下载，但另一个高可信来源称权重未公开。"
}
```

## 建议目录结构

```text
app/services/
  conflict_detector.py

tests/services/
  test_conflict_detector.py
```

## 本阶段不做

```text
不解决冲突
不替用户判断绝对真相
只暴露冲突和约束回答
```

## 验收标准

```text
高分 support + 高分 oppose → conflicting
conflicts 数组中有 summary
answer_constraints 要求说明来源冲突
```

## 建议 Git 标签

```text
v0.1.11-conflict-detector
```

## 给 Codex / Claude Code 的指令

```text
实现 conflict_detector。检测同一 claim 下高分 support 与高分 oppose evidence 的冲突，生成 severity 和 summary，并让 claim_aggregator 将该 claim 标记为 conflicting。回答约束中必须要求说明来源冲突。补充测试。
```

---

# 十五、阶段 12：MCP 工具化，做成可装配模块

## 阶段目标

让 Claude、Cursor、Codex、自建 Agent 可以调用。

这一步相当于把零件做成标准接口件，不只是在你自己的机器上能用。

## 开发任务

```text
1. 定义 MCP tool name
2. 定义 MCP 参数 schema
3. 复用 TrustedSearchService
4. 返回标准 evidence package
5. 写 MCP 调用示例
6. 写 README 文档
```

## 工具名建议

```text
trusted_search
```

## 参数 schema

```json
{
  "query": "string",
  "question_type": "auto",
  "strictness": "balanced",
  "max_sources": 8,
  "require_primary_source": false,
  "return_raw_evidence": true
}
```

## 本阶段不做

```text
不另写一套逻辑
不让 MCP 和 REST API 分叉
不做前端
```

## 验收标准

```text
MCP 调用结果和 REST API 一致
Agent 能拿到结构化 evidence package
README 有调用示例
```

## 建议 Git 标签

```text
v0.1.12-mcp-tool
```

## 给 Codex / Claude Code 的指令

```text
为 Critical Search Layer 添加 MCP 工具封装，工具名 trusted_search。复用现有 TrustedSearchService，不要复制业务逻辑。工具参数与 REST API 保持一致，返回标准 evidence package JSON，并补充调用示例文档。
```

---

# 十六、全阶段 Git 标签建议

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

# 十七、每阶段共同施工规范

## 1. 每阶段必须有测试

```text
服务函数测试
接口测试
失败场景测试
```

不能只写代码不测。

## 2. 每阶段必须可回退

每完成一个阶段：

```text
git status
pytest
git add .
git commit
git tag
```

## 3. 外部依赖必须 mock

尤其是：

```text
搜索 API
网页抓取
LLM
```

否则测试不稳定。

## 4. 不要提前做数据库

MVP 可以先无状态。

数据库应该等到你需要以下能力时再加：

```text
缓存搜索结果
记录来源历史信誉
做用户历史查询
做证据图谱
```

## 5. 不要提前做前端

这个产品第一形态是：

```text
AI Agent 可调用工具 / 插件 / 中间件
```

所以 API 比前端重要。

## 6. 每个模块都要能单独替换

例如：

```text
Tavily 可以换 Brave
trafilatura 可以换 readability
规则拆解可以换 LLM 拆解
简单评分可以换复杂评分
REST 可以扩展 MCP
```

模块边界要干净。

## 7. 不允许无证据生成结论

核心底线：

```text
没有证据 → unsupported
低可信来源 → uncertain
来源冲突 → conflicting
证据不足 → 必须披露不确定性
```

---

# 十八、当前马上执行的第一条指令

现在不要继续扩展需求。  
第一刀只做项目基准面和 mock 接口。

直接给 Codex / Claude Code：

```text
根据 PRD，为 Critical Search Layer 创建 FastAPI 项目骨架。先完成 /health 接口、/api/v1/trusted-search mock 接口、Pydantic schemas 和基础 pytest 测试。不要接搜索 API、不要接 LLM、不要做数据库。保证项目能启动、测试能通过、接口返回符合 PRD 的结构化 JSON。
```

这一步就是铣基准面。

基准面没加工出来，后面所有“智能搜索”“证据评分”“冲突检测”都是空中楼阁。
