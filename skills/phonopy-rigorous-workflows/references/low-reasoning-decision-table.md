# 低推理模型机械决策表

唯一机器真源是 [weak-model-decision-table.json](weak-model-decision-table.json)
中的 shared `candidate-decision-table@1.0`。本表仅供人类阅读。按 ascending
priority 选择首个有精确证据的条件；不能建立时必须走最后的 fail-closed
default，不得猜命令、补 provenance、改负频符号或跨 lineage 拼产物。

| priority | 首个可观察条件 | finding / exit | 最小动作 |
|---:|---|---|---|
| 1 | 版本不为精确 4.3.1 或 stage 无 profile | `PH_VERSION_UNSUPPORTED` / 3 | 建 exact-version profile。 |
| 2 | unit/primitive identity、atom count 或 primitive matrix 不闭合 | `PH_STRUCTURE_INVALID` / 2 | 重建结构 manifest。 |
| 3 | supercell matrix 非整数 3×3、奇异或 determinant/atom count 不闭合 | `PH_SUPERCELL_INVALID` / 2 | 修正 supercell 并重建下游 hashes。 |
| 4 | displacement id/hash/index/vector norm 不合约 | displacement findings / 2 | 从同一结构重建位移集。 |
| 5 | displacement 与 force 不是严格一对一 | `PH_DISPLACEMENT_CLOSURE_FAILED` / 2 | 每个位移绑定唯一 force parent。 |
| 6 | force unit/shape/parent acceptance/projection 不合约 | force findings / 2 | 回上游计算并重新导出。 |
| 7 | ordered force-collection hash 不符 | `PH_FORCE_COLLECTION_HASH_MISMATCH` / 2 | 依 displacement id 规范重算。 |
| 8 | force constants shape 或两个 parent 不符 | `PH_FORCE_CONSTANTS_INVALID` / 2 | 用同一已验收 collection 重建。 |
| 9 | mesh/band/DOS/NAC 与 force-constant parent 不同 | `PH_PRODUCT_PARENT_MISMATCH` / 2 | 只选同一 lineage。 |
| 10 | frequency bytes/unit/3N/dimension/q-path 不合约 | table/product findings / 2 | 解析原始绑定 artifact。 |
| 11 | NAC tensor/primitive/response/unit/projection 不合约 | `PH_NAC_INVALID` / 2 | 从同一 primitive 的已验收 response 重建。 |
| 12 | output 存在、alias input 或 durable publish 失败 | output findings / 2 | 使用新的 absent target。 |
| 13 | 请求 native execution，但 exact 4.3.1 executable/distribution 不可用 | `PH_NATIVE_UNAVAILABLE` / 3 | 保持 documentation-only。 |
| 14 | 使用 v3 setup/collection、把 `phonopy-load` 当主命令、使用 main `--nac` 或 pinned parser 不存在的 option | `PH_V4_CLI_MISMATCH` / 3 | `phonopy-init` 负责 setup/collection，`phonopy` 负责 YAML calculation，并只用 4.3.1 options。 |
| 15 | capability 无 recipe 或官方文字与 pinned parser 冲突 | `PH_RECIPE_NOT_ESTABLISHED` / `PH_DOCUMENTATION_CONFLICT` / 3 | 解析 exact parser/source 冲突或建立 recipe。 |
| 16 | 所有当前 candidate gate 通过并保留 signed frequency | 无失败 finding / 0 | 只保存 `no_positive_claim` 报告；另做收敛和物理评审。 |
| 17 | 以上条件均不能由 exact evidence 建立 | `PH_DECISION_NO_MATCH` / 2 | 停止并补足能唯一选 case 的证据。 |

## 禁止的机械捷径

- v4 中不得用旧版单命令直觉代替 `phonopy-init`/`phonopy` 分工。
- 目录 listing、官网 prose 或 `--help` 单独都不是科学上充分的 recipe。
- 不把 `complete` 当 input、SCF、force、response 或 convergence acceptance。
- 不按文件名拼接父子产物，不因 projection 写了 `pass` 就忽略 raw hash。
- 不自动取负频绝对值，也不把 ASR/symmetrization 当作收敛证据。
