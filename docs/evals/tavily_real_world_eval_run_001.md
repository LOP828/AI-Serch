# Tavily Real-world Eval Run 001

版本：v0.2.3-c  
文档类型：第一轮 Tavily real-world eval 手动记录文件  
状态：待人工运行并填写，不包含真实响应结果

---

# 1. 文件用途

本文件用于记录第一轮 3-5 个 Tavily 真实样本评估结果。当前只准备样本和空记录模板，不自动发起真实网络请求，不读取或写入 API key，不优化算法。

本轮重点观察真实 Tavily 搜索进入 `/api/v1/trusted-search` 主链路后，CSL evidence package 的质量瓶颈：

- Tavily sources 是否相关。
- 官方 / 一手来源是否优先出现。
- `source_type` 是否识别正确。
- `page_fetch` 是成功还是 fallback snippet。
- evidence 是否真正支持 claim。
- `final_score` 是否合理。
- claim status 是否过度 confident / uncertain。
- `answer_constraints` 是否合理。

---

# 2. 本轮建议样本

| eval_id | category | query | question_type | strictness | max_sources |
|---|---|---|---|---|---:|
| eval_001 | AI 模型信息 | GPT-4.1 是否是 OpenAI 发布的模型？ | ai_model_info | balanced | 2 |
| eval_002 | AI 模型信息 | Llama 3.1 是否公开模型权重并允许商用？ | ai_model_info | balanced | 2 |
| eval_003 | 科技新闻 / 发布信息 | OpenAI 最近是否发布了新的语音模型？ | tech_news | balanced | 2 |
| eval_004 | 产品参数 | RTX 5070 Ti 是否是 16GB 显存？ | product_info | balanced | 2 |
| eval_005 | 政策 / 官方信息 | 美国 SEC 是否发布过关于比特币现货 ETF 的批准公告？ | policy_legal | balanced | 2 |

---

# 3. 手动运行方式

真实 eval 必须显式 opt-in。不要把 Tavily 设为默认 provider。

PowerShell 临时设置方式：

```powershell
$secureKey = Read-Host "Enter Tavily API key for this shell only" -AsSecureString
$plainKey = [System.Net.NetworkCredential]::new("", $secureKey).Password
$env:CSL_SEARCH_API_KEY = $plainKey
Remove-Variable plainKey
Remove-Variable secureKey

$env:CSL_RUN_INTEGRATION_TESTS = "true"
$env:CSL_SEARCH_PROVIDER = "tavily"
$env:CSL_SEARCH_ALLOW_NETWORK = "true"
```

建议通过 `/api/v1/trusted-search` 主链路手动运行每个样本，并把脱敏后的 `TrustedSearchResponse` 摘要填入下方记录区。

运行结束后清理环境变量：

```powershell
Remove-Item Env:\CSL_RUN_INTEGRATION_TESTS
Remove-Item Env:\CSL_SEARCH_PROVIDER
Remove-Item Env:\CSL_SEARCH_ALLOW_NETWORK
Remove-Item Env:\CSL_SEARCH_API_KEY
Remove-Item Env:\PYTHONPATH
```

如果某个变量不存在，只清理当前实际设置过的变量即可。

---

# 4. 安全要求

- 不要把 API key 写进该 eval 文件。
- 不要记录 Authorization header。
- 不要记录完整 raw provider payload。
- 不要提交敏感信息。
- 可以记录脱敏后的 `TrustedSearchResponse` 摘要。
- `evidence_text` 只记录短摘录。
- URL 只建议记录 domain 或脱敏 URL，不粘贴长 URL、tracking URL、token 或完整 query string。
- 本轮只记录观察结果，不优化算法。
- 不要因为单个样本就大改生产逻辑。
- 不要让默认 pytest 访问真实网络。
- 不要把 Tavily 设为默认 provider。

---

# 5. Eval Records

## eval_001

### Basic Info

```yaml
eval_id: eval_001
run_time:
evaluator:
query: GPT-4.1 是否是 OpenAI 发布的模型？
question_type: ai_model_info
strictness: balanced
max_sources: 2
provider: tavily
endpoint_or_entrypoint: /api/v1/trusted-search
opt_in_env_used:
tavily_network_enabled:
notes:
```

### Request Config

```yaml
CSL_SEARCH_PROVIDER:
CSL_SEARCH_ALLOW_NETWORK:
CSL_RUN_INTEGRATION_TESTS:
CSL_SEARCH_API_KEY_PRESENT: yes/no
CSL_SEARCH_API_KEY_VALUE: DO NOT RECORD
PYTHONPATH_USED: yes/no
UV_PROJECT_ENVIRONMENT_USED: yes/no
```

### Response Summary

```yaml
overall_status:
overall_confidence:
claims_count:
sources_count:
evidence_count:
conflicts_count:
answer_allowed_tone:
must_disclose_uncertainty:
can_answer_confidently:
```

### Claims

| claim_id | claim_text | claim_type | status | confidence | evidence_count | human_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|
|  |  |  |  |  |  |  |  |

### Sources

| source_id | title | url_domain_only | source_type | base_reliability | is_primary_source | published_at | human_source_type_judgment | suspected_issue |
|---|---|---|---|---:|---|---|---|---|
|  |  |  |  |  |  |  |  |  |

### Page Fetch Summary

```yaml
fetch_success_count:
snippet_fallback_count:
failed_count:
empty_text_count:
noisy_text_count:
notes:
```

### Evidence

| evidence_id | claim_id | source_id | support_type | relevance_score | final_score | evidence_text_short_excerpt | human_support_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|---|
|  |  |  |  |  |  |  |  |  |

### Quality Scoring

| metric | score | reason |
|---|---:|---|
| search_relevance_score |  |  |
| source_quality_score |  |  |
| source_classification_score |  |  |
| fetch_quality_score |  |  |
| evidence_quality_score |  |  |
| scoring_reasonableness_score |  |  |
| aggregation_reasonableness_score |  |  |
| answer_constraint_score |  |  |
| overall_trust_score |  |  |

### Failure Point Checklist

- [ ] Tavily returned irrelevant sources
- [ ] Missing official / primary source
- [ ] Source classified as unknown too often
- [ ] Source type misclassified
- [ ] Page fetch failed too often
- [ ] Snippet fallback too frequent
- [ ] Evidence unrelated to claim
- [ ] Evidence support_type wrong
- [ ] Evidence missed key fact
- [ ] Scoring too high for weak source
- [ ] Scoring too low for strong source
- [ ] Claim aggregator over-confirmed
- [ ] Claim aggregator too conservative
- [ ] Conflict not detected
- [ ] Answer constraints too confident
- [ ] Answer constraints too cautious

### Human Conclusion

```yaml
What worked well:
What failed:
Most likely root cause:
Recommended next fix:
Should this sample become a regression test? yes/no
Priority: P0/P1/P2
```

## eval_002

### Basic Info

```yaml
eval_id: eval_002
run_time:
evaluator:
query: Llama 3.1 是否公开模型权重并允许商用？
question_type: ai_model_info
strictness: balanced
max_sources: 2
provider: tavily
endpoint_or_entrypoint: /api/v1/trusted-search
opt_in_env_used:
tavily_network_enabled:
notes:
```

### Request Config

```yaml
CSL_SEARCH_PROVIDER:
CSL_SEARCH_ALLOW_NETWORK:
CSL_RUN_INTEGRATION_TESTS:
CSL_SEARCH_API_KEY_PRESENT: yes/no
CSL_SEARCH_API_KEY_VALUE: DO NOT RECORD
PYTHONPATH_USED: yes/no
UV_PROJECT_ENVIRONMENT_USED: yes/no
```

### Response Summary

```yaml
overall_status:
overall_confidence:
claims_count:
sources_count:
evidence_count:
conflicts_count:
answer_allowed_tone:
must_disclose_uncertainty:
can_answer_confidently:
```

### Claims

| claim_id | claim_text | claim_type | status | confidence | evidence_count | human_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|
|  |  |  |  |  |  |  |  |

### Sources

| source_id | title | url_domain_only | source_type | base_reliability | is_primary_source | published_at | human_source_type_judgment | suspected_issue |
|---|---|---|---|---:|---|---|---|---|
|  |  |  |  |  |  |  |  |  |

### Page Fetch Summary

```yaml
fetch_success_count:
snippet_fallback_count:
failed_count:
empty_text_count:
noisy_text_count:
notes:
```

### Evidence

| evidence_id | claim_id | source_id | support_type | relevance_score | final_score | evidence_text_short_excerpt | human_support_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|---|
|  |  |  |  |  |  |  |  |  |

### Quality Scoring

| metric | score | reason |
|---|---:|---|
| search_relevance_score |  |  |
| source_quality_score |  |  |
| source_classification_score |  |  |
| fetch_quality_score |  |  |
| evidence_quality_score |  |  |
| scoring_reasonableness_score |  |  |
| aggregation_reasonableness_score |  |  |
| answer_constraint_score |  |  |
| overall_trust_score |  |  |

### Failure Point Checklist

- [ ] Tavily returned irrelevant sources
- [ ] Missing official / primary source
- [ ] Source classified as unknown too often
- [ ] Source type misclassified
- [ ] Page fetch failed too often
- [ ] Snippet fallback too frequent
- [ ] Evidence unrelated to claim
- [ ] Evidence support_type wrong
- [ ] Evidence missed key fact
- [ ] Scoring too high for weak source
- [ ] Scoring too low for strong source
- [ ] Claim aggregator over-confirmed
- [ ] Claim aggregator too conservative
- [ ] Conflict not detected
- [ ] Answer constraints too confident
- [ ] Answer constraints too cautious

### Human Conclusion

```yaml
What worked well:
What failed:
Most likely root cause:
Recommended next fix:
Should this sample become a regression test? yes/no
Priority: P0/P1/P2
```

## eval_003

### Basic Info

```yaml
eval_id: eval_003
run_time:
evaluator:
query: OpenAI 最近是否发布了新的语音模型？
question_type: tech_news
strictness: balanced
max_sources: 2
provider: tavily
endpoint_or_entrypoint: /api/v1/trusted-search
opt_in_env_used:
tavily_network_enabled:
notes:
```

### Request Config

```yaml
CSL_SEARCH_PROVIDER:
CSL_SEARCH_ALLOW_NETWORK:
CSL_RUN_INTEGRATION_TESTS:
CSL_SEARCH_API_KEY_PRESENT: yes/no
CSL_SEARCH_API_KEY_VALUE: DO NOT RECORD
PYTHONPATH_USED: yes/no
UV_PROJECT_ENVIRONMENT_USED: yes/no
```

### Response Summary

```yaml
overall_status:
overall_confidence:
claims_count:
sources_count:
evidence_count:
conflicts_count:
answer_allowed_tone:
must_disclose_uncertainty:
can_answer_confidently:
```

### Claims

| claim_id | claim_text | claim_type | status | confidence | evidence_count | human_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|
|  |  |  |  |  |  |  |  |

### Sources

| source_id | title | url_domain_only | source_type | base_reliability | is_primary_source | published_at | human_source_type_judgment | suspected_issue |
|---|---|---|---|---:|---|---|---|---|
|  |  |  |  |  |  |  |  |  |

### Page Fetch Summary

```yaml
fetch_success_count:
snippet_fallback_count:
failed_count:
empty_text_count:
noisy_text_count:
notes:
```

### Evidence

| evidence_id | claim_id | source_id | support_type | relevance_score | final_score | evidence_text_short_excerpt | human_support_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|---|
|  |  |  |  |  |  |  |  |  |

### Quality Scoring

| metric | score | reason |
|---|---:|---|
| search_relevance_score |  |  |
| source_quality_score |  |  |
| source_classification_score |  |  |
| fetch_quality_score |  |  |
| evidence_quality_score |  |  |
| scoring_reasonableness_score |  |  |
| aggregation_reasonableness_score |  |  |
| answer_constraint_score |  |  |
| overall_trust_score |  |  |

### Failure Point Checklist

- [ ] Tavily returned irrelevant sources
- [ ] Missing official / primary source
- [ ] Source classified as unknown too often
- [ ] Source type misclassified
- [ ] Page fetch failed too often
- [ ] Snippet fallback too frequent
- [ ] Evidence unrelated to claim
- [ ] Evidence support_type wrong
- [ ] Evidence missed key fact
- [ ] Scoring too high for weak source
- [ ] Scoring too low for strong source
- [ ] Claim aggregator over-confirmed
- [ ] Claim aggregator too conservative
- [ ] Conflict not detected
- [ ] Answer constraints too confident
- [ ] Answer constraints too cautious

### Human Conclusion

```yaml
What worked well:
What failed:
Most likely root cause:
Recommended next fix:
Should this sample become a regression test? yes/no
Priority: P0/P1/P2
```

## eval_004

### Basic Info

```yaml
eval_id: eval_004
run_time:
evaluator:
query: RTX 5070 Ti 是否是 16GB 显存？
question_type: product_info
strictness: balanced
max_sources: 2
provider: tavily
endpoint_or_entrypoint: /api/v1/trusted-search
opt_in_env_used:
tavily_network_enabled:
notes:
```

### Request Config

```yaml
CSL_SEARCH_PROVIDER:
CSL_SEARCH_ALLOW_NETWORK:
CSL_RUN_INTEGRATION_TESTS:
CSL_SEARCH_API_KEY_PRESENT: yes/no
CSL_SEARCH_API_KEY_VALUE: DO NOT RECORD
PYTHONPATH_USED: yes/no
UV_PROJECT_ENVIRONMENT_USED: yes/no
```

### Response Summary

```yaml
overall_status:
overall_confidence:
claims_count:
sources_count:
evidence_count:
conflicts_count:
answer_allowed_tone:
must_disclose_uncertainty:
can_answer_confidently:
```

### Claims

| claim_id | claim_text | claim_type | status | confidence | evidence_count | human_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|
|  |  |  |  |  |  |  |  |

### Sources

| source_id | title | url_domain_only | source_type | base_reliability | is_primary_source | published_at | human_source_type_judgment | suspected_issue |
|---|---|---|---|---:|---|---|---|---|
|  |  |  |  |  |  |  |  |  |

### Page Fetch Summary

```yaml
fetch_success_count:
snippet_fallback_count:
failed_count:
empty_text_count:
noisy_text_count:
notes:
```

### Evidence

| evidence_id | claim_id | source_id | support_type | relevance_score | final_score | evidence_text_short_excerpt | human_support_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|---|
|  |  |  |  |  |  |  |  |  |

### Quality Scoring

| metric | score | reason |
|---|---:|---|
| search_relevance_score |  |  |
| source_quality_score |  |  |
| source_classification_score |  |  |
| fetch_quality_score |  |  |
| evidence_quality_score |  |  |
| scoring_reasonableness_score |  |  |
| aggregation_reasonableness_score |  |  |
| answer_constraint_score |  |  |
| overall_trust_score |  |  |

### Failure Point Checklist

- [ ] Tavily returned irrelevant sources
- [ ] Missing official / primary source
- [ ] Source classified as unknown too often
- [ ] Source type misclassified
- [ ] Page fetch failed too often
- [ ] Snippet fallback too frequent
- [ ] Evidence unrelated to claim
- [ ] Evidence support_type wrong
- [ ] Evidence missed key fact
- [ ] Scoring too high for weak source
- [ ] Scoring too low for strong source
- [ ] Claim aggregator over-confirmed
- [ ] Claim aggregator too conservative
- [ ] Conflict not detected
- [ ] Answer constraints too confident
- [ ] Answer constraints too cautious

### Human Conclusion

```yaml
What worked well:
What failed:
Most likely root cause:
Recommended next fix:
Should this sample become a regression test? yes/no
Priority: P0/P1/P2
```

## eval_005

### Basic Info

```yaml
eval_id: eval_005
run_time:
evaluator:
query: 美国 SEC 是否发布过关于比特币现货 ETF 的批准公告？
question_type: policy_legal
strictness: balanced
max_sources: 2
provider: tavily
endpoint_or_entrypoint: /api/v1/trusted-search
opt_in_env_used:
tavily_network_enabled:
notes:
```

### Request Config

```yaml
CSL_SEARCH_PROVIDER:
CSL_SEARCH_ALLOW_NETWORK:
CSL_RUN_INTEGRATION_TESTS:
CSL_SEARCH_API_KEY_PRESENT: yes/no
CSL_SEARCH_API_KEY_VALUE: DO NOT RECORD
PYTHONPATH_USED: yes/no
UV_PROJECT_ENVIRONMENT_USED: yes/no
```

### Response Summary

```yaml
overall_status:
overall_confidence:
claims_count:
sources_count:
evidence_count:
conflicts_count:
answer_allowed_tone:
must_disclose_uncertainty:
can_answer_confidently:
```

### Claims

| claim_id | claim_text | claim_type | status | confidence | evidence_count | human_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|
|  |  |  |  |  |  |  |  |

### Sources

| source_id | title | url_domain_only | source_type | base_reliability | is_primary_source | published_at | human_source_type_judgment | suspected_issue |
|---|---|---|---|---:|---|---|---|---|
|  |  |  |  |  |  |  |  |  |

### Page Fetch Summary

```yaml
fetch_success_count:
snippet_fallback_count:
failed_count:
empty_text_count:
noisy_text_count:
notes:
```

### Evidence

| evidence_id | claim_id | source_id | support_type | relevance_score | final_score | evidence_text_short_excerpt | human_support_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|---|
|  |  |  |  |  |  |  |  |  |

### Quality Scoring

| metric | score | reason |
|---|---:|---|
| search_relevance_score |  |  |
| source_quality_score |  |  |
| source_classification_score |  |  |
| fetch_quality_score |  |  |
| evidence_quality_score |  |  |
| scoring_reasonableness_score |  |  |
| aggregation_reasonableness_score |  |  |
| answer_constraint_score |  |  |
| overall_trust_score |  |  |

### Failure Point Checklist

- [ ] Tavily returned irrelevant sources
- [ ] Missing official / primary source
- [ ] Source classified as unknown too often
- [ ] Source type misclassified
- [ ] Page fetch failed too often
- [ ] Snippet fallback too frequent
- [ ] Evidence unrelated to claim
- [ ] Evidence support_type wrong
- [ ] Evidence missed key fact
- [ ] Scoring too high for weak source
- [ ] Scoring too low for strong source
- [ ] Claim aggregator over-confirmed
- [ ] Claim aggregator too conservative
- [ ] Conflict not detected
- [ ] Answer constraints too confident
- [ ] Answer constraints too cautious

### Human Conclusion

```yaml
What worked well:
What failed:
Most likely root cause:
Recommended next fix:
Should this sample become a regression test? yes/no
Priority: P0/P1/P2
```

---

# 6. 本轮人工结论汇总区

```yaml
Top 3 recurring issues:
  - 
  - 
  - 
Most urgent fix candidate:
Should we tune source_classifier? yes/no/unclear
Should we tune page_fetcher? yes/no/unclear
Should we tune evidence_extractor? yes/no/unclear
Should we tune scoring? yes/no/unclear
Overall notes:
```

---

# 7. 本轮禁止事项

- 不要改生产代码。
- 不要改测试代码。
- 不要发起真实网络请求。
- 不要读取、申请、写入 API key。
- 不要新增依赖。
- 不要修改 `pyproject.toml`。
- 不要修改 `env.example`。
- 不要修改 README。
- 不要修改 MCP。
- 不要修改 `TrustedSearchService`。
- 不要修改 `SearchAdapter`。
- 不要修改 `SearchResultSchema` / `SourceSchema`。
- 不要移动任何 tag。
- 不要补 v0.1.7 tag。
- 不要重写 Git 历史。
- 不要根据样本假设直接改算法。
