# Critical Search Layer

中文名：AI 批判性搜索层  
版本：MVP v0.1  
项目形态：AI Agent 可调用的可信搜索工具 / 插件 / 中间件

---

## 1. 项目定位

Critical Search Layer 不是搜索引擎，也不是大模型。

它是在 AI Agent 与搜索引擎之间增加的一层“批判性搜索层”，用于帮助 AI 在回答前完成：

```text
问题类型识别
命题拆解
搜索计划生成
来源类型识别
证据抽取
可信度评分
冲突检测
回答约束生成
```

核心目标：

```text
让 AI 不只是找到信息，而是判断信息值不值得信，以及应该用多大确定性回答。
```

---

## 2. 当前开发阶段

当前代码已形成 REST API first 的 mock 可信搜索闭环，并提供最小 MCP wrapper：

```text
FastAPI 骨架
/health 接口
/api/v1/trusted-search 接口
Pydantic schemas
TrustedSearchService 编排
MCP trusted_search wrapper
```

当前不要做：

```text
不接搜索 API
不接 LLM
不做数据库
不做前端
```

---

## 3. 当前目录结构

```text
critical_search_layer/
  AGENTS.md
  README.md
  env.example
  .gitignore
  pyproject.toml
  docs/
    critical_search_layer_prd_v_0_1.md
    critical_search_layer_development_sequence_v_0_1.md
    critical_search_layer_detailed_development_tasks.md
    critical_search_layer_constraints.md
    05_api_contract.md
    06_test_cases.md
  app/
    main.py
    core/
      config.py
      logging.py
      exceptions.py
    api/
      routes/
        health.py
        trusted_search.py
    schemas/
      trusted_search.py
      claim.py
      source.py
      evidence.py
      constraints.py
      conflict.py
      page.py
      search.py
    services/
      trusted_search_service.py
    policies/
      source_policy.yml
    mcp/
      server.py
      tools.py
  tests/
    e2e/
    mcp/
    services/
```

---

## 4. 本地开发环境

建议使用 `uv` 管理 Python 环境。

### 创建环境

```bash
uv sync
```

### 启动服务

```bash
uv run uvicorn app.main:app --reload
```

### 启动 MCP server

当前项目未引入官方 MCP SDK，提供一个无新增依赖的 stdio JSON wrapper：

```bash
uv run python -m app.mcp.server
```

它支持 `tools/list` 和 `tools/call` 风格的 JSON 行输入，也支持简化调用。

### 运行测试

```bash
uv run pytest
```

---

## 5. 环境变量

复制 `env.example` 为 `.env`：

```bash
cp env.example .env
```

Windows PowerShell：

```powershell
Copy-Item env.example .env
```

当前 v0.1 MVP 只读取 `CSL_APP_NAME`、`CSL_APP_VERSION`、`CSL_ENVIRONMENT`、`CSL_LOG_LEVEL`。搜索、LLM、数据库和 Redis 配置项是未来接入预留，当前运行不会使用。真实 API Key 只能放在 `.env`，不能提交到 Git。

---

## 6. 核心接口

### 健康检查

```http
GET /health
```

期望返回：

```json
{
  "status": "ok"
}
```

### 可信搜索

```http
POST /api/v1/trusted-search
```

当前返回结构化 evidence package，不生成自然语言最终答案。

示例请求：

```json
{
  "query": "MiroThinker 1.7 是不是开源模型？",
  "question_type": "auto",
  "strictness": "balanced",
  "max_sources": 8,
  "require_primary_source": false,
  "return_raw_evidence": true
}
```

响应会包含：

```text
query
question_type
risk_level
overall_status
overall_confidence
claims
search_plan
sources
page_fetches
conflicts
answer_constraints
```

注意：当前实现不调用真实搜索 API、不调用 LLM、不连接数据库。搜索和页面抓取默认使用 mock / fallback 行为，保证测试稳定。

### MCP tool

Tool name:

```text
trusted_search
```

Tool description:

```text
对用户问题进行批判性搜索分析，返回结构化 evidence package，包括 question_type、claims、search_plan、sources、page_fetches、evidence、conflicts 和 answer_constraints。
```

输入参数与 REST 请求一致：

```json
{
  "query": "MiroThinker 1.7 是不是开源模型？",
  "question_type": "auto",
  "strictness": "balanced",
  "max_sources": 8,
  "require_primary_source": false,
  "return_raw_evidence": true
}
```

stdio JSON-RPC 风格调用示例：

```json
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"trusted_search","arguments":{"query":"MiroThinker 1.7 是不是开源模型？"}}}
```

简化调用示例：

```json
{"tool":"trusted_search","arguments":{"query":"MiroThinker 1.7 是不是开源模型？"}}
```

输出为 `TrustedSearchResponse` 的 JSON-compatible dict，保留 evidence、conflicts 和 answer_constraints。

完整接口契约见：

```text
docs/05_api_contract.md
```

---

## 7. 测试策略

当前测试重点：

```text
/health 是否正常
trusted-search 是否能接收 query
TrustedSearchService 端到端 mock 闭环是否稳定
services 单元测试是否覆盖分类、拆解、计划、来源分类、抓取 fallback、证据抽取、评分、聚合、约束、冲突
MCP wrapper 是否复用 TrustedSearchService
非法输入是否返回 422
```

完整测试用例见：

```text
docs/06_test_cases.md
```

---

## 8. 开发原则

1. 先跑通最小闭环，再逐步增强。
2. 每个阶段都必须有测试。
3. 外部依赖必须 mock。
4. 搜索失败、网页抓取失败、LLM 失败都不能导致整个流程崩溃。
5. 没有证据时返回 unsupported，不能编造证据。
6. 不确定就是产品能力，不是产品缺陷。

---

## 9. Git 标签建议

```text
v0.1.0-skeleton
v0.1.1-api-schema
v0.1.2-question-claims
v0.1.3-search-adapter
v0.1.4-source-classifier
v0.1.5-page-fetcher
v0.1.6-evidence-extractor
v0.1.7-reliability-scorer
v0.1.8-claim-aggregator
v0.1.9-answer-constraints
v0.1.10-e2e-mvp
v0.1.11-conflict-detector
v0.1.12-mcp-tool
```

---

## 10. 当前能力边界

已完成 v0.1 mock MVP 闭环：

```text
query
  -> question_type
  -> claims
  -> search_plan
  -> mock search_results
  -> classified sources
  -> page_fetches with fallback
  -> rule-based evidence
  -> reliability scores
  -> claim status
  -> conflicts
  -> answer_constraints
  -> evidence package JSON
```

当前仍不做：

```text
真实搜索 provider
真实 LLM evidence extraction
数据库/缓存
前端
官方 MCP SDK runtime
```
