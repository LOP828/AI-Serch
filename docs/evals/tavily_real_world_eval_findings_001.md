# Tavily Real-world Eval Findings 001

版本：v0.2.3 findings  
文档类型：Tavily real-world eval 第一批质量问题汇总  
范围：基于 `eval_001` 和 `eval_002` 的脱敏人工记录

---

# 1. 背景

Tavily 已经能通过显式 opt-in 进入 `/api/v1/trusted-search` 主链路。默认 provider 仍为 `static`，默认 `pytest` 不访问真实网络，API key 只能通过临时环境变量传入。

当前评估不是为了证明 Tavily 能联网，而是为了观察真实搜索结果进入 CSL 后，最终 evidence package 的质量是否可靠。本轮只基于前两个真实样本，不急着改算法。

本轮目标是找出第一刀应该修：

- `SearchPlanner`
- `source_classifier`
- `page_fetcher`
- `evidence_extractor`
- `reliability_scorer`
- `claim_aggregator`
- `answer_constraints`

初步结论是：第一瓶颈在 `SearchPlanner` 的官方来源优先查询，其次是 evidence relevance 的实体/版本保护。

---

# 2. Eval 样本概览

| eval_id | query | overall_status | overall_confidence | sources_count | main issue |
|---|---|---|---:|---:|---|
| eval_001 | GPT-4.1 是否是 OpenAI 发布的模型？ | uncertain | 0.0547 | 2 | missing official OpenAI source; only Zhihu / Reddit community sources returned |
| eval_002 | Llama 3.1 是否公开模型权重并允许商用？ | uncertain |  | 2 | entity/version mismatch; sources discussed older LLaMA or unrelated models, not Llama 3.1 official sources |

---

# 3. 共同发现

- Tavily 能进入 trusted-search 主链路，API route opt-in wiring 有效。
- 默认 static 安全模式没有被破坏。
- 两个样本都没有召回足够好的官方 / 一手来源。
- `SearchPlanner` 对 `ai_model_info` 缺少 official-source-biased query。
- `max_sources=2` 在真实 provider 下可能过早截断。
- `evidence_extractor` 对实体和版本不够敏感。
- `reliability_scorer` 没有明显过度信任弱来源。
- `claim_aggregator` 保持 cautious / uncertain，表现合理。
- `answer_constraints` 能限制过度确定表达，表现合理。

当前后半段 pipeline 的谨慎行为是产品能力，不是主要缺陷。第一优先级不是让系统更自信，而是让系统找到更好的官方证据，并过滤错位证据。

---

# 4. Eval 001 详细结论

Query:

```text
GPT-4.1 是否是 OpenAI 发布的模型？
```

Observed result:

- only Zhihu and Reddit were returned
- both were classified as `community_forum`
- c1 had one supporting evidence with `final_score = 0.328`
- `overall_status` remained `uncertain`
- `allowed_tone` was `cautious`

Human judgment:

- `source_classifier` was correct
- scorer was reasonable because it did not overtrust community sources
- aggregator and answer constraints were reasonable
- main failure was search quality: official OpenAI source was missing

Root cause:

- query/search planning did not prioritize official OpenAI source
- official-source-biased search terms were missing
- `max_sources=2` may have truncated better sources

---

# 5. Eval 002 详细结论

Query:

```text
Llama 3.1 是否公开模型权重并允许商用？
```

Observed result:

- sources were CSDN and QbitAI
- both were weak secondary sources
- evidence mixed older LLaMA / unrelated model information into a Llama 3.1 query
- several evidence items had relatively high `relevance_score` despite entity/version mismatch
- overall stayed `uncertain` and `cautious`

Human judgment:

- search quality was poor
- evidence quality was poor
- source classification did not falsely mark sources as official
- scoring stayed low because source base reliability was low
- answer constraints were reasonable
- main failure was entity/version mismatch and lack of official Meta / llama.com / Hugging Face sources

Root cause:

- `SearchPlanner` lacks exact-version official queries
- evidence extraction lacks entity/version guard
- `max_sources=2` may have truncated official sources
- `relevance_score` is too high for mismatched evidence

---

# 6. Failure Categories

## P1 - SearchPlanner official-source-biased query missing

`ai_model_info` 问题应优先生成官方来源查询，例如：

- `{model} official`
- `{model} official blog`
- `{model} model card`
- `{model} Hugging Face`
- `{model} license`
- `site:openai.com {model}`
- `site:ai.meta.com {model}`
- `site:llama.com {model}`
- `site:huggingface.co {model}`

当前两个样本都说明：只把原始 query 交给真实 provider，容易返回社区、媒体或二手中文内容，而不是官方发布页、模型卡或许可证页面。

## P1 - Entity/version guard missing before evidence scoring

对于 Llama 3.1 这类问题，证据必须明确命中目标实体和版本。

只提到 LLaMA、LLaMA-13B、旧 LLaMA、其他模型的证据，不能给高 `relevance_score`。后续应设计 entity/version matching 或 evidence relevance penalty，使错位证据在进入 scoring 前就被降权或剔除。

## P2 - max_sources too small for real provider

mock 阶段 `max_sources=2` 可控，但真实 provider 可能需要先拉取更多候选，再做 source ranking / filtering。

后续可以尝试：

```text
provider candidates = 5-10
source classification / filtering / ranking
response max_sources = user requested max_sources
```

即把 provider 候选数量和最终 response 来源数量分离。

## P2 - Source type coverage for Chinese tech media / blogs

CSDN、QbitAI 当前为 `unknown`。虽然没有误判成官方，但未来可以考虑分类为：

- `expert_blog`
- `mainstream_media`
- `tech_media`
- `community_blog`

这不是第一优先级。比起细化媒体类型，先找对官方来源更重要。

## P2 - Page fetch quality needs more observation

前两个样本不足以判断 `page_fetcher` 是主要瓶颈。需要后续 `eval_003`、`eval_004`、`eval_005` 继续观察 fetch success、fallback snippet、empty text 和 noisy text 的比例。

---

# 7. What Should NOT Be Fixed First

当前不应该优先做：

- 不要先调高 scorer。
- 不要因为 output `uncertain` 就认为 aggregator 错。
- 不要先接 Brave / SerpAPI。
- 不要先让 Tavily 成为默认 provider。
- 不要先做数据库。
- 不要先做前端。
- 不要因为两个样本就大改全部模块。

说明：

当前后半段 cautious 行为是合理的。第一优先级不是让系统更自信，而是让系统找到更好的官方证据，并过滤错位证据。若直接调高 scoring 或放宽 aggregation，只会把弱来源和错位证据包装成更自信的错误。

---

# 8. Recommended Next Fixes

## Step 1

设计 `ai_model_info` 的 official-source-biased `SearchPlanner` 改进方案文档。

目标：让模型信息问题优先搜索官方博客、官方文档、模型卡、Hugging Face、license 页面和组织域名。

## Step 2

设计 entity/version guard 方案文档，用于 `EvidenceExtractor` 前或 `EvidenceExtractor` 内部 relevance 判断。

目标：避免旧模型、相邻模型、同系列但不同版本的证据获得高 relevance。

## Step 3

设计 real provider 候选扩展策略，例如 `provider_max_candidates` 和 response `max_sources` 分离。

目标：真实 provider 先返回更多候选，再由 CSL 根据 source type、domain 和 relevance 做筛选。

## Step 4

再跑 `eval_003`、`eval_004`、`eval_005`，看这些问题是否复现，并观察 tech news、product_info、policy_legal 是否出现同类官方来源缺失或 entity/version mismatch。

---

# 9. Proposed Next Documents

建议下一阶段文档：

- `docs/search_planner_official_source_strategy.md`
- `docs/evidence_entity_version_guard_plan.md`
- `docs/real_provider_candidate_expansion_plan.md`

下一步建议优先写：

```text
docs/search_planner_official_source_strategy.md
```

原因：两个已完成样本都首先失败在官方来源召回，而不是 scoring、aggregation 或 answer constraints。应先把 SearchPlanner 的官方来源查询策略设计清楚，再进入代码改动。

---

# 10. Current Decision

Based on `eval_001` and `eval_002`, the first fix should target `SearchPlanner` official-source-biased query generation, followed by entity/version guard for evidence relevance. Scoring, aggregation, and answer constraints are not the first bottleneck.

---

# 11. 禁止事项

- 不要记录 API key。
- 不要记录 Authorization header。
- 不要提交 raw provider payload。
- 不要发真实网络请求。
- 不要改生产代码。
- 不要改测试代码。
- 不要新增依赖。
- 不要修改 `pyproject.toml`。
- 不要修改 `env.example`。
- 不要修改 README。
- 不要修改 MCP。
- 不要修改 `TrustedSearchService`。
- 不要修改 `SearchAdapter`。
- 不要修改 `SearchResultSchema` / `SourceSchema`。
- 不要移动 v0.2.0 / v0.2.1 / v0.2.2 标签。
- 不要补 v0.1.7 tag。
- 不要重写 Git 历史。
