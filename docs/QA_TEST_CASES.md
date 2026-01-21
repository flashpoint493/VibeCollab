# VibeCollab 测试用例手册

## 测试用例格式

```
### TC-{模块}-{序号}: {测试名称}
- **关联**: TASK-XXX
- **前置**: {前置条件}
- **步骤**:
  1. {步骤1}
  2. {步骤2}
- **预期**: {预期结果}
- **状态**: 🟢/🟡/🔴/⚪
```

## Phase 1 测试用例

### TC-CLI-001: 项目初始化
- **关联**: 核心功能
- **前置**: 已安装 vibe-collab
- **步骤**:
  1. 运行 `vibecollab init -n "TestProject" -d generic -o ./test-project`
  2. 检查生成的文件
- **预期**: 
  - 生成 CONTRIBUTING_AI.md
  - 生成 project.yaml
  - 生成 docs/ 目录及所有文档
  - 自动初始化 Git 仓库（如果可用）
- **状态**: 🟢

### TC-CLI-002: 生成协作规则文档
- **关联**: 核心功能
- **前置**: 存在 project.yaml 配置文件
- **步骤**:
  1. 运行 `vibecollab generate -c project.yaml`
  2. 检查生成的 CONTRIBUTING_AI.md
- **预期**: 
  - 生成完整的协作规则文档
  - 包含所有配置的章节
  - 自动集成 llms.txt（如果存在）
- **状态**: 🟢

### TC-CLI-003: llms.txt 集成
- **关联**: DECISION-002
- **前置**: 项目目录中已有 llms.txt
- **步骤**:
  1. 运行 `vibecollab generate -c project.yaml`
  2. 检查 llms.txt 文件
- **预期**: 
  - llms.txt 中添加 AI Collaboration 章节
  - 引用 CONTRIBUTING_AI.md
  - 不重复添加（多次运行）
- **状态**: 🟢

### TC-CLI-004: 创建新的 llms.txt
- **关联**: DECISION-002
- **前置**: 项目目录中没有 llms.txt
- **步骤**:
  1. 运行 `vibecollab generate -c project.yaml`
  2. 检查是否创建 llms.txt
- **预期**: 
  - 创建符合 llmstxt.org 标准的 llms.txt
  - 包含项目基本信息和 AI Collaboration 章节
- **状态**: 🟢

### TC-GIT-001: Git 自动初始化
- **关联**: DECISION-007
- **前置**: Git 已安装，项目目录不是 Git 仓库
- **步骤**:
  1. 运行 `vibecollab init -n "TestProject" -d generic -o ./test-project`
  2. 检查 .git 目录
- **预期**: 
  - 自动初始化 Git 仓库
  - 创建初始提交
  - 显示成功提示
- **状态**: 🟢

### TC-GIT-002: Git 检查提示
- **关联**: DECISION-007
- **前置**: Git 未安装或项目不是 Git 仓库
- **步骤**:
  1. 运行 `vibecollab generate -c project.yaml`
  2. 查看输出提示
- **预期**: 
  - 显示 Git 状态警告或提示
  - 建议初始化 Git 仓库
- **状态**: 🟢

### TC-LIFECYCLE-001: 项目生涯检查
- **关联**: DECISION-004
- **前置**: 项目已初始化，包含 lifecycle 配置
- **步骤**:
  1. 运行 `vibecollab lifecycle check`
  2. 查看输出信息
- **预期**: 
  - 显示当前阶段信息
  - 显示阶段重点和原则
  - 显示里程碑状态
  - 显示是否可以升级
- **状态**: 🟢

### TC-LIFECYCLE-002: 项目生涯升级
- **关联**: DECISION-004
- **前置**: 项目处于 demo 阶段，满足升级条件
- **步骤**:
  1. 运行 `vibecollab lifecycle upgrade`
  2. 检查 project.yaml 更新
  3. 检查阶段历史记录
- **预期**: 
  - 更新 current_stage 为 production
  - 添加新的阶段历史记录
  - 显示升级建议
- **状态**: 🟡 (需要手动测试)

### TC-ROADMAP-001: ROADMAP 包含阶段信息
- **关联**: DECISION-004
- **前置**: 项目已初始化
- **步骤**:
  1. 检查 docs/ROADMAP.md
  2. 查看阶段信息
- **预期**: 
  - 包含当前项目生涯阶段章节
  - 显示阶段重点和原则
  - 显示阶段历史
- **状态**: 🟢

### TC-CONTRIBUTING-001: CONTRIBUTING_AI.md 包含阶段化规则
- **关联**: DECISION-004
- **前置**: 项目已生成 CONTRIBUTING_AI.md
- **步骤**:
  1. 检查 CONTRIBUTING_AI.md
  2. 查找阶段化协作规则章节
- **预期**: 
  - 包含"阶段化协作规则"章节
  - 显示当前激活阶段
  - 列出所有阶段的规则
- **状态**: 🟢

### TC-UPGRADE-001: 协议升级命令
- **关联**: 核心功能
- **前置**: 存在旧版本的项目配置
- **步骤**:
  1. 运行 `vibecollab upgrade -c project.yaml`
  2. 检查配置合并结果
- **预期**: 
  - 保留用户自定义配置
  - 添加新的配置项
  - 重新生成 CONTRIBUTING_AI.md
- **状态**: 🟢

### TC-DOMAIN-001: 领域扩展加载
- **关联**: 核心功能
- **前置**: 使用领域模板初始化项目
- **步骤**:
  1. 运行 `vibecollab init -n "GameProject" -d game -o ./game-project`
  2. 检查生成的文档
- **预期**: 
  - 加载 game 领域扩展
  - 生成领域特定的章节
  - 包含领域特定的角色和流程
- **状态**: 🟢

---

## 已知问题

### 🔴 高优先级问题
(暂无)

### 🟡 中优先级问题
- Windows 控制台编码问题（GBK）导致某些 Unicode 字符显示异常
  - 影响: twine upload 时的进度条显示
  - 状态: 已通过 --disable-progress-bar 缓解

### ⚪ 低优先级问题
- 大项目生成速度可能较慢
- 配置验证错误提示可以更详细

---

*最后更新: 2026-01-21*
