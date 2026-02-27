# VibeCollab 决策记录

## 待确认决策

(暂无)

## 已确认决策

### DECISION-017: v0.10.x 发布工程 — 从"能用"到"专业开源项目"
- **等级**: S
- **角色**: [PM] [ARCH]
- **问题**: 项目功能已基本完成 (v0.9.4, 1201 tests, 36 .py files, ~15K LOC)，但存在三大硬伤阻碍开源采纳：(1) 代码/CLI/文档全中文，国际受众无法使用 (2) 97 条 git commit 中英混杂，不专业 (3) README/GitHub 门面缺乏开源项目标准要素
- **决策**: 分 5 个版本递进完成，**严格按序执行，不可跳步**

#### 版本规划

**v0.10.0 — 最后业务逻辑 + 稳定性门槛**
> 确保功能冻结前所有业务逻辑闭环，建立发布质量门槛
- 外部项目 QA 全量验证（Phase 11 TC-E2E-001~010）
- 测试覆盖率 ≥ 85%
- `vibecollab check` 全绿
- MCP Server 在 Cursor/CodeBuddy 中实际验证
- 修复 QA 过程中发现的所有 bug
- **功能冻结**: 此版本后不再新增业务功能

**v0.10.1 — 代码国际化 (Code i18n)**
> 代码层面全英文化，确保非中文母语开发者可读
- **Scope 1: docstring/comment** — 36 个 .py 文件的中文注释/docstring 全部翻译为英文（~2055 行）
- **Scope 2: CLI help** — 62+ 处 `help=` 参数翻译为英文
- **Scope 3: 运行时输出** — `click.echo` / `console.print` 中的中文提示翻译为英文
- **Scope 4: 错误消息** — "错误:", "未找到" 等翻译为英文
- **不改**: 生成的 CONTRIBUTING_AI.md 模板内容保持中文（用户面向中文项目时需要）
- **参考模板**: `event_log.py`, `llm_client.py`, `config_manager.py`, `task_manager.py`（已是英文）
- 全量测试必须通过，覆盖率不降

**v0.10.2 — 文档双语化 (Doc Bilingual)**
> README 和核心文档提供英文版本
- README.md 重写为英文（作为主 README）
- README_CN.md 保留中文版
- CHANGELOG.md 整理为英文
- pyproject.toml description 英文化
- docs/ 下内部开发文档保持中文（开发者自用）

**v0.10.3 — Git 历史重写 + 仓库门面**
> 这是破坏性操作，必须在最后执行
- `git filter-branch` 或 `git-filter-repo` 重写全部 97+ commit message 为标准英文
  - 保持 Conventional Commits 格式: `feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `release:`
  - 保留关键信息（版本号、测试数、决策编号）
  - 一次性 force push（不可逆）
- GitHub 仓库门面:
  - About 描述 + Topics 标签
  - Issue / PR template
  - CONTRIBUTING.md (英文，面向外部贡献者)
  - CODE_OF_CONDUCT.md
  - GitHub Release 创建（v0.10.3 起）
  - Badge: PyPI / CI / Coverage / License / Python Version

**v1.0.0 — 正式发布**
> 标记稳定版本
- 清理所有 .dev0 标记
- PyPI v1.0.0 发布
- GitHub Release v1.0.0
- 宣发准备

#### 核心原则
1. **先功能冻结，再美化** — v0.10.0 之后不再新增功能
2. **先代码英文化，再文档英文化** — 代码是根本，文档跟随
3. **Git 历史重写放最后** — 避免 force push 后还要继续提交中文 commit
4. **每个版本自成一体，可独立发布 PyPI** — 任何版本都是可发布状态
5. **全量测试是铁门** — 每个版本必须 1201+ tests passed, 0 regression

#### 工作量估算

| 版本 | 核心工作 | 预估工时 |
|------|---------|---------|
| v0.10.0 | QA 验证 + bug fix + 覆盖率 | 2-3 session |
| v0.10.1 | 36 文件代码英文化 (~2055 行中文) | 3-4 session |
| v0.10.2 | README 英文重写 + CHANGELOG 整理 | 1-2 session |
| v0.10.3 | 97 commit 重写 + GitHub 门面 | 1-2 session |
| v1.0.0 | 版本号 + Release + 宣发 | 1 session |

- **日期**: 2026-02-27
- **状态**: CONFIRMED
- **影响**: 整个项目从 demo 阶段向 production 阶段过渡的关键路径

### DECISION-001: 将 llm.txt 重命名为 CONTRIBUTING_AI.md
- **等级**: A
- **角色**: [ARCH]
- **问题**: 输出文件名应该使用什么名称？
- **决策**: 使用 `CONTRIBUTING_AI.md` 作为主要输出文件
- **理由**: 
  - 更符合 GitHub 社区规范（类似 CONTRIBUTING.md）
  - 明确表示这是 AI 协作指南
  - 避免与 llms.txt 标准混淆
- **日期**: 2026-01-20
- **状态**: CONFIRMED
- **影响**: 所有代码、文档、模板中的引用都需要更新

### DECISION-002: 集成 llms.txt 标准
- **等级**: A
- **角色**: [ARCH]
- **问题**: 如何与 llmstxt.org 标准集成？
- **决策**: 在 llms.txt 中添加 AI Collaboration 章节，引用 CONTRIBUTING_AI.md
- **理由**:
  - llms.txt 是更广泛采用的标准
  - Context7 等工具原生支持
  - 未来 AI 训练/推理优先读取
  - 职责分离：llms.txt 描述项目，CONTRIBUTING_AI.md 定义协作规则
- **日期**: 2026-01-20
- **状态**: CONFIRMED
- **影响**: 新增 llmstxt.py 模块，自动检测和更新 llms.txt

### DECISION-003: 重命名包为 vibe-collab
- **等级**: A
- **角色**: [ARCH]
- **问题**: 包名应该叫什么？
- **决策**: 使用 `vibe-collab` 作为包名和仓库名
- **理由**:
  - 体现 Vibe Development 哲学
  - 强调协作（collaboration）特性
  - 避免与现有 PyPI 包名冲突
  - 更简洁、易记
- **日期**: 2026-01-20
- **状态**: CONFIRMED
- **影响**: 包名、仓库名、所有文档引用都需要更新

### DECISION-004: 项目生涯阶段信息放在 ROADMAP.md
- **等级**: B
- **角色**: [PM]
- **问题**: 项目生涯阶段信息应该放在哪里？
- **决策**: 放在 ROADMAP.md 文档中，而不是 CONTRIBUTING_AI.md
- **理由**:
  - ROADMAP 是 PM 侧重的文档
  - 生涯阶段管理更符合项目管理的范畴
  - 保持 CONTRIBUTING_AI.md 专注于协作规则
- **日期**: 2026-01-21
- **状态**: CONFIRMED
- **影响**: ROADMAP.md 模板需要包含阶段信息

### DECISION-005: Demo 阶段早期介入 CI/CD
- **等级**: B
- **角色**: [ARCH]
- **问题**: CI/CD 应该在哪个阶段建立？
- **决策**: Demo 阶段就应该建立 CI/CD
- **理由**:
  - 早期建立 CI/CD 可以避免后期迁移成本
  - 自动化测试和部署有助于快速迭代
  - 符合现代开发最佳实践
- **日期**: 2026-01-21
- **状态**: CONFIRMED
- **影响**: 更新 demo 阶段的 principles，添加"建立 CI/CD"

### DECISION-006: Production 阶段前确立性能规范和代码重构
- **等级**: A
- **角色**: [ARCH]
- **问题**: 性能规范和代码重构应该在什么时候进行？
- **决策**: 在进入 Production 阶段前就应该开始
- **理由**:
  - 量产前需要建立稳定的代码结构
  - 性能标准需要在规模化前定义
  - 全量代码 review 可以提前发现架构问题
- **日期**: 2026-01-21
- **状态**: CONFIRMED
- **影响**: 更新 production 阶段的 principles

### DECISION-007: 自动 Git 检查和初始化
- **等级**: B
- **角色**: [DEV]
- **问题**: 是否应该自动初始化 Git 仓库？
- **决策**: 在项目初始化时自动检查，可选自动初始化
- **理由**:
  - 确保项目从一开始就使用版本控制
  - 巩固后续对话时坚持 Git 同步的习惯
  - 提供 `--no-git` 选项给不需要的用户
- **日期**: 2026-01-21
- **状态**: CONFIRMED
- **影响**: 新增 git_utils.py 模块，集成到项目初始化流程

### DECISION-008: 多开发者支持架构设计
- **发起人**: user
- **参与者**: user, AI
- **等级**: A
- **角色**: [ARCH]
- **问题**: 如何支持多个开发者/多个 Agent 协同开发？
- **选项**:
  - A: 每个开发者独立 CONTEXT.md，无全局视图
  - B: 保持单一 CONTEXT.md，添加开发者标记
  - C: 开发者独立 CONTEXT.md + 全局聚合视图（选择）
- **决策**: 采用方案 C - 开发者独立上下文 + 全局自动聚合
- **理由**:
  - **隔离性**: 各开发者维护自己的工作上下文，避免冲突
  - **全局视图**: 自动聚合提供项目整体状态，便于协调
  - **可扩展**: 易于添加新开发者，无需重构现有结构
  - **向后兼容**: 单开发者项目可平滑迁移到多开发者模式
- **技术方案**:
  - 开发者身份识别: Git 用户名自动识别（`git config user.name`）
  - 目录结构: `docs/developers/{developer}/CONTEXT.md`
  - 全局聚合: `docs/CONTEXT.md` 自动从各开发者上下文生成（只读）
  - 协作管理: 新增 `docs/developers/COLLABORATION.md` 记录依赖和交接
  - CHANGELOG.md: 保持全局统一（版本历史应该统一）
  - DECISIONS.md: 添加 `initiator` 和 `participants` 字段标记参与者
  - Git commit: 不额外标记，使用 Git 原生 author 信息
- **日期**: 2026-02-10
- **状态**: CONFIRMED
- **影响**: 
  - 新增 `src/vibecollab/developer.py` 模块（DeveloperManager, ContextAggregator）
  - 扩展 `project.yaml` schema（multi_developer 配置）
  - 新增 CLI 命令（`vibecollab dev *`）
  - 更新项目初始化逻辑（支持 `--multi-dev` 选项）
  - 版本升级到 v0.5.0

### DECISION-009: Borrow architectural patterns for protocol maturity
- **发起人**: user
- **参与者**: user, AI
- **等级**: A
- **角色**: [ARCH]
- **问题**: How to improve VibeCollab's protocol maturity and structural robustness?
- **选项**:
  - A: Full-scale architecture overhaul (high risk, high disruption)
  - B: Selective pattern borrowing with gradual introduction (chosen)
  - C: Minimal changes, only fix bugs
- **决策**: Direction B — Selectively adopt 10 proven architectural patterns, mapped to VibeCollab-native concepts, introduced incrementally with unit tests per iteration.
- **理由**:
  - Incremental approach reduces risk and allows validation at each step
  - Patterns are renamed and adapted to VibeCollab's project-centric philosophy
  - Each iteration is independently testable and committable
  - Avoids coupling to any external framework's proprietary terminology
- **Borrowed patterns**:
  1. State separation (mutable JSON + immutable JSONL) → multi-file split (High)
  2. Append-only event log → EventLog events.jsonl (High)
  3. Validate-solidify-rollback loop → Task solidify check (High)
  4. Atomic write → Python atomic_write (Medium)
  5. Content-addressable hashing → SHA-256 fingerprint (Medium)
  6. Signal extraction → Project health signals (Medium)
  7. Experience reuse patterns → Project Pattern / Template (Medium)
  8. Blast radius control → Task max change scope (Medium)
  9. Defense-in-depth safety → Multi-level validation guards (Low)
  10. Asset sharing protocol → Cross-project template sharing (Low)
- **日期**: 2026-02-24
- **状态**: CONFIRMED
- **影响**:
  - Iteration 1: EventLog module (event_log.py) — COMPLETED
  - Iteration 2: TaskManager module (task_manager.py) — COMPLETED
  - Iteration 3: PatternEngine module (pattern_engine.py) — COMPLETED
  - Iteration 4: Health Signals (health.py) + Agent Executor (agent_executor.py) — COMPLETED

### DECISION-010: 三模式 AI 架构 (IDE + CLI + Agent)
- **发起人**: user
- **参与者**: user, AI
- **等级**: A
- **角色**: [ARCH]
- **问题**: VibeCollab 应如何支持不同的 AI 交互场景？
- **选项**:
  - A: 仅保留 IDE 对话模式 (现有)
  - B: 添加 CLI 人机交互 + IDE (两模式)
  - C: IDE + CLI 人机交互 + Agent 自主 (三模式，选择)
- **决策**: 采用方案 C — 三模式共存
- **理由**:
  - **IDE 对话**: 开发者在 Cursor/CodeBuddy 中直接协作，读 CONTRIBUTING_AI.md (已有)
  - **CLI 人机交互**: `vibecollab ai ask/chat`，无需 IDE 也能与 AI 协作
  - **Agent 自主**: `vibecollab ai agent run/serve`，服务器部署，配 API Key 自驱开发
  - 三模式满足从本地开发到服务器部署的完整场景
  - Agent 模式内置安全门控 (PID锁, pending-solidify, 最大周期, 自适应退避, 断路器)
- **技术方案**:
  - 新增 `cli_ai.py` 作为命令层，注册到主 CLI (`vibecollab ai`)
  - 复用 `LLMClient` + `build_project_context()` + `TaskManager` + `EventLog`
  - Agent serve 循环: Plan→Execute→Solidify，每周期独立
  - 环境变量配置: `VIBECOLLAB_AGENT_MAX_CYCLES`, `VIBECOLLAB_AGENT_*`
- **日期**: 2026-02-24
- **状态**: CONFIRMED
- **影响**:
  - 新增 `src/vibecollab/cli_ai.py` (870+ 行)
  - 新增 `tests/test_cli_ai.py` (32 tests)
  - 版本升级到 v0.5.8

### DECISION-011: Pattern Engine 架构 (Manifest 驱动模板引擎)
- **发起人**: user
- **参与者**: user, AI
- **等级**: A
- **角色**: [ARCH]
- **问题**: 如何替换 generator.py 中 27 个硬编码的 `_add_*()` 方法，实现可维护、可扩展的文档生成？
- **选项**:
  - A: 保持硬编码 Python 方法，逐步优化
  - B: Jinja2 模板 + manifest.yaml 声明式引擎 (选择)
  - C: 纯 Markdown 拼接，不用模板引擎
- **决策**: 采用方案 B — Manifest 驱动的 Jinja2 模板引擎 + 本地覆盖机制
- **理由**:
  - **可维护性**: 每个章节独立 `.md.j2` 模板，修改不影响其他章节
  - **声明式控制**: `manifest.yaml` 定义章节顺序、条件、模板映射，非代码即配置
  - **可扩展性**: Template Overlay 允许用户在 `.vibecollab/patterns/` 自定义模板和 manifest
  - **代码精简**: generator.py 从 1713 行减至 83 行，降低维护成本
  - **条件语法**: 支持 `config.x.enabled|true` 默认值语法，比硬编码 if/else 更灵活
- **技术方案**:
  - `PatternEngine`: Jinja2 Environment + ChoiceLoader (本地优先 → 内置回退)
  - `manifest.yaml`: 27 个 section 定义 (id, template, condition, chapter_title)
  - `_merge_manifests()`: 支持 override/insert(after)/exclude 三种合并操作
  - `_evaluate_condition()`: 支持 `|default` 语法的条件求值
  - 27 个 `.md.j2` 模板文件 + `DEFAULT_STAGES` 内置阶段定义
- **日期**: 2026-02-24
- **状态**: CONFIRMED
- **影响**:
  - `src/vibecollab/pattern_engine.py` 增强 (~290 行)
  - `src/vibecollab/generator.py` 精简 (1713 → 83 行)
  - `tests/test_pattern_engine.py` (40 tests)
  - 新增 `Jinja2>=3.0` 依赖
  - 新增 `src/vibecollab/patterns/` 目录 (27 模板 + manifest.yaml)

### DECISION-012: 砍掉 Web UI，转向 Insight 沉淀系统
- **发起人**: user
- **参与者**: user, AI
- **等级**: S
- **角色**: [ARCH] [PM]
- **问题**: v0.7.0 应该做什么？Web UI 还是沉淀系统？
- **选项**:
  - A: v0.7.0 做 Web UI（项目状态可视化、冲突图谱、实时监控）
  - B: 砍掉 Web UI，v0.7.0 做 Insight 沉淀系统（选择）
- **决策**: 砍掉 Web UI，v0.7.0 全力做 Insight 沉淀系统
- **理由**:
  - Web UI 不是 VibeCollab 的核心竞争力，投入产出比低
  - 沉淀系统直接增强 AI 协作质量，是核心差异化能力
  - 开发中成功的步骤和经验应可被固定化、复用、跨 Developer 共享
  - 未来沉淀不仅是 YAML 知识，还可关联实际工具/脚本/模板（Artifact），并可跨项目复用
- **核心架构：本体与注册表分离**:
  - **Insight 本体** (`INS-xxx.yaml`): 可移植的知识包，包含 title/summary/tags/category/body/artifacts/origin/fingerprint
  - **Registry 注册表** (`registry.yaml`): 项目级使用状态，包含 weight/used_count/last_used_at/active + 衰减设置
  - 本体是**跨项目可复用**的纯知识描述；注册表记录**本项目**的使用权重和生命周期
  - 存储路径: `.vibecollab/insights/INS-xxx.yaml` + `.vibecollab/insights/registry.yaml`
- **Tag 驱动的 Developer 描述**:
  - Developer 使用开放式 Tag 体系描述（替代枚举字段），存于 `.metadata.yaml`
  - 特定 Tag 可影响决策行为（如 `prefers:conservative` 影响风险评估）
  - Developer 可记录 contributed（创造的 Insight）和 bookmarks（收藏的 Insight）
- **搜索与溯源**:
  - Tag 搜索: Jaccard 相似度 × 注册表权重排序
  - Category 搜索: 精确匹配 + 权重排序
  - 溯源链: `origin.derived_from` 追踪派生关系，`get_derived_tree()` 构建上下游关系
  - **自描述溯源协议**: origin.source 结构不依赖项目内部 ID 体系
    - `context`: 创建背景自然语言描述
    - `source.description`: 来源的自描述（必填当 source 存在时），跨项目可读
    - `source.ref`: 来源项目内部 ID（降级为可选 hint）
    - `source.url`: 外部可访问链接（可选）
    - `source.project`: 来源项目名（可选）
- **权重衰减机制**:
  - `decay_rate` × 周期衰减，`use_reward` 使用奖励，`deactivate_threshold` 自动停用
  - 生命周期状态（weight/used_count/active）完全属于项目级注册表，不属于沉淀本体
- **一致性校验**（5 项全量检查）:
  - 注册表 ↔ 文件双向一致性
  - `derived_from` 引用完整性
  - Developer metadata 引用完整性
  - SHA-256 内容指纹校验
  - 所有 CRUD 操作自动记录 EventLog 审计事件
- **设计原则**:
  - 面向协作沉淀固化，而非 Agent 自进化
  - Tag 驱动的开放式描述，而非僵硬枚举字段
  - 融合 VibeCollab 自有符号系统（决策分级 S/A/B/C、SHA-256 指纹、EventLog 审计），不照搬外部术语
  - Insight 本体极简可移植，未来可抽象为包通过包管理注册到项目
- **日期**: 2026-02-25
- **状态**: CONFIRMED
- **影响**:
  - ROADMAP.md 更新：v0.7.0 目标变更
  - `schema/insight.schema.yaml` — Insight 本体 + Registry + Developer Tag 三部分 Schema ✅
  - `src/vibecollab/insight_manager.py` — 核心模块（CRUD/Registry/搜索/溯源/一致性校验）✅
  - `tests/test_insight_manager.py` — 62 单元测试 ✅
  - `tests/test_developer.py` — developer.py 全覆盖，88 单元测试（含 Tag 扩展）✅
  - Developer metadata 扩展 — tags/contributed/bookmarks CRUD ✅
  - `src/vibecollab/cli_insight.py` — CLI 命令组 (list/show/add/search/use/decay/check/delete) ✅
  - `tests/test_cli_insight.py` — 21 单元测试 ✅
  - 一致性校验集成到 `vibecollab check --insights` ✅
  - 跨 Developer 共享 + 溯源 CLI 可视化（bookmark/unbookmark/trace/who/stats）✅
  - InsightManager 扩展: get_full_trace / get_insight_developers / get_cross_developer_stats ✅

### DECISION-013: AI Agent 接入引导与行动建议系统
- **发起人**: user
- **参与者**: user, AI
- **等级**: A
- **角色**: [ARCH]
- **问题**: AI Agent 接入项目后如何确保理解项目全貌？修改文件后如何知道下一步做什么？
- **选项**:
  - A: 仅依赖 CONTRIBUTING_AI.md 文档（现状，被动）
  - B: 新增 onboard + next 命令实现主动引导（选择）
- **决策**: 新增 `vibecollab onboard` 和 `vibecollab next` 两个核心命令
- **理由**:
  - **onboard**: 解决"AI 不知道从哪开始"问题，提供项目概况/进度/决策/待办/应读文件
  - **next**: 解决"改了文件不知道下一步"问题，基于 git diff + mtime + linked_groups 生成行动建议
  - 从被动诊断（check 告诉你哪里错了）进化为主动引导（onboard/next 告诉你该做什么）
  - 同时增强文档一致性检查：linked_groups 三级检查（local_mtime/git_commit/release）
- **日期**: 2026-02-25
- **状态**: CONFIRMED
- **影响**:
  - 新增 `src/vibecollab/cli_guide.py` (~570 行)
  - 新增 `tests/test_cli_guide.py` (29 tests)
  - `protocol_checker.py` 增强: _check_document_consistency() + 三级检查方法
  - `project.yaml` 新增 `documentation.consistency` 配置块
  - update_threshold_hours 从 24h → 15min

---

### DECISION-014: Task-Insight 自动关联系统
- **发起人**: user
- **参与者**: user, AI
- **等级**: A
- **角色**: [ARCH]
- **问题**: Insight 沉淀与 Task 系统之间仅有元数据标注的间接关联，如何建立直接的知识-任务链接？
- **选项**:
  - A: 保持间接关联（仅 origin.source_type="task" 元数据）
  - B: Task 创建时自动搜索关联 Insight，存入 metadata（选择）
  - C: 全双向绑定（Insight 反向引用 Task）
- **决策**: B — 单向自动关联（Task → Insight）
- **理由**:
  - 零配置：InsightManager 可选注入，无 InsightManager 时自动退化
  - 低侵入：仅在 create_task() 追加 metadata，不改变返回类型和现有 API
  - 高价值：Agent 创建 Task 时自动获得知识上下文，减少重复劳动
  - 从 feature/description 提取关键词 + Jaccard × weight 匹配，复用已有搜索逻辑
- **日期**: 2026-02-25
- **状态**: CONFIRMED
- **影响**:
  - `task_manager.py` 增强: insight_manager 参数 + _find_related_insights() + suggest_insights()
  - 新增 `src/vibecollab/cli_task.py` (task create/list/show/suggest)
  - 新增 `tests/test_task_insight_integration.py` (28 tests)
  - 完全向后兼容

---

### DECISION-015: 砍掉自举能力(v0.9.2)和 Agent 增强(v0.10.1)，聚焦 MCP + 发布
- **发起人**: user
- **参与者**: user, AI
- **等级**: S
- **角色**: [PM]
- **问题**: v0.9.2 自举能力和 v0.10.1 Agent 增强是否值得继续投入？v0.10 应该做什么？
- **选项**:
  - A: 按原计划推进 v0.9.2 自举 → v0.10.0 无监督 → v0.10.1 Agent
  - B: 砍掉自举和 Agent，MCP 完成后直接进入发布准备（选择）
  - C: 只砍 Agent，保留自举
- **决策**: B — 砍掉 v0.9.2 和 v0.10.1，v0.10.0 改为发布准备（文档/Wiki/README/PyPI）
- **理由**:
  - `bootstrap` 价值不足：已有手写 CONTRIBUTING_AI.md (1488行)，自动生成会覆盖且质量更差
  - `ContextBuilder` 重构可在 MCP 开发中按需进行，不需要单列版本
  - Agent 自建能力与 MCP + 外部 IDE (Cline/Cursor/CodeBuddy) 路线冲突，`vibecollab ai` 已在 DECISION-012 中标记 experimental 冻结
  - 无监督运行（Git Hook/CI/CD）降为未来规划，优先级低于产品发布
  - v0.10.0 聚焦文档完善 + PyPI 正式发布，是走向 v1.0 的关键步骤
- **日期**: 2026-02-27
- **状态**: CONFIRMED
- **影响**:
  - ROADMAP 版本链简化为: v0.9.0(语义检索) → v0.9.1(MCP) → v0.10.0(发布准备)
  - v0.9.2 自举、v0.10.1 Agent 标记 ❌ 已砍掉
  - 原 v0.10.0 无监督运行能力降入"未来规划"
  - v1.0.0 前置条件简化

---

### DECISION-016: v0.9.3 优先接通 Task/EventLog 到核心工作流
- **发起人**: user
- **参与者**: user, AI
- **等级**: S
- **角色**: [PM, ARCH]
- **问题**: TaskManager（53 tests）和 EventLog（23 tests）已精心实现，但与用户日常工作流完全脱节。tasks.json 为空，events.jsonl 仅有 Insight 操作事件。onboard/next/check 三个核心命令均不读取 Task/EventLog 数据。HealthExtractor 已实现但未接入 CLI。v0.9.3/v0.9.4 应该做什么？
- **选项**:
  - A: 接受现状 — Task/EventLog 作为底层 API 存在，等用户手动使用
  - B: 接通核心工作流 — onboard 注入 Task 概览、next 基于 Task 推荐、MCP 暴露 task_create/transition、CLI 补齐 transition/solidify/rollback（选择）
  - C: 砍掉 TaskManager — 代码已验证，但用户不用就是废代码，不如删掉降低维护成本
- **决策**: B — v0.9.3 优先将 Task/EventLog 接通到核心工作流，Insight 质量推到 v0.9.4
- **理由**:
  - TaskManager/EventLog 设计良好、测试充分，问题不是代码质量而是接入缺失
  - onboard/next 是用户高频使用的命令，注入 Task/EventLog 数据能让用户感知到这些模块的价值
  - MCP 暴露 task_create/transition 让 AI IDE 能自动管理任务，形成完整闭环
  - CLI 缺少 transition/solidify/rollback 导致用户无法手动操作任务状态
  - health 命令已接入 HealthExtractor，但 onboard/check 缺少 EventLog 可见性
  - Insight 质量（去重/关联图谱/跨项目）优先级低于核心工作流打通
- **日期**: 2026-02-27
- **状态**: CONFIRMED
- **影响**:
  - v0.9.3 从 "Insight 质量与生命周期" 改为 "Task/EventLog 核心工作流接通"
  - v0.9.4 新增 "Insight 质量与生命周期"
  - Task CLI 补齐 transition/solidify/rollback 三个命令
  - onboard 注入活跃 Task 概览
  - next 基于 Task 状态推荐行动
  - MCP 新增 task_create / task_transition Tool
  - EventLog 数据在 onboard 中可见

---
*决策记录格式见 CONTRIBUTING_AI.md*
