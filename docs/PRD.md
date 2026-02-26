# 产品需求文档 - PRD.md

**版本**: v0.8.0  
**最后更新**: 2026-02-26

---

## 项目概述

VibeCollab 是一个 AI 协作开发框架，从 YAML 配置生成标准化的 AI 协作协议，内置知识沉淀系统，支持多开发者/多 Agent 协同开发。

### 核心价值

- **单一数据源**: project.yaml 作为项目配置的唯一来源
- **模板驱动**: 使用 Jinja2 模板生成 CONTRIBUTING_AI.md
- **三模式 CLI**: 支持 IDE/交互/Agent 三种模式
- **知识沉淀**: Insight 系统自动积累和复用开发经验
- **多开发者协同**: 支持多人/多 Agent 协同开发

---

## 目标用户

1. **AI 驱动的开发团队**
   - 需要与 AI 进行大规模协作
   - 需要统一的协作规则
   - 需要知识沉淀和复用

2. **个人开发者 + AI**
   - 需要结构化的 AI 协作框架
   - 需要自动化文档生成
   - 需要知识积累

3. **多 Agent 协作场景**
   - 需要多个 AI Agent 协同工作
   - 需要独立的上下文管理
   - 需要冲突检测

---

## 功能需求

### Phase 1: 核心框架 ✅ (v0.8.0)

#### 1.1 PatternEngine - 模板渲染引擎
- ✅ Jinja2 模板渲染
- ✅ 26 个内置模板
- ✅ Template Overlay 支持
- ✅ manifest.yaml 章节管理

#### 1.2 ProjectAdapter - 配置适配器
- ✅ 必需字段验证
- ✅ 默认值支持
- ✅ 自定义字段支持
- ✅ 点路径访问

#### 1.3 三模式 CLI
- ✅ `vibecollab ai ask` - 单次问答
- ✅ `vibecollab ai chat` - 持续对话
- ✅ `vibecollab ai agent` - 自主模式

### Phase 2: 知识沉淀 ✅ (v0.8.0)

#### 2.1 Profile 系统
- ✅ DeveloperProfile - 开发者能力画像
- ✅ 3 个预设 Profile（全栈/AI专家/后端）
- ✅ ProfileManager - CRUD + 推荐

#### 2.2 Insight Collection
- ✅ InsightCollection - 知识包
- ✅ 4 个预设 Collection（Web/AI/后端/Vibe核心）
- ✅ 学习路径支持

#### 2.3 Task-Insight 关联
- ✅ 自动关联相关 Insight
- ✅ 关键词提取 + Jaccard 匹配

### Phase 3: 配置验证 ✅ (v0.8.0)

#### 3.1 ConfigValidator
- ✅ 必需字段验证
- ✅ 数据类型验证
- ✅ 值范围验证
- ✅ 三级错误报告（ERROR/WARNING/INFO）

#### 3.2 协议自检
- ✅ `vibecollab check` 命令
- ✅ 文档存在性检查
- ✅ Git 关联性检查

#### 3.3 健康检查
- ✅ `vibecollab health` 命令
- ✅ 0-100 量化评分
- ✅ 10+ 种信号类型

---

## 未来规划

### v0.9.0 (计划中)

#### 主题：生态完善

1. **领域扩展**
   - 移动端扩展
   - AI/ML 扩展
   - 更多模板

2. **CLI 增强**
   - 交互式引导
   - 插件系统
   - 配置热重载

### v1.0.0 (未来)

#### 主题：正式版

1. **稳定性保障**
   - 完整测试覆盖
   - 完善文档
   - 社区支持

2. **性能优化**
   - 模板渲染性能
   - 大型项目支持

---

## 非功能需求

### 性能
- 模板渲染时间 < 1s（中等大小项目）
- 配置验证时间 < 2s
- 健康检查时间 < 3s

### 可靠性
- 90+ 个单元测试，100% 通过率
- 覆盖率 > 80%

### 可扩展性
- 支持自定义模板
- 支持自定义字段
- 支持领域扩展

### 可用性
- 清晰的错误提示
- 完整的文档
- 交互式引导

---

## 技术栈

- **Python**: 3.8+
- **模板引擎**: Jinja2
- **CLI**: Click + Rich
- **配置**: PyYAML
- **测试**: pytest

---

## 成功指标

### v0.8.0-alpha

- [x] 90 个单元测试全部通过
- [x] 3 个 Phase 全部完成
- [x] 完整的文档体系
- [x] Git 仓库已推送

### v1.0.0

- [ ] 测试覆盖率 > 90%
- [ ] 10+ 个领域扩展
- [ ] 100+ 个用户
- [ ] 活跃的社区

---

## 相关链接

- **GitHub**: https://github.com/flashpoint493/VibeCollab
- **文档**: docs/
- **架构分析**: docs/ARCHITECTURE_QA.md
- **用户指南**: docs/USER_GUIDE_v080.md

---

*此文档由 AI Agent 维护*
