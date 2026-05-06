# AGENTS.md

## Project: Critical Search Layer

Critical Search Layer is a trusted-search middleware for AI agents. It sits between an AI agent and external search results. Its job is not to generate a final natural-language answer directly, but to produce a structured evidence package that helps an AI answer with appropriate caution.

Chinese name: AI 批判性搜索层

Target form: REST API first, later MCP tool.

Core idea:

> Search results are not answers. They are raw material. The system must classify the question, decompose it into verifiable claims, search for sources, extract evidence, score reliability, expose conflicts, and generate answer constraints.

---

## Canonical project documents

Before making changes, read these documents if they exist in the repository:

1. `critical_search_layer_prd_v_0_1.md`
2. `critical_search_layer_development_sequence_v_0_1.md`
3. `critical_search_layer_detailed_development_tasks.md`
4. `critical_search_layer_constraints.md`
5. This `AGENTS.md`

When documents and code disagree, do not silently choose one. Report the mismatch and make the smallest safe change needed for the current task.

---

## Product boundary

This project is a trustworthy search layer, not:

- a general search engine
- a chatbot
- a browser plugin
- a frontend app
- a database-heavy knowledge system
- a high-risk medical, legal, or financial decision engine
- a model training project

MVP v0.1 must stay focused on the smallest useful closed loop:

```text
query
  -> question_type
  -> claims
  -> search_plan
  -> search_results
  -> source_type
  -> fetched_text_or_snippet
  -> evidence
  -> reliability_score
  -> claim_status
  -> answer_constraints
  -> evidence_package_json
```

---

## Development strategy

Think like machining a mechanical part:

1. First create the reference surface: project skeleton, schemas, tests.
2. Then rough-machine the shape: classifier, claim decomposer, search planner, search adapter.
3. Then semi-finish: source classifier, page fetcher, evidence extractor, reliability scorer.
4. Then finish: claim aggregator, answer constraints, conflict detection.
5. Then assemble: end-to-end trusted-search service and MCP wrapper.

Do not build the whole factory before the first part can be inspected.

---

## Current priority

Unless the user explicitly says otherwise, follow the staged order below.

### Stage 0: project skeleton

Goal: project can start and tests can run.

Implement only:

- FastAPI app entry
- config module
- logging module
- basic exception handling
- `/health`
- pytest setup
- README run instructions

Do not implement business logic.

Suggested tag:

```text
v0.1.0-skeleton
```

### Stage 1: API schema and mock trusted-search

Goal: freeze the API boundary.

Implement only:

- `TrustedSearchRequest`
- `TrustedSearchResponse`
- `ClaimSchema`
- `SourceSchema`
- `EvidenceSchema`
- `AnswerConstraintsSchema`
- `ErrorResponse`
- `POST /api/v1/trusted-search`
- mock evidence package response
- API tests

Do not call search APIs, LLMs, databases, or MCP.

Suggested tag:

```text
v0.1.1-api-schema
```

### Stage 2: question classifier and claim decomposer

Goal: understand the query and split it into verifiable claims.

Implement:

- rule-based `question_classifier.py`
- template-based `claim_decomposer.py`
- first-class support for `ai_model_info`
- tests for classification and claim decomposition

For the sample query:

```text
MiroThinker 1.7 是不是开源模型？
```

Expected claims should cover:

- public release page exists
- model weights are public
- training code is public
- training data is public
- license allows commercial use
- whether it can strictly be called open source

Suggested tag:

```text
v0.1.2-question-claims
```

### Stage 3: search planner and search adapter

Goal: turn claims into search queries and obtain candidate sources.

Implement:

- `search_planner.py`
- one search API adapter only
- URL deduplication
- controlled failure behavior
- mock-based tests

Do not add multiple search providers in the first version.

Suggested tag:

```text
v0.1.3-search-adapter
```

### Stage 4: source classifier

Goal: classify source types and assign base reliability.

Implement:

- `source_policy.yml`
- `source_classifier.py`
- domain-based rules
- `base_reliability`
- `is_primary_source`
- tests

Key domain rules:

```text
huggingface.co    -> official_model_card
modelscope.cn     -> official_model_card
github.com        -> source_code_repo
gitlab.com        -> source_code_repo
arxiv.org         -> academic_paper
openreview.net    -> academic_paper
sec.gov           -> financial_filing
*.gov             -> government_docs
reddit.com        -> community_forum
zhihu.com         -> community_forum
x.com             -> community_forum
unknown           -> unknown
```

Suggested tag:

```text
v0.1.4-source-classifier
```

### Stage 5: page fetcher

Goal: fetch readable text from candidate URLs.

Implement:

- `page_fetcher.py`
- `httpx` fetching
- timeout
- basic user-agent
- `trafilatura` extraction
- fallback to search snippet
- max text length
- `fetch_status`
- tests with mocked HTTP

Do not implement browser rendering, login handling, PDF parsing, or special Hugging Face/GitHub adapters yet.

Suggested tag:

```text
v0.1.5-page-fetcher
```

### Stage 6: evidence extractor

Goal: extract short evidence snippets tied to specific claims.

Implement:

- `evidence_extractor.py`
- LLM-backed extractor interface if configured
- simple keyword fallback
- strict output validation
- no fabricated evidence
- tests for support, oppose, partial, neutral, and empty evidence

Hard rules:

- Evidence must be tied to one `claim_id`.
- Evidence text must come from source text.
- Evidence should be short, normally 1-3 sentences.
- If there is no evidence, return an empty list.
- `support_type` must be one of: `support`, `oppose`, `partial`, `neutral`.

Suggested tag:

```text
v0.1.6-evidence-extractor
```

### Stage 7: reliability scorer

Goal: compute an explainable score for each evidence item.

First formula:

```text
final_score = relevance_score × source_base_score × primary_source_factor × recency_factor
```

Implement:

- `reliability_scorer.py`
- `score_breakdown`
- tests for different source types and relevance scores

Do not implement cross-check, conflict penalty, or interest-conflict penalty in the first scoring version.

Suggested tag:

```text
v0.1.7-reliability-scorer
```

### Stage 8: claim aggregator

Goal: aggregate evidence into claim status.

Statuses:

```text
confirmed
likely
uncertain
unsupported
conflicting
false_likely
```

First rules:

```text
confirmed:
  top support score >= 0.80 and no strong oppose evidence

likely:
  top support score >= 0.65 but not enough for confirmed

uncertain:
  weak or partial evidence exists

unsupported:
  no useful support or partial evidence exists

false_likely:
  strong oppose evidence and weak support

conflicting:
  strong support and strong oppose evidence both exist
```

Suggested tag:

```text
v0.1.8-claim-aggregator
```

### Stage 9: answer constraint builder

Goal: convert claim status into rules for downstream AI answers.

Implement:

- `can_answer_confidently`
- `must_disclose_uncertainty`
- `must_cite_sources`
- `allowed_tone`
- `required_phrases`
- `forbidden_phrases`

Rules:

- `uncertain` requires uncertainty disclosure.
- `unsupported` forbids confident claims.
- `conflicting` requires conflict disclosure.
- Only strongly confirmed claims allow confident language.

Suggested tag:

```text
v0.1.9-answer-constraints
```

### Stage 10: end-to-end integration

Goal: complete the first usable trusted-search loop.

Implement:

- `TrustedSearchService`
- end-to-end orchestration
- API route calls service
- mock-based E2E tests
- controlled behavior for search/fetch/extraction failure

Suggested tag:

```text
v0.1.10-e2e-mvp
```

### Stage 11: conflict detector

Goal: expose high-quality evidence conflicts.

Implement:

- `conflict_detector.py`
- conflict severity
- conflict summary
- claim status update to `conflicting`
- answer constraints update
- tests

Do not resolve conflicts by force. Expose them.

Suggested tag:

```text
v0.1.11-conflict-detector
```

### Stage 12: MCP tool wrapper

Goal: let agents call `trusted_search` through MCP.

Implement:

- MCP tool schema
- wrapper around existing `TrustedSearchService`
- same input and output shape as REST API
- examples in README

Do not duplicate business logic.

Suggested tag:

```text
v0.1.12-mcp-tool
```

---

## Expected project structure

Prefer this structure unless there is a strong reason to change it:

```text
app/
  main.py
  api/
    routes/
      health.py
      trusted_search.py
  core/
    config.py
    logging.py
    exceptions.py
  services/
    question_classifier.py
    claim_decomposer.py
    search_planner.py
    search_adapter.py
    page_fetcher.py
    source_classifier.py
    evidence_extractor.py
    reliability_scorer.py
    claim_aggregator.py
    conflict_detector.py
    answer_constraint_builder.py
    trusted_search_service.py
  schemas/
    trusted_search.py
    claim.py
    source.py
    evidence.py
    constraints.py
  policies/
    source_policy.yml
    question_policy.yml
  tests/
    api/
    services/
```

---

## Coding rules

1. Keep each module small and replaceable.
2. Prefer explicit Pydantic schemas over loose dictionaries at boundaries.
3. Avoid global mutable state.
4. External calls must have timeouts.
5. External failures must not crash the whole trusted-search flow.
6. Return controlled errors or degraded evidence packages.
7. Do not hide uncertainty.
8. Do not fabricate evidence.
9. Do not convert low-quality sources into high-confidence claims.
10. Keep the first implementation simple and testable.

---

## API rules

Primary endpoint:

```http
POST /api/v1/trusted-search
```

Expected request shape:

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

Expected response must include at least:

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

Each claim must include:

```text
claim_id
claim_text
claim_type
status
confidence
reason
evidence
```

Each source must include:

```text
source_id
title
url
source_type
base_reliability
is_primary_source
```

Each evidence item must include:

```text
source_id
support_type
evidence_text
relevance_score
final_score
score_breakdown
```

---

## Testing rules

Every stage must include tests before it is considered done.

Required test categories:

- API tests for routes
- unit tests for services
- failure-path tests
- mock external API tests
- end-to-end test after Stage 10

External systems must be mocked in tests:

- search API
- LLM
- webpage fetching
- MCP runtime

Do not let tests depend on live internet access.

Preferred commands:

```bash
pytest
```

If the project uses `uv`, prefer:

```bash
uv run pytest
```

---

## Dependency rules

Use minimal dependencies.

Recommended initial stack:

```text
FastAPI
Pydantic / pydantic-settings
httpx
PyYAML
pytest
pytest-asyncio if needed
trafilatura when implementing page fetching
```

Do not add PostgreSQL, Redis, Celery, frontend frameworks, browser automation, or multiple search providers during the first closed loop unless explicitly requested.

---

## Search adapter rules

The first search adapter should support only one provider.

The adapter must return this normalized shape:

```text
title
url
snippet
published_at
```

It must:

- support `max_results`
- deduplicate by normalized URL
- handle timeout and provider failure
- return a controlled error or empty result list instead of raising uncaught exceptions

---

## LLM usage rules

LLM usage is allowed mainly for evidence extraction and later flexible claim decomposition.

Hard limits:

- The LLM must not invent evidence.
- The LLM must be instructed to quote or extract only from provided source text.
- If no evidence exists, it must return an empty list.
- Validate LLM output with Pydantic before using it.
- Add a deterministic fallback where possible.

---

## Evidence rules

Evidence is the core product unit.

Never treat a source as evidence by itself. A source becomes useful only after it supports or opposes a specific claim.

Evidence must answer:

```text
Which claim does this support or oppose?
What exactly does the source say?
How relevant is it?
How reliable is the source?
How confident should the downstream AI be?
```

Do not produce evidence from vague impressions or page titles alone unless using the snippet fallback, and mark the fetch status clearly.

---

## Scoring rules

Scoring is explainability, not truth.

Every `final_score` must have a `score_breakdown`.

First version factors:

```text
relevance_score
source_base_score
primary_source_factor
recency_factor
```

Later factors may include:

```text
cross_check_factor
conflict_penalty
interest_conflict_penalty
```

Do not implement later factors until the basic scoring loop is stable.

---

## Answer constraint rules

The system should not directly produce a final confident answer unless the evidence supports it.

Generate constraints that downstream AI must follow.

Examples of forbidden phrases when evidence is weak:

```text
毫无疑问
已经确定
官方确认
完全开源
一定会发布
```

Examples of required phrases when evidence is weak:

```text
目前只能确认
证据不足
尚未看到官方来源
存在来源冲突
需要区分权重开放、代码开放、训练数据开放和许可证限制
```

---

## Git discipline

After each stage:

```bash
git status
pytest
# or: uv run pytest
git add .
git commit -m "..."
git tag <stage-tag>
```

Use small commits. Do not mix unrelated stages.

Suggested tags:

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

## What not to do early

Do not do these before the first end-to-end MVP works:

- frontend UI
- user accounts
- database persistence
- Redis cache
- browser extension
- multiple search engines
- advanced source reputation history
- evidence graph
- MCP wrapper
- medical/legal/financial high-risk automation
- full natural-language answer generation

---

## First command to follow

When starting from scratch, implement only this:

```text
Create the FastAPI skeleton for Critical Search Layer. Add /health, /api/v1/trusted-search mock endpoint, Pydantic schemas, and basic pytest tests. Do not connect a search API, do not use an LLM, do not add a database, and do not implement MCP. The project must start, tests must pass, and the mock response must follow the PRD evidence package shape.
```

---

## Definition of done

A stage is done only when:

1. Code is implemented.
2. Tests are added.
3. Tests pass.
4. Failure cases are handled.
5. The public API shape remains compatible.
6. No forbidden early-scope work was added.
7. Documentation or README is updated when behavior changes.
