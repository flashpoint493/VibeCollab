# VibeCollab 测试用例手册

## 测试用例格式

```
### TC-{模块}-{序号}: {测试名称}
- **关联**: TASK-XXX
- **前置**: {前置条件}
- **步骤**:
  1. {步骤1}
  2. {步骤2}
- **预期**: {预期结果}
- **状态**: 🟢/🟡/🔴/⚪
```

## Phase 1 测试用例

### TC-CLI-001: 项目初始化
- **关联**: 核心功能
- **前置**: 已安装 vibe-collab
- **步骤**:
  1. 运行 `vibecollab init -n "TestProject" -d generic -o ./test-project`
  2. 检查生成的文件
- **预期**: 
  - 生成 CONTRIBUTING_AI.md
  - 生成 project.yaml
  - 生成 docs/ 目录及所有文档
  - 自动初始化 Git 仓库（如果可用）
- **状态**: 🟢

### TC-CLI-002: 生成协作规则文档
- **关联**: 核心功能
- **前置**: 存在 project.yaml 配置文件
- **步骤**:
  1. 运行 `vibecollab generate -c project.yaml`
  2. 检查生成的 CONTRIBUTING_AI.md
- **预期**: 
  - 生成完整的协作规则文档
  - 包含所有配置的章节
  - 自动集成 llms.txt（如果存在）
- **状态**: 🟢

### TC-CLI-003: llms.txt 集成
- **关联**: DECISION-002
- **前置**: 项目目录中已有 llms.txt
- **步骤**:
  1. 运行 `vibecollab generate -c project.yaml`
  2. 检查 llms.txt 文件
- **预期**: 
  - llms.txt 中添加 AI Collaboration 章节
  - 引用 CONTRIBUTING_AI.md
  - 不重复添加（多次运行）
- **状态**: 🟢

### TC-CLI-004: 创建新的 llms.txt
- **关联**: DECISION-002
- **前置**: 项目目录中没有 llms.txt
- **步骤**:
  1. 运行 `vibecollab generate -c project.yaml`
  2. 检查是否创建 llms.txt
- **预期**: 
  - 创建符合 llmstxt.org 标准的 llms.txt
  - 包含项目基本信息和 AI Collaboration 章节
- **状态**: 🟢

### TC-GIT-001: Git 自动初始化
- **关联**: DECISION-007
- **前置**: Git 已安装，项目目录不是 Git 仓库
- **步骤**:
  1. 运行 `vibecollab init -n "TestProject" -d generic -o ./test-project`
  2. 检查 .git 目录
- **预期**: 
  - 自动初始化 Git 仓库
  - 创建初始提交
  - 显示成功提示
- **状态**: 🟢

### TC-GIT-002: Git 检查提示
- **关联**: DECISION-007
- **前置**: Git 未安装或项目不是 Git 仓库
- **步骤**:
  1. 运行 `vibecollab generate -c project.yaml`
  2. 查看输出提示
- **预期**: 
  - 显示 Git 状态警告或提示
  - 建议初始化 Git 仓库
- **状态**: 🟢

### TC-LIFECYCLE-001: 项目生涯检查
- **关联**: DECISION-004
- **前置**: 项目已初始化，包含 lifecycle 配置
- **步骤**:
  1. 运行 `vibecollab lifecycle check`
  2. 查看输出信息
- **预期**: 
  - 显示当前阶段信息
  - 显示阶段重点和原则
  - 显示里程碑状态
  - 显示是否可以升级
- **状态**: 🟢

### TC-LIFECYCLE-002: 项目生涯升级
- **关联**: DECISION-004
- **前置**: 项目处于 demo 阶段，满足升级条件
- **步骤**:
  1. 运行 `vibecollab lifecycle upgrade`
  2. 检查 project.yaml 更新
  3. 检查阶段历史记录
- **预期**: 
  - 更新 current_stage 为 production
  - 添加新的阶段历史记录
  - 显示升级建议
- **状态**: 🟡 (需要手动测试)

### TC-ROADMAP-001: ROADMAP 包含阶段信息
- **关联**: DECISION-004
- **前置**: 项目已初始化
- **步骤**:
  1. 检查 docs/ROADMAP.md
  2. 查看阶段信息
- **预期**: 
  - 包含当前项目生涯阶段章节
  - 显示阶段重点和原则
  - 显示阶段历史
- **状态**: 🟢

### TC-CONTRIBUTING-001: CONTRIBUTING_AI.md 包含阶段化规则
- **关联**: DECISION-004
- **前置**: 项目已生成 CONTRIBUTING_AI.md
- **步骤**:
  1. 检查 CONTRIBUTING_AI.md
  2. 查找阶段化协作规则章节
- **预期**: 
  - 包含"阶段化协作规则"章节
  - 显示当前激活阶段
  - 列出所有阶段的规则
- **状态**: 🟢

### TC-UPGRADE-001: 协议升级命令
- **关联**: 核心功能
- **前置**: 存在旧版本的项目配置
- **步骤**:
  1. 运行 `vibecollab upgrade -c project.yaml`
  2. 检查配置合并结果
- **预期**: 
  - 保留用户自定义配置
  - 添加新的配置项
  - 重新生成 CONTRIBUTING_AI.md
- **状态**: 🟢

### TC-DOMAIN-001: 领域扩展加载
- **关联**: 核心功能
- **前置**: 使用领域模板初始化项目
- **步骤**:
  1. 运行 `vibecollab init -n "GameProject" -d game -o ./game-project`
  2. 检查生成的文档
- **预期**: 
  - 加载 game 领域扩展
  - 生成领域特定的章节
  - 包含领域特定的角色和流程
- **状态**: 🟢

## Phase 2 测试用例 (v0.5.5 ~ v0.5.8)

### TC-EVENTLOG-001: EventLog 追加与读取
- **关联**: v0.5.5
- **前置**: 项目已初始化
- **步骤**:
  1. 创建 `EventLog(project_root)`
  2. 调用 `event_log.append(Event(event_type=..., summary=..., actor=..., payload=...))`
  3. 调用 `event_log.read_all()`
- **预期**:
  - 事件持久化到 `.vibecollab/events.jsonl`
  - 读取返回所有已追加事件
- **状态**: 🟢 (unit test 覆盖)

### TC-TASK-001: TaskManager 生命周期
- **关联**: v0.5.6
- **前置**: 项目已初始化
- **步骤**:
  1. 创建 `TaskManager(project_root, event_log)`
  2. `create_task(id=..., role=..., feature=...)`
  3. `transition_task(id, "validate")` → `transition_task(id, "solidify")`
- **预期**:
  - Task 状态按 IN_PROGRESS→REVIEW→DONE 流转
  - 非法流转抛出异常
- **状态**: 🟢 (unit test 覆盖)

### TC-LLM-001: LLMClient 配置与调用
- **关联**: v0.5.7
- **前置**: 设置 `VIBECOLLAB_LLM_API_KEY` 环境变量
- **步骤**:
  1. 创建 `LLMConfig()` 读取环境变量
  2. 创建 `LLMClient(config)` 并调用 `client.ask("test")`
- **预期**:
  - 正确解析 provider/model/endpoint
  - API 调用返回响应 (或 mock 验证请求格式)
- **状态**: 🟢 (unit test 覆盖)

### TC-AI-001: AI Ask 单轮提问
- **关联**: v0.5.8
- **前置**: LLM 配置已设置
- **步骤**:
  1. 运行 `vibecollab ai ask "项目状态如何?"`
- **预期**:
  - 自动注入项目上下文
  - 返回 LLM 响应
  - 记录事件到 EventLog
- **状态**: 🟢 (unit test 覆盖)

### TC-AI-002: AI Chat 多轮对话
- **关联**: v0.5.8
- **前置**: LLM 配置已设置
- **步骤**:
  1. 运行 `vibecollab ai chat`
  2. 输入问题，查看回复
  3. 输入 "exit" 退出
- **预期**:
  - 保持对话历史
  - 支持 exit/quit/bye 退出
- **状态**: 🟢 (unit test 覆盖)

### TC-AI-003: Agent Plan 只读分析
- **关联**: v0.5.8
- **前置**: LLM 配置已设置
- **步骤**:
  1. 运行 `vibecollab ai agent plan`
- **预期**:
  - 输出行动计划
  - 不执行任何变更
- **状态**: 🟢 (unit test 覆盖)

### TC-AI-004: Agent Run 单周期执行
- **关联**: v0.5.8
- **前置**: LLM 配置已设置
- **步骤**:
  1. 运行 `vibecollab ai agent run`
  2. 运行 `vibecollab ai agent run --dry-run`
- **预期**:
  - 完成 Plan→Execute→Solidify 单周期
  - `--dry-run` 只输出计划不执行
  - pending-solidify 门控阻塞执行
- **状态**: 🟢 (unit test 覆盖)

### TC-AI-005: Agent Serve 安全门控
- **关联**: v0.5.8
- **前置**: LLM 配置已设置
- **步骤**:
  1. 运行 `vibecollab ai agent serve -n 1`
  2. 尝试同时运行第二个实例
- **预期**:
  - PID 锁阻止多实例
  - 最大周期数限制生效
  - RSS 内存阈值检查
  - 自适应退避 + 断路器
- **状态**: 🟢 (unit test 覆盖)

### TC-AI-006: Agent Status 状态查看
- **关联**: v0.5.8
- **前置**: 无特殊要求
- **步骤**:
  1. 运行 `vibecollab ai agent status`
- **预期**:
  - 显示 PID 锁状态
  - 显示 LLM 配置
  - 显示任务统计和最近事件
- **状态**: 🟢 (unit test 覆盖)

---

## Phase 3 测试用例 (v0.5.9)

### TC-PATTERN-001: PatternEngine 基础渲染
- **关联**: v0.5.9
- **前置**: 项目已初始化，存在 project.yaml
- **步骤**:
  1. 创建 `PatternEngine(config, project_root)`
  2. 调用 `engine.render()`
- **预期**:
  - 生成完整 CONTRIBUTING_AI.md 内容
  - 包含 manifest.yaml 中定义的所有启用章节
  - 章节顺序与 manifest 一致
- **状态**: 🟢 (unit test 覆盖)

### TC-PATTERN-002: Manifest 条件求值
- **关联**: v0.5.9
- **前置**: 配置中包含/不包含特定功能
- **步骤**:
  1. 配置 `protocol_check.enabled: false`
  2. 渲染文档
- **预期**:
  - 条件为 false 的章节不出现在输出中
  - `|default` 语法正确处理缺失配置 (默认启用)
- **状态**: 🟢 (unit test 覆盖)

### TC-PATTERN-003: Template Overlay 本地覆盖
- **关联**: v0.5.9
- **前置**: 项目中存在 `.vibecollab/patterns/` 目录
- **步骤**:
  1. 在 `.vibecollab/patterns/` 创建自定义模板
  2. 创建本地 `manifest.yaml` (override/insert/exclude)
  3. 渲染文档
- **预期**:
  - 本地模板优先于内置模板
  - manifest 合并正确: 覆盖、after 定位插入、exclude 排除
  - `list_patterns()` 正确标注 source: "local" / "builtin"
- **状态**: 🟢 (unit test 覆盖, 8 overlay tests)

### TC-PATTERN-004: 外部项目兼容性
- **关联**: v0.5.9
- **前置**: 使用非 VibeCollab 项目的 project.yaml
- **步骤**:
  1. 使用 test-project 的 project.yaml 配置
  2. 渲染 CONTRIBUTING_AI.md
- **预期**:
  - 正确处理缺失的配置项 (lifecycle, multi_developer 等)
  - 输出比 legacy 更完整 (DEFAULT_STAGES 回退, |true 默认)
- **状态**: 🟢 (test_generate_full_config 验证)

### TC-PATTERN-005: Legacy 移除兼容性
- **关联**: v0.5.9
- **前置**: 使用 generator.py 的 public API
- **步骤**:
  1. `generator = LLMContextGenerator.from_file(path)`
  2. `output = generator.generate()`
- **预期**:
  - API 不变，调用方无需修改
  - 输出由 PatternEngine 生成
  - cli.py, project.py 等调用方正常工作
- **状态**: 🟢 (unit test 覆盖)

### TC-HEALTH-001: HealthExtractor 基础提取
- **关联**: v0.5.9
- **前置**: 项目已初始化
- **步骤**:
  1. 创建 `HealthExtractor(project_root, config)`
  2. 调用 `extractor.extract()`
- **预期**:
  - 返回 `HealthReport`，包含 signals 列表、score (0-100)、summary
  - 从 ProtocolChecker / EventLog / TaskManager 三个数据源提取信号
- **状态**: 🟢 (unit test 覆盖, 32 tests)

### TC-HEALTH-002: 健康评分与分级
- **关联**: v0.5.9
- **前置**: HealthReport 包含不同级别的信号
- **步骤**:
  1. 构造包含 CRITICAL / WARNING / INFO 信号的 report
  2. 计算评分
- **预期**:
  - CRITICAL -25 分, WARNING -10 分, INFO 不扣分
  - 评分下限为 0，上限为 100
  - 分级: A(90+) / B(80+) / C(70+) / D(60+) / F(<60)
- **状态**: 🟢 (unit test 覆盖, 10 scoring tests)

### TC-HEALTH-003: 健康检查 CLI 命令
- **关联**: v0.5.9
- **前置**: 项目已初始化
- **步骤**:
  1. 运行 `vibecollab health`
  2. 运行 `vibecollab health --json`
- **预期**:
  - 显示健康评分和信号列表
  - `--json` 输出 JSON 格式
- **状态**: 🟢 (unit test 覆盖)

### TC-EXECUTOR-001: AgentExecutor JSON 解析
- **关联**: v0.5.9
- **前置**: LLM 返回包含 JSON 代码块的文本
- **步骤**:
  1. 创建 `AgentExecutor(project_root)`
  2. 调用 `executor.parse_changes(llm_output)`
- **预期**:
  - 支持三种 JSON 格式: 单对象、数组、`{"changes": [...]}`
  - 从 markdown ```json 块中提取
  - 返回 `FileChange` 列表
- **状态**: 🟢 (unit test 覆盖, 9 parse tests)

### TC-EXECUTOR-002: AgentExecutor 安全校验
- **关联**: v0.5.9
- **前置**: 变更列表包含路径遍历或受保护文件
- **步骤**:
  1. 提交包含 `../` 路径遍历的变更
  2. 提交针对 `.git/` 等受保护文件的变更
  3. 超过 MAX_FILES_PER_CYCLE 的变更
- **预期**:
  - 路径遍历被拒绝
  - 受保护文件 (.git/, .env, project.yaml, pyproject.toml) 被拒绝
  - 超限变更被拒绝
- **状态**: 🟢 (unit test 覆盖, 5 validation tests)

### TC-EXECUTOR-003: AgentExecutor 完整周期
- **关联**: v0.5.9
- **前置**: LLM 输出有效变更
- **步骤**:
  1. 调用 `executor.execute_full_cycle(llm_output, commit_message, test_command)`
- **预期**:
  - Parse → Validate → Apply → Test → Commit 完整流程
  - 测试失败时自动回滚
  - 成功时返回 git hash
- **状态**: 🟢 (unit test 覆盖, 5 full cycle tests)

### TC-EXECUTOR-004: Agent Run 实际执行集成
- **关联**: v0.5.9
- **前置**: LLM 配置已设置
- **步骤**:
  1. 运行 `vibecollab ai agent run`
  2. LLM 返回 JSON 变更计划
- **预期**:
  - AgentExecutor 解析并执行变更
  - 测试通过后自动 git commit
  - 失败时回滚并报告错误
- **状态**: 🟢 (unit test 覆盖)

---

## Phase 4 测试用例 (v0.7.0 — Insight 沉淀系统)

### TC-INSIGHT-001: InsightManager CRUD
- **关联**: v0.7.0
- **前置**: 项目已初始化
- **步骤**:
  1. 创建 `InsightManager(project_root)`
  2. `create(title=..., tags=[...], category=..., body={...}, created_by=...)`
  3. `get(insight_id)`, `list_all()`, `update(insight_id, ...)`, `delete(insight_id, ...)`
- **预期**:
  - 沉淀文件持久化到 `.vibecollab/insights/INS-xxx.yaml`
  - 注册表自动维护 `registry.yaml`
  - 所有操作记录 EventLog 审计事件
- **状态**: 🟢 (11 unit tests 覆盖)

### TC-INSIGHT-002: Registry 权重衰减与使用奖励
- **关联**: v0.7.0
- **前置**: 至少 1 条沉淀已创建
- **步骤**:
  1. `record_use(insight_id, used_by=...)` — 使用奖励
  2. `apply_decay()` — 权重衰减
  3. `get_active_insights()` — 查看活跃列表
- **预期**:
  - 使用后 weight +0.1, used_count +1
  - 衰减后 weight *= 0.95
  - weight < 0.1 时自动 active=false
- **状态**: 🟢 (8 unit tests 覆盖)

### TC-INSIGHT-003: Tag 搜索 (Jaccard × 权重)
- **关联**: v0.7.0
- **前置**: 多条不同 tag 的沉淀
- **步骤**:
  1. `search_by_tags(["python", "refactor"])`
  2. `search_by_category("workflow")`
- **预期**:
  - 按 Jaccard 相似度 × 注册表权重排序
  - 无匹配返回空列表
- **状态**: 🟢 (6 unit tests 覆盖)

### TC-INSIGHT-004: 溯源 derived_from
- **关联**: v0.7.0
- **前置**: 存在派生关系的沉淀
- **步骤**:
  1. 创建 INS-001，再创建 INS-002 (derived_from: [INS-001])
  2. `get_derived_tree("INS-001")`
- **预期**:
  - derived_from 返回上游 ID
  - derived_by 返回下游 ID
- **状态**: 🟢 (3 unit tests 覆盖)

### TC-INSIGHT-005: 一致性校验 (5 项全量)
- **关联**: v0.7.0
- **前置**: 沉淀系统已有数据
- **步骤**:
  1. `check_consistency()`
  2. 构造各种不一致场景测试
- **预期**:
  - 注册表↔文件双向一致性检查
  - derived_from 引用完整性检查
  - Developer metadata 引用完整性检查
  - SHA-256 指纹一致性检查
  - 低权重活跃沉淀发出警告
- **状态**: 🟢 (7 unit tests 覆盖)

### TC-INSIGHT-006: Developer Tag 扩展
- **关联**: v0.7.0
- **前置**: Developer metadata 已初始化
- **步骤**:
  1. `dm.set_tags(["arch", "python"], "alice")`
  2. `dm.add_contributed("INS-001", "alice")`
  3. `dm.add_bookmark("INS-002", "alice")`
- **预期**:
  - tags/contributed/bookmarks 正确写入 .metadata.yaml
  - 不影响已有的 developer/created_at/total_updates 字段
  - 去重：重复添加返回 False
- **状态**: 🟢 (21 unit tests 覆盖)

### TC-INSIGHT-007: CLI insight list/show/add/search
- **关联**: v0.7.0
- **前置**: 项目已初始化
- **步骤**:
  1. `vibecollab insight list [--active-only] [--json]`
  2. `vibecollab insight show INS-001`
  3. `vibecollab insight add --title ... --tags ... --category ... --scenario ... --approach ...`
  4. `vibecollab insight search --tags python`
- **预期**:
  - list: 正确列出/过滤/JSON 输出
  - show: 显示详情含 body、registry 状态
  - add: 创建并记录 contributed
  - search: 匹配并按权重排序
- **状态**: 🟢 (12 unit tests 覆盖)

### TC-INSIGHT-008: CLI insight use/decay/check/delete
- **关联**: v0.7.0
- **前置**: 至少 1 条沉淀
- **步骤**:
  1. `vibecollab insight use INS-001`
  2. `vibecollab insight decay [--dry-run]`
  3. `vibecollab insight check [--json]`
  4. `vibecollab insight delete INS-001 -y`
- **预期**:
  - use: 权重奖励 +0.1
  - decay: 衰减或预览
  - check: 一致性校验报告
  - delete: 删除文件和注册表条目
- **状态**: 🟢 (9 unit tests 覆盖)

### TC-INSIGHT-009: vibecollab check --insights 集成
- **关联**: v0.7.0
- **前置**: 项目已初始化
- **步骤**:
  1. 运行 `vibecollab check --insights`
- **预期**:
  - 协议检查 + Insight 一致性校验联合执行
  - 合并统计错误/警告数
  - Insight 错误计入退出码
- **状态**: 🟢 (需手动验证)

---

## 已知问题

### 🔴 高优先级问题
(暂无)

### 🟡 中优先级问题
- Windows 控制台编码问题（GBK）导致某些 Unicode 字符显示异常
  - 影响: twine upload 时的进度条显示
  - 状态: 已通过 --disable-progress-bar 缓解

### ⚪ 低优先级问题
- 大项目生成速度可能较慢
- 配置验证错误提示可以更详细

---

*最后更新: 2026-02-25 (v0.7.0-dev)*
