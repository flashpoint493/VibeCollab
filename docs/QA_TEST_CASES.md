# 产品 QA 测试用例 - QA_TEST_CASES.md

**版本**: v0.8.0  
**最后更新**: 2026-02-26

---

## 核心功能测试

### TC-CORE-001: 项目初始化

**功能**: 项目初始化

**前置条件**: 已安装 vibe-collab

**测试步骤**:
1. 运行 `vibecollab init -n "TestProject" -d web -o ./test-project`
2. 检查生成的文件结构

**预期结果**:
- 生成的目录包含 `project.yaml`
- 生成的目录包含 `CONTRIBUTING_AI.md`
- 生成的目录包含 `docs/` 目录

**状态**: 🟢 PASS

---

### TC-CORE-002: 协议生成

**功能**: 从配置生成 AI 协议文档

**前置条件**: 已有 `project.yaml`

**测试步骤**:
1. 运行 `vibecollab generate -c project.yaml`
2. 检查生成的 `CONTRIBUTING_AI.md`

**预期结果**:
- 文件成功生成
- 包含核心理念章节
- 包含角色定义章节
- 包含决策分级章节

**状态**: 🟢 PASS

---

### TC-CORE-003: 配置验证

**功能**: 验证配置文件

**前置条件**: 已有 `project.yaml`

**测试步骤**:
1. 运行 `vibecollab validate -c project.yaml`

**预期结果**:
- 显示验证结果
- 有效配置显示 ✅
- 无效配置显示错误信息

**状态**: 🟢 PASS

---

## AI 协作功能测试

### TC-AI-001: 单次问答

**功能**: AI 单次问答

**前置条件**: 已初始化项目

**测试步骤**:
1. 运行 `vibecollab ai ask "如何设计用户认证？"`
2. 检查回答质量

**预期结果**:
- 返回合理的回答
- 回答基于项目上下文
- 不报错

**状态**: 🟢 PASS

---

### TC-AI-002: 持续对话

**功能**: AI 持续对话

**前置条件**: 已初始化项目

**测试步骤**:
1. 运行 `vibecollab ai chat`
2. 进行多轮对话
3. 检查对话结束后的文档更新

**预期结果**:
- 对话流畅
- 上下文保持
- 对话结束自动更新 `docs/CONTEXT.md`
- 对话结束自动更新 `docs/CHANGELOG.md`

**状态**: 🟢 PASS

---

### TC-AI-003: Agent 自主模式

**功能**: Agent 自主执行任务

**前置条件**: 已初始化项目

**测试步骤**:
1. 运行 `vibecollab ai agent plan`
2. 检查生成的行动计划

**预期结果**:
- 生成合理的行动计划
- 计划基于项目状态
- 不报错

**状态**: 🟢 PASS

---

## 知识沉淀功能测试

### TC-INSIGHT-001: 创建 Insight

**功能**: 创建知识沉淀

**前置条件**: 已初始化项目

**测试步骤**:
1. 运行 `vibecollab insight add --title "测试 Insight" --category "technique"`
2. 检查 Insight 是否创建

**预期结果**:
- Insight 成功创建
- 存储在 `.vibecollab/insights/` 目录
- 可以通过 `vibecollab insight list` 查看

**状态**: 🟢 PASS

---

### TC-INSIGHT-002: 搜索 Insight

**功能**: 搜索相关知识沉淀

**前置条件**: 已有多个 Insight

**测试步骤**:
1. 运行 `vibecollab insight search --tags "security"`
2. 检查搜索结果

**预期结果**:
- 返回匹配的 Insight
- 按相关性排序
- 显示 Insight 详情

**状态**: 🟢 PASS

---

### TC-INSIGHT-003: 使用 Insight

**功能**: 记录使用 Insight

**前置条件**: 已有 Insight

**测试步骤**:
1. 运行 `vibecollab insight use INS-001`
2. 检查 Insight 权重是否更新

**预期结果**:
- Insight 权重增加
- 使用记录保存
- 不报错

**状态**: 🟢 PASS

---

## Profile 功能测试

### TC-PROFILE-001: Profile 加载

**功能**: 加载开发者 Profile

**前置条件**: 已有 Profile 文件

**测试步骤**:
1. 运行 `vibecollab dev whoami`
2. 检查返回的 Profile 信息

**预期结果**:
- 返回当前开发者 ID
- 返回 Profile 详情
- 不报错

**状态**: 🟢 PASS

---

### TC-PROFILE-002: Profile 推荐

**功能**: 推荐 Profile

**前置条件**: 已有多个 Profile

**测试步骤**:
1. 使用 ProfileManager API
2. 调用 `recommend_profiles()` 方法
3. 检查推荐结果

**预期结果**:
- 返回匹配的 Profile
- 按匹配度排序
- 包含 Profile 详情

**状态**: 🟢 PASS

---

## 多开发者协同测试

### TC-MULTI-001: 开发者切换

**功能**: 切换开发者身份

**前置条件**: 多开发者模式已启用

**测试步骤**:
1. 运行 `vibecollab dev switch alice`
2. 检查 `docs/developers/alice/CONTEXT.md`
3. 运行 `vibecollab dev switch bob`
4. 检查 `docs/developers/bob/CONTEXT.md`

**预期结果**:
- 每个开发者有独立的 CONTEXT.md
- 切换不相互影响
- 不报错

**状态**: 🟢 PASS

---

### TC-MULTI-002: 冲突检测

**功能**: 检测跨开发者冲突

**前置条件**: 多开发者模式已启用

**测试步骤**:
1. 运行 `vibecollab dev conflicts`
2. 检查检测结果

**预期结果**:
- 返回冲突列表
- 显示冲突类型（文件/任务/依赖）
- 提供解决建议

**状态**: 🟢 PASS

---

## 协议自检测试

### TC-CHECK-001: 协议检查

**功能**: 检查协议遵循情况

**前置条件**: 已有项目

**测试步骤**:
1. 运行 `vibecollab check`
2. 检查检查结果

**预期结果**:
- 返回错误、警告、信息列表
- 提供修复建议
- 不报错

**状态**: 🟢 PASS

---

## 健康检查测试

### TC-HEALTH-001: 健康评分

**功能**: 量化项目健康状态

**前置条件**: 已有项目

**测试步骤**:
1. 运行 `vibecollab health`
2. 检查健康评分

**预期结果**:
- 返回 0-100 的分数
- 返回等级（A/B/C/D/F）
- 返回信号列表

**状态**: 🟢 PASS

---

## 测试总结

### 测试统计

- **总测试用例**: 15
- **通过**: 15
- **失败**: 0
- **通过率**: 100%

### 覆盖范围

- 核心功能: 3 个测试
- AI 协作: 3 个测试
- 知识沉淀: 3 个测试
- Profile: 2 个测试
- 多开发者: 2 个测试
- 协议自检: 1 个测试
- 健康检查: 1 个测试

---

*此文档由 AI Agent 维护*
