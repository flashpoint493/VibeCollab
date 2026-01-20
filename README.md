# LLMTxt

[![PyPI version](https://badge.fury.io/py/llmtxt.svg)](https://badge.fury.io/py/llmtxt)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**从 YAML 配置生成标准化的 AI 协作规则文档 (llm.txt)**

将 Vibe Development 哲学和 LLM 协作协议抽象为可配置、可复用的框架，支持快速在不同领域部署工程化的人机协作流程。

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

### 自定义配置后重新生成

```bash
# 编辑 project.yaml 后
llmtxt generate -c project.yaml -o llm.txt

# 验证配置
llmtxt validate -c project.yaml
```

---

## CLI 命令

```bash
# 查看帮助
llmtxt --help

# 初始化项目
llmtxt init -n <name> -d <domain> -o <output>

# 生成 llm.txt
llmtxt generate -c <config> -o <output>

# 验证配置
llmtxt validate -c <config>

# 列出支持的领域
llmtxt domains

# 列出可用模板
llmtxt templates

# 导出模板
llmtxt export-template -t <template> -o <output>
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
| 时机 | 提交时 | 功能完成时 |

---

## 支持的领域

| 领域 | 说明 | 特有配置 |
|------|------|---------|
| `generic` | 通用项目 | 基础配置 |
| `game` | 游戏开发 | GM 控制台、GDD 文档 |
| `web` | Web 应用 | API 文档、部署环境 |
| `data` | 数据工程 | ETL 管道、数据质量 |
| `mobile` | 移动应用 | 平台适配、发布流程 |
| `infra` | 基础设施 | IaC、监控告警 |

---

## 配置说明

### 项目配置结构 (`project.yaml`)

```yaml
# 项目基本信息
project:
  name: "MyProject"
  version: "v1.0"
  domain: "web"

# 核心理念
philosophy:
  vibe_development:
    enabled: true
    principles:
      - "AI 不是执行者，而是协作伙伴"
      - "不急于产出代码，先对齐理解"

# 职能角色
roles:
  - code: "DEV"
    name: "开发"
    focus: ["具体实现", "Bug修复"]
    triggers: ["开发", "实现"]
    is_gatekeeper: false

# 决策分级
decision_levels:
  - level: "S"
    name: "战略决策"
    scope: "整体方向"
    review:
      required: true
      mode: "sync"

# 测试体系
testing:
  unit_test:
    enabled: true
    framework: "jest"
    coverage_target: 0.8
  product_qa:
    enabled: true
    test_case_file: "docs/QA_TEST_CASES.md"

# 领域扩展
domain_extensions:
  web:
    api_docs:
      format: "openapi"
```

---

## 工作流程

### 开始新对话

```
继续项目开发。
请先读取 llm.txt 和 docs/CONTEXT.md 恢复上下文。
本次对话目标: {你的目标}
```

### 结束对话

```
请更新 docs/CONTEXT.md 保存当前进度。
总结本次对话的决策和产出。
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

## 扩展指南

### 添加新领域

1. 创建 `src/llmtxt/templates/domains/{domain}.extension.yaml`
2. 定义 `roles_override` 覆盖或添加角色
3. 定义 `domain_extensions.{domain}` 添加特有配置

### 自定义生成模板

修改 `src/llmtxt/generator.py` 中对应的 `_add_*` 方法。

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

## 符号系统

### 决策状态
- `PENDING` - 待确认
- `CONFIRMED` - 已确认
- `REVISED` - 已修订

### 任务状态
- `TODO` - 待开始
- `IN_PROGRESS` - 进行中
- `REVIEW` - 待审核
- `DONE` - 已完成

### 测试状态
- 🟢 通过
- 🟡 部分通过
- 🔴 未通过
- ⚪ 跳过

---

## License

MIT

---

*本框架源自游戏开发实践，抽象为通用的 AI 协作协议生成器。*
