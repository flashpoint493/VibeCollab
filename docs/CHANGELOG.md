# VibeCollab 变更日志

## v0.4.3 (2026-02-09)

### 配置改进
- **关键文件职责配置完善**:
  - 补充 `llms.txt`, `DECISIONS.md`, `QA_TEST_CASES.md`, `ROADMAP.md` 到文档体系配置
  - 确保其他仓库使用时能生成完整的关键文件职责说明（CONTRIBUTING_AI.md 第八章）
  - 同步更新 `project.yaml` 和 `default.project.yaml` 模板

### 发布
- 构建 PyPI 发布包 (dist/vibe_collab-0.4.3.tar.gz, vibe_collab-0.4.3-py3-none-any.whl)
- 待上传到 PyPI

---

## v0.4.2 (2026-01-21)

### 新功能
- **协议自检机制**: 
  - 协议检查器模块 (`protocol_checker.py`)，检查 Git 协议、文档更新、对话流程协议
  - CLI 命令 `vibecollab check` 执行协议检查，支持严格模式
  - 在 CONTRIBUTING_AI.md 中添加协议自检章节（第十章节）
  - 支持对话中通过触发词触发自检（"检查协议"、"协议自检"等）
- **PRD 文档管理**: 
  - PRD 管理器模块 (`prd_manager.py`)，支持需求的创建、更新、状态管理
  - 需求变化历史跟踪
  - 项目初始化时自动创建 PRD.md 模板
  - 在 CONTRIBUTING_AI.md 中添加 PRD 管理章节（第十一章节）
  - 支持对话中通过触发词管理 PRD（"记录需求"、"更新 PRD"等）

### 改进
- 更新项目配置模板，添加 `protocol_check` 和 `prd_management` 配置项
- 在文档列表中添加 PRD.md
- 完善快速参考章节，添加协议自检触发词

### 文档
- 创建 PRD.md 记录项目需求（REQ-001: 协议自检机制, REQ-002: PRD 文档管理）

---

## v0.4.1 (2026-01-21)

### 改进
- **阶段定义优化**: 
  - Production 阶段添加"完善发布平台标准"原则
  - Commercial 阶段添加"插件化增量开发"和"数据热更"重点
- **阶段化规则设计优化**: CONTRIBUTING_AI.md 中的阶段规则改为类型定义和模板，具体当前阶段信息移至 ROADMAP.md

---

## v0.4.0 (2026-01-21)

### 新功能
- **Git 检查和初始化**: 项目初始化时自动检查 Git，可选自动初始化仓库
- **项目生涯管理**: 4个阶段（demo/production/commercial/stable）的完整管理系统
- **阶段化协作规则**: CONTRIBUTING_AI.md 中包含所有阶段的规则，标注当前激活阶段
- **ROADMAP 集成**: 在 ROADMAP.md 中显示项目生涯阶段信息
- **生涯管理命令**: `vibecollab lifecycle check` 和 `upgrade` 命令

### 改进
- 将生涯阶段信息放在 ROADMAP.md（PM 侧重的文档）
- Demo 阶段早期介入 CI/CD
- Production 阶段前确立性能规范和代码重构
- 完善文档体系（DECISIONS.md, ROADMAP.md, QA_TEST_CASES.md）

### 重构
- 全局替换 llm.txt 为 CONTRIBUTING_AI.md
- 更新所有代码、文档、模板引用

---

## v0.3.0 (2026-01-20)

### 新功能
- **llms.txt 标准集成**: 自动检测并更新 llms.txt，添加 AI Collaboration 章节
- **llmstxt.py 模块**: 管理 llms.txt 的创建和更新

### 重构
- 重命名包为 `vibe-collab`
- 重命名仓库为 `VibeCollab`

---

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

## 对话记录

### 对话16: 修复 Windows 编码问题 (2026-02-10) [FIX]

**问题**:
- `vibecollab check` 命令在 Windows GBK 环境下因 emoji 字符崩溃
- UnicodeEncodeError: 'gbk' codec can't encode character

**解决方案**:
- 实现 `is_windows_gbk()` 平台检测函数
- 添加 emoji 和特殊字符映射表：
  - ✅ → OK, ❌ → X, ⚠️ → !, ℹ️ → i
  - • → -, 🔒 → [保留]
- 修改所有 CLI 输出使用 EMOJI_MAP 和 BULLET

**修改文件**:
- `src/vibecollab/cli.py`: 添加平台检测和字符替代（+80 行）
- `src/vibecollab/cli_lifecycle.py`: 同步修改生涯管理命令（+36 行）

**测试结果**:
- ✅ `vibecollab check` 在 Windows GBK 下正常运行
- ✅ 显示格式良好，易读性未受影响

**技术债务**:
- ✅ **已解决**: Windows 控制台编码问题（高优先级）

### 对话15: 协议自检执行 (2026-02-10) [VIBE]

**检查结果**:
- ✅ Git 仓库正常
- ⚠️ CHANGELOG.md 19天未更新
- ⚠️ CONTEXT.md 2天未更新
- 总计 3 项检查：0 错误，2 警告，1 信息

**发现问题**:
- Windows 控制台编码问题：`vibecollab check` 因 emoji 字符导致 GBK 编码错误
- 临时方案：直接调用 Python `ProtocolChecker` 模块

**产出**:
- 更新 CONTEXT.md 记录对话15
- 补充 CHANGELOG.md 缺失的记录（对话14、v0.4.3）
- 将 Windows 编码问题记录到技术债务

### 对话14: 完善关键文件职责配置 (2026-02-09) [CONFIG]

**背景**:
- 从 GitHub 拉取最新代码
- 发现 documentation.key_files 配置不完整

**改进**:
- 补充 4 个关键文件配置：llms.txt, DECISIONS.md, QA_TEST_CASES.md, ROADMAP.md
- 同步更新 project.yaml 和 templates/default.project.yaml

**发布**:
- 版本升级到 v0.4.3
- 构建发布包：`python -m build`

---

## 历史版本

### 对话1-4: 项目初始化到文档同步

- 项目初始化、CLI 实现
- Schema 设计、生成器核心逻辑
- 领域模板创建
