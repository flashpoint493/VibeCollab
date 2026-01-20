# LLMTXTGenerator 当前上下文

## 当前状态
- **阶段**: Phase 1 - 核心框架 + 扩展机制重构
- **进度**: 扩展机制重新设计完成
- **下一步**: 实现扩展机制的代码支持

## 本次对话成果

### 决策
- **[DESIGN] 扩展机制重设计** (S级，已确认)
  - 扩展 = 流程钩子 + 上下文注入 + 引用文档
  - 不是静态配置说明，而是流程节点的上下文增强
  - 支持引用外部文档，避免扩展内容膨胀

### 产出
1. **llm.txt** - 本项目自身的协作规则（元实现）
2. **schema/extension.schema.yaml** - 扩展机制 Schema
3. **重构三个领域扩展**:
   - `game.extension.yaml` - 游戏领域（GM命令注入、测试模板）
   - `web.extension.yaml` - Web领域（API文档注入、部署指南）
   - `data.extension.yaml` - 数据领域（数据质量检查）

### 扩展机制核心概念

```
钩子 (Hook)
  ├── trigger: 触发点 (qa.list_test_cases, dev.feature_complete, ...)
  ├── action: 动作 (inject_context, append_checklist, ...)
  ├── context_id: 关联上下文
  └── condition: 触发条件

上下文 (Context)
  ├── type: reference  → 引用外部文档
  ├── type: template   → 内联模板
  ├── type: computed   → 动态计算
  └── type: file_list  → 文件列表
```

## 待完成事项
- [ ] 在 generator.py 中实现扩展钩子处理
- [ ] 在生成的 llm.txt 中体现扩展内容
- [ ] 添加扩展机制的单元测试
- [ ] 完善 mobile/infra 领域扩展

## 技术债务
- templates/ 和 src/llmtxt/templates/ 存在重复，需要统一

---
*最后更新: 2026-01-20*
