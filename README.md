# LLMTxt

[![PyPI version](https://badge.fury.io/py/llmtxt.svg)](https://badge.fury.io/py/llmtxt)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**从 YAML 配置生成标准化的 AI 协作规则文档 (llm.txt)**

将 Vibe Development 哲学和 LLM 协作协议抽象为可配置、可复用的框架，支持快速在不同领域部署工程化的人机协作流程。

> 本项目自身也使用 llm.txt 进行开发（元实现）

---

## 安装

```bash
pip install llmtxt
```

或从源码安装：

```bash
git clone https://github.com/user/llmtxt.git
cd llmtxt
pip install -e .
```

---

## 快速开始

### 初始化新项目

```bash
# 通用项目
llmtxt init -n "MyProject" -d generic -o ./my-project

# 游戏项目
llmtxt init -n "MyGame" -d game -o ./my-game

# Web 项目
llmtxt init -n "MyWebApp" -d web -o ./my-webapp

# 数据工程项目
llmtxt init -n "MyDataPipeline" -d data -o ./my-data
```

### 生成的项目结构

```
my-project/
├── llm.txt                    # AI 协作规则文档
├── project.yaml               # 项目配置 (可编辑)
└── docs/
    ├── CONTEXT.md             # 当前上下文 (每次对话更新)
    ├── DECISIONS.md           # 决策记录
    ├── CHANGELOG.md           # 变更日志
    ├── ROADMAP.md             # 路线图
    └── QA_TEST_CASES.md       # 测试用例
```

### 自定义后重新生成

```bash
# 编辑 project.yaml 后重新生成
llmtxt generate -c project.yaml -o llm.txt

# 验证配置
llmtxt validate -c project.yaml
```

---

## CLI 命令

```bash
llmtxt --help                              # 查看帮助
llmtxt init -n <name> -d <domain> -o <dir> # 初始化项目
llmtxt generate -c <config> -o <output>    # 生成 llm.txt
llmtxt validate -c <config>                # 验证配置
llmtxt domains                             # 列出支持的领域
llmtxt templates                           # 列出可用模板
llmtxt export-template -t <name> -o <file> # 导出模板
```

---

## 核心概念

### Vibe Development 哲学

> **最珍贵的是对话过程本身，不追求直接出结果，而是步步为营共同规划。**

- AI 不是执行者，而是**协作伙伴**
- 不急于产出代码，先**对齐理解**
- 每个决策都是**共同思考**的结果
- 对话本身就是**设计过程**的一部分

### 决策分级制度

| 等级 | 类型 | 影响范围 | Review 要求 |
|-----|------|---------|------------|
| **S** | 战略决策 | 整体方向 | 必须人工确认 |
| **A** | 架构决策 | 系统设计 | 人工 Review |
| **B** | 实现决策 | 具体方案 | 可快速确认 |
| **C** | 细节决策 | 参数命名 | AI 自主决策 |

### 双轨测试体系

| 维度 | Unit Test | Product QA |
|------|-----------|------------|
| 视角 | 开发者 | 用户 |
| 目标 | 代码正确性 | 功能完整性 |
| 粒度 | 函数/模块级 | 功能/流程级 |
| 执行 | 自动化 | 可自动+人工 |

---

## 扩展机制

### 扩展的本质

> **扩展 = 流程钩子 + 上下文注入 + 引用文档**

扩展不是静态配置，而是在特定流程节点注入上下文：

```yaml
hooks:
  # QA 列测试用例时，自动注入 GM 命令
  - trigger: "qa.list_test_cases"
    action: "inject_context"
    context_id: "gm_commands"
    condition: "files.exists('docs/GM_COMMANDS.md')"

contexts:
  gm_commands:
    type: "reference"              # 引用外部文档
    source: "docs/GM_COMMANDS.md"  # 避免扩展膨胀
```

### 钩子触发点

| 触发点 | 时机 | 用途 |
|-------|------|------|
| `dialogue.start` | 对话开始 | 注入领域上下文 |
| `dialogue.end` | 对话结束 | 额外更新文件 |
| `qa.list_test_cases` | QA 列测试用例 | 注入测试辅助工具 |
| `dev.feature_complete` | 功能完成 | 提供验收模板 |
| `build.pre` | 构建前 | 检查清单 |
| `build.post` | 构建后 | 部署指引 |

### 上下文类型

| 类型 | 说明 | 适用场景 |
|-----|------|---------|
| `reference` | 引用外部文档 | 内容多时，避免膨胀 |
| `template` | 内联模板 | 内容短，直接嵌入 |
| `computed` | 动态计算 | 需要运行时数据 |
| `file_list` | 文件列表 | 列出匹配的文件 |

---

## 支持的领域

| 领域 | 说明 | 扩展内容 |
|------|------|---------|
| `generic` | 通用项目 | 基础配置 |
| `game` | 游戏开发 | GM 命令注入、测试模板 |
| `web` | Web 应用 | API 文档注入、部署指南 |
| `data` | 数据工程 | 数据质量检查、管道清单 |
| `mobile` | 移动应用 | (规划中) |
| `infra` | 基础设施 | (规划中) |

---

## 配置结构

### 项目配置 (`project.yaml`)

```yaml
project:
  name: "MyProject"
  version: "v1.0"
  domain: "web"

philosophy:
  vibe_development:
    enabled: true
    principles:
      - "AI 不是执行者，而是协作伙伴"

roles:
  - code: "DEV"
    name: "开发"
    focus: ["实现", "Bug修复"]
    is_gatekeeper: false

decision_levels:
  - level: "S"
    name: "战略决策"
    review:
      required: true
      mode: "sync"

testing:
  unit_test:
    enabled: true
    framework: "jest"
    coverage_target: 0.8
  product_qa:
    enabled: true
    test_case_file: "docs/QA_TEST_CASES.md"
```

### 领域扩展 (`domains/*.extension.yaml`)

```yaml
roles_override:
  - code: "DESIGN"
    name: "游戏策划"
    focus: ["玩法", "体验", "平衡"]

domain_extensions:
  game:
    hooks:
      - trigger: "qa.list_test_cases"
        action: "inject_context"
        context_id: "gm_commands"
    
    contexts:
      gm_commands:
        type: "reference"
        source: "docs/GM_COMMANDS.md"
    
    additional_files:
      - path: "docs/GM_COMMANDS.md"
        purpose: "GM 控制台命令"
```

---

## 工作流程

### 开始新对话

```
继续项目开发。
请先读取 llm.txt 和 docs/CONTEXT.md 恢复上下文。
本次对话目标: {你的目标}
```

### 结束对话（必须）

```
请更新 docs/CONTEXT.md 保存当前进度。
更新 docs/CHANGELOG.md 记录产出。
然后 git commit 记录本次对话。
```

### Vibe Check

```
在继续之前，确认一下：
- 我们对齐理解了吗？
- 这个方向对吗？
- 有什么我没考虑到的？
```

---

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black src tests
ruff check src tests
```

---

## 项目结构

```
LLMTXTGenerator/
├── llm.txt                      # 本项目的协作规则（元实现）
├── pyproject.toml               # 包配置
├── src/llmtxt/
│   ├── cli.py                   # CLI 命令
│   ├── generator.py             # 文档生成器
│   ├── project.py               # 项目管理
│   ├── templates.py             # 模板管理
│   └── templates/
│       ├── default.project.yaml
│       └── domains/             # 领域扩展
├── schema/
│   ├── project.schema.yaml      # 项目配置 Schema
│   └── extension.schema.yaml    # 扩展机制 Schema
├── docs/
│   ├── CONTEXT.md               # 当前开发上下文
│   └── CHANGELOG.md             # 变更日志
└── tests/
```

---

## License

MIT

---

*本框架源自游戏开发实践，用 llm.txt 来开发 llm.txt 生成器。*
