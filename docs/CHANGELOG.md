# LLMTXTGenerator 变更日志

## 2026-01-20

### 对话8: 补充遗漏章节 [FEAT]

根据 llm_example.txt 原始游戏案例，补充遗漏的重要章节：

**generator.py 新增方法**:
- `_add_iteration_protocols()` - 迭代建议管理、版本回顾、构建打包、配置级迭代
- `_add_qa_protocol()` - QA 验收协议、快速验收模板
- `_add_prompt_engineering()` - Prompt 工程最佳实践
- `_add_decisions_summary()` - 已确认决策汇总
- `_add_changelog()` - 文档迭代日志
- `_add_git_history_reference()` - Git 历史参考

**default.project.yaml 新增配置**:
- `version_review` - 版本回顾配置
- `build` - 构建配置
- `quick_acceptance` - 快速验收配置
- `prompt_engineering` - Prompt 工程配置
- `confirmed_decisions` - 已确认决策列表
- `llm_txt_changelog` - 文档迭代日志

**SKILL.md 同步更新**:
- 补充重要协议章节
- 添加 Prompt 工程最佳实践

---

### 对话7: 封装 Cursor Skill [FEAT]

### 对话6: 清理重复模板 [REFACTOR]

### 对话5: 实现扩展钩子处理 [DEV]

### 对话1-4: 项目初始化到文档同步
