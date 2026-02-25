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

### v0.7.0 - Insight 沉淀系统（已完成）
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

### v0.7.1 - Task-Insight 自动关联（开发中）
- [x] TaskManager.create_task() 自动搜索关联 Insight ✅
- [x] _extract_search_tags(): 从 feature/description/role 提取关键词 ✅
- [x] _find_related_insights(): Jaccard × weight 匹配 + metadata 存储 ✅
- [x] suggest_insights(): 已有任务的 Insight 推荐 ✅
- [x] CLI `vibecollab task create/list/show/suggest` ✅
- [x] EventLog 记录关联 Insight ✅
- [x] 向后兼容（无 InsightManager 时自动跳过）✅
- [x] 28 个单元测试（含 CLI + 集成 + 向后兼容）✅

### v1.0.0 - 正式版（待规划）
- [ ] 文档完善和中英文支持
- [ ] 完整的教程和示例
- [ ] 社区反馈整合
- [ ] 性能和稳定性达到生产级别

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

*最后更新: 2026-02-25 (v0.7.1-dev)*
