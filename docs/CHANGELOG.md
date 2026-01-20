# LLMTXTGenerator 变更日志

## 2026-01-20

### 对话7: 封装 Cursor Skill [FEAT]

**新增**:
- `.codebuddy/skills/llmtxt/SKILL.md` - Skill 定义
- `references/project_template.yaml` - 项目配置模板
- `assets/CONTEXT_TEMPLATE.md` - 上下文模板
- `assets/CHANGELOG_TEMPLATE.md` - 变更日志模板
- `dist/llmtxt-skill.zip` - 可分发的 Skill 包

---

### 对话6: 清理重复模板 [REFACTOR]

- 删除 `templates/` 目录
- 版本升级至 0.1.1

---

### 对话5: 实现扩展钩子处理 [DEV]

- 新增 `extension.py` 扩展处理器
- 24 个测试通过

---

### 对话4-1: 项目初始化到文档同步
