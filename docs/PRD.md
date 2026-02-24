# VibeCollab 产品需求文档 (PRD)

本文档记录项目的原始需求和需求变化历史。

## 需求列表

## REQ-001: 协议自检机制

**原始描述**:
> 我们使用协议时常常发现，有时候对话时会漏掉一些东西，比如没有记得提交git，没有记得及时同步某个对应文档.md。我觉得我们需要一个skill和底层功能支持，让使用本框架的agent自检一下是否有全量启动应有的协议，并且也在用户的触发词中加入。

**当前描述**:
> 实现协议自检机制，包括：
> 1. 协议检查器模块，检查 Git 协议、文档更新、对话流程协议
> 2. CLI 命令 `vibecollab check` 执行协议检查
> 3. 在 CONTRIBUTING_AI.md 中添加协议自检章节
> 4. 支持对话中通过触发词触发自检

**状态**: completed
**优先级**: high
**创建时间**: 2026-01-21
**更新时间**: 2026-01-21

**需求变化历史**:
- **2026-01-21**: 需求实现完成
  - 从: 原始需求描述
  - 到: 当前描述
  - 原因: 需求已实现，包括协议检查器、CLI 命令、文档章节和触发词支持

---

## REQ-002: PRD 文档管理

**原始描述**:
> 我们虽然是一个启发式对话，需求在对话中推进，不过我们目前没有一个记录原始需求和变化的 PRD.md。我认为项目需求也在随着对话变化和成长。

**当前描述**:
> 实现 PRD 文档管理系统，包括：
> 1. PRD 管理器模块，支持需求的创建、更新、状态管理
> 2. 需求变化历史跟踪
> 3. 项目初始化时自动创建 PRD.md 模板
> 4. 在 CONTRIBUTING_AI.md 中添加 PRD 管理章节
> 5. 支持对话中通过触发词管理 PRD

**状态**: completed
**优先级**: high
**创建时间**: 2026-01-21
**更新时间**: 2026-01-21

**需求变化历史**:
- **2026-01-21**: 需求实现完成
  - 从: 原始需求描述
  - 到: 当前描述
  - 原因: 需求已实现，包括 PRD 管理器、文档模板、文档章节和触发词支持

---

## REQ-003: 事件审计日志

**当前描述**:
> 实现 append-only JSONL 格式的事件日志系统，用于追踪项目所有操作：
> 1. `EventLog` 模块，支持 append + read_all
> 2. `Event` 数据类（event_type, summary, actor, payload, timestamp）
> 3. 持久化到 `.vibecollab/events.jsonl`
> 4. 支持自定义事件类型（TASK_CREATED, TASK_TRANSITIONED, DECISION, CUSTOM 等）

**状态**: completed
**优先级**: high
**创建时间**: 2026-02-24
**更新时间**: 2026-02-24

---

## REQ-004: 任务生命周期管理

**当前描述**:
> 实现任务状态机管理系统：
> 1. `TaskManager` 模块，支持 create/transition/list/get
> 2. 状态流转: IN_PROGRESS → REVIEW → DONE，支持 rollback
> 3. 变更范围控制（最大文件数/行数限制）
> 4. 所有状态变更自动记录到 EventLog

**状态**: completed
**优先级**: high
**创建时间**: 2026-02-24
**更新时间**: 2026-02-24

---

## REQ-005: LLM 客户端集成

**当前描述**:
> 实现 provider-agnostic 的 LLM 客户端：
> 1. `LLMClient` 模块，支持 OpenAI-compatible API 和 Anthropic Claude
> 2. 环境变量配置（`VIBECOLLAB_LLM_*`），零硬编码 API key
> 3. `build_project_context()` 自动组装项目上下文
> 4. 单轮 ask() + 多轮 chat() API

**状态**: completed
**优先级**: high
**创建时间**: 2026-02-24
**更新时间**: 2026-02-24

---

## REQ-006: 三模式 AI CLI

**当前描述**:
> 实现三种 AI 使用模式的 CLI 命令层：
> 1. `vibecollab ai ask/chat` — 人机交互模式
> 2. `vibecollab ai agent plan/run/serve/status` — Agent 自主模式
> 3. 安全门控: PID 单例锁、pending-solidify 检查、最大周期数、自适应退避、断路器、RSS 内存限制
> 4. 与 IDE 对话模式 (读 CONTRIBUTING_AI.md) 共存

**状态**: completed
**优先级**: high
**创建时间**: 2026-02-24
**更新时间**: 2026-02-24

---

## REQ-007: Pattern Engine (模板驱动文档生成)

**当前描述**:
> 实现 Jinja2 模板驱动的 CONTRIBUTING_AI.md 生成引擎，替代 27 个硬编码 Python 方法：
> 1. `PatternEngine` 模块，基于 `manifest.yaml` 声明式控制章节
> 2. 27 个 `.md.j2` 模板文件，每个章节独立可维护
> 3. Template Overlay 机制: 用户可在 `.vibecollab/patterns/` 自定义模板和 manifest
> 4. 条件求值支持 `|default` 语法，manifest 合并支持 override/insert/exclude
> 5. 移除 generator.py 中全部 legacy 代码 (1713 → 83 行)

**状态**: completed
**优先级**: high
**创建时间**: 2026-02-24
**更新时间**: 2026-02-24

---

## 需求统计

| 状态 | 数量 |
|------|------|
| draft | 0 |
| confirmed | 0 |
| in_progress | 0 |
| completed | 7 |
| cancelled | 0 |

---

*最后更新: 2026-02-24*
