# Tavily Real-world Eval Findings 003

版本：v0.2.5 findings  
文档类型：Tavily real-world eval 第三轮质量问题汇总  
范围：基于 `docs/evals/tavily_real_world_eval_run_003.md` 的脱敏记录

---

# 1. 记录边界

本文件只根据 `docs/evals/tavily_real_world_eval_run_003.md` 总结，不读取临时 JSON、不包含 API key、Authorization header、raw provider payload 或完整网页正文。

本轮重点不是继续证明 Tavily 能联网，而是判断 v0.2.5 的 source-type ranking/filtering 是否改善 final sources，并识别下一轮最小开发任务。

---

# 2. 核心结论

v0.2.5 source-type ranking/filtering 已经生效。`ai_model_info` 两个样本中，final sources 从 run_002 的 `unknown` 来源前移到 Hugging Face / GitHub 等 primary source type：

- eval_001: final sources 为两个 `huggingface.co`，均被标为 `official_model_card`。
- eval_002: final sources 为 `huggingface.co` + `github.com`，分别为 `official_model_card` 和 `source_code_repo`。

但新的核心问题也很明确：`source_type` 不等于目标实体的官方来源。

- `official_model_card` 不等于 OpenAI 官方源。
- `source_code_repo` 不等于目标组织控制的 repo。
- `huggingface.co` 或 `github.com` 的平台级 source type 只能说明来源形态较强，不能证明它属于 OpenAI、Meta、Llama、NVIDIA 或 SEC 等目标实体。

因此，v0.2.5 解决了“让强 source type 更靠前”的问题，但暴露了 entity/domain ownership guard 缺口。

---

# 3. Eval 级发现

## eval_001: GPT-4.1 / OpenAI

Observed:

- final sources 均为 `huggingface.co`。
- 两个 source 都被分类为 `official_model_card`，`base_reliability=0.88`，`is_primary_source=true`。
- claim `source_code` 为 `likely`，claim `training_data` 为 `confirmed`。

Finding:

这不是可信改善。GPT-4.1 是否由 OpenAI 发布，理想 primary source 应是 OpenAI 官方发布页、OpenAI docs、OpenAI blog 或 OpenAI API 文档，而不是任意 Hugging Face 页面。

`source_code=likely` 和 `training_data=confirmed` 不应视为真实质量提升，因为这些结论来自与目标实体不对齐的伪官方源。该样本暴露的是 source-type ranking 的副作用：平台型官方来源被排前，但缺少目标实体所有权校验。

## eval_002: Llama 3.1 / Meta

Observed:

- final sources 从 run_002 的 Ollama / IBM 变为 Hugging Face / GitHub。
- source types 分别为 `official_model_card` 和 `source_code_repo`。

Finding:

这是部分改善。相比 Ollama / IBM，Hugging Face / GitHub 更接近模型卡和代码仓库这类一手材料形态。

但仍不能完全确认，因为还需要判断这些页面是否属于 Meta / Llama 官方实体控制。对于 Llama 3.1，必须区分官方 Meta/Llama repo、官方模型卡、镜像、社区页面和第三方整理页。

## eval_003: OpenAI 语音模型

Observed:

- final sources 包含 `openai.com`。
- `openai.com` 仍被 `source_classifier` 标为 `unknown`，`base_reliability=0.3`，`is_primary_source=false`。

Finding:

source_classifier 官方域名规则仍有缺口。OpenAI 官方域名没有被识别为 `official_docs` 或 `official_blog` 等更合适的 source type，导致 ranking 无法稳定优先官方 OpenAI source。

## eval_004: RTX 5070 Ti 显存

Observed:

- final sources 仍是 Zhihu / Reddit。
- 两个 source 都是 `community_forum`。

Finding:

product_info 官方候选召回不足。对于显存规格问题，理想来源应是 NVIDIA、板卡厂商规格页、官方产品页或官方零售参数页。ranking 不能排序不存在的 NVIDIA / 厂商规格源。

## eval_005: SEC 比特币现货 ETF/ETP

Observed:

- final sources 仍未命中 `sec.gov`。
- final sources 是非 SEC `unknown` 域名。
- 一个看似描述 SEC 正式批准 ETF/ETP 上市的证据被标为 `oppose`。

Finding:

policy/legal 官方候选召回不足仍存在。对于 SEC 问题，`sec.gov` 的 order、statement、press release 或 official notice 应优先进入候选池。

此外，evidence_extractor 仍有 claim-scope confusion：描述批准公告或批准上市的证据，不应仅因上下文包含限制、风险、败诉背景或“不认可比特币”之类限定表达，就被误判为反对“SEC 是否发布批准公告”。

---

# 4. 分析维度

## Source-type ranking 已解决的问题

v0.2.5 已经能在候选存在时让强 source type 进入 final sources。run_003 的 eval_001 和 eval_002 清楚显示，`official_model_card`、`source_code_repo` 能压过 run_002 中的 `unknown` 第三方来源。

这说明 ranking 机制本身有效，不应回退，也不应通过调低 source-type ranking 来掩盖 entity mismatch。

## Source_classifier 仍缺的问题

`openai.com` 仍被标为 `unknown`。这会让 OpenAI 官方页面在 tech_news / ai_model_info 等问题中失去应有优先级。

source_classifier 还缺少更细的官方域名规则，例如 OpenAI 官方域、厂商域、政府/监管域的稳定识别。当前只靠平台域名如 Hugging Face/GitHub 会造成“平台 source type 强，但目标实体未确认”的误升。

## SearchPlanner / official query recall 仍缺的问题

product_info 和 policy_legal 样本没有召回官方候选：

- eval_004 没有 NVIDIA 或厂商规格页。
- eval_005 没有 `sec.gov`。

这说明 SearchPlanner 的官方 query recall 仍需要增强。ranking 只能处理候选池已有内容，不能凭空生成官方 source。

## Entity/domain ownership guard 缺口

这是第三轮最重要的新问题。

需要在 source promotion 或 final source ranking 阶段加入目标实体所有权判断：

- OpenAI 问题中，OpenAI 官方域应优先于 Hugging Face 用户页。
- Meta/Llama 问题中，Meta/Llama 官方组织、官方 repo、官方模型卡应优先于第三方镜像。
- GitHub repo 需要判断 owner 是否为目标组织或可信官方组织。
- Hugging Face model card 需要判断 namespace 是否为目标组织或官方发布主体。

第一版 guard 不需要复杂知识图谱，可以从 query/entity、domain、path namespace、title keyword 做保守规则。

## Evidence_extractor claim-scope 问题

eval_005 延续 run_002 的问题：批准公告相关 evidence 仍可能被误判为 `oppose`。

抽取器需要区分：

- 是否发布/批准 ETF/ETP 上市公告；
- 是否认可或背书比特币；
- 是否提示投资风险；
- 是否讨论账号被盗或未经授权推文。

这些是不同 claim scope，不能互相替代。

## Answer_constraints 是否合理

本轮 answer constraints 整体合理：

- 所有样本仍为 cautious tone。
- 缺官方源或存在实体不对齐风险时，`can_answer_confidently=false`。
- weak / uncertain evidence 下没有放行高确定性回答。

eval_001 的 `partially_confirmed` 和部分 claim 高置信度暴露的是上游 source ownership 与 evidence scope 问题，不是 answer_constraints 应该放宽或收紧的问题。

---

# 5. 不应立即做的事

- 不要建议调高 scorer。
- 不要建议放宽 aggregator。
- 不要接 Brave / SerpAPI。
- 不要因为单个样本大改系统。
- 不要把 Hugging Face 平台页自动当作 OpenAI 官方源。
- 不要把 GitHub repo 自动当作目标组织控制的 repo。
- 不要修改 schema、MCP、TavilyProvider 或依赖来处理本轮 findings。

---

# 6. 下一步最多 3 个开发任务

## Task 1: 增加 entity-aware official source guard

为什么现在做：

source-type ranking 已经生效，下一瓶颈从“强 source type 是否靠前”变成“强 source type 是否属于目标实体”。eval_001 明确显示 `official_model_card` 可以误升非 OpenAI 官方页，导致 claim 置信度看起来改善但实际不可信。

应改文件：

- `app/services/trusted_search_service.py`
- 如需独立 helper，可新增 `app/services/source_ranker.py`
- 必要时复用 `app/services/source_classifier.py` 的分类结果，但不要改 schema

应补测试：

- `tests/services/test_trusted_search_service.py` 或新增 `tests/services/test_source_ranker.py`
- OpenAI query 中，`openai.com` source 应优先于 Hugging Face 用户页。
- GPT-4.1 query 中，Hugging Face 非 OpenAI namespace 不应被当作目标 primary source。
- Llama query 中，Meta/Llama official repo 或 namespace 应优先于第三方 mirror。
- 同分仍保持 provider 原顺序。

明确不做：

- 不引入组织知识库或数据库。
- 不新增 schema 字段。
- 不引入 LLM reranker。
- 不调高 scorer 或放宽 aggregator。

## Task 2: 补全 source_classifier 官方域名规则

为什么现在做：

eval_003 中 `openai.com` 仍为 `unknown`，直接削弱官方 OpenAI source 的 ranking 和 reliability。这个缺口比继续调 ranking 权重更基础。

应改文件：

- `app/services/source_classifier.py`
- `app/policies/source_policy.yml` 仅在现有 source type 不足时谨慎调整；优先复用已有 `official_docs` / `official_blog`

应补测试：

- `tests/services/test_source_classifier.py`
- `openai.com` 官方 docs/blog/research/news 页面应分类为官方来源。
- `platform.openai.com/docs` 应分类为 `official_docs`。
- 非官方第三方 OpenAI 讨论页不能因为 title 含 OpenAI 被升为官方。

明确不做：

- 不把所有提到 OpenAI 的页面标为官方。
- 不新增 schema。
- 不改变 TavilyProvider。
- 不做复杂来源历史信誉系统。

## Task 3: 增强 policy_legal / product_info 官方 query recall

为什么现在做：

eval_004 和 eval_005 说明，如果候选池没有官方源，source-type ranking 无法发挥作用。product_info 需要厂商/规格源，policy_legal 需要政府/监管源。

应改文件：

- `app/services/search_planner.py`

应补测试：

- `tests/services/test_search_planner.py`
- product_info 的 RTX / GPU / 显存问题应生成 NVIDIA、manufacturer、specification、product page 相关 query。
- policy_legal 的 SEC / ETF / ETP 问题应生成 `site:sec.gov`、approval order、statement、press release 相关 query。
- query budget 不应破坏现有 strictness 行为。

明确不做：

- 不接 Brave / SerpAPI。
- 不发真实网络请求。
- 不新增 provider。
- 不修改 response schema。

---

# 7. 当前决策

第三轮结论是：v0.2.5 source-type ranking/filtering 方向正确并已生效，但下一步必须补 entity/domain ownership guard。否则系统会把“平台上看起来像一手材料的页面”误当成“目标实体官方来源”。

下一轮应先修 entity-aware official source guard，再补 OpenAI 等官方域名分类，最后增强 product_info / policy_legal 的官方 query recall。Scorer、aggregator 和 provider 选择不是本轮瓶颈。
