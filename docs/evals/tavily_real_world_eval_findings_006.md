# Tavily Real-world Eval Findings 006

版本：v0.2.8 findings  
文档类型：Tavily real-world eval 第六轮质量问题汇总  
范围：基于 `docs/evals/tavily_real_world_eval_run_006.md` 的脱敏记录

---

# 1. 记录边界

本文件只根据 `docs/evals/tavily_real_world_eval_run_006.md` 总结，不包含 API key、Authorization header、raw provider payload 或完整网页正文，也不补造 run_006 中没有的数据。

本轮目标是判断 v0.2.8 product memory spec evidence matching 是否解决 eval_004 的 false conflict，并形成下一轮开发依据。

---

# 2. 核心结论

v0.2.8 第一刀有效。

eval_004 从 run_005 到 run_006 出现结构性改善：

| metric | run_005 | run_006 |
|---|---:|---:|
| overall_status | conflicting | mostly_confirmed |
| conflicts_count | 1 | 0 |
| evidence_count | 2 | 2 |
| support evidence count | 1 | 2 |
| oppose evidence count | 1 | 0 |

Run 006 中两条 evidence 都是 `support`：

- `RTX 5070 Ti 16G` excerpt 被判为 `support`。
- `RTX 5070 Ti 16GB` excerpt 被判为 `support`。

结论：

- `16G` 与 `16GB` 在显存语境下已被正确视为等价表达。
- eval_004 的 false conflict 已消失。
- 根因确实是 `evidence_extractor` 对 product memory spec support/oppose 的方向判定问题。
- 这不是 scorer 问题。
- 这不是 aggregator 问题。
- 这不是 source ranking 问题。

下一步不应调高 scorer、不应放宽 aggregator，也不应继续扩大 source ranking。

---

# 3. Eval 级状态

## eval_001: GPT-4.1 / OpenAI

Observed:

- `overall_status=confirmed`
- `overall_confidence=0.9405`
- `claims_count=3`
- `evidence_count=6`
- `conflicts_count=0`
- final sources: `openai.com` and `platform.openai.com`, both `official_docs`

Finding:

v0.2.7 的 AI model release/origin claim decomposition 行为保持稳定。

## eval_002: Llama 3.1

Observed:

- `overall_status=partially_confirmed`
- `overall_confidence=0.5163`
- `claims_count=6`
- `evidence_count=5`
- `conflicts_count=0`

Finding:

Open-source / weights / commercial-use decomposition 行为保持，不受 v0.2.8 product memory spec change 影响。

## eval_003: OpenAI voice model

Observed:

- `overall_status=confirmed`
- `overall_confidence=0.9196`
- `claims_count=1`
- `evidence_count=2`
- `conflicts_count=0`
- final sources: `openai.com` official docs

Finding:

OpenAI official docs result 保持。没有看到 source recall 或 classification 回退。

## eval_004: RTX 5070 Ti memory spec

Observed:

- `overall_status=mostly_confirmed`
- `overall_confidence=0.7216`
- `claims_count=1`
- `evidence_count=2`
- `conflicts_count=0`
- final sources: `nvidia.com / product_page`
- page fetch status: `fallback=2`

Claim:

| claim_id | claim_text | claim_type | status | confidence | evidence_count |
|---|---|---|---|---:|---:|
| c1 | RTX 5070 Ti 是否是 16GB 显存？ 这一问题可以被外部来源验证 | general_fact | likely | 0.7216 | 2 |

Evidence:

| evidence_id | source_id | support_type | final_score | key observation |
|---|---|---|---:|---|
| ev-c1-s1-1 | s1 | support | 0.7216 | excerpt contains `RTX 5070 Ti 16G` |
| ev-c1-s2-1 | s2 | support | 0.7216 | excerpt contains `RTX 5070 Ti 16GB` |

Finding:

This is the key validation sample for v0.2.8.

The run_005 false `oppose` on the `RTX 5070 Ti 16G` evidence is gone. Both `16G` and `16GB` are now treated as equivalent expressions for the 16GB VRAM claim, so the sample no longer creates a conflict.

Remaining issue:

eval_004 is still `mostly_confirmed`, not `confirmed`. Based on run_006, the likely reason is evidence-source quality:

- both final sources are NVIDIA GeForce Forums pages;
- both page fetches are `fallback`;
- the source domain is `nvidia.com`, but the page content is forum / user-spec content rather than a stable NVIDIA official specification page.

This should not be interpreted as scorer, aggregator, or ranking failure.

## eval_005: SEC Bitcoin ETF/ETP

Observed:

- `overall_status=confirmed`
- `overall_confidence=0.9405`
- `claims_count=1`
- `evidence_count=2`
- `conflicts_count=0`
- final sources: `sec.gov` government docs

Finding:

SEC official-source behavior remains stable. No source recall or classification regression is visible in run_006.

---

# 4. Analysis Dimensions

## Evidence extraction

Solved:

- product memory spec support/oppose direction improved for eval_004.
- same model + equivalent value now supports the claim.
- `16G` and `16GB` are treated as equivalent in the VRAM context.

Remaining:

- evidence quality still depends on what text is available from fallback snippets.
- NVIDIA forum snippets can support a claim, but they are weaker than official specification pages.

## Conflict detection

Solved by upstream evidence direction:

- run_005 conflict disappeared once the false `oppose` became `support`.
- no evidence in run_006 suggests conflict_detector itself needs to be changed first.

Do not change conflict detection based on run_006.

## Scorer

Not the issue.

Run_006 has no conflict and still returns `mostly_confirmed`. That is consistent with evidence coming from fallback forum snippets rather than stronger official spec pages. Do not tune scorer upward to force `confirmed`.

## Aggregator

Not the issue.

The aggregator now receives support-only evidence and produces `mostly_confirmed`. That is acceptable for the observed source quality. Do not loosen aggregator thresholds.

## Source ranking

Not the current priority.

`nvidia.com` sources are already in final sources. The remaining issue is not that official-domain results cannot enter final sources; it is that the official-domain pages are forum snippets rather than stable product specification pages.

## Source subtype / product official spec recall

Potential next area:

- Distinguish official-domain forum / support community pages from official product specification pages.
- Improve product_info official spec page recall so a product spec page can compete with forum snippets.

This should be scoped as a future product_info source-quality task, not a scorer / aggregator task.

## Product claim semantics

Potential next area:

The current eval_004 claim remains `general_fact`:

```text
RTX 5070 Ti 是否是 16GB 显存？ 这一问题可以被外部来源验证
```

For product specs, a better internal claim boundary would explicitly bind:

- model: `RTX 5070 Ti`
- attribute: `VRAM / memory size / 显存`
- value: `16GB`

This can make future evidence matching and conflict handling clearer without changing schema.

---

# 5. What Not To Do

- Do not connect Brave / SerpAPI.
- Do not modify TavilyProvider.
- Do not tune scorer upward.
- Do not loosen aggregator.
- Do not continue expanding source ranking unless later evals show source ranking regression.
- Do not introduce an LLM reranker.
- Do not treat NVIDIA forum snippets as equivalent to stable official specification pages.

---

# 6. Recommended Next Tasks

## Task 1: Evaluate product_info official specification page recall

Why now:

eval_004 no longer has a false conflict, but it remains `mostly_confirmed`. The remaining gap appears to be that final evidence comes from NVIDIA GeForce Forums / fallback snippets rather than a stable NVIDIA official specification page.

Likely files to inspect later:

- `app/services/search_planner.py`
- `tests/services/test_search_planner.py`
- `app/services/trusted_search_service.py`
- `tests/services/test_trusted_search_service.py`

Tests to add later:

- RTX product_info queries should include official specification style searches.
- NVIDIA official product/spec pages should be able to enter candidates ahead of forum snippets when available.
- Existing `max_sources` truncation behavior must remain unchanged.

Explicit non-goals:

- Do not connect Brave / SerpAPI.
- Do not modify TavilyProvider.
- Do not broaden ranking without a targeted product_info spec recall test.

## Task 2: Refine source classification for official-domain forum/support community pages

Why now:

Run_006 shows both final sources are `nvidia.com` and classified as `product_page`, but their titles indicate NVIDIA GeForce Forums. The domain is official, but the page subtype is not the same as an official product specification page.

Likely files to inspect later:

- `app/services/source_classifier.py`
- `tests/services/test_source_classifier.py`

Tests to add later:

- NVIDIA product specification URLs should remain product/spec sources.
- NVIDIA forum/community URLs should not be treated as equivalent to official spec pages.
- Board partner product pages should not regress.

Explicit non-goals:

- Do not lower all `nvidia.com` reliability blindly.
- Do not change schema unless there is a separate explicit design step.
- Do not use scorer changes to compensate for source subtype ambiguity.

## Task 3: Add product spec claim semantics for model + attribute + value

Why now:

The eval_004 claim is still a generic `general_fact`, while the actual task is a numeric product specification check. Making the claim text/type logic more explicit can reduce future ambiguity in evidence matching and conflict detection.

Likely files to inspect later:

- `app/services/claim_decomposer.py`
- `tests/services/test_claim_decomposer.py`
- `app/services/evidence_extractor.py`
- `tests/services/test_evidence_extractor.py`

Tests to add later:

- `RTX 5070 Ti 是否是 16GB 显存？` should preserve model + attribute + value in the generated claim.
- Other model values should not support or oppose unless bound to the same model.
- Existing AI model and general fact decomposition should not regress.

Explicit non-goals:

- Do not introduce a full product knowledge graph.
- Do not introduce LLM decomposition.
- Do not change schema in this task.

---

# 7. Current Decision

v0.2.8 fixed the eval_004 evidence direction bug. The system has moved from false conflict to support-only `mostly_confirmed`.

The next useful work should focus on product source quality and product spec semantics, not scorer, aggregator, TavilyProvider, or broad source ranking changes.
