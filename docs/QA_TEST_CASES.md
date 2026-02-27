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

### TC-INSIGHT-010: CLI insight bookmark/unbookmark/trace
- **关联**: v0.7.0
- **前置**: 至少 1 条沉淀
- **步骤**:
  1. `vibecollab insight bookmark INS-001`
  2. `vibecollab insight bookmark INS-001`（重复收藏）
  3. `vibecollab insight unbookmark INS-001`
  4. `vibecollab insight trace INS-001 [--json]`
- **预期**:
  - bookmark: 收藏成功，重复收藏提示已存在
  - unbookmark: 取消收藏成功
  - trace: 显示 ASCII 溯源树（上游 + 本节点 + 下游）
- **状态**: 🟢 (9 unit tests 覆盖)

### TC-INSIGHT-011: CLI insight who/stats（跨 Developer 共享）
- **关联**: v0.7.0
- **前置**: 多开发者环境 + 至少 1 条沉淀
- **步骤**:
  1. `vibecollab insight who INS-001 [--json]`
  2. `vibecollab insight stats [--json]`
- **预期**:
  - who: 显示创建者/使用者/收藏者/贡献者
  - stats: 汇总沉淀总数、开发者总数、使用次数、最常使用/最多共享
- **状态**: 🟢 (6 unit tests 覆盖)

---

## Phase 5 测试用例 (v0.7.1 — Task-Insight 自动关联)

### TC-TASKINS-001: Task 创建自动关联 Insight
- **关联**: v0.7.1
- **前置**: InsightManager 有已创建的 Insight
- **步骤**:
  1. 创建 `TaskManager(project_root, event_log, insight_manager=im)`
  2. `create_task(id=..., feature="重构缓存层", description="优化性能")`
- **预期**:
  - 自动从 feature/description 提取搜索标签
  - Jaccard × weight 匹配相关 Insight
  - 结果存入 `task.metadata["related_insights"]`
  - EventLog 记录关联信息
- **状态**: 🟢 (unit test 覆盖, 28 tests)

### TC-TASKINS-002: Task Suggest 推荐
- **关联**: v0.7.1
- **前置**: 已有 Task + Insight 数据
- **步骤**:
  1. `vibecollab task suggest TASK-001`
- **预期**:
  - 显示推荐的关联 Insight 列表
  - 按匹配分数排序
- **状态**: 🟢 (unit test 覆盖)

### TC-TASKINS-003: 向后兼容（无 InsightManager）
- **关联**: v0.7.1
- **前置**: 未初始化 InsightManager
- **步骤**:
  1. 创建 `TaskManager(project_root, event_log)` (无 insight_manager)
  2. `create_task(id=..., feature=...)`
- **预期**:
  - 正常创建 Task，不抛异常
  - `metadata["related_insights"]` 为空列表
- **状态**: 🟢 (unit test 覆盖)

---

## Phase 6 测试用例 (v0.8.0 — Config 配置管理 + 质量加固)

### TC-CONFIG-001: Config Setup 交互式向导
- **关联**: v0.8.0
- **前置**: 已安装 vibe-collab
- **步骤**:
  1. 运行 `vibecollab config setup`
  2. 选择 Provider / 输入 API Key / 选择 Base URL
- **预期**:
  - 配置写入 `~/.vibecollab/config.yaml`
  - API Key 安全存储
- **状态**: 🟢 (unit test 覆盖, 38 tests)

### TC-CONFIG-002: Config Show 查看配置
- **关联**: v0.8.0
- **前置**: 已有配置
- **步骤**:
  1. 运行 `vibecollab config show`
- **预期**:
  - 显示三层合并结果
  - 标识每项的来源（env/config/default）
  - API Key 遮蔽显示
- **状态**: 🟢 (unit test 覆盖)

### TC-CONFIG-003: Config Set 单项设置
- **关联**: v0.8.0
- **前置**: 已有配置文件
- **步骤**:
  1. 运行 `vibecollab config set llm.provider anthropic`
  2. 运行 `vibecollab config show` 验证
- **预期**:
  - 配置文件中对应键更新
  - show 输出反映新值
- **状态**: 🟢 (unit test 覆盖)

### TC-CONFIG-004: 三层配置优先级
- **关联**: v0.8.0
- **前置**: 同时设置环境变量和配置文件
- **步骤**:
  1. 设置 `VIBECOLLAB_LLM_PROVIDER=anthropic` 环境变量
  2. 配置文件设置 `llm.provider: openai`
  3. 调用 `resolve_llm_config()`
- **预期**:
  - 环境变量优先：结果为 anthropic
  - 优先级: env > config file > defaults
- **状态**: 🟢 (unit test 覆盖)

### TC-FLAKY-001: test_onboard_basic 稳定性
- **关联**: v0.8.0 Bug Fix
- **前置**: 全量测试环境
- **步骤**:
  1. 运行 `python -m pytest` 全量测试（连续 2 次）
- **预期**:
  - 779/779 passed
  - `test_onboard_basic` 不再因 `test_serve_lock_conflict` 污染而失败
- **状态**: 🟢 (已修复验证)

### TC-COV-001: 测试覆盖率 ≥ 80%
- **关联**: v0.8.0
- **前置**: 全量测试环境
- **步骤**:
  1. 运行 `python -m pytest --cov=vibecollab --cov-report=term`
- **预期**:
  - 总覆盖率 ≥ 80%（当前 81%）
  - 关键模块: git_utils 100%, extension 100%, llmstxt 97%, lifecycle 93%, cli_lifecycle 92%, templates 91%
- **状态**: 🟢

---

## Phase 7 测试用例 (v0.9.0 — 语义检索引擎)

### TC-INDEX-001: 文档索引（增量）
- **关联**: v0.9.0
- **前置**: 项目已初始化，存在 CONTRIBUTING_AI.md / CONTEXT.md / DECISIONS.md 等文档
- **步骤**:
  1. 运行 `vibecollab index`
  2. 检查 `.vibecollab/vectors/` 是否生成数据库文件
  3. 再次运行 `vibecollab index`
- **预期**:
  - 首次运行索引所有文档和 Insight YAML
  - 输出索引文档数和 chunk 数
  - 二次运行为增量更新（未变文件跳过）
- **状态**: ⚪ (待验证)

### TC-INDEX-002: 文档索引（重建）
- **关联**: v0.9.0
- **前置**: 已有索引数据
- **步骤**:
  1. 运行 `vibecollab index --rebuild`
- **预期**:
  - 清除旧索引后重建
  - 输出"清除旧索引"提示
  - 重建后搜索功能正常
- **状态**: ⚪ (待验证)

### TC-INDEX-003: 后端选择
- **关联**: v0.9.0
- **前置**: 已安装 vibe-collab
- **步骤**:
  1. 运行 `vibecollab index --backend pure_python`
  2. 运行 `vibecollab index --backend auto`（无 sentence-transformers 时自动降级）
- **预期**:
  - `pure_python` 使用 trigram 哈希 embedding（零外部依赖）
  - `auto` 未安装 sentence-transformers 时降级为 pure_python
  - 两种后端都能完成索引和后续搜索
- **状态**: ⚪ (待验证)

### TC-SEARCH-001: 全局语义搜索
- **关联**: v0.9.0
- **前置**: 已运行 `vibecollab index`
- **步骤**:
  1. 运行 `vibecollab search "协议检查"`
  2. 运行 `vibecollab search "决策记录" --type insight`
  3. 运行 `vibecollab search "task" --min-score 0.5`
- **预期**:
  - 返回按相关度排序的结果列表
  - 每条结果含来源（文档/Insight）和相关度评分
  - `--type` 过滤来源类型
  - `--min-score` 过滤低分结果
- **状态**: ⚪ (待验证)

### TC-SEARCH-002: Insight 语义搜索
- **关联**: v0.9.0
- **前置**: 已运行 `vibecollab index`，存在 Insight 数据
- **步骤**:
  1. 运行 `vibecollab insight search --semantic --tags "架构"`
- **预期**:
  - 基于向量余弦相似度搜索 Insight
  - 结果包含 ID / 标题 / 分数
- **状态**: ⚪ (待验证)

---

## Phase 8 测试用例 (v0.9.1 — MCP Server + AI IDE 集成)

### TC-MCP-001: MCP Server 启动 (stdio)
- **关联**: v0.9.1
- **前置**: `pip install vibe-collab[mcp]` 已安装 mcp 依赖
- **步骤**:
  1. 运行 `vibecollab mcp serve`
  2. 通过 stdin 发送 MCP initialize 请求
- **预期**:
  - Server 以 stdio 模式启动
  - 响应 MCP initialize 握手
  - 列出 14 个 Tools / 6 个 Resources / 1 个 Prompt
- **状态**: ⚪ (待验证)

### TC-MCP-002: MCP Config 输出
- **关联**: v0.9.1
- **前置**: 已安装 vibe-collab
- **步骤**:
  1. 运行 `vibecollab mcp config --ide cursor`
  2. 运行 `vibecollab mcp config --ide cline`
  3. 运行 `vibecollab mcp config --ide codebuddy`
- **预期**:
  - cursor: 输出 `.cursor/mcp.json` 格式的 JSON 配置
  - cline: 输出 Cline MCP 配置格式
  - codebuddy: 输出 `.codebuddy/mcp.json` 格式
  - 配置含正确的 command / args / env
- **状态**: ⚪ (待验证)

### TC-MCP-003: MCP Inject 自动注入
- **关联**: v0.9.1
- **前置**: 已安装 vibe-collab
- **步骤**:
  1. 运行 `vibecollab mcp inject --ide codebuddy`
  2. 检查 `.codebuddy/mcp.json` 文件
- **预期**:
  - 自动创建/合并 IDE 配置文件
  - 已有配置不被覆盖（merge 策略）
  - 注入 vibecollab MCP Server 配置
- **状态**: ⚪ (待验证)

### TC-MCP-004: MCP Tool — onboard
- **关联**: v0.9.1
- **前置**: MCP Server 运行中
- **步骤**:
  1. 调用 MCP tool `onboard`
- **预期**:
  - 返回项目概况、当前进度、活跃任务、最近事件、Insight 经验
  - 包含结构化的 JSON 数据
- **状态**: ⚪ (待验证)

### TC-MCP-005: MCP Tool — check
- **关联**: v0.9.1
- **前置**: MCP Server 运行中
- **步骤**:
  1. 调用 MCP tool `check`
- **预期**:
  - 返回协议检查报告
  - 包含 error / warning / info 统计
- **状态**: ⚪ (待验证)

### TC-MCP-006: MCP Tool — insight_search
- **关联**: v0.9.1
- **前置**: MCP Server 运行中，存在 Insight 数据
- **步骤**:
  1. 调用 MCP tool `insight_search` with tags="架构"
- **预期**:
  - 返回匹配的 Insight 列表
  - 按权重排序
- **状态**: ⚪ (待验证)

### TC-MCP-007: MCP Tool — search_docs
- **关联**: v0.9.1
- **前置**: MCP Server 运行中，已建立索引
- **步骤**:
  1. 调用 MCP tool `search_docs` with query="项目部署"
- **预期**:
  - 返回语义搜索结果
  - 含来源文件和评分
- **状态**: ⚪ (待验证)

### TC-MCP-008: MCP Resource 读取
- **关联**: v0.9.1
- **前置**: MCP Server 运行中
- **步骤**:
  1. 读取 Resource `contributing_ai`
  2. 读取 Resource `context`
  3. 读取 Resource `insights/list`
- **预期**:
  - 返回对应文档的完整内容
  - insights/list 返回所有 Insight 的 YAML 列表
- **状态**: ⚪ (待验证)

### TC-MCP-009: MCP Prompt — start_conversation
- **关联**: v0.9.1
- **前置**: MCP Server 运行中
- **步骤**:
  1. 调用 Prompt `start_conversation`
- **预期**:
  - 返回包含项目信息、CONTEXT 摘要、开发者上下文的系统 prompt
  - 列出可用的 14 个 MCP Tools
- **状态**: ⚪ (待验证)

---

## Phase 9 测试用例 (v0.9.2 ~ v0.9.3 — Insight 信号 + Task 工作流)

### TC-SIGNAL-001: Insight Suggest 候选推荐
- **关联**: v0.9.2
- **前置**: 项目有 git 提交历史
- **步骤**:
  1. 确保有若干 git commit（含 feat/fix/refactor 关键词）
  2. 运行 `vibecollab insight suggest --json`
- **预期**:
  - 从 git commit、文档变更、Task 变化中提取候选
  - 每个候选含 title / tags / confidence / source_signal
  - JSON 输出包含 candidates 数组
- **状态**: ⚪ (待验证)

### TC-SIGNAL-002: Insight Suggest 交互模式
- **关联**: v0.9.2
- **前置**: 存在候选 Insight
- **步骤**:
  1. 运行 `vibecollab insight suggest`
  2. 输入编号选择候选
- **预期**:
  - 列出候选 Insight
  - 选择后自动调用 `insight add` 创建
  - 信号快照更新
- **状态**: ⚪ (待验证)

### TC-SIGNAL-003: Insight Add 快照联动
- **关联**: v0.9.2
- **前置**: 项目已初始化
- **步骤**:
  1. 运行 `vibecollab insight add --title "测试" --tags test --category workflow --scenario "测试场景" --approach "测试方法"`
  2. 检查 `.vibecollab/insight_signal.json`
- **预期**:
  - Insight 创建成功
  - 信号快照自动更新（记录当前时间和 commit hash）
- **状态**: ⚪ (待验证)

### TC-SESSION-001: MCP Session Save
- **关联**: v0.9.2
- **前置**: MCP Server 运行中
- **步骤**:
  1. 调用 MCP tool `session_save` with summary="完成了功能X开发"
- **预期**:
  - Session 保存到 `.vibecollab/sessions/`
  - 返回 session ID
- **状态**: ⚪ (待验证)

### TC-TASK-CLI-001: Task Transition 状态推进
- **关联**: v0.9.3
- **前置**: 已有 Task 处于 TODO 状态
- **步骤**:
  1. `vibecollab task create --id TASK-QA-001 --role QA --feature "测试功能"`
  2. `vibecollab task transition TASK-QA-001 IN_PROGRESS`
  3. `vibecollab task transition TASK-QA-001 REVIEW`
  4. `vibecollab task list --json`
- **预期**:
  - 状态按 TODO → IN_PROGRESS → REVIEW 正确流转
  - 非法状态跳转被拒绝（如 TODO → DONE）
  - list 输出正确显示当前状态
- **状态**: ⚪ (待验证)

### TC-TASK-CLI-002: Task Solidify 固化
- **关联**: v0.9.3
- **前置**: Task 处于 REVIEW 状态
- **步骤**:
  1. `vibecollab task solidify TASK-QA-001`
- **预期**:
  - REVIEW → DONE 固化成功
  - 非 REVIEW 状态执行 solidify 被拒绝
  - EventLog 记录 solidify 事件
- **状态**: ⚪ (待验证)

### TC-TASK-CLI-003: Task Rollback 回滚
- **关联**: v0.9.3
- **前置**: Task 处于 IN_PROGRESS 或 REVIEW 状态
- **步骤**:
  1. `vibecollab task transition TASK-QA-001 IN_PROGRESS`
  2. `vibecollab task rollback TASK-QA-001 --reason "需要重新设计"`
- **预期**:
  - IN_PROGRESS → TODO 回滚成功
  - REVIEW → IN_PROGRESS 回滚成功
  - TODO 状态无法回滚
  - reason 记录到 EventLog
- **状态**: ⚪ (待验证)

### TC-ONBOARD-001: Onboard 命令全量输出
- **关联**: v0.9.3
- **前置**: 项目已初始化，有 Task 和 EventLog 数据
- **步骤**:
  1. 运行 `vibecollab onboard --json`
- **预期**:
  - JSON 包含: project_info / current_status / active_tasks / task_summary / recent_events / insights / related_insights
  - 活跃 Task 概览含 TODO/IN_PROGRESS/REVIEW 统计
  - 最近 EventLog 事件摘要
- **状态**: ⚪ (待验证)

### TC-NEXT-001: Next 命令行动建议
- **关联**: v0.9.3
- **前置**: 项目有多种待处理状态
- **步骤**:
  1. 创建若干 TODO 和 REVIEW 状态的 Task
  2. 运行 `vibecollab next --json`
- **预期**:
  - REVIEW 任务推荐 solidify（P1）
  - TODO 积压 >3 时触发提示（P2）
  - 建议按优先级排序
- **状态**: ⚪ (待验证)

---

## Phase 10 测试用例 (v0.9.4 — Insight 质量与生命周期)

### TC-DEDUP-001: Insight 自动去重检测
- **关联**: v0.9.4
- **前置**: 已有 Insight 数据
- **步骤**:
  1. 运行 `vibecollab insight add --title "已有的标题" --tags existing,tag --category workflow --scenario "..." --approach "..."`（与已有 Insight 标题/标签高度重叠）
- **预期**:
  - 检测到重复，输出相似 Insight 信息
  - 阻止创建，提示使用 `--force` 跳过
- **状态**: ⚪ (待验证)

### TC-DEDUP-002: Insight 强制创建（跳过去重）
- **关联**: v0.9.4
- **前置**: 去重检测会触发
- **步骤**:
  1. 运行 `vibecollab insight add --title "重复标题" --tags dup --category workflow --scenario "..." --approach "..." --force`
- **预期**:
  - 跳过去重检测
  - 成功创建 Insight
- **状态**: ⚪ (待验证)

### TC-GRAPH-001: Insight 关联图谱（文本）
- **关联**: v0.9.4
- **前置**: 存在多条 Insight（含 derived_from 关系）
- **步骤**:
  1. 运行 `vibecollab insight graph`
  2. 运行 `vibecollab insight graph --format json`
  3. 运行 `vibecollab insight graph --format mermaid`
- **预期**:
  - 默认文本: 显示节点/边/统计信息
  - JSON: 含 nodes / edges / stats（total_nodes / total_edges / isolated / components）
  - Mermaid: 输出 `graph LR` 语法，可粘贴到 Markdown 渲染
- **状态**: ⚪ (待验证)

### TC-EXPORT-001: Insight 导出
- **关联**: v0.9.4
- **前置**: 存在 Insight 数据
- **步骤**:
  1. 运行 `vibecollab insight export`（stdout）
  2. 运行 `vibecollab insight export -o insights_bundle.yaml`
  3. 运行 `vibecollab insight export --ids INS-001,INS-002`
  4. 运行 `vibecollab insight export --include-registry`
- **预期**:
  - 输出 YAML 格式的 Insight Bundle
  - `-o` 写入文件
  - `--ids` 选择性导出
  - `--include-registry` 包含注册表状态（weight/used_count/active）
- **状态**: ⚪ (待验证)

### TC-IMPORT-001: Insight 导入（skip 策略）
- **关联**: v0.9.4
- **前置**: 有导出的 YAML bundle 文件
- **步骤**:
  1. 导出 A 项目的 Insight: `vibecollab insight export -o bundle.yaml`
  2. 在 B 项目中导入: `vibecollab insight import bundle.yaml`
  3. 再次导入相同文件
- **预期**:
  - 首次导入成功，显示导入数量
  - 二次导入: 已存在的 ID 被 skip（默认策略）
  - 导入的 Insight 自动设置 `source.project` 标记来源
- **状态**: ⚪ (待验证)

### TC-IMPORT-002: Insight 导入（rename/overwrite 策略）
- **关联**: v0.9.4
- **前置**: 有导出的 YAML bundle 文件，目标项目已有同 ID Insight
- **步骤**:
  1. `vibecollab insight import bundle.yaml --strategy rename`
  2. `vibecollab insight import bundle.yaml --strategy overwrite`
- **预期**:
  - rename: 冲突 ID 自动分配新 ID (INS-xxx)
  - overwrite: 覆盖已有 Insight
- **状态**: ⚪ (待验证)

---

## Phase 11 — 端到端集成测试（外部项目全量验证）

> 以下用例用于在**非 VibeCollab 本身**的外部真实项目中验证完整工作流。

### TC-E2E-001: 全新项目初始化 + 生成 + 检查
- **关联**: 全版本
- **前置**: 一个已有代码的外部项目（含 Git）
- **步骤**:
  1. `cd /path/to/external-project`
  2. `pip install vibe-collab[mcp]`
  3. `vibecollab init -n "项目名" -d generic`
  4. `vibecollab generate -c project.yaml`
  5. `vibecollab check`
  6. `vibecollab health`
  7. `vibecollab health --json`
- **预期**:
  - init 生成 project.yaml + docs/ + .vibecollab/
  - generate 生成 CONTRIBUTING_AI.md + llms.txt
  - check 无 error（warning 可接受）
  - health 输出评分和信号
  - 无 Python traceback / 无 UnicodeEncodeError
- **状态**: ⚪ (待验证)

### TC-E2E-002: Insight 全链路（创建→搜索→衰减→导出→导入）
- **关联**: 全版本
- **前置**: 项目已 init
- **步骤**:
  1. `vibecollab insight add --title "缓存策略选型" --tags cache,architecture --category architecture --scenario "高并发场景" --approach "Redis + 本地二级缓存"`
  2. `vibecollab insight add --title "API 错误处理规范" --tags api,error-handling --category workflow --scenario "REST API" --approach "统一 ErrorResponse 结构"`
  3. `vibecollab insight list`
  4. `vibecollab insight search --tags cache`
  5. `vibecollab insight use INS-001`
  6. `vibecollab insight decay --dry-run`
  7. `vibecollab insight graph`
  8. `vibecollab insight export -o /tmp/insights_backup.yaml`
  9. `vibecollab insight check`
- **预期**:
  - 全链路无报错
  - search 返回匹配结果
  - use 后 weight 增加
  - decay --dry-run 不实际修改
  - graph 显示节点信息
  - export 输出有效 YAML
  - check 一致性校验通过
- **状态**: ⚪ (待验证)

### TC-E2E-003: Task 全链路（创建→推进→固化）
- **关联**: 全版本
- **前置**: 项目已 init
- **步骤**:
  1. `vibecollab task create --id TASK-DEV-001 --role DEV --feature "用户认证模块"`
  2. `vibecollab task list`
  3. `vibecollab task transition TASK-DEV-001 IN_PROGRESS`
  4. `vibecollab task transition TASK-DEV-001 REVIEW`
  5. `vibecollab task solidify TASK-DEV-001`
  6. `vibecollab task list --status DONE --json`
- **预期**:
  - 创建成功，list 显示 TODO 状态
  - 状态流转 TODO → IN_PROGRESS → REVIEW → DONE
  - solidify 后 list --status DONE 返回该 Task
  - --json 输出有效 JSON
- **状态**: ⚪ (待验证)

### TC-E2E-004: Onboard + Next 引导流程
- **关联**: 全版本
- **前置**: 项目有 Task 和 Insight 数据
- **步骤**:
  1. `vibecollab onboard`
  2. `vibecollab onboard --json`
  3. `vibecollab next`
  4. `vibecollab next --json`
- **预期**:
  - onboard: 显示项目概况、当前进度、活跃任务、Insight 概要
  - next: 显示行动建议（按优先级排序）
  - --json 输出有效 JSON
  - 无空项目报错（graceful handling）
- **状态**: ⚪ (待验证)

### TC-E2E-005: 索引 + 搜索 全链路
- **关联**: v0.9.0+
- **前置**: 项目已 init + generate
- **步骤**:
  1. `vibecollab index`
  2. `vibecollab search "项目概述"`
  3. `vibecollab search "决策" --type insight`
  4. `vibecollab insight search --semantic --tags "架构"`
- **预期**:
  - index 成功完成（纯 Python 降级方案可用）
  - search 返回结果含来源和评分
  - semantic 搜索返回 Insight
- **状态**: ⚪ (待验证)

### TC-E2E-006: MCP Server 端到端（CodeBuddy/Cursor 集成）
- **关联**: v0.9.1+
- **前置**: 已 `pip install vibe-collab[mcp]`
- **步骤**:
  1. `vibecollab mcp config --ide codebuddy`（确认输出格式）
  2. `vibecollab mcp inject --ide codebuddy`
  3. 在 CodeBuddy/Cursor 中重启，确认 MCP Server 连接
  4. 在 AI 对话中触发 `onboard` / `check` / `insight_search` tool
- **预期**:
  - config 输出有效 JSON
  - inject 生成正确配置文件
  - IDE 连接 MCP Server 成功
  - Tool 调用返回项目上下文
- **状态**: ⚪ (待验证)

### TC-E2E-007: Prompt 命令生成 LLM 上下文
- **关联**: v0.8.0+
- **前置**: 项目已 init + generate
- **步骤**:
  1. `vibecollab prompt`
  2. `vibecollab prompt --compact`
  3. `vibecollab prompt --sections protocol,context`
  4. `vibecollab prompt --copy`（Windows 验证）
- **预期**:
  - 输出 Markdown 格式的 LLM prompt
  - --compact 精简版省略路线图和角色定义
  - --sections 选择性输出
  - --copy 复制到剪贴板
- **状态**: ⚪ (待验证)

### TC-E2E-008: 跨项目 Insight 迁移
- **关联**: v0.9.4
- **前置**: 两个独立的 VibeCollab 项目
- **步骤**:
  1. 在项目 A: `vibecollab insight export -o /tmp/insights_a.yaml`
  2. 在项目 B: `vibecollab insight import /tmp/insights_a.yaml --json`
  3. 在项目 B: `vibecollab insight list`
  4. 在项目 B: `vibecollab insight check`
- **预期**:
  - 导出含 vibecollab_version / exported_at / insights 数组
  - 导入后 Insight 在 B 中可用
  - source.project 标记来源项目
  - 一致性校验通过
- **状态**: ⚪ (待验证)

### TC-E2E-009: Windows 兼容性验证
- **关联**: 全版本
- **前置**: Windows PowerShell/CMD 环境
- **步骤**:
  1. 运行以上所有 TC-E2E-001 ~ 008 的命令
  2. 特别关注含 emoji/中文/特殊字符的输出
- **预期**:
  - 所有命令无 UnicodeEncodeError
  - GBK 终端正确降级显示（emoji → ASCII 替代）
  - 路径分隔符正确处理
- **状态**: ⚪ (待验证)

### TC-E2E-010: 空项目/极简配置边界测试
- **关联**: 全版本
- **前置**: 空目录 + `vibecollab init`（最少参数）
- **步骤**:
  1. `mkdir empty-test && cd empty-test`
  2. `vibecollab init -n "EmptyProject" -d generic`
  3. `vibecollab check`
  4. `vibecollab onboard`
  5. `vibecollab next`
  6. `vibecollab task list`
  7. `vibecollab insight list`
  8. `vibecollab insight suggest --json`
- **预期**:
  - 所有命令 graceful 处理空数据
  - 无 traceback / 无 KeyError / 无 FileNotFoundError
  - 空列表返回友好提示而非报错
- **状态**: ⚪ (待验证)

---

## 已知问题

### 🔴 高优先级问题
(暂无)

### 🟡 中优先级问题
(暂无 — Windows GBK 兼容已通过 `_compat.py` 统一解决)

### ⚪ 低优先级问题（延后到 v1.0）
- 大项目（100+ 文件）生成速度可优化
- `cli_insight.py` / `cli_task.py` 尚未迁移到 Rich 输出风格（功能正常，仅视觉不一致）

---

*最后更新: 2026-02-27 (v0.9.4)*
