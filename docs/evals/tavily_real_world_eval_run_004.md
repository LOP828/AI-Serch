# Tavily Real-world Eval Run 004

版本：v0.2.6-sanitized-eval  
文档类型：Tavily real-world eval 脱敏记录  
数据来源：`tavily_eval_run_004_sanitized.json`

---

# 1. 记录边界

本文件只根据脱敏 JSON 摘要整理，不包含 API key、Authorization header、raw provider payload 或完整网页正文。`evidence` 仅保留 JSON 中已有的短摘录。

全局运行信息：

```yaml
run_time: 2026-06-16T22:59:37.753905Z
provider: tavily
endpoint_or_entrypoint: /api/v1/trusted-search
opt_in_env_used: yes
tavily_network_enabled: yes
api_key_present: yes
```

---

# 2. Run 003 对比摘要

v0.2.6 的三刀改动对官方来源召回、分类和排序有明显改善：

| eval_id | run_003 final source pattern | run_004 final source pattern | v0.2.6 observation |
|---|---|---|---|
| eval_001 | Hugging Face / Hugging Face, both `official_model_card` | `platform.openai.com` / `platform.openai.com`, both `official_docs` | OpenAI 官方源已进入 final sources，但 evidence 为空，问题转移到 claim decomposition / evidence semantics |
| eval_002 | Hugging Face / GitHub | Hugging Face / GitHub | 与 run_003 基本一致，仍为模型卡 / 代码仓库类 primary source |
| eval_003 | TMTPost / OpenAI, both `unknown` | `openai.com` / `openai.com`, both `official_docs` | OpenAI 官方域名分类和排序生效，overall_status 变为 `confirmed` |
| eval_004 | Zhihu / Reddit, both `community_forum` | `nvidia.com` / `nvidia.com`, both `product_page` | NVIDIA 官方域进入 final sources，overall_status 变为 `mostly_confirmed` |
| eval_005 | iThome / TDCC, both `unknown` | `sec.gov` / `sec.gov`, both `government_docs` | SEC 官方源进入 final sources，overall_status 变为 `confirmed` |

Human interpretation:

- v0.2.6 official-source recall / classification / ranking 三刀有效。
- 系统已从“官方源进不来”推进到“官方源已进入，但部分 claim 语义仍需修”。
- eval_001 不应被解读为官方源失败；它应记录为 claim decomposition / evidence extraction 下一层问题。

---

# eval_001

## Basic Info

```yaml
eval_id: eval_001
run_time: 2026-06-16T22:59:37.753905Z
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
overall_status: unsupported
overall_confidence: 0.0
claims_count: 6
sources_count: 2
evidence_count: 0
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
| s1 | OpenAI Platform | platform.openai.com | official_docs | 0.95 | true | not_reviewed | not_provided_in_json |
| s2 | Tokenizer - OpenAI API | platform.openai.com | official_docs | 0.95 | true | not_reviewed | not_provided_in_json |

## Claims

| claim_id | claim_text | claim_type | status | confidence | evidence_count | human_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|
| c1 | GPT-4.1 是否存在公开发布页面 | existence | unsupported | 0.0 | 0 | not_reviewed | not_provided_in_json |
| c2 | GPT-4.1 是否公开模型权重 | model_weights | unsupported | 0.0 | 0 | not_reviewed | not_provided_in_json |
| c3 | GPT-4.1 是否公开训练代码 | source_code | unsupported | 0.0 | 0 | not_reviewed | not_provided_in_json |
| c4 | GPT-4.1 是否公开训练数据 | training_data | unsupported | 0.0 | 0 | not_reviewed | not_provided_in_json |
| c5 | GPT-4.1 的许可证是否允许商用 | license | unsupported | 0.0 | 0 | not_reviewed | not_provided_in_json |
| c6 | GPT-4.1 是否能严格称为开源模型 | interpretation | unsupported | 0.0 | 0 | not_reviewed | not_provided_in_json |

## Evidence

No evidence items were returned in the sanitized JSON.

## Human Conclusion

Run 004 fixes the run_003 source ownership failure for this sample: final sources are now OpenAI official docs on `platform.openai.com`, not third-party Hugging Face pages.

However, `overall_status` remains `unsupported` because no evidence was extracted for any claim. This should not be interpreted as an official-source recall failure. The likely next-layer issue is claim decomposition / evidence semantics: the generic AI-model open-source claim set asks about model weights, training code, training data, license, and strict open-source status, while the user asked whether GPT-4.1 is an OpenAI-released model.

---

# eval_002

## Basic Info

```yaml
eval_id: eval_002
run_time: 2026-06-16T22:59:37.753905Z
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

Run 004 is effectively unchanged from run_003 for this sample. Hugging Face and GitHub remain in final sources as primary source types. This remains a partial improvement over run_002, but the sanitized record still does not provide enough human review to determine whether the Hugging Face namespace and GitHub owner are official Meta/Llama-controlled sources.

---

# eval_003

## Basic Info

```yaml
eval_id: eval_003
run_time: 2026-06-16T22:59:37.753905Z
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
overall_status: confirmed
overall_confidence: 0.9196
claims_count: 1
sources_count: 2
evidence_count: 2
conflicts_count: 0
answer_allowed_tone: confident
must_disclose_uncertainty: false
can_answer_confidently: true
page_fetch_status_counts:
  fallback: 2
```

## Sources

| source_id | title | domain | source_type | base_reliability | is_primary_source | human_source_type_judgment | suspected_issue |
|---|---|---|---|---:|---|---|---|
| s1 | 应对合成语音的挑战与机遇 - OpenAI | openai.com | official_docs | 0.95 | true | not_reviewed | not_provided_in_json |
| s2 | 探索合成語音的挑戰與機遇 - OpenAI | openai.com | official_docs | 0.95 | true | not_reviewed | not_provided_in_json |

## Claims

| claim_id | claim_text | claim_type | status | confidence | evidence_count | human_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|
| c1 | OpenAI 最近是否发布了新的语音模型？ 这一问题可以被外部来源验证 | general_fact | confirmed | 0.9196 | 2 | not_reviewed | not_provided_in_json |

## Evidence

| evidence_id | claim_id | source_id | support_type | relevance_score | final_score | short excerpt | human_support_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|---|
| ev-c1-s1-1 | c1 | s1 | support | 0.88 | 0.9196 | # 应对合成语音的挑战与机遇 \| OpenAI. OpenAI 致力于开发安全可靠、惠及全员的 AI⁠。今天，我们将分享一款名为“Voice Engine”的模型在小规模技术预览中的初步洞察与结果。 | not_reviewed | not_provided_in_json |
| ev-c1-s2-1 | c1 | s2 | support | 0.88 | 0.9196 | # 探索合成語音的挑戰與機遇 \| OpenAI. OpenAI 致力於開發安全且造福廣大社群的 AI⁠。今天，我們分享來自 Voice Engine 模型在小規模預覽中的初步見解和結果 | not_reviewed | not_provided_in_json |

## Human Conclusion

Run 004 shows a clear v0.2.6 improvement. In run_003, `openai.com` was still classified as `unknown`; in run_004, both final sources are `openai.com` with `official_docs`, `base_reliability=0.95`, and `is_primary_source=true`. The claim is now `confirmed`.

---

# eval_004

## Basic Info

```yaml
eval_id: eval_004
run_time: 2026-06-16T22:59:37.753905Z
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
overall_status: mostly_confirmed
overall_confidence: 0.748
claims_count: 1
sources_count: 2
evidence_count: 2
conflicts_count: 0
answer_allowed_tone: confident
must_disclose_uncertainty: false
can_answer_confidently: true
page_fetch_status_counts:
  fallback: 2
```

## Sources

| source_id | title | domain | source_type | base_reliability | is_primary_source | human_source_type_judgment | suspected_issue |
|---|---|---|---|---:|---|---|---|
| s1 | [HELP] RTX 5070 Ti with low GPU usag \| NVIDIA GeForce Forums | nvidia.com | product_page | 0.8 | true | not_reviewed | not_provided_in_json |
| s2 | GPU not detected (RTX 5070 Ti - "No \| NVIDIA GeForce Forums | nvidia.com | product_page | 0.8 | true | not_reviewed | not_provided_in_json |

## Claims

| claim_id | claim_text | claim_type | status | confidence | evidence_count | human_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|
| c1 | RTX 5070 Ti 是否是 16GB 显存？ 这一问题可以被外部来源验证 | general_fact | likely | 0.748 | 2 | not_reviewed | not_provided_in_json |

## Evidence

| evidence_id | claim_id | source_id | support_type | relevance_score | final_score | short excerpt | human_support_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|---|
| ev-c1-s1-1 | c1 | s1 | support | 0.85 | 0.748 | My Specs: CPU: Intel Core i7 14700K GPU: ZOTAC GeForce RTX 5070 Ti AMP ... PC Specifications GPU: MSI GeForce RTX 5070 Ti 16G Ventus 3X OC Drivers | not_reviewed | not_provided_in_json |
| ev-c1-s2-1 | c1 | s2 | support | 0.82 | 0.7216 | My system specs: GPU: MSI GeForce RTX 5070 Ti 16GB CPU: AMD Ryzen 7 7800X3D Motherboard: MSI B840 GAMING PLUS WIFI AM5 DDR5 PSU: GamePower AXG-850 850W | not_reviewed | not_provided_in_json |

## Human Conclusion

Run 004 improves over run_003 by bringing `nvidia.com` into final sources and classifying it as `product_page`. The result is now `mostly_confirmed`.

One caveat remains: both source titles are NVIDIA GeForce Forums pages, not clearly official NVIDIA specification pages. This run still supports that official-domain recall and classification improved, while later work may need to distinguish official product/spec pages from official-domain community/forum pages.

---

# eval_005

## Basic Info

```yaml
eval_id: eval_005
run_time: 2026-06-16T22:59:37.753905Z
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
overall_status: confirmed
overall_confidence: 0.9405
claims_count: 1
sources_count: 2
evidence_count: 2
conflicts_count: 0
answer_allowed_tone: confident
must_disclose_uncertainty: false
can_answer_confidently: true
page_fetch_status_counts:
  fallback: 2
```

## Sources

| source_id | title | domain | source_type | base_reliability | is_primary_source | human_source_type_judgment | suspected_issue |
|---|---|---|---|---:|---|---|---|
| s1 | [PDF] Fast-Tracking Digital Asset ETFs: Who's Next in Line for Approval? | sec.gov | government_docs | 0.95 | true | not_reviewed | not_provided_in_json |
| s2 | Statement on the Approval of Spot Bitcoin Exchange-Traded Products | sec.gov | government_docs | 0.95 | true | not_reviewed | not_provided_in_json |

## Claims

| claim_id | claim_text | claim_type | status | confidence | evidence_count | human_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|
| c1 | 美国 SEC 是否发布过关于比特币现货 ETF 的批准公告？ 这一问题可以被外部来源验证 | general_fact | confirmed | 0.9405 | 2 | not_reviewed | not_provided_in_json |

## Evidence

| evidence_id | claim_id | source_id | support_type | relevance_score | final_score | short excerpt | human_support_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|---|
| ev-c1-s1-1 | c1 | s1 | support | 0.82 | 0.8569 | The filings follow a surge in crypto ETF applications over the past year following the approval of the first BTC exchange-traded products (ETPs) | not_reviewed | not_provided_in_json |
| ev-c1-s2-1 | c1 | s2 | support | 0.9 | 0.9405 | ### [About](https://www.sec.gov/about). * [Careers](https://www.sec.gov/about/careers-securities-exchange-commission). Court of Appeals for the District of Columbia held that th... | not_reviewed | not_provided_in_json |

## Human Conclusion

Run 004 shows the strongest v0.2.6 improvement. Run 003 did not hit `sec.gov`; run 004 returns two `sec.gov` sources, both classified as `government_docs`, with the claim `confirmed`.

This indicates the policy/legal official-source recall and classification fixes are working for the SEC sample.

---

# 3. Overall Human Conclusion

v0.2.6 official-source recall / classification / ranking 三刀有效。

The system has moved from:

```text
official source often missing or misclassified
```

to:

```text
official source reaches final sources, but some claim semantics still need repair
```

Key results:

- eval_001 now reaches OpenAI official docs via `platform.openai.com`, but remains `unsupported` because no evidence was extracted. This is not an official-source failure; it points to claim decomposition / evidence extraction semantics.
- eval_003 reaches `openai.com` official docs and becomes `confirmed`.
- eval_004 reaches `nvidia.com` and becomes `mostly_confirmed`, though official-domain forum vs specification-page distinction remains worth tracking.
- eval_005 reaches `sec.gov` government docs and becomes `confirmed`.

Next diagnostic focus should shift from source recall to claim semantics and evidence extraction quality, especially for AI model questions where the user asks a release/ownership question but the current claim template decomposes into open-source subclaims.
