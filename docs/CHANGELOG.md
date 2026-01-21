# LLMContextGenerator 变更日志

## v0.2.0 (2026-01-20)

### 新功能
- **需求澄清协议**: 将用户模糊需求自动转化为结构化描述
- **upgrade 命令**: `llmcontext upgrade` 无缝升级协议到最新版本，保留用户配置
- **Git 初始化约束**: 协议层强制新项目初始化 Git 仓库
- **使用流程图**: README 添加完整工作流程图

### 改进
- README 补充完整章节列表、Cursor Skill 说明
- SKILL.md 同步所有协议更新
- project_template.yaml 新增需求澄清、快速验收、构建配置

---

## v0.1.1 (2026-01-20)

### 对话10: 需求澄清协议 [FEAT]

**generator.py**:
- 新增 `_add_requirement_clarification()` 方法
- 将用户模糊需求转化为结构化描述

**结构化需求模板**:
- 原始描述 → 需求分析（目标/场景/用户）
- 功能要求 → 验收标准
- 待确认项 → 决策等级

---

### 对话9: CONTRIBUTING_AI.md 自更新 + README 更新 [VIBE] [DOC]

- 新增 `project.yaml` - 项目自身配置
- `CONTRIBUTING_AI.md` 使用生成器自更新，包含全部章节
- README 补充完整章节列表、Cursor Skill 说明

---

### 对话8: 补充遗漏章节 [FEAT]

**generator.py 新增方法**:
- `_add_iteration_protocols()` - 迭代建议管理、版本回顾、构建打包、配置级迭代
- `_add_qa_protocol()` - QA 验收协议、快速验收模板
- `_add_prompt_engineering()` - Prompt 工程最佳实践
- `_add_decisions_summary()` - 已确认决策汇总
- `_add_changelog()` - 文档迭代日志
- `_add_git_history_reference()` - Git 历史参考

---

### 对话7: 封装 Cursor Skill [FEAT]

- 创建 `.cursor/skills/llmcontext/SKILL.md`
- 添加 references/project_template.yaml
- 添加 assets/CONTEXT_TEMPLATE.md、CHANGELOG_TEMPLATE.md
- 打包为 llmcontext-skill.zip

---

### 对话6: 清理重复模板 [REFACTOR]

- 删除根目录 `templates/`（保留包内）
- 更新 pyproject.toml 构建配置

---

### 对话5: 实现扩展钩子处理 [DEV]

- 新增 `extension.py`: 钩子管理、条件评估、上下文解析
- 支持 reference/template/file_list/computed 四种上下文
- 集成到 generator.py 生成扩展章节
- 新增 13 个扩展机制单元测试

---

### 对话1-4: 项目初始化到文档同步

- 项目初始化、CLI 实现
- Schema 设计、生成器核心逻辑
- 领域模板创建
