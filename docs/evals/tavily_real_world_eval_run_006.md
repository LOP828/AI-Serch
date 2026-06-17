# Tavily Real-world Eval Run 006

版本：v0.2.8-sanitized-eval  
文档类型：Tavily real-world eval 脱敏记录  
数据来源：`tavily_eval_run_006_sanitized.json`

---

# 1. 记录边界

本文件只根据脱敏 JSON 摘要整理，不包含 API key、Authorization header、raw provider payload 或完整网页正文。`evidence` 仅保留 JSON 中已有的短摘录。

全局运行信息：

```yaml
run_time: 2026-06-17T00:08:27.830100Z
provider: tavily
endpoint_or_entrypoint: /api/v1/trusted-search
opt_in_env_used: yes
tavily_network_enabled: yes
api_key_present: yes
```

---

# 2. Run 005 对比摘要

v0.2.8 的 product memory spec evidence matching 对 eval_004 有明显效果：

| eval_id | run_005 status | run_006 status | run_006 observation |
|---|---|---|---|
| eval_001 | confirmed | confirmed | GPT-4.1 release/origin 行为保持 |
| eval_002 | partially_confirmed | partially_confirmed | Open-source / weights / commercial-use 行为保持 |
| eval_003 | confirmed | confirmed | OpenAI official docs result 保持 |
| eval_004 | `conflicting`, conflicts_count=1 | `mostly_confirmed`, conflicts_count=0 | RTX 5070 Ti 16G / 16GB 均被判为 support，不再误触发 conflict |
| eval_005 | confirmed | confirmed | SEC sample 仍 confirmed |

Human interpretation:

- v0.2.8 第一刀有效：`16G` 与 `16GB` 在显存语境下被正确视为等价。
- eval_004 的 evidence support/oppose 方向问题已修复。
- eval_004 仍为 `mostly_confirmed` 而非 `confirmed`，可能因为证据来自 NVIDIA forum snippet，而非稳定官方规格页。
- 下一步不应调 scorer / aggregator；后续可考虑 product official spec page recall 或 source subtype refinement，但本轮先只记录。

---

# eval_001

## Basic Info

```yaml
eval_id: eval_001
run_time: 2026-06-17T00:08:27.830100Z
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
overall_status: confirmed
overall_confidence: 0.9405
claims_count: 3
sources_count: 2
evidence_count: 6
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
| s1 | Introducing GPT-4.1 in the API - OpenAI | openai.com | official_docs | 0.95 | true | not_reviewed | not_provided_in_json |
| s2 | OpenAI Platform | platform.openai.com | official_docs | 0.95 | true | not_reviewed | not_provided_in_json |

## Claims

| claim_id | claim_text | claim_type | status | confidence | evidence_count | human_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|
| c1 | GPT-4.1 是否存在 OpenAI 官方发布或文档页面 | official_release_page | confirmed | 0.9405 | 2 | not_reviewed | not_provided_in_json |
| c2 | GPT-4.1 是否由 OpenAI 提供或发布 | model_provider | confirmed | 0.9405 | 2 | not_reviewed | not_provided_in_json |
| c3 | GPT-4.1 是否可通过 OpenAI API / platform 使用 | model_access | confirmed | 0.9405 | 2 | not_reviewed | not_provided_in_json |

## Evidence

| evidence_id | claim_id | source_id | support_type | relevance_score | final_score | short excerpt | human_support_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|---|
| ev-c1-s1-1 | c1 | s1 | support | 0.9 | 0.9405 | * **Coding**: GPT‑4.1 scores 54.6% on [SWE-bench Verified](https://openai.com/index/introducing-swe-bench-verified/), improving by 21.4%abs over GPT‑4o and 26.6%abs over GPT‑4.5... | not_reviewed | not_provided_in_json |
| ev-c1-s2-1 | c1 | s2 | support | 0.9 | 0.9405 | # OpenAI Platform. # Build on the OpenAI API Platform. Sign up or login with an OpenAI account to build with the OpenAI API. | not_reviewed | not_provided_in_json |
| ev-c2-s1-1 | c2 | s1 | support | 0.9 | 0.9405 | * **Coding**: GPT‑4.1 scores 54.6% on [SWE-bench Verified](https://openai.com/index/introducing-swe-bench-verified/), improving by 21.4%abs over GPT‑4o and 26.6%abs over GPT‑4.5... | not_reviewed | not_provided_in_json |
| ev-c2-s2-1 | c2 | s2 | support | 0.9 | 0.9405 | # OpenAI Platform. # Build on the OpenAI API Platform. Sign up or login with an OpenAI account to build with the OpenAI API. | not_reviewed | not_provided_in_json |
| ev-c3-s1-1 | c3 | s1 | support | 0.9 | 0.9405 | * **Coding**: GPT‑4.1 scores 54.6% on [SWE-bench Verified](https://openai.com/index/introducing-swe-bench-verified/), improving by 21.4%abs over GPT‑4o and 26.6%abs over GPT‑4.5... | not_reviewed | not_provided_in_json |
| ev-c3-s2-1 | c3 | s2 | support | 0.9 | 0.9405 | # OpenAI Platform. # Build on the OpenAI API Platform. Sign up or login with an OpenAI account to build with the OpenAI API. | not_reviewed | not_provided_in_json |

## Human Conclusion

Run 006 keeps eval_001 confirmed. v0.2.7 AI model release/origin claim decomposition behavior remains stable.

---

# eval_002

## Basic Info

```yaml
eval_id: eval_002
run_time: 2026-06-17T00:08:27.830100Z
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

Run 006 keeps eval_002 partially_confirmed. Open-source / weights / commercial-use decomposition remains unchanged.

---

# eval_003

## Basic Info

```yaml
eval_id: eval_003
run_time: 2026-06-17T00:08:27.830100Z
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
| ev-c1-s1-1 | c1 | s1 | support | 0.88 | 0.9196 | # 应对合成语音的挑战与机遇 \| OpenAI. OpenAI 致力于开发安全可靠、惠及全员的 AI⁠。今天，我们将分享一款名为“Voice Engine”的模型在小规模技术预览中的初步洞察与结果。该模型只需借助文本输入和一段时长 15 秒的音频样本，即可生成自然流畅且与原始发言者声音高度相似的语音。值得注意的是，小模型仅凭时长 15 秒的样本，就能生... | not_reviewed | not_provided_in_json |
| ev-c1-s2-1 | c1 | s2 | support | 0.88 | 0.9196 | # 探索合成語音的挑戰與機遇 \| OpenAI. OpenAI 致力於開發安全且造福廣大社群的 AI⁠。今天，我們分享來自 Voice Engine 模型在小規模預覽中的初步見解和結果，該模型使用文字輸入和單一 15 秒語音樣本，生成語氣自然流暢、且與原講者高度相似的語音。值得注意的是，小型模型只需一段 15 秒樣本，即可創造出富有情感且逼真的語音。.... | not_reviewed | not_provided_in_json |

## Human Conclusion

Run 006 keeps eval_003 confirmed with OpenAI official docs. No source recall or classification regression is visible in the sanitized record.

---

# eval_004

## Basic Info

```yaml
eval_id: eval_004
run_time: 2026-06-17T00:08:27.830100Z
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
overall_confidence: 0.7216
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
| s1 | Topic: [HELP] RTX 5070 Ti with low on NVIDIA #GeForce Forums | nvidia.com | product_page | 0.8 | true | not_reviewed | not_provided_in_json |
| s2 | GPU not detected (RTX 5070 Ti - "No \| NVIDIA GeForce Forums | nvidia.com | product_page | 0.8 | true | not_reviewed | not_provided_in_json |

## Claims

| claim_id | claim_text | claim_type | status | confidence | evidence_count | human_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|
| c1 | RTX 5070 Ti 是否是 16GB 显存？ 这一问题可以被外部来源验证 | general_fact | likely | 0.7216 | 2 | not_reviewed | not_provided_in_json |

## Evidence

| evidence_id | claim_id | source_id | support_type | relevance_score | final_score | short excerpt | human_support_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|---|
| ev-c1-s1-1 | c1 | s1 | support | 0.82 | 0.7216 | PC Specifications GPU: MSI GeForce RTX 5070 Ti 16G Ventus 3X OC Drivers tested: 581.08 (Game Ready) and 576.28 WHQL (clean install with DDU) NVIDIA Control Panel: Prefer maximum... | not_reviewed | not_provided_in_json |
| ev-c1-s2-1 | c1 | s2 | support | 0.82 | 0.7216 | My system specs: GPU: MSI GeForce RTX 5070 Ti 16GB CPU: AMD Ryzen 7 7800X3D Motherboard: MSI B840 GAMING PLUS WIFI AM5 DDR5 PSU: GamePower AXG-850 850W | not_reviewed | not_provided_in_json |

## Conflicts

No conflicts were recorded in the sanitized run.

## Human Conclusion

Run 006 verifies v0.2.8 first cut for product memory spec evidence matching.

Compared with run_005:

```text
run_005: overall_status=conflicting / conflicts_count=1
run_006: overall_status=mostly_confirmed / conflicts_count=0
```

The key evidence direction changed as intended:

- `RTX 5070 Ti 16G` excerpt is now `support`.
- `RTX 5070 Ti 16GB` excerpt remains `support`.

This confirms that `16G` and `16GB` are treated as equivalent in the VRAM / memory-size context, and the previous false `oppose` no longer triggers conflict.

The result is still `mostly_confirmed`, not `confirmed`. The likely reason from the sanitized record is evidence quality: both sources are NVIDIA forum snippets with `fallback` fetch status, not stable official specification pages. This should not be treated as a scorer / aggregator problem.

This run should only record that product evidence direction is fixed. Later work may consider product official spec page recall or source subtype refinement, but no change is recommended in this run document.

---

# eval_005

## Basic Info

```yaml
eval_id: eval_005
run_time: 2026-06-17T00:08:27.830100Z
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
| s1 | FWP | sec.gov | government_docs | 0.95 | true | not_reviewed | not_provided_in_json |
| s2 | Comments of Henry Dobry on Dec. 6, 2023 | sec.gov | government_docs | 0.95 | true | not_reviewed | not_provided_in_json |

## Claims

| claim_id | claim_text | claim_type | status | confidence | evidence_count | human_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|
| c1 | 美国 SEC 是否发布过关于比特币现货 ETF 的批准公告？ 这一问题可以被外部来源验证 | general_fact | confirmed | 0.9405 | 2 | not_reviewed | not_provided_in_json |

## Evidence

| evidence_id | claim_id | source_id | support_type | relevance_score | final_score | short excerpt | human_support_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|---|
| ev-c1-s1-1 | c1 | s1 | support | 0.9 | 0.9405 | Grayscale Investments® Receives SEC Approval to Uplist Grayscale Bitcoin Trust to NYSE Arca as Spot Bitcoin ETF. Securities and Exchange Commission (SEC) has approved NYSE Arca’... | not_reviewed | not_provided_in_json |
| ev-c1-s2-1 | c1 | s2 | support | 0.9 | 0.9405 | I am a long-time investor and long-term stakeholder in the digital asset community and feel both qualified and grateful for this opportunity to voice my opinion, comments, and c... | not_reviewed | not_provided_in_json |

## Human Conclusion

Run 006 keeps eval_005 confirmed with `sec.gov` government docs. No source recall or official classification regression is visible in the sanitized record.

---

# 3. Overall Human Conclusion

v0.2.8 product memory spec evidence matching is effective for eval_004.

The key change from run_005 to run_006 is:

```text
run_005 eval_004: conflicting / conflicts_count=1
run_006 eval_004: mostly_confirmed / conflicts_count=0
```

Both eval_004 evidence items are now `support`:

- `RTX 5070 Ti 16G` is support.
- `RTX 5070 Ti 16GB` is support.

This confirms that `16G` and `16GB` are now treated as equivalent in the product VRAM context and no longer create a false oppose/conflict.

The remaining reason eval_004 is `mostly_confirmed` rather than `confirmed` appears to be evidence-source quality in the sanitized record: both final sources are NVIDIA forum snippets with fallback fetch status, not stable official specification pages.

Do not tune scorer or relax aggregator based on this run. Do not continue source ranking work in this run document. Future work may consider product official spec page recall or source subtype refinement, but run_006 should be recorded primarily as evidence-direction validation for v0.2.8.
