# TavilyProvider Real HTTP Implementation Plan

版本：v0.2 后续实现计划
文档类型：TavilyProvider 真实 HTTP 实现边界 / 配置 / 错误映射 / 测试策略
当前状态：计划文档，不包含真实 provider 代码

---

# 1. 当前背景

Critical Search Layer 当前已经完成 v0.1 mock/static MVP，并进入 v0.2 Search Provider Foundation 收口阶段。

当前已就绪能力：

```text
SearchProvider 抽象接口
SearchAdapter 可选注入 SearchProvider
SearchProviderFactory 配置入口
SearchProvider normalizer
TavilyProvider disabled stub
provider foundation hardening tests
```

当前 `TavilyProvider` 仍只是 disabled stub。它不会发起 HTTP 请求，不读取 API key，不访问真实 Tavily API，只返回受控的 `provider_unavailable`。

下一阶段目标不是直接接入真实 API，而是先设计真实 `TavilyProvider` 的实现边界、配置方式、HTTP 请求结构、错误归一化、fallback 责任边界和测试策略。正式实现必须继续保持默认 mock/static 行为，不能让真实网络请求进入默认测试或默认运行路径。

---

# 2. TavilyProvider 未来职责边界

`TavilyProvider` 未来只负责一件事：调用 Tavily 搜索 API，并把 provider 响应归一为 `SearchProviderResponse`。

允许职责：

```text
构造 Tavily search 请求
设置请求 timeout
处理 Tavily HTTP 状态码
解析 Tavily JSON payload
调用 normalize_tavily_results 生成 normalized_results
返回 SearchProviderResponse
把 provider 错误归一为 SearchProviderErrorCode
把内部调试信息放入 SearchProviderMetadata.debug
```

`normalized_results` 必须复用：

```text
app/services/search_provider_normalizer.py::normalize_tavily_results
```

禁止职责：

```text
来源分类
base_reliability 评分
页面抓取或正文解析
evidence 抽取
relevance_score / final_score 计算
claim status 聚合
conflict 检测
answer_constraints 生成
自然语言最终回答生成
```

这些能力继续由现有 CSL pipeline 中的 `source_classifier`、`page_fetcher`、`evidence_extractor`、`reliability_scorer`、`claim_aggregator`、`conflict_detector` 和 `answer_constraint_builder` 负责。

---

# 3. 配置设计

真实 Tavily 接入应沿用当前 `CSL_` 前缀配置风格。

建议配置项：

```env
CSL_SEARCH_PROVIDER=static
CSL_SEARCH_API_KEY=
CSL_SEARCH_TIMEOUT_SECONDS=8
CSL_SEARCH_RETRY_ATTEMPTS=1
CSL_SEARCH_RETRY_BACKOFF_SECONDS=0.5
CSL_SEARCH_FALLBACK_TO_MOCK=true
```

## API key 命名

优先使用统一配置：

```text
CSL_SEARCH_API_KEY
```

不建议第一版同时引入 `CSL_TAVILY_API_KEY`。原因：

```text
当前阶段只允许一个真实 provider。
统一 key 名称更符合 SearchProvider 抽象。
未来切换 provider 时 factory 可以继续使用同一配置入口。
```

如果后续多 provider 并存，才单独评估 provider-specific key，例如 `CSL_TAVILY_API_KEY`、`CSL_BRAVE_API_KEY`。该扩展必须作为单独配置变更处理。

## 默认 provider

默认配置必须继续保持 `static` 或 `mock`。不允许 `tavily` 成为默认 provider。

原因：

```text
默认测试不能依赖真实网络。
默认运行不能要求 API key。
默认行为必须兼容当前 v0.1/v0.2 mock/static MVP。
```

## secret 规则

`.env` 不得提交真实 key。测试 fixture、文档、README、CI 配置、录制样本中都不得写入真实 API key。

---

# 4. HTTP 请求设计

未来真实实现应优先复用已有依赖：

```text
httpx
```

当前项目已经依赖 `httpx`。本阶段不新增依赖；如果未来希望使用 Tavily SDK，必须单独评估依赖、版本、测试隔离和替换成本，不能在实现 TavilyProvider 时顺手添加。

## 客户端形态

建议引入可注入 HTTP client：

```text
TavilyProvider(http_client=..., api_key=..., timeout_seconds=...)
```

默认仍 disabled，只有配置层显式允许 Tavily 且提供 client/key 时才进入真实路径。测试使用 fake HTTP client 或 monkeypatch，不访问网络。

## 请求方法与 endpoint

未来按 Tavily Search API 文档使用 search endpoint。实现前需要重新核对官方 endpoint、认证 header 和 payload 字段。

建议形态：

```text
POST <tavily-search-endpoint>
Authorization / API key header: 按 Tavily 官方文档
Content-Type: application/json
```

请求 body 建议只包含第一版必要字段：

```json
{
  "query": "...",
  "max_results": 8,
  "search_depth": "basic"
}
```

第一版不要启用 raw content、extract、crawl、advanced search 等高成本或职责外功能。

## max_results

`SearchAdapter.search(query, max_results)` 传入的 `max_results` 应直接映射到 Tavily 请求的最大结果数量字段，并在响应归一化后再次用 `normalize_tavily_results(..., max_results=max_results)` 截断，防止 provider 多返回结果。

## timeout

`CSL_SEARCH_TIMEOUT_SECONDS` 应映射到 `httpx` 请求 timeout。默认建议 8 秒，不应无限等待。

本文档阶段不发起真实 HTTP 请求。

---

# 5. Tavily raw payload 到 SearchResultSchema 的映射

Tavily raw payload 归一化必须复用：

```text
app/services/search_provider_normalizer.py::normalize_tavily_results
```

当前映射：

| Tavily 字段 | SearchResultSchema 字段 |
|---|---|
| `title` | `title` |
| `url` | `url` |
| `content` | `snippet` |
| `published_date` | `published_at` |

兼容字段：

```text
snippet 可作为 content 缺失时的 fallback
published_at 可作为 published_date 缺失时的 fallback
```

缺失字段处理：

```text
缺失 title：丢弃该结果
缺失 url：丢弃该结果
缺失 content/snippet：snippet 使用空字符串
缺失 published_date/published_at：published_at = null
无效 URL：丢弃该结果
非预期 results 结构：返回空 normalized_results，并视场景归类 provider_bad_response
```

重复 URL 处理：

```text
按规范化 URL 去重
忽略 utm_* query 参数
忽略 fragment
保持结果顺序稳定
```

Provider 私有字段不得进入 `SearchResultSchema`：

```text
score
raw_content
provider
request_id
fallback_used
raw_payload
debug
```

这些字段只能留在 `SearchProviderMetadata.raw_payload` 或 `SearchProviderMetadata.debug`，并且默认不进入 `TrustedSearchResponse` 主业务结果。

---

# 6. 错误映射设计

所有错误必须返回受控 `SearchProviderResponse`。不允许未处理异常穿透到 `SearchAdapter`、`TrustedSearchService` 或 FastAPI route。

错误映射：

| 条件 | SearchProviderErrorCode |
|---|---|
| 请求 timeout | `provider_timeout` |
| HTTP 401 / 403 | `provider_auth_failed` |
| HTTP 429 | `provider_rate_limited` |
| provider 明确返回 quota exhausted / credit exhausted | `provider_quota_exceeded` |
| 非预期 JSON / 缺字段 / payload 结构无法解析 | `provider_bad_response` |
| HTTP 5xx / DNS / 连接失败 / 服务不可用 | `provider_unavailable` |

错误响应形态：

```text
normalized_results = []
metadata.provider = "tavily"
metadata.debug 包含安全的错误上下文
error_code = 对应 SearchProviderErrorCode
error_message = 简短、安全、不包含 API key 的说明
```

日志和 debug 中禁止记录：

```text
API key
完整 Authorization header
用户 secret
未脱敏 provider raw error
```

---

# 7. Fallback 策略

`TavilyProvider` 自身不应伪造真实结果。

如果 Tavily 失败，provider 只返回受控错误：

```text
SearchProviderResponse(
  normalized_results=[],
  metadata=SearchProviderMetadata(provider="tavily", ...),
  error_code=...,
  error_message=...
)
```

是否 fallback 到 mock/static 应由 adapter/factory 或更上层策略决定，而不是由 `TavilyProvider` 内部混入静态结果。

fallback 规则：

```text
fallback metadata/debug 不得污染 SearchResultSchema
fallback 结果不能伪装成真实搜索结果
fallback_used 等状态只能放在 metadata/debug、SearchAdapterResponse.error 或未来单独 debug 字段
```

如果未来需要向 API 响应暴露 provider/fallback 状态，必须作为 schema 扩展单独设计，不能顺手塞进 `SearchResultSchema` 或 `SourceSchema`。

---

# 8. 测试策略

默认测试策略：

```text
uv run pytest 默认不访问真实网络
CI 默认不需要 API key
无 API key 时真实 provider integration test skip 或不运行
单元测试使用 fake HTTP client / monkeypatch / local payload
```

单元测试覆盖：

```text
成功响应映射为 normalized_results
empty results 合法返回
timeout -> provider_timeout
401/403 -> provider_auth_failed
429 -> provider_rate_limited
quota exhausted -> provider_quota_exceeded
非预期 JSON -> provider_bad_response
缺字段 / 无效 URL -> provider_bad_response 或丢弃坏结果
5xx / 网络不可用 -> provider_unavailable
metadata/debug 不进入 SearchResultSchema
max_results 被请求层和 normalizer 层共同尊重
```

integration test 规则：

```text
必须显式 opt-in，例如 RUN_SEARCH_PROVIDER_INTEGRATION=1
必须提供本地 API key
默认 CI 不运行
不得成为 pytest 必需条件
不得提交真实响应中的 secret 或隐私 query
```

---

# 9. 分阶段落地顺序

## 阶段 A：文档计划

新增本文档，明确 TavilyProvider 真实 HTTP 实现边界。不得写真实 HTTP 代码。

## 阶段 B：引入可注入 HTTP client，但默认 disabled

扩展 `TavilyProvider` 构造参数，使 HTTP client 可注入。默认仍返回 disabled stub，不访问网络。

## 阶段 C：用 fake client 测真实实现逻辑

使用 fake HTTP client / monkeypatch 覆盖成功、失败和异常路径。测试不得访问真实网络。

## 阶段 D：配置层允许 tavily，但默认仍 static

在 factory/config 中加入显式 Tavily 开关。默认 provider 继续是 `static` 或 `mock`。

## 阶段 E：手动 opt-in integration test

新增默认 skip 的 integration test。只有显式环境变量和本地 API key 同时存在时才运行。

## 阶段 F：真实 API key 本地验证

开发者在本地 `.env` 或 secret manager 中配置 key 后手动验证。验证结果不得提交 secret，不得让 CI 依赖真实 provider。

每个阶段都必须保持：

```text
默认测试不依赖真实网络
默认运行不需要 API key
SearchResultSchema / SourceSchema 不变
TrustedSearchService 主链路不变
SearchAdapter 不消费 search_plan queries
```

---

# 10. 本阶段绝对不要做

```text
不要写真实 Tavily HTTP 实现
不要接 Brave / SerpAPI
不要发起任何 HTTP 请求
不要读取、申请、写入 API key
不要新增依赖
不要修改 pyproject.toml
不要修改 env.example
不要修改 README
不要修改 MCP
不要修改 TrustedSearchService
不要修改 SearchAdapter 主行为
不要让 SearchAdapter 消费 search_plan queries
不要修改 SearchResultSchema / SourceSchema
不要做数据库
不要做前端
不要接真实 LLM
不要补 v0.1.7 tag
不要重写 Git 历史
```
