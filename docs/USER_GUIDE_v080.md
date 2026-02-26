# VibeCollab v0.8.0 - 用户获得的价值

## 前言：你作为开发者能获得什么？

使用 VibeCollab v0.8.0 开发项目，你将获得一套**结构化的 AI 协作框架**，它不是简单的工具，而是一个**开发方法论 + 自动化系统**的组合。

---

## 📦 一开箱即用的 AI 协作协议

### 1.1 自动生成的 `CONTRIBUTING_AI.md`

你只需要写一个 `project.yaml`，VibeCollab 会自动生成完整的 AI 协作规则文档：

**命令**：
```bash
vibecollab generate -c project.yaml
```

**你得到什么**：
- 一份 20+ 页的 AI 协作规则文档
- 包含项目特定的配置
- 所有 AI 需要知道的规则都在这里

**具体内容**：
```markdown
# CONTRIBUTING_AI.md

## 核心理念
- Vibe Development 哲学
- 决策质量观
- 对话驱动开发

## 职能角色定义
- DESIGN（协议设计）
- ARCH（架构）
- DEV（开发）
- PM（项目管理）
- QA（产品质量保证）

## 决策分级制度
- S 级：战略决策（必须人工确认）
- A 级：架构决策（人工 Review）
- B 级：实现决策（快速确认）
- C 级：细节决策（AI 自主）

## 任务单元管理
- 对话驱动的任务单元
- 状态流转（TODO → IN_PROGRESS → REVIEW → DONE）
- 依赖管理

## 对话流程协议
- 开始新对话：读取 CONTEXT.md + CONTRIBUTING_AI.md
- 结束对话：更新 CONTEXT.md + CHANGELOG.md + git commit
- Vibe Check：确认对齐理解

## ...（还有 20+ 章节）
```

**价值**：
- ✅ 不用从头写 AI 提示词
- ✅ 所有 AI 都遵循统一的协作规则
- ✅ 新成员（人类或 AI）快速接入

---

## 🎯 二三模式 AI CLI

### 2.1 `vibecollab ai ask` - 单次问答

**场景**：快速问一个问题

```bash
vibecollab ai ask "如何设计用户认证系统？"
```

**你得到什么**：
- AI 自动注入项目上下文
- 基于项目配置的回答
- 不需要手动复制粘贴上下文

**对比**：

| 方式 | 操作量 | 上下文质量 |
|------|--------|-----------|
| 直接用 ChatGPT | 手动复制粘贴项目信息 | 容易遗漏 |
| vibecollab ai ask | 一条命令 | 自动注入完整上下文 |

### 2.2 `vibecollab ai chat` - 持续对话

**场景**：多轮讨论一个功能

```bash
vibecollab ai chat
```

**你得到什么**：
- 多轮对话，保持上下文
- 每轮对话都注入项目配置
- 对话结束自动更新文档

**示例对话流**：

```bash
$ vibecollab ai chat

> 我要实现用户登录功能

[AI] 好的，这是实现方案...

> 那用 JWT 还是 Session？

[AI] 建议使用 JWT，因为...

> 好的，开始实现

[AI] 正在生成代码...

[系统] 对话结束，正在更新 docs/CONTEXT.md...
[系统] 正在更新 docs/CHANGELOG.md...
[系统] 正在 git commit...
```

**价值**：
- ✅ 不用担心忘记更新文档
- ✅ 每次对话都有完整的 git 记录
- ✅ 团队协作可追溯

### 2.3 `vibecollab ai agent` - 自主模式

**场景**：让 AI 自主完成一个任务

```bash
vibecollab ai agent run
```

**你得到什么**：
- AI 自主 Plan → Execute → Solidify
- 自动化执行、验证、固化
- 适合重复性任务

**工作流程**：

```
Plan 阶段:
  → 分析项目状态
  → 识别待办事项
  → 生成行动计划

Execute 阶段:
  → 执行代码修改
  → 运行测试
  → 验证结果

Solidify 阶段:
  → 更新文档
  → Git 提交
  → 记录到 Insight 系统
```

**价值**：
- ✅ 解放双手，AI 自主工作
- ✅ 每一步都有验证和回滚
- ✅ 自动知识沉淀

---

## 🧠 三 Insight 知识沉淀系统

### 3.1 自动知识积累

**场景**：你在开发中学到了一个经验

**使用前**：
- 写在 README 里（容易被遗忘）
- 记在笔记本里（不共享）
- 靠记忆（会忘记）

**使用 v0.8.0**：
```bash
# 创建 Insight
vibecollab insight add \
  --title "JWT Token 过期时间最佳实践" \
  --category "security" \
  --tags "jwt,auth,security" \
  --content "过期时间建议设置为 15 分钟，..."

# 记录使用（奖励权重）
vibecollab insight use INS-001

# 搜索相关 Insight
vibecollab insight search --tags "jwt"
```

**你得到什么**：
- 结构化的知识库
- 自动关联和推荐
- 权重衰减和奖励机制

### 3.2 Task-Insight 自动关联

**场景**：创建任务时自动推荐相关经验

```bash
# 创建任务
vibecollab task create \
  --id TASK-DEV-001 \
  --role DEV \
  --feature "用户登录功能"

# 系统自动搜索关联 Insight
[系统] 发现 3 个相关 Insight:
  - INS-001: JWT Token 过期时间最佳实践
  - INS-005: 密码哈希最佳实践
  - INS-012: 安全测试清单

# 关联到任务
[系统] 已自动关联到 TASK-DEV-001
```

**价值**：
- ✅ 不用翻阅历史文档
- ✅ 相关经验自动推送
- ✅ 避免重复犯错

### 3.3 学习路径推荐

**场景**：新团队成员快速上手

**使用 v0.8.0 的 Profile 和 Collection**：

```python
# ProfileManager 推荐学习路径
from vibecollab import ProfileManager

manager = ProfileManager()

# 为开发者推荐 Profile 和 Collection
recommendation = manager.recommend_for_developer(
    skills=["python", "react"],
    tags=["web", "fullstack"],
    limit=3
)

print(recommendation)
# {
#   "profiles": [FULLSTACK_DEV],
#   "collections": [WEB_DEV_ESSENTIALS, BACKEND_FOUNDATIONS]
# }

# 获取学习路径
collection = manager.get_collection("web-dev-essentials")
print(collection.get_learning_path())
# ["INS-001", "INS-002", "INS-005", "INS-012"]
```

**价值**：
- ✅ 新成员快速找到学习路径
- ✅ 按序学习，循序渐进
- ✅ 经验可打包、可移植

---

## 👥 四多开发者/多 Agent 协同

### 4.1 独立上下文管理

**场景**：多开发者协同，每个人有自己的工作上下文

**使用 v0.8.0**：

```bash
# 切换开发者身份
vibecollab dev switch alice

# alice 的工作上下文
# docs/developers/alice/CONTEXT.md

# 切换到 bob
vibecollab dev switch bob

# bob 的工作上下文
# docs/developers/bob/CONTEXT.md
```

**你得到什么**：
- 每个开发者独立的工作空间
- 不冲突的 CONTEXT.md
- 清晰的权责边界

### 4.2 自动冲突检测

**场景**：多开发者同时修改同一文件

**使用 v0.8.0**：
```bash
# 检测跨开发者冲突
vibecollab dev conflicts -v

[系统] 检测到 2 个冲突:
  1. 文件冲突: src/auth.py (alice 和 bob 同时修改)
  2. 任务冲突: TASK-DEV-001 依赖 TASK-ARCH-002，但后者被 alice 取消
```

**价值**：
- ✅ 提前发现冲突
- ✅ 不用等到 Git merge
- ✅ 明确的冲突类型（文件/任务/依赖）

### 4.3 全局聚合视图

**场景**：查看整个团队的工作状态

**使用 v0.8.0**：
```bash
# 重新生成全局聚合
vibecollab dev sync --aggregate

# 查看 docs/CONTEXT.md（全局聚合）
# 自动汇总所有开发者的工作状态
```

**你得到什么**：
- 一目了然的团队进度
- 自动化的状态汇总
- 便于项目管理和排期

---

## 🔍 五协议自检和健康检查

### 5.1 配置验证

**场景**：确保配置正确

**使用 v0.8.0**：
```bash
vibecollab validate -c project.yaml
```

**你得到什么**：

```
⚠️ 发现 1 个警告:
  ⚠️ project.version: 版本格式可能不符合语义化版本: v0.8.0-dev
   💡 建议使用格式: major.minor.patch (如 1.0.0)

ℹ️ 发现 2 个提示:
  ℹ️ roles.QA: 角色 QA 是 gatekeeper
  ℹ️ multi_developer: 多开发者模式已启用

✅ 配置有效: project.yaml
```

**价值**：
- ✅ 三级报告（ERROR/WARNING/INFO）
- ✅ 不阻塞可选项
- ✅ 提供修复建议

### 5.2 项目健康评分

**场景**：了解项目整体健康状态

**使用 v0.8.0**：
```bash
vibecollab health --json
```

**你得到什么**：

```json
{
  "score": 75,
  "grade": "B",
  "signals": [
    {
      "name": "test_coverage",
      "level": "warning",
      "value": 65,
      "message": "测试覆盖率低于目标 (65% < 80%)"
    },
    {
      "name": "recent_commits",
      "level": "info",
      "value": 5,
      "message": "最近 7 天有 5 个提交"
    },
    {
      "name": "unresolved_tasks",
      "level": "warning",
      "value": 3,
      "message": "3 个任务处于 REVIEW 状态超过 3 天"
    }
  ]
}
```

**价值**：
- ✅ 量化项目健康状态
- ✅ 10+ 种信号类型
- ✅ 便于跟踪改进

---

## 📋 六文档体系和版本管理

### 6.1 自动化文档生成

**使用 v0.8.0**，你得到一套完整的文档体系：

```
my-project/
├── CONTRIBUTING_AI.md         # AI 协作规则（自动生成）
├── llms.txt                   # 项目上下文摘要（自动生成）
├── project.yaml                # 项目配置（你写的）
└── docs/
    ├── CONTEXT.md              # 当前开发上下文（自动更新）
    ├── DECISIONS.md            # 决策记录（自动更新）
    ├── CHANGELOG.md            # 变更日志（自动更新）
    ├── ROADMAP.md              # 路线图（你维护）
    ├── QA_TEST_CASES.md        # 测试用例（你维护）
    ├── PRD.md                  # 产品需求（你维护）
    └── developers/             # 开发者工作空间（多开发者模式）
        ├── alice/
        │   ├── CONTEXT.md      # alice 的工作上下文
        │   └── .metadata.yaml
        └── bob/
            ├── CONTEXT.md
            └── .metadata.yaml
```

**文档更新时机**：

| 文件 | 更新时机 | 更新方式 |
|------|----------|----------|
| CONTEXT.md | 每次对话结束 | AI/手动更新 |
| CHANGELOG.md | 每次对话结束 | AI/手动更新 |
| DECISIONS.md | 重要决策后 | AI/手动更新 |
| CONTRIBUTING_AI.md | 协作方式演进 | `vibecollab generate` |

**价值**：
- ✅ 不用担心文档过时
- ✅ 每次对话都有记录
- ✅ 便于回溯和审计

### 6.2 Git 自动集成

**场景**：每次对话结束自动提交

**使用 v0.8.0**，对话结束后：
```bash
[系统] 正在更新 docs/CONTEXT.md...
[系统] 正在更新 docs/CHANGELOG.md...
[系统] 正在 git commit...

# 自动提交信息
git commit -m "feat(DEV-001): 实现用户登录功能

- 添加 JWT 认证
- 实现登录/登出 API
- 添加单元测试

相关 Insight: INS-001, INS-005"
```

**价值**：
- ✅ 不用手动写 commit message
- ✅ 每次修改都有追溯
- ✅ Insight 自动关联

---

## 🎨 七高度可定制

### 7.1 自定义角色

**场景**：你的项目有特殊的角色体系

```yaml
# project.yaml
roles:
  - code: "ML_ENGINEER"
    name: "机器学习工程师"
    focus: ["模型训练", "数据分析"]
    triggers: ["ML", "模型", "训练"]
    is_gatekeeper: false
```

**AI 就能识别**：
```bash
vibecollab ai ask "作为一个 ML_ENGINEER，如何优化模型训练速度？"
```

### 7.2 自定义字段

**场景**：你的项目有特殊的元数据

```yaml
# project.yaml
custom:
  company: "MyCompany"
  team_size: 20
  framework: "MyCustomFramework"
```

**访问自定义字段**：
```python
from vibecollab import ProjectAdapter

adapter = ProjectAdapter(config)
company = adapter.get_custom("company", "Unknown")
team_size = adapter.get_custom("team_size", 0)
```

### 7.3 自定义模板

**场景**：你想在协作规则中加入自定义章节

```
my-project/
├── .vibecollab/
│   └── patterns/
│       ├── 03_roles.md.j2        # 覆盖内置的角色模板
│       ├── custom_intro.md.j2     # 新增公司简介章节
│       └── manifest.yaml         # 自定义章节顺序
└── CONTRIBUTING_AI.md            # 自动生成
```

**.vibecollab/patterns/manifest.yaml**:
```yaml
sections:
  - id: header
    template: 01_header.md.j2
  - id: custom_company_intro    # 新增章节
    template: custom_intro.md.j2
    condition: "has_custom_field(company)"
  - id: roles
    template: 03_roles.md.j2
```

**.vibecollab/patterns/custom_intro.md.j2**:
```jinja2
## 公司简介

{{ custom.company }} 拥有 {{ custom.team_size }} 人的开发团队，
主要使用 {{ custom.framework }} 框架。
```

**重新生成**：
```bash
vibecollab generate -c project.yaml
```

**结果**：
```markdown
# CONTRIBUTING_AI.md

...（默认章节）

## 公司简介

MyCompany 拥有 20 人的开发团队，
主要使用 MyCustomFramework 框架。

...（其他章节）
```

**价值**：
- ✅ 不修改源代码
- ✅ 保持向后兼容
- ✅ 灵活定制

---

## 🚀 八实际使用场景

### 场景 1：单人开发 + AI 协作

**工作流**：

```bash
# 1. 初始化项目
vibecollab init -n "MyApp" -d web -o ./my-app

# 2. 开始开发
cd my-app
vibecollab ai chat

> 我要实现用户注册功能

[AI] 好的，这是实现方案...

> 开始实现

[AI] 正在生成代码...

[系统] 对话结束，已更新文档和 git commit

# 3. 查看进度
cat docs/CONTEXT.md
cat docs/CHANGELOG.md
```

**你获得**：
- ✅ AI 自动遵循协作规则
- ✅ 每次对话都有完整记录
- ✅ 不用手动更新文档

### 场景 2：多人协同

**工作流**：

```bash
# 1. Alice 的视角
vibecollab dev switch alice
vibecollab ai chat

> 我要实现后端 API

[AI] 好的，作为 DEV 角色...

[系统] 已更新 docs/developers/alice/CONTEXT.md

# 2. Bob 的视角
vibecollab dev switch bob
vibecollab dev conflicts

[系统] 检测到文件冲突: src/auth.py
[系统] 建议与 alice 协调

# 3. PM 的视角
vibecollab dev sync --aggregate

# 查看全局聚合的 docs/CONTEXT.md
# 一目了然地看到 Alice 和 Bob 的进度
```

**你获得**：
- ✅ 清晰的权责边界
- ✅ 自动冲突检测
- ✅ 全局进度视图

### 场景 3：新成员接入

**工作流**：

```bash
# 1. 新成员加入
vibecollab dev init --developer "carol"

# 2. 引导接入
vibecollab onboard --developer carol

[系统] 项目概况: MyApp v1.0.0
[系统] 当前进度: 80%
[系统] 待办事项: [TASK-DEV-003, TASK-QA-001]
[系统] 推荐学习路径: [INS-001, INS-002, INS-005]

# 3. 推荐下一步
vibecollab next

[系统] 建议完成 TASK-DEV-003: 用户注册功能
[系统] 关联 Insight: INS-001, INS-005
```

**你获得**：
- ✅ 快速了解项目
- ✅ 明确的下一步行动
- ✅ 推荐的学习路径

---

## 💎 九总结：你到底获得了什么？

### 9.1 核心价值

| 价值 | 说明 | 影响 |
|------|------|------|
| **结构化协作** | AI 遵循统一的协作规则 | 提升协作效率 |
| **知识沉淀** | 自动积累和复用经验 | 避免重复犯错 |
| **文档自动化** | 自动生成和更新文档 | 降低维护成本 |
| **冲突预警** | 提前发现文件/任务冲突 | 减少合并冲突 |
| **健康量化** | 量化的项目健康评分 | 持续改进 |
| **高度定制** | 灵活的配置和模板 | 适应各种项目 |

### 9.2 对比：用 vs 不用 VibeCollab

| 维度 | 不用 VibeCollab | 用 VibeCollab v0.8.0 |
|------|---------------|---------------------|
| AI 协作规则 | 手写提示词，不一致 | 自动生成，统一规则 |
| 知识管理 | 靠记忆，容易遗忘 | 自动沉淀，随时复用 |
| 文档更新 | 手动更新，容易过时 | 自动更新，实时同步 |
| 冲突处理 | Git merge 时才发现 | 提前预警，提前解决 |
| 团队协作 | 上下文混乱 | 独立上下文，清晰边界 |
| 新人接入 | 阅读大量文档 | 自动引导，推荐路径 |
| 项目健康 | 凭感觉，不量化 | 量化评分，信号追踪 |

### 9.3 适合的使用场景

✅ **适合**：
- 需要大量 AI 协作的项目
- 多人/多 Agent 协同开发
- 需要知识沉淀和复用的团队
- 注重文档和追溯的项目

❌ **可能不适合**：
- 单人小项目（过度设计）
- 不需要 AI 协作的项目
- 已有成熟工具链的项目

---

## 🔟 十快速上手

### 第一步：安装

```bash
pip install vibe-collab
```

### 第二步：初始化项目

```bash
vibecollab init -n "MyApp" -d web -o ./my-app
cd my-app
```

### 第三步：开始协作

```bash
# 生成 AI 协作规则
vibecollab generate -c project.yaml

# 开始 AI 对话
vibecollab ai chat

# 验证配置
vibecollab validate -c project.yaml

# 查看健康状态
vibecollab health
```

---

## 🎊 结语

VibeCollab v0.8.0 不是一个简单的工具，而是一个：

📋 **开发方法论** - Vibe Development 哲学  
🤖 **AI 协作框架** - 三模式 CLI  
🧠 **知识管理系统** - Insight 沉淀  
👥 **协同开发平台** - 多开发者/多 Agent 支持  
📊 **质量保障体系** - 协议自检 + 健康评分  

**它让 AI 不再是简单的代码生成器，而是真正的协作伙伴。**

---

*文档版本: v0.8.0*  
*最后更新: 2026-02-26*
