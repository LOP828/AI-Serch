# Tavily Opt-in Usage

版本：v0.2.2 开发者使用说明
文档类型：Tavily provider 显式 opt-in 运行与验证指南

---

# 1. 当前能力说明

Critical Search Layer 当前默认 provider 仍是 `static`。Tavily 不是默认 provider，也不应被设置为默认 provider。

当前 `/api/v1/trusted-search` 已支持通过配置显式 opt-in 到 Tavily provider：

```text
CSL_SEARCH_PROVIDER=tavily
CSL_SEARCH_ALLOW_NETWORK=true
CSL_SEARCH_API_KEY=<temporary local value>
```

默认 `pytest` 不访问真实 Tavily 网络。Integration tests 默认 skip，只有显式设置 opt-in 环境变量并提供临时 API key 时才运行。

---

# 2. 安全边界

- 不要把 API key 写入代码。
- 不要把 API key 写入 `.env` 后提交。
- 不要把 API key 写入 `README`、`docs` 或 Git 历史。
- API key 只建议使用当前 shell 进程的临时环境变量。
- 测试结束后清理环境变量。
- 不要把 Tavily 设为默认 provider。

---

# 3. 默认本地测试命令

默认验证命令：

```powershell
uv run pytest
uv run ruff check .
```

默认结果应类似：

```text
192 passed, 2 skipped
All checks passed!
```

默认测试不访问真实 Tavily 网络，不需要 API key，也不应依赖外部搜索服务。

---

# 4. 单独运行 TavilyProvider Integration Test

该测试只验证 `TavilyProvider` provider 层真实 opt-in 路径。

需要临时设置：

```powershell
$env:CSL_RUN_INTEGRATION_TESTS = "true"
$env:CSL_SEARCH_PROVIDER = "tavily"
$env:CSL_SEARCH_ALLOW_NETWORK = "true"
$env:CSL_SEARCH_API_KEY = "<temporary local value>"
```

运行命令：

```powershell
uv run python -m pytest tests/integration/test_tavily_provider_integration.py -m integration
```

Windows 单独运行时如果遇到 `No module named app`，可以临时设置：

```powershell
$env:PYTHONPATH = (Get-Location).Path
```

---

# 5. 运行 Trusted-search Tavily Route Integration Test

该测试走 `/api/v1/trusted-search` 主链路：

```text
SearchProviderFactory
-> SearchAdapter(provider=TavilyProvider)
-> TrustedSearchService
-> /api/v1/trusted-search
-> TrustedSearchResponse
```

需要临时设置：

```powershell
$env:CSL_RUN_INTEGRATION_TESTS = "true"
$env:CSL_SEARCH_PROVIDER = "tavily"
$env:CSL_SEARCH_ALLOW_NETWORK = "true"
$env:CSL_SEARCH_API_KEY = "<temporary local value>"
```

运行命令：

```powershell
uv run python -m pytest tests/integration/test_trusted_search_tavily_integration.py -m integration
```

该测试不应要求 claim status 为 `confirmed`。外部搜索结果可能随时间和 Tavily 返回内容波动，测试只应验证 `TrustedSearchResponse` 结构稳定、主链路可用，并确认响应中不泄露 API key。

---

# 6. PowerShell 临时输入 API Key 示例

不要把真实 key 写进命令历史、文档或代码。可以用 `Read-Host -AsSecureString` 在当前 PowerShell 会话中临时输入：

```powershell
$secureKey = Read-Host "Enter Tavily API key for this shell only" -AsSecureString
$plainKey = [System.Net.NetworkCredential]::new("", $secureKey).Password
$env:CSL_SEARCH_API_KEY = $plainKey
Remove-Variable plainKey
Remove-Variable secureKey
```

然后设置其余 opt-in 环境变量：

```powershell
$env:CSL_RUN_INTEGRATION_TESTS = "true"
$env:CSL_SEARCH_PROVIDER = "tavily"
$env:CSL_SEARCH_ALLOW_NETWORK = "true"
```

---

# 7. 清理环境变量

测试结束后清理当前 PowerShell 会话中的临时环境变量：

```powershell
Remove-Item Env:\CSL_RUN_INTEGRATION_TESTS
Remove-Item Env:\CSL_SEARCH_PROVIDER
Remove-Item Env:\CSL_SEARCH_ALLOW_NETWORK
Remove-Item Env:\CSL_SEARCH_API_KEY
Remove-Item Env:\PYTHONPATH
```

如果某个变量不存在，PowerShell 可能提示路径不存在。可以只清理当前实际设置过的变量。

---

# 8. Windows uv Cache / .venv 权限问题处理

如果 `uv run pytest` 遇到用户目录 cache 或 `.venv\lib64` 权限问题，可以临时把 uv 环境和 cache 放在工作区内：

```powershell
$env:UV_PROJECT_ENVIRONMENT = ".uv-venv"
$env:UV_CACHE_DIR = ".uv-cache"
```

然后重新运行：

```powershell
uv run pytest
uv run ruff check .
```

跑完后清理：

```powershell
Remove-Item Env:\UV_PROJECT_ENVIRONMENT
Remove-Item Env:\UV_CACHE_DIR
Remove-Item -Recurse -Force .uv-venv,.uv-cache
```

不要提交 `.uv-venv` 或 `.uv-cache` 临时目录。

---

# 9. 当前不支持或不建议做的事

- 不要把 Tavily 设为默认 provider。
- 不要接 Brave / SerpAPI。
- 不要在 CI 默认跑真实 integration test。
- 不要让默认 pytest 访问真实网络。
- 不要让 `SearchAdapter` 消费 `search_plan` queries。
- 不要修改 schema 或 MCP。

---

# 10. 故障排查

## No module named app

单独运行 integration 文件时设置：

```powershell
$env:PYTHONPATH = (Get-Location).Path
```

## API key 缺失

Integration test 应 skip，或者 Tavily provider 返回受控 `provider_auth_failed`。不要把 key 打印到终端、日志、文档或失败信息中。

## 网络失败

检查本机代理、GitHub 访问、Tavily API 连接和 DNS。网络失败属于外部环境问题，不应让默认测试失败。

## Rate limit / quota

`rate limit` 或 `quota` 属于外部服务限制。默认测试不依赖 Tavily，因此不应因为外部服务限制失败。

## 401 / 403

检查临时 API key 是否有效，确认当前 shell 中的 `CSL_SEARCH_API_KEY` 已设置。但不要打印 key，不要把 key 写入文档或提交历史。
