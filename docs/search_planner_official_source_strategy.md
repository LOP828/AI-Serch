# SearchPlanner Official Source Strategy

版本：v0.2.3 strategy draft  
文档类型：SearchPlanner 官方来源优先查询策略设计  
当前状态：设计文档，不包含代码实现

---

# 1. 背景与当前问题

CSL 当前已经完成 v0.2 Tavily opt-in 主链路：

```text
/api/v1/trusted-search
  -> build_search_adapter()
  -> TrustedSearchService
  -> SearchAdapter
  -> TavilyProvider, only when explicitly opted in
```

默认 provider 仍为 `static`。默认 `pytest` 不访问真实网络。Tavily 只能通过显式配置启用：

```text
CSL_SEARCH_PROVIDER=tavily
CSL_SEARCH_ALLOW_NETWORK=true
CSL_SEARCH_API_KEY=<temporary local value>
```

`eval_001` 和 `eval_002` 显示，真实 Tavily 搜索进入主链路后，召回质量仍不稳定：

- `GPT-4.1 是否是 OpenAI 发布的模型？` 只返回 Zhihu / Reddit 等社区来源，缺少 OpenAI 官方来源。
- `Llama 3.1 是否公开模型权重并允许商用？` 返回 CSDN / QbitAI 等弱二手来源，并混入旧 LLaMA 或无关模型证据。
- `SourceClassifier` 没有把弱来源误判为官方来源。
- `ReliabilityScorer` 没有明显过度信任弱来源。
- `ClaimAggregator` 和 `answer_constraints` 保持 `uncertain` / cautious，是合理行为。

因此，当前主要问题不是 scorer 或 aggregator 不够强，而是 `SearchPlanner` 缺少 official-source-biased query strategy。下一阶段应先在 query 层提高候选来源质量，而不是通过提高分数掩盖弱来源或错位证据。

本轮核验还发现：

- `docs/evals/tavily_real_world_eval_run_002.md` 当前不存在；`eval_002` 记录在 `docs/evals/tavily_real_world_eval_run_001.md` 内。
- `app/policies/question_policy.yml` 当前不存在。
- `.uv-venv` 和 `.uv-cache` 是上一轮为绕过本机 uv cache 权限创建的临时产物；本阶段不删除，只记录。

---

# 2. 设计目标

本策略只覆盖 `ai_model_info` 问题类型的 SearchPlanner 查询设计。

目标：

- 对 `ai_model_info` 类型优先召回官方来源。
- 在 query 层先提高候选来源质量。
- 优先找到官方模型卡、官方 GitHub/GitLab repo、论文、官方博客、官方文档、许可证页面。
- 保留完整 entity/version 字符串，减少旧版本或相邻版本材料混入。
- 不通过调高 `relevance_score`、`final_score` 或 claim aggregation 阈值来掩盖弱来源问题。
- 保持默认 `static` provider 和 mock tests 稳定。
- 保持 Tavily 真实网络调用继续显式 opt-in。
- 不接 Brave / SerpAPI。
- 不接真实 LLM。
- 不修改 scorer / aggregator。

非目标：

- 不改变 `TrustedSearchService` 主链路。
- 不让 `TavilyProvider` 负责来源分类、证据抽取或评分。
- 不在本文档中实现 `EvidenceExtractor` entity/version guard。
- 不把 Tavily 设为默认 provider。

---

# 3. AI Model Info 的来源优先级

`ai_model_info` 的可信来源优先级应与 `source_policy.yml` 和 `source_classifier.py` 保持一致。

## P0: Official model card

优先域名：

- `huggingface.co`
- `modelscope.cn`

原因：

- 通常包含模型权重、模型卡、license、文件列表、使用限制。
- 当前 `SourceClassifier` 会归类为 `official_model_card`，基础可靠度为 `0.88`。

## P0: Source repo

优先域名：

- `github.com`
- `gitlab.com`

原因：

- 适合验证代码是否公开、训练代码是否公开、release/tag 是否存在。
- 当前会归类为 `source_code_repo`，基础可靠度为 `0.88`。

## P0: Paper / academic record

优先域名：

- `arxiv.org`
- `openreview.net`

原因：

- 适合验证论文、模型介绍、训练数据说明、实验细节。
- 当前会归类为 `academic_paper`，基础可靠度为 `0.90`。

## P1: Official docs / official blog

优先来源：

- 项目或公司官方网站。
- 官方博客。
- 文档路径，例如 `docs.*` 或 `/docs/`。
- 发布公告、model release、license page、terms page。

原因：

- 对发布事实、产品能力、许可证说明、官方限制最有价值。
- 当前 `SourceClassifier` 已能识别 `docs.` 或 `/docs/` 为 `official_docs`。
- 公司官方博客域名需要后续按 source policy 或 domain rules 扩展，但 query 策略可以先主动召回。

## P2: Trusted technical media

示例：

- 高质量技术媒体。
- 研究机构博客。
- 被广泛引用的二手技术报道。

原因：

- 可作为辅助来源，但不应替代官方模型卡、repo、论文或官方发布页。
- 后续可细分 `mainstream_media`、`expert_blog`、`tech_media`，但不是当前第一优先级。

## P3: Community / forum

示例：

- `reddit.com`
- `zhihu.com`
- `x.com`
- `twitter.com`

使用原则：

- 仅作为弱辅助来源。
- 可用于发现线索，但不能单独支撑高置信结论。
- 不能因为社区讨论提到某模型存在，就把 claim 聚合为 confirmed。

---

# 4. Query 策略设计

`SearchPlanner` 应围绕完整 `entity` 生成少量高价值 query family。对于 `ai_model_info`，query 设计应优先保留模型名和版本号，而不是只使用宽泛中文问题。

当前已有 suffix 类似：

```text
Hugging Face
GitHub
paper
arXiv
license
official
```

下一阶段应把这些 suffix 组织为明确的 query family，并根据 `strictness` 控制数量和偏向。

## 4.1 Exact entity query

目标：保留完整模型名，减少 provider 将 query 泛化到旧版本或无关同系列模型。

示例：

```text
"{entity}"
{entity}
```

适用：

- 所有 `ai_model_info` claim。
- balanced / strict / loose 都应保留。

## 4.2 Official query

目标：主动召回官方发布页、官方博客、官方文档。

示例：

```text
{entity} official
{entity} official release
{entity} official blog
{entity} official documentation
```

适用：

- `existence`
- `interpretation`
- 通用 fallback query family

## 4.3 Site-biased Hugging Face query

目标：优先召回模型卡和权重页面。

示例：

```text
{entity} Hugging Face
{entity} site:huggingface.co
"{entity}" site:huggingface.co
"{entity}" model card
```

适用：

- `existence`
- `model_weights`
- `license`
- `interpretation`

注意：

- `site:huggingface.co` 应保留完整 entity/version。
- 如果 entity 包含空格或点号版本，例如 `Llama 3.1`、`GPT-4.1`，quoted query 更重要。

## 4.4 Site-biased GitHub query

目标：优先召回源代码、训练代码、release repo。

示例：

```text
{entity} GitHub
{entity} site:github.com
"{entity}" site:github.com
{entity} source code
{entity} training code GitHub
```

适用：

- `source_code`
- `model_weights`
- `interpretation`

## 4.5 Paper / arXiv query

目标：召回论文、技术报告、训练数据描述。

示例：

```text
{entity} arXiv
{entity} paper
{entity} technical report
"{entity}" arXiv
"{entity}" paper
```

适用：

- `training_data`
- `existence`
- `interpretation`

## 4.6 License query

目标：验证商业使用、开源许可、使用限制。

示例：

```text
{entity} license
"{entity}" license
{entity} commercial use
{entity} license Hugging Face
{entity} license GitHub
```

适用：

- `license`
- `interpretation`

## 4.7 Model card query

目标：直接查找模型卡，而不是宽泛搜索新闻或社区讨论。

示例：

```text
{entity} model card
"{entity}" model card
{entity} model files
{entity} weights model card
```

适用：

- `existence`
- `model_weights`
- `license`

## 4.8 Version-specific query

目标：强制保留完整版本字符串，减少同系列错位。

示例：

```text
"{entity}"
"{entity}" official
"{entity}" Hugging Face
"{entity}" GitHub
"{entity}" license
"{entity}" model card
```

适用：

- 所有 `ai_model_info` claim。

原则：

- 当 entity 含数字版本、点号版本、连字符版本时，优先生成 quoted exact query。
- 不要把 `Llama 3.1` 简化为 `Llama`。
- 不要把 `GPT-5.1` 简化为 `GPT-5`。

---

# 5. Exact-version / Entity Guard 思路

AI 模型信息对实体和版本高度敏感。模型同名不同版本之间，权重公开、license、训练数据、代码开放情况可能完全不同。

必须避免：

- `MiroThinker 1.7` 被 `MiroThinker 1.6` 或 `MiroThinker 2.0` 的证据替代。
- `GPT-5.1` 被 `GPT-5` 或 `GPT-5.5` 的材料替代。
- `Llama 3.1` 被旧 `LLaMA`、`LLaMA-13B`、`Llama 2` 或无关 open model 材料替代。

SearchPlanner 层原则：

- query 应优先保留完整 entity/version 字符串。
- quoted exact entity query 应出现在 high-value query budget 中。
- site-biased query 也应使用完整 entity/version，而不是宽泛系列名。
- 对包含点号、连字符、大小写混合的模型名，应尽量保留原始形式。

EvidenceExtractor 后续原则：

- 后续需要 entity/version guard。
- 证据文本只提到相邻版本、旧版本、同系列泛称时，应降权或剔除。
- 本阶段只设计 SearchPlanner，不实现 extractor guard。

---

# 6. max_sources 和 Query Budget 建议

真实 provider 下不能无限扩 query。多 claim、多 query 会带来成本、延迟和 rate limit 风险。下一阶段应把 query budget 作为 SearchPlanner 策略的一部分。

当前 `TrustedSearchService` 虽然生成 `search_plan`，但实际 `SearchAdapter.search()` 仍只接收原始 `request.query`。因此，本策略分为两层：

- SearchPlanner 先生成更好的 `search_plan`，供 API response 和后续实现使用。
- 后续如要让 adapter 消费多条 query，需要单独设计 provider candidate expansion，不在本文档实现。

## strict

目标：优先官方、一手、精确版本。

建议 query family：

- quoted exact entity
- official query
- site-biased Hugging Face / ModelScope
- site-biased GitHub / GitLab
- paper / arXiv
- license, only for license or interpretation claim

建议数量：

```text
每个 claim 3-5 条 query
尽量使用 site-biased 和 quoted exact query
避免 broad community query
```

## balanced

目标：保持官方优先，同时兼顾召回。

建议 query family：

- exact entity query
- official query
- Hugging Face query
- GitHub query
- paper / arXiv query
- license 或 model card query

建议数量：

```text
每个 claim 4-6 类高价值 query
优先 official / model card / repo / paper / license
```

## loose

目标：允许更宽召回，但仍不要让社区来源优先于官方来源。

建议 query family：

- balanced 的全部核心 query
- broader query，例如 `{entity} release`、`{entity} announcement`
- trusted technical media query

建议数量：

```text
每个 claim 5-8 条 query
可保留 broader query
community/forum 不作为主动优先 query
```

## Provider candidates 与 response max_sources

`eval_001` 和 `eval_002` 都使用 `max_sources=2`，这可能过早截断真实 provider 结果。后续可考虑拆分：

```text
provider_max_candidates = 5-10
response max_sources = user requested max_sources
```

流程设想：

```text
provider 返回更多候选
CSL 根据 source type、domain、exact entity match 做 filtering / ranking
最终 response 仍尊重 request.max_sources
```

该策略需要后续代码设计，不在本文档实现。

---

# 7. 与现有模块的边界

## SearchPlanner

职责：

- 生成更好的 `queries`。
- 生成 `preferred_source_types`。
- 对 `ai_model_info` 使用 official-source-biased query family。
- 保留 exact entity/version 字符串。

不负责：

- 直接调用 Tavily。
- 做 URL 去重。
- 分类 source type。
- 抽取 evidence。
- 计算 reliability score。
- 聚合 claim status。

## SearchAdapter / TavilyProvider

职责：

- `SearchAdapter` 继续返回 normalized search results。
- `TavilyProvider` 只负责真实 provider 请求、错误归一化、payload 归一化。
- Tavily 真实网络调用继续 opt-in。

不负责：

- 根据弱来源自行调分。
- 伪造 fallback 为真实结果。
- 生成 evidence 或 answer constraints。

## SourceClassifier

职责：

- 根据 URL/domain 分类来源。
- 继续识别 `huggingface.co`、`modelscope.cn`、`github.com`、`gitlab.com`、`arxiv.org`、`openreview.net`、`*.gov`、`reddit.com`、`zhihu.com` 等。
- 继续提供 `base_reliability` 和 `is_primary_source`。

不负责：

- 生成搜索 query。
- 修复 provider 召回不足。

## ReliabilityScorer

职责：

- 按 evidence relevance、source base score、primary source factor、recency factor 打分。
- 继续保持 explainable scoring。

不应做：

- 通过提高弱来源分数掩盖召回问题。
- 让社区来源或 unknown 来源获得高置信结论。

## ClaimAggregator

职责：

- 基于已有 scored evidence 聚合 claim status。
- 当证据不足、弱或冲突时保持 `uncertain`、`unsupported`、`conflicting`。

不应做：

- 因为搜索召回不足而强行 `confirmed`。
- 用聚合规则弥补官方来源缺失。

## EvidenceExtractor

职责：

- 从 source text/snippet 中抽取绑定 claim 的短证据。

后续需要：

- entity/version guard。
- 对相邻版本、旧版本、无关模型证据降权或剔除。

本阶段不做：

- 不实现 extractor guard。
- 不接真实 LLM。

---

# 8. 后续代码落地建议

下一阶段可以修改：

- `app/services/search_planner.py`
- `tests/services/test_search_planner.py`

可能新增：

- `ai_model_info` query family fixture。
- exact-version query cases。
- strict / balanced / loose query budget cases。
- regression cases for:
  - `GPT-4.1 是否是 OpenAI 发布的模型？`
  - `Llama 3.1 是否公开模型权重并允许商用？`
  - `MiroThinker 1.7 是不是开源模型？`

建议测试断言：

- `ai_model_info` search plan 包含 quoted exact entity query。
- balanced 至少包含 official、Hugging Face、GitHub、arXiv/paper、license/model card 中的高价值 query。
- strict 更偏 `site:huggingface.co`、`site:github.com`、official query。
- loose 可包含 broader query，但不应移除 official-source-biased query。
- preferred source types 继续优先 `official_model_card`、`source_code_repo`、`academic_paper`、`official_docs`、`official_blog`。

本轮不修改代码。本文档只为下一阶段实现提供边界。

---

# 9. 验收标准

文档层面的验收标准：

- 明确 `ai_model_info` 的 official-source-biased query 策略。
- 明确来源优先级：official model card、source repo、paper、official docs/blog、trusted technical media、community/forum。
- 明确 strict / balanced / loose 的 query budget 和差异。
- 明确 exact-version query 原则。
- 明确 `EvidenceExtractor` entity/version guard 是后续阶段，不在本文档实现。
- 明确不改 scorer / aggregator 来掩盖召回问题。
- 明确默认 static provider、mock tests、Tavily opt-in 边界不变。
- 明确下一阶段代码改动范围只应集中在 `app/services/search_planner.py` 和 `tests/services/test_search_planner.py`。

---

# 10. 禁止事项

下一阶段实现前仍应遵守：

- 不要把 Tavily 设为默认 provider。
- 不要让默认测试访问真实网络。
- 不要读取、申请、写入 API key。
- 不要记录 Authorization header。
- 不要接 Brave / SerpAPI。
- 不要接真实 LLM。
- 不要新增数据库。
- 不要新增前端。
- 不要修改 scorer / aggregator 来制造更高置信度。
- 不要让 provider 层承担 evidence、scoring、aggregation 或 answer constraints 职责。
