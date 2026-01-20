---
name: llmtxt
description: |
  This skill provides a standardized AI collaboration protocol (llm.txt) for project development.
  It should be used when: (1) initializing a new project that needs AI collaboration rules,
  (2) continuing development on a project with existing llm.txt, (3) the user mentions 
  "vibe development", "AI collaboration", "llm.txt", or wants structured human-AI pair programming.
  The skill enforces conversation lifecycle management, decision tracking, and git commit discipline.
---

# LLMTxt - AI 协作协议 Skill

## 概述

LLMTxt 提供标准化的 AI 协作开发规则，实现 **Vibe Development** 哲学：
- AI 不是执行者，而是**协作伙伴**
- 不急于产出代码，先**对齐理解**
- 每个决策都是**共同思考**的结果
- 对话本身就是**设计过程**的一部分

## 何时使用此 Skill

- 用户要求初始化新项目的 AI 协作规则
- 项目根目录存在 `llm.txt` 文件
- 用户提及 "vibe development"、"协作协议"、"llm.txt"
- 需要结构化的人机协作开发流程

## 核心工作流

### 1. 对话开始时（强制）

每次新对话开始，必须执行：

```
1. 读取 llm.txt → 了解协作规则
2. 读取 docs/CONTEXT.md → 恢复当前状态
3. 确认用户本次对话目标
```

### 2. 对话进行中

遵循决策分级制度：

| 等级 | 类型 | 影响范围 | 处理方式 |
|-----|------|---------|---------|
| **S** | 战略决策 | 协议设计、核心概念 | 必须人工确认 |
| **A** | 架构决策 | Schema结构、扩展机制 | 人工Review |
| **B** | 实现决策 | 具体实现方案 | 可快速确认 |
| **C** | 细节决策 | 命名、格式 | AI自主决策 |

### 3. 对话结束时（强制）

每次对话结束前，必须执行：

```
1. 更新 docs/CONTEXT.md → 保存进度
2. 更新 docs/CHANGELOG.md → 记录产出
3. Git commit → 记录对话成果
```

## CLI 工具使用

本 Skill 配套 Python CLI 工具 `llmtxt`：

```bash
# 初始化新项目（选择领域: generic/game/web/data）
llmtxt init -n "项目名" -d <domain> -o <output_dir>

# 从 YAML 配置生成 llm.txt
llmtxt generate -c project.yaml -o llm.txt

# 验证配置文件
llmtxt validate -c project.yaml

# 查看可用领域
llmtxt domains

# 查看可用模板
llmtxt templates
```

### 安装 CLI

```bash
pip install llmtxt
# 或从源码安装
pip install -e /path/to/LLMTXTGenerator
```

## 职能角色定义

在对话中根据任务自动切换角色视角：

| 角色代号 | 职能 | 触发词 |
|---------|------|--------|
| `[DESIGN]` | 协议设计 | "设计"、"协议"、"Schema" |
| `[ARCH]` | 架构 | "架构"、"重构"、"模块" |
| `[DEV]` | 开发 | "开发"、"实现"、"代码" |
| `[PM]` | 项目管理 | "规划"、"发布"、"里程碑" |
| `[QA]` | 质量保证 | "测试"、"验证" |

## Git 协作规范

### Commit 前缀

```
[DESIGN]   协议/Schema 设计变更
[ARCH]     架构调整
[FEAT]     新功能
[FIX]      Bug修复
[REFACTOR] 重构
[DOC]      文档更新
[TEST]     测试相关
```

## 关键文件

| 文件 | 职责 | 更新时机 |
|-----|------|---------|
| `llm.txt` | 项目协作规则 | 协作方式演进时 |
| `docs/CONTEXT.md` | 当前开发上下文 | 每次对话结束 |
| `docs/CHANGELOG.md` | 变更日志 | 每次有效对话 |
| `project.yaml` | 项目配置 | 配置变更时 |

## 扩展机制

扩展 = 流程钩子 + 上下文注入 + 引用文档

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

## 快速参考

### 开始新对话

```
继续项目开发。
请先读取 llm.txt 和 docs/CONTEXT.md 恢复上下文。
本次对话目标: {目标}
```

### 结束对话

```
请更新 CONTEXT.md 保存当前进度。
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
