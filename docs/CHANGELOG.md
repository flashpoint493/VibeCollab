# Changelog Markdown template - renders docs/changelog.yaml to docs/CHANGELOG.md
# Project Changelog

## [v0.12.3] - 2026-04-08

### Features
- **Step-by-Step Workflow Execution**: 单步执行和状态持久化
  - `vibecollab plan step <workflow> <index>` - 执行单个步骤
  - `vibecollab plan status <workflow>` - 查看执行状态
  - `vibecollab plan steps <workflow>` - 列出所有步骤及状态
  - `vibecollab plan reset <workflow>` - 重置执行状态
  - `vibecollab plan run <workflow> --interactive` - 交互式执行
  - `vibecollab plan run <workflow> --resume` - 从保存状态恢复
  - `vibecollab plan run <workflow> --from-step N --to-step M` - 范围执行
  - 状态自动持久化到 `.vibecollab/plan_state/<plan_name>.json`

### Implementation
- 新增 `StepState` / `PlanExecutionState` 数据类
- 新增 `StepStateManager` 状态持久化管理器
- 新增 `StepExecutor` 单步骤执行器
- 扩展 `PlanRunner` 支持单步、交互、范围、恢复执行模式

## [v0.12.1] - 2026-04-06

### Fixes
- 修复 Insight 指纹验证问题 (INS-038, INS-060)
- 修复代码格式问题 (ruff lint)
- 优化 GitHub Actions CI/CD 流程

## [v0.12.0] - 2026-04-06

### Features
- **YAML Data Layer Migration**: 完成文档层 Markdown → YAML Big-Bang 迁移
  - docs/changelog.yaml → docs/CHANGELOG.md 渲染
  - docs/context.yaml → docs/CONTEXT.md 渲染
  - docs/decisions.yaml → docs/DECISIONS.md 渲染
- **Role Directory Isolation**: 角色配置从 docs/roles/ 迁移到 .vibecollab/roles/
  - 实现角色目录与项目文档的物理隔离
  - 更新 CLI 和相关工具路径引用

### Changes
- 重构 src/vibecollab/cli/skill.py，简化技能管理逻辑
- 更新 MCP 工具实现，优化 IDE 适配器交互
- 增强 Insight 管理器，支持更多查询和导出功能

### Insights (New)
- INS-066: Role Directory Isolation 经验
- INS-065: YAML Docs Directory Isolation 经验
- INS-064: Tag-Based Insight Discovery
- INS-063: IDE Adapter Implementation Pattern

---
*This file is auto-generated from docs/changelog.yaml*