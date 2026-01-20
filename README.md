# LLMTXTGenerator

**从 YAML 配置生成标准化的 AI 协作规则文档 (llm.txt)**

将 Vibe Development 哲学和 LLM 协作协议抽象为可配置、可复用的框架，支持快速在不同领域部署工程化的人机协作流程。

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 初始化新项目

```bash
# 通用项目
python init_project.py -n "MyProject" -d generic -o ./my-project

# 游戏项目
python init_project.py -n "MyGame" -d game -o ./my-game

# Web 项目
python init_project.py -n "MyWebApp" -d web -o ./my-webapp

# 数据工程项目
python init_project.py -n "MyDataPipeline" -d data -o ./my-data
```

### 3. 生成的项目结构

```
my-project/
├── llm.txt                    # AI 协作规则文档
├── project.yaml               # 项目配置 (可编辑)
├── llm_txt_generator.py       # 生成器副本
└── docs/
    ├── CONTEXT.md             # 当前上下文 (每次对话更新)
    ├── DECISIONS.md           # 决策记录
    ├── CHANGELOG.md           # 变更日志
    ├── ROADMAP.md             # 路线图
    └── QA_TEST_CASES.md       # 测试用例
```

### 4. 自定义配置后重新生成

```bash
# 编辑 project.yaml 后
python llm_txt_generator.py -c project.yaml -o llm.txt
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

## 配置说明

### 项目配置结构 (`project.yaml`)

```yaml
# 项目基本信息
project:
  name: "MyProject"
  version: "v1.0"
  domain: "web"  # generic/game/web/data/mobile/infra

# 核心理念
philosophy:
  vibe_development:
    enabled: true
    principles: [...]
  decision_quality:
    target_rate: 0.9
    critical_tolerance: 0

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

# 里程碑
milestone:
  lifecycle:
    - phase: "feature_dev"
      description: "特性开发期"
    - phase: "bug_fix"
      description: "Bug 修复期"
    - phase: "acceptance"
      description: "里程碑验收"

# 领域扩展 (可选)
domain_extensions:
  web:
    api_docs:
      format: "openapi"
```

### 支持的领域

| 领域 | 说明 | 特有配置 |
|------|------|---------|
| `generic` | 通用项目 | 基础配置 |
| `game` | 游戏开发 | GM 控制台、GDD 文档 |
| `web` | Web 应用 | API 文档、部署环境 |
| `data` | 数据工程 | ETL 管道、数据质量 |

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

## 目录结构

```
LLMTXTGenerator/
├── init_project.py              # 项目初始化脚本
├── requirements.txt             # Python 依赖
├── schema/
│   └── project.schema.yaml      # YAML Schema 定义
├── generator/
│   └── llm_txt_generator.py     # 文档生成器
├── templates/
│   ├── default.project.yaml     # 默认项目模板
│   └── domains/
│       ├── game.extension.yaml  # 游戏领域扩展
│       ├── web.extension.yaml   # Web 领域扩展
│       └── data.extension.yaml  # 数据工程扩展
└── docs/
    ├── CONTEXT.md               # 本项目上下文
    └── CHANGELOG.md             # 本项目变更日志
```

---

## 扩展指南

### 添加新领域

1. 创建 `templates/domains/{domain}.extension.yaml`
2. 定义 `roles_override` 覆盖或添加角色
3. 定义 `domain_extensions.{domain}` 添加特有配置
4. 在 `init_project.py` 的 `DOMAINS` 列表中添加新领域

### 自定义生成模板

修改 `generator/llm_txt_generator.py` 中对应的 `_add_*` 方法。

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

### Bug 优先级
- `P0` - 崩溃/阻断
- `P1` - 功能异常
- `P2` - 体验问题
- `P3` - 优化建议

---

## License

MIT

---

*本框架源自游戏开发实践，抽象为通用的 AI 协作协议生成器。*
