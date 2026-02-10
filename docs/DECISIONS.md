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

---
*决策记录格式见 CONTRIBUTING_AI.md*
