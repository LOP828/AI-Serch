# Provider Candidate Expansion Plan

版本：v0.2.4 minimal implementation draft  
文档类型：真实 provider 多 query 候选池扩展设计  
当前状态：已完成最小代码实现，不包含真实网络验证

---

# 1. 背景与当前状态

CSL 已完成 `v0.2.3-search-planner-official-source-strategy`。当前 `SearchPlanner` 在 `ai_model_info` 场景下已经能生成 official-source-biased queries，包括 exact entity、quoted exact entity、official、Hugging Face、GitHub、site-biased、paper/arXiv、license、model card 等 query family。

当前主链路仍保持原有执行方式：

```text
TrustedSearchService
  -> build_search_plan(...)
  -> SearchAdapter.search(request.query, max_results=request.max_sources)
  -> source_classifier
  -> page_fetcher
  -> evidence_extractor
  -> reliability_scorer
  -> claim_aggregator
  -> answer_constraint_builder
```

也就是说，`search_plan` 现在会生成并返回给 API 调用方，但还不驱动 `SearchAdapter` 多 query 执行。`SearchAdapter` 仍只执行原始 `request.query`。

Tavily real-world eval findings 显示：

- `eval_001` 中，`GPT-4.1 是否是 OpenAI 发布的模型？` 只返回 Zhihu / Reddit 等社区来源，缺少 OpenAI 官方来源。
- `eval_002` 中，`Llama 3.1 是否公开模型权重并允许商用？` 返回 CSDN / QbitAI 等弱二手来源，并出现 entity/version mismatch。
- `max_sources=2` 在真实 provider 下可能过早截断，导致官方来源还未进入候选池。
- `ReliabilityScorer`、`ClaimAggregator` 和 answer constraints 的谨慎行为是合理的，不应通过调高分数或放松聚合规则弥补 search quality 问题。

下一步应设计 provider candidate expansion：让真实 provider 可以使用 `search_plan` 中有限数量的高价值 queries 扩大候选池，再由 CSL 做去重、来源分类、过滤和截断。

本轮最小实现采用保守策略：

- `TrustedSearchService` 从现有 `search_plan` 中选择有限 query budget。
- `SearchAdapter` 增加兼容的 `search_many(...)` 方法，旧 `search(query, max_results)` 行为保持不变。
- `search_many(...)` 通过循环调用现有 `search(...)` 合并候选，复用 canonical URL 去重。
- 最终 `TrustedSearchResponse.sources` 仍按 `request.max_sources` 截断。
- 未修改 schema、TavilyProvider、source classifier、extractor、scorer、aggregator、config 或依赖。

---

# 2. 设计目标

目标：

- 让真实 provider 可以基于 `search_plan` 执行多条高价值 query。
- 先扩大候选池，再由 CSL 做 URL 去重、来源分类、候选排序和最终截断。
- 控制请求数量、成本、延迟、timeout 和 rate limit 风险。
- 保持默认 `CSL_SEARCH_PROVIDER=static` 行为稳定。
- 保持默认 `pytest` 不访问真实网络。
- 保持 Tavily 继续显式 opt-in。
- 继续让 provider 只负责返回 normalized search results，不承担 source classification、scoring、evidence extraction 或 answer constraints。
- 不改变 schema。若未来需要暴露 search debug/search errors，应作为单独 schema 设计。

核心目标不是让系统更自信，而是让更可靠的候选来源有机会进入 evidence pipeline。

---

# 3. 非目标

本阶段不做：

- 不接 Brave / SerpAPI。
- 不接真实 LLM。
- 不改 `ReliabilityScorer`。
- 不改 `ClaimAggregator`。
- 不改 `EvidenceExtractor` entity/version guard。
- 不让 `TavilyProvider` 做 source classification、source ranking、evidence extraction 或 scoring。
- 不把 Tavily 设为默认 provider。
- 不做数据库。
- 不做前端。
- 不改 MCP。
- 不改 response schema。
- 不让默认测试访问真实网络。

---

# 4. Provider Candidate Expansion 核心流程设计

未来候选扩展流程建议：

```text
TrustedSearchService
  -> classify question
  -> decompose claims
  -> SearchPlanner 生成 search_plan
  -> 从每个 claim 的 queries 中选择有限 query budget
  -> SearchAdapter 或新增 orchestration 层执行多条 query
  -> provider 返回候选 results
  -> canonical URL 去重
  -> 保留 provider candidate pool
  -> SourceClassifier 分类
  -> 按 source_type / preferred_source_types / query family / query order 排序
  -> 截断为 response max_sources
  -> page_fetcher / evidence_extractor / scorer / aggregator 保持原流程
```

关键边界：

- `SearchPlanner` 只负责生成 queries 和 `preferred_source_types`。
- `SearchAdapter` 或新增 search orchestration 层负责多 query 执行、candidate pool 合并和受控失败。
- `SourceClassifier` 继续负责 URL/domain 来源分类。
- `ReliabilityScorer` 继续只基于 evidence 和 source score 打分。
- `ClaimAggregator` 继续只基于 scored evidence 聚合状态。

候选扩展不应直接把 search result 标题、provider score 或 provider 摘要变成高置信结论。搜索结果仍只是原材料。

---

# 5. Query Budget 设计

不能按 `claims x all queries` 无限展开。`ai_model_info` 可能有 6 个 claims，每个 claim 又有多条 query。如果全部请求真实 provider，会快速放大成本和延迟。

建议把 query selection 设计为独立策略：

```text
input:
  search_plan
  strictness
  question_type
  max_sources

output:
  selected_queries with query_family metadata
```

## strict

目标：高精度、官方、一手、精确版本。

建议选择：

- quoted exact entity
- `site:huggingface.co`
- `site:github.com`
- official / official release
- arXiv / paper
- license, only when license or interpretation claim exists

已实现的第一版预算：

```text
strict: 最多 3 条 query
```

## balanced

目标：官方优先，同时保留合理召回。

建议选择：

- exact entity / quoted exact entity
- official
- Hugging Face
- GitHub
- paper 或 arXiv
- license 或 model card

已实现的第一版预算：

```text
balanced: 最多 5 条 query
```

## loose

目标：扩大召回，但仍有上限。

建议选择：

- balanced 的核心 official-source-biased queries
- release
- announcement
- technical report
- trusted technical media query, if later supported

已实现的第一版预算：

```text
loose: 最多 7 条 query
```

## Query selection 原则

- 先跨 claim 合并 query，再去重。
- 优先保留完整 entity/version query。
- 优先保留 site-biased、official、model card、repo、paper、license。
- 同一 family 不要选太多重复 query。
- 每次选择结果必须顺序稳定，便于 mock tests。

---

# 6. provider_max_candidates 与 response max_sources 分离

当前 `request.max_sources` 既限制 provider 返回，也限制最终 response sources。真实 provider 下这会过早截断候选池。

建议分离两个概念：

```text
provider_max_candidates:
  内部候选池目标大小，供 source filtering/ranking 使用。

response max_sources:
  用户请求的最终 sources 数量，继续由 TrustedSearchRequest.max_sources 控制。
```

示例：

```text
用户请求 max_sources=2
internal provider_max_candidates=6

SearchAdapter / orchestration:
  执行最多 5 条 balanced selected queries
  每条 query 请求 ceil(6 / selected_query_count) 个 results
  合并去重得到最多 6 个 candidates
  最终 response.sources 截断为 2
```

这样可以避免 `max_sources=2` 在 Tavily 原始返回阶段就过滤掉官方来源。

约束：

- `provider_max_candidates` 不应无限增长。
- 第一版实现为 `min(max(max_sources * 3, max_sources), 10)`。
- 默认 static provider 不需要 candidate expansion。
- 如果 schema 暂不扩展，`provider_max_candidates` 可以先作为内部配置或 adapter 层策略，不进入 API response。

---

# 7. 去重策略

候选合并必须稳定去重。

Canonical URL 规则建议复用或扩展现有 `normalize_url` 思路：

- scheme 小写。
- domain 小写。
- 去除 fragment。
- 去除 `utm_*` 参数。
- 去除常见 tracking 参数，例如 `fbclid`、`gclid`、`mc_cid`、`mc_eid`，具体列表后续实现时再定。
- path 尾部 slash 规范化。
- 保持非 tracking query 参数，避免误合并不同页面。

同一 canonical URL 多次出现时：

- 保留更高优 query family 命中的结果。
- 若 query family 权重相同，保留先出现的结果。
- 可合并内部 debug metadata，例如 matched queries，但默认不进入 schema。

顺序稳定原则：

- selected query order 稳定。
- provider result order 稳定。
- 去重时 first useful candidate wins。
- filtering/ranking 的 tie-breaker 使用原始 candidate order。

---

# 8. 排序 / Filtering 策略

候选排序应保持简单、可解释，不引入复杂 reranker。

建议排序信号：

1. `preferred_source_types` 命中。
2. source type 优先级。
3. query family 优先级。
4. query order。
5. provider result order。

## Source type 优先级

高优先：

- `official_model_card`
- `source_code_repo`
- `academic_paper`
- `official_docs`
- `official_blog`

中等优先：

- `product_page`
- `mainstream_media`
- `expert_blog`

低优先：

- `community_forum`
- `unknown`
- `seo_content`

## Query family 优先级

建议顺序：

```text
site-biased exact
quoted exact official
official / official release
model card
Hugging Face / ModelScope
GitHub / GitLab
paper / arXiv / OpenReview
license
broad release / announcement / technical report
```

注意：

- 不应只因为某来源来自 broad query 就丢弃；它可以作为补充候选。
- 不应让 community/forum 因数量多而压过少量官方来源。
- 不在本阶段引入 ML reranker 或 LLM reranker。

---

# 9. Fallback / Failure 策略

多 query 执行必须容忍局部失败。

原则：

- 单条 query timeout 不应让整个 trusted-search 崩溃。
- 单条 query provider error 应记录为内部受控错误。
- 如果部分 query 成功，继续使用成功 candidates。
- 如果全部 query 失败，按现有 fallback/error 策略返回空 results 或 fallback results。
- fallback 结果不能伪装成真实 search provider 结果。
- 默认 static provider 不应受影响。

错误类型继续使用现有 provider error boundary：

- `provider_timeout`
- `provider_auth_failed`
- `provider_rate_limited`
- `provider_quota_exceeded`
- `provider_bad_response`
- `provider_unavailable`

处理建议：

- `provider_auth_failed`：通常停止后续 real provider queries，避免重复无效请求。
- `provider_quota_exceeded`：停止后续 real provider queries，可返回已有成功 candidates 或 fallback。
- `provider_rate_limited`：停止或降级剩余 queries，避免放大 rate limit。
- `provider_timeout` / `provider_unavailable`：允许其他 selected queries 继续。
- `provider_bad_response`：丢弃该 query 的坏结果，继续处理其他 query。

如果未来需要向 API 调用方暴露 search errors，应单独设计 debug field，不在本阶段修改 schema。

---

# 10. 测试策略

本轮已实现第一批 fake/static 测试；后续仍应继续避免真实网络依赖。

已覆盖的测试：

- `SearchAdapter.search(...)` 旧行为兼容。
- `SearchAdapter.search_many(...)` 多 query 去重和顺序稳定。
- 单条 query failure 不影响其它 query 成功结果。
- 全部 query failure 返回受控 error。
- 默认 static/mock 路径不访问真实网络。
- strict / balanced / loose query budget。
- `provider_max_candidates` 大于 response `max_sources`。
- response sources 仍按 `request.max_sources` 截断。
- search plan 为空时 fallback 到原始 request query。

后续测试建议：

## SearchPlanner query selection tests

- strict / balanced / loose query selection budget。
- high-value query family 优先级。
- quoted exact entity/version 保留。
- selected queries 去重和顺序稳定。

## SearchAdapter multi-query fake provider tests

- fake provider 收到 selected queries，且不会访问网络。
- provider 每条 query 返回固定 results。
- candidate pool 合并后按 canonical URL 去重。
- response sources 仍尊重 `max_sources`。
- provider over-returning 仍被内部候选上限截断。

## URL 去重和顺序稳定 tests

- fragment 去重。
- `utm_*` 去重。
- tracking 参数去重。
- 相同 URL 多 query 命中时保留更高优 query family。
- tie-breaker 顺序稳定。

## Query budget tests

- claims x all queries 不会全部展开。
- strict query 数量最少。
- balanced 选择 4-6 条高价值 query。
- loose 允许 broader query，但仍有上限。

## Provider partial failure tests

- 单条 query timeout，其他 query 成功。
- rate limit / quota 后停止后续 query。
- 全部 query 失败时返回受控空结果或 fallback。
- 不泄露 API key、Authorization header 或 raw provider payload。

## Route / integration tests

- 默认 `pytest` 不访问真实网络。
- integration test 继续 opt-in skip。
- Tavily route integration 只验证结构、错误边界和 secret 不泄露，不断言具体外部来源。

当前仓库没有 `tests/api/test_trusted_search*.py` 匹配文件；trusted-search route/service/e2e 测试当前分布在：

- `tests/test_trusted_search_mock.py`
- `tests/services/test_trusted_search_service.py`
- `tests/e2e/test_trusted_search_flow.py`
- `tests/integration/test_trusted_search_tavily_integration.py`

---

# 11. 本轮已修改和未来可能修改文件

本轮最小实现已修改：

- `app/services/trusted_search_service.py`
- `app/services/search_adapter.py`
- `tests/services/test_search_adapter.py`
- `tests/services/test_trusted_search_service.py`
- `docs/provider_candidate_expansion_plan.md`

后续增强可能继续涉及：

- `app/services/search_planner.py`
- `tests/integration/test_trusted_search_tavily_integration.py`

可能需要新增 helper，但应保持边界清晰：

- query selection helper
- candidate pool item structure
- candidate ranking helper
- multi-query adapter helper

后续增强仍应避免修改 schema、TavilyProvider、source classifier、extractor、scorer、aggregator、config、MCP 和依赖，除非单独立项。

---

# 12. 风险与约束

## 成本和延迟

query 数量放大会增加 provider 调用次数、延迟、timeout 概率、rate limit 和 quota 消耗。必须用 query budget 控制。

## 真实 provider 不稳定

Tavily 或其他真实 provider 结果会随时间变化。测试不能断言具体外部来源、标题或排序。真实 integration test 只能验证结构、边界和安全性。

## 不做多 provider 聚合

provider candidate expansion 不是多 provider 聚合。第一版仍只围绕当前 opt-in provider，避免引入跨 provider 去重、成本分配和错误归因复杂度。

## 不用 scoring 修补 search quality

不要通过调高 scorer 或放松 aggregator 让弱来源显得可靠。候选扩展的目的，是让更好的官方来源进入 pipeline。

## 低质量来源数量不能转成高置信

多个 community/forum、unknown 或 SEO 来源不应因为数量多而形成高 confidence。最终 claim status 仍必须由 evidence quality 和 source reliability 约束。

## Schema 稳定

候选扩展的内部 metadata 不应直接塞进 `SearchResultSchema` 或 `SourceSchema`。如需暴露 debug，应单独设计 schema 变更。

---

# 13. 验收标准

文档层面验收标准：

- 明确 provider candidate expansion 的候选池流程。
- 明确 strict / balanced / loose 的 query budget。
- 明确 `provider_max_candidates` 与 response `max_sources` 分离。
- 明确 canonical URL 去重、排序、filtering 和 failure handling。
- 明确默认 static provider、默认 pytest、Tavily opt-in 安全边界不变。
- 明确不接 Brave / SerpAPI、不接真实 LLM、不改 scorer / aggregator / extractor / schema。
- 明确下一阶段代码改动范围。

下一阶段如果进入实现，应先写 fake-provider tests，再改 orchestration/adapter。不要先跑真实 Tavily 验证。
