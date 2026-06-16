# Tavily Real-world Eval Findings 005

版本：v0.2.7 findings  
文档类型：Tavily real-world eval 第五轮质量问题汇总  
范围：基于 `docs/evals/tavily_real_world_eval_run_005.md` 的脱敏记录

---

# 1. 记录边界

本文件只根据 `docs/evals/tavily_real_world_eval_run_005.md` 总结，不包含 API key、Authorization header、raw provider payload 或完整网页正文，也不补造 run_005 中没有的数据。

本轮目标是判断 v0.2.7 AI model intent routing 是否解决 eval_001，并形成下一轮开发依据。

---

# 2. 核心结论

v0.2.7 第一刀有效。

eval_001 从 run_004 到 run_005 出现结构性改善：

| metric | run_004 | run_005 |
|---|---:|---:|
| overall_status | unsupported | confirmed |
| overall_confidence | 0.0 | 0.9405 |
| claims_count | 6 | 3 |
| evidence_count | 0 | 6 |

Run 005 final sources:

- `openai.com` / `official_docs`
- `platform.openai.com` / `official_docs`

Run 005 claim types:

- `official_release_page`
- `model_provider`
- `model_access`

结论：

- release/origin query 不再被误拆成 open-source claims。
- evidence extractor 能从 OpenAI official docs 中支持新的 release/origin claims。
- v0.2.6 已解决官方源进入 final sources；v0.2.7 进一步解决了 eval_001 的 claim decomposition 语义问题。

下一步不应回头继续调 source recall / source ranking，除非后续 eval 证明回退。

---

# 3. Eval 级发现

## eval_001: GPT-4.1 / OpenAI

Observed:

- `overall_status=confirmed`
- `overall_confidence=0.9405`
- `claims_count=3`
- `evidence_count=6`
- final sources: `openai.com` and `platform.openai.com`, both `official_docs`

Claim types:

- `official_release_page`
- `model_provider`
- `model_access`

Finding:

This is the strongest signal in run_005. The same query that was unsupported in run_004 is now confirmed because the decomposer asks release/origin/access claims instead of open-source claims.

The result validates v0.2.7 first cut. It also shows that evidence extraction can already support the new claims when official OpenAI docs are present.

## eval_002: Llama 3.1

Observed:

- `overall_status=partially_confirmed`
- final sources remain Hugging Face / GitHub primary source types.
- claims remain open-source / weights / license oriented.

Finding:

This is expected. The query asks whether Llama 3.1公开模型权重并允许商用, so preserving open-source-related claims is correct.

## eval_003: OpenAI voice model

Observed:

- `overall_status=confirmed`
- final sources are `openai.com` official docs.

Finding:

No source recall or classification regression is visible. This remains a success case for v0.2.6 source-layer fixes.

## eval_004: RTX 5070 Ti

Observed:

- `overall_status=conflicting`
- `conflicts_count=1`
- final sources are `nvidia.com` product pages.
- one evidence item is `oppose`, one is `support`.

Finding:

Record this as a conflict phenomenon only. Do not immediately conclude that scorer should be tuned or aggregator should be relaxed.

The next useful step is to inspect the evidence extraction and conflict detection boundary:

- Was the `oppose` evidence actually opposing the 16GB VRAM claim?
- Did forum/user-spec text cause support_type confusion?
- Should official specification pages be distinguished from official-domain forum pages?

## eval_005: SEC Bitcoin ETF/ETP

Observed:

- `overall_status=confirmed`
- final sources are `sec.gov` government docs.

Finding:

No source recall or official classification regression is visible. The sample remains confirmed with government sources.

---

# 4. Analysis Dimensions

## Source recall / ranking

Do not prioritize source recall or ranking next.

Reason:

- eval_001 has OpenAI official docs.
- eval_003 has OpenAI official docs.
- eval_004 has NVIDIA official-domain sources.
- eval_005 has SEC official sources.

v0.2.6 source-layer fixes are still holding in run_005.

## Claim decomposition

v0.2.7 claim decomposition fix worked for the highest-priority AI model release/origin sample.

The next step is not necessarily more implementation; first broaden tests for AI model intent routing so future changes do not regress:

- `released by`
- `官方文档`
- `API 可用性`
- `上下文长度`
- open-source queries that must remain open-source claims

## Evidence extraction

eval_001 shows evidence extraction can support release/origin claims from OpenAI official docs.

eval_004 suggests evidence extraction still needs closer review for product_info:

- official-domain forum text may include ambiguous user specs;
- support/oppose classification may be too brittle for hardware spec questions.

## Conflict detection

eval_004 surfaced a conflict. That may be correct behavior, but the evidence boundary needs review before changing logic.

The immediate next task should be analysis/planning, not scorer or aggregator changes.

## Answer constraints

Answer constraints appear reasonable:

- eval_001/003/005 confirmed cases allow confident tone.
- eval_004 conflicting case uses `conflict_aware`, requires uncertainty disclosure, and does not allow confident answer.

Do not loosen answer constraints.

---

# 5. What Not To Do

- Do not connect Brave / SerpAPI.
- Do not modify TavilyProvider.
- Do not tune scorer upward.
- Do not loosen aggregator.
- Do not keep expanding source ranking unless a later eval shows source recall/ranking regression.
- Do not treat eval_004 as proof that conflict handling is wrong before inspecting evidence boundaries.

---

# 6. Recommended Next Tasks

## Task 1: Analyze eval_004 conflicting evidence / conflict detection boundary

Why now:

Run 005 introduces one new notable issue: RTX 5070 Ti is `conflicting` with one support and one oppose item. This should be understood before any implementation change.

Recommended artifact:

- `docs/evals/tavily_real_world_eval_005_conflict_analysis.md`

Likely files to inspect later:

- `app/services/evidence_extractor.py`
- `app/services/conflict_detector.py`
- `app/services/claim_aggregator.py`

Tests to plan later:

- product_info evidence that says `RTX 5070 Ti 16G` should not be marked oppose.
- official-domain forum snippets should not be treated as official specs without care.
- conflict detector should distinguish true opposing evidence from noisy extraction.

Explicit non-goals:

- Do not tune scorer first.
- Do not relax aggregator first.
- Do not implement before writing the analysis plan.

## Task 2: Add broader AI model intent routing tests

Why now:

eval_001 is fixed, but v0.2.7 intent routing should be protected against regression across nearby phrasing.

Files to change:

- `tests/services/test_claim_decomposer.py`

Potential cases:

- `GPT-4.1 released by OpenAI?`
- `GPT-4.1 是否有 OpenAI 官方文档？`
- `GPT-4.1 是否可以通过 OpenAI API 使用？`
- `GPT-4.1 上下文长度是多少？`
- `GPT-4.1 是否开源？`
- `Llama 3.1 是否公开权重并允许商用？`

Explicit non-goals:

- Do not introduce LLM intent detection.
- Do not change schema.
- Do not route all AI model questions to release/origin.

## Task 3: Evaluate evidence extraction precision for official docs snippets

Why now:

Run 005 evidence is good enough for eval_001, but eval_004 and eval_005 show snippets can contain noisy or weakly scoped text. This task should assess whether targeted extraction improvements are needed.

Likely files to inspect later:

- `app/services/evidence_extractor.py`
- `app/services/page_fetcher.py`

Tests to plan later:

- OpenAI release docs should support release/origin claims.
- NVIDIA user forum specs should not be overtreated as official specification evidence.
- SEC docs with navigational text should extract the approval-specific sentence if present.

Explicit non-goals:

- Do not add browser rendering.
- Do not add PDF parsing in this task.
- Do not alter scoring to hide extraction issues.

---

# 7. Current Decision

The next development focus should not return to source recall or ranking. v0.2.6 and v0.2.7 together moved the system past the official-source bottleneck for these samples.

The next highest-signal work is to understand eval_004's conflicting evidence boundary, while preserving and broadening tests for the now-successful AI model intent routing.
