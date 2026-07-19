# 低推理模型机械决策表

唯一机器真源是符合 shared `candidate-decision-table@1.0` 的
[weak-model-decision-table.json](weak-model-decision-table.json)。本文件只供
人类阅读；逐项按 JSON 的 ascending priority 选择首个可由精确证据建立的
条件，无法建立时必须走最后的 fail-closed default。

| priority | 可直接观察的首个条件 | finding / exit | 最小动作 |
|---:|---|---|---|
| 1 | source 不是 bounded strict UTF-8 JSON object | `MW_SOURCE_INVALID` / 2 | 重新导出无 duplicate/BOM/NaN 的单一记录。 |
| 2 | format、basename 或 suffix 不一致 | `MW_SOURCE_PROVENANCE_INCOMPLETE` / 2 | 从 producer 证据修正，不得只改后缀。 |
| 3 | 实际 wavefunction 的 basename/hash/bytes 或 regular-file identity 不符 | `MW_WAVEFUNCTION_HASH_MISMATCH` / 2 | 提供同一原始 bytes 或重建证据。 |
| 4 | element、charge、electron、multiplicity 或 ECP closure 不成立 | `MW_SOURCE_PROVENANCE_INCOMPLETE` / 2 | 回到电子态/基组/ECP producer 记录。 |
| 5 | parent acceptance 任一不为精确 pass | `MW_PARENT_ACCEPTANCE_FAILED` / 2 | 回上游计算 Skill。 |
| 6 | raw parent hash 与 semantic projection 脱离 | `MW_PARENT_PROJECTION_MISMATCH` / 2 | 由同一 raw record 重建 projection。 |
| 7 | profile 未知 | `MW_PROFILE_UNKNOWN` / 2 | 选择 exact registered profile。 |
| 8 | community build 或无 exact platform regression | `MW_PROFILE_BLOCKED` / 3 | 补 build/banner/digest/transcript/terms 证据。 |
| 9 | 请求 native run，但 exact binary 不可用或 identity 未建立 | `MW_NATIVE_UNAVAILABLE` / 3 | 保持 documentation-only。 |
| 10 | function/subfunction 只有目录 listing，没有 exact recipe | `MW_RECIPE_NOT_ESTABLISHED` / 3 | 捕获完整 prompt/stdin/output/return/failure。 |
| 11 | noGUI/full mode 不兼容，或 input family 缺任务所需数据 | `MW_EXECUTION_MODE_INCOMPATIBLE` / `MW_INPUT_INELIGIBLE` / 3 | 换兼容 distribution 和语义完备输入；不得猜缺失信息。 |
| 12 | native menu task 不属于 guard 唯一的 inventory route | `MW_TASK_UNSUPPORTED` / 3 | 建独立 versioned menu contract 和 fixtures。 |
| 13 | banner 重复/漂移、sentinel 乱序或 fatal text | `MW_VERSION_MISMATCH` / `MW_PROMPT_DRIFT` / `MW_FATAL_SENTINEL` / 2 | 捕获并修复 exact-version 完整 transcript。 |
| 14 | charge table 的 unit/index/order/value/declared total/closure 不合约 | table/charge findings / 2 | 保持 atom order 和 charge state 重建表。 |
| 15 | output 存在、alias input 或 durable publish 失败 | output findings / 2 | 保留旧文件，使用新的 absent target。 |
| 16 | 所有当前请求的 candidate gate 通过 | 无失败 finding / 0 | 仅保留 `no_positive_claim` 报告；不可授权执行/晋级，另做科学评审。 |
| 17 | 以上条件均无法由 exact evidence 建立 | `MW_DECISION_NO_MATCH` / 2 | 停止并补足能唯一选择前述 case 的证据。 |

目录查询成功只说明手册中存在该功能；recipe plan 成功只说明已记录官方
序列；transcript 与 artifact gate 成功也不说明 population、bond order、
topology、IGMH、spectrum 或化学解释正确。所有 parser 只消费第一次 bounded
read 的已验证 bytes/text，验证后禁止按路径重新打开再解析。
