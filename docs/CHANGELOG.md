# LLMTXTGenerator 变更日志

## 2026-01-20

### 对话5: 实现扩展钩子处理 [DEV]

**新增**:
- `src/llmtxt/extension.py` - 扩展处理器模块
  - `ExtensionProcessor` 类：钩子管理、条件评估、上下文解析
  - `Hook` / `Context` / `Extension` 数据类
  - 支持条件表达式：`files.exists()`, `project.has_feature()`, `project.domain ==`
  - 支持上下文类型：reference, template, file_list, computed
- `tests/test_extension.py` - 13 个单元测试

**修改**:
- `src/llmtxt/generator.py`
  - 集成 ExtensionProcessor
  - 新增 `_add_extension_sections()` 渲染扩展章节
  - `from_file()` 支持 project_root 参数
- `src/llmtxt/project.py`
  - 修复 `_merge_extension()` None 值处理
- `src/llmtxt/__init__.py`
  - 导出 ExtensionProcessor, Extension, Hook, Context

**测试**: 24 passed

---

### 对话4: 文档同步 [DOC]
- 更新 README 同步扩展机制设计

### 对话3: 扩展机制重设计 [DESIGN]
- 重新定义扩展 = 流程钩子 + 上下文注入
- 新增 extension.schema.yaml
- 重构 game/web/data 领域扩展

### 对话2: Python 包重构 [FEAT]
- 重构为标准包结构
- 添加 CLI (Click + Rich)
- 准备 PyPI 发布

### 对话1: 项目初始化 [ARCH]
- 从游戏 llm.txt 抽象核心协议
- 设计 YAML Schema
