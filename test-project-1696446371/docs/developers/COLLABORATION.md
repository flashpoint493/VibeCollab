# TestProject 协作文档

## 任务分配矩阵

| 任务 ID | 任务名称 | 负责人 | 协作者 | 状态 | 依赖 |
|---------|----------|--------|--------|------|------|
| TASK-DEV-001 | 用户认证模块 | ocarina | - | IN_PROGRESS | - |
| TASK-DEV-002 | 前端登录页面 | alice | ocarina | IN_PROGRESS | - |
| TASK-DEV-003 | RESTful API 设计 | alice | ocarina | TODO | TASK-DEV-001 |

## 任务依赖关系

```
TASK-DEV-001 (ocarina) ──> TASK-DEV-003 (alice)
                            │
                            └──> 前后端集成
```

## 协作约定

### API 接口设计
- **负责人**: alice
- **审核人**: ocarina
- **约定**: 所有 API 接口需要双方确认后才能实现

### 代码审查
- 所有 PR 需要另一位开发者 review
- 关键模块（认证、支付）需要双方都 approve

## 交接记录

### 2026-02-10 23:00 - 数据库设计交接
- **交接人**: ocarina
- **接收人**: alice
- **内容**: 用户表 schema 已完成，alice 可以开始前端开发
- **文档**: `docs/database_schema.md`

## 待讨论事项

1. **API 接口格式**
   - 提出人: alice
   - 需要讨论: RESTful 还是 GraphQL？
   - 优先级: HIGH

2. **Session 过期策略**
   - 提出人: ocarina
   - 需要讨论: 默认过期时间设置
   - 优先级: MEDIUM

---
*最后更新: 2026-02-10 23:10*
