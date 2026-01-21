# 项目生涯管理系统设计方案

## 1. Git 检查和初始化

### 功能需求
- 在项目初始化或升级时检查 Git 是否安装
- 检查项目目录是否已初始化 Git 仓库
- 如果未初始化，提示或自动初始化
- 在生成的文档中强调 Git 同步的重要性

### 实现方案
- 创建 `src/vibecollab/git_utils.py` 模块
- 提供函数：
  - `check_git_installed()`: 检查 git 是否安装
  - `is_git_repo(path)`: 检查路径是否是 git 仓库
  - `init_git_repo(path)`: 初始化 git 仓库
  - `ensure_git_repo(path, auto_init=False)`: 确保 git 仓库存在

## 2. 项目生涯管理系统

### 生涯阶段定义

```yaml
lifecycle:
  current_stage: "demo"  # demo / production / commercial / stable
  stages:
    demo:
      name: "原型验证"
      description: "快速验证核心概念和可行性"
      focus: ["快速迭代", "概念验证", "核心功能"]
      principles:
        - "快速试错，快速调整"
        - "优先核心功能，暂缓优化"
        - "技术债务可接受，但需记录"
        - "详细的Git开发迭代记录"
        - "记录重要决定DECISIONS.md"
        - "建立 CI/CD"
      milestones: []  # 里程碑列表
      
    production:
      name: "量产"
      description: "产品化开发，准备规模化"
      focus: ["稳定性", "性能优化", "可维护性"]
      principles:
        - "代码质量优先"
        - "建立发布和宣发预备, 指定和完善目标平台支持"
        - "启动前review全量代码，建立更稳定稳健的代码结构"
        - "完善QA产品测试覆盖"
        - "定义性能标准"
        - "Unitest单元测试、检查规范"
      milestones: []
      
    commercial:
      name: "商业化"
      description: "面向市场，追求增长"
      focus: ["用户体验", "市场适配", "扩展性"]
      principles:
        - "用户反馈驱动"
        - "数据驱动决策"
        - "快速响应市场"
      milestones: []
      
    stable:
      name: "稳定运营"
      description: "成熟产品，稳定维护"
      focus: ["稳定性", "维护成本", "长期规划"]
      principles:
        - "变更需谨慎"
        - "向后兼容优先"
        - "文档完善"
      milestones: []
```

### 设计选项对比

#### 选项 A: 单一 CONTRIBUTING_AI.md + 阶段字段
**优点**:
- 简单，单一文档
- 易于维护
- AI 读取方便

**缺点**:
- 文档可能过长
- 不同阶段规则混在一起
- 升级时需要重新生成整个文档

#### 选项 B: 多个 CONTRIBUTING_AI 文件（按阶段）
**优点**:
- 职责清晰，每个阶段独立
- 可以保留历史版本
- 升级时只需切换文件

**缺点**:
- 文件管理复杂
- 需要维护多个文件
- AI 需要知道当前阶段才能读取正确文件

#### 选项 C: 单一文件 + 阶段化章节（推荐）
**优点**:
- 平衡了简单性和清晰度
- 单一文档，但结构清晰
- 可以同时看到所有阶段的规则
- 升级时只需更新当前阶段标记

**缺点**:
- 文档可能较长（但可以通过折叠/索引优化）

### 推荐方案：选项 C + 配置驱动

```yaml
# project.yaml
lifecycle:
  current_stage: "demo"
  stage_history:
    - stage: "demo"
      started_at: "2026-01-20"
      milestones_completed: []
  
  # 每个阶段的特定配置
  stage_configs:
    demo:
      # 可以覆盖全局配置
      roles_override: []
      decision_levels_override: {}
      workflow_override: {}
```

在 `CONTRIBUTING_AI.md` 中：
```markdown
# AI 协作规则

## 当前项目生涯阶段
**阶段**: 原型验证 (demo)
**开始时间**: 2026-01-20
**阶段重点**: 快速迭代、概念验证、核心功能

## 阶段化协作规则

### 通用规则
（所有阶段都适用的规则）

### 原型验证阶段规则
（demo 阶段特定的规则和原则）

### 量产阶段规则
（production 阶段的规则，当前未激活）

### 商业化阶段规则
（commercial 阶段的规则，当前未激活）

### 稳定运营阶段规则
（stable 阶段的规则，当前未激活）
```

### 生涯升级流程

1. **触发时机**: 里程碑完成后自动检查，或手动触发
2. **检查条件**: 
   - 当前阶段里程碑是否全部完成
   - 是否满足下一阶段的前置条件
3. **升级流程**:
   - 生成升级建议
   - 更新 `project.yaml` 中的 `lifecycle.current_stage`
   - 重新生成 `CONTRIBUTING_AI.md`（更新当前阶段标记）
   - 记录升级历史
   - 提示需要关注的变更点

### 实现模块

1. `src/vibecollab/lifecycle.py`: 生涯管理核心逻辑
2. `src/vibecollab/git_utils.py`: Git 工具函数
3. 更新 `generator.py`: 支持阶段化规则生成
4. 更新 `cli.py`: 添加生涯检查命令

## 3. 集成点

- `Project.generate_all()`: 检查 Git，初始化生涯配置
- `Project.regenerate()`: 检查生涯状态，更新文档
- 新增命令: `vibecollab lifecycle check`: 检查当前生涯状态
- 新增命令: `vibecollab lifecycle upgrade`: 升级到下一阶段
