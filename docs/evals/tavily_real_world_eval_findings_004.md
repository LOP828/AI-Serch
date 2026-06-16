# Tavily Real-world Eval Findings 004

版本：v0.2.6 findings  
文档类型：Tavily real-world eval 第四轮质量问题汇总  
范围：基于 `docs/evals/tavily_real_world_eval_run_004.md` 的脱敏记录

---

# 1. 记录边界

本文件只根据 `docs/evals/tavily_real_world_eval_run_004.md` 总结，不包含 API key、Authorization header、raw provider payload 或完整网页正文，也不补造 run_004 中没有的数据。

本轮目标是判断 v0.2.6 三刀后的真实搜索质量变化，并确定下一轮开发重点。

---

# 2. 核心结论

v0.2.6 三刀有效：

- OpenAI/GPT entity-aware ranking guard 生效。
- official domain classification 生效。
- official-source query recall 生效。

系统已经从“官方源进不来 / 官方源被错误分类 / 非目标强 source type 抢占 final sources”，推进到“官方源已进入 final sources，但部分 claim 语义和 evidence extraction 仍需修”。

最重要的转折是 eval_001：`platform.openai.com` 已进入 final sources 且为 `official_docs`，但 `overall_status=unsupported`、`evidence_count=0`。这不是 source recall 失败，而是 AI model claim decomposition / evidence semantics 问题。

---

# 3. Eval 级发现

## eval_001: GPT-4.1 / OpenAI

Observed:

- final sources 已从 run_003 的 Hugging Face 变为 `platform.openai.com`。
- 两个 final sources 都是 `official_docs`，`base_reliability=0.95`，`is_primary_source=true`。
- `overall_status=unsupported`。
- `overall_confidence=0.0`。
- `evidence_count=0`。

Finding:

这是 v0.2.6 官方源召回和 entity-aware ranking 的成功案例，不应被解读为官方源失败。

失败点转移到了 claim decomposition / evidence semantics。原始问题是：

```text
GPT-4.1 是否是 OpenAI 发布的模型？
```

但 claim set 仍偏向 open-source template：

- 是否公开模型权重
- 是否公开训练代码
- 是否公开训练数据
- 许可证是否允许商用
- 是否能严格称为开源模型

这些 claim 并不能直接表达“GPT-4.1 是否由 OpenAI 发布 / 是否存在 OpenAI 官方发布或 API 文档”。因此，即使命中 OpenAI 官方文档，抽取器也可能找不到与这些 open-source subclaims 匹配的 evidence。

## eval_002: Llama 3.1 / Meta

Observed:

- run_004 与 run_003 基本一致。
- final sources 仍为 Hugging Face `official_model_card` 和 GitHub `source_code_repo`。
- `overall_status=partially_confirmed`。

Finding:

该样本没有新增明显回归。它仍然需要后续实体所有权判断和 claim semantics 改进，但不是本轮最突出的新问题。

## eval_003: OpenAI 语音模型

Observed:

- `openai.com` official docs 进入 final sources。
- 两个 source 都是 `official_docs`，`base_reliability=0.95`，`is_primary_source=true`。
- `overall_status=confirmed`。
- `overall_confidence=0.9196`。

Finding:

OpenAI 官方域名 classification 和 ranking/retrieval 生效。run_003 中 `openai.com` 仍为 `unknown`，run_004 已转为 official source 并支持 confirmed 结论。

## eval_004: RTX 5070 Ti 显存

Observed:

- `nvidia.com` 进入 final sources。
- source type 为 `product_page`，`base_reliability=0.8`，`is_primary_source=true`。
- `overall_status=mostly_confirmed`。

Finding:

product_info 官方源 recall 改善明显。run_003 的 final sources 是 Zhihu / Reddit，run_004 已进入 NVIDIA 官方域。

Remaining caveat:

run_004 sources 是 NVIDIA GeForce Forums 页面，不是明确的官方规格页。该问题应记录为 page extraction / evidence selection 或 official-domain page subtype 细化的后续优化，不应误判为 source recall 失败。

## eval_005: SEC 比特币现货 ETF/ETP

Observed:

- `sec.gov` 进入 final sources。
- source type 为 `government_docs`，`base_reliability=0.95`，`is_primary_source=true`。
- `overall_status=confirmed`。
- `overall_confidence=0.9405`。

Finding:

policy_legal 官方源 recall 改善明显。run_003 未命中 `sec.gov`，run_004 命中两个 `sec.gov` sources。

Remaining caveat:

Evidence excerpt 仍带有页面导航或上下文噪音，例如 `About` / `Careers` 一类片段。该问题属于 page extraction / evidence selection 后续优化，不是 source recall 或 source classification 问题。

---

# 4. 分析维度

## Source recall 已解决的问题

run_004 证明官方源召回显著改善：

- OpenAI/GPT: `platform.openai.com` 进入 final sources。
- OpenAI voice model: `openai.com` 进入 final sources。
- product_info RTX: `nvidia.com` 进入 final sources。
- policy_legal SEC: `sec.gov` 进入 final sources。

因此，下一轮不应继续优先做 source ranking，除非新 eval 证明回退。

## Source classification 已解决的问题

run_004 证明官方域名分类生效：

- `platform.openai.com` -> `official_docs`
- `openai.com` -> `official_docs`
- `nvidia.com` -> `product_page`
- `sec.gov` -> `government_docs`

这些 source 的 `base_reliability` 和 `is_primary_source` 均明显高于 run_003 中的 `unknown` / community results。

## Entity-aware ranking 已解决的问题

eval_001 从 run_003 的 Hugging Face final sources 变成 run_004 的 `platform.openai.com` final sources，说明 OpenAI/GPT entity-aware ranking guard 生效。

当前没有证据显示 source-type ranking 或 entity-aware ranking 回退。不要继续优先改 ranking。

## Claim decomposition 仍缺的问题

eval_001 是最明确的新瓶颈。

当前 `ai_model_info` claim decomposition 过度套用了“是否开源模型”的 subclaim 模板。对于“是否是 OpenAI 发布的模型”这类 release/origin 问题，应拆成：

- GPT-4.1 是否存在 OpenAI 官方发布页或 API 文档；
- OpenAI 是否将 GPT-4.1 列为可用模型；
- GPT-4.1 是否由 OpenAI 发布或提供；
- 是否需要区分 OpenAI 原生发布与 Azure/OpenRouter 等第三方平台转述。

不应默认拆成权重、训练代码、训练数据、license 和严格开源解释。

## Evidence extraction / evidence semantics 仍缺的问题

eval_001 命中官方 docs 但无 evidence，说明 extractor 对官方 docs fallback/snippet 的模型发布语义支持不足。

eval_004 和 eval_005 的 snippets 也显示 evidence selection 仍有噪音：

- NVIDIA 样本命中官方域，但 snippet 来自论坛用户规格描述，不是明确规格页。
- SEC 样本命中官方域，但 evidence 摘录包含页面导航或上下文噪音。

这些应作为后续优化，但优先级低于 eval_001 的 claim semantics。

## Answer constraints 是否合理

整体合理：

- eval_001 在 evidence_count=0 时保持 `cautious`、`must_disclose_uncertainty=true`、`can_answer_confidently=false`。
- eval_003 / eval_004 / eval_005 在官方源和 supporting evidence 进入后允许更 confident 的 tone。

当前不应通过 answer constraints 修复 eval_001。问题在上游 claim decomposition 和 evidence extraction。

---

# 5. 不应立即做的事

- 不要建议调高 scorer。
- 不要建议放宽 aggregator。
- 不要接 Brave / SerpAPI。
- 不要继续优先做 source ranking，除非新 eval 证明回退。
- 不要把 eval_001 误判为 source recall 失败。
- 不要因为 NVIDIA / SEC evidence snippet 有噪音就回退官方域名分类。
- 不要改 schema、TavilyProvider、MCP 或依赖来处理本轮 findings。

---

# 6. 下一步最多 3 个开发任务

## Task 1: 改进 AI model query 的 claim decomposition

为什么现在做：

eval_001 已经命中 OpenAI 官方 docs，但 claim set 仍是 open-source template，导致所有 claim unsupported。当前最大瓶颈从 source recall 转为 claim semantics。

应改文件：

- `app/services/claim_decomposer.py`

应补测试：

- `tests/services/test_claim_decomposer.py`
- GPT-4.1 “是否是 OpenAI 发布的模型”应生成 release/origin claims，而不是 open-source subclaims。
- “Llama 3.1 是否公开模型权重并允许商用”仍应保留 weights/license/open-source 相关 claims。
- “MiroThinker 1.7 是不是开源模型”仍应保留原 open-source claim template。

明确不做：

- 不改 schema。
- 不引入 LLM claim decomposer。
- 不改变 scorer 或 aggregator。
- 不把所有 ai_model_info 问题都统一成 release/origin template。

## Task 2: 改进 evidence extractor 对官方 docs fallback/snippet 的模型发布语义支持

为什么现在做：

eval_001 的 `platform.openai.com` source 已进入 final sources，但 evidence_count=0。即使 claim decomposition 改好，extractor 也需要能从官方 docs/snippet 中识别“模型存在 / OpenAI 提供 / API 可用”等 release/origin evidence。

应改文件：

- `app/services/evidence_extractor.py`

应补测试：

- `tests/services/test_evidence_extractor.py`
- 官方 OpenAI docs snippet 中出现 GPT-4.1 / models / API availability 时，应支持 release/origin claim。
- 不应把 OpenAI docs 中的 tokenizer、通用 API 文档错误抽成 model release evidence。
- 无相关模型名时仍返回空 evidence。

明确不做：

- 不引入 LLM reranker。
- 不从标题或主观推断编造 evidence。
- 不调高 relevance score 绕过 evidence 缺失。

## Task 3: 记录并小步优化 official-domain evidence snippet 噪音

为什么现在做：

eval_004 / eval_005 已证明官方源进入 final sources，但 snippets 仍有噪音。该任务优先级低于 eval_001 claim semantics，但可作为后续质量收敛。

应改文件：

- `app/services/page_fetcher.py`
- `app/services/evidence_extractor.py`

应补测试：

- `tests/services/test_page_fetcher.py`
- `tests/services/test_evidence_extractor.py`
- SEC 页面导航文本不应成为主要 evidence snippet。
- NVIDIA forum/user-spec snippet 与 official spec page snippet 应能区分或降噪。

明确不做：

- 不实现浏览器渲染。
- 不实现 PDF 专项解析。
- 不接新搜索 provider。
- 不把该任务排在 claim decomposition 修复之前。

---

# 7. 当前决策

v0.2.6 三刀已经完成它们的目标：官方源能进来、官方域能被识别、entity-aware ranking 能避免 OpenAI 问题被 Hugging Face 抢占。

下一轮开发应从 source layer 转向 claim/evidence layer，优先修 AI model query 的 claim decomposition，尤其是 release/origin claim 与 open-source claim 的区分。
