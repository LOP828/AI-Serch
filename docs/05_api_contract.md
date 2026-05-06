# Critical Search Layer API Contract

版本：v0.1  
文档类型：接口契约  
适用阶段：MVP 第一轮到 v0.1 最小闭环

---

# 1. 设计原则

API 的第一目标不是生成自然语言答案，而是返回结构化证据包。

核心原则：

```text
输入：用户问题
输出：结构化 evidence package
```

AI Agent 拿到 evidence package 后，再根据 answer_constraints 生成最终回答。

---

# 2. 通用约定

## 2.1 Content-Type

```http
Content-Type: application/json
```

## 2.2 JSON 命名风格

统一使用 snake_case。

示例：

```json
{
  "question_type": "ai_model_info",
  "overall_confidence": 0.72
}
```

## 2.3 时间格式

统一使用 ISO 8601 字符串。

```json
{
  "created_at": "2026-05-06T12:00:00Z"
}
```

## 2.4 分数字段

所有置信度、相关性、可信度分数范围均为：

```text
0.0 - 1.0
```

---

# 3. Health API

## 3.1 Endpoint

```http
GET /health
```

## 3.2 Response

```json
{
  "status": "ok"
}
```

## 3.3 验收标准

```text
服务启动后，GET /health 返回 200
返回 JSON 中 status = ok
```

---

# 4. Trusted Search API

## 4.1 Endpoint

```http
POST /api/v1/trusted-search
```

---

## 4.2 Request Body

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

---

## 4.3 Request Fields

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---:|---|---|
| query | string | 是 | 无 | 用户问题 |
| question_type | string | 否 | auto | 问题类型，auto 表示自动识别 |
| strictness | string | 否 | balanced | 搜索和评分严格程度 |
| max_sources | integer | 否 | 8 | 最大来源数量 |
| require_primary_source | boolean | 否 | false | 是否要求一手来源 |
| return_raw_evidence | boolean | 否 | true | 是否返回原始证据文本 |

---

## 4.4 question_type 枚举

```text
auto
ai_model_info
tech_news
product_info
policy_legal
technical_doc
general_fact
unknown
```

---

## 4.5 strictness 枚举

```text
loose
balanced
strict
```

含义：

```text
loose:
  更重召回，允许较多弱来源进入证据包

balanced:
  默认模式，在召回和可信度之间平衡

strict:
  更重可信度，高风险问题优先要求一手来源
```

---

## 4.6 Response Body

```json
{
  "query": "MiroThinker 1.7 是不是开源模型？",
  "question_type": "ai_model_info",
  "risk_level": "medium",
  "overall_status": "partially_confirmed",
  "overall_confidence": 0.72,
  "claims": [
    {
      "claim_id": "c1",
      "claim_text": "MiroThinker 1.7 存在公开发布页面",
      "claim_type": "existence",
      "status": "confirmed",
      "confidence": 0.91,
      "reason": "官方模型卡提供了公开模型页面。",
      "evidence": [
        {
          "evidence_id": "e1",
          "source_id": "s1",
          "claim_id": "c1",
          "evidence_text": "页面显示 MiroThinker 1.7 的模型发布信息。",
          "support_type": "support",
          "relevance_score": 0.92,
          "source_score": 0.88,
          "primary_source_factor": 1.1,
          "recency_factor": 1.0,
          "cross_check_factor": 1.0,
          "conflict_penalty": 1.0,
          "interest_conflict_penalty": 1.0,
          "final_score": 0.89,
          "score_breakdown": {
            "relevance_score": 0.92,
            "source_base_score": 0.88,
            "primary_source_factor": 1.1,
            "recency_factor": 1.0,
            "final_score": 0.89
          }
        }
      ]
    }
  ],
  "sources": [
    {
      "source_id": "s1",
      "title": "MiroThinker-1.7 - Hugging Face",
      "url": "https://huggingface.co/example/mirothinker-1.7",
      "domain": "huggingface.co",
      "snippet": "Model card for MiroThinker 1.7...",
      "source_type": "official_model_card",
      "base_reliability": 0.88,
      "is_primary_source": true,
      "published_at": null,
      "author": null,
      "fetched_at": "2026-05-06T12:00:00Z",
      "fetch_status": "success"
    }
  ],
  "conflicts": [],
  "answer_constraints": {
    "can_answer_confidently": false,
    "must_disclose_uncertainty": true,
    "must_cite_sources": true,
    "allowed_tone": "cautious",
    "required_phrases": [
      "目前只能确认部分信息",
      "仍需区分权重开放、代码开放、训练数据开放和许可证限制"
    ],
    "forbidden_phrases": [
      "毫无疑问",
      "已经完全开源",
      "官方已经确认"
    ]
  }
}
```

---

# 5. Response Fields

## 5.1 顶层字段

| 字段 | 类型 | 说明 |
|---|---|---|
| query | string | 原始用户问题 |
| question_type | string | 自动或指定的问题类型 |
| risk_level | string | low / medium / high |
| overall_status | string | 整体状态 |
| overall_confidence | number | 整体置信度 |
| claims | array | 命题列表 |
| sources | array | 来源列表 |
| conflicts | array | 冲突列表 |
| answer_constraints | object | 回答约束 |

---

## 5.2 overall_status 枚举

```text
confirmed
partially_confirmed
uncertain
unsupported
conflicting
failed
```

---

## 5.3 Claim 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| claim_id | string | 命题 ID |
| claim_text | string | 命题文本 |
| claim_type | string | 命题类型 |
| status | string | 命题状态 |
| confidence | number | 命题置信度 |
| reason | string | 状态解释 |
| evidence | array | 该命题下的证据 |

---

## 5.4 claim.status 枚举

```text
confirmed
likely
uncertain
unsupported
conflicting
false_likely
```

---

## 5.5 Source 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| source_id | string | 来源 ID |
| title | string | 页面标题 |
| url | string | 来源 URL |
| domain | string | 域名 |
| snippet | string | 搜索摘要 |
| source_type | string | 来源类型 |
| base_reliability | number | 来源基础可信度 |
| is_primary_source | boolean | 是否一手来源 |
| published_at | string/null | 发布时间 |
| author | string/null | 作者 |
| fetched_at | string/null | 抓取时间 |
| fetch_status | string/null | 抓取状态 |

---

## 5.6 source_type 枚举

```text
official_docs
official_blog
official_model_card
source_code_repo
academic_paper
financial_filing
government_docs
mainstream_media
expert_blog
community_forum
product_page
seo_content
unknown
```

---

## 5.7 Evidence 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| evidence_id | string | 证据 ID |
| source_id | string | 来源 ID |
| claim_id | string | 命题 ID |
| evidence_text | string | 证据文本 |
| support_type | string | 支持关系 |
| relevance_score | number | 相关性分数 |
| source_score | number | 来源基础分 |
| primary_source_factor | number | 一手来源因子 |
| recency_factor | number | 新鲜度因子 |
| cross_check_factor | number | 交叉验证因子 |
| conflict_penalty | number | 冲突惩罚 |
| interest_conflict_penalty | number | 利益相关惩罚 |
| final_score | number | 最终分数 |
| score_breakdown | object | 评分解释 |

---

## 5.8 support_type 枚举

```text
support
oppose
partial
neutral
```

---

## 5.9 fetch_status 枚举

```text
success
fallback_snippet
timeout
http_error
parse_error
blocked
not_fetched
```

---

# 6. Error Response

## 6.1 参数错误

FastAPI 默认返回 422。

示例：

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "query"],
      "msg": "String should have at least 1 character",
      "input": ""
    }
  ]
}
```

## 6.2 服务内部错误

```json
{
  "error": {
    "code": "internal_error",
    "message": "Unexpected server error.",
    "request_id": "req_123"
  }
}
```

## 6.3 外部搜索失败

搜索失败不应导致整个 trusted-search 失败。

推荐返回：

```json
{
  "query": "MiroThinker 1.7 是不是开源模型？",
  "question_type": "ai_model_info",
  "overall_status": "failed",
  "overall_confidence": 0.0,
  "claims": [],
  "sources": [],
  "conflicts": [],
  "answer_constraints": {
    "can_answer_confidently": false,
    "must_disclose_uncertainty": true,
    "must_cite_sources": false,
    "allowed_tone": "cautious",
    "required_phrases": ["搜索失败，无法确认"],
    "forbidden_phrases": ["已经确认", "毫无疑问"]
  }
}
```

---

# 7. 第一阶段 mock 要求

第一阶段 `/api/v1/trusted-search` 不接真实搜索，只返回 mock evidence package。

但 mock 必须符合最终 schema，方便后续逐步替换内部模块。

## 7.1 Mock 输入

```json
{
  "query": "MiroThinker 1.7 是不是开源模型？"
}
```

## 7.2 Mock 输出要求

必须包含：

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

至少包含：

```text
1 个 claim
1 个 source
1 条 evidence
```

---

# 8. 后续兼容要求

后续新增字段时：

```text
可以向后兼容地增加字段
不能随意删除已有字段
不能修改已有枚举含义
不能让 REST API 和 MCP 工具返回结构分叉
```
