# Critical Search Layer Search Provider Integration Plan

版本：v0.1 后续接入方案
文档类型：真实搜索 provider 接入边界 / 配置 / 降级 / 测试策略
当前状态：设计文档，不包含业务代码实现

---

# 1. 背景与目标

Critical Search Layer 当前已经完成 v0.1 mock/static MVP 闭环：

```text
query
  -> question_classifier
  -> claim_decomposer
  -> search_planner
  -> StaticSearchAdapter / MockSearchAdapter
  -> source_classifier
  -> page_fetcher fallback
  -> evidence_extractor
  -> reliability_scorer
  -> claim_aggregator
  -> conflict_detector
  -> answer_constraint_builder
  -> TrustedSearchResponse
```

当前系统不依赖真实搜索 API、真实 LLM、数据库或前端。搜索结果来自
`StaticSearchAdapter` / `MockSearchAdapter`，页面抓取默认可 fallback 到搜索摘要，测试稳定且不访问真实网络。

下一阶段不要立刻接入真实搜索 API。应先固定真实搜索 provider 的接入边界、配置项、错误降级、quota/rate limit 策略和 mock 测试策略。真实 provider 只能替换“搜索候选来源”这一层，不能把来源可信度评分、证据抽取、claim 聚合或 answer constraints 逻辑塞进 provider 层。

---

# 2. Provider 选型对比

本方案对比 Tavily、Brave Search API、SerpAPI。以下判断基于 2026-05-07 可见的官方文档和产品说明，真实接入前应再次核对价格、额度和服务条款。

| 维度 | Tavily | Brave Search API | SerpAPI |
|---|---|---|---|
| 搜索结果质量 | 面向 AI 应用做相关性排序和内容处理，适合 agent 快速拿候选资料；但其排序和抽取有 provider 自身加工，需避免把它当最终证据。 | 使用 Brave 自有 Web index，覆盖面和新鲜度是主要卖点；适合需要相对通用、独立 Web 搜索的场景。 | 主要封装 Google/Bing/Yahoo 等 SERP 结构，覆盖传统搜索结果和 rich snippets；结果质量依赖底层搜索引擎和 SERP 解析。 |
| AI Agent / RAG / 搜索增强适配 | 强。官方定位就是面向 AI applications，返回 `content`、可选 raw content、search depth 等参数。 | 强。官方明确面向 chatbots、agents、RAG，并提供 LLM context / extra snippets 等能力。 | 中。结构化 SERP 适合通用搜索接入，但不是专门为 CSL 的 evidence pipeline 设计；需要更多字段清洗。 |
| 返回字段结构映射难度 | 低。`title`、`url`、`content`、`published_date` 可直接映射。 | 低到中。Web results 通常包含 title/url/description 或 snippets，但不同垂直 endpoint 的字段需要统一。 | 中。`organic_results` 中 `title`、`link`、`snippet`、`date` 可映射，但 rich results、ads、knowledge graph 等需要过滤。 |
| 成本与免费额度风险 | 官方文档显示有免费 credits，basic search 消耗较低；advanced search、extract/crawl 会增加 credit 消耗。风险是误用 advanced/raw content 导致成本上升。 | 官方页面显示 Search 约按请求计费，并有月度免费 credit；免费 credit 可能要求账号/支付验证。风险是高 QPS 或多 claim 查询放大请求数。 | 免费额度较低，付费套餐按月搜索量和 hourly throughput 限制；多 claim 查询容易快速消耗月额度。 |
| rate limit / quota 风险 | credit 模型清晰，需在 CSL 内部按 query 数量预估消耗；advanced 搜索会翻倍消耗。 | 有较高 Search capacity 描述，但具体账号额度仍要按 dashboard/plan 控制。 | 套餐有月搜索量和 hourly throughput；免费层很容易被 E2E 或开发调试耗尽。 |
| API 稳定性 | 专门 API，直接 HTTP/SDK 都可用；仍需处理 401/429/5xx。 | 独立搜索 API，文档化 endpoint 和认证方式；仍需处理垂直结果差异。 | 成熟 SERP API，字段丰富；但 SERP 形态复杂，字段兼容和过滤成本更高。 |
| 可测试性 | 高。返回结构较简单，适合 fake payload 和 fixture。 | 高。可用 fake Web results 测试 normalized mapping。 | 中。payload 类型多，测试样本需要覆盖 organic/rich/empty/error 状态。 |
| 长期可替换性 | 高。适合先作为 `SearchProvider` 的第一个真实实现。 | 高。适合作为第一备选或后续替换实现。 | 中到高。适合需要 Google SERP 兼容或更丰富垂直结果时引入，但不宜作为第一版复杂化入口。 |

## 首选 provider

首选 Tavily。

原因：

```text
1. 与 AI Agent / RAG / 搜索增强场景贴合。
2. 输出字段容易映射到当前 SearchResultSchema。
3. 可先只使用 basic search，避免 raw content / extract / crawl 带来的成本和职责混淆。
4. 作为第一版 provider，可以保持接入面小、测试样本简单。
```

## 备选 provider

备选 Brave Search API。

原因：

```text
1. Brave 使用自有 Web index，适合作为 Tavily 不可用或质量不足时的替代。
2. 官方面向 agents/RAG 的定位清晰。
3. Web Search endpoint 可以映射到 CSL 的候选来源结构。
```

## 为什么暂时不做多 provider 同时接入

第一版真实搜索接入只应支持一个 provider。多 provider 同时接入会引入：

```text
provider routing
重复结果归并
跨 provider 去重和排序
quota 分配
错误归因
成本控制
测试矩阵膨胀
```

这些问题会干扰当前最重要的目标：验证“真实候选来源进入现有 evidence pipeline 后是否稳定”。因此建议先实现一个 provider，保留接口可替换性，后续再评估多 provider 策略。

---

# 3. SearchProvider 接口边界设计

本节只描述未来接口设计，不实现代码。

建议抽象：

```text
SearchProvider.search(request) -> SearchProviderResponse
```

建议输入字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| query | string | 是 | 单条搜索查询；第一步必须沿用现有 `SearchAdapter.search(query, max_results)` 的 `query` 输入 |
| max_results | integer | 是 | 最大返回结果数，默认可沿用 TrustedSearchRequest.max_sources |
| search_mode / strictness | string | 否 | 可映射 loose / balanced / strict，控制 provider 查询深度或过滤 |
| timeout_seconds | number | 是 | 单次 provider 请求超时 |
| locale / language | string/null | 否 | 语言或地区偏好，例如 `en`、`zh-CN`、`us` |
| safe_search | string/bool/null | 否 | 安全搜索策略，默认使用 provider 的保守设置 |

第一步落地边界：

```text
必须先保持现有 SearchAdapter.search(query, max_results) 抽象不变。
SearchProvider 只作为 SearchAdapter 后面的实现细节。
不要提前让 SearchAdapter 消费 search_plan queries。
是否逐条执行 search_plan queries，应作为后续单独设计，不属于 SearchProvider 接口落地第一步。
不得因此修改 TrustedSearchService 主链路。
```

建议输出分层：

```text
normalized_results: list[SearchResultSchema]
metadata / error / debug: provider 内部状态、错误、fallback、raw payload 等调试信息
```

`normalized_results` 只能映射当前 `SearchResultSchema` 已有字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| title | string | 候选页面标题 |
| url | string | 候选来源 URL |
| snippet | string | 搜索摘要或 provider 的内容摘要 |
| published_at | string/null | 发布时间；provider 无法提供时为 null |

`metadata / error / debug` 可包含但默认不进入主业务响应：

| 字段 | 类型 | 说明 |
|---|---|---|
| provider | string | provider 标识，例如 `tavily`、`brave`、`serpapi`、`mock` |
| fallback_used | bool | 是否使用 mock/static 降级结果 |
| error | string/null | 受控错误码，可对应 `SearchAdapterResponse.error` |
| raw_provider_payload | object/null | 裁剪后的 provider 原始响应，仅用于内部调试或测试 fixture |

`provider`、`source`、`fallback`、`raw_provider_payload` 等信息属于 metadata/error/debug 层。当前业务响应结构保持稳定，`raw_provider_payload` 默认不进入 `TrustedSearchResponse` 主业务结果。

Provider 层职责边界：

```text
只负责调用搜索服务并返回候选来源。
只做 provider response -> normalized_results 的最小字段映射。
只做 provider 错误分类、timeout、retry 和 quota/rate limit 保护。
```

Provider 层绝对不要做：

```text
source_type 分类
base_reliability 评分
页面抓取或正文解析
evidence 抽取
relevance_score / final_score 计算
claim status 聚合
conflict 检测
answer_constraints 生成
自然语言最终回答生成
```

---

# 4. env.example 未来配置项设计

本阶段只设计配置项，不要求填写真实 API key，也不修改运行逻辑。

建议未来 `.env` 配置：

```env
CSL_SEARCH_PROVIDER=tavily
CSL_SEARCH_API_KEY=
CSL_SEARCH_TIMEOUT_SECONDS=8
CSL_SEARCH_MAX_RESULTS_DEFAULT=8
CSL_SEARCH_RETRY_ATTEMPTS=1
CSL_SEARCH_RETRY_BACKOFF_SECONDS=0.5
CSL_SEARCH_RATE_LIMIT_PER_MINUTE=30
CSL_SEARCH_MONTHLY_QUOTA=1000
CSL_SEARCH_FALLBACK_TO_MOCK=true
```

配置说明：

```text
CSL_SEARCH_PROVIDER:
  tavily / brave / serpapi / mock。默认仍建议 mock，直到真实 provider 测试完成。

CSL_SEARCH_API_KEY:
  本地 .env 中填写。不要提交真实密钥。

CSL_SEARCH_TIMEOUT_SECONDS:
  单次 provider HTTP 请求超时，不应无限等待。

CSL_SEARCH_MAX_RESULTS_DEFAULT:
  provider 默认返回数量，上层 request.max_sources 可以覆盖。

CSL_SEARCH_RETRY_ATTEMPTS:
  重试次数，建议第一版为 0 或 1。

CSL_SEARCH_RETRY_BACKOFF_SECONDS:
  重试间隔，建议指数退避或固定短退避，不做无脑重试。

CSL_SEARCH_RATE_LIMIT_PER_MINUTE:
  本地保护阈值，避免开发/CI 意外打满额度。

CSL_SEARCH_MONTHLY_QUOTA:
  本地预算阈值，用于保护账户额度。

CSL_SEARCH_FALLBACK_TO_MOCK:
  provider 不可用时是否回退 mock/static 搜索。生产环境应谨慎开启。
```

正式实现时应沿用当前 `app/core/config.py` 的 `CSL_` 前缀约定。无前缀的 `SEARCH_PROVIDER`、`SEARCH_API_KEY` 等名称最多只能作为概念说明，不应写入 `env.example` 或配置代码，避免后续实现偏离当前配置模式。

真实 API key 只能放在本地 `.env` 或部署环境的 secret manager 中，不能提交到 Git，也不能写入 README、测试 fixture 或录制样本。

---

# 5. Timeout、Retry、Quota、Rate Limit、Fallback 策略

## Timeout

建议第一版策略：

```text
单次 provider 请求 timeout_seconds 默认为 8 秒。
strict 模式可以略微提高到 10 秒，但不建议超过 15 秒。
tech_news 或 policy_legal 等时效性问题不应无限等待。
```

超时后 provider 返回受控错误 `provider_timeout`，不能抛出未处理异常。

## Retry

避免无脑重试。建议：

```text
默认最多重试 1 次。
只对 timeout、短暂 5xx、连接错误做重试。
不对 401/403/auth failed 做重试。
不对 429/rate limit 做立即重试。
不对 quota exceeded 做重试。
重试间隔使用短 backoff，例如 0.5s -> 1.0s。
```

每次 retry 都应写内部日志，包含 provider、错误类型、attempt，但不记录 API key。

## Quota 即将耗尽或已耗尽

建议在 provider wrapper 内维护轻量 quota guard：

```text
v0.1/v0.2 初期只能做进程内计数或配置阈值保护。
如果进程内计数显示达到 CSL_SEARCH_MONTHLY_QUOTA 的 90%，可记录 warning。
如果进程内计数达到 100%，停止真实 provider 调用，返回 provider_quota_exceeded。
如果 provider 返回 quota exceeded，也归类为 provider_quota_exceeded。
不承诺跨进程、跨重启、跨月份的精确 quota 统计。
精确 quota 需要未来持久化存储、外部缓存或 provider dashboard 支持。
当前阶段不要引入数据库、Redis 或新依赖来解决 quota 问题。
```

quota 耗尽时：

```text
CSL_SEARCH_FALLBACK_TO_MOCK=true:
  可以返回 mock/static 降级结果，并在 SearchAdapterResponse.error、内部 debug metadata 或日志中记录 fallback 状态。

CSL_SEARCH_FALLBACK_TO_MOCK=false:
  返回空 results 和受控错误，不让 trusted-search 崩溃。
```

## Rate Limit 命中

provider 返回 429 或本地 rate limiter 命中时：

```text
返回 provider_rate_limited。
不要立即高频重试。
如果 response header 有 Retry-After，可记录到 debug/internal log。
默认 trusted-search 继续走降级路径。
```

## Fallback 到 mock/static

provider 不可用时允许 fallback，但必须明确记录，避免误导为真实搜索：

```text
v0.1 兼容方案下，不把 provider/mock/static 标记塞进 SearchResultSchema 或 SourceSchema。
fallback/provider 状态优先放在 SearchAdapterResponse.error、内部 debug metadata、日志或未来单独的 search_debug 字段中。
当前业务响应结构保持稳定。
内部 debug/search_errors 记录真实 provider 失败原因。
sources 后续仍可正常 source_classifier/page_fetcher/evidence_extractor
fallback 结果可以继续被用于流程降级，但不能伪装成真实搜索结果。
answer_constraints 应保持谨慎，不因 fallback 结果而伪装成真实检索。
```

如果未来需要在主业务响应中显式暴露 provider/fallback 状态，必须作为后续 schema 扩展单独设计，不能在本阶段顺手改 `SearchResultSchema` 或 `SourceSchema`。

---

# 6. Provider 失败时的可控错误设计

provider 失败不能让 `/api/v1/trusted-search` 崩溃。Provider 层应把异常归一为受控错误。

建议错误类型：

| 错误类型 | 典型原因 | 行为 |
|---|---|---|
| provider_timeout | 请求超过 timeout_seconds | 返回空 results 或 fallback results |
| provider_auth_failed | API key 缺失、无效、401/403 | 不重试，记录安全日志，不暴露 key |
| provider_rate_limited | HTTP 429 或本地 rate limiter 命中 | 不立即重试，可 fallback |
| provider_quota_exceeded | 月额度耗尽或本地 quota guard 拦截 | 停止真实调用，可 fallback |
| provider_bad_response | JSON 结构异常、字段无法解析、无效 URL | 丢弃坏结果，必要时返回 error |
| provider_unavailable | 5xx、DNS、连接失败、服务不可用 | 可短重试一次，失败后 fallback/空 results |

错误进入系统的建议方式：

```text
内部日志:
  记录 provider、error_type、request_id、attempt、http_status、duration_ms。
  不记录 API key。

debug 信息:
  只在未来显式 debug 模式或内部字段中返回。
  默认主业务 response 不暴露 provider 原始错误细节。

受控错误字段:
  SearchAdapterResponse.error 可继续承载简短错误码。
  未来可扩展 search_debug/search_errors，但默认不破坏 TrustedSearchResponse shape。
```

最终 trusted-search 响应应尽量保持结构稳定：

```text
query/question_type/risk_level 正常返回
claims 正常返回
search_plan 正常返回
sources 可为空或来自 mock fallback
page_fetches 可为空或 fallback
evidence 可为空
conflicts 可为空
answer_constraints 继续生成谨慎约束
overall_status 倾向 unsupported / uncertain
overall_confidence 不应虚高
```

无法获得真实搜索结果时，claim 状态应倾向 `unsupported` / `uncertain`，不能编造 evidence，也不能把 provider 的标题或摘要强行当成高置信事实。

---

# 7. Mock 测试策略

测试必须默认不依赖真实网络。

保留策略：

```text
单元测试继续使用 MockSearchAdapter / StaticSearchAdapter。
E2E mock test 继续走固定 search results、fallback page_fetch、规则证据抽取。
默认 uv run pytest 不访问真实外网。
CI 默认不需要 API key。
```

未来真实 provider 测试策略：

```text
真实 provider 只能放入显式 opt-in integration tests。
integration tests 默认 skip，只有设置 RUN_SEARCH_PROVIDER_INTEGRATION=1 且提供 API key 时才运行。
integration tests 不应成为 CI 必需条件。
```

稳定测试样本建议：

```text
fixture:
  用固定 fake provider response 覆盖 timeout/auth/rate limit/quota/bad response/success。

fake provider:
  实现 SearchProvider 协议，但不发 HTTP 请求。

recorded sample payload:
  保存脱敏、裁剪后的官方样例或手工构造 JSON。
  不保存 API key、用户隐私 query、完整网页正文。

mapping tests:
  只验证 provider payload -> SearchResultSchema 的映射和过滤。

failure-path tests:
  确认 provider 错误不会导致 trusted-search 500。
```

---

# 8. Provider 输出到现有 SearchResultSchema 的映射方案

现有 `SearchResultSchema`：

```text
title
url
snippet
published_at
```

第一版不要修改现有 schema。Provider 私有字段应留在 adapter 内部或 debug/raw payload 中。

Provider 层输出必须分成两层：

```text
normalized_results: list[SearchResultSchema]
metadata / error / debug
```

当前 `normalized_results` 只映射 `title`、`url`、`snippet`、`published_at`。`provider`、`source`、`fallback`、`raw_provider_payload` 等信息属于 metadata/error/debug 层，不进入 `SearchResultSchema` 或 `SourceSchema`。`raw_provider_payload` 默认不进入 `TrustedSearchResponse` 主业务结果。

## Tavily 映射

Tavily search results 常见字段：

```text
title
url
content
published_date
raw_content optional
score
```

映射：

| Tavily 字段 | SearchResultSchema 字段 |
|---|---|
| title | title |
| url | url |
| content | snippet |
| published_date | published_at |

规则：

```text
如果 content 缺失，snippet 使用空字符串。
如果 published_date 缺失，published_at = null。
raw_content 默认不进入 SearchResultSchema。
score 不进入 SearchResultSchema，避免和 CSL reliability_score 混淆。
```

## Brave Search API 映射

Brave Web Search 常见字段可来自 web results：

```text
title
url
description / snippet
age / page_age / date-like metadata
```

映射：

| Brave 字段 | SearchResultSchema 字段 |
|---|---|
| title | title |
| url | url |
| description 或 snippets 合并 | snippet |
| age / date-like metadata | published_at，如果无法规范化则 null |

规则：

```text
优先使用普通 web results，不在第一版使用 Answers 或 LLM Context 生成的答案。
如果有多个 snippets，只取最相关或合并为短 snippet。
无法稳定解析时间时 published_at = null。
```

## SerpAPI 映射

SerpAPI Google organic results 常见字段：

```text
organic_results[].title
organic_results[].link
organic_results[].snippet
organic_results[].date
organic_results[].source
```

映射：

| SerpAPI 字段 | SearchResultSchema 字段 |
|---|---|
| organic_results[].title | title |
| organic_results[].link | url |
| organic_results[].snippet | snippet |
| organic_results[].date | published_at，如果无法规范化则 null |

规则：

```text
第一版只消费 organic_results。
不消费 ads、shopping、knowledge graph、answer box 作为普通来源。
如果 link 缺失但 redirect_link 存在，不建议直接使用 redirect_link，优先丢弃或解析真实目标 URL。
```

## 通用过滤和去重

所有 provider 都必须执行：

```text
相同规范化 URL 只保留一条。
过滤空 URL、无效 URL。
空 title 结果优先丢弃；如果 url 明确有效且 snippet 非空，可降级用域名作为内部 title，但需记录 provider_bad_response warning。
snippet 缺失时使用空字符串或 provider 摘要字段 fallback。
published_at 缺失或无法解析时统一置为 null。
保持结果顺序稳定，不做复杂 rerank。
```

---

# 9. 与现有 TrustedSearchService 的关系

真实 SearchProvider 未来应作为 SearchAdapter 后面的实现替换点。

下一阶段落地 `SearchProvider` 抽象时，必须先保持现有调用关系不变：

```text
TrustedSearchService 仍调用 SearchAdapter.search(request.query, max_results=request.max_sources)
SearchAdapter 内部再选择 mock/static 或真实 SearchProvider 实现
```

当前 `TrustedSearchService` 虽然生成 `search_plan`，实际搜索调用仍以原始 `request.query` 为输入。不要在 SearchProvider 接口落地第一步提前改成逐条消费 `search_plan` queries。是否逐条执行 search plan、如何合并多条查询结果、如何控制多 claim 查询成本，应作为后续单独设计。

建议层次：

```text
TrustedSearchService
  -> SearchAdapter
       -> SearchProvider
            -> TavilyProvider / BraveProvider / SerpApiProvider
```

当前主链路不要改变：

```text
query
  -> question_classifier
  -> claim_decomposer
  -> search_planner
  -> search_adapter
  -> source_classifier
  -> page_fetcher
  -> evidence_extractor
  -> reliability_scorer
  -> claim_aggregator
  -> conflict_detector
  -> answer_constraint_builder
  -> TrustedSearchResponse
```

真实 provider 接入后，`TrustedSearchService` 仍只依赖 `SearchAdapter` 协议。provider 的成功、失败、fallback 都应在 adapter/provider 层收敛为 normalized results 和受控错误。

因此，本阶段和下一阶段的接口准备不得修改 `TrustedSearchService` 主链路，也不得借 provider 抽象落地顺手改变 schema 或业务响应结构。

---

# 10. 本阶段绝对不要做

```text
不要写真实 provider 代码
不要接 Tavily / Brave / SerpAPI 的真实 API
不要申请或写入 API key
不要改 TrustedSearchService 业务逻辑
不要引入新依赖
不要改 MCP
不要做数据库
不要做前端
不要接真实 LLM
不要重写 Git 历史
不要补 v0.1.7 tag
不要破坏现有 101 个测试
```

---

# 11. 参考资料

以下资料用于本方案的 provider 选型判断。真实实现前应重新核对最新版本。

```text
Tavily Search API:
https://docs.tavily.com/api-reference/endpoint/search
https://docs.tavily.com/guides/api-credits
https://docs.tavily.com/sdk/python/reference

Brave Search API:
https://brave.com/search/api/
https://api-dashboard.search.brave.com/documentation/pricing

SerpAPI:
https://serpapi.com/pricing
https://serpapi.com/organic-results
https://serpapi.com/search-api
```
