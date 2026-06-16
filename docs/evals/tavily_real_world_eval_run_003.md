# Tavily Real-world Eval Run 003

版本：v0.2.5-sanitized-eval  
文档类型：Tavily real-world eval 脱敏记录  
数据来源：`tavily_eval_run_003_sanitized.json`

---

# 1. 记录边界

本文件只根据脱敏 JSON 摘要整理，不包含 API key、Authorization header、raw provider payload 或完整网页正文。`evidence` 仅保留 JSON 中已有的短摘录。

全局运行信息：

```yaml
run_time: 2026-06-16T22:05:05.052637Z
provider: tavily
endpoint_or_entrypoint: /api/v1/trusted-search
opt_in_env_used: yes
tavily_network_enabled: yes
api_key_present: yes
```

---

# 2. Run 002 对比摘要

v0.2.5 的 source-type ranking/filtering 已经对部分样本生效：`ai_model_info` 样本中，final sources 从 run_002 的 `unknown` 二手/第三方来源，前移到 `official_model_card`、`source_code_repo` 等 primary source type。

但 run_003 同时暴露了新的关键缺口：source type 与目标实体/domain 没有对齐。换句话说，系统能把 Hugging Face / GitHub 这类 source type 排到前面，但还不能确认这些来源是否属于目标实体的一手官方源。

逐项对比：

| eval_id | run_002 final source pattern | run_003 final source pattern | source-type ranking observation |
|---|---|---|---|
| eval_001 | Azure / OpenRouter, both `unknown` | Hugging Face / Hugging Face, both `official_model_card` | source type 明显前移，但 GPT-4.1 的理想 primary source 应是 OpenAI 官方源 |
| eval_002 | Ollama / IBM, both `unknown` | Hugging Face / GitHub, `official_model_card` + `source_code_repo` | 可能改善，但仍需确认是否属于 Meta / Llama 官方实体 |
| eval_003 | TMTPost / OpenAI, both `unknown` | TMTPost / OpenAI, both `unknown` | OpenAI 域名仍未被 source_classifier 识别为官方来源 |
| eval_004 | Zhihu / ZFrontier | Zhihu / Reddit, both `community_forum` | 产品规格类官方候选召回仍不足 |
| eval_005 | Securities Times / Caixin, both `unknown` | iThome / TDCC, both `unknown` | policy/legal 官方候选召回仍不足，未命中 `sec.gov` |

---

# eval_001

## Basic Info

```yaml
eval_id: eval_001
run_time: 2026-06-16T22:05:05.052637Z
query: GPT-4.1 是否是 OpenAI 发布的模型？
question_type: ai_model_info
strictness: balanced
max_sources: 2
provider: tavily
endpoint_or_entrypoint: /api/v1/trusted-search
opt_in_env_used: yes
tavily_network_enabled: yes
status: completed
```

## Response Summary

```yaml
overall_status: partially_confirmed
overall_confidence: 0.4017
claims_count: 6
sources_count: 2
evidence_count: 3
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
| s1 | @samihalawa on Hugging Face: "BREAKING NEWS! 🚀 OpenAI’s GPT-4.1 API Models Are Here – Built for Developers…" | huggingface.co | official_model_card | 0.88 | true | not_reviewed | not_provided_in_json |
| s2 | gpt-4.1-2025-04-14.json · level8/flower at main | huggingface.co | official_model_card | 0.88 | true | not_reviewed | not_provided_in_json |

## Claims

| claim_id | claim_text | claim_type | status | confidence | evidence_count | human_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|
| c1 | GPT-4.1 是否存在公开发布页面 | existence | likely | 0.7938 | 1 | not_reviewed | not_provided_in_json |
| c2 | GPT-4.1 是否公开模型权重 | model_weights | unsupported | 0.0 | 0 | not_reviewed | not_provided_in_json |
| c3 | GPT-4.1 是否公开训练代码 | source_code | likely | 0.7938 | 1 | not_reviewed | not_provided_in_json |
| c4 | GPT-4.1 是否公开训练数据 | training_data | confirmed | 0.8228 | 1 | not_reviewed | not_provided_in_json |
| c5 | GPT-4.1 的许可证是否允许商用 | license | unsupported | 0.0 | 0 | not_reviewed | not_provided_in_json |
| c6 | GPT-4.1 是否能严格称为开源模型 | interpretation | unsupported | 0.0 | 0 | not_reviewed | not_provided_in_json |

## Evidence

| evidence_id | claim_id | source_id | support_type | relevance_score | final_score | short excerpt | human_support_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|---|
| ev-c1-s1-1 | c1 | s1 | support | 0.82 | 0.7938 | • API Only: Available via OpenAI API and Playground—ChatGPT remains on GPT-4o. | not_reviewed | not_provided_in_json |
| ev-c3-s1-1 | c3 | s1 | support | 0.82 | 0.7938 | • Long Context: All models support up to 1 million tokens—8x more than GPT-4o—enabling full repo analysis and deep document comprehension. | not_reviewed | not_provided_in_json |
| ev-c4-s2-1 | c4 | s2 | support | 0.85 | 0.8228 | # Datasets:. Dataset cardFiles Files and versions xetCommunity. | not_reviewed | not_provided_in_json |

## Human Conclusion

Run 003 shows source-type ranking is active: both final sources are `huggingface.co` and classified as `official_model_card`, unlike run_002 where final sources were Azure and OpenRouter with `unknown` source type.

However, for the query “GPT-4.1 是否是 OpenAI 发布的模型？”, the ideal primary source should be OpenAI official source, not arbitrary Hugging Face pages. This is an entity/domain alignment problem: `source_type=official_model_card` does not guarantee the source is the target entity’s official source. The high source-type score may therefore over-promote non-OpenAI-controlled pages.

---

# eval_002

## Basic Info

```yaml
eval_id: eval_002
run_time: 2026-06-16T22:05:05.052637Z
query: Llama 3.1 是否公开模型权重并允许商用？
question_type: ai_model_info
strictness: balanced
max_sources: 2
provider: tavily
endpoint_or_entrypoint: /api/v1/trusted-search
opt_in_env_used: yes
tavily_network_enabled: yes
status: completed
```

## Response Summary

```yaml
overall_status: partially_confirmed
overall_confidence: 0.5163
claims_count: 6
sources_count: 2
evidence_count: 5
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
| s1 | Llama 3.1 - 405B, 70B & 8B with multilinguality and long context | huggingface.co | official_model_card | 0.88 | true | not_reviewed | not_provided_in_json |
| s2 | The official Meta Llama 3 GitHub site | github.com | source_code_repo | 0.88 | true | not_reviewed | not_provided_in_json |

## Claims

| claim_id | claim_text | claim_type | status | confidence | evidence_count | human_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|
| c1 | Llama 3.1 是否存在公开发布页面 | existence | confirmed | 0.8518 | 2 | not_reviewed | not_provided_in_json |
| c2 | Llama 3.1 是否公开模型权重 | model_weights | unsupported | 0.0 | 0 | not_reviewed | not_provided_in_json |
| c3 | Llama 3.1 是否公开训练代码 | source_code | likely | 0.7938 | 1 | not_reviewed | not_provided_in_json |
| c4 | Llama 3.1 是否公开训练数据 | training_data | likely | 0.7938 | 1 | not_reviewed | not_provided_in_json |
| c5 | Llama 3.1 的许可证是否允许商用 | license | unsupported | 0.0 | 0 | not_reviewed | not_provided_in_json |
| c6 | Llama 3.1 是否能严格称为开源模型 | interpretation | uncertain | 0.6582 | 1 | not_reviewed | not_provided_in_json |

## Evidence

| evidence_id | claim_id | source_id | support_type | relevance_score | final_score | short excerpt | human_support_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|---|
| ev-c1-s1-1 | c1 | s1 | support | 0.88 | 0.8518 | Eight open-weight models (3 base models and 5 fine-tuned ones) are available on the Hub. In addition to the six generative models, Meta released two new models: Llama Guard 3 an... | not_reviewed | not_provided_in_json |
| ev-c1-s2-1 | c1 | s2 | support | 0.82 | 0.7938 | As part of the Llama 3.1 release, we've consolidated GitHub repos and added some additional repos as we've expanded Llama's functionality into | not_reviewed | not_provided_in_json |
| ev-c3-s2-1 | c3 | s2 | support | 0.82 | 0.7938 | As part of the Llama 3.1 release, we've consolidated GitHub repos and added some additional repos as we've expanded Llama's functionality into | not_reviewed | not_provided_in_json |
| ev-c4-s1-1 | c4 | s1 | support | 0.82 | 0.7938 | Llama 3.1 comes in three sizes: 8B for efficient deployment and development on consumer-size GPU, 70B for large-scale AI native applications, and 405B for synthetic data, LLM as... | not_reviewed | not_provided_in_json |
| ev-c6-s1-1 | c6 | s1 | partial | 0.68 | 0.6582 | Eight open-weight models (3 base models and 5 fine-tuned ones) are available on the Hub. | not_reviewed | not_provided_in_json |

## Human Conclusion

Run 003 likely improves over run_002: final sources moved from Ollama/IBM `unknown` sources to Hugging Face `official_model_card` and GitHub `source_code_repo`.

This is promising for Llama 3.1, but the record still needs entity-aware review. A Hugging Face model page or GitHub repository should be checked against the target entity: is it Meta / Llama official, or merely a related mirror, community repo, or secondary page? The JSON does not provide enough human review to conclude that both final sources are official Meta/Llama-controlled sources.

---

# eval_003

## Basic Info

```yaml
eval_id: eval_003
run_time: 2026-06-16T22:05:05.052637Z
query: OpenAI 最近是否发布了新的语音模型？
question_type: tech_news
strictness: balanced
max_sources: 2
provider: tavily
endpoint_or_entrypoint: /api/v1/trusted-search
opt_in_env_used: yes
tavily_network_enabled: yes
status: completed
```

## Response Summary

```yaml
overall_status: uncertain
overall_confidence: 0.264
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
| c1 | OpenAI 最近是否发布了新的语音模型？ 这一问题可以被外部来源验证 | general_fact | uncertain | 0.264 | 2 | not_reviewed | not_provided_in_json |

## Evidence

| evidence_id | claim_id | source_id | support_type | relevance_score | final_score | short excerpt | human_support_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|---|
| ev-c1-s1-1 | c1 | s1 | support | 0.85 | 0.255 | 昨天凌晨，OpenAI发布了三款音频模型：GPT-Realtime-2、GPT-Realtime-Translate和GPT-Realtime-Whisper。 OpenAI官网的表述是，新模型可以让开发者构建能 | not_reviewed | not_provided_in_json |
| ev-c1-s2-1 | c1 | s2 | support | 0.88 | 0.264 | # 应对合成语音的挑战与机遇 \| OpenAI. OpenAI 致力于开发安全可靠、惠及全员的 AI⁠。今天，我们将分享一款名为“Voice Engine”的模型在小规模技术预览中的初步洞察与结果。 | not_reviewed | not_provided_in_json |

## Human Conclusion

Run 003 again includes `openai.com`, but source_type remains `unknown` with base reliability 0.3 and `is_primary_source=false`. This confirms the run_002 finding: `source_classifier` does not yet recognize OpenAI official domains as official source types.

Because the OpenAI page is not classified as official, source-type ranking cannot reliably prefer it over media sources. The output remains cautious and uncertain, which is appropriate for the classified evidence package.

---

# eval_004

## Basic Info

```yaml
eval_id: eval_004
run_time: 2026-06-16T22:05:05.052637Z
query: RTX 5070 Ti 是否是 16GB 显存？
question_type: product_info
strictness: balanced
max_sources: 2
provider: tavily
endpoint_or_entrypoint: /api/v1/trusted-search
opt_in_env_used: yes
tavily_network_enabled: yes
status: completed
```

## Response Summary

```yaml
overall_status: uncertain
overall_confidence: 0.36
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
| s2 | RTX 5070 Ti 和 RTX 5060 Ti 16GB 显卡已停产。 : r/LocalLLaMA | reddit.com | community_forum | 0.4 | false | not_reviewed | not_provided_in_json |

## Claims

| claim_id | claim_text | claim_type | status | confidence | evidence_count | human_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|
| c1 | RTX 5070 Ti 是否是 16GB 显存？ 这一问题可以被外部来源验证 | general_fact | uncertain | 0.36 | 2 | not_reviewed | not_provided_in_json |

## Evidence

| evidence_id | claim_id | source_id | support_type | relevance_score | final_score | short excerpt | human_support_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|---|
| ev-c1-s1-1 | c1 | s1 | support | 0.85 | 0.34 | 这使得RTX 5070 Ti在图形处理、光线追踪及AI相关任务上理论性能更强。 显存部分，RTX 5070 Ti配备16GB GDDR7 显存，位宽256bit，显存带宽达896GB/s；RTX 4070 | not_reviewed | not_provided_in_json |
| ev-c1-s2-1 | c1 | s2 | support | 0.9 | 0.36 | # RTX 5070 Ti 和 RTX 5060 Ti 16GB 显卡已停产。 Skip to main contentRTX 5070 Ti 和 RTX 5060 Ti 16GB 显卡已停产。 | not_reviewed | not_provided_in_json |

## Human Conclusion

Run 003 still returns Zhihu and Reddit, both `community_forum`, for a product specification query. This means the product_info path still lacks stable official candidate recall for manufacturer or specification sources.

Source-type ranking cannot promote an official product/spec page if the candidate pool does not contain one. The cautious `uncertain` result is appropriate under these sources.

---

# eval_005

## Basic Info

```yaml
eval_id: eval_005
run_time: 2026-06-16T22:05:05.052637Z
query: 美国 SEC 是否发布过关于比特币现货 ETF 的批准公告？
question_type: policy_legal
strictness: balanced
max_sources: 2
provider: tavily
endpoint_or_entrypoint: /api/v1/trusted-search
opt_in_env_used: yes
tavily_network_enabled: yes
status: completed
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
| s1 | 美國SEC正式批准比特幣現貨ETF，預計周四開始交易 \| iThome | ithome.com.tw | unknown | 0.3 | false | not_reviewed | not_provided_in_json |
| s2 | 集保電子雙月刊 | tdcc.com.tw | unknown | 0.3 | false | not_reviewed | not_provided_in_json |

## Claims

| claim_id | claim_text | claim_type | status | confidence | evidence_count | human_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|
| c1 | 美国 SEC 是否发布过关于比特币现货 ETF 的批准公告？ 这一问题可以被外部来源验证 | general_fact | uncertain | 0.27 | 2 | not_reviewed | not_provided_in_json |

## Evidence

| evidence_id | claim_id | source_id | support_type | relevance_score | final_score | short excerpt | human_support_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|---|
| ev-c1-s1-1 | c1 | s1 | oppose | 0.86 | 0.258 | # 美國SEC正式批准比特幣現貨ETF，預計周四開始交易. 在拒絕放行比特幣現貨交易產品的官司敗訴後，迫使美國證券交易委員會（SEC）在1月10日對外公告，開放民間進行比特幣現貨ETF上市與交易. | not_reviewed | not_provided_in_json |
| ev-c1-s2-1 | c1 | s2 | support | 0.9 | 0.27 | # 從美國SEC核准發行比特幣現貨ETF看我國虛擬資產監管. 一如市場預期，美國證券交易委員會(SEC)在當地時間2024年1月11日，正式批准包含貝萊德(Blackrock)、方舟(ARK Invest)及灰度(Grayscale)等公司所提交的11檔比特幣現貨ETF申請 | not_reviewed | not_provided_in_json |

## Human Conclusion

Run 003 still does not hit `sec.gov`. The final sources are non-SEC `unknown` domains, so policy/legal official candidate recall remains insufficient.

The first evidence item appears to say SEC formally approved spot bitcoin ETF/ETP listing, yet it is marked `oppose`. This resembles the run_002 claim-scope confusion: wording about approval context or constraints can be misread as opposition to the claim that SEC issued an approval announcement.

---

# 3. Overall Human Conclusion

v0.2.5 source-type ranking is working in the narrow sense that higher source types can move ahead of lower source types when candidates exist. This is visible in eval_001 and eval_002, where Hugging Face and GitHub primary source types entered final sources.

However, run_003 exposes the next quality gap: source type is not the same as entity-aware officialness. A source can be `official_model_card` by domain policy while still not being the target entity’s primary official source. For GPT-4.1, a Hugging Face page is not an OpenAI official source merely because Hugging Face is classified as `official_model_card`.

The remaining issues are:

- entity/domain alignment is missing for official source promotion;
- OpenAI official domains are still classified as `unknown`;
- product_info still lacks manufacturer/specification source recall;
- policy_legal still lacks SEC official source recall;
- evidence extraction still shows claim-scope confusion in the SEC sample.

The cautious answer constraints remain appropriate. The next improvement should not be scorer or aggregator tuning; it should be entity-aware official source guard plus targeted source_classifier/SearchPlanner coverage.
