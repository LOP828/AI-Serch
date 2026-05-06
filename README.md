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

当前阶段只做第一轮基础闭环：

```text
FastAPI 骨架
/health 接口
/api/v1/trusted-search mock 接口
Pydantic schemas
pytest 基础测试
```

当前不要做：

```text
不接搜索 API
不接 LLM
不做数据库
不做 MCP
不做前端
不做复杂评分
```

---

## 3. 推荐目录结构

```text
critical_search_layer/
  AGENTS.md
  README.md
  .env.example
  .gitignore
  pyproject.toml
  docs/
    01_prd.md
    02_development_sequence.md
    03_detailed_development_tasks.md
    04_constraints.md
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
    services/
    policies/
  tests/
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

### 运行测试

```bash
uv run pytest
```

---

## 5. 环境变量

复制 `.env.example` 为 `.env`：

```bash
cp .env.example .env
```

Windows PowerShell：

```powershell
Copy-Item .env.example .env
```

真实 API Key 只能放在 `.env`，不能提交到 Git。

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

第一阶段只返回 mock evidence package。

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

第一阶段响应会包含固定的 mock 结构：

```text
query
question_type
risk_level
overall_status
overall_confidence
claims
sources
conflicts
answer_constraints
```

注意：当前 mock 接口不调用搜索 API、不调用 LLM、不连接数据库，也不执行真实证据抽取或评分。

完整接口契约见：

```text
docs/05_api_contract.md
```

---

## 7. 测试策略

第一阶段测试重点：

```text
/health 是否正常
trusted-search 是否能接收 query
trusted-search 是否返回符合 schema 的 mock JSON
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

## 10. 当前下一步

当前最应该执行：

```text
根据 PRD，为 Critical Search Layer 创建 FastAPI 项目骨架。先完成 /health 接口、/api/v1/trusted-search mock 接口、Pydantic schemas 和基础 pytest 测试。不要接搜索 API、不要接 LLM、不要做数据库。保证项目能启动、测试能通过、接口返回符合 PRD 的结构化 JSON。
```
