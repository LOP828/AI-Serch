# Tavily Real-world Eval Findings 002

版本：v0.2.4 findings  
文档类型：Tavily real-world eval 第二轮质量问题汇总  
范围：基于 `docs/evals/tavily_real_world_eval_run_002.md` 的脱敏记录

---

# 1. 记录边界

本文件只整理第二轮 Tavily real-world eval 的脱敏结果，不包含 API key、Authorization header、raw provider payload、完整网页正文或任何新增网络验证。

本轮不是为了调高系统置信度，而是为了定位真实 provider 候选进入 CSL 后的质量瓶颈。结论只基于 `tavily_real_world_eval_run_002.md` 中已有字段和人工备注。

---

# 2. 样本概览

| eval_id | query | final sources | overall_status | main finding |
|---|---|---|---|---|
| eval_001 | GPT-4.1 是否是 OpenAI 发布的模型？ | Azure, OpenRouter | uncertain | 未召回 OpenAI 官方源；Azure/OpenRouter 不是 primary OpenAI source |
| eval_002 | Llama 3.1 是否公开模型权重并允许商用？ | Ollama, IBM | uncertain | 未召回 Meta / llama.com / Hugging Face 官方源；仍有版本/范围错位风险 |
| eval_003 | OpenAI 最近是否发布了新的语音模型？ | TMTPost, OpenAI | uncertain | 命中一个 `openai.com` 页面，但 source type 仍为 `unknown`，且是否为发布源不足 |
| eval_004 | RTX 5070 Ti 是否是 16GB 显存？ | Zhihu, ZFrontier | uncertain | 有 16GB 支持性摘录，但未命中 NVIDIA 或板卡厂商规格源 |
| eval_005 | 美国 SEC 是否发布过关于比特币现货 ETF 的批准公告？ | Securities Times, Caixin | unsupported | 缺 SEC 官方源；二手媒体进入最终 sources；claim scope 被误判为 oppose |

---

# 3. 核心结论

第二轮比第一轮有进步：eval_001 不再落到 Zhihu/Reddit，eval_002 不再落到 CSDN/QbitAI。但主要瓶颈仍然不是 scorer、aggregator 或 answer constraints，而是官方/一手来源没有稳定进入最终 evidence package。

当前系统在弱来源下保持 `uncertain`、`unsupported`、`cautious` 是合理的。不能因为答案不够自信就调高 scorer，也不能放宽 aggregator。更应该先让 SearchPlanner 和候选筛选把官方来源找进来，再让 evidence_extractor 对 claim scope 做更严格保护。

---

# 4. 必须覆盖样本结论

## eval_001: GPT-4.1 / OpenAI 官方源

脱敏结果中最终 sources 为：

- `azure.microsoft.com`
- `openrouter.ai`

没有 OpenAI 官方源进入最终 sources。

Azure 可以是 GPT-4.1 在 Azure AI Foundry / GitHub developer 场景下的发布或集成信息来源，但它不是 OpenAI primary source。OpenRouter 是第三方模型路由/价格/基准信息来源，也不是 OpenAI primary source。

因此，eval_001 的主要问题是 OpenAI 官方源召回失败，不能把 Azure 或 OpenRouter 当作“OpenAI 发布该模型”的一手证据。当前输出保持 `uncertain` 和 `must_disclose_uncertainty=true` 是合理的。

## eval_002: Llama 3.1 官方源与版本错位

脱敏结果中最终 sources 为：

- `ollama.com`
- `ibm.com`

没有 Meta、`llama.com`、Hugging Face 或 ModelScope 官方模型源进入最终 sources。

Ollama 和 IBM 可以提供有用背景，但不是 Meta / Llama 官方发布、权重、许可证的一手来源。证据中出现 “Llama 3.1 is a new state-of-the-art model from Meta” 和 “405B” 等相关内容，但仍不足以替代官方模型卡、官方 license 或 Meta 发布页。

本样本仍有版本/范围错位风险：证据可能覆盖 Llama 3.1 系列、某个规模、输出使用许可或媒体语境下的 “open source” 表述，但 claim 需要分别回答权重公开、商用许可、训练代码、训练数据和严格开源含义。当前 `model_weights` 仍为 `unsupported`，`license` 和 `interpretation` 为 `uncertain`，说明 answer constraints 没有过度放行。

## eval_003: OpenAI 语音模型发布源

脱敏结果中最终 sources 为：

- `tmtpost.com`
- `openai.com`

本样本命中了一个 `openai.com` source，但该 source title 为“应对合成语音的挑战与机遇”，source type 被分类为 `unknown`，并不能从脱敏记录中确认它就是“新语音模型发布”的官方发布源。

问题不是系统完全没有触达 OpenAI 域名，而是：

- SearchPlanner 没有稳定优先定位 OpenAI 官方发布/新闻/博客页面。
- source_classifier 未识别 `openai.com` 的官方来源类型。
- evidence 来自 fallback snippet，缺少正文级确认。

因此，`overall_status=uncertain`、`allowed_tone=cautious` 是合理的。

## eval_004: RTX 5070 Ti 显存规格源

脱敏结果中最终 sources 为：

- `zhuanlan.zhihu.com`
- `zfrontier.com`

证据摘录都支持 “16GB”，但未命中 NVIDIA 官方规格页、AIC 板卡厂商产品规格页或零售官方参数页。Zhihu 是社区来源，ZFrontier 当前为 `unknown`。对于产品参数问题，二手评测/社区内容可以作为补充，但不应替代厂商/规格源。

当前结果保持 `uncertain` 合理。问题主要在产品信息类 SearchPlanner 缺少厂商/规格源偏置，以及 provider 候选扩展/过滤没有把官方规格源排进最终 sources。

## eval_005: SEC 比特币现货 ETF/ETP

脱敏结果中最终 sources 为：

- `stcn.com`
- `finance.caixin.com`

没有 SEC 官方源进入最终 sources，且两个最终 sources 都是二手媒体。对于 policy/legal 类问题，SEC 官方公告、order、press release、statement 或 `sec.gov` 页面应优先于媒体转述。

本样本还暴露了 evidence_extractor 的 claim-scope confusion：

- Securities Times 摘录讨论的是 SEC X/Twitter 账号被盗和未授权推文，不等于最终是否发布过批准公告。
- Caixin 摘录称 SEC 批准现货比特币 ETP 上市，但并未批准或认可比特币。这句话对“SEC 是否发布过关于比特币现货 ETF/ETP 的批准公告”应至少是支持或部分支持，而不是 `oppose`。

“SEC 批准 ETP 上市但不认可比特币”区分的是批准上市产品与认可底层资产，不应被判成反对“发布批准公告”。因此，`unsupported` 的直接原因不是缺乏任何支持性信息，而是二手来源质量弱叠加 evidence_extractor 将 claim scope 判错。

---

# 5. 分析维度

## SearchPlanner 问题

SearchPlanner 仍缺少按问题类型生成的一手来源偏置：

- `ai_model_info`: 应优先生成 OpenAI、Meta、llama.com、Hugging Face、model card、license 等查询。
- `tech_news`: 应优先生成官方博客、发布页、news/research/product update 查询。
- `product_info`: 应优先生成 NVIDIA、板卡厂商、规格页、product specification 查询。
- `policy_legal`: 应优先生成 `site:sec.gov`、approval order、statement、press release 等查询。

当前多个样本都显示 provider 可以返回相关内容，但最终没有稳定拿到最权威的官方源。

## Provider candidate expansion 问题

`max_sources=2` 用作最终 response 限制是合理的，但如果同时限制 provider 候选数量，会过早截断官方源。真实 provider 应先拉取更多候选，再由 CSL 做 source classification、ranking 和 filtering。

第二轮不能证明 Tavily 本身无法召回官方源，只能说明当前候选进入最终 sources 的策略不够稳。下一步应分离 provider candidate count 与 response `max_sources`。

## Source-type ranking/filtering 问题

最终 sources 中出现 Azure、OpenRouter、Ollama、IBM、TMTPost、Zhihu、ZFrontier、Securities Times、Caixin，说明当前最终来源选择主要受 provider 排序影响，未充分按 source type 和 primary-source preference 重排。

需要在不改 schema 的前提下，让官方源、厂商规格源、政府/监管源优先进入最终 `sources`；媒体和社区来源可以保留为补充，但不应挤掉一手来源。

## Source_classifier 问题

`openai.com` 在 eval_003 中被分类为 `unknown`。这会导致官方 OpenAI 页面无法获得应有的 source type 和 base reliability。

同时，`azure.microsoft.com`、`openrouter.ai`、`ollama.com`、`ibm.com` 不应被误升为目标实体的一手来源。分类应能表达“相关但非目标实体 primary source”的事实，至少在 ranking/filtering 阶段不能把它们当作 OpenAI 或 Meta 官方源。

SEC 类问题也要求 `sec.gov` 保持政府/监管官方源优先；本轮没有命中 SEC，因此不能从结果中验证分类是否生效。

## Evidence_extractor claim-scope 问题

eval_005 是最明确的 evidence_extractor 问题。抽取器把“批准 ETP 上市但不认可比特币”判为 `oppose`，说明它没有把 claim 的核心谓词限定为“是否发布/批准 ETF/ETP 上市公告”，而是被“未认可比特币”带偏。

eval_002 也有较弱的 claim-scope 风险：Llama 3.1 系列、405B、输出使用许可、商业使用、严格开源含义是不同命题，不能互相替代。

下一步应增强 claim-aware support/oppose 判定，而不是简单提高 relevance score。

## Answer_constraints 是否合理

本轮 answer constraints 整体合理：

- 所有样本都保持 `allowed_tone=cautious`。
- 弱来源或缺官方源时 `must_disclose_uncertainty=true`。
- 没有让系统在二手来源、fallback snippet 或错位证据下 confident answer。

eval_005 的 `unsupported` 过弱来自 evidence support_type 判错和缺官方源，不是 answer_constraints 过严。当前不应修改 answer constraint builder 来掩盖上游证据错误。

---

# 6. 不应立即做的事

- 不要建议调高 scorer。
- 不要建议放宽 aggregator。
- 不要接 Brave / SerpAPI 来绕过当前问题。
- 不要因为单个样本大改系统。
- 不要把 Azure/OpenRouter 当作 OpenAI primary source。
- 不要把 Ollama/IBM 当作 Meta/Llama primary source。
- 不要把媒体转述当作 policy/legal 类问题的最终权威来源。
- 不要修改 schema、MCP、依赖或测试范围外代码来处理本轮 findings。

---

# 7. 下一轮最多 3 个开发任务

## Task 1: 增强 SearchPlanner 的官方来源查询模板

为什么现在做：

五个样本都直接或间接暴露官方/一手来源召回不足。这是当前最稳定复现的瓶颈，先修它比调 scorer 或 aggregator 更安全。

应改文件：

- `app/services/search_planner.py`

应补测试：

- `tests/services/test_search_planner.py`
- 覆盖 `ai_model_info` 的 OpenAI / Meta / Llama / Hugging Face / license 查询。
- 覆盖 `tech_news` 的 OpenAI 官方发布源查询。
- 覆盖 `product_info` 的 NVIDIA / manufacturer / specs 查询。
- 覆盖 `policy_legal` 的 `site:sec.gov` / approval order / statement 查询。

明确不做：

- 不新增搜索 provider。
- 不发真实网络请求。
- 不修改 request/response schema。
- 不把 Tavily 设为默认 provider。

## Task 2: 分离 provider candidate expansion 与最终 max_sources，并做 source-type ranking

为什么现在做：

`max_sources=2` 作为最终输出限制合理，但不应让真实 provider 只给两个候选就结束。需要先拿更多候选，再按官方/一手来源优先筛选，避免二手媒体或社区内容挤掉权威源。

应改文件：

- `app/services/trusted_search_service.py`
- `app/services/search_adapter.py`
- `app/services/search_provider_normalizer.py`（如候选归一化影响排序）
- `app/services/source_classifier.py`（如 ranking 需要使用分类结果）

应补测试：

- `tests/services/test_trusted_search_service.py`
- `tests/services/test_search_adapter.py`
- `tests/services/test_search_provider_normalizer.py`
- 构造 provider 返回 5-10 个候选、最终 response 仍只返回用户 `max_sources` 的测试。
- 验证官方域名优先进入最终 sources，二手媒体/社区不应在有官方源时挤占名额。
- 验证 provider failure 仍受控返回 degraded package。

明确不做：

- 不修改 schema。
- 不新增依赖。
- 不引入数据库、缓存或历史信誉系统。
- 不接 Brave / SerpAPI。

## Task 3: 增强 evidence_extractor 的 claim-scope support/oppose 判定

为什么现在做：

eval_005 明确显示 “SEC 批准 ETP 上市但不认可比特币” 被错误判为 `oppose`。这是 claim-scope confusion，不是 scoring 问题。若不修，后续即使命中官方 SEC 源，也可能把限定性声明误读成反对证据。

应改文件：

- `app/services/evidence_extractor.py`

应补测试：

- `tests/services/test_evidence_extractor.py`
- 增加 policy/legal 样本：批准 ETP/ETF 上市但不认可底层资产，应为 `support` 或 `partial`，不能为 `oppose`。
- 增加 unauthorized tweet 与 final approval notice 区分测试。
- 增加 Llama 3.1 权重、license、严格开源含义分离测试，避免跨 claim 套用证据。

明确不做：

- 不用 LLM 替代当前 deterministic fallback。
- 不提高 scorer。
- 不放宽 aggregator。
- 不让抽取器从来源标题或主观推断中编造 evidence。

---

# 8. 当前决策

第二轮应优先修“找到一手来源”和“不要把限定性声明误判为反对证据”。系统保持谨慎输出是正确行为。下一轮开发应小步推进：先改 SearchPlanner，再处理候选扩展与来源排序，随后补 evidence_extractor 的 claim-scope guard。
