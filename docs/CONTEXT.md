# VibeCollab 全局上下文

> ⚠️ **此文件自动生成，请勿手动编辑**
> 上次更新: 2026-02-28
> 聚合自: alice, ocarina

## 项目整体状态
- **版本**: v0.9.8 (PyPI 已发布)
- **上一版本**: v0.9.7 (功能迭代)
- **活跃开发者**: 2 (alice, ocarina)
- **测试**: 1345 passed, 89% 覆盖率
- **当前阶段**: v0.9.7 迭代，推进 v0.10.0 功能冻结

## 各开发者工作状态

### alice
- **上次更新**: 2026-02-25
- **活跃度**: 暂停（上次活跃于 v0.5.4）
- **已完成**: CLI 开发者切换功能 (TASK-DEV-004), switch 命令测试和文档 (TASK-DEV-005 ✅)
- **无遗留任务**

### ocarina
- **上次更新**: 2026-02-28
- **当前任务**: 无（v0.9.8 已发布 PyPI，后续小版本迭代至 v0.10.0）
- **最近完成**:
  - **Schema 驱动规则**：`ide_rules_summary.md.j2` + `get_rules_body()`，有 project.yaml 时用生成结果与 README/context 一致
  - **多平台 rules+skills**：ide_platforms 接入，`rules inject`/`setup` 支持 10 平台（cursor, cline, codebuddy, windsurf, claude, opencode, roo, agents, kiro, trae），vx 结构对齐
  - **协议检查**：`_check_ide_inject_consistency()`，canonical 与磁盘规则文件对比；CI 增加 `vibecollab check`（有 project.yaml 时）
  - `vibecollab rules inject`：Cursor/CodeBuddy/Cline + Cline 规则注入，skill.md 修正与 rules inject 步骤
  - onboard Windows GBK 编码修复、v0.9.7 Roadmap 格式引导（TASK-DEV-008）、TASK-DEV-006、v0.9.5 ROADMAP ↔ Task

## 活跃任务

无活跃任务。待提交：schema 驱动规则、ide_platforms、多平台 inject、protocol check IDE 一致性、CI、kiro/trae、CONTEXT/CHANGELOG/ROADMAP。

## 跨开发者协作
(详见 docs/developers/COLLABORATION.md)

## 全局技术债务
- cli.py (72%) 和 cli_insight.py (71%) 覆盖率仍待提升
- 外部 QA 验证 (Phase 11 TC-E2E-001~010) 待执行
- events.jsonl Windows 文件锁问题需排查

---
*此文件由多开发者上下文自动聚合生成*
