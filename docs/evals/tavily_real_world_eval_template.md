# Tavily Real-world Eval Template

版本：v0.2.3-b  
文档类型：Tavily 真实样本手动 eval 记录模板  
用途：手动记录每一次 Tavily 真实搜索进入 CSL 主链路后的 evidence package 质量

---

# 1. 文件说明

这是手动 eval 记录模板，用于评估真实 Tavily 搜索结果进入 `/api/v1/trusted-search` 主链路后，CSL 生成的 evidence package 是否可靠。

评估重点包括：

- `source_classifier` 是否正确分类真实来源。
- `page_fetcher` 是抓到正文还是 fallback snippet。
- `evidence_extractor` 是否抽到有效证据。
- `reliability_scorer` 分数是否合理。
- `claim_aggregator` 是否过度确认或过度保守。
- `answer_constraints` 是否正确限制最终回答语气。

安全边界：

- 不应记录 API key。
- 不应记录 Authorization header。
- 不应记录未脱敏 raw provider payload。
- 可记录脱敏后的 `TrustedSearchResponse` 摘要。
- 不应粘贴完整网页正文、敏感 header、长 tracking URL 或用户隐私信息。

---

# 2. 单次 Eval 基本信息模板

```yaml
eval_id:
run_time:
evaluator:
query:
question_type:
strictness:
max_sources:
provider:
endpoint_or_entrypoint:
opt_in_env_used:
tavily_network_enabled:
notes:
```

字段建议：

- `eval_id`：例如 `tavily-ai-model-001`。
- `run_time`：建议使用本地时间加时区，例如 `2026-05-11T20:30:00+08:00`。
- `endpoint_or_entrypoint`：例如 `/api/v1/trusted-search`、`TestClient`、manual script。
- `opt_in_env_used`：记录 `yes/no`，不要记录 API key 值。
- `tavily_network_enabled`：记录 `yes/no`。

---

# 3. 请求配置模板

```yaml
CSL_SEARCH_PROVIDER:
CSL_SEARCH_ALLOW_NETWORK:
CSL_RUN_INTEGRATION_TESTS:
CSL_SEARCH_API_KEY_PRESENT: yes/no
CSL_SEARCH_API_KEY_VALUE: DO NOT RECORD
PYTHONPATH_USED: yes/no
UV_PROJECT_ENVIRONMENT_USED: yes/no
```

记录规则：

- `CSL_SEARCH_API_KEY_PRESENT` 只写 `yes` 或 `no`。
- `CSL_SEARCH_API_KEY_VALUE` 必须固定写 `DO NOT RECORD`。
- 如果使用临时 uv cache / venv，只记录是否使用，不提交 `.uv-venv` 或 `.uv-cache`。

---

# 4. Response Summary 模板

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

建议只记录结构化摘要，不粘贴完整 raw response。若需要保存完整响应，必须先确认不包含 API key、敏感 header、未脱敏 provider debug 信息或隐私内容。

---

# 5. Claim-level 记录表

| claim_id | claim_text | claim_type | status | confidence | evidence_count | human_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|
|  |  |  |  |  |  |  |  |

`human_judgment` 建议写：

```text
reasonable / too_confident / too_conservative / unsupported_but_should_have_evidence / unclear
```

`suspected_issue` 建议写：

```text
search_quality / source_classifier / page_fetcher / evidence_extractor / reliability_scorer / claim_aggregator / answer_constraints / none
```

---

# 6. Source-level 记录表

| source_id | title | url_domain_only | source_type | base_reliability | is_primary_source | published_at | human_source_type_judgment | suspected_issue |
|---|---|---|---|---:|---|---|---|---|
|  |  |  |  |  |  |  |  |  |

URL 记录规则：

- 只建议记录 domain 或脱敏 URL。
- 不建议粘贴长 URL、raw tracking URL、含 token 的 URL 或完整 query string。
- 如需保留路径，先移除 `utm_*`、session id、token、email、user id 等敏感或追踪参数。

`human_source_type_judgment` 建议写：

```text
correct / should_be_official_docs / should_be_official_blog / should_be_official_model_card / should_be_source_code_repo / should_be_academic_paper / should_be_government_docs / should_be_mainstream_media / should_be_community_forum / should_be_seo_content / should_be_unknown
```

---

# 7. Page Fetch Summary 模板

```yaml
fetch_success_count:
snippet_fallback_count:
failed_count:
empty_text_count:
noisy_text_count:
notes:
```

记录建议：

- `fetch_success_count`：抓到可用正文的来源数量。
- `snippet_fallback_count`：使用搜索 snippet fallback 的来源数量。
- `failed_count`：timeout、HTTP error、blocked、parse error 等失败数量。
- `empty_text_count`：返回正文为空或近似为空的数量。
- `noisy_text_count`：抓到导航、广告、页脚、cookie banner 等噪声为主的数量。

---

# 8. Evidence-level 记录表

| evidence_id | claim_id | source_id | support_type | relevance_score | final_score | evidence_text_short_excerpt | human_support_judgment | suspected_issue |
|---|---|---|---|---:|---:|---|---|---|
|  |  |  |  |  |  |  |  |  |

记录规则：

- `evidence_text_short_excerpt` 只放短摘录。
- 不粘贴大段网页正文。
- 不粘贴完整 raw provider payload。
- 如果 evidence 来自 fallback snippet，应在 `suspected_issue` 或 notes 中标明。

`human_support_judgment` 建议写：

```text
correct_support / correct_oppose / correct_partial / should_be_neutral / unrelated / overclaimed / missed_context / unclear
```

---

# 9. Quality Scoring 表

使用 1-5 分制：

```text
1 = 严重不可用
2 = 问题明显
3 = 可用但需人工判断
4 = 基本可靠
5 = 质量较好
```

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

评分建议：

- 分数必须配一句人工理由。
- `overall_trust_score` 不应高于核心瓶颈模块的可信程度太多。
- 如果 evidence 主要来自 snippet fallback，`evidence_quality_score` 和 `overall_trust_score` 应谨慎。

---

# 10. Failure Point Checklist

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

可补充其他失败点：

- [ ] Other:

---

# 11. Human Conclusion 模板

```yaml
What worked well:
What failed:
Most likely root cause:
Recommended next fix:
Should this sample become a regression test? yes/no
Priority: P0/P1/P2
```

优先级建议：

- `P0`：可能导致下游 AI 明显误导、过度确认或泄露敏感信息。
- `P1`：明显影响 evidence package 质量，但有人工复核可发现。
- `P2`：质量改进项、覆盖率问题或文案约束改进。

---

# 12. Example Empty Template

复制以下块用于单次 eval 记录。

````markdown
## Eval Record

### Basic Info

```yaml
eval_id:
run_time:
evaluator:
query:
question_type:
strictness:
max_sources:
provider:
endpoint_or_entrypoint:
opt_in_env_used:
tavily_network_enabled:
notes:
````

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
- [ ] Other:

### Human Conclusion

```yaml
What worked well:
What failed:
Most likely root cause:
Recommended next fix:
Should this sample become a regression test? yes/no
Priority: P0/P1/P2
```
```

---

# 13. 禁止事项

Eval 记录禁止：

- 不要记录 API key。
- 不要记录 Authorization header。
- 不要提交真实 raw provider payload。
- 不要提交敏感信息。
- 不要因为单个样本就大改生产逻辑。
- 不要让默认 pytest 访问真实网络。
- 不要把 Tavily 设为默认 provider。

本阶段禁止：

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
- 不要移动 v0.2.0 / v0.2.1 / v0.2.2 标签。
- 不要补 v0.1.7 tag。
- 不要重写 Git 历史。
