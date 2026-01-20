# LLMTXTGenerator 变更日志

## 2026-01-20

### 对话6: 清理重复模板 [REFACTOR]

**删除**:
- `templates/` 目录（与 `src/llmtxt/templates/` 重复）

**修改**:
- `pyproject.toml`: 移除 `/templates` 引用，版本升级至 0.1.1
- `src/llmtxt/__init__.py`: 同步版本号
- `tests/test_cli.py`: 版本测试兼容

**构建**: llmtxt-0.1.1 本地安装成功

---

### 对话5: 实现扩展钩子处理 [DEV]

**新增**:
- `src/llmtxt/extension.py` - 扩展处理器
- `tests/test_extension.py` - 13 个测试

**测试**: 24 passed

---

### 对话4: 文档同步 [DOC]

### 对话3: 扩展机制重设计 [DESIGN]

### 对话2: Python 包重构 [FEAT]

### 对话1: 项目初始化 [ARCH]
