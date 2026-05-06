# 产品需求文档 PRD

# 项目名称：Critical Search Layer

中文名：AI 批判性搜索层  
版本：MVP v0.1  
文档状态：初稿  
目标形态：AI Agent 可调用的可信搜索工具 / 插件 / 中间件  

---

# 一、产品概述

## 1.1 背景

当前 AI 搜索工具通常能够完成“搜索—摘要—回答”的基本流程，但在信息真实性和可靠性判断上存在明显不足。

常见问题包括：

1. 搜索结果主要按相关性排序，而不是按可信度排序。
2. AI 容易把“有人这么说”包装成“事实就是如此”。
3. 对官方来源、媒体转述、社区传言、营销软文、SEO 垃圾内容缺少清晰区分。
4. 缺少对一手来源、利益相关、证据冲突、信息过期、多源交叉验证的系统处理。
5. AI 生成答案时，常常用过高确定性的语气表达低置信度信息。

因此，需要在 AI 与搜索引擎之间增加一层“批判性搜索层”，让 AI 不只是找到信息，还能判断信息是否值得相信，以及应该用多大确定性回答。

## 1.2 产品定义

Critical Search Layer 是一个面向 AI Agent 的可信搜索中间件。

它不替代大模型，也不替代搜索引擎，而是在搜索结果和 AI 回答之间加入以下能力：

1. 问题类型识别
2. 命题拆解
3. 搜索计划生成
4. 来源类型识别
5. 证据抽取
6. 可信度评分
7. 冲突检测
8. 回答口径约束

一句话定义：

> Critical Search Layer 是一套给 AI 搜索使用的批判性思维工具，让 AI 在相信信息之前先学会怀疑、验证、加权和保留不确定性。

---

# 二、产品目标

## 2.1 MVP 目标

MVP 阶段的核心目标不是做一个完美搜索引擎，而是验证以下假设：

> 如果 AI 在回答前先获得结构化证据包，而不是直接获得网页摘要，那么最终回答的真实性、可靠性和不确定性表达会显著改善。

## 2.2 具体目标

MVP v0.1 需要实现：

1. 用户输入一个问题，系统能够自动判断问题类型。
2. 系统能够将复杂问题拆解为若干可验证命题。
3. 系统能够调用搜索 API 获取候选来源。
4. 系统能够识别来源类型，如官方文档、论文、模型卡、GitHub、主流媒体、社区帖子、SEO 内容等。
5. 系统能够从网页内容中抽取支持或反驳某个命题的证据。
6. 系统能够对每条证据进行可信度评分。
7. 系统能够识别同一命题下的证据冲突。
8. 系统能够返回结构化证据包，而不是只返回自然语言答案。
9. 系统能够给 AI 提供回答约束，例如“可以确认”“较可能”“无法确认”“来源冲突”。

## 2.3 非目标

MVP v0.1 暂不做以下事项：

1. 不训练新模型。
2. 不自建通用搜索引擎。
3. 不做复杂的用户账号系统。
4. 不做浏览器插件前端。
5. 不做医学、投资、法律建议类高风险自动决策。
6. 不承诺判断绝对真相，只判断证据强弱和回答置信度。
7. 不追求所有领域通用，先聚焦若干高频场景。

---

# 三、用户与使用场景

## 3.1 目标用户

### 1. AI Agent 开发者

他们希望自己的 AI Agent 在联网搜索时更加可靠，减少幻觉和错误引用。

### 2. 内容创作者

他们需要快速核查信息来源，区分事实、传言、观点和营销内容。

### 3. 研究型 AI 用户

他们经常让 AI 搜索技术信息、模型信息、产品信息和新闻，需要更高可信度。

### 4. 企业内部知识库使用者

企业希望 AI 在引用内部文档和外部信息时能够标明证据来源、冲突和置信度。

## 3.2 典型使用场景

### 场景 1：AI 模型信息核查

用户问：

> MiroThinker 1.7 是不是开源模型？

系统应拆解为：

1. MiroThinker 1.7 是否存在？
2. 是否有官方模型卡？
3. 是否公开权重？
4. 是否公开代码？
5. 是否公开训练数据？
6. 许可证是否允许商用？
7. 是否能严格称为“开源”？

最终返回：

- 哪些可以确认
- 哪些只能部分确认
- 哪些无法确认
- AI 应该如何谨慎回答

### 场景 2：科技爆料真实性核查

用户问：

> OpenAI 某个新模型是不是下周发布？

系统应优先检查：

1. 官方博客
2. 官方 X / 新闻稿
3. 可信媒体
4. 爆料源历史可信度
5. 是否有多个独立来源
6. 是否存在相反证据

如果只有社区爆料，系统应返回：

> 未验证，不能确认为事实，只能说“有传言称”。

### 场景 3：产品参数核查

用户问：

> 某款笔记本显卡是不是 12GB 显存？

系统应优先检查：

1. 厂商官网
2. 京东/天猫官方店参数页
3. 产品说明书
4. 评测媒体拆机

最终返回具体参数和来源可信度。

### 场景 4：政策法规信息核查

用户问：

> 某项政策现在是否还有效？

系统应优先检查：

1. 政府官网
2. 法规原文
3. 监管机构公告
4. 最近修订日期

媒体解读只能作为辅助，不能作为最高可信来源。

---

# 四、核心产品逻辑

## 4.1 总体流程

```text
用户问题
  ↓
问题类型识别
  ↓
命题拆解
  ↓
搜索计划生成
  ↓
多源搜索
  ↓
网页解析
  ↓
来源类型识别
  ↓
证据抽取
  ↓
可信度评分
  ↓
冲突检测
  ↓
证据包生成
  ↓
返回给 AI
  ↓
AI 根据证据包回答
```

## 4.2 核心原则

### 原则 1：搜索结果不是答案

搜索结果只是候选材料，必须经过证据抽取和可信度评估后，才能进入回答生成阶段。

### 原则 2：可信度绑定命题，而不是绑定网站

同一个来源在不同命题上的可信度不同。

例如：

- 官方模型卡对“模型是否发布”可信度高。
- 官方模型卡对“模型是否世界第一”可信度需要打折。
- 社区帖子对“用户遇到的问题”有参考价值。
- 社区帖子对“客观事实结论”可信度较低。

### 原则 3：一手来源优先

原始文件、官方文档、论文、源码、财报、法规文本等优先级高于媒体转述和社区讨论。

### 原则 4：多数不等于真实

多个低质量网站重复同一说法，不等于交叉验证。

系统需要尽量区分：

1. 独立来源
2. 相互转载
3. 原始来源
4. 搬运来源

### 原则 5：冲突必须暴露

当高可信来源之间存在冲突时，系统不应强行给出确定结论，而应明确标记为 conflicting。

### 原则 6：不确定性是产品能力

当证据不足时，系统必须允许并鼓励 AI 回答“无法确认”“目前证据不足”“只能说有传言”。

---

# 五、功能需求

# 5.1 问题类型识别

## 功能说明

系统需要根据用户问题自动判断问题类型。

## MVP 支持类型

```text
ai_model_info      AI 模型信息
tech_news          科技新闻 / 爆料
product_info       产品参数 / 价格 / 规格
policy_legal       政策法规信息
technical_doc      技术文档 / 编程问题
general_fact       普通事实问题
unknown            无法判断
```

## 输入

```json
{
  "query": "MiroThinker 1.7 是不是开源模型？"
}
```

## 输出

```json
{
  "question_type": "ai_model_info",
  "risk_level": "medium"
}
```

## 验收标准

1. 能识别 AI 模型、产品参数、政策法规、新闻爆料等基本类型。
2. 识别失败时返回 unknown，而不是胡乱归类。
3. 高风险类型应提高证据门槛。

---

# 5.2 命题拆解

## 功能说明

系统需要将复杂问题拆成多个可验证命题。

## 示例

用户问题：

> MiroThinker 1.7 是不是开源模型？

拆解结果：

```json
{
  "claims": [
    {
      "claim_id": "c1",
      "claim_text": "MiroThinker 1.7 存在公开发布页面",
      "claim_type": "existence"
    },
    {
      "claim_id": "c2",
      "claim_text": "MiroThinker 1.7 公开了模型权重",
      "claim_type": "model_weights"
    },
    {
      "claim_id": "c3",
      "claim_text": "MiroThinker 1.7 公开了训练代码",
      "claim_type": "source_code"
    },
    {
      "claim_id": "c4",
      "claim_text": "MiroThinker 1.7 的许可证允许商用",
      "claim_type": "license"
    },
    {
      "claim_id": "c5",
      "claim_text": "MiroThinker 1.7 可以严格称为开源模型",
      "claim_type": "interpretation"
    }
  ]
}
```

## 验收标准

1. 复杂问题至少拆解为 2 个以上可验证命题。
2. 命题应尽量具体、可搜索、可验证。
3. 避免生成无法验证的抽象命题，例如“它是不是很厉害”。

---

# 5.3 搜索计划生成

## 功能说明

系统根据问题类型和命题生成搜索计划。

不同问题类型应优先搜索不同来源。

## 示例：AI 模型信息

优先搜索顺序：

1. 官方网站
2. Hugging Face / ModelScope 模型卡
3. GitHub 仓库
4. arXiv / 论文
5. 官方博客
6. 第三方评测
7. 技术媒体
8. 社区讨论

## 示例：政策法规

优先搜索顺序：

1. 政府官网
2. 法规原文
3. 监管机构公告
4. 法院文件
5. 主流媒体解读
6. 社区讨论

## 输出示例

```json
{
  "search_plan": [
    {
      "claim_id": "c1",
      "queries": [
        "MiroThinker 1.7 Hugging Face",
        "MiroThinker 1.7 GitHub",
        "MiroThinker 1.7 paper"
      ],
      "preferred_source_types": [
        "official_model_card",
        "source_code_repo",
        "academic_paper"
      ]
    }
  ]
}
```

## 验收标准

1. 每个命题至少生成 1 个搜索查询。
2. 不同问题类型应有不同的来源偏好。
3. 支持 strict / balanced / loose 三种搜索模式。

---

# 5.4 搜索适配器

## 功能说明

系统通过外部搜索 API 获取候选结果。

MVP 可选搜索服务：

1. Brave Search API
2. Tavily
3. SerpAPI
4. Bing Search API
5. Google Programmable Search

## 输入

```json
{
  "query": "MiroThinker 1.7 Hugging Face",
  "max_results": 10
}
```

## 输出

```json
{
  "results": [
    {
      "title": "MiroThinker-1.7 - Hugging Face",
      "url": "https://huggingface.co/...",
      "snippet": "...",
      "published_at": null
    }
  ]
}
```

## 验收标准

1. 能获取标题、URL、摘要。
2. 能限制最大结果数。
3. 搜索失败时返回错误状态，不中断整个流程。

---

# 5.5 网页解析

## 功能说明

系统需要抓取网页正文，并尽量去除导航栏、广告、无关内容。

## 技术建议

可使用：

1. trafilatura
2. readability-lxml
3. BeautifulSoup
4. newspaper3k

## 输出示例

```json
{
  "url": "https://huggingface.co/...",
  "title": "MiroThinker-1.7",
  "text": "正文内容...",
  "metadata": {
    "published_at": null,
    "author": null
  }
}
```

## 验收标准

1. 能解析常见网页正文。
2. 解析失败时保留搜索摘要作为 fallback。
3. 对 PDF、GitHub、Hugging Face 等特殊页面后续单独适配。

---

# 5.6 来源类型识别

## 功能说明

系统需要识别每个来源属于哪类。

## 来源类型

```text
official_docs          官方文档
official_blog          官方博客
official_model_card    官方模型卡
source_code_repo       GitHub/GitLab 源码仓库
academic_paper         论文 / 预印本
financial_filing       财报 / SEC 文件
government_docs        政府文件 / 法规
mainstream_media       主流媒体
expert_blog            专家博客
community_forum        社区论坛 / Reddit / 知乎 / X
product_page           商品页 / 厂商参数页
seo_content            SEO 内容站
unknown                未知来源
```

## 识别规则

MVP 可基于域名规则和页面特征：

1. huggingface.co → official_model_card 或 model_hosting
2. github.com / gitlab.com → source_code_repo
3. arxiv.org / openreview.net → academic_paper
4. sec.gov → financial_filing
5. gov 域名 → government_docs
6. docs.* 或 */docs/* → official_docs 候选
7. reddit.com / zhihu.com / x.com → community_forum

## 输出示例

```json
{
  "url": "https://huggingface.co/miromind-ai/MiroThinker-1.7",
  "source_type": "official_model_card",
  "base_reliability": 0.88,
  "is_primary_source": true
}
```

## 验收标准

1. 常见来源能正确分类。
2. 无法识别时返回 unknown。
3. 每种来源类型有默认基础可信度。

---

# 5.7 证据抽取

## 功能说明

系统需要从网页正文中抽取与命题相关的证据。

每条证据需要判断其对命题的关系：

```text
support   支持
oppose    反驳
neutral   中立 / 无关
partial   部分支持
```

## 输入

```json
{
  "claim": "MiroThinker 1.7 公开了模型权重",
  "document_text": "网页正文..."
}
```

## 输出

```json
{
  "evidence": [
    {
      "claim_id": "c2",
      "evidence_text": "页面提供了模型权重下载入口...",
      "support_type": "support",
      "relevance_score": 0.86
    }
  ]
}
```

## 验收标准

1. 每条证据必须对应一个具体命题。
2. 证据文本不能太长，建议控制在 1-3 句话。
3. 支持、反驳、部分支持、无关必须区分。
4. 没有找到证据时返回空数组，而不是编造证据。

---

# 5.8 可信度评分

## 功能说明

系统需要对每条证据进行可信度评分。

## 基础公式

```text
final_score =
  relevance_score
  × source_base_score
  × primary_source_factor
  × recency_factor
  × cross_check_factor
  × conflict_penalty
  × interest_conflict_penalty
```

## 评分因子

### 1. relevance_score

证据与命题的相关程度。

范围：0.0 - 1.0

### 2. source_base_score

来源类型基础可信度。

示例：

```text
official_docs:       0.95
academic_paper:      0.90
official_model_card: 0.88
source_code_repo:    0.88
government_docs:     0.95
mainstream_media:    0.75
expert_blog:         0.65
community_forum:     0.40
seo_content:         0.20
unknown:             0.30
```

### 3. primary_source_factor

一手来源加成。

```text
primary source:      1.10
secondary source:    1.00
unclear source:      0.90
```

### 4. recency_factor

新鲜度因子。

对于 AI 模型、价格、政策、新闻等时效性强的问题，较新来源得分更高。

```text
very_recent:         1.05
normal:              1.00
possibly_outdated:   0.80
outdated:            0.60
```

### 5. cross_check_factor

交叉验证因子。

```text
confirmed_by_independent_sources: 1.15
single_source_only:               1.00
copied_by_multiple_sources:       0.90
```

### 6. conflict_penalty

冲突惩罚。

```text
no_conflict:          1.00
minor_conflict:       0.85
major_conflict:       0.60
```

### 7. interest_conflict_penalty

利益相关惩罚。

```text
no_obvious_conflict:  1.00
self_claim:           0.85
sales_or_marketing:   0.70
```

## 验收标准

1. 每条证据必须有 final_score。
2. 分数应可解释，能展示主要加分/减分原因。
3. 来源基础分和问题类型应支持配置化。

---

# 5.9 命题状态聚合

## 功能说明

系统需要根据一组证据判断每个命题的状态。

## 命题状态

```text
confirmed     高可信证据支持
likely        有较强证据支持，但仍有不足
uncertain     证据不足，无法确认
conflicting   存在明显冲突
unsupported   未找到可靠证据支持
false_likely  有较强证据反驳
```

## 聚合规则示例

### confirmed

满足：

1. 至少一个高可信一手来源支持。
2. 没有高可信反对证据。
3. final_score 高于阈值。

### likely

满足：

1. 有可信来源支持。
2. 但来源数量不足，或不是一手来源。

### uncertain

满足：

1. 只有低可信来源。
2. 或证据相关性较弱。
3. 或证据只能部分支持。

### conflicting

满足：

1. 同一命题下同时存在高分支持证据和高分反驳证据。

### unsupported

满足：

1. 搜索后没有找到足够相关证据。

## 输出示例

```json
{
  "claim_id": "c2",
  "claim_text": "MiroThinker 1.7 公开了模型权重",
  "status": "confirmed",
  "confidence": 0.89,
  "reason": "官方模型卡提供公开模型页面，且来源为一手来源。"
}
```

## 验收标准

1. 每个命题必须有状态。
2. 状态必须与证据分数一致。
3. conflicting 状态不能被自动压平为 likely 或 confirmed。

---

# 5.10 回答约束生成

## 功能说明

系统需要根据命题状态生成 AI 回答约束。

## 约束类型

```text
can_answer_confidently       是否可以确定回答
must_disclose_uncertainty    是否必须披露不确定性
must_cite_sources            是否必须引用来源
forbidden_phrases            禁止使用的表达
required_phrases             必须包含的表达
allowed_tone                 允许的确定性语气
```

## 示例

```json
{
  "answer_constraints": {
    "can_answer_confidently": false,
    "must_disclose_uncertainty": true,
    "must_cite_sources": true,
    "allowed_tone": "cautious",
    "forbidden_phrases": [
      "已经确定",
      "毫无疑问",
      "官方确认"
    ],
    "required_phrases": [
      "目前只能确认",
      "仍需区分权重开放、代码开放、训练数据开放和许可证限制"
    ]
  }
}
```

## 验收标准

1. confirmed 命题允许使用较确定表达。
2. uncertain 命题必须要求 AI 披露不确定性。
3. conflicting 命题必须要求 AI 说明来源冲突。
4. unsupported 命题禁止 AI 下肯定结论。

---

# 六、接口设计

# 6.1 核心 API：可信搜索

## Endpoint

```http
POST /api/v1/trusted-search
```

## 请求参数

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

## 参数说明

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| query | string | 是 | 用户问题 |
| question_type | string | 否 | auto / ai_model_info / tech_news / product_info / policy_legal / technical_doc |
| strictness | string | 否 | loose / balanced / strict |
| max_sources | int | 否 | 最大来源数量 |
| require_primary_source | bool | 否 | 是否强制要求一手来源 |
| return_raw_evidence | bool | 否 | 是否返回原始证据 |

## 返回示例

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
      "status": "confirmed",
      "confidence": 0.91,
      "evidence": [
        {
          "source_id": "s1",
          "support_type": "support",
          "evidence_text": "...",
          "final_score": 0.91
        }
      ]
    },
    {
      "claim_id": "c5",
      "claim_text": "MiroThinker 1.7 可以严格称为开源模型",
      "status": "uncertain",
      "confidence": 0.55,
      "evidence": [
        {
          "source_id": "s1",
          "support_type": "partial",
          "evidence_text": "页面公开了模型信息，但训练数据和完整训练代码开放情况需要进一步核查。",
          "final_score": 0.62
        }
      ]
    }
  ],
  "sources": [
    {
      "source_id": "s1",
      "title": "MiroThinker-1.7 - Hugging Face",
      "url": "https://huggingface.co/...",
      "source_type": "official_model_card",
      "base_reliability": 0.88,
      "is_primary_source": true
    }
  ],
  "conflicts": [],
  "answer_constraints": {
    "can_answer_confidently": false,
    "must_disclose_uncertainty": true,
    "must_cite_sources": true,
    "allowed_tone": "cautious",
    "required_phrases": [
      "可以确认部分信息",
      "但是否严格意义完全开源仍需看许可证、代码和训练数据开放情况"
    ],
    "forbidden_phrases": [
      "毫无疑问是开源模型",
      "已经完全开源"
    ]
  }
}
```

---

# 七、数据结构设计

# 7.1 Question

```text
question_id
query
question_type
risk_level
strictness
created_at
```

# 7.2 Claim

```text
claim_id
question_id
claim_text
claim_type
status
confidence
reason
created_at
```

# 7.3 Source

```text
source_id
url
domain
title
source_type
base_reliability
is_primary_source
published_at
author
fetched_at
```

# 7.4 Evidence

```text
evidence_id
claim_id
source_id
evidence_text
support_type
relevance_score
source_score
primary_source_factor
recency_factor
cross_check_factor
conflict_penalty
interest_conflict_penalty
final_score
created_at
```

# 7.5 Conflict

```text
conflict_id
claim_id
supporting_evidence_ids
opposing_evidence_ids
severity
summary
created_at
```

# 7.6 AnswerConstraints

```text
constraint_id
question_id
can_answer_confidently
must_disclose_uncertainty
must_cite_sources
allowed_tone
required_phrases
forbidden_phrases
created_at
```

---

# 八、配置文件设计

# 8.1 source_policy.yml

```yaml
source_types:
  official_docs:
    base_score: 0.95
    description: "官方文档、产品说明、平台文档"

  official_blog:
    base_score: 0.90
    description: "公司或项目官方博客"

  official_model_card:
    base_score: 0.88
    description: "Hugging Face、ModelScope 等模型卡"

  source_code_repo:
    base_score: 0.88
    description: "GitHub/GitLab 源码仓库"

  academic_paper:
    base_score: 0.90
    description: "论文、预印本、学术出版物"

  government_docs:
    base_score: 0.95
    description: "政府文件、法规、监管公告"

  financial_filing:
    base_score: 0.95
    description: "财报、SEC 文件、交易所公告"

  mainstream_media:
    base_score: 0.75
    description: "主流媒体报道"

  expert_blog:
    base_score: 0.65
    description: "领域专家博客"

  community_forum:
    base_score: 0.40
    description: "论坛、Reddit、知乎、X 等社区内容"

  seo_content:
    base_score: 0.20
    description: "SEO 聚合站、无署名搬运站"

  unknown:
    base_score: 0.30
    description: "未知来源"
```

# 8.2 question_policy.yml

```yaml
question_types:
  ai_model_info:
    preferred_sources:
      - official_docs
      - official_model_card
      - source_code_repo
      - academic_paper
      - official_blog
    weak_sources:
      - community_forum
      - seo_content
    recency_required: true
    min_confidence_for_confirmed: 0.80

  tech_news:
    preferred_sources:
      - official_blog
      - mainstream_media
      - official_docs
    weak_sources:
      - community_forum
      - seo_content
    recency_required: true
    min_confidence_for_confirmed: 0.82

  product_info:
    preferred_sources:
      - official_docs
      - product_page
      - mainstream_media
    weak_sources:
      - community_forum
      - seo_content
    recency_required: true
    min_confidence_for_confirmed: 0.80

  policy_legal:
    preferred_sources:
      - government_docs
      - official_docs
    weak_sources:
      - mainstream_media
      - community_forum
      - seo_content
    recency_required: true
    min_confidence_for_confirmed: 0.88

  technical_doc:
    preferred_sources:
      - official_docs
      - source_code_repo
      - expert_blog
    weak_sources:
      - community_forum
      - seo_content
    recency_required: true
    min_confidence_for_confirmed: 0.78
```

---

# 九、技术方案建议

## 9.1 推荐技术栈

```text
后端框架：FastAPI
数据校验：Pydantic
搜索 API：Brave Search API / Tavily / SerpAPI
网页解析：trafilatura / BeautifulSoup / readability-lxml
规则配置：YAML
数据库：PostgreSQL，MVP 可先不用
缓存：Redis，MVP 可先不用
LLM：用于命题拆解和证据抽取
接口形态：REST API，后续扩展 MCP
```

## 9.2 MVP 阶段模块划分

```text
app/
  api/
    routes/
      trusted_search.py
  core/
    config.py
  services/
    question_classifier.py
    claim_decomposer.py
    search_planner.py
    search_adapter.py
    page_fetcher.py
    source_classifier.py
    evidence_extractor.py
    reliability_scorer.py
    conflict_detector.py
    evidence_package_builder.py
  schemas/
    trusted_search.py
    claim.py
    source.py
    evidence.py
  policies/
    source_policy.yml
    question_policy.yml
  tests/
```

---

# 十、MVP 里程碑

## v0.1：基础可信搜索闭环

目标：完成从 query 到 evidence package 的最小闭环。

功能：

1. 接收用户问题。
2. 自动识别问题类型。
3. 拆解为 2-5 个命题。
4. 调用搜索 API。
5. 获取网页正文。
6. 识别来源类型。
7. 抽取证据。
8. 给证据打分。
9. 返回结构化证据包。

## v0.2：回答约束增强

目标：让返回结果能直接约束 AI 回答。

功能：

1. 输出 answer_constraints。
2. 对不同命题状态生成不同回答口径。
3. 标记 forbidden_phrases 和 required_phrases。

## v0.3：冲突检测

目标：识别支持和反对证据的冲突。

功能：

1. 同一命题下识别 support / oppose。
2. 高分证据冲突时标记 conflicting。
3. 输出冲突摘要。

## v0.4：MCP 工具化

目标：让 Claude、Cursor、Codex、自建 Agent 可以通过 MCP 调用。

功能：

1. 封装 trusted_search 工具。
2. 输出标准 JSON。
3. 提供工具描述和参数 schema。

## v0.5：领域策略扩展

目标：增加更多问题类型和来源规则。

可扩展方向：

1. 医学健康信息核查
2. 金融信息核查
3. 学术论文可信度核查
4. 企业内部知识库可信检索

---

# 十一、验收标准

## 11.1 功能验收

MVP v0.1 完成时，应满足：

1. 输入一个问题后，系统能返回结构化 JSON。
2. JSON 中包含 question_type、claims、sources、evidence、confidence、answer_constraints。
3. 每个 claim 至少有 status 和 confidence。
4. 每个 source 至少有 source_type 和 base_reliability。
5. 每个 evidence 至少有 support_type、relevance_score、final_score。
6. 搜索失败或网页抓取失败时，系统不会崩溃。
7. 没有证据时，系统返回 unsupported，而不是生成虚假证据。

## 11.2 质量验收

选择 20 个测试问题，人工评估：

1. 来源分类准确率 ≥ 80%。
2. 命题拆解基本合理率 ≥ 75%。
3. 证据支持关系判断合理率 ≥ 75%。
4. confirmed 命题中，不应出现明显由低可信来源单独支撑的情况。
5. uncertain / unsupported 问题中，系统不应输出高确定性回答约束。

## 11.3 安全验收

1. 高风险问题不能只凭社区来源给出确定结论。
2. 无法确认的信息必须标注不确定。
3. 冲突证据不能被隐藏。
4. AI 生成回答时应被要求引用来源和说明不确定性。

---

# 十二、测试用例

## 测试用例 1：AI 模型开源性核查

输入：

```text
MiroThinker 1.7 是不是开源模型？
```

期望：

1. question_type = ai_model_info。
2. 拆解出模型存在、权重开放、代码开放、训练数据开放、许可证等命题。
3. Hugging Face 被识别为 official_model_card。
4. 如果不能确认完整训练数据和代码，应返回 uncertain 或 partially_confirmed。
5. answer_constraints 要求谨慎表达。

## 测试用例 2：科技爆料核查

输入：

```text
OpenAI 下周会发布某个代号模型吗？
```

期望：

1. question_type = tech_news。
2. 官方来源缺失时不能 confirmed。
3. 社区爆料只能作为低权重证据。
4. answer_constraints 要求使用“传言”“尚未确认”等表达。

## 测试用例 3：产品参数核查

输入：

```text
某款笔记本的 RTX 5070 Ti 是不是 12GB 显存？
```

期望：

1. question_type = product_info。
2. 优先搜索厂商官网和电商官方参数。
3. 如果不同商品页参数冲突，应标记 conflicting。

## 测试用例 4：政策有效性核查

输入：

```text
某项政策现在还有效吗？
```

期望：

1. question_type = policy_legal。
2. 必须优先使用政府/监管机构来源。
3. 媒体解读不能单独支撑 confirmed。
4. 如果找不到官方来源，应输出 uncertain。

---

# 十三、风险与限制

## 13.1 搜索 API 限制

不同搜索 API 的结果质量和覆盖范围不同，可能影响最终证据质量。

## 13.2 网页抓取失败

部分网站反爬、动态渲染或登录限制会导致正文无法获取。

## 13.3 来源分类误判

仅靠域名规则可能误判来源类型，需要逐步增加规则和人工校正。

## 13.4 LLM 抽取证据可能出错

LLM 可能误判支持/反驳关系，因此关键判断应尽量保留原文证据，并允许人工复核。

## 13.5 可信度评分不是绝对真理

分数代表证据强弱，不代表事实必然正确。

## 13.6 高风险领域需要额外规范

医学、金融、法律建议等领域需要更严格规则，MVP 不应直接支持自动决策。

---

# 十四、未来扩展方向

## 14.1 MCP 工具

将 trusted_search 封装为 MCP 工具，让 Claude、Cursor、Codex、自建 Agent 调用。

## 14.2 浏览器插件

用户浏览网页时，插件可以自动判断当前网页可信度、来源类型、利益相关和证据等级。

## 14.3 写作事实核查助手

用户写公众号、论文、报告时，系统自动标注哪些句子需要证据，哪些证据不足。

## 14.4 企业知识库可信检索

对企业内部文档进行来源分层，例如正式制度、会议纪要、草稿、个人笔记、过期文档等。

## 14.5 证据图谱

将命题、证据、来源、冲突关系构建为图谱，便于追踪事实链条。

## 14.6 来源历史信誉系统

长期记录来源在不同领域的可靠表现，形成领域化信誉评分。

---

# 十五、产品定位总结

Critical Search Layer 的本质不是搜索引擎，而是 AI 搜索过程中的批判性思维层。

普通 AI 搜索解决：

> 信息在哪里？

Critical Search Layer 解决：

> 这个信息值不值得信？  
> 它能支持哪个命题？  
> 它是一手来源还是转述？  
> 有没有相反证据？  
> AI 应该用多确定的语气回答？

最终目标：

> 让 AI 不只是会搜索，而是会怀疑、会验证、会区分证据强弱，并且在证据不足时敢于说“不确定”。

