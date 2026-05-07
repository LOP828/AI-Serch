# Critical Search Layer Test Cases

版本：v0.1  
文档类型：测试用例 / 验收清单  
适用对象：Codex、Claude Code、开发者本人

---

# 1. 测试原则

本项目测试的目标不是追求覆盖率数字，而是保证可信搜索流程不会跑偏。

核心原则：

```text
每个阶段都有测试
外部依赖必须 mock
失败场景必须可控
没有证据不能编造
不确定不能被包装成确定
```

---

# 2. 阶段 0：项目骨架测试

## 2.1 Health 接口正常

### 输入

```http
GET /health
```

### 期望

```json
{
  "status": "ok"
}
```

### 验收

```text
HTTP 200
status = ok
```

---

## 2.2 应用可以启动

### 操作

```bash
uv run uvicorn app.main:app --reload
```

### 验收

```text
服务正常启动
没有 import error
没有配置错误
```

---

# 3. 阶段 1：Schema 和 mock 接口测试

## 3.1 trusted-search 接收合法 query

### 输入

```http
POST /api/v1/trusted-search
```

```json
{
  "query": "MiroThinker 1.7 是不是开源模型？"
}
```

### 期望

```text
HTTP 200
返回结构化 JSON
```

### 必须包含字段

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

---

## 3.2 trusted-search 返回 mock claim

### 验收

```text
claims 是数组
至少包含 1 个 claim
claim 包含 claim_id、claim_text、status、confidence、evidence
```

---

## 3.3 trusted-search 返回 mock source

### 验收

```text
sources 是数组
至少包含 1 个 source
source 包含 source_id、title、url、source_type、base_reliability、is_primary_source
```

---

## 3.4 trusted-search 返回 evidence

### 验收

```text
evidence 包含 evidence_text、support_type、relevance_score、final_score
support_type 必须是 support / oppose / partial / neutral 之一
final_score 范围是 0.0 - 1.0
```

---

## 3.5 空 query 返回错误

### 输入

```json
{
  "query": ""
}
```

### 期望

```text
HTTP 422
不能返回正常 evidence package
```

---

# 4. 阶段 2：问题分类测试

## 4.1 AI 模型信息识别

### 输入

```text
MiroThinker 1.7 是不是开源模型？
```

### 期望

```text
question_type = ai_model_info
risk_level = medium
```

---

## 4.2 科技新闻识别

### 输入

```text
OpenAI 下周会发布某个代号模型吗？
```

### 期望

```text
question_type = tech_news
```

---

## 4.3 产品参数识别

### 输入

```text
某款笔记本的 RTX 5070 Ti 是不是 12GB 显存？
```

### 期望

```text
question_type = product_info
```

---

## 4.4 政策法规识别

### 输入

```text
某项政策现在是否还有效？
```

### 期望

```text
question_type = policy_legal
risk_level = high
```

---

## 4.5 技术文档识别

### 输入

```text
FastAPI 的 Depends 怎么使用？
```

### 期望

```text
question_type = technical_doc
```

---

## 4.6 无法识别时返回 unknown

### 输入

```text
这个东西到底怎么样？
```

### 期望

```text
question_type = unknown
```

---

# 5. 阶段 2：命题拆解测试

## 5.1 AI 模型开源性问题拆解

### 输入

```text
MiroThinker 1.7 是不是开源模型？
```

### 期望 claims

```text
MiroThinker 1.7 是否存在公开发布页面
MiroThinker 1.7 是否公开模型权重
MiroThinker 1.7 是否公开训练代码
MiroThinker 1.7 是否公开训练数据
MiroThinker 1.7 的许可证是否允许商用
MiroThinker 1.7 是否能严格称为开源模型
```

### 验收

```text
至少 5 个 claim
每个 claim 有 claim_id
每个 claim 有 claim_text
每个 claim 有 claim_type
不能生成“它是不是很厉害”这类无法验证命题
```

---

# 6. 阶段 3：搜索计划测试

## 6.1 AI 模型 claim 生成搜索词

### 输入 claim

```text
MiroThinker 1.7 是否公开模型权重
```

### 期望 queries 包含

```text
MiroThinker 1.7 Hugging Face
MiroThinker 1.7 GitHub
MiroThinker 1.7 license
MiroThinker 1.7 official
```

---

## 6.2 每个 claim 至少有一个 query

### 验收

```text
search_plan 中每个 claim_id 都有 queries
queries 长度 >= 1
```

---

# 7. 阶段 3：搜索适配器测试

## 7.1 搜索结果格式统一

### Mock 返回

```json
[
  {
    "title": "MiroThinker-1.7 - Hugging Face",
    "url": "https://huggingface.co/example/mirothinker-1.7",
    "snippet": "Model card...",
    "published_at": null
  }
]
```

### 验收

```text
每条结果有 title、url、snippet、published_at
```

---

## 7.2 URL 去重

### 输入

```text
https://example.com/a?utm_source=x
https://example.com/a
https://example.com/a#section
```

### 期望

```text
只保留一个 canonical URL
```

---

## 7.3 搜索失败可控

### 模拟

```text
搜索 API timeout
```

### 期望

```text
不抛出未处理异常
返回空 results 或 controlled error
trusted-search 流程不中断
```

---

# 8. 阶段 4：来源分类测试

## 8.1 Hugging Face

### 输入

```text
https://huggingface.co/example/model
```

### 期望

```text
source_type = official_model_card
is_primary_source = true
base_reliability = 0.88
```

---

## 8.2 GitHub

### 输入

```text
https://github.com/example/repo
```

### 期望

```text
source_type = source_code_repo
is_primary_source = true
```

---

## 8.3 arXiv

### 输入

```text
https://arxiv.org/abs/2501.12345
```

### 期望

```text
source_type = academic_paper
```

---

## 8.4 gov 域名

### 输入

```text
https://www.sec.gov/example
```

### 期望

```text
source_type = financial_filing
```

---

## 8.5 社区来源

### 输入

```text
https://www.reddit.com/r/example/comments/xxx
```

### 期望

```text
source_type = community_forum
base_reliability = 0.40
```

---

## 8.6 未知来源

### 输入

```text
https://unknown-example-site.com/article
```

### 期望

```text
source_type = unknown
base_reliability = 0.30
```

---

# 9. 阶段 5：网页抓取测试

## 9.1 普通网页提取成功

### 模拟

```text
httpx 返回 HTML
trafilatura 成功提取正文
```

### 期望

```text
fetch_status = success
text 非空
```

---

## 9.2 抓取失败 fallback snippet

### 模拟

```text
httpx timeout
```

### 输入 snippet

```text
This is a search snippet.
```

### 期望

```text
fetch_status = fallback
text = snippet
```

---

## 9.3 正文长度限制

### 模拟

```text
正文长度超过 MAX_DOCUMENT_CHARS
```

### 期望

```text
text 被截断
不会返回超长正文
```

---

# 10. 阶段 6：证据抽取测试

## 10.1 support 证据

### Claim

```text
MiroThinker 1.7 公开了模型权重
```

### Document

```text
The model weights are available for download in safetensors format.
```

### 期望

```text
support_type = support
relevance_score > 0.7
```

---

## 10.2 partial 证据

### Claim

```text
MiroThinker 1.7 可以严格称为开源模型
```

### Document

```text
The model weights are publicly available, but training data is not disclosed.
```

### 期望

```text
support_type = partial
```

---

## 10.3 oppose 证据

### Claim

```text
MiroThinker 1.7 公开了模型权重
```

### Document

```text
The model weights are not publicly released.
```

### 期望

```text
support_type = oppose
```

---

## 10.4 无证据不编造

### Claim

```text
MiroThinker 1.7 公开了训练数据
```

### Document

```text
This page only discusses benchmark results.
```

### 期望

```text
evidence = []
```

---

# 11. 阶段 7：可信度评分测试

## 11.1 官方模型卡高分

### 输入

```text
relevance_score = 0.90
source_base_score = 0.88
primary_source_factor = 1.10
recency_factor = 1.00
```

### 期望

```text
final_score ≈ 0.87
score_breakdown 存在
```

---

## 11.2 社区来源低分

### 输入

```text
relevance_score = 0.90
source_base_score = 0.40
primary_source_factor = 1.00
recency_factor = 1.00
```

### 期望

```text
final_score ≈ 0.36
```

---

## 11.3 低相关性不能高分

### 输入

```text
relevance_score = 0.20
source_base_score = 0.95
primary_source_factor = 1.10
recency_factor = 1.00
```

### 期望

```text
final_score 不应超过 0.25
```

---

# 12. 阶段 8：命题聚合测试

## 12.1 confirmed

### 条件

```text
最高 support final_score >= 0.80
无高分 oppose
```

### 期望

```text
status = confirmed
```

---

## 12.2 likely

### 条件

```text
最高 support final_score >= 0.65
但不足 0.80
```

### 期望

```text
status = likely
```

---

## 12.3 unsupported

### 条件

```text
无 support
无 partial
```

### 期望

```text
status = unsupported
```

---

## 12.4 conflicting

### 条件

```text
最高 support final_score >= 0.75
最高 oppose final_score >= 0.75
```

### 期望

```text
status = conflicting
```

---

# 13. 阶段 9：回答约束测试

## 13.1 uncertain 必须谨慎

### 条件

```text
至少一个核心 claim = uncertain
```

### 期望

```text
can_answer_confidently = false
must_disclose_uncertainty = true
allowed_tone = cautious
```

---

## 13.2 unsupported 禁止肯定表达

### 条件

```text
至少一个核心 claim = unsupported
```

### 期望 forbidden_phrases 包含

```text
已经确认
毫无疑问
官方确认
```

---

## 13.3 conflicting 必须说明冲突

### 条件

```text
至少一个 claim = conflicting
```

### 期望

```text
must_disclose_uncertainty = true
required_phrases 包含“来源冲突”或类似表达
```

---

## 13.4 全 confirmed 才能自信回答

### 条件

```text
所有核心 claim = confirmed
```

### 期望

```text
can_answer_confidently = true
allowed_tone = confident
```

---

# 14. 阶段 10：端到端测试

## 14.1 AI 模型开源性核查

### 输入

```text
MiroThinker 1.7 是不是开源模型？
```

### Mock 来源

```text
Hugging Face 模型卡
GitHub 仓库
license 文档
```

### 期望

```text
question_type = ai_model_info
claims 包含模型存在、权重、代码、训练数据、许可证、是否严格开源
sources 包含 official_model_card
answer_constraints 要求谨慎表达
```

---

## 14.2 科技爆料核查

### 输入

```text
OpenAI 下周会发布某个代号模型吗？
```

### Mock 来源

```text
社区帖子
无官方博客
无主流媒体确认
```

### 期望

```text
question_type = tech_news
overall_status = uncertain 或 unsupported
answer_constraints 禁止“官方确认”
```

---

## 14.3 产品参数核查

### 输入

```text
某款笔记本 RTX 5070 Ti 是不是 12GB 显存？
```

### Mock 来源

```text
厂商官网参数页
电商参数页
测评文章
```

### 期望

```text
question_type = product_info
优先使用 product_page / official_docs
参数冲突时标记 conflicting
```

---

## 14.4 政策有效性核查

### 输入

```text
某项政策现在还有效吗？
```

### Mock 来源

```text
政府官网
媒体解读
社区讨论
```

### 期望

```text
question_type = policy_legal
政府来源权重最高
没有官方来源时不能 confirmed
```

---

# 15. 回归测试清单

每次提交前必须运行：

```bash
uv run pytest
```

建议同时运行：

```bash
uv run ruff check .
uv run ruff format --check .
```

---

# 16. v0.1 mock MVP 验收

当前 v0.1 mock MVP 验收：

```text
GET /health 正常
POST /api/v1/trusted-search 正常
trusted-search 返回完整 evidence package
response 包含 claims、search_plan、sources、page_fetches、evidence、conflicts、answer_constraints
evidence 包含 final_score 和 score_breakdown
claims 已聚合 status/confidence/reason
answer_constraints 由 claim status 生成，不是固定 mock
MCP trusted_search wrapper 可调用 TrustedSearchService
query 为空时返回 422
pytest 通过
```

当前仍不验收：

```text
搜索准确率
真实网页覆盖率
真实 LLM 抽取质量
真实搜索 provider 可用性
数据库持久化
前端展示
```
