# LLMTXTGenerator 变更日志

## [0.1.0] - 2026-01-20

### Added
- 核心 YAML Schema 设计 (`schema/project.schema.yaml`)
- 默认项目模板 (`templates/default.project.yaml`)
- Python 生成器 (`generator/llm_txt_generator.py`)
- 领域扩展模板:
  - `templates/domains/game.extension.yaml`
  - `templates/domains/web.extension.yaml`
  - `templates/domains/data.extension.yaml`
- 项目初始化脚本 (`init_project.py`)
- 文档体系初始化

### 核心抽象
- 从游戏领域 llm.txt 提取通用协作协议
- 建立 YAML 配置驱动的文档生成机制
- 分离 Unit Test 和 Product QA 两种测试体系
- 设计符号学标注系统 (symbology)

---
