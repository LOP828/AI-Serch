# TavilyProvider Manual Verification

版本：v0.2.1 手动验证记录
文档类型：TavilyProvider 显式 opt-in integration test 验证结果

---

# 1. 验证背景

`TavilyProvider` 已完成最小真实 HTTP client 实现。

当前默认安全边界保持不变：

```text
默认 provider 仍为 static
默认 pytest 不访问真实网络
integration test 必须显式 opt-in
API key 不写入代码、文档、.env、README 或 Git 历史
```

`TavilyProvider` 仍只负责调用 Tavily search API 并返回 `SearchProviderResponse`。它不负责 source classification、evidence extraction、reliability scoring、claim aggregation、conflict detection 或 answer constraints。

---

# 2. 手动验证环境变量

本次手动验证使用临时环境变量：

```text
CSL_RUN_INTEGRATION_TESTS=true
CSL_SEARCH_PROVIDER=tavily
CSL_SEARCH_ALLOW_NETWORK=true
CSL_SEARCH_API_KEY=<temporary local value>
```

安全要求：

```text
不要把 API key 写入代码
不要把 API key 写入文档
不要把 API key 写入 .env
不要把 API key 写入 README
不要把 API key 写入 Git 历史
```

---

# 3. 手动验证命令

本次使用的 integration test 命令：

```powershell
uv run python -m pytest tests/integration/test_tavily_provider_integration.py -m integration
```

单独运行 integration 文件时，Windows 环境下可能需要临时设置：

```powershell
$env:PYTHONPATH = (Get-Location).Path
```

---

# 4. 验证结果

本次确认结果：

```text
integration test: 1 passed, 3 deselected
default full test suite: 185 passed, 1 skipped
ruff: All checks passed
git status: working tree clean
```

---

# 5. 安全边界确认

- 默认 `pytest` 不访问真实网络。
- 没有 API key 时 integration test skip。
- 没有显式 `CSL_RUN_INTEGRATION_TESTS=true` 时 skip。
- API key 未出现在 debug、metadata 或 error message。
- `SearchResultSchema` 未被 provider/raw/debug 字段污染。
- `TrustedSearchService` 主链路未修改。
- `SearchAdapter` 主行为未修改。
- Tavily integration test 只在显式 opt-in 条件下运行。

---

# 6. 当前能力边界

- `CSL_SEARCH_PROVIDER=tavily` 已可用于显式 opt-in 验证。
- 仍不应把 `tavily` 设为默认 provider。
- 仍不接 Brave / SerpAPI。
- 仍没有数据库。
- 仍没有前端。
- 仍没有真实 LLM。
- 仍不让 `SearchAdapter` 消费 `search_plan` queries。

---

# 7. 后续建议

- 可以打 `v0.2.1-tavily-provider-opt-in` tag。
- 后续再补开发者使用说明。
- 后续再考虑 `TavilyProvider` 在 trusted-search 主链路中的真实 opt-in 行为测试。
- 不要急着接 Brave / SerpAPI。
