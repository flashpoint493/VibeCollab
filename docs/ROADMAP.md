# VibeCollab 路线图

## 当前项目生涯阶段

**阶段**: 原型验证 (demo)
**开始时间**: 2026-01-20
**阶段描述**: 快速验证核心概念和可行性

### 阶段重点
- 快速迭代
- 概念验证
- 核心功能

### 阶段原则
- 快速试错，快速调整
- 优先核心功能，暂缓优化
- 技术债务可接受，但需记录
- 详细的Git开发迭代记录
- 记录重要决定DECISIONS.md
- 建立 CI/CD

### 当前阶段里程碑
- v0.4.3 (已完成)
- v0.5.0 (已完成) - 多开发者支持
- v0.5.1 (已完成) - 冲突检测
- v0.5.4 (已完成) - CLI 开发者切换
- v0.5.5 (已完成) - EventLog 审计日志
- v0.5.6 (已完成) - TaskManager 验证-固化-回滚
- v0.5.7 (已完成) - LLM Client (CLI + API Key)
- v0.5.8 (已完成) - AI CLI 三模式架构 (ask/chat/agent)
- v0.5.9 (已完成) - Pattern Engine + Template Overlay
- v0.6.0 (已完成) - 协议成熟度提升 + 测试覆盖率增强

---

## 已完成里程碑

### Phase 2 - 多开发者支持 (v0.5.0 - v0.5.1)

#### v0.5.9 - Pattern Engine + Template Overlay (2026-02-24)
- [x] PatternEngine: Jinja2 模板 + manifest.yaml 声明式引擎
- [x] 27 个 .md.j2 模板替代硬编码 _add_*() 方法
- [x] Template Overlay: .vibecollab/patterns/ 本地覆盖机制
- [x] Legacy 移除: generator.py 1713→83 行
- [x] DECISION-011: Pattern Engine 架构
- [x] 40 PatternEngine tests (含 8 Overlay tests), 全量 215 tests 零回归

#### v0.5.8 - AI CLI 三模式架构 (2026-02-24)
- [x] vibecollab ai ask / chat — 人机交互 CLI
- [x] vibecollab ai agent plan / run / serve — Agent 自主模式
- [x] 安全门控: PID锁, pending-solidify, 最大周期, 自适应退避, 断路器, 内存阈值
- [x] DECISION-010: 三模式架构
- [x] 32 unit tests, 全量 174 tests 零回归

#### v0.5.7 - LLM Client (2026-02-24)
- [x] LLMClient: OpenAI + Anthropic 双 provider 支持
- [x] 环境变量配置 (VIBECOLLAB_LLM_*)
- [x] build_project_context() 自动上下文组装
- [x] httpx 可选依赖 (pip install vibe-collab[llm])
- [x] 30 unit tests, 全量 142 tests 零回归

#### v0.5.6 - TaskManager 验证-固化-回滚 (2026-02-24)
- [x] Task dataclass + TaskStatus 状态机
- [x] TaskManager: CRUD + transition + validate + solidify + rollback
- [x] EventLog 集成: 每次操作自动记录事件
- [x] 原子 JSON 持久化 (.vibecollab/tasks.json)
- [x] 53 unit tests, 全量 112 tests 零回归
- [x] 跨模块集成验证 (TaskManager + EventLog)

#### v0.5.5 - EventLog 审计日志 (2026-02-24)
- [x] Append-only JSONL 事件日志 (event_log.py)
- [x] 17 种事件类型, SHA-256 content fingerprint
- [x] 原子追加, 查询 API, 完整性验证
- [x] 24 unit tests, 全量 59 tests 零回归
- [x] DECISION-009 架构模式借鉴确认 (Direction B)

#### v0.5.4 - CLI 开发者切换 (2026-02-24)
- [x] `vibecollab dev switch` 命令
- [x] 持久化切换状态 (.vibecollab.local.yaml)
- [x] `vibecollab dev whoami` 显示身份来源

#### v0.5.1 - 冲突检测 (2026-02-10)
- [x] 跨开发者冲突检测算法
- [x] CLI 命令 `vibecollab dev conflicts`
- [x] CONTRIBUTING_AI.md 多开发者协作协议章节
- [x] 文档完善和使用示例

#### v0.5.0 - 多开发者支持 (2026-02-10)
- [x] 架构设计和决策确认 (DECISION-008)
- [x] 开发者身份自动识别（Git 用户名）
- [x] 开发者独立 CONTEXT.md 管理
- [x] 全局 CONTEXT.md 自动聚合
- [x] 开发者协作文档 (COLLABORATION.md)
- [x] CLI 命令扩展 (`vibecollab dev *`)
- [x] 项目配置扩展 (multi_developer)
- [x] 单开发者项目迁移支持
- [x] 完整单元测试验证

### Phase 1 - 核心功能完善 (v0.1.0 - v0.4.3)

#### 目标
- [x] 项目初始化和 CLI 实现
- [x] YAML 配置驱动生成
- [x] 领域扩展机制
- [x] 决策分级制度
- [x] 需求澄清协议
- [x] Git 检查和初始化
- [x] 项目生涯管理
- [x] 协议自检机制
- [x] PRD 文档管理
- [x] Windows 编码兼容

#### 完成时间
2026-01-20 至 2026-02-10

---

## 已完成里程碑: v0.6.0 - 协议成熟度提升 + CI/CD ✅

### 目标
借鉴成熟架构模式提升协议健壮性，完善开发流程 (DECISION-009)

### 核心功能
- [x] EventLog append-only 审计日志 (Iteration 1 ✅)
- [x] TaskManager 验证-固化-回滚 (Iteration 2 ✅)
- [x] Pattern Engine — Jinja2 模板驱动 + Template Overlay (Iteration 3 ✅)
- [x] Legacy 代码移除 — generator.py 1713→83 行 (Iteration 3 ✅)
- [x] 建立 CI/CD 流程（GitHub Actions）✅
- [x] Health Signal Extractor — 项目健康信号提取 (Iteration 4 ✅)
- [x] Agent Executor — LLM 计划实际执行 (文件写入/测试/git commit) ✅
- [x] Ruff lint 全量修复 ✅
- [x] 自动化测试覆盖率报告 ✅
- [x] 测试覆盖率提升 (58%→68%, +74 tests) ✅

### 完成时间
2026-02-24

---

## 未来里程碑

### ~~v0.7.0 - Web UI~~ ❌ 已砍掉 (DECISION-012)
> 决策：Web UI 不是核心竞争力，不投入资源。资源转向经验系统。

### v0.7.0 - Insight 沉淀系统（已完成 ✅）
- [x] Insight Schema 设计（本体 + Registry + Developer Tag 三部分）✅
- [x] InsightManager 核心模块（CRUD / Registry / 搜索 / 溯源 / 一致性校验）✅
- [x] InsightManager 单元测试 (62 tests) ✅
- [x] developer.py 单元测试补齐 (67 tests) ✅
- [x] Developer metadata 扩展（tags / contributed / bookmarks + 21 tests）✅
- [x] CLI 命令封装（`vibecollab insight list/show/add/search/use/decay/check/delete` + 21 tests）✅
- [x] 跨 Developer 共享 + 溯源 CLI 可视化（bookmark/unbookmark/trace/who/stats + 24 tests）✅
- [x] 一致性校验集成到 `vibecollab check --insights` ✅
- [x] 文档一致性检查增强（linked_groups 三级检查 + 可配置阈值）✅
- [x] Agent 引导命令 `vibecollab onboard` + `vibecollab next` ✅
- [x] 技术债务清理（版本号统一 v0.7.0-dev、项目名 VibeCollab、REQ-010→completed）✅
- [x] protocol_checker 多开发者动态发现（从文件系统扫描替代静态配置）✅

### v0.7.1 - Task-Insight 自动关联（已完成 ✅）
- [x] TaskManager.create_task() 自动搜索关联 Insight ✅
- [x] _extract_search_tags(): 从 feature/description/role 提取关键词 ✅
- [x] _find_related_insights(): Jaccard × weight 匹配 + metadata 存储 ✅
- [x] suggest_insights(): 已有任务的 Insight 推荐 ✅
- [x] CLI `vibecollab task create/list/show/suggest` ✅
- [x] EventLog 记录关联 Insight ✅
- [x] 向后兼容（无 InsightManager 时自动跳过）✅
- [x] 28 个单元测试（含 CLI + 集成 + 向后兼容）✅

### v0.8.0 - 稳定性验证 + 泛用性压力测试（开发中）
> 目标：在正式 v1.0 之前，对高级特性进行广泛的真实场景测试和质量加固

#### Config 配置管理系统 ✅
- [x] 三层配置架构 (env > ~/.vibecollab/config.yaml > defaults) ✅
- [x] `vibecollab config setup` 交互式向导 ✅
- [x] `vibecollab config show/set/path` 命令 ✅
- [x] `resolve_llm_config()` 统一解析 + LLMConfig 三层集成 ✅
- [x] 轻量 .env 解析 (VIBECOLLAB_* 前缀) ✅
- [x] 38 个单元测试 ✅

#### 测试覆盖率提升
- [x] 全量测试覆盖率 ≥ 80%（81% ✅）
- [x] Agent 模式 E2E 测试（35 tests: executor + cli_ai 全链路 ✅）
- [x] LLM Client mock 集成测试（26 tests: OpenAI + Anthropic 双 provider ✅）
- [x] CLI 命令全量 E2E 测试（48/48 子命令 CliRunner 覆盖 ✅）

#### Agent 模式稳定性 ✅
- [x] agent serve 长运行压力测试（100+ 周期、退避/断路器/内存阈值）✅
- [x] 并发安全验证（PID 锁、文件锁竞争）✅
- [x] agent run 失败恢复场景（测试回滚、网络超时、LLM 拒绝）✅
- [x] 自适应退避算法的边界条件测试 ✅

#### Insight 系统泛用性 ✅
- [x] 大规模 Insight 压力测试（100+ 条沉淀的搜索/衰减性能）✅
- [ ] 跨项目 Insight 可移植性验证（导出→导入→保持完整性）— 延后，需 export/import API
- [x] Task-Insight 关联精度评估（中英文混合场景、长文本、边界输入）✅
- [x] 衰减/奖励长期运行模拟（多轮 decay 后的权重分布合理性）✅

#### Insight 融入 IDE 对话模式 ✅
- [x] `27_insight_workflow.md.j2` 经验沉淀工作流模板章节 ✅
- [x] 对话结束流程增加"经验沉淀检查"步骤 ✅
- [x] `vibecollab next` 命令增加 Insight 沉淀提示（5 种信号检测）✅
- [x] manifest.yaml 注册 + 条件开关 (`insight.enabled|true`) ✅
- [x] 16 个单元测试（沉淀提示逻辑 11 + 模板渲染 5）✅

#### 人机交互质量
- [x] vibecollab ai ask/chat 在不同 terminal 环境下的 Unicode 兼容 ✅ `_compat.py` 统一兼容层
- [x] **`vibecollab prompt` 命令** ✅ — LLM 上下文 prompt 生成器，替代手动复制 CONTRIBUTING_AI.md
  - `_collect_project_context()` 共享函数 + `_extract_md_sections()` + `_build_prompt_text()`
  - `--compact` / `--copy` / `--sections` / `-d` 四种模式
  - 23 个单元测试，956/956 passed
- [x] **Protocol Checker watch_files 机制** ✅ — DECISIONS.md/PRD.md 跟随检查 + max_inactive_hours 可配置
- [ ] Rich 面板在 Windows PowerShell/CMD/WSL 的渲染验证 — 需手动验证
- [ ] onboard/next 在大型项目（多开发者、多文件）上的输出质量 — 需手动验证
- [x] 错误信息友好度审查（所有 CLI 命令的异常路径）✅ 审计完成 + insight 错误处理增强

#### 泛用性验证
- [ ] 在 3+ 个真实外部项目上运行 `vibecollab init` + `generate` + `check`
- [ ] 不同 Python 版本兼容性（3.9 / 3.10 / 3.11 / 3.12 / 3.13）— CI 已配置，待 push 验证
- [ ] 不同 OS 兼容性（Windows / macOS / Linux）
- [x] 极简项目（空 project.yaml）和复杂项目（全量配置）的边界测试 ✅ 15 tests

#### 文档与质量
- [ ] QA_TEST_CASES.md 全量更新（覆盖 v0.7.x 新功能）
- [x] README.md 更新（安装/快速开始/功能列表同步）✅ 项目结构/测试数/版本历史同步
- [x] 已知问题清零或标记延后 ✅

#### 定位决策
- [x] **`vibecollab ai` 标记 experimental** ✅ — VibeCollab 定位为协议管理工具，不自建 LLM 运行时。Tool Use 交给 Cline/Cursor/Aider。`ai ask/chat/agent` 保留但冻结，不继续投入
- [x] **Insight 读取路径规划** ✅ — 不在 `build_project_context()` 中注入，而是通过协议指引（CONTRIBUTING_AI.md）让 Cline/Cursor 在正确时机调用 `vibecollab insight search`

## v0.8.x+ 后续开发规划

> **核心方向**: VibeCollab 定位为**协议管理工具 + 结构化知识引擎**，不自建 LLM 运行时。
> 后续版本围绕**MCP/IDE 集成、文档完善与发布**两条主线推进。

### v0.9.0 - 语义检索引擎（Insight/文档向量化）

> 目标：让 Insight 和项目文档可被语义搜索，替代纯标签 Jaccard 匹配

#### 文档/代码向量化
- [x] `Embedder` 模块 — 轻量 embedding 抽象层 ✅
  - 支持 OpenAI `text-embedding-3-small` / 本地 `sentence-transformers` 双后端
  - 纯 Python trigram 哈希降级方案（零外部依赖）
  - 可选依赖 `pip install vibe-collab[embedding]`
- [x] `VectorStore` 模块 — 本地持久化向量存储 ✅
  - SQLite + 纯 Python 余弦相似度（零外部依赖方案）
  - struct pack/unpack 向量 blob 存储
  - 存储路径 `.vibecollab/vectors/`
- [x] `vibecollab index` 命令 — 索引项目文档 ✅
  - 增量索引 `CONTRIBUTING_AI.md`、`CONTEXT.md`、`DECISIONS.md`、`ROADMAP.md`、`PRD.md`、`CHANGELOG.md`
  - Insight YAML 全量索引（标题 + body + tags，支持结构化 dict body）
  - `--rebuild` 模式: 清除旧索引后重建
  - `--backend` 选择 embedding 后端
  - 代码文件可选索引（docstring / 函数签名）— 延后
  - `--watch` 模式: 文件变更自动重建索引 — 延后

#### 语义搜索集成
- [x] `vibecollab insight search --semantic` 增强 ✅
  - 基于向量余弦相似度的 Insight 语义搜索
  - 保持纯标签搜索为默认（零依赖兼容）
  - 混合检索 (标签 Jaccard + 向量余弦 → 加权融合排序) — 延后
- [x] `vibecollab search` 新命令 — 全局语义搜索 ✅
  - 跨 Insight / 文档统一搜索
  - 输出附带来源和相关度评分
  - `--type` 过滤来源类型，`--min-score` 阈值过滤
- [x] `onboard` 增强 — 语义匹配当前任务相关 Insight ✅
  - 从 CONTEXT.md / 开发者上下文提取当前任务描述 → 向量检索 Top-N 相关 Insight
  - Rich 面板 + JSON 输出双格式支持
  - 11 个单元测试

### v0.9.1 - MCP Server + AI IDE 集成

> 目标：让 VibeCollab 成为 Cline/Cursor/CodeBuddy 等 AI IDE 的"协议后端"，
> 从"手动复制粘贴"变成"IDE 自动读取协议"

#### MCP Server（Model Context Protocol）✅
- [x] `vibecollab mcp serve` — 标准 MCP Server 实现 ✅
  - Tool 暴露: `insight_search`, `insight_add`, `task_list`, `check`, `next`, `onboard`, `search_docs`, `project_prompt`, `developer_context`
  - Resource 暴露: `CONTRIBUTING_AI.md`, `CONTEXT.md`, `DECISIONS.md`, `ROADMAP.md`, `CHANGELOG.md`, Insight 列表
  - Prompt 暴露: `start_conversation` 对话开始时上下文注入模板
- [x] MCP CLI 命令组 ✅
  - `vibecollab mcp config --ide cursor/cline/codebuddy` 输出配置
  - `vibecollab mcp inject --ide all` 自动注入 IDE 配置文件
  - 支持 `stdio` 和 `sse` 两种传输模式
- [x] PyPI v0.9.1 发布 ✅ — `pip install vibe-collab[mcp]`
- [x] CodeBuddy Rule 集成 ✅ — `.codebuddy/rules/vibecollab-protocol.mdc`
- [x] 35 个单元测试，1074 全量 passed ✅

#### IDE 适配（待完善）
- [ ] Cursor Skill 自动生成 — `vibecollab export cursor-skill`
  - 从 `project.yaml` + `CONTRIBUTING_AI.md` 自动生成 `.cursor/skills/vibecollab/SKILL.md`
  - 项目配置变更时自动重新生成
- [ ] Cline Custom Instructions 适配 — `vibecollab export cline`
  - 生成 `.cline/custom_instructions.md`
- [ ] CodeBuddy Rule 适配 — `vibecollab export codebuddy`
  - 生成 `.codebuddy/rules/vibecollab.md`

### v0.9.2 - Insight 沉淀信号增强

> 目标：让 Insight 沉淀从"纯 LLM 推理"变成"结构化信号驱动"，提供可靠的沉淀上下文

#### 沉淀信号收集
- [x] `vibecollab insight suggest` — 基于结构化信号推荐候选 Insight ✅
  - 距上次 `insight add` 以来的 git commit 历史分析
  - CONTEXT.md / DECISIONS.md 变更 diff 检测
  - 新增/关闭的 Task 提取
  - 输出候选 Insight 列表，人工 confirm 后入库
- [x] 信号快照 — `.vibecollab/insight_signal.json` ✅
  - 记录上次 insight 沉淀的时间点和 commit hash
  - `insight add` 自动更新快照
  - `insight suggest` 从快照到 HEAD 提取增量信号

#### 对话持久化（一级缓存）
- [x] 对话 summary 存储 — `.vibecollab/sessions/` ✅
  - AI IDE 对话结束时的 summary 持久化（手动或 MCP 自动触发）
  - 作为 `insight suggest` 的输入信号之一
  - MCP `session_save` tool 暴露写入接口
- [x] MCP Server 增强 ✅
  - `insight_suggest` tool: 基于信号推荐候选 Insight
  - `session_save` tool: 保存对话 session summary
- [x] 60 个单元测试（insight_signal + session_store）✅
  - 全量 1134 passed, 1 skipped, 零回归

### v0.9.3 - Task/EventLog 核心工作流接通

> 目标：让 TaskManager 和 EventLog 从"底层 API"变成用户日常可感知的功能 (DECISION-016)

#### Task CLI 补齐
- [x] `vibecollab task transition` — 手动推进任务状态 (TODO→IN_PROGRESS→REVIEW→DONE) ✅
- [x] `vibecollab task solidify` — 固化任务 (REVIEW→DONE，通过验证门控) ✅
- [x] `vibecollab task rollback` — 回滚任务状态 ✅

#### 核心命令注入
- [x] `onboard` 注入活跃 Task 概览 — 显示当前 TODO/IN_PROGRESS/REVIEW 任务 ✅
- [x] `onboard` 注入最近 EventLog 事件摘要 ✅
- [x] `next` 基于 Task 状态推荐行动 — 超时/阻塞/待 solidify 任务优先提示 ✅

#### MCP Server 增强
- [x] `task_create` tool — AI IDE 可直接创建任务 ✅
- [x] `task_transition` tool — AI IDE 可推进任务状态 ✅

#### 测试 & 决策
- [x] 30 个单元测试，全量 1164 passed, 零回归 ✅
- [x] DECISION-016: v0.9.3 方向决策 (S 级) ✅

### v0.9.4 - Insight 质量与生命周期（已完成 ✅）

> 目标：提升沉淀质量，建立 Insight 从产生到淘汰的完整生命周期

- [x] Insight 自动去重 — 新增 Insight 时指纹+标题+标签相似度检查，防止重复沉淀 ✅
- [x] Insight 关联图谱 — `vibecollab insight graph` 可视化派生/关联关系 (text/json/mermaid) ✅
- [x] 跨项目 Insight 可移植性 — `insight export` / `insight import`（YAML 格式，三种冲突策略）✅
- [x] MCP Server 新增 `insight_graph` / `insight_export` 两个 Tool ✅
- [x] 36 个单元测试，全量 1201 passed, 零回归 ✅

### v0.9.5 - ROADMAP ↔ Task 集成（已完成 ✅）

> 目标：让 ROADMAP.md 与 TaskManager 双向联动，结构化追踪里程碑进度

- [x] RoadmapParser 模块 — 解析 ROADMAP.md 里程碑 + checklist + inline Task ID 引用 ✅
- [x] 双向同步 — ROADMAP `[x]` ↔ Task DONE 状态，三种方向（both/roadmap_to_tasks/tasks_to_roadmap）✅
- [x] Task `milestone` 字段 — Task dataclass 新增里程碑关联，`list_tasks(milestone=)` 过滤 ✅
- [x] CLI `vibecollab roadmap status/sync/parse` 命令组 ✅
- [x] CLI `vibecollab task create --milestone` / `task list --milestone` 增强 ✅
- [x] MCP Server 新增 `roadmap_status` / `roadmap_sync` 两个 Tool ✅
- [x] README 双语重构（英文主 README + 中文 README.zh-CN.md）✅
- [x] 40 个单元测试，全量 1331 passed, 89% 覆盖率, 零回归 ✅

### v0.9.7 - Roadmap 解析器格式引导（开发中）

> 目标：解决用户 ROADMAP 格式不匹配时无提示的问题，严格 ### 格式约束 + 清晰错误引导

- [x] 严格 ### 里程碑格式 — 只接受 `### vX.Y.Z`，拒绝 `####` 等其他层级 TASK-DEV-008
- [x] 零里程碑格式提示 — CLI 输出期望格式 + Task ID 关联语法 TASK-DEV-008
- [x] sync 零里程碑区分 — 不再误报"已同步" TASK-DEV-008
- [x] MCP Tool 描述增强 — AI IDE 可据此指导用户修改 ROADMAP TASK-DEV-008
- [x] init 模板兼容 — 生成的 ROADMAP 开箱可解析 TASK-DEV-008
- [x] v0.9.7 PyPI 发布

### v0.9.6 - PyPI 适配 + 文档质量（已完成 ✅）

> 目标：PyPI 发布页面可用性优化，项目文档时效性维护

- [x] README.pypi.md — PyPI 专用 README（去 Mermaid + 绝对 URL）TASK-DEV-006
- [x] pyproject.toml readme 字段指向 README.pypi.md TASK-DEV-006
- [x] CONTEXT.md 过期任务清理（TASK-DEV-005 已完成标记）TASK-DEV-007
- [x] v0.9.6 PyPI 发布

### v0.10.0 - 功能冻结 + 稳定性门槛 (DECISION-017)

> 目标：确保功能冻结前所有业务逻辑闭环，建立发布质量门槛。此版本后不再新增业务功能。

#### 外部项目 QA 验证
- [ ] 在 3+ 个真实外部项目上运行 Phase 11 TC-E2E-001~010
- [ ] 修复 QA 过程中发现的所有 bug

#### 质量门槛
- [ ] 测试覆盖率 ≥ 85%
- [ ] `vibecollab check` 全绿
- [ ] MCP Server 在 Cursor/CodeBuddy 中实际验证
- [ ] 功能冻结声明

### v0.10.1 - 代码国际化 (Code i18n)

> 目标：代码层面全英文化，确保非中文母语开发者可读

- [ ] 36 个 .py 文件的中文 docstring/comment 翻译为英文 (~2055 行)
- [ ] 62+ 处 CLI `help=` 参数翻译为英文
- [ ] 运行时输出文本 (`click.echo` / `console.print`) 英文化
- [ ] 错误消息英文化
- [ ] 全量 1201+ tests passed, 覆盖率不降

### v0.10.2 - 文档双语化 (Doc Bilingual)

> 目标：README 和核心文档提供英文版本

- [ ] README.md 重写为英文（作为主 README）
- [ ] README_CN.md 保留中文版
- [ ] CHANGELOG.md 整理为英文
- [ ] pyproject.toml description 英文化

### v0.10.3 - Git 历史重写 + 仓库门面

> 目标：一次性重写全部 commit message 为标准英文 + GitHub 门面专业化

- [ ] `git-filter-repo` 重写 97+ commit message 为 Conventional Commits 英文格式
- [ ] force push（不可逆，确保是最后的 history-breaking 操作）
- [ ] GitHub About 描述 + Topics 标签
- [ ] Issue / PR template
- [ ] CONTRIBUTING.md (英文，面向外部贡献者)
- [ ] CODE_OF_CONDUCT.md
- [ ] GitHub Release (v0.10.3+)
- [ ] Badge: PyPI / CI / Coverage / License / Python Version

### v1.0.0 - 正式发布

> 目标：标记稳定版本，PyPI + GitHub Release

- [ ] 清理所有 .dev0 标记
- [ ] PyPI v1.0.0 发布
- [ ] GitHub Release v1.0.0

### ~~v0.9.2(旧) - 自举能力~~ ❌ 已砍掉 (DECISION-015)
> 决策：`bootstrap` 价值不足（已有手写 CONTRIBUTING_AI.md），`ContextBuilder` 重构可在 MCP 开发中按需进行，不单列版本。

### ~~v0.10.1(旧) - Agent 稳定性增强~~ ❌ 已砍掉 (DECISION-015)
> 决策：MCP + 外部 IDE (Cline/Cursor/CodeBuddy) 已覆盖 Agent 场景，不再投入自建 Agent 能力。`vibecollab ai` 保持 experimental 冻结。

---

## 阶段历史

- **demo**: 2026-01-20 (进行中 → v1.0.0 后升级为 production)

---

## 未来规划

### 无监督运行能力（待定）
> 从 v0.10.0 降入未来规划 (DECISION-015)

- Git Hook 集成 (`vibecollab hook install`)
- CI/CD 无监督模式 (`vibecollab ci check/report/gate`)
- GitHub Action (`vibecollab-action`)
- 定时任务 (`vibecollab cron`)

### Production 阶段（量产）
**预计时间**: v1.0.0 发布后
**前置条件**: 
- v0.10.x 全部完成
- 测试覆盖率 85%+
- 代码/文档全英文化
- GitHub 门面专业化

**重点任务**:
- 社区运营 + 外部贡献者引入
- 插件生态（自定义 Pattern / 领域扩展）
- 性能优化（大规模项目）
- i18n 框架（多语言 CLI 输出）

### Commercial 阶段（商业化）
**预计时间**: 待定
**重点**:
- 用户体验优化
- 市场适配
- 扩展性提升

### Stable 阶段（稳定运营）
**预计时间**: 待定
**重点**:
- 稳定性维护
- 降低维护成本
- 长期规划

---

*最后更新: 2026-02-28 (v0.9.7 开发中)*
