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
> 后续版本围绕**自举能力、语义检索、IDE 集成、无监督运行**四条主线推进。

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

### v0.9.1 - 自举能力（VibeCollab 管理自身演进）

> 目标：VibeCollab 能用自己的协议和工具来管理自身的开发过程

#### 协议自举
- [ ] `vibecollab bootstrap` — 用 VibeCollab 协议初始化 VibeCollab 自身
  - 自动生成 VibeCollab 项目的 CONTRIBUTING_AI.md（吃自己的狗粮）
  - 验证: `vibecollab check` 在 VibeCollab 仓库上的输出为全绿
- [ ] 协议模板自测框架 — 模板变更后自动验证生成结果
  - CI 中增加 `vibecollab generate && vibecollab check` 自测步骤
  - 模板语法错误自动阻断发布

#### 模型推理解析增强
- [ ] `ContextBuilder` 重构 — 结构化上下文组装器
  - 替代 `build_project_context()` 的纯字符串拼接
  - 支持 Token 预算管理（按优先级截断）
  - 自动选择注入哪些 Insight / 文档段落（基于向量相关度 + Token 预算）
- [ ] Insight 自动生成 — 从 `git diff` + commit message 自动提炼候选 Insight
  - `vibecollab insight suggest` — 分析最近 N 次 commit，推荐可沉淀的经验
  - 人工 confirm 后入库（保持人在回路）

### v0.10.0 - AI IDE 集成层

> 目标：让 VibeCollab 成为 Cline/Cursor/Aider/OpenClaw 等 AI IDE 的"协议后端"

#### MCP Server（Model Context Protocol）
- [ ] `vibecollab mcp serve` — 标准 MCP Server 实现
  - Tool 暴露: `insight_search`, `insight_add`, `task_list`, `check`, `next`, `onboard`
  - Resource 暴露: `CONTRIBUTING_AI.md`, `CONTEXT.md`, `DECISIONS.md`, Insight YAML
  - Prompt 暴露: 对话开始时的上下文注入模板
- [ ] MCP 配置自动注入
  - `vibecollab init` 自动生成 `.cursor/mcp.json` / `.cline/mcp_settings.json`
  - 支持 `stdio` 和 `sse` 两种传输模式

#### Cursor / Cline / CodeBuddy 适配
- [ ] Cursor Skill 自动生成 — `vibecollab export cursor-skill`
  - 从 `project.yaml` + `CONTRIBUTING_AI.md` 自动生成 `.cursor/skills/vibecollab/SKILL.md`
  - 项目配置变更时自动重新生成
- [ ] Cline Custom Instructions 适配 — `vibecollab export cline`
  - 生成 `.cline/custom_instructions.md`
- [ ] CodeBuddy Rule 适配 — `vibecollab export codebuddy`
  - 生成 `.codebuddy/rules/vibecollab.md`

#### OpenClaw 插件
- [ ] `vibecollab-openclaw` 独立包
  - 注册为 OpenClaw Agent 插件
  - 暴露 VibeCollab CLI 能力为 OpenClaw Tool
  - 协议检查结果作为 Agent 评估反馈

### v0.10.1 - 无监督运行能力

> 目标：VibeCollab 在 CI/CD 和 Git Hook 中无需人工干预地运行

#### Git Hook 集成
- [ ] `vibecollab hook install` — 自动注入 Git hooks
  - `pre-commit`: `vibecollab check --strict` 阻断不合规提交
  - `post-commit`: `vibecollab insight suggest --auto` 自动推荐 Insight
  - `commit-msg`: 验证 commit message 格式是否符合协议 commit_prefixes

#### CI/CD 无监督模式
- [ ] `vibecollab ci` 命令组 — CI 环境优化
  - `vibecollab ci check` — 非交互模式，JSON 输出，退出码表示成败
  - `vibecollab ci report` — 生成 Markdown 格式的协议遵循报告（可作为 PR comment）
  - `vibecollab ci gate` — 作为 PR merge 门控（协议检查 + Insight 覆盖率）
- [ ] GitHub Action — `vibecollab-action`
  - 封装为可复用的 GitHub Action
  - 支持 PR 评论注入检查报告
  - 支持 auto-label（基于变更范围自动打标签）

#### 定时任务
- [ ] `vibecollab cron` — 周期性无监督任务
  - Insight 衰减周期执行 (`insight decay --all`)
  - 文档一致性自动报告
  - 向量索引增量更新

### v0.11.0 - Agent 稳定性增强（experimental 模块升级）

> 前提：v0.10.0 MCP 路径验证后，评估是否值得继续投入 agent 自建能力
> 如果 MCP + 外部 IDE 已满足 95% 场景，此版本可降级或取消

#### Agent 能力增强（条件性）
- [ ] Tool Use 框架 — 结构化工具调用协议
  - 定义 VibeCollab Tool Schema（JSON Schema）
  - LLM 返回 tool_call → agent_executor 解析执行
  - 支持 OpenAI function calling / Anthropic tool use 格式
- [ ] Agent 记忆系统 — 跨会话上下文保持
  - 短期: 对话内 token 管理（滑动窗口 + 摘要压缩）
  - 中期: 会话间状态持久化 (`.vibecollab/agent_memory/`)
  - 长期: Insight 系统作为永久记忆层
- [ ] Agent 自我评估 — 执行后健康检查
  - 每次 `agent run` 后自动执行 `vibecollab check`
  - 检查结果反馈给下一轮 LLM prompt
  - 连续 3 次 check 失败 → 自动暂停并通知

#### Agent 安全加固
- [ ] 沙箱执行环境 — 限制 agent 可操作范围
  - 文件系统白名单（只允许操作项目目录内文件）
  - 命令白名单（禁止 `rm -rf` 等危险操作）
  - 网络访问限制（仅允许 LLM API 调用）
- [ ] 人工审批门控 — 高风险操作确认
  - S/A 级决策变更需人工确认
  - 删除操作需人工确认
  - 基于 git diff 的变更量阈值（超过 N 行自动暂停）

### v1.0.0 - 正式发布

> 前置条件：v0.9.x 语义检索 + v0.10.x IDE 集成 至少各完成核心功能

#### 质量门槛
- [ ] 测试覆盖率 ≥ 85%
- [ ] 3+ 外部真实项目验证
- [ ] 英文文档完善（README / Quick Start / API Reference）
- [ ] PyPI 稳定版发布 + GitHub Release + Changelog
- [ ] MCP Server 至少在 Cursor/Cline 中可用

#### 正式功能集
- [ ] 协议管理: init / generate / validate / check
- [ ] 知识引擎: insight CRUD / 语义搜索 / 自动推荐
- [ ] IDE 集成: MCP Server / Cursor Skill / Cline 适配
- [ ] CI/CD: 无监督检查 / PR 门控 / Git Hook
- [ ] 文档: 中英文 README / 教程 / API 文档

---

## 阶段历史

- **demo**: 2026-01-20 (进行中)

---

## 未来规划

### Production 阶段（量产）
**预计时间**: 待定
**前置条件**: 
- 核心功能稳定
- 文档完善
- 测试覆盖率达到 80%+
- CI/CD 流程建立

**重点任务**:
- 代码质量优化
- 建立发布和宣发预备
- 全量代码 review
- 完善 QA 产品测试覆盖
- 定义性能标准
- 单元测试和检查规范

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

*最后更新: 2026-02-27 (v0.8.0)*
