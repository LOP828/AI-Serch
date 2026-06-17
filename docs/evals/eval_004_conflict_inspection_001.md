# Eval 004 Conflict Inspection 001

版本：v0.2.8 inspection  
文档类型：eval_004 conflicting 人工结构化检查  
范围：基于 `docs/evals/tavily_real_world_eval_run_005.md` 和 `docs/eval_004_conflict_analysis_plan.md`

---

# 1. 记录边界

本文件只使用 `docs/evals/tavily_real_world_eval_run_005.md` 中已经记录的脱敏摘要，不保存 raw provider payload，不保存完整网页正文，也不补造 run_005 中没有的数据。

本文件目标是人工检查 eval_004 的 `conflicting` 根因，判断下一刀应优先看：

- `evidence_extractor`
- `conflict_detector`
- product_info claim semantics

不建议在此阶段调高 scorer、放宽 aggregator 或继续扩大 source ranking。

---

# 2. Eval 004 基本信息

```yaml
eval_id: eval_004
query: RTX 5070 Ti 是否是 16GB 显存？
question_type: product_info
overall_status: conflicting
overall_confidence: 0.6
claims_count: 1
sources_count: 2
evidence_count: 2
conflicts_count: 1
page_fetch_status_counts:
  fallback: 2
```

Final sources:

| source_id | title | domain | source_type | base_reliability | is_primary_source |
|---|---|---|---|---:|---|
| s1 | Topic: [HELP] RTX 5070 Ti with low on NVIDIA #GeForce Forums | `nvidia.com` | `product_page` | 0.8 | true |
| s2 | GPU not detected (RTX 5070 Ti - "No \| NVIDIA GeForce Forums | `nvidia.com` | `product_page` | 0.8 | true |

Inspection note:

- final sources 已是 `nvidia.com / product_page`。
- source recall 不应作为 eval_004 当前主要问题。
- 两个 source 都像 NVIDIA GeForce Forums 页面，而不是明确的 NVIDIA official specification page。
- run_005 记录的 page fetch status 是 `fallback`，说明 evidence 可能来自 snippet 或短文本。

---

# 3. Claim Inspection

| claim_id | claim_text | claim_type | status | confidence | evidence_count |
|---|---|---|---|---:|---:|
| c1 | RTX 5070 Ti 是否是 16GB 显存？ 这一问题可以被外部来源验证 | `general_fact` | `conflicting` | 0.7216 | 2 |

人工判断：

- claim 语义目前偏粗，`claim_type=general_fact` 没有表达这是 product spec numeric claim。
- claim_text 没有显式结构化约束：同一型号、同一规格字段、同一数值。
- 对显存规格类问题，理想判断边界应是：
  - 型号：`RTX 5070 Ti`
  - 属性：显存 / VRAM / memory size
  - 目标值：`16GB`，并接受 `16G` 等价表达

可能问题：

- product_info claim semantics 还没有明确绑定型号、属性和值。
- 这会把 evidence_extractor 和 conflict_detector 推到更难的位置。

---

# 4. Evidence Inspection

## 4.1 Evidence 1

| field | value |
|---|---|
| evidence_id | ev-c1-s1-1 |
| source_id | s1 |
| system support_type | `oppose` |
| relevance_score | 0.81 |
| final_score | 0.7128 |
| short_excerpt | `[HELP] RTX 5070 Ti with low GPU usage in DX11/DX12 (constant VRel) — FurMark OK (~300W), but Fire St. PC Specifications GPU: MSI GeForce RTX 5070 Ti 16G Ventus 3X OC Drivers tes...` |

人工判断：

- 该 excerpt 不应轻易作为 `oppose`。
- excerpt 中出现 `RTX 5070 Ti 16G`，在显存语境下 `16G` 应视为 `16GB` 的等价表达。
- 仅根据 run_005 摘要，未看到同一型号对应非 16GB 显存值。
- 因此该 excerpt 更接近 support 或至少无法判断，不应作为明确 oppose。

可能问题：

- 型号绑定：excerpt 明确包含 `RTX 5070 Ti`，与目标型号一致。
- 数值绑定：excerpt 明确包含 `16G`，应与 `16GB` 等价。
- `16G` vs `16GB`：可能未被 evidence extractor 正确归一化。
- 页面噪音：标题包含 low GPU usage / DX11 / DX12 / driver 等故障上下文，可能干扰了 support_type。
- 其他型号串扰：run_005 摘要中没有看到其他型号数值，但 fallback snippet 可能存在截断或上下文不完整。

Root-cause signal:

- 更像 evidence_extractor support/oppose 判定问题。
- conflict_detector 只是接收了一个 high-score `oppose` evidence 后触发 conflict。

## 4.2 Evidence 2

| field | value |
|---|---|
| evidence_id | ev-c1-s2-1 |
| source_id | s2 |
| system support_type | `support` |
| relevance_score | 0.82 |
| final_score | 0.7216 |
| short_excerpt | `My system specs: GPU: MSI GeForce RTX 5070 Ti 16GB CPU: AMD Ryzen 7 7800X3D Motherboard: MSI B840 GAMING PLUS WIFI AM5 DDR5 PSU: GamePower AXG-850 850W` |

人工判断：

- 该 excerpt 支持 `RTX 5070 Ti 是否是 16GB 显存`。
- excerpt 明确包含同一型号 `RTX 5070 Ti` 和目标数值 `16GB`。
- 但它来自论坛用户的 system specs，而不是官方规格表；因此它可以作为 support evidence，但不应被当作 NVIDIA official spec page 的同等强度证据。

可能问题：

- 型号绑定：明确绑定 `RTX 5070 Ti`。
- 数值绑定：明确绑定 `16GB`。
- 页面噪音：论坛用户配置可能不是官方规格页，可靠性应谨慎。
- 其他型号串扰：run_005 摘要未显示其他型号污染该 excerpt。

Root-cause signal:

- 该 evidence 的 support_type 合理。
- 更大的问题是 source page 类型和 evidence 语义质量：`nvidia.com` official-domain forum 不等于 NVIDIA official specification page。

---

# 5. Conflict Inspection

Run 005 conflict:

| conflict_id | claim_id | severity | summary |
|---|---|---|---|
| conflict-1 | c1 | minor | High-confidence supporting and opposing evidence were found for the same claim. |

人工判断：

- conflict_detector 当前输出是可解释的：同一 claim 下存在 system-labeled `support` 和 `oppose` evidence。
- 但从 excerpt 本身看，`oppose` evidence 不够成立。
- 因此本次 conflict 更可能是上游 evidence_extractor 的 support_type 误判造成，而不是 conflict_detector 本身必然错误。

关键规则：

- 如果 oppose excerpt 中出现 `RTX 5070 Ti 16G` / `RTX 5070 Ti 16GB`，它不应轻易作为 oppose。
- `16G` 和 `16GB` 在显存语境下应被视为等价表达。
- oppose evidence 必须明确同一型号对应非 16GB 数值。
- 不能只因为页面包含其他型号、故障描述、驱动问题、论坛噪音或截断上下文就标为 oppose。

---

# 6. Root Cause Assessment

| possible root cause | assessment | priority |
|---|---|---|
| source recall failure | 不成立。final sources 已是 `nvidia.com / product_page`。 | low |
| source ranking failure | 不成立。当前问题不是官方源进不来。 | low |
| evidence_extractor support/oppose error | 最可能。`oppose` excerpt 中出现 `RTX 5070 Ti 16G`。 | high |
| conflict_detector over-trigger | 次要。若 `oppose` 是误判，conflict detector 只是按输入触发。 | medium |
| product_info claim semantics too broad | 重要背景问题。当前 claim 没有型号/属性/数值边界。 | medium |
| snippet/page extraction noise | 可能存在。run_005 记录 page fetch 为 `fallback`，且 sources 是论坛页面。 | medium |

结论：

下一刀应优先看 `evidence_extractor` 对 product spec numeric claims 的 support/oppose 判定。`conflict_detector` 可以补保护性测试，但不应作为第一修复点。product_info claim semantics 值得后续最小增强，但不应在未锁定 evidence 误判前扩大改动面。

---

# 7. Recommended Next Cut

## Priority 1: evidence_extractor product spec support/oppose guard

为什么现在做：

- run_005 的 `oppose` excerpt 包含 `RTX 5070 Ti 16G`。
- 对 `RTX 5070 Ti 是否是 16GB 显存？` 来说，这不应被标成明确反对。
- 错误的 `oppose` 会直接触发 conflict。

应改方向：

- 在 product spec / numeric claim 的 evidence 判断中，要求 support evidence 同时包含目标型号和目标值。
- 对 `16G` / `16GB` 做显存语境等价处理。
- 要求 oppose evidence 明确包含同一型号和不同显存值，例如同一型号绑定 `12GB` 或 `24GB`。
- 只有其他型号或故障上下文时，不应输出 oppose。

应优先补测试，而不是先调运行阈值。

## Priority 2: conflict_detector product spec numeric claim protection

为什么作为第二优先级：

- conflict_detector 不应替 evidence_extractor 修正错误 support_type。
- 但它可以有保护性边界：产品规格类 claim 的 conflict 应由真正同一型号不同数值触发。

应改方向：

- 如果 support/oppose 证据没有明确同一型号与不同数值绑定，不应升级为强 conflict。
- weak / neutral / unrelated evidence 不应触发 conflict。

## Priority 3: product_info claim semantics refinement

为什么后置：

- claim 当前是 `general_fact`，确实偏粗。
- 但最直接的失败信号是 `oppose` evidence 对 `16G` 的误判。
- claim semantics 可以作为后续 v0.2.x 小刀，不应一次扩大到完整产品知识图谱。

---

# 8. Minimal Test Suggestions

下一阶段如进入代码，建议最小测试覆盖：

1. `RTX 5070 Ti 16G` 应 support `RTX 5070 Ti 是否是 16GB 显存？`。
2. `RTX 5070 Ti 16GB` 应 support `RTX 5070 Ti 是否是 16GB 显存？`。
3. `RTX 5070 16GB` 不应 support `RTX 5070 Ti 是否是 16GB 显存？`。
4. `RTX 5080 16GB` 不应 support `RTX 5070 Ti 是否是 16GB 显存？`。
5. 其他型号不同显存不应 oppose `RTX 5070 Ti 是否是 16GB 显存？`，除非明确绑定 `RTX 5070 Ti`。
6. 同一型号明确写 `RTX 5070 Ti 12GB` 才能 oppose 16GB claim。
7. 同一型号明确写 `RTX 5070 Ti 24GB` 才能 oppose 16GB claim。
8. forum snippets 中的 low GPU usage、driver、GPU not detected 等故障描述不应构成显存规格 oppose evidence。

---

# 9. Explicit Non-goals

- 不接 Brave / SerpAPI。
- 不改 TavilyProvider。
- 不继续扩大 source ranking。
- 不调高 scorer。
- 不放宽 aggregator。
- 不把 `nvidia.com` forum 等同于 NVIDIA official specification page。
- 不做复杂知识图谱。
- 不引入 LLM reranker。
- 不保存 raw provider payload。
- 不保存完整网页正文。

---

# 10. Final Judgment

本次人工检查认为：

- eval_004 的 `conflicting` 更可能来自 evidence_extractor 的 product spec support/oppose 判定问题。
- 具体信号是 system-labeled `oppose` excerpt 中出现了 `RTX 5070 Ti 16G`，而 `16G` 在显存语境下应与 `16GB` 等价。
- conflict_detector 当前可能只是按 support/oppose 输入正常触发 conflict，因此不应优先改 scorer 或 aggregator。

推荐下一刀：

1. 优先补 evidence_extractor 的 product spec numeric claim 测试。
2. 再视测试结果决定是否加 conflict_detector 保护。
3. 后续再考虑 product_info claim semantics 的最小增强。
