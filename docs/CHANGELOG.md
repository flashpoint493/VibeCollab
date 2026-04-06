# Changelog Markdown template - renders docs/changelog.yaml to docs/CHANGELOG.md
# Project Changelog

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