# REQ: VibeCollab Plan 能力增强需求

> 状态: **软约束运行中** | 优先级: **P1** | 创建: 2026-04-07
>
> **当前策略**: PlanRunner 暂未实现的 action 以**软约束**形式运行（AI 自觉遵守 workflow YAML 中的声明）。
> VibeCollab 后续版本更新后，这些软约束将升级为硬执行，同时更新 `tkgo-setup.md`。

## 1. 背景

TKGO 项目的完整开发链路需要：

```
IDE 加载 setup skill → 开发者发需求
→ 制作人角色接收 → 需求评审/分类
→ 路由触发 plans/workflows 中的计划步骤
→ workflow 逐步加载 role + role plan 微文件
→ vibecollab role 切换角色和上下文
→ 建立 task → 执行开发
→ 完成后沉淀 insight → 更新 role context
→ 回到上层 plan 步骤 → 直到任务完成
→ 全局 context 聚合
```

## 2. 现状分析：VibeCollab PlanRunner 实际能力

### 2.1 PlanRunner 支持的 action（5 种）

| Action | 功能 | 执行方式 |
|--------|------|---------|
| `cli` | 执行 shell 命令 | `subprocess.run(command)` |
| `assert` | 文件/内容断言 | 检查文件存在性和内容 |
| `wait` | 延时 | `time.sleep(seconds)` |
| `prompt` | 发送消息给 HostAdapter | FileExchange / Subprocess / Auto |
| `loop` | 自治多轮循环 | state_command → prompt_template → check_command |

### 2.2 plans/workflows/ 中使用但 PlanRunner 不支持的 action

| 使用的 Action | PlanRunner 行为 | 影响 |
|--------------|----------------|------|
| `role_switch` | `Unknown action` **报错** | 所有角色流转步骤无法执行 |
| `check` | `Unknown action` **报错** | 质量门禁步骤无法执行 |
| `decision` | `Unknown action` **报错** | 条件分支无法执行 |

### 2.3 plans/workflows/ 中使用但 PlanRunner 不处理的字段

| 字段 | PlanRunner 是否处理 | 说明 |
|------|-------------------|------|
| `plan:` (步骤中引用微文件路径) | **不处理** | 纯 YAML 字段，不会自动加载文件 |
| `on_complete:` | **不处理** | PlanRunner 源码中 0 匹配 |
| `on_start:` | **不处理** | 属于 dialogue_protocol 配置，非 PlanRunner |
| `quality_gate:` | **不处理** | 属于 Git hooks 能力，非 PlanRunner |
| `knowledge_capture:` | **不处理** | 纯声明性标记 |
| `insight_inject:` | **不处理** | 无自动注入机制 |
| `completion_criteria:` | **不处理** | 无自动检查逻辑 |

### 2.4 已有且可用的 CLI 能力

| CLI 命令 | 功能 | 可用于 plan |
|----------|------|-----------|
| `vibecollab role switch <role>` | 切换角色 + 加载 context.yaml | ✅ 通过 `action: cli` |
| `vibecollab role whoami` | 查看当前角色 | ✅ |
| `vibecollab role sync` | 聚合所有角色 context | ✅ |
| `vibecollab task create --id X --role Y --feature Z` | 创建任务 + 自动关联 insight | ✅ |
| `vibecollab task transition <id> <status>` | 任务状态流转 | ✅ |
| `vibecollab task solidify <id>` | 固化任务（验证门控） | ✅ |
| `vibecollab insight search --tags <kw>` | 搜索经验 | ✅ |
| `vibecollab insight add --title X --tags Y --body Z` | 沉淀经验 | ✅ |
| `vibecollab check` | 协议合规检查 | ✅ |
| `vibecollab next --json` | 获取下一步建议 | ✅ |

## 3. 能力缺口清单

### GAP-001: `role_switch` action 不被支持 (关键)

**现状**: plans/workflows/ 中的步骤使用 `action: role_switch`，PlanRunner 返回 Unknown action 错误。

**解决方案 A: 改写 workflow（不改 VibeCollab 源码）**

将 `action: role_switch` 改为 `action: cli` + `command: "vibecollab role switch <role>"`：

```yaml
# 之前（不可执行）
- action: role_switch
  role: DEV
  description: "程序: 编码实现"
  plan: ".vibecollab/plans/agents/04-developer/step-03-implementation.yaml"

# 之后（可执行）
- action: cli
  command: "vibecollab role switch dev"
  description: "切换到 DEV 角色"
  expect:
    exit_code: 0
```

**解决方案 B: 扩展 PlanRunner（改 VibeCollab 源码）**

在 `execution_plan.py` 中增加 `role_switch` action 处理：

```python
elif action == "role_switch":
    role = step.get("role", "")
    sr = _exec_cli(
        {"command": f"vibecollab role switch {role}", "expect": step.get("expect", {})},
        self.project_root, self.timeout
    )
```

**推荐**: 方案 A（零侵入）+ 长期方案 B（更优雅）

### GAP-002: 微文件不会自动加载到上下文

**现状**: `plan:` 字段指向微文件路径，但 PlanRunner 不读取它。

**解决方案**: 在 `action: prompt` 中，将微文件内容嵌入 `message` 字段，或在 `action: cli` 中用 `cat` 输出。

**长期方案**: 扩展 PlanRunner 支持 `context_files` 字段，在 prompt 步骤中自动拼接文件内容到 message。

### GAP-003: 无条件分支能力（decision/check action）

**现状**: workflow 中的 `action: check` 和 `action: decision` 无法执行。

**解决方案**: 用 `action: cli` + `expect` 实现条件检查：

```yaml
- action: cli
  command: "vibecollab check"
  expect:
    exit_code: 0
  on_fail: abort  # 检查不通过则中止
```

### GAP-004: on_complete/on_start 生命周期钩子

**现状**: 微文件中新增的 `on_complete`/`on_start` 节点不被 PlanRunner 处理。

**解决方案**: 这些节点作为 **AI 阅读的指导规则**，不需要 PlanRunner 执行。AI 在执行微文件步骤时应主动读取并执行这些 CLI 命令。

## 4. 当前可行的完整链路（不改 VibeCollab 源码）

### 4.1 人机对话驱动模式

```
IDE 加载 tkgo-setup skill
  ↓
开发者: "开发存档系统"
  ↓
AI 读取 workflow 描述 (.vibecollab/plans/workflows/feature-development.yaml)
  ↓ 了解完整角色流转路径
  ↓
vibecollab role switch producer
  → 读取 agents/00-producer/step-01-requirement-analysis.yaml
  → 执行需求分类 + Smart Probe
  → vibecollab task create --id TASK-FEAT-001 --role PRODUCER --feature "存档系统"
  → 更新 roles/producer/context.yaml
  ↓
vibecollab role switch design
  → 读取 agents/02-designer/step-01~06 微文件
  → vibecollab insight search --tags "design,gameplay"
  → 执行策划 + 质量门禁
  → vibecollab task transition TASK-FEAT-001 IN_PROGRESS
  → 更新 roles/design/context.yaml
  ↓
vibecollab role switch arch → ... → vibecollab role switch dev → ...
  ↓
vibecollab role switch qa
  → 验收通过
  → vibecollab task solidify TASK-FEAT-001
  → vibecollab insight add --title "存档系统经验" --tags "feature,save-system"
  → 更新 roles/qa/context.yaml
  ↓
vibecollab role sync (全局 context 聚合)
vibecollab check
git commit -m "[FEAT] 实现存档系统"
```

### 4.2 Auto Driver 自主模式

`auto-dev-loop.yaml` 使用 `action: loop` + `prompt_template`，在模板中指导 AI 自行切角色。这是唯一能完全自动执行的方式：

```bash
vibecollab plan run auto-dev-loop --host auto:codebuddy -v
```

### 4.3 可执行 Workflow 模式（需改写 plans/workflows/）

将 `action: role_switch` 全部改为 `action: cli`，使 workflow 可以被 `vibecollab plan run` 直接执行。每个步骤通过 `action: prompt` 向 AI 发送微文件内容。

## 5. 建议优先级

| 优先级 | 项目 | 工作量 |
|--------|------|--------|
| **P0** | 人机对话驱动模式已可用 (当前状态) | 0 — skill 已配置完毕 |
| **P1** | 改写 plans/workflows/ 使其可被 plan run 执行 (GAP-001/003) | 中 — 5个文件 |
| **P2** | VibeCollab 源码扩展 role_switch action (GAP-001B) | 低 — 约10行代码 |
| **P3** | VibeCollab 源码扩展 context_files 自动加载 (GAP-002) | 中 — 需要设计 |
