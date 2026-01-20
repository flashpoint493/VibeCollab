# LLMTXTGenerator 当前上下文

## 当前状态
- **阶段**: Phase 1 - 核心框架完成
- **进度**: 初始架构建立完成
- **下一步**: 测试生成器，完善领域扩展

## 本次对话目标
将游戏行业的 llm.txt 抽象成可复用的生成器框架

## 已完成事项
- [x] 分析原始 llm.txt 核心模块
- [x] 设计 YAML Schema (`schema/project.schema.yaml`)
- [x] 创建默认模板 (`templates/default.project.yaml`)
- [x] 实现生成器 (`generator/llm_txt_generator.py`)
- [x] 创建领域扩展 (game/web/data)
- [x] 创建项目初始化脚本 (`init_project.py`)
- [x] 初始化 Git 仓库

## 核心抽象

### 原始文档模块 → YAML 配置映射

| 原始章节 | 抽象为 | YAML 路径 |
|---------|--------|-----------|
| 核心理念 | philosophy | `philosophy.*` |
| 职能角色 | roles | `roles[]` |
| 决策分级 | decision_levels | `decision_levels[]` |
| 任务单元 | task_unit | `task_unit.*` |
| 对话流程 | dialogue_protocol | `dialogue_protocol.*` |
| Git工作流 | git_workflow | `git_workflow.*` |
| QA验收 | testing.product_qa | `testing.product_qa.*` |
| (新增)单元测试 | testing.unit_test | `testing.unit_test.*` |
| 里程碑 | milestone | `milestone.*` |
| 迭代管理 | iteration | `iteration.*` |
| 文档体系 | documentation | `documentation.*` |
| 符号系统 | symbology | `symbology.*` |
| 领域扩展 | domain_extensions | `domain_extensions.{domain}.*` |

## 下一步计划
1. 测试生成器是否正常工作
2. 完善 schema 的 JSON Schema 验证
3. 添加更多领域扩展 (mobile/infra)
4. 添加 CLI 更友好的交互

---
*最后更新: 2026-01-20*
