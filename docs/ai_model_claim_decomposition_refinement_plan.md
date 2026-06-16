# AI Model Claim Decomposition Refinement Plan

版本：v0.2.7-plan  
文档类型：开发计划 / 最小实现边界  
适用范围：AI model question intent routing and claim decomposition

---

# 1. 背景

`docs/evals/tavily_real_world_eval_findings_004.md` 显示，v0.2.6 已经解决官方源召回、官方域名分类和 entity-aware ranking 的主要问题。

eval_001 中：

- query: `GPT-4.1 是否是 OpenAI 发布的模型？`
- final sources: `platform.openai.com`
- source_type: `official_docs`
- overall_status: `unsupported`
- evidence_count: `0`

这不是 source recall 失败。问题已经转移到 claim decomposition / evidence semantics：用户问的是 release/origin，但系统仍使用 open-source template，把问题拆成权重、训练代码、训练数据、许可证和严格开源解释。

v0.2.7 的目标是让 AI model 问题根据用户意图拆分，而不是一律套 open-source 模板。

---

# 2. 问题定义

AI model 问题至少有几类不同意图，不能都拆成开源状态核查。

必须区分：

- release/origin claim 不等于 open-source claim。
- closed API model 查询不应强行拆成 weights / source code / training data / license。
- open-source 查询才需要拆 weights / source code / license / training data / strict open-source interpretation。

当前问题：

```text
GPT-4.1 是否是 OpenAI 发布的模型？
```

被拆成：

```text
GPT-4.1 是否公开模型权重
GPT-4.1 是否公开训练代码
GPT-4.1 是否公开训练数据
GPT-4.1 的许可证是否允许商用
GPT-4.1 是否能严格称为开源模型
```

这些 subclaims 与用户原始意图不匹配。即使命中 OpenAI 官方文档，也很可能抽不到证据。

---

# 3. 最小意图分类

v0.2.7 只做规则化最小覆盖，不做通用自然语言理解。

| intent | trigger examples | expected claim focus |
|---|---|---|
| `release_or_origin` | 是否是 OpenAI 发布、谁发布、是否由某公司提供、官方发布页、发布时间 | 官方发布/文档页面、提供方、发布方、第三方转述区分 |
| `model_access` | 是否可用、API、platform、ChatGPT、Azure、OpenRouter、怎么访问 | API / platform availability, access channel |
| `open_source_status` | 是否开源、公开权重、允许商用、license、训练代码、训练数据 | weights, source code, training data, license, strict open-source interpretation |
| `model_capability_or_spec` | 上下文长度、多模态、价格、版本、参数、能力 | capability/spec claims such as context length, modalities, price, version |

First implementation can route by keyword and phrase patterns.

---

# 4. Eval 001 修复目标

For:

```text
GPT-4.1 是否是 OpenAI 发布的模型？
```

Expected claims:

1. `GPT-4.1 是否存在 OpenAI 官方发布或文档页面`
2. `GPT-4.1 是否由 OpenAI 提供或发布`
3. `GPT-4.1 是否可通过 OpenAI API / platform 使用`

Do not generate by default:

- `GPT-4.1 是否公开训练代码`
- `GPT-4.1 是否公开训练数据`
- `GPT-4.1 的许可证是否允许商用`
- `GPT-4.1 是否能严格称为开源模型`

Open-source subclaims should only appear when the query asks about open source, open weights, license, commercial use, training code, or training data.

---

# 5. Behaviors to Preserve

Do not break the existing open-source decomposition where it is actually the user intent.

Examples that should keep open-source decomposition:

```text
Llama 3.1 是否公开模型权重并允许商用？
MiroThinker 1.7 是不是开源模型？
GPT-4.1 是否开源？
```

These should still produce relevant claims such as:

- existence / official page;
- model weights;
- source code when applicable;
- training data when applicable;
- license / commercial use;
- strict open-source interpretation.

For `Llama 3.1 是否公开模型权重并允许商用？`, weights and license claims are required and must not regress.

For `MiroThinker 1.7 是不是开源模型？`, the current six-claim template remains appropriate.

---

# 6. Proposed Rule Design

## Step 1: Detect AI model intent

Add a small helper inside `claim_decomposer.py`, for example:

```text
_classify_ai_model_query_intent(query: str) -> str
```

Suggested priority:

1. `open_source_status`
2. `release_or_origin`
3. `model_access`
4. `model_capability_or_spec`
5. fallback to current open-source template only when clearly open-source-like or when no safer intent is detected

Open-source intent should win when query contains:

- `开源`
- `公开权重`
- `权重`
- `license`
- `许可证`
- `商用`
- `commercial`
- `training code`
- `训练代码`
- `训练数据`

Release/origin intent should match when query contains:

- `是否是 ... 发布`
- `是不是 ... 发布`
- `由 ... 发布`
- `谁发布`
- `发布的模型`
- `官方发布`
- `官方文档`
- `official release`
- `released by`

Model access intent should match when query contains:

- `API`
- `platform`
- `可用`
- `能用`
- `访问`
- `ChatGPT`
- `Azure`
- `OpenRouter`

Capability/spec intent can be basic for now:

- `上下文`
- `context`
- `多模态`
- `价格`
- `版本`
- `参数`

## Step 2: Add release/origin template

For release/origin:

```text
1. {entity} 是否存在 {provider} 官方发布或文档页面
2. {entity} 是否由 {provider} 提供或发布
3. {entity} 是否可通过 {provider} API / platform 使用
```

Provider extraction can be conservative:

- If query contains `OpenAI`, provider is `OpenAI`.
- Otherwise use a generic form: `{entity} 是否存在官方发布或文档页面`.

## Step 3: Keep open-source template unchanged

For open-source intent, preserve current six-claim template.

This is important because current eval samples and tests rely on it:

- MiroThinker open-source question;
- Llama weights / commercial-use question.

---

# 7. File Change Suggestions

Primary files:

- `app/services/claim_decomposer.py`
- `tests/services/test_claim_decomposer.py`

Possible follow-up file, not first priority:

- `tests/services/test_evidence_extractor.py`

The first implementation should prefer not changing `evidence_extractor.py`. Once release/origin claims exist, a later pass can teach the extractor to recognize official docs snippets for release/origin evidence.

No schema changes are needed because `claim_type` is already a string.

Suggested claim_type values:

- `official_release_page`
- `model_provider`
- `model_access`

Use stable, explicit names. Do not add enums or schema fields.

---

# 8. Test Plan

## GPT-4.1 release/origin query

Input:

```text
GPT-4.1 是否是 OpenAI 发布的模型？
```

Expected:

- Does generate:
  - official OpenAI release/docs page claim;
  - OpenAI provider/release claim;
  - OpenAI API/platform access claim.
- Does not generate:
  - `source_code`;
  - `training_data`;
  - `license`;
  - strict open-source interpretation.

## GPT-4.1 open-source query

Input:

```text
GPT-4.1 是否开源？
```

Expected:

- Still generates open-source related claims.
- Includes model weights / source code / training data / license / strict interpretation where appropriate.

## Llama weights and commercial-use query

Input:

```text
Llama 3.1 是否公开模型权重并允许商用？
```

Expected:

- Still generates weights claim.
- Still generates license / commercial-use claim.
- Does not collapse into release/origin-only claims.

## MiroThinker open-source query

Input:

```text
MiroThinker 1.7 是不是开源模型？
```

Expected:

- Current six-claim open-source decomposition does not regress.

## Trusted search E2E mock

Expected:

- Existing mock flow should still return valid response shape.
- No schema changes.
- No network access.

---

# 9. Explicit Non-goals

Do not do the following in v0.2.7:

- Do not change source ranking.
- Do not change SearchPlanner.
- Do not change source_classifier.
- Do not change scorer.
- Do not loosen aggregator.
- Do not modify schema.
- Do not modify TavilyProvider.
- Do not modify MCP.
- Do not add dependencies.
- Do not connect Brave / SerpAPI.
- Do not introduce LLM decomposition.
- Do not build general natural-language intent understanding.
- Do not route all AI model questions into release/origin claims.

---

# 10. Recommended Implementation Order

## Step 1: Add intent classifier helper

Implement a deterministic helper in `claim_decomposer.py` that classifies AI model queries into the minimum intent set.

Start with keyword and phrase matching only.

## Step 2: Add release/origin claim template

Implement the three-claim release/origin template for GPT/OpenAI-style release questions.

Keep claim IDs stable as `c1`, `c2`, `c3`.

## Step 3: Preserve open-source behavior

Keep the existing six-claim template for open-source intent. Add tests before changing behavior so regressions are visible.

## Step 4: Run targeted and full tests in Windows PowerShell

Recommended verification after implementation:

```powershell
uv run pytest tests/services/test_claim_decomposer.py
uv run pytest
uv run ruff check .
```

---

# 11. Decision

v0.2.7 should make AI model claim decomposition intent-aware with the smallest deterministic rule set. The first target is eval_001: distinguish “is GPT-4.1 released/provided by OpenAI?” from “is this model open source?”.

This is not a source-layer problem anymore. Official sources now reach final sources; the next bottleneck is whether the system asks the right claims of those sources.
