# Eval 004 Conflict Analysis Plan

版本：v0.2.7 follow-up plan  
文档类型：eval_004 conflicting 分析计划  
范围：基于 `docs/evals/tavily_real_world_eval_run_005.md` 和 `docs/evals/tavily_real_world_eval_findings_005.md`

---

# 1. 目标

为下一阶段分析 eval_004 的 `conflicting` 结果制定最小方案。

本计划不把问题重新归因到 source recall / source ranking。v0.2.6 已让 RTX 5070 Ti 样本命中 `nvidia.com` official-domain candidate，并进入 final sources。run_005 中的问题是：官方域名来源已进入，但同一 claim 下同时出现 support 与 oppose evidence。

下一刀应先判断冲突来自哪里：

- evidence extraction 是否把上下文噪音误判为反对证据；
- conflict detection 是否对产品规格数值类 claim 过于敏感；
- product spec claim 语义是否太粗；
- page extraction / snippet fallback 是否引入型号串扰；
- NVIDIA 页面是否同时包含多个型号或用户配置，导致规格串扰。

---

# 2. 现象描述

## 2.1 Run 005 eval_004 状态

`docs/evals/tavily_real_world_eval_run_005.md` 记录：

```yaml
eval_id: eval_004
query: RTX 5070 Ti 是否是 16GB 显存？
question_type: product_info
overall_status: conflicting
overall_confidence: 0.6
claims_count: 1
evidence_count: 2
conflicts_count: 1
answer_allowed_tone: conflict_aware
must_disclose_uncertainty: true
can_answer_confidently: false
```

Final sources 均为 `nvidia.com`：

| source_id | domain | source_type | base_reliability | is_primary_source |
|---|---|---|---:|---|
| s1 | `nvidia.com` | `product_page` | 0.8 | true |
| s2 | `nvidia.com` | `product_page` | 0.8 | true |

Evidence 摘要：

| evidence_id | source_id | support_type | final_score | 摘要 |
|---|---|---|---:|---|
| ev-c1-s1-1 | s1 | `oppose` | 0.7128 | 摘录中出现 `MSI GeForce RTX 5070 Ti 16G Ventus 3X OC` |
| ev-c1-s2-1 | s2 | `support` | 0.7216 | 摘录中出现 `MSI GeForce RTX 5070 Ti 16GB` |

## 2.2 初步判断

这不是当前最主要的 source recall 问题。

原因：

- eval_004 已命中 `nvidia.com`。
- final sources 的 `source_type` 已是 `product_page`。
- conflicting 来自同一 claim 下同时出现 support / oppose evidence。

因此下一阶段应检查证据边界，而不是继续扩大 source ranking。

---

# 3. 可能原因分类

## 3.1 Claim 表达可能过于粗糙

当前 claim：

```text
RTX 5070 Ti 是否是 16GB 显存？ 这一问题可以被外部来源验证
```

这个 claim 对产品规格类问题可能过于粗：

- 没有明确规格字段是 `VRAM / memory size`；
- 没有要求型号必须严格匹配 `RTX 5070 Ti`；
- 没有区分桌面版、Laptop、厂商 OC 型号、论坛用户配置；
- 没有要求数值必须直接绑定同一型号。

可能的后续方向不是扩大 claim 数量，而是给 product_info spec claim 增加更明确的语义边界。

## 3.2 Evidence extractor 可能误判 oppose

run_005 中被标为 `oppose` 的 excerpt 同样包含：

```text
MSI GeForce RTX 5070 Ti 16G Ventus 3X OC
```

这看起来更像支持 16GB / 16G 的证据，而不是反对证据。需要检查：

- `oppose` 是否由附近其他文本触发；
- 是否把 low GPU usage、driver、forum issue 等非显存信息当作反对；
- 是否因为 query 是疑问句而错误处理了 support_type；
- 是否对 `16G` 与 `16GB` 的等价关系处理不足。

## 3.3 Conflict detector 可能对数值类证据过于敏感

当前 conflict summary：

```text
High-confidence supporting and opposing evidence were found for the same claim.
```

如果 `oppose` 是误抽取，conflict detector 的输出是合理后果，不是根因。

需要确认：

- conflict detector 是否只根据 support_type 聚合；
- 是否需要在产品规格类 claim 中要求 oppose evidence 明确包含同一型号的不同数值；
- 是否应把低语义质量的 oppose evidence 降为 neutral / partial，而不是让它触发 conflict。

## 3.4 Page extraction / snippet fallback 可能包含噪音

run_005 的 page fetch status 为 fallback。这意味着证据很可能来自 search snippet 或可用短文本，而不是稳定正文解析。

风险：

- snippet 可能截断关键上下文；
- forum 页面标题、用户配置、回复内容可能混杂；
- 一个页面可能同时包含问题描述、签名、其他用户硬件配置；
- `nvidia.com` official-domain forum 不等于 NVIDIA official spec page。

## 3.5 NVIDIA 页面可能存在型号串扰

产品规格类问题需要强绑定：

```text
same model + same attribute + same value
```

如果页面同时出现：

- `RTX 5070`
- `RTX 5070 Ti`
- `RTX 5070 Laptop`
- `RTX 5080`
- board vendor model names

则 evidence extractor 不能只靠页面级 source reliability 判断 support/oppose。

---

# 4. 分析顺序

## Step 1: 人工检查 run_005 中 eval_004 的结构化摘要

先只使用脱敏记录中已有信息：

- claim_text
- source title/domain/source_type
- evidence excerpt
- support_type
- final_score
- conflict summary

目标：

- 判断 `oppose` excerpt 是否真的反对 16GB 显存；
- 判断冲突是否来自 evidence extraction；
- 判断是否需要更细 product_info claim semantics。

## Step 2: 定位根因类型

按优先级判断：

1. evidence extraction 问题：support/oppose 分类错误。
2. conflict detection 问题：把弱反对或噪音证据升级成 conflict。
3. claim decomposition 问题：product spec claim 缺少型号、属性、数值绑定。
4. page extraction / snippet 问题：fallback 文本过短或混杂。

只有完成这一步后才决定是否改代码。

## Step 3: 形成最小修复方案

如果确认为 evidence extraction 问题：

- 优先补 `evidence_extractor` 的产品规格类测试；
- 要求 support evidence 同时包含目标型号和目标数值；
- 要求 oppose evidence 明确包含同一目标型号的不同数值；
- 对只包含其他型号、论坛问题、性能问题、驱动问题的文本返回 neutral 或空 evidence。

如果确认为 conflict detection 问题：

- 优先补 `conflict_detector` 的边界测试；
- 确认 conflict 只应由真正强反对证据触发；
- 不通过降低阈值或放宽聚合来掩盖问题。

如果确认为 claim decomposition 问题：

- 优先规划 product_info spec claim 的最小字段化语义；
- 不改 schema；
- 不做完整产品知识图谱；
- 只在 claim_text / claim_type 层面提升可验证性。

---

# 5. 下一刀候选

## 候选 A：doc-level conflict inspection helper / analysis

优先级最高。

建议先新增一个分析文档或轻量 helper，用于把单个 eval 的 claim/evidence/conflict 摘要展开成人工审查表。

目的：

- 不直接改运行逻辑；
- 不误把单个样本当作系统性 scorer / aggregator 问题；
- 为后续测试提供明确样例。

可能产物：

- `docs/evals/tavily_real_world_eval_005_conflict_analysis.md`

## 候选 B：evidence_extractor 产品规格边界测试

如果人工检查确认 `oppose` 是误判，则优先补 evidence extractor 测试。

应覆盖：

- `RTX 5070 Ti 16G` 应支持 16GB 显存 claim；
- `RTX 5070 Ti 16GB` 应支持 16GB 显存 claim；
- `RTX 5070 12GB` 不应反对 `RTX 5070 Ti 16GB`；
- `RTX 5070 Laptop 12GB` 不应反对桌面 `RTX 5070 Ti 16GB`；
- forum 中的 driver / low usage / GPU not detected 文本不应构成显存反对证据。

## 候选 C：conflict_detector 数值规格类边界测试

如果人工检查发现 evidence support_type 本身合理，但 conflict 触发过宽，则补 conflict detector 测试。

应覆盖：

- 同一型号、同一属性、不同数值才构成强 conflict；
- 其他型号的规格不应构成该 claim 的 oppose evidence；
- weak / neutral / unrelated evidence 不应触发 conflict。

---

# 6. 测试建议

下一阶段如进入代码，应优先补测试，不先改 scorer 或 aggregator。

建议测试方向：

1. product spec support evidence 必须同时包含同一型号和同一数值。
2. product spec oppose evidence 必须明确包含同一型号的不同数值。
3. `RTX 5070 Ti 16GB` 不应被 `RTX 5070`、`RTX 5080`、`RTX 5070 Laptop` 规格污染。
4. `16G` 与 `16GB` 在显存语境中应视为等价支持，而不是冲突信号。
5. forum / support page snippet 中的故障描述不应自动变成规格反对证据。
6. official-domain forum page 不应被当作 official specification page 的等价证据。

---

# 7. 明确不做

- 不接 Brave / SerpAPI。
- 不改 TavilyProvider。
- 不继续调 source ranking。
- 不调高 scorer。
- 不放宽 aggregator。
- 不做复杂知识图谱。
- 不引入 LLM reranker。
- 不把单个 eval_004 conflicting 样本直接解释为评分系统失败。
- 不在未检查 evidence 边界前改 claim_aggregator。

---

# 8. 推荐结论

eval_004 的下一刀应先做 conflict inspection，而不是直接改执行链路。

推荐顺序：

1. 新增 run_005 eval_004 conflict analysis 文档，人工标注 `oppose` evidence 是否真实反对。
2. 若 `oppose` 为误判，优先补 evidence_extractor 的 product spec 测试。
3. 若 evidence 合理但 conflict 触发过宽，再补 conflict_detector 的数值规格类测试。

当前不建议调 scorer、不建议放宽 aggregator、不建议继续扩大 source ranking。
