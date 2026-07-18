# DFT-Codex-Skills 全库审计 — 2026-07-18

## 结论

七个 Skill 的当前本地源码没有发现会阻断基本使用的结构或测试失败；主要欠缺集中在跨 Skill 数据谱系、共享语义/隐私校验、安装副本一致性和扩展成本，而不是 QE、VASP、CP2K、SIESTA 某一个 Skill 的单点失效。

审计期间先执行原有基线：220 项测试通过。补充软件注册、联动审计和两项根级回归后，fresh 全库回归共 222 项测试通过；七个 Skill 结构有效，所有 JSON Schema 和 agent YAML 可解析，Python 可编译，未发现大于 5 MiB 的仓库文件、已跟踪计算输出或明显敏感标记。

## 当前能力边界

| 模块 | 已具备 | 仍需补齐 |
|---|---|---|
| QE | 官方来源边界、计划/输入/输出/收敛 fail-closed gate、run manifest 交接 | capability catalog 仍是 Markdown；需统一机器 profile |
| VASP | 官方 Wiki 来源、任务证据 profile、输入/运行审计、收敛与 claim package | 与共享 semantic validator、artifact 来源绑定尚未接通 |
| CP2K | 官方手册同步、Quickstep 审计、任务/方法 profile、受控 forward fixture | 后处理各 observable 仍为 `design-only`；当前 fixture 不能证明 2026.2 正向运行成熟度 |
| SIESTA | 版本化官方来源、FDF/赝势/谱系/收敛 gate、任务 profile | 后处理各 observable 仍为 `design-only`；版本精确的运行 artifact 仍需补齐 |
| dft-postprocess | QE/VASP run trace、bands、DOS 和 real-space 等真实 artifact 路由；规范化数据、绘图、工具执行记录 | planner/backend 仍有中央条件链；run→plan→artifact 绑定不强制 |
| dft-campaign-efficiency | 隐私安全记录、run 转换、可比性和推荐门禁 | artifact 证据尚未形成强哈希闭环；共享验证入口未统一隐私规则 |
| CIF | 结构事实、对称性尝试、近邻距离和指定键长匹配 | 尚无跨计算代码共享的 structure manifest/结构谱系契约 |

后处理成熟度必须按 observable 阅读：QE 的 run trace、bands、DOS/PDOS、phonon、EPC、real-space 为 `real-artifact-validated`；VASP 的 run trace、bands、DOS/PDOS、real-space 为该级别；两者 NEB/optical 目前为 `synthetic-validated`；VASP phonon/EPC 及 CP2K/SIESTA 所有已登记 route 仍为 `design-only`。

## 已确认问题

### A. 交接和契约

1. README 描述“postprocessing consumes run manifests”，但当前 plan builder 不接收 run manifest，artifact builder 只接收可自由填写的 `source_run_ids`。没有 source manifest SHA-256、code/version/task 一致性或上游篡改检测。
2. 通用 `validate_contract.py` 只运行 JSON Schema。当前 Schema 会接受 `status=accepted`、`scientific_acceptance=not_assessed`、空 evidence 且 configuration 含绝对私有路径的组合；结构有效不等于语义或隐私有效。
3. 审计时 `create_run_manifest.py` 把 `evidence` 固定为空数组；本轮已补充 `--evidence` JSON 数组入口，但 terminal/accepted 状态所需的证据角色尚未由共享 semantic validator 强制。
4. artifact 只用 source ID，不绑定 run manifest；campaign record 也没有形成 run + artifact 的完整哈希链。
5. Schema 全部固定为 `schema_version: 1.0`，尚无迁移器或兼容性测试策略。

### B. 扩展性

1. 审计前，四个软件代码散落硬编码于五个 Schema、多个 CLI、安装/验证工具和 observable validator。新增软件容易出现“Schema 接受但 CLI 拒绝”或“CLI 接受但 route 缺失”。本轮已用统一软件注册表、Schema 同步检查和仓库审计器收敛这一问题。
2. postprocess 的 `_builtin_step` 是按 observable/code/backend 展开的中央条件链，capability detector 也维护固定工具表。新增 backend 仍需改中央代码，不是独立 adapter plugin。
3. `tools/run_tests.py` 知道每个计算 Skill 的私有测试命令；未来新增软件仍需修改总测试器。应改为每个 Skill 声明标准 check hook。
4. 计算功能 profile 尚未完全同构：VASP/CP2K/SIESTA 有 JSON task profile，QE 仍以 Markdown 合同为主。

### C. 部署、隐私和仓库卫生

1. 当前本地工作区有大量未提交更新，`HEAD` 与 `origin/main` 都停在 `17e475e`。因此远端 CI 只代表旧提交，不代表本次本地状态。
2. 常规 `~/.codex/skills` 中只有 `dft-postprocess` 指向本仓库；VASP/CIF 是真实目录，QE/CP2K/SIESTA/efficiency 在该位置缺失。另有旧名 QE 目录位于 `~/.agents/skills/qe-official-params`。安装版本存在漂移风险。
3. tool execution record 会记录解析后的绝对工作目录、输入/输出和日志路径。文档要求这类记录留在 runtime 外部区域，但 Schema/validator 未自动阻止误提交或进一步匿名化。
4. 工作区有被 `.gitignore` 正确排除的 `.DS_Store`、`__pycache__` 和 `.pyc`。它们未污染 Git，但可在无并行进程使用时定期清理。

## 本轮补充

- `registry/software-registry.yaml`：统一计算代码、计算 Skill、capability catalog、生命周期和服务接口。
- `tools/software_registry.py`：验证注册结构、Skill 与 catalog 路径。
- `tools/sync_contract_codes.py`：检查或显式同步五个共享 Schema 的 code enum。
- `tools/audit_repository.py`：检查注册 Skill、Schema、机器 capability catalog 和所有 observable 的代码覆盖；可选审计安装符号链接。
- `tools/create_run_manifest.py`：支持导入计算 Skill 生成的 evidence role/label/status/SHA-256 数组。
- 现有 manifest/安装/Skill 验证/后处理/效率 CLI 已改为从注册表读取代码或 Skill 列表。
- 根测试增加注册表扩展示例和全库接口一致性测试。

## 优先级

- P0：共享 semantic/privacy validator；run→plan→artifact 哈希绑定；安装副本迁移。
- P1：postprocess adapter plugin 接口；CP2K/SIESTA real-artifact 前向验证；QE 机器 capability profile；CIF structure manifest；标准 Skill test hook。
- P2：契约迁移、artifact 驱动的效率闭环、版本变化后的建议降级和更完整 CI。

具体接口、步骤和验收条件见 [`integration-and-extension-plan.md`](integration-and-extension-plan.md)。
