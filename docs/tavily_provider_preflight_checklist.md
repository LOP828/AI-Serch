# TavilyProvider Real HTTP Preflight Checklist

版本：v0.2 接入前检查清单
文档类型：真实 Tavily HTTP 实现前置条件 / 安全边界 / 测试门槛
当前状态：checklist 文档，不包含真实 HTTP 代码

---

# 1. 当前状态确认

- `TavilyProvider` 已有 disabled stub。
- `TavilyProvider` 已支持 fake client / request callable 路径。
- `search_provider_factory` 已支持 `CSL_SEARCH_PROVIDER=tavily` disabled opt-in。
- 默认 provider 仍是 `static`。
- 默认 `pytest` 不访问真实网络。
- 当前 Tavily opt-in 不读取 API key，不注入真实 HTTP client，不发起真实 Tavily 请求。

---

# 2. 真实 HTTP 实现前必须满足的条件

- 必须明确使用哪个 HTTP client。
  - 当前优先方案：复用现有依赖 `httpx`。
  - 不应引入 Tavily SDK，除非单独评估依赖、测试隔离和替换成本。
- 必须明确是否需要新增依赖。
  - 如果需要新增依赖，必须单独 commit。
  - 新增依赖必须有独立测试和回滚边界。
  - 不得在真实 HTTP 实现 commit 中顺手修改 `pyproject.toml`。
- API key 配置命名方案必须确定。
  - 首选：`CSL_SEARCH_API_KEY`。
  - 备选：`CSL_TAVILY_API_KEY`，仅在多 provider key 管理明确需要时考虑。
- timeout / retry / error mapping 必须已有 fake client 测试覆盖。
- integration test 必须 opt-in。
- CI 默认不能依赖 API key。
- 默认运行路径必须仍是 `static` / `mock`。

---

# 3. 配置 Checklist

- [ ] 确定使用 `CSL_SEARCH_API_KEY` 还是 `CSL_TAVILY_API_KEY`。
- [ ] 确定是否需要 `CSL_SEARCH_ALLOW_NETWORK` 或 `CSL_TAVILY_ALLOW_NETWORK`。
- [ ] allow-network 配置默认必须是 `False`。
- [ ] 默认 provider 必须仍是 `static`。
- [ ] `.env` 不得提交真实 key。
- [ ] `env.example` 不得包含真实 key。
- [ ] 没有 key 时不能崩溃。
- [ ] 没有 key 时应返回受控 `SearchProviderResponse`，例如 `provider_auth_failed` 或 disabled/unavailable 状态。
- [ ] 配置层不得让 `tavily` 自动成为默认 provider。
- [ ] 配置层不得自动创建真实网络 client，除非显式 opt-in 条件全部满足。

---

# 4. 安全边界 Checklist

- [ ] 不允许未处理异常穿透到 `TrustedSearchService`。
- [ ] 不允许 raw payload 进入 `SearchResultSchema`。
- [ ] 不允许 provider/debug metadata 污染业务 schema。
- [ ] 不允许 `TavilyProvider` 伪造 mock/static 结果。
- [ ] fallback 必须显式标记在 metadata/debug/error 层。
- [ ] fallback 结果不能伪装成真实搜索结果。
- [ ] 真实 provider 失败时必须返回 controlled `SearchProviderResponse`。
- [ ] `SearchProviderResponse.error_code` 必须使用 `SearchProviderErrorCode`。
- [ ] debug/log 不得记录 API key。
- [ ] debug/log 不得记录完整 Authorization header。
- [ ] Tavily provider 不得承担 source classification、evidence extraction、reliability scoring、claim aggregation、conflict detection 或 answer constraints。

---

# 5. 测试 Checklist

- [ ] 单元测试使用 fake client。
- [ ] 成功响应测试。
- [ ] empty results 测试。
- [ ] timeout 测试。
- [ ] 401/403 auth failed 测试。
- [ ] 429 rate limit 测试。
- [ ] quota exceeded 测试。
- [ ] bad response 测试。
- [ ] network unavailable 测试。
- [ ] generic exception 测试。
- [ ] `max_results` 截断测试。
- [ ] no API key 测试。
- [ ] provider/raw/debug 字段不进入 `SearchResultSchema` 测试。
- [ ] 默认 `pytest` 不访问真实网络。
- [ ] `uv run pytest` 通过。
- [ ] `uv run ruff check .` 通过。

---

# 6. Integration Test Checklist

- [ ] integration test 必须显式 opt-in，例如：

```text
CSL_RUN_INTEGRATION_TESTS=true
```

- [ ] 没有 API key 时 skip。
- [ ] 不进入默认 `pytest` 路径。
- [ ] 不在 CI 默认运行。
- [ ] 不提交真实响应中的敏感信息。
- [ ] 可以记录脱敏样例 payload。
- [ ] 脱敏样例 payload 不能记录 API key。
- [ ] 脱敏样例 payload 不能记录用户隐私 query。
- [ ] integration test 失败不能阻塞默认单元测试。

---

# 7. 分阶段实施建议

## 阶段 1：真实 HTTP 实现仍使用 fake client 测试

先把真实请求构造、响应解析、错误映射逻辑写成可由 fake client 驱动的代码。默认测试仍不访问网络。

## 阶段 2：增加 API key 配置，但默认不用

增加 key 配置字段前必须先确定命名方案。没有 key 时必须受控失败，不能崩溃。

## 阶段 3：增加 allow_network 显式开关

allow-network 默认必须是 `False`。只有显式配置后才允许真实网络路径。

## 阶段 4：本地手动 integration test

新增默认 skip 的 integration test。只有本地显式设置 integration 环境变量和 API key 后才运行。

## 阶段 5：再决定是否让 tavily provider 成为可用 opt-in

只有 fake client 单元测试、配置测试、错误映射测试和手动 integration test 都稳定后，才允许让 `CSL_SEARCH_PROVIDER=tavily` 进入真实可用 opt-in。

## 阶段 6：仍然不改变默认 static 行为

即使 Tavily 真实 HTTP opt-in 可用，默认 provider 仍必须是 `static`，默认 CI 仍不需要网络和 API key。

---

# 8. 本阶段绝对不要做

```text
不要写真实 HTTP 实现
不要发起真实网络请求
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
不要移动 v0.2.0-search-provider-foundation tag
不要补 v0.1.7 tag
不要重写 Git 历史
```
