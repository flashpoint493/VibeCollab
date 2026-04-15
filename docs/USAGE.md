# VibeCollab v0.12.0 使用指南

> **快速参考**: v0.12.0新特性的常用命令示例

---

## 目录

1. [YAML-first文档系统](#yaml-first文档系统)
2. [工作流自动化](#工作流自动化)
3. [Insight派生链](#insight派生链)
4. [快速命令参考](#快速命令参考)

---

## YAML-first文档系统

### 核心概念

- **YAML是源文件** (`docs/*.yaml`)
- **Markdown是视图** (`docs/*.md`) - 自动生成，请勿手动编辑

### 基本命令

```bash
# 列出所有可渲染的YAML文档
vibecollab docs list

# 渲染所有文档
vibecollab docs render --all

# 渲染特定类型
vibecollab docs render -k context -k roadmap

# 验证YAML文档
vibecollab docs validate docs/context.yaml
```

### 支持的文档类型

| 类型 | YAML文件 | 输出Markdown |
|------|---------|-------------|
| context | context.yaml | CONTEXT.md |
| decisions | decisions.yaml | DECISIONS.md |
| changelog | changelog.yaml | CHANGELOG.md |
| roadmap | roadmap.yaml | ROADMAP.md |
| prd | prd.yaml | PRD.md |
| qa | qa.yaml | QA_TEST_CASES.md |

### 工作流集成

```bash
# 在提交前自动渲染
git add docs/*.yaml
vibecollab docs render --all
git add docs/*.md
git commit -m "更新文档"
```

---

## 工作流自动化

### 列出预置工作流

```bash
vibecollab plan list
```

### 预置工作流

| 工作流 | 用途 | 主要步骤 |
|--------|------|---------|
| `daily-sync` | 日常同步 | 检查→验证→渲染→提交→推送 |
| `release-prep` | 发布准备 | 测试→构建→打包→标签 |
| `insight-collect` | Insight收集 | 索引→建议→导出→提交 |

### 运行工作流

```bash
# 运行日常同步工作流
vibecollab plan run daily-sync

# 试运行模式(不实际执行)
vibecollab plan run release-prep --dry-run

# 详细输出
vibecollab plan run insight-collect -v

# 验证工作流语法
vibecollab plan validate daily-sync
```

### 使用不同Host适配器

```bash
# 文件交换适配器
vibecollab plan run daily-sync --host file_exchange

# 子进程适配器
vibecollab plan run daily-sync --host subprocess:git

# 自动IDE驱动(键盘模拟)
vibecollab plan run daily-sync --host auto:cursor
```

---

## Insight派生链

### 查看派生图

```bash
# 显示Insight派生树
vibecollab insight graph --show-derivation

# Mermaid格式(可用于图表渲染)
vibecollab insight graph --show-derivation --format mermaid

# JSON格式
vibecollab insight graph --show-derivation --json
```

### 创建带派生的Insight

```bash
# 自动检测派生关系(基于最近任务)
vibecollab insight derive \
  --title "新的设计模式" \
  --tags "design,pattern" \
  --category technique \
  --scenario "处理复杂状态机" \
  --approach "使用状态模式分离状态逻辑" \
  --source-task TASK-DEV-001

# 预览派生建议(不创建)
vibecollab insight derive \
  --title "测试派生" \
  --tags "test" \
  --category technique \
  --scenario "测试" \
  --approach "方法" \
  --dry-run

# 指定置信度阈值(0.0-1.0)
vibecollab insight derive \
  --title "高精度派生" \
  --tags "test" \
  --category technique \
  --scenario "测试" \
  --approach "方法" \
  --min-confidence 0.8

# 手动指定派生来源
vibecollab insight derive \
  --title "派生Insight" \
  --tags "derived" \
  --category technique \
  --scenario "场景" \
  --approach "方法" \
  --derived-from INS-001,INS-002
```

### 追溯Insight来源

```bash
# 查看Insight的完整追溯链
vibecollab insight trace <insight-id>
```

---

## 快速命令参考

### 文档管理

```bash
vibecollab docs list                    # 列出可渲染文档
vibecollab docs render --all            # 渲染所有文档
vibecollab docs render -k context       # 渲染特定类型
vibecollab docs validate <file>         # 验证文档
```

### 工作流

```bash
vibecollab plan list                    # 列出工作流
vibecollab plan run <workflow>          # 运行工作流
vibecollab plan run <wf> --dry-run      # 试运行
vibecollab plan run <wf> -v             # 详细输出
vibecollab plan validate <wf>           # 验证工作流
```

### Insight

```bash
vibecollab insight graph --show-derivation              # 派生图
vibecollab insight derive --title ... --tags ...        # 创建派生Insight
vibecollab insight trace <id>                           # 追溯来源
vibecollab insight list                                 # 列出Insight
vibecollab insight search <query>                       # 搜索Insight
```

### 日常开发工作流

```bash
# 1. 开始工作
vibecollab onboard                      # AI onboarding
vibecollab task list                    # 查看任务

# 2. 开发中
vibecollab insight suggest              # 获取Insight建议
# ... 编写代码 ...

# 3. 任务完成
vibecollab docs render --all            # 更新文档
vibecollab check                        # 检查合规
vibecollab insight derive ...           # 记录新Insight
vibecollab session save                 # 保存会话

# 4. 提交
vibecollab plan run daily-sync          # 运行同步工作流
```

### v0.12.0完整功能清单

| 命令 | 描述 |
|------|------|
| `vibecollab init` | 初始化项目 |
| `vibecollab generate` | 生成协作规则 |
| `vibecollab validate` | 验证配置 |
| `vibecollab upgrade` | 升级协议 |
| `vibecollab check` | 合规检查 |
| `vibecollab health` | 健康检查 |
| `vibecollab onboard` | AI onboarding |
| `vibecollab next` | 下一步建议 |
| `vibecollab prompt` | 生成提示词 |
| `vibecollab index` | 索引文档 |
| `vibecollab search` | 语义搜索 |
| `vibecollab docs list/render/validate` | 文档管理 ⭐新 |
| `vibecollab plan list/run/validate` | 工作流 ⭐新 |
| `vibecollab insight add/search/suggest/derive` | Insight管理 ⭐新 |
| `vibecollab insight graph --show-derivation` | 派生图 ⭐新 |
| `vibecollab task create/list/transition` | 任务管理 |
| `vibecollab roadmap status/sync` | 路线图 |
| `vibecollab role list/switch` | 角色管理 |
| `vibecollab hooks install` | Git钩子 |
| `vibecollab mcp serve/inject` | MCP服务器 |
| `vibecollab config setup` | 配置管理 |
| `vibecollab auto list/init` | 自动驱动 |

---

## 更多资源

- [完整README](../README.md)
- [v0.12.0迁移指南](./v0.12.0-migration-guide.md)
- [CHANGELOG](./CHANGELOG.md)
- [QA测试用例](./QA_TEST_CASES.md)
