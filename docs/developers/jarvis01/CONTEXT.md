# VibeCollab - jarvis01 的工作上下文

## 当前状态
- **版本**: v0.8.0-dev
- **开发者**: jarvis01
- **角色**: Agent Developer
- **上次更新**: 2026-02-26 00:00:00
- **工作模式**: Agent 自主模式

## 开发者信息
- **身份**: AI Agent (GLM-4.7)
- **能力**: 自主开发、Insight 生成、任务执行、代码生成
- **专长**: 架构设计、系统分析、问题解决
- **状态**: 已启动，正在推进 v0.8.0

## 核心原则

> **遇到问题时，优先使用 vibe-collab CLI 的能力**

## 开发策略

### 问题解决优先级

1. **使用 CLI 验证**
   ```bash
   vibecollab validate config
   vibecollab check
   ```

2. **使用 CLI 搜索**
   ```bash
   vibecollab insight search "关键词"
   ```

3. **使用 CLI 询问**
   ```bash
   vibecollab ai ask "遇到的问题"
   ```

4. **使用 CLI 引导**
   ```bash
   vibecollab next
   ```

5. **使用 Agent 模式**
   ```bash
   vibecollab ai agent
   ```

### 不做的事

- ❌ 遇到问题时直接写代码绕过
- ❌ 忽略 CLI 提供的能力
- ❌ 不验证就提交代码

## 当前任务

### 🎯 Phase 1.3: 编写单元测试 (P0)

**目标**: 测试 ProjectAdapter 和 PatternEngine 集成

#### 步骤 1.3.1: 创建测试文件

**文件**: `tests/test_project_adapter.py`

**测试用例**:
- 测试必需字段验证
- 测试点路径解析
- 测试默认值返回
- 测试角色获取
- 测试自定义字段
- 测试错误处理

**验证标准**:
- ✅ 覆盖率 > 80%
- ✅ 所有边界情况测试

#### 步骤 1.3.2: 创建 PatternEngine 测试

**文件**: `tests/test_pattern_engine.py`

**测试用例**:
- 测试适配器集成
- 测试模板渲染
- 测试自定义字段访问
- 测试本地模板覆盖

**验证标准**:
- ✅ 适配器正确传递到模板
- ✅ 模板可以访问 adapter
- ✅ 自定义字段可访问

#### 步骤 1.3.3: 运行测试

```bash
cd /root/.openclaw/workspace/vibecollab/repo
python -m pytest tests/test_project_adapter.py -v --cov
python -m pytest tests/test_pattern_engine.py -v --cov
```

#### 步骤 1.3.4: 修复问题

如果测试失败：
1. 使用 `vibecollab ai ask` 分析问题
2. 使用 `vibecollab insight search` 查找相关知识
3. 修复后重新测试

## 项目目标

推进 VibeCollab 到 v0.8.0 版本，核心改进：
- ✅ ProjectAdapter 配置适配器
- ✅ 集成到 PatternEngine
- ⏳ 单元测试覆盖率 > 80%
- ⏳ Developer Profile 框架
- ⏳ Insight Collection 知识包
- ⏳ 配置验证 CLI

## 最近完成

### 2026-02-26 00:00

1. **创建 CLI 使用指南**
   - CLI_GUIDE.md: 完整的 CLI 使用文档
   - 问题解决流程
   - 最佳实践
   - 故障排除

2. **更新开发策略**
   - 明确问题解决优先级
   - 强调使用 CLI 能力
   - 避免绕过 CLI 直接写代码

3. **调整 Phase 1.3**
   - 详细规划单元测试
   - 加入 CLI 验证步骤
   - 准备测试运行命令

### 2026-02-25 23:50

1. **Phase 1.2 完成**
   - PatternEngine 集成 ProjectAdapter
   - 添加 adapter 和 custom 到模板上下文

2. **进度汇报**
   - 生成完整的进度汇报
   - 更新 CHANGELOG.md

### 2026-02-25 23:45

1. **Phase 1.1 完成**
   - ProjectAdapter 核心实现
   - 更新 __init__.py

2. **架构决策确认**
   - DECISION-003: Profile 模式
   - DECISION-004: ProjectAdapter 框架

### 2026-02-25 23:30

1. **深入领悟用户需求**
   - 理解"依靠 LLM 推理而非静态配置"
   - 理解"避免过度设计"
   - 理解"优先使用 CLI 能力"

2. **调整开发计划**
   - 确认两个架构决策
   - 制定详细的 Phase 计划

### 2026-02-25 23:00

1. **问题分析**
   - 阅读 CONTRIBUTING_AI.md
   - 分析 Insight Manager
   - 架构设计讨论

2. **Insight 生成**
   - INS-011: 避免过度设计
   - INS-012: 配置适配器模式

3. **决策记录**
   - DECISION-003: 不将 Developer 作为包
   - DECISION-004: ProjectAdapter 框架

4. **文档更新**
   - DECISION_ANALYSIS.md
   - DECISIONS.md
   - CHANGELOG.md

### 2026-02-25 22:43

1. 初始化 jarvis01 开发环境
2. 配置 GLM-4.7 API
3. 创建开发者上下文文件
4. 制定 v0.8.0 开发计划

## 待解决问题

- [ ] 开始实施 Phase 1.3.1: 创建测试文件
- [ ] 完成 Phase 1: 单元测试
- [ ] 开始 Phase 2: Developer Profile 框架

## 技术债务

- [ ] 需要完善部分缺失的模块
- [ ] 测试覆盖率有待提高
- [ ] 文档需要完善

## 开发笔记

### 核心领悟

1. **依靠 LLM 推理能力**
   - LLM 的优势是推理，而非记忆
   - 应该让 LLM 从上下文中动态推导
   - 静态配置应该最小化

2. **遵循 YAGNI 原则**
   - 只设计当前需要的功能
   - 保留扩展性但不预实现

3. **Profile 而非包**
   - Profile 定义能力和倾向
   - Insight Collection 提供知识
   - LLM 动态组合和推理

4. **配置扩展性**
   - 使用适配器模式
   - 支持自定义字段
   - 保持向后兼容

5. **优先使用 CLI**
   - 遇到问题先使用 CLI 验证
   - 使用 CLI 搜索和询问
   - 不绕过 CLI 直接写代码

### VibeCollab 最佳实践

1. **遵循协作规则**
   - 优先使用 vibe-collab CLI 能力
   - 使用 Insight 表达知识
   - 遵循决策分级制度

2. **文档驱动**
   - 每次对话更新 CONTEXT.md
   - 记录重要决策到 DECISIONS.md
   - 更新 CHANGELOG.md

3. **CLI 优先**
   - 使用 `vibecollab validate config` 验证
   - 使用 `vibecollab insight search` 搜索
   - 使用 `vibecollab ai ask` 询问
   - 使用 `vibecollab next` 获取建议

4. **代码质量**
   - 使用 ProjectAdapter 提高兼容性
   - 最小化状态
   - 依靠 LLM 推理能力

### 开发流程

1. **遇到问题时**:
   ```bash
   # 1. 验证
   vibecollab validate config
   vibecollab check

   # 2. 搜索
   vibecollab insight search "关键词"

   # 3. 询问
   vibecollab ai ask "问题"

   # 4. 引导
   vibecollab next
   ```

2. **完成功能后**:
   ```bash
   # 1. 验证
   vibecollab check

   # 2. 测试
   python -m pytest tests/

   # 3. 固化
   vibecollab task solidify
   ```

---
*此文件由 jarvis01 (Agent) 维护*
