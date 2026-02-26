# 多开发者协作文档 - COLLABORATION.md

**版本**: v0.8.0  
**最后更新**: 2026-02-26

---

## 开发者列表

| 开发者 | ID | 角色 | 专长 | 状态 |
|--------|-----|------|------|------|
| jarvis01 | jarvis01 | AI Agent | Python, AI开发 | ✅ 活跃 |

---

## 协作规则

### 1. 工作空间隔离

每个开发者/Agent 都有独立的工作上下文：

```
docs/developers/{dev_id}/
├── CONTEXT.md          # 开发者的工作上下文
└── .metadata.yaml     # 元数据（角色、专长）
```

### 2. 任务分配

任务分配原则：
- 按角色和专长分配
- 明确的依赖关系
- 清晰的验收标准

### 3. 协作流程

#### 开始新任务
1. 切换到自己的开发者身份：
   ```bash
   vibecollab dev switch {dev_id}
   ```

2. 查看当前任务：
   ```bash
   vibecollab next
   ```

3. 开始工作：
   ```bash
   vibecollab ai chat
   ```

#### 完成任务
1. 更新自己的 CONTEXT.md
2. 更新全局 CHANGELOG.md
3. Git 提交代码
4. 同步到全局聚合：
   ```bash
   vibecollab dev sync --aggregate
   ```

### 4. 冲突处理

#### 文件冲突
- 运行冲突检测：
  ```bash
  vibecollab dev conflicts
  ```
- 协调解决
- 重新提交

#### 任务冲突
- 检查任务依赖
- 协调任务顺序
- 使用 Task Manager 管理

---

## 里程碑

### v0.8.0-alpha (当前)

**目标**: 完成核心功能

**状态**: ✅ 100% 完成

**完成情况**:
- [x] Phase 1: ProjectAdapter
- [x] Phase 2: Profile System
- [x] Phase 3: 配置验证 CLI

### v0.9.0 (计划中)

**目标**: 生态完善

**预计完成**: 2026-03-15

**主要任务**:
- [ ] 领域扩展（mobile/ai/data）
- [ ] CLI 增强（插件系统）
- [ ] 配置迁移工具

### v1.0.0 (未来)

**目标**: 正式版

**预计完成**: 2026-04-01

**主要任务**:
- [ ] 测试覆盖率 > 90%
- [ ] 完整文档
- [ ] 社区支持

---

## 沟通渠道

### 日常沟通
- GitHub Issues: https://github.com/flashpoint493/VibeCollab/issues
- Pull Requests: https://github.com/flashpoint493/VibeCollab/pulls

### 紧急联系
- GitHub Discussions: https://github.com/flashpoint493/VibeCollab/discussions

---

## 最佳实践

### 1. 代码提交
- 使用明确的 commit message
- 关联相关的 Issue
- 关联相关的 Insight

### 2. 文档更新
- 每次对话结束更新 CONTEXT.md
- 重要决策更新 DECISIONS.md
- 功能完成更新 CHANGELOG.md

### 3. 知识沉淀
- 重要经验创建 Insight
- 使用 `vibecollab insight add`
- 定期回顾和整理

---

## 工具使用

### 开发者管理
```bash
# 列出所有开发者
vibecollab dev list

# 查看开发者状态
vibecollab dev status jarvis01

# 切换开发者身份
vibecollab dev switch jarvis01
```

### 冲突检测
```bash
# 检测跨开发者冲突
vibecollab dev conflicts -v
```

### 全局同步
```bash
# 同步到全局聚合
vibecollab dev sync --aggregate

# 查看全局聚合的 CONTEXT.md
cat docs/CONTEXT.md
```

---

## 团队动态

### 2026-02-26

- **新增**: AI Agent jarvis01 加入团队
- **完成**: Phase 1、2、3 全部完成
- **里程碑**: v0.8.0-alpha 核心功能完成

---

*此文档由 AI Agent 维护*
