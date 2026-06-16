# Entity-aware Official Source Guard Plan

版本：v0.2.6-plan  
文档类型：开发计划 / 最小实现边界  
适用范围：Critical Search Layer source ranking / source classification / search planning

---

# 1. 背景

`docs/evals/tavily_real_world_eval_findings_003.md` 显示，v0.2.5 的 source-type ranking/filtering 已经生效：在 `ai_model_info` 样本中，Hugging Face / GitHub 等 primary source type 能进入 final sources。

但第三轮 eval 也暴露了新的核心问题：source type 与 claim entity/domain 没有对齐。例如 GPT-4.1 样本中，Hugging Face 被分类为 `official_model_card`，但它不是 OpenAI 官方源。

v0.2.6 的目标不是重写 ranking，也不是提高置信度，而是在现有 source-type ranking 之上增加最小 entity-aware official source guard，避免“平台型强来源”压过“目标实体官方来源”。

---

# 2. 问题定义

当前系统把 source type 当作来源质量的主要排序信号，但 source type 只能说明来源形态，不等于目标实体官方性。

必须明确区分：

- `source_type` 不等于目标实体官方来源。
- `official_model_card` 不等于 OpenAI 官方源。
- `source_code_repo` 不等于目标组织控制的 repo。
- Hugging Face / GitHub 是平台域名，不能自动证明页面由 OpenAI、Meta、Llama、NVIDIA 或 SEC 控制。

典型风险：

- GPT-4.1 query 中，非 OpenAI Hugging Face 页面被排到 OpenAI 官方页面之前。
- Llama query 中，第三方 GitHub mirror 被当作 Meta/Llama official repo。
- SEC query 中，金融媒体或机构文章替代 `sec.gov` 官方公告。
- RTX query 中，社区帖子替代 NVIDIA 或板卡厂商规格页。

---

# 3. 最小适用范围

v0.2.6 只覆盖第三轮 eval 已暴露的实体类别，不扩展到所有实体。

| scope | target examples | preferred official ownership signal |
|---|---|---|
| OpenAI / GPT series | GPT-4.1, OpenAI voice model | `openai.com`, `platform.openai.com`, `help.openai.com` |
| Meta / Llama series | Llama 3.1, Meta Llama | `llama.com`, `meta.com`, `huggingface.co/meta-llama`, `github.com/meta-llama` |
| SEC / policy_legal | spot bitcoin ETF/ETP approval | `sec.gov` |
| NVIDIA / RTX product specs | RTX 5070 Ti VRAM | `nvidia.com` and common board-partner product/spec pages |

Out of scope for v0.2.6:

- universal entity resolution;
- organization knowledge graph;
- all model vendors;
- all GPU vendors;
- all regulators or government agencies.

---

# 4. Rule Draft

## OpenAI / GPT

If query or claim text indicates OpenAI / GPT / GPT-4.1 / OpenAI voice models:

- Prefer:
  - `openai.com`
  - `platform.openai.com`
  - `help.openai.com`
- Treat Hugging Face / GitHub as non-target official unless the URL or namespace clearly indicates OpenAI-controlled ownership.
- Do not let generic `official_model_card` outrank OpenAI official domains for OpenAI claims.

## Meta / Llama

If query or claim text indicates Meta / Llama / Llama 3.1:

- Prefer:
  - `llama.com`
  - `meta.com`
  - `huggingface.co/meta-llama`
  - `github.com/meta-llama`
- Treat third-party Hugging Face namespaces and third-party GitHub owners as weaker than target-aligned official sources.
- Keep `official_model_card` and `source_code_repo` useful, but only treat them as target-official when namespace/owner aligns.

## SEC / Policy Legal

If query or claim text indicates SEC / ETF / ETP approval / securities regulator:

- Prefer:
  - `sec.gov`
- SEC official pages should outrank media, financial institutions, blogs, and community sources even if those sources are highly relevant.
- `financial_filing` / `government_docs` source types still matter, but entity alignment to SEC is the stronger signal.

## NVIDIA / RTX Product Specs

If query or claim text indicates NVIDIA / RTX / GeForce / GPU VRAM / product specs:

- Prefer:
  - `nvidia.com`
  - common board-partner official product/spec pages
- Initial board-partner allowlist can be conservative and small, for example:
  - `asus.com`
  - `msi.com`
  - `gigabyte.com`
  - `galax.com`
  - `zotac.com`
  - `pny.com`
  - `colorful.cn`
  - `inno3d.com`
  - `palit.com`
- Community/forum sources should not outrank official product/spec pages.

---

# 5. Sorting Strategy

The existing source-type priority should remain in place.

v0.2.6 adds entity/domain alignment as a stronger or co-equal ranking signal:

1. Entity/domain alignment priority.
2. Source type priority.
3. `is_primary_source`.
4. `base_reliability`.
5. Original provider order for stable tie-breaking.

Rules:

- Target entity official domain must not be pushed below a non-target high source type.
- Non-target `official_model_card` cannot outrank target official domain for that entity.
- Non-target `source_code_repo` cannot outrank target organization-controlled repo or official domain.
- Same score must preserve provider original order.
- Final `response.sources` must still respect `request.max_sources`.
- Provider candidate expansion and search query budget behavior should remain unchanged.

Example expected behavior:

```text
Query: GPT-4.1 是否是 OpenAI 发布的模型？
Candidates:
  1. huggingface.co/some-user/gpt-4.1
  2. openai.com/index/gpt-4-1

Expected final ranking:
  1. openai.com/index/gpt-4-1
  2. huggingface.co/some-user/gpt-4.1
```

---

# 6. File Change Suggestions

Implementation should stay small and local.

Recommended files:

- `app/services/trusted_search_service.py`
  - Apply entity-aware ranking before `request.max_sources` truncation.
  - Preserve current source-type ranking and stable sort behavior.

- `app/services/source_classifier.py`
  - Add or refine official domain recognition for OpenAI and vendor domains where needed.
  - Keep domain classification deterministic.

- `app/services/search_planner.py`
  - Add official query recall for policy/legal and product_info where candidate absence blocks ranking.

Recommended tests:

- `tests/services/test_trusted_search_service.py`
  - Source ranking and max source truncation behavior.

- `tests/services/test_source_classifier.py`
  - Official domain classification rules.

- `tests/services/test_search_planner.py`
  - Official query generation for policy/legal and product_info.

Optional structure:

- If ranking logic grows beyond a few helper functions, create `app/services/source_ranker.py`.
- Keep the public schema unchanged.

---

# 7. Test Plan

All tests must be deterministic and must not access the real network.

## GPT-4.1 / OpenAI

Case:

- Provider returns `huggingface.co` first.
- Provider returns `openai.com` later.

Expected:

- `openai.com` ranks before Hugging Face for OpenAI/GPT claims.
- Non-OpenAI Hugging Face namespace is not treated as target official source.
- Final sources still respect `max_sources`.

## Llama / Meta

Case:

- Provider returns third-party Hugging Face/GitHub first.
- Provider returns `huggingface.co/meta-llama`, `github.com/meta-llama`, `llama.com`, or `meta.com` later.

Expected:

- Meta/Llama official namespace/domain ranks first.
- Third-party HF/GitHub does not outrank target-aligned official source.

## SEC / Policy Legal

Case:

- Provider returns media or financial institution pages before `sec.gov`.

Expected:

- `sec.gov` ranks before non-SEC sources.
- `sec.gov` is classified as high-reliability official/government/regulator source according to existing source types.

## RTX / Product Specs

Case:

- Provider returns Zhihu/Reddit/community source before NVIDIA or board-partner spec page.

Expected:

- `nvidia.com` or board-partner official spec page ranks before community source.
- Community source can remain as fallback only when no official product/spec source exists.

## Stable Sorting

Case:

- Two candidates have the same entity alignment, source type, primary flag, and base reliability.

Expected:

- Original provider order is preserved.

## max_sources

Case:

- Internal candidate pool has more than `request.max_sources`.

Expected:

- Ranking runs before truncation.
- Final `response.sources` length still equals or is below `request.max_sources`.

## Default Network Safety

Expected:

- Unit tests use fake/static providers only.
- Default tests do not use Tavily network.
- No API key is read or required.

---

# 8. Explicit Non-goals

Do not do the following in v0.2.6:

- Do not connect Brave / SerpAPI or any new provider.
- Do not introduce an LLM reranker.
- Do not change request/response schema.
- Do not modify TavilyProvider.
- Do not modify MCP.
- Do not add dependencies.
- Do not tune scorer upward.
- Do not loosen claim_aggregator.
- Do not expand to all entities.
- Do not add a database, cache, organization registry, or knowledge graph.
- Do not make real network calls in tests.

---

# 9. Recommended Implementation Order

## Step 1: Add entity-aware ranking guard

Start in `TrustedSearchService` or a small `source_ranker` helper. This directly addresses the eval_001 failure where non-target Hugging Face sources outrank the expected OpenAI official source.

Minimum tests:

- OpenAI official domain beats non-OpenAI Hugging Face.
- Meta/Llama official namespace beats third-party HF/GitHub.
- Stable ordering remains intact.
- `max_sources` behavior remains unchanged.

## Step 2: Complete official domain classification gaps

Update `source_classifier` for OpenAI official domains and conservative vendor/regulator domains where the current rules are too weak.

Minimum tests:

- `openai.com` official pages classify as official source type.
- `platform.openai.com/docs` classifies as `official_docs`.
- Third-party pages mentioning OpenAI do not become official.

## Step 3: Improve official query recall for missing-source classes

Update `SearchPlanner` for product_info and policy_legal so ranking has official candidates to work with.

Minimum tests:

- SEC questions generate `site:sec.gov` / approval order / statement / press release queries.
- RTX/GPU specification questions generate NVIDIA / manufacturer / specification / product page queries.
- Existing strictness query budget behavior remains compatible.

---

# 10. Decision

v0.2.6 should keep source-type ranking but add entity-aware official source guard. The first implementation should be conservative, deterministic, and limited to OpenAI/GPT, Meta/Llama, SEC, and NVIDIA/RTX because those are the concrete failure modes seen in eval run 003.

This is a ranking and source selection quality fix, not a scoring, aggregation, schema, provider, or MCP change.
