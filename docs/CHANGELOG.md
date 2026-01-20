# LLMTXTGenerator 变更日志

## [Unreleased]

### 2026-01-20 对话4: 文档同步
- **[DOC]** 更新 README 同步最新扩展机制
- 补充扩展机制章节：钩子、上下文类型
- 完善配置示例和项目结构说明

### 2026-01-20 对话3: 扩展机制重设计
- **[DESIGN]** 重新定义扩展机制：钩子 + 上下文注入 + 引用文档
- **[DESIGN]** 定义钩子触发点：dialogue/qa/dev/build/milestone
- **[DESIGN]** 定义上下文类型：reference/template/computed/file_list
- 新增 `schema/extension.schema.yaml` 扩展机制 Schema
- 重构三个领域扩展：game/web/data
- 本项目自身使用 llm.txt（元实现）

### 2026-01-20 对话2: Python 包重构
- **[FEAT]** 重构为标准 Python 包结构
- **[FEAT]** 添加 Click + Rich CLI 工具
- 命令：`llmtxt init/generate/validate/domains/templates`
- 添加 pytest 单元测试
- 准备 PyPI 发布

### 2026-01-20 对话1: 项目初始化
- **[ARCH]** 从游戏领域 llm.txt 抽象核心协作协议
- **[ARCH]** 设计 YAML Schema 配置驱动
- 分离 UnitTest 和 ProductQA 测试体系
- 创建 game/web/data 领域扩展模板

---

## [0.1.0] - 2026-01-20

初始版本，核心功能：
- YAML 配置生成 llm.txt
- 多领域扩展支持
- CLI 工具

---
