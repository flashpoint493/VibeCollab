# LLMTxt

[![PyPI version](https://badge.fury.io/py/llmtxt.svg)](https://badge.fury.io/py/llmtxt)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**从 YAML 配置生成标准化的 AI 协作规则文档 (llm.txt)**

将 Vibe Development 哲学和 LLM 协作协议抽象为可配置、可复用的框架，支持快速在不同领域部署工程化的人机协作流程。

> 本项目自身也使用 llm.txt 进行开发（元实现）

---

## 工作流程图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LLMTxt 使用流程                                    │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│  1. 安装 llmtxt   │
│  pip install     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     ┌─────────────────────────────────────────┐
│  2. 初始化项目    │     │  llmtxt init -n "项目" -d game -o ./    │
│                  │────▶│                                         │
│  选择领域模板     │     │  领域: generic | game | web | data      │
└────────┬─────────┘     └─────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────┐
│                        生成项目结构                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐   │
│  │  llm.txt    │  │project.yaml │  │        docs/            │   │
│  │  协作规则    │  │  配置文件    │  │ CONTEXT.md CHANGELOG.md │   │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘   │
└──────────────────────────┬───────────────────────────────────────┘
                           │
         ┌─────────────────┴─────────────────┐
         ▼                                   ▼
┌──────────────────┐               ┌──────────────────┐
│  3. 开始对话      │               │  3. 自定义配置    │
│  (与 AI 协作)     │               │  编辑 project.yaml│
└────────┬─────────┘               └────────┬─────────┘
         │                                   │
         ▼                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                        对话生命周期                               │
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐   │
│  │  对话开始    │───▶│  协作开发    │───▶│     对话结束        │   │
│  │             │    │             │    │                     │   │
│  │ • 读 llm.txt│    │ • 需求澄清   │    │ • 更新 CONTEXT.md   │   │
│  │ • 读 CONTEXT│    │ • 决策分级   │    │ • 更新 CHANGELOG    │   │
│  │ • 确认目标   │    │ • 代码实现   │    │ • git commit        │   │
│  └─────────────┘    └─────────────┘    └─────────────────────┘   │
│         │                  │                      │              │
│         └──────────────────┴──────────────────────┘              │
│                            │                                     │
│                    ┌───────┴───────┐                             │
│                    ▼               ▼                             │
│           ┌──────────────┐  ┌──────────────┐                     │
│           │ 功能完成时    │  │ 配置变更时    │                     │
│           │ QA 验收测试   │  │ 重新生成      │                     │
│           │              │  │ llm.txt      │                     │
│           └──────────────┘  └──────────────┘                     │
└──────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                        里程碑发布                                 │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  │
│  │ 全量 QA    │─▶│ 构建打包   │─▶│ 版本回顾   │─▶│  发布      │  │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 特性

- **完整协议覆盖**: 决策分级、迭代管理、QA验收、Prompt工程最佳实践
- **领域扩展**: 支持 game/web/data 等领域的定制扩展
- **钩子机制**: 在对话流程节点自动注入上下文
- **Cursor Skill**: 可作为 IDE Skill 使用，提供结构化协作流程
- **自举实现**: 本项目使用自身生成的 llm.txt 进行开发

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

# 游戏项目（含 GM 命令注入）
llmtxt init -n "MyGame" -d game -o ./my-game

# Web 项目（含 API 文档注入）
llmtxt init -n "MyWebApp" -d web -o ./my-webapp
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
    ├── ROADMAP.md             # 路线图 + 迭代建议池
    └── QA_TEST_CASES.md       # 产品QA测试用例
```

### 自定义后重新生成

```bash
# 编辑 project.yaml 后重新生成
llmtxt generate -c project.yaml -o llm.txt

# 验证配置
llmtxt validate -c project.yaml
```

---

## 生成的 llm.txt 包含章节

| 章节 | 说明 |
|------|------|
| 核心理念 | Vibe Development 哲学、决策质量观 |
| 职能角色定义 | 可自定义的角色体系 (DESIGN/ARCH/DEV/PM/QA/TEST) |
| 决策分级制度 | S/A/B/C 四级决策及 Review 要求 |
| 开发流程协议 | 对话开始/结束时的强制流程 |
| **需求澄清协议** | **模糊需求 → 结构化描述转化** |
| 迭代建议管理协议 | QA 建议 → PM 评审 → 纳入/延后/拒绝 |
| 版本回顾协议 | 里程碑验收后的回顾流程 |
| 构建打包协议 | 全量验收前的 CheckList |
| 配置级迭代协议 | 无需审批的快速配置修改 |
| QA 验收协议 | 测试用例要素、快速验收模板 |
| Git 协作规范 | 分支策略、Commit 前缀 |
| 测试体系 | Unit Test + Product QA 双轨 |
| 里程碑定义 | 生命周期、Bug 优先级 |
| Prompt 工程最佳实践 | 有效提问模板、高价值引导词 |
| 符号学标注系统 | 统一的状态/优先级符号 |
| 已确认决策汇总 | 项目决策记录表 |
| 文档迭代日志 | llm.txt 自身版本历史 |

---

## CLI 命令

```bash
llmtxt --help                              # 查看帮助
llmtxt --version                           # 查看版本
llmtxt init -n <name> -d <domain> -o <dir> # 初始化项目
llmtxt generate -c <config> -o <output>    # 生成 llm.txt
llmtxt validate -c <config>                # 验证配置
llmtxt domains                             # 列出支持的领域
llmtxt templates                           # 列出可用模板
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

> **扩展 = 流程钩子 + 上下文注入 + 引用文档**

```yaml
domain_extensions:
  game:
    hooks:
      - trigger: "qa.list_test_cases"
        action: "inject_context"
        context_id: "gm_commands"
        condition: "files.exists('docs/GM_COMMANDS.md')"
    
    contexts:
      gm_commands:
        type: "reference"
        source: "docs/GM_COMMANDS.md"
```

### 钩子触发点

| 触发点 | 时机 |
|-------|------|
| `dialogue.start` | 对话开始 |
| `dialogue.end` | 对话结束 |
| `qa.list_test_cases` | QA 列测试用例 |
| `dev.feature_complete` | 功能完成 |
| `build.pre` / `build.post` | 构建前后 |

### 上下文类型

| 类型 | 说明 |
|-----|------|
| `reference` | 引用外部文档 |
| `template` | 内联模板 |
| `computed` | 动态计算 |
| `file_list` | 文件列表 |

---

## Cursor Skill 使用

本项目包含 Cursor IDE Skill，位于 `.codebuddy/skills/llmtxt/`：

```bash
# 复制到你的项目
cp -r .codebuddy/skills/llmtxt your-project/.codebuddy/skills/

# 或解压 dist/llmtxt-skill.zip
```

Skill 会在对话中自动：
1. 读取 llm.txt 和 CONTEXT.md 恢复上下文
2. 遵循决策分级制度
3. 对话结束时更新文档并 git commit

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

## 项目结构

```
LLMTXTGenerator/
├── llm.txt                      # 本项目的协作规则（自举）
├── project.yaml                 # 本项目的配置
├── pyproject.toml               # 包配置
├── src/llmtxt/
│   ├── cli.py                   # CLI 命令
│   ├── generator.py             # 文档生成器
│   ├── extension.py             # 扩展处理器
│   ├── project.py               # 项目管理
│   ├── templates.py             # 模板管理
│   └── templates/
│       ├── default.project.yaml
│       └── domains/             # 领域扩展
├── schema/
│   ├── project.schema.yaml      # 项目配置 Schema
│   └── extension.schema.yaml    # 扩展机制 Schema
├── .codebuddy/skills/llmtxt/    # Cursor Skill
├── docs/
│   ├── CONTEXT.md
│   └── CHANGELOG.md
└── tests/
```

---

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 重新生成本项目的 llm.txt
python -c "from llmtxt import LLMTxtGenerator; import yaml; from pathlib import Path; \
  config = yaml.safe_load(open('project.yaml', encoding='utf-8')); \
  g = LLMTxtGenerator(config, Path('.')); \
  Path('llm.txt').write_text(g.generate(), encoding='utf-8')"
```

---

## License

MIT

---

*本框架源自游戏开发实践，用 llm.txt 来开发 llm.txt 生成器。*
