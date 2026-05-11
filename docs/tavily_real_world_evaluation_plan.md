# Tavily Real-world Evaluation Plan

版本：v0.2.3-tavily-real-world-eval  
文档类型：真实 Tavily 搜索进入 CSL 主链路后的质量评估方案  
当前状态：评估计划文档，不包含生产代码、测试代码或真实网络调用

---

# 1. 背景与阶段定位

Critical Search Layer 当前已经完成 v0.1 mock/static MVP、v0.2.0 SearchProvider Foundation、v0.2.1 TavilyProvider opt-in，以及 v0.2.2 trusted-search route 层 Tavily opt-in wiring。

当前能力边界：

```text
/api/v1/trusted-search 已在 route 层接入 search_provider_factory
默认 provider 仍为 static
TavilyProvider 只能通过显式 opt-in 进入主链路
默认 pytest 不访问真实网络
API key 只能通过临时环境变量传入
```

本阶段建议名称：

```text
v0.2.3-tavily-real-world-eval
```

本阶段不是继续扩展 provider 数量，也不是优化算法。当前不急着接 Brave / SerpAPI。重点是验证：当 Tavily 真实搜索结果进入 CSL 主链路后，最终 evidence package 的质量是否可靠，问题主要卡在 source classification、page fetch、evidence extraction、reliability scoring、claim aggregation，还是 answer constraints。

---

# 2. 本阶段目标

本阶段目标是设计一套可人工复核的真实样本评估方法，用于观察真实 Tavily 搜索结果进入 CSL 后的质量瓶颈。

具体目标：

- 用真实 Tavily 搜索样本验证 CSL 主链路质量。
- 观察 `source_classifier` 是否能正确分类真实来源。
- 观察 `page_fetcher` 是抓到正文还是 fallback snippet。
- 观察 `evidence_extractor` 是否能抽出有效证据。
- 观察 `reliability_scorer` 是否存在过高或过低评分。
- 观察 `claim_aggregator` 是否过度 `confirmed` 或过度 `uncertain`。
- 观察 `answer_constraints` 是否能正确限制最终回答语气。
- 记录问题和失败模式，不急着优化算法。

本阶段产物应先是评估计划和人工观察框架，而不是自动化评分系统。

---

# 3. 本阶段非目标

本阶段明确不做：

- 不接 Brave / SerpAPI。
- 不改默认 provider。
- 不让默认 pytest 访问真实网络。
- 不改 `SearchResultSchema` / `SourceSchema`。
- 不改 MCP。
- 不做数据库。
- 不做前端。
- 不接真实 LLM。
- 不让 `SearchAdapter` 消费 `search_plan` queries。
- 不直接大改 scoring / extractor / classifier。
- 不把 API key 写入仓库。

本阶段只观察真实搜索结果进入现有 pipeline 后的表现。任何优化建议都应先记录为后续问题清单，避免因为少量真实样本的偶然结果直接大改系统。

---

# 4. 评估问题集设计

以下问题先作为候选集。本轮不要求真实运行，也不要求保存真实响应。

## A. AI 模型信息

目标：验证模型发布、权重开放、许可证、模型卡、代码仓库等信息是否能被拆解、检索、分类和约束。

候选样本：

- GPT-4.1 是否是 OpenAI 发布的模型？
- DeepSeek-V3 是否公开了模型权重？
- Llama 3.1 是否公开权重并允许商用？
- Qwen3 是否有官方模型卡？
- MiroThinker 1.7 是不是开源模型？

重点观察：

- 是否优先出现官方博客、官方文档、Hugging Face、ModelScope、GitHub、arXiv 等来源。
- 是否能区分“权重开放”“代码开放”“训练数据开放”“许可证允许商用”和“严格开源”。
- 是否把社区讨论或媒体转述误判为官方确认。

## B. 科技新闻 / 发布信息

目标：验证时效性问题下，系统是否能避免把传闻、媒体转述或社区讨论直接聚合成 confirmed。

候选样本：

- OpenAI 最近是否发布了新的语音模型？
- Anthropic 最近是否发布了新的 Claude 模型？
- Google Gemini 最近是否发布了新版本？
- Meta 最近是否发布了新的 Llama 系列模型？
- xAI 最近是否发布了新的 Grok 模型？

重点观察：

- 是否出现官方博客、release notes、新闻稿或可信媒体。
- 最新消息是否容易因页面日期缺失导致 recency 失真。
- 没有官方来源时，answer constraints 是否要求谨慎表达。

## C. 产品参数

目标：验证产品规格、硬件参数、厂商页面、电商页面和评测页面的来源质量。

候选样本：

- RTX 5070 Ti 是否是 16GB 显存？
- 某款笔记本是否搭载 RTX 5070 8GB？
- AMD Ryzen 9 9950X 是否是 16 核 32 线程？
- Intel Core Ultra 9 285K 是否支持指定核心数 / 线程数？
- 某款 GPU 是否支持 PCIe 5.0？

重点观察：

- 厂商官网、产品规格页、评测媒体和电商参数页是否分类合理。
- 搜索结果中 SEO 聚合站是否过多。
- 参数冲突时是否能避免过度 confirmed。

## D. 政策 / 法规 / 官方信息

目标：验证政策法规问题下，系统是否优先政府、监管机构、法律原文等一手来源，并保持高证据门槛。

候选样本：

- 某项政策是否仍然有效？
- 某监管机构是否发布了某公告？
- 某法律条文是否有最新修订？
- 美国 FTC 是否发布了某项监管公告？
- 欧盟是否更新了某项 AI 相关法规要求？

重点观察：

- 是否优先出现 `.gov`、监管机构、官方公报或法规原文。
- 媒体解读是否被错误当作主要证据。
- 政策有效性和最新修订是否因 fetch 失败或日期缺失而变得不可靠。

---

# 5. 每个样本要记录的字段

每个真实评估样本建议按以下字段记录。第一版可手动记录为 Markdown 表格或 YAML-like block。

```text
eval_id:
query:
question_type:
strictness:
max_sources:
run_time:
provider:
opt-in env used:
claims count:
sources count:
evidence count:
page_fetch status summary:
source_type distribution:
claim statuses:
overall_status:
overall_confidence:
answer_constraints.allowed_tone:
human_notes:
suspected_failure_points:
```

字段说明：

- `eval_id`：例如 `tavily-ai-model-001`。
- `run_time`：记录本地运行时间，建议使用 ISO-like 时间，避免只写“今天”。
- `opt-in env used`：只记录是否使用 opt-in 变量，不记录 API key 值。
- `page_fetch status summary`：例如 `success=2, fallback_snippet=5, timeout=1`。
- `source_type distribution`：例如 `official_blog=1, mainstream_media=2, unknown=5`。
- `claim statuses`：记录各 claim 的 `confirmed` / `likely` / `uncertain` / `unsupported` / `conflicting` / `false_likely` 分布。
- `human_notes`：人工观察到的具体质量问题。
- `suspected_failure_points`：可写 `search_quality`、`source_classifier`、`page_fetcher`、`evidence_extractor`、`reliability_scorer`、`claim_aggregator`、`answer_constraints`。

---

# 6. 质量评估维度

## A. Search Quality

检查 Tavily 返回的候选来源质量：

- Tavily 返回来源是否相关。
- 是否优先出现官方 / 一手来源。
- 是否有 SEO / 低质量来源。
- 是否缺少关键来源。
- 是否返回重复、转载、聚合页或明显过时页面。

人工判断重点：如果搜索结果本身没有提供可验证材料，后续 evidence pipeline 不应被要求强行产出 confirmed。

## B. Source Classification Quality

检查 `source_classifier` 对真实 URL 的分类：

- 官方文档是否识别正确。
- GitHub / Hugging Face / arXiv / 政府网站是否识别正确。
- `unknown` 是否过多。
- 是否误把媒体 / 社区内容当一手来源。
- 是否需要补充新域名规则，例如官方 blog 子域名、厂商 support 页面、监管机构子站。

人工判断重点：source type 只提供基础可靠度，不能因为域名看起来权威就自动确认所有 claim。

## C. Page Fetch Quality

检查 `page_fetcher` 是否提供了可用于抽证据的正文：

- fetch 成功比例。
- fallback snippet 比例。
- 是否正文为空。
- 是否抓到了导航 / 广告 / 噪声。
- 是否需要后续特殊处理 GitHub / Hugging Face / PDF。
- 是否因动态渲染、反爬、登录页、地区限制导致正文不可用。

人工判断重点：如果大量使用 fallback snippet，证据质量和评分应被谨慎解读。

## D. Evidence Extraction Quality

检查 `evidence_extractor` 是否真正抽出了绑定 claim 的短证据：

- evidence 是否真正支持 claim。
- 是否出现无关证据。
- 是否遗漏关键证据。
- `support` / `oppose` / `partial` 是否判断合理。
- `evidence_text` 是否过长或过短。
- evidence 是否来自 source text 或 snippet，而不是系统推测。

人工判断重点：没有证据时应返回空 evidence，而不是为了填充结果生成弱证据。

## E. Reliability Scoring Quality

检查 `reliability_scorer` 分数是否符合人工直觉和规则边界：

- 官方来源分数是否合理。
- 社区 / SEO 来源分数是否过高。
- recency 是否合理。
- `primary_source_factor` 是否合理。
- 是否出现低质量来源高分。
- 低 relevance 是否仍被强 source base score 抬得过高。

人工判断重点：评分是 explainability，不是绝对真理。高分证据仍需要看 evidence_text 是否真的支持 claim。

## F. Claim Aggregation Quality

检查 `claim_aggregator` 对多条 evidence 的聚合是否稳健：

- `confirmed` 是否过度自信。
- `uncertain` 是否过度保守。
- `unsupported` 是否合理。
- `conflicting` 是否能暴露冲突。
- 是否因为单条低质量支持证据就把 claim 推到 confirmed。
- 是否因为 fetch 失败导致所有 claim 机械地 unsupported。

人工判断重点：聚合状态必须能反映证据强弱，而不是只反映是否搜到了某个网页。

## G. Answer Constraint Quality

检查 `answer_constraints` 是否正确限制下游回答：

- `allowed_tone` 是否匹配证据强弱。
- `uncertain` 时是否要求披露不确定性。
- `conflicting` 时是否要求说明冲突。
- `forbidden_phrases` 是否合理。
- `required_phrases` 是否能提示关键限制，例如区分权重、代码、训练数据和许可证。

人工判断重点：当证据不足、来源冲突或只剩 snippet fallback 时，系统必须限制高确定性表达。

---

# 7. 人工评分表

建议每个样本按 1-5 分记录以下评分：

| 字段 | 分数 | 说明 |
|---|---:|---|
| `search_relevance_score` | 1-5 | Tavily 返回结果与 query / claims 的相关性 |
| `source_quality_score` | 1-5 | 来源是否权威、一手、少 SEO 或低质量内容 |
| `source_classification_score` | 1-5 | CSL 对来源类型和 primary source 的判断是否合理 |
| `fetch_quality_score` | 1-5 | page fetch 是否抓到可用正文，fallback 是否可接受 |
| `evidence_quality_score` | 1-5 | evidence 是否准确、短、绑定 claim、无编造 |
| `scoring_reasonableness_score` | 1-5 | final_score 和 score_breakdown 是否合理 |
| `aggregation_reasonableness_score` | 1-5 | claim status 和 overall_status 是否合理 |
| `answer_constraint_score` | 1-5 | answer_constraints 是否正确限制语气 |
| `overall_trust_score` | 1-5 | 该 evidence package 是否值得给下游 AI 使用 |

评分含义：

```text
1 = 严重不可用，可能误导下游回答
3 = 可用但需要人工判断，不能直接作为高置信依据
5 = 质量较好，可作为后续自动化基础
```

建议记录分数时同时写一句人工理由。例如：

```text
evidence_quality_score: 3
reason: 抽到了相关片段，但只来自 fallback snippet，且没有覆盖许可证 claim。
```

---

# 8. 运行方式设计

真实 eval 必须显式 opt-in。默认测试和默认运行不得访问真实 Tavily 网络。

需要临时环境变量：

```text
CSL_RUN_INTEGRATION_TESTS=true
CSL_SEARCH_PROVIDER=tavily
CSL_SEARCH_ALLOW_NETWORK=true
CSL_SEARCH_API_KEY=<temporary local value>
```

安全规则：

- API key 只能用临时环境变量。
- 不要写入文档、代码、`.env`、README、Git 历史。
- 不要在终端输出、测试失败信息、日志或评估记录中粘贴 API key。
- 跑完后必须清理环境变量。
- 默认 `pytest` 不运行真实 eval。

PowerShell 清理示例：

```powershell
Remove-Item Env:\CSL_RUN_INTEGRATION_TESTS
Remove-Item Env:\CSL_SEARCH_PROVIDER
Remove-Item Env:\CSL_SEARCH_ALLOW_NETWORK
Remove-Item Env:\CSL_SEARCH_API_KEY
```

如果某个变量不存在，PowerShell 可能提示路径不存在；只清理当前实际设置过的变量即可。

真实 eval 应作为手动流程执行，不能成为默认 CI 或默认 `uv run pytest` 的一部分。

---

# 9. 输出保存策略

本阶段先不引入数据库。

建议：

- 先手动保存 Markdown 评估记录。
- 后续可以考虑 JSONL，便于聚合统计。
- 不提交包含 API key、敏感 header、完整 raw payload 的文件。
- 可以保存脱敏后的 `TrustedSearchResponse` 摘要。
- 如要保存完整响应，必须确认没有 key、敏感 header、用户隐私或不应提交的 provider debug 信息。

未来可考虑新增文件：

```text
docs/evals/tavily_real_world_eval_notes.md
docs/evals/tavily_real_world_eval_template.md
```

本轮只写 plan，不新增 eval notes 文件，也不新增 eval template 文件。

建议保存摘要而非完整响应：

```text
query
question_type
source_type distribution
fetch_status summary
claim status distribution
answer_constraints summary
human scores
human notes
suspected failure points
```

---

# 10. 风险与注意事项

真实 Tavily eval 存在以下风险：

- 真实搜索结果会波动，同一 query 不同时间可能返回不同来源。
- Tavily quota / rate limit 可能影响样本运行。
- 网页抓取可能失败、超时、被阻止或只拿到 snippet。
- 外部页面会变化，页面结构和内容可能随时间更新。
- `source_classifier` 当前规则可能不足，真实域名下 `unknown` 可能偏多。
- `evidence_extractor` 规则版能力有限，可能漏抽关键证据或误判 support type。
- mock 测试稳定性不能被真实搜索破坏。
- 不应因为单次真实搜索结果就大改系统。
- 不应把 Tavily 返回的 snippet 直接等同于高质量证据。
- 不应把 provider 搜索排名等同于 CSL 的可靠性排序。

处理原则：

```text
先记录失败模式
再按模块归因
最后决定是否优化
```

---

# 11. 后续阶段建议

建议把 v0.2.3 拆成以下小阶段：

## v0.2.3-a：写评估计划文档

产物：

```text
docs/tavily_real_world_evaluation_plan.md
```

边界：

```text
不改生产代码
不改测试代码
不发真实网络请求
```

## v0.2.3-b：新增 eval 记录模板

产物建议：

```text
docs/evals/tavily_real_world_eval_template.md
```

边界：

```text
只新增模板
仍不跑真实 Tavily eval
```

## v0.2.3-c：手动跑 5 个真实样本

建议样本：

```text
2 个 AI 模型信息
1 个科技新闻 / 发布信息
1 个产品参数
1 个政策 / 官方信息
```

边界：

```text
必须显式 opt-in
必须使用临时 API key
必须脱敏记录
```

## v0.2.3-d：整理质量问题清单

按模块归因：

```text
search_quality
source_classifier
page_fetcher
evidence_extractor
reliability_scorer
claim_aggregator
answer_constraints
```

## v0.2.3-e：决定优先修哪个模块

候选优先级：

```text
source_classifier
page_fetcher
evidence_extractor
reliability_scorer
```

决策原则：先修最频繁、最影响 evidence package 可信度、且改动最小的瓶颈。

---

# 12. 本阶段禁止事项

本阶段必须严格禁止：

- 不改生产代码。
- 不改测试代码。
- 不发真实网络请求。
- 不读取、申请、写入 API key。
- 不新增依赖。
- 不修改 `pyproject.toml`。
- 不修改 `env.example`。
- 不修改 README。
- 不修改 MCP。
- 不修改 `TrustedSearchService`。
- 不修改 `SearchAdapter`。
- 不修改 `SearchResultSchema` / `SourceSchema`。
- 不移动 v0.2.0 / v0.2.1 / v0.2.2 标签。
- 不补 v0.1.7 tag。
- 不重写 Git 历史。

完成本阶段后，只应出现一个新增文件：

```text
docs/tavily_real_world_evaluation_plan.md
```

---

# 13. 本阶段完成检查

本阶段完成时应检查：

```text
uv run pytest
uv run ruff check .
git status --short
```

预期：

```text
默认 pytest 不访问真实网络
默认测试保持稳定
ruff 通过
只新增 docs/tavily_real_world_evaluation_plan.md
没有 API key、真实响应、raw payload 或敏感 header 进入仓库
```
