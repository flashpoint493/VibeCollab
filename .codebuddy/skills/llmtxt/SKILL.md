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
3. 读取 docs/DECISIONS.md → 了解已确认决策
4. 运行 git log --oneline -10 → 了解最近进展
5. 确认用户本次对话目标
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
3. 如有新决策，更新 docs/DECISIONS.md
4. Git commit → 记录对话成果
```

## 重要协议

### 迭代建议管理协议

QA 测试中产生的迭代建议，必须经过 PM 评审：
- ✅ 纳入当前里程碑
- ⏳ 延后到下个里程碑
- ❌ 拒绝（不符合方向）
- 🔄 合并其他迭代

### 版本回顾协议

每次新版本规划前，必须回顾：
1. 测试表现（通过率、问题分布）
2. 用户体验反馈
3. 技术债务
4. 迭代建议池

### 构建打包协议

全量验收前必须完成：
```
[ ] 1. npm run build
[ ] 2. 测试打包产物
[ ] 3. 确认正常运行
[ ] 4. 更新操作说明
```

### 配置级迭代协议

仅修改配置、不改动代码逻辑的迭代，可快速执行：
- 无需 PM 审批
- 无需创建 TASK
- commit 使用 `[CONFIG]` 前缀

### QA 验收协议

功能完成后，AI 必须提供快速验收清单：

```markdown
## 🧪 快速验收

**启动**: `npm run dev`

**验收项**:
- [ ] 功能A: {操作} → {预期}

**快速回复**:
✅ 全部通过
或
⚠️ 问题: {描述}
```

## CLI 工具使用

```bash
# 初始化新项目（选择领域: generic/game/web/data）
llmtxt init -n "项目名" -d <domain> -o <output_dir>

# 从 YAML 配置生成 llm.txt
llmtxt generate -c project.yaml -o llm.txt

# 验证配置文件
llmtxt validate -c project.yaml

# 查看可用领域
llmtxt domains
```

## 职能角色定义

| 角色代号 | 职能 | 触发词 |
|---------|------|--------|
| `[DESIGN]` | 产品设计 | "设计"、"需求"、"产品" |
| `[ARCH]` | 架构 | "架构"、"重构"、"模块" |
| `[DEV]` | 开发 | "开发"、"实现"、"代码" |
| `[PM]` | 项目管理 | "规划"、"发布"、"里程碑" |
| `[QA]` | 产品质量保证 | "验收"、"体验测试" |
| `[TEST]` | 单元测试 | "单元测试"、"coverage" |

## Git 协作规范

### Commit 前缀

```
[DESIGN]   设计文档变更
[ARCH]     架构调整
[FEAT]     新功能
[FIX]      Bug修复
[CONFIG]   配置调整（不改逻辑）
[REFACTOR] 重构
[DOC]      文档更新
[TEST]     测试相关
[VIBE]     协作流程更新
```

## Prompt 工程最佳实践

### 不要说
- "帮我写一个XXX" (跳过思考)
- "直接给我代码" (跳过设计)

### 推荐说
- "我想和你讨论一下XXX的设计"
- "你觉得这个方案有什么问题"
- "我们先对齐一下理解，再动手"
- "这个决策你怎么看"

### 高价值引导词

| 场景 | 引导词 |
|-----|-------|
| 深入分析 | "请从{角色}视角分析" |
| 方案对比 | "给出2-3个方案并对比优劣" |
| 风险评估 | "这个方案最大的风险是什么" |
| 简化问题 | "MVP版本最少需要什么" |
| Vibe 对齐 | "你理解我的意图了吗" |

## 关键文件

| 文件 | 职责 | 更新时机 |
|-----|------|---------|
| `llm.txt` | 项目协作规则 | 协作方式演进时 |
| `docs/CONTEXT.md` | 当前开发上下文 | 每次对话结束 |
| `docs/CHANGELOG.md` | 变更日志 | 每次有效对话 |
| `docs/DECISIONS.md` | 决策记录 | S/A级决策后 |
| `docs/QA_TEST_CASES.md` | 测试用例 | 功能完成时 |
| `docs/ROADMAP.md` | 路线图+迭代建议 | 里程碑规划时 |
| `project.yaml` | 项目配置 | 配置变更时 |

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
