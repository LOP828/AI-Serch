# Trusted-search Tavily Opt-in Wiring Plan

版本：v0.2.2 待接入计划
文档类型：trusted-search 主链路 Tavily opt-in wiring 审查与最小接入建议

---

# 1. 当前结论

`TavilyProvider` 已经可以通过 `SearchProviderFactory` 单独 opt-in 构建：

```text
CSL_SEARCH_PROVIDER=tavily
CSL_SEARCH_ALLOW_NETWORK=true
CSL_SEARCH_API_KEY=<temporary local value>
```

但当前 `/api/v1/trusted-search` API 主链路尚未接入 `search_provider_factory`。

当前 route 直接调用：

```text
TrustedSearchService().search(request)
```

当前 `TrustedSearchService` 在没有显式注入 `search_adapter` 时仍使用：

```text
StaticSearchAdapter()
```

因此，即使设置 `CSL_SEARCH_PROVIDER=tavily`，当前 API 主链路仍不会自动通过 factory 构建 `SearchAdapter(provider=TavilyProvider)`。

---

# 2. 已可用能力

当前已可用：

- `SearchProviderFactory` 能根据 `CSL_SEARCH_PROVIDER=tavily` 构建 Tavily adapter。
- `TavilyProvider` 已有最小真实 HTTP client。
- Tavily provider integration test 已默认 skip，并可通过显式本地 opt-in 手动验证。
- 默认 provider 仍为 `static`。
- 默认 pytest 不访问真实网络。
- API key 只通过临时环境变量传入，不写入代码、文档、`.env` 或 Git 历史。

---

# 3. 当前未启用的 wiring

目标主链路是：

```text
SearchProviderFactory
-> SearchAdapter(provider=TavilyProvider)
-> TrustedSearchService
-> /api/v1/trusted-search
-> TrustedSearchResponse
```

当前缺口在 `TrustedSearchService` 实例创建处：

```text
/api/v1/trusted-search
-> TrustedSearchService()
-> StaticSearchAdapter()
```

也就是说，factory 目前存在，但没有被 API route 或 service 默认构造路径调用。

---

# 4. 建议的最小 wiring 点

建议优先在 FastAPI route 层做最小依赖注入，而不是改动 service 内部默认行为：

```text
app/api/routes/trusted_search.py
```

建议形态：

```text
adapter = build_search_adapter()
service = TrustedSearchService(search_adapter=adapter)
return service.search(request)
```

这样做的原因：

- 保持 `TrustedSearchService()` 默认单测行为不变。
- 默认 provider 仍由配置层决定，且默认仍是 `static`。
- API route 成为配置到主链路的唯一 opt-in 入口。
- 不改变 `TrustedSearchResponse` schema。
- 不改变 `SearchResultSchema` / `SourceSchema`。
- 不让 `SearchAdapter` 消费 `search_plan` queries。
- 不修改 MCP 行为。

---

# 5. 默认安全边界

接入 factory 后仍必须保持：

- `CSL_SEARCH_PROVIDER` 默认值为 `static`。
- `CSL_SEARCH_ALLOW_NETWORK` 默认值为 `false`。
- 默认 `uv run pytest` 不访问真实网络。
- 没有 `CSL_SEARCH_API_KEY` 时，Tavily opt-in 路径必须受控失败或被 integration test skip。
- API key 不进入 response、debug、log、测试断言输出或文档。
- 不新增依赖。
- 不修改 schema。
- 不修改 MCP。

---

# 6. 不应在本 wiring 中做的事

本接入点不应包含：

- 修改 Tavily 为默认 provider。
- 修改 allow-network 默认值。
- 接 Brave / SerpAPI。
- 修改 search plan 执行逻辑。
- 让 `SearchAdapter` 消费 `search_plan` 中的 queries。
- 修改 source / evidence / reliability / claim aggregation schema。
- 修改 MCP wrapper。
- 新增数据库、前端或真实 LLM。

---

# 7. 后续 opt-in E2E 测试建议

在 route 层接入 factory 后，可以新增默认 skip 的 integration / E2E 测试：

```text
tests/integration/test_trusted_search_tavily_integration.py
```

skip 条件至少包括：

```text
CSL_RUN_INTEGRATION_TESTS == "true"
CSL_SEARCH_PROVIDER == "tavily"
CSL_SEARCH_ALLOW_NETWORK == "true"
CSL_SEARCH_API_KEY is not empty
```

测试建议：

- 使用 FastAPI `TestClient` 调用 `/api/v1/trusted-search`。
- query 使用稳定、低风险问题，例如 `OpenAI official blog`。
- `max_sources` 控制为 1 或 2。
- 只断言 response 结构兼容，不断言 `confirmed` 或具体 source。
- 断言 response 中不包含 API key。
- 断言 `claims`、`sources`、`evidence`、`answer_constraints` 结构保持兼容。

该测试默认必须 skip，不能进入普通 pytest 的真实网络路径。

---

# 8. 推荐下一步

下一步可以做一个极小生产改动：

```text
app/api/routes/trusted_search.py
```

仅把 route 中的 `TrustedSearchService()` 改为使用 `build_search_adapter()` 注入。

随后新增默认 skip 的：

```text
tests/integration/test_trusted_search_tavily_integration.py
```

该改动完成前，不能声称 `CSL_SEARCH_PROVIDER=tavily` 已经进入 trusted-search API 主链路。
