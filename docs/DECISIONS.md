# VibeCollab 决策记录

## 待确认决策

(暂无)

## 已确认决策

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
  - 待完成：跨 Developer 共享 + 溯源 CLI 可视化、一致性校验集成到 `vibecollab check`

---
*决策记录格式见 CONTRIBUTING_AI.md*
