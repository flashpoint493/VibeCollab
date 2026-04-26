# VibeCollab Dashboard - 开发驾驶舱使用指南

## 概述

VibeCollab Dashboard 是一个轻量级的开发驾驶舱可视化工具，提供实时的工作流上下文监控、校验和可视化功能。它基于现有的 v0.12.x 架构，不引入新的业务逻辑，只提供派生视图。

## 安装与设置

Dashboard 功能已集成到 VibeCollab 中，无需额外安装。确保你的项目包含以下文件：

- `project.yaml` - 项目配置
- `.vibecollab/tasks.json` - 任务管理
- `.vibecollab/workflows/*.yaml` - 工作流定义
- `.vibecollab/plan_state/*.json` - 执行计划状态
- `.vibecollab/roles/*/context.yaml` - 角色上下文

## 可用命令

### 1. 显示开发驾驶舱面板

```bash
# 显示一次性面板
vibecollab workflow panel

# 监控模式（每2秒自动刷新）
vibecollab workflow panel --watch
```

**面板内容包含6个区域：**
- **Project Status**: 项目版本、里程碑、Git状态、当前角色
- **Workflow Health**: 校验状态、配置健康度
- **Roadmap & Tasks**: 路线图进度、任务状态统计
- **Active Plans**: 正在执行的计划、步骤进度
- **Role Requests**: 角色上下文、待处理需求
- **Prompt Suggestions**: AI提示建议、下一步命令推荐

### 2. 工作流校验

```bash
# 显示格式化校验结果
vibecollab workflow validate

# 输出JSON格式结果（用于外部工具集成）
vibecollab workflow validate --json-output
```

**校验内容包括：**
- 工作流文件可发现性和可解析性
- 计划schema合法性
- Action host配置检查
- 状态文件可读性
- Roadmap与Tasks对齐性
- 角色上下文存在性
- 文档时效性检查

### 3. 生成快照

```bash
# 生成默认路径的快照
vibecollab workflow snapshot

# 指定输出路径
vibecollab workflow snapshot --output dashboard.json
```

**快照文件位置：** `.vibecollab/runtime/workflow_snapshot.json`

## 快照数据结构

快照文件包含以下主要字段：

```yaml
kind: workflow_snapshot
generated_at: "2026-04-13T12:00:00Z"
project:
  name: VibeCollab
  version: v0.12.4
  milestone: v0.12.x support
git:
  dirty: true
  changed_files: 7
role:
  current: dev
  active_roles: [architect, dev, insight_collector]
roadmap:
  pending_count: 10
  top_pending: [...]
tasks:
  summary:
    todo: 0
    in_progress: 1
    review: 0
    done: 24
  active: [...]
plans:
  active: [...]
workflows:
  discovered: [...]
validate:
  status: warn
  issues: [...]
suggestions:
  next_commands: [...]
  prompt_hints: [...]
```

## 架构设计

### 包结构
```
src/vibecollab_dashboard/
├── __init__.py          # 包导出
├── workflow_snapshot.py # 数据聚合层
├── workflow_validator.py # 校验逻辑层
└── workflow_panel.py    # UI渲染层
```

### 设计原则
1. **无业务逻辑修改**: Dashboard 只读取现有数据，不修改业务逻辑
2. **派生视图**: metadata 自动从现有状态源汇总
3. **轻量级**: 基于 rich 库，不引入重依赖
4. **可扩展**: 后续可拆分为独立包 `vibecollab_dashboard`

## 故障排除

### 常见问题

**Q: 面板显示 "ModuleNotFoundError"**
A: 确保项目路径正确，且所有依赖包已安装

**Q: 校验报告大量警告**
A: 检查项目配置文件完整性，特别是角色上下文路径

**Q: 快照生成失败**
A: 确认 `.vibecollab` 目录结构完整

### 调试模式

可以设置环境变量查看详细日志：
```bash
export VIBECOLLAB_DEBUG=1
vibecollab workflow panel
```

## 后续计划

- [ ] 支持键盘交互（r刷新、j导出、v校验、q退出）
- [ ] 增量刷新高亮显示变化
- [ ] 外部工具集成接口
- [ ] 性能优化和缓存机制

## 贡献指南

Dashboard 设计为独立包，欢迎贡献：
1. 遵循现有代码风格
2. 保持无业务逻辑修改原则
3. 添加相应的测试用例
4. 更新使用文档