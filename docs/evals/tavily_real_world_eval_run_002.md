# Tavily Real-world Eval Run 002

版本：v0.2.4-sanitized-eval  
文档类型：Tavily real-world eval 脱敏记录  
数据来源：`tavily_eval_run_002_sanitized.json`

---

# 1. 记录边界

本文件只根据脱敏 JSON 摘要整理，不包含 API key、Authorization header、raw provider
payload 或完整网页正文。`evidence` 仅保留 JSON 中已有的短摘录。

全局运行信息：

```yaml
run_time: 2026-06-16T14:45:59.579159Z
provider: tavily
endpoint_or_entrypoint: /api/v1/trusted-search
opt_in_env_used: yes
tavily_network_enabled: yes
api_key_present: yes
```

---

# eval_001

## Basic Info

```yaml
eval_id: eval_001
run_time: 2026-06-16T14:45:59.579159Z
query: GPT-4.1 是否是 OpenAI 发布的模型？
question_type: ai_model_info
strictness: balanced
max_sources: 2
provider: tavily
endpoint_or_entrypoint: /api/v1/trusted-search
opt_in_env_used: yes
tavily_network_enabled: yes
status: completed
data_completeness: incomplete_human_review_fields
```

## Response Summary

```yaml
overall_status: uncertain
overall_confidence: 0.0425
claims_count: 6
sources_count: 2
evidence_count: 1
conflicts_count: 0
answer_allowed_tone: cautious
must_disclose_uncertainty: true
can_answer_confidently: false
page_fetch_status_counts:
  fallback: 2
```

## Sources

| source_id | title | domain | source_type | base_reliability | is_primary_source | human_source_type_judgment | suspected_issue |
|---|---|---|---|---:|---|---|---|
| s1 | Announcing the GPT-4.1 model series for Azure AI Foundry and GitHub developers | azure.microsoft.com | unknown | 0.3 | false | not_reviewed | not_provided_in_json |
| s2 | GPT-4.1 - API Pricing & Benchmarks | openrouter.ai | unknown | 0.3 | false | not_reviewed | not_provided_in_json |

## Claims

| claim_id | claim_text | claim_type | status | confidence | evidence_count | human_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|
| c1 | GPT-4.1 是否存在公开发布页面 | existence | unsupported | 0.0 | 0 | not_reviewed | not_provided_in_json |
| c2 | GPT-4.1 是否公开模型权重 | model_weights | unsupported | 0.0 | 0 | not_reviewed | not_provided_in_json |
| c3 | GPT-4.1 是否公开训练代码 | source_code | uncertain | 0.255 | 1 | not_reviewed | not_provided_in_json |
| c4 | GPT-4.1 是否公开训练数据 | training_data | unsupported | 0.0 | 0 | not_reviewed | not_provided_in_json |
| c5 | GPT-4.1 的许可证是否允许商用 | license | unsupported | 0.0 | 0 | not_reviewed | not_provided_in_json |
| c6 | GPT-4.1 是否能严格称为开源模型 | interpretation | unsupported | 0.0 | 0 | not_reviewed | not_provided_in_json |

## Evidence

| evidence_id | claim_id | source_id | support_type | relevance_score | final_score | short excerpt | human_support_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|---|
| ev-c3-s1-1 | c3 | s1 | support | 0.85 | 0.255 | Announcing the GPT-4.1 model series for Azure AI Foundry and GitHub developers. We are excited to share the launch of the next iteration of the GPT model series with GPT-4.1,... | not_reviewed | not_provided_in_json |

## Quality Scoring

| metric | score | reason |
|---|---:|---|
| search_relevance_score | incomplete | 1-5 score not provided in sanitized JSON. |
| source_quality_score | incomplete | 1-5 score not provided in sanitized JSON. |
| evidence_quality_score | incomplete | 1-5 score not provided in sanitized JSON. |
| answer_constraint_score | incomplete | 1-5 score not provided in sanitized JSON. |

## Human Conclusion

Sanitized JSON shows no OpenAI official source in final sources. The result improved away from
Zhihu/Reddit but still landed on Azure and OpenRouter, both classified as `unknown`.
Human review fields are incomplete, so no stronger conclusion is recorded here.

---

# eval_002

## Basic Info

```yaml
eval_id: eval_002
run_time: 2026-06-16T14:45:59.579159Z
query: Llama 3.1 是否公开模型权重并允许商用？
question_type: ai_model_info
strictness: balanced
max_sources: 2
provider: tavily
endpoint_or_entrypoint: /api/v1/trusted-search
opt_in_env_used: yes
tavily_network_enabled: yes
status: completed
data_completeness: incomplete_human_review_fields
```

## Response Summary

```yaml
overall_status: uncertain
overall_confidence: 0.1029
claims_count: 6
sources_count: 2
evidence_count: 4
conflicts_count: 0
answer_allowed_tone: cautious
must_disclose_uncertainty: true
can_answer_confidently: false
page_fetch_status_counts:
  fallback: 2
```

## Sources

| source_id | title | domain | source_type | base_reliability | is_primary_source | human_source_type_judgment | suspected_issue |
|---|---|---|---|---:|---|---|---|
| s1 | llama3.1 | ollama.com | unknown | 0.3 | false | not_reviewed | not_provided_in_json |
| s2 | Meta releases new Llama 3.1 models, including highly ... - IBM | ibm.com | unknown | 0.3 | false | not_reviewed | not_provided_in_json |

## Claims

| claim_id | claim_text | claim_type | status | confidence | evidence_count | human_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|
| c1 | Llama 3.1 是否存在公开发布页面 | existence | uncertain | 0.264 | 2 | not_reviewed | not_provided_in_json |
| c2 | Llama 3.1 是否公开模型权重 | model_weights | unsupported | 0.0 | 0 | not_reviewed | not_provided_in_json |
| c3 | Llama 3.1 是否公开训练代码 | source_code | unsupported | 0.0 | 0 | not_reviewed | not_provided_in_json |
| c4 | Llama 3.1 是否公开训练数据 | training_data | unsupported | 0.0 | 0 | not_reviewed | not_provided_in_json |
| c5 | Llama 3.1 的许可证是否允许商用 | license | uncertain | 0.0984 | 1 | not_reviewed | not_provided_in_json |
| c6 | Llama 3.1 是否能严格称为开源模型 | interpretation | uncertain | 0.255 | 1 | not_reviewed | not_provided_in_json |

## Evidence

| evidence_id | claim_id | source_id | support_type | relevance_score | final_score | short excerpt | human_support_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|---|
| ev-c1-s1-1 | c1 | s1 | support | 0.88 | 0.264 | Llama 3.1 is a new state-of-the-art model from Meta available in 8B, 70B and 405B parameter sizes. Llama 3.1 family of models available... | not_reviewed | not_provided_in_json |
| ev-c1-s2-1 | c1 | s2 | support | 0.82 | 0.246 | The instruction-tuned Llama 3.1-405B, which figures to be the largest and most powerful open source language model available today... | not_reviewed | not_provided_in_json |
| ev-c5-s1-1 | c5 | s1 | support | 0.328 | 0.0984 | Meta also has made changes to their license, allowing developers to use the outputs from Llama models, including the 405B model, to improve other models. | not_reviewed | not_provided_in_json |
| ev-c6-s2-1 | c6 | s2 | support | 0.85 | 0.255 | Llama 3.1 comprises both pretrained and instruction-tuned text in/text out open source generative AI models in sizes of 8B, 70B... | not_reviewed | not_provided_in_json |

## Quality Scoring

| metric | score | reason |
|---|---:|---|
| search_relevance_score | incomplete | 1-5 score not provided in sanitized JSON. |
| source_quality_score | incomplete | 1-5 score not provided in sanitized JSON. |
| evidence_quality_score | incomplete | 1-5 score not provided in sanitized JSON. |
| answer_constraint_score | incomplete | 1-5 score not provided in sanitized JSON. |

## Human Conclusion

Sanitized JSON shows no Meta, llama.com, Hugging Face, or ModelScope official source in final
sources. CSDN/QbitAI did not appear, but sources are still non-primary and classified as
`unknown`. Evidence stayed low-scored because source reliability is low.

---

# eval_003

## Basic Info

```yaml
eval_id: eval_003
run_time: 2026-06-16T14:45:59.579159Z
query: OpenAI 最近是否发布了新的语音模型？
question_type: tech_news
strictness: balanced
max_sources: 2
provider: tavily
endpoint_or_entrypoint: /api/v1/trusted-search
opt_in_env_used: yes
tavily_network_enabled: yes
status: completed
data_completeness: incomplete_human_review_fields
```

## Response Summary

```yaml
overall_status: uncertain
overall_confidence: 0.27
claims_count: 1
sources_count: 2
evidence_count: 2
conflicts_count: 0
answer_allowed_tone: cautious
must_disclose_uncertainty: true
can_answer_confidently: false
page_fetch_status_counts:
  fallback: 2
```

## Sources

| source_id | title | domain | source_type | base_reliability | is_primary_source | human_source_type_judgment | suspected_issue |
|---|---|---|---|---:|---|---|---|
| s1 | AI有嘴了，OpenAI连发三语音模型-钛媒体官方网站 | tmtpost.com | unknown | 0.3 | false | not_reviewed | not_provided_in_json |
| s2 | 应对合成语音的挑战与机遇 | openai.com | unknown | 0.3 | false | not_reviewed | not_provided_in_json |

## Claims

| claim_id | claim_text | claim_type | status | confidence | evidence_count | human_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|
| c1 | OpenAI 最近是否发布了新的语音模型？ 这一问题可以被外部来源验证 | general_fact | uncertain | 0.27 | 2 | not_reviewed | not_provided_in_json |

## Evidence

| evidence_id | claim_id | source_id | support_type | relevance_score | final_score | short excerpt | human_support_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|---|
| ev-c1-s1-1 | c1 | s1 | support | 0.9 | 0.27 | AI有嘴了，OpenAI连发三语音模型. 昨天凌晨，OpenAI发布了三款音频模型：GPT-Realtime-2、GPT-Realtime-Translate和... | not_reviewed | not_provided_in_json |
| ev-c1-s2-1 | c1 | s2 | support | 0.88 | 0.264 | 应对合成语音的挑战与机遇 \| OpenAI. OpenAI 致力于开发安全可靠、惠及全员的 AI。今天，我们将分享... | not_reviewed | not_provided_in_json |

## Quality Scoring

| metric | score | reason |
|---|---:|---|
| search_relevance_score | incomplete | 1-5 score not provided in sanitized JSON. |
| source_quality_score | incomplete | 1-5 score not provided in sanitized JSON. |
| evidence_quality_score | incomplete | 1-5 score not provided in sanitized JSON. |
| answer_constraint_score | incomplete | 1-5 score not provided in sanitized JSON. |

## Human Conclusion

Sanitized JSON includes one `openai.com` source but it is classified as `unknown`, not official
docs/blog. The package remains cautious and uncertain. Human review data is incomplete.

---

# eval_004

## Basic Info

```yaml
eval_id: eval_004
run_time: 2026-06-16T14:45:59.579159Z
query: RTX 5070 Ti 是否是 16GB 显存？
question_type: product_info
strictness: balanced
max_sources: 2
provider: tavily
endpoint_or_entrypoint: /api/v1/trusted-search
opt_in_env_used: yes
tavily_network_enabled: yes
status: completed
data_completeness: incomplete_human_review_fields
```

## Response Summary

```yaml
overall_status: uncertain
overall_confidence: 0.34
claims_count: 1
sources_count: 2
evidence_count: 2
conflicts_count: 0
answer_allowed_tone: cautious
must_disclose_uncertainty: true
can_answer_confidently: false
page_fetch_status_counts:
  fallback: 2
```

## Sources

| source_id | title | domain | source_type | base_reliability | is_primary_source | human_source_type_judgment | suspected_issue |
|---|---|---|---|---:|---|---|---|
| s1 | 影驰RTX 5070 Ti HOF OC LAB 黑魂X - 知乎专栏 | zhuanlan.zhihu.com | community_forum | 0.4 | false | not_reviewed | not_provided_in_json |
| s2 | 最值得买的50系显卡？iGame GeForce RTX 5070 Ti Advanced OC ... | zfrontier.com | unknown | 0.3 | false | not_reviewed | not_provided_in_json |

## Claims

| claim_id | claim_text | claim_type | status | confidence | evidence_count | human_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|
| c1 | RTX 5070 Ti 是否是 16GB 显存？ 这一问题可以被外部来源验证 | general_fact | uncertain | 0.34 | 2 | not_reviewed | not_provided_in_json |

## Evidence

| evidence_id | claim_id | source_id | support_type | relevance_score | final_score | short excerpt | human_support_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|---|
| ev-c1-s1-1 | c1 | s1 | support | 0.85 | 0.34 | 这使得RTX 5070 Ti在图形处理、光线追踪及AI相关任务上理论性能更强。显存部分，RTX 5070 Ti配备16GB... | not_reviewed | not_provided_in_json |
| ev-c1-s2-1 | c1 | s2 | support | 0.82 | 0.246 | RTX 5070Ti 显卡一样采用了最新的NVIDIA Blackwell架构...8960个CUDA核心数量和16GB GDDR 7高速显存... | not_reviewed | not_provided_in_json |

## Quality Scoring

| metric | score | reason |
|---|---:|---|
| search_relevance_score | incomplete | 1-5 score not provided in sanitized JSON. |
| source_quality_score | incomplete | 1-5 score not provided in sanitized JSON. |
| evidence_quality_score | incomplete | 1-5 score not provided in sanitized JSON. |
| answer_constraint_score | incomplete | 1-5 score not provided in sanitized JSON. |

## Human Conclusion

Sanitized JSON shows evidence supporting 16GB, but final sources are Zhihu and ZFrontier rather
than NVIDIA or board-partner official product pages. The package remains cautious and uncertain.
Human review data is incomplete.

---

# eval_005

## Basic Info

```yaml
eval_id: eval_005
run_time: 2026-06-16T14:45:59.579159Z
query: 美国 SEC 是否发布过关于比特币现货 ETF 的批准公告？
question_type: policy_legal
strictness: balanced
max_sources: 2
provider: tavily
endpoint_or_entrypoint: /api/v1/trusted-search
opt_in_env_used: yes
tavily_network_enabled: yes
status: completed
data_completeness: incomplete_human_review_fields
```

## Response Summary

```yaml
overall_status: unsupported
overall_confidence: 0.0
claims_count: 1
sources_count: 2
evidence_count: 2
conflicts_count: 0
answer_allowed_tone: cautious
must_disclose_uncertainty: true
can_answer_confidently: false
page_fetch_status_counts:
  fallback: 2
```

## Sources

| source_id | title | domain | source_type | base_reliability | is_primary_source | human_source_type_judgment | suspected_issue |
|---|---|---|---|---:|---|---|---|
| s1 | 11只比特币现货ETF获批上市！美国证交会主席最新声明 - 证券时报 | stcn.com | unknown | 0.3 | false | secondary_source | missing_official_primary_source |
| s2 | 美SEC批准现货比特币ETF上市同时提示加密货币风险 - Caixin | finance.caixin.com | unknown | 0.3 | false | secondary_source | missing_official_primary_source |

## Claims

| claim_id | claim_text | claim_type | status | confidence | evidence_count | human_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|
| c1 | 美国 SEC 是否发布过关于比特币现货 ETF 的批准公告？ 这一问题可以被外部来源验证 | general_fact | unsupported | 0.0 | 2 | status appears too weak given secondary-source evidence says SEC approved spot bitcoin ETP listing | missing_official_primary_source; evidence_extractor_claim_scope_confusion |

## Evidence

| evidence_id | claim_id | source_id | support_type | relevance_score | final_score | short excerpt | human_support_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|---|
| ev-c1-s1-1 | c1 | s1 | oppose | 0.78 | 0.234 | 据证券时报，“美国证券交易委员会的@SECGov X / Twitter账户已被泄露。关于比特币ETF的未经授权的推文不是由SEC... | discusses unauthorized tweet, not the final SEC approval notice | missing_official_primary_source; evidence_extractor_claim_scope_confusion |
| ev-c1-s2-1 | c1 | s2 | oppose | 0.78 | 0.234 | SEC主席根斯勒声明，虽然SEC批准了现货比特币ETP上市，但并未批准或认可比特币。投资者应对比特币... | incorrectly treated as oppose; it supports SEC approved ETP listing while distinguishing approval from endorsing bitcoin | missing_official_primary_source; evidence_extractor_claim_scope_confusion |

## Quality Scoring

| metric | score | reason |
|---|---:|---|
| search_relevance_score | incomplete | 1-5 score not provided in sanitized JSON. |
| source_quality_score | incomplete | 1-5 score not provided in sanitized JSON; final sources are secondary media, not SEC official. |
| evidence_quality_score | incomplete | 1-5 score not provided in sanitized JSON; evidence scope confusion is visible in the summary. |
| answer_constraint_score | incomplete | 1-5 score not provided in sanitized JSON. |

## Human Conclusion

Eval 005 did not recall an SEC official source. The final sources are secondary sources from
Securities Times and Caixin. The Caixin excerpt says SEC approved spot bitcoin ETP listing but did
not approve or endorse bitcoin; this was classified as `oppose`, which confuses the claim scope.

Key suspected issues:

- `missing_official_primary_source`
- `evidence_extractor_claim_scope_confusion`

