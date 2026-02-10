"""
LLMContext Generator - 文档生成器
"""

import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

from .extension import ExtensionProcessor
from .lifecycle import LifecycleManager


class LLMContextGenerator:
    """AI 协作协议文档生成器"""

    def __init__(self, config: Dict[str, Any], project_root: Optional[Path] = None):
        self.config = config
        self.sections: List[str] = []
        self.project_root = project_root or Path.cwd()
        
        # 初始化扩展处理器
        self.extension_processor = ExtensionProcessor(self.project_root)
        self._load_extensions()

    def _load_extensions(self):
        """加载扩展配置"""
        # 从 domain_extensions 加载
        if "domain_extensions" in self.config:
            self.extension_processor.load_from_config(self.config)
        
        # 从独立扩展文件加载（如果指定）
        ext_files = self.config.get("extension_files", [])
        for ext_file in ext_files:
            ext_path = self.project_root / ext_file
            if ext_path.exists():
                import yaml as yaml_
                with open(ext_path, "r", encoding="utf-8") as f:
                    ext_data = yaml_.safe_load(f)
                self.extension_processor.load_from_config(ext_data)

    @classmethod
    def from_file(cls, path: Path, project_root: Optional[Path] = None) -> "LLMContextGenerator":
        """从文件加载配置"""
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        root = project_root or path.parent
        return cls(config, root)

    def validate(self) -> List[str]:
        """验证配置，返回错误列表"""
        errors = []
        
        # 检查必需字段
        if "project" not in self.config:
            errors.append("缺少 'project' 配置")
        else:
            project = self.config["project"]
            if "name" not in project:
                errors.append("缺少 'project.name'")
        
        # 检查角色定义
        roles = self.config.get("roles", [])
        for i, role in enumerate(roles):
            if "code" not in role:
                errors.append(f"角色 {i} 缺少 'code'")
            if "name" not in role:
                errors.append(f"角色 {i} 缺少 'name'")
        
        # 检查决策级别
        levels = self.config.get("decision_levels", [])
        valid_levels = {"S", "A", "B", "C"}
        for level in levels:
            if level.get("level") not in valid_levels:
                errors.append(f"无效的决策级别: {level.get('level')}")
        
        return errors

    def generate(self) -> str:
        """生成完整的 CONTRIBUTING_AI.md 文档"""
        self.sections = []
        
        self._add_header()
        self._add_philosophy()
        self._add_roles()
        self._add_decision_levels()
        self._add_task_unit()
        self._add_dialogue_protocol()
        self._add_requirement_clarification()  # 新增：需求澄清协议
        self._add_iteration_protocols()
        self._add_qa_protocol()
        self._add_git_workflow()
        self._add_testing()
        self._add_milestone()
        self._add_iteration()
        self._add_lifecycle_rules()
        self._add_documentation()
        self._add_multi_developer_protocol()  # 新增：多开发者协作协议
        self._add_prompt_engineering()
        self._add_symbology()
        self._add_decisions_summary()
        self._add_extension_sections()
        self._add_protocol_check()
        self._add_prd_management()
        self._add_quick_reference()
        self._add_changelog()
        self._add_git_history_reference()
        self._add_footer()

        return "\n".join(self.sections)

    def _add_header(self):
        """添加文档头部"""
        project = self.config.get("project", {})
        self.sections.append(f"""# {project.get('name', 'Project')} AI 协作开发规则
## LLM Collaboration Protocol {project.get('version', 'v1.0')}

---
""")

    def _add_philosophy(self):
        """添加核心理念章节"""
        philosophy = self.config.get("philosophy", {})
        vibe = philosophy.get("vibe_development", {})
        decision_quality = philosophy.get("decision_quality", {})

        content = """# 一、核心理念

## 1.1 Vibe Development 哲学

> **最珍贵的是对话过程本身，不追求直接出结果，而是步步为营共同规划。**

本项目采用 **Vibe Development** 模式：
"""
        if vibe.get("enabled", True):
            for principle in vibe.get("principles", []):
                content += f"- {principle}\n"

        target_rate = decision_quality.get('target_rate', 0.9)
        content += f"""
## 1.2 决策质量观

> **大量决策，{int(target_rate * 100)}% 正确率，关键决策零失误**

项目是一系列决策的集合：
- 只有做对 {int(target_rate * 100)}% 以上的决策，项目才有望成功
- 关键决策容错数: {decision_quality.get('critical_tolerance', 0)}
- 因此每个 S/A 级决策都需要 **人机共同 Review**
"""

        if philosophy.get("long_term_dialogue", True):
            content += """
## 1.3 长期对话工程观

这是一个**长期对话工程**，不是一次性任务：
- 对话是连续的，上下文需要被**持久化保存**
- 每次对话都在前次基础上**迭代推进**
- Git 提交历史记录了**思维演进过程**
- CONTRIBUTING_AI.md 是**活文档**，随项目成长
"""

        content += "\n---\n"
        self.sections.append(content)

    def _add_roles(self):
        """添加职能角色定义章节"""
        roles = self.config.get("roles", [])

        content = """# 二、职能角色定义

本项目模拟多职能协作，AI 在对话中切换不同角色视角：

| 角色代号 | 职能 | 关注点 | 触发词 |
|---------|------|--------|--------|
"""
        for role in roles:
            code = role.get("code", "")
            name = role.get("name", "")
            focus = "、".join(role.get("focus", []))
            triggers = "、".join([f'"{t}"' for t in role.get("triggers", [])])
            content += f"| `[{code}]` | {name} | {focus} | {triggers} |\n"

        content += """
**使用方式**: 在对话中明确指定角色，或让 AI 自动识别并标注当前角色视角。
"""

        # 找出守门人角色
        gatekeepers = [r for r in roles if r.get("is_gatekeeper", False)]
        for gk in gatekeepers:
            content += f"""
## 2.2 {gk.get('code', '')} 角色的特殊地位

> **{gk.get('code', '')} 是每个功能的最后守门人，无验收则不算完成**

{gk.get('code', '')} 职能贯穿整个开发流程：
- **开发前**: 参与需求评审，提出测试视角问题
- **开发中**: 准备测试用例框架
- **开发后**: 执行验收测试，确认功能符合预期
"""

        content += "\n---\n"
        self.sections.append(content)

    def _add_decision_levels(self):
        """添加决策分级制度章节"""
        levels = self.config.get("decision_levels", [])

        content = """# 三、决策分级制度

## 3.1 决策等级

| 等级 | 类型 | 影响范围 | Review 要求 |
|-----|------|---------|------------|
"""
        for level in levels:
            l = level.get("level", "")
            name = level.get("name", "")
            scope = level.get("scope", "")
            review = level.get("review", {})
            review_desc = self._format_review_requirement(review)
            content += f"| **{l}** | {name} | {scope} | {review_desc} |\n"

        content += """
## 3.2 决策记录格式

```markdown
## DECISION-{序号}: {标题}
- **等级**: S/A/B/C
- **角色**: [角色代号]
- **问题**: {需要决策的问题}
- **选项**: 
  - A: {选项A}
  - B: {选项B}
- **决策**: {最终选择}
- **理由**: {为什么这么选}
- **日期**: {YYYY-MM-DD}
- **状态**: PENDING / CONFIRMED / REVISED
```

---
"""
        self.sections.append(content)

    def _format_review_requirement(self, review: Dict) -> str:
        """格式化 Review 要求描述"""
        if not review.get("required", False):
            if review.get("mode") == "auto":
                return "AI 提出建议，人工可快速确认或默认通过"
            return "AI 自主决策，事后可调整"
        
        if review.get("mode") == "sync":
            return "必须人工确认，记录决策理由"
        elif review.get("mode") == "async":
            return "人工Review，可异步确认"
        return "需要 Review"

    def _add_task_unit(self):
        """添加任务单元定义章节"""
        task_unit = self.config.get("task_unit", {})

        content = f"""# 四、开发流程协议

## 4.1 任务单元定义

开发不按日期，按 **对话任务单元** 推进：

```
任务单元 (Task Unit):
├── ID: {task_unit.get('id_pattern', 'TASK-{role}-{seq}')}
"""
        for field in task_unit.get("required_fields", []):
            if field != "id":
                content += f"├── {field}\n"

        statuses = task_unit.get('statuses', ['TODO', 'IN_PROGRESS', 'REVIEW', 'DONE'])
        content += f"""└── 状态: {' / '.join(statuses)}
```
"""
        self.sections.append(content)

    def _add_dialogue_protocol(self):
        """添加对话流程协议章节"""
        protocol = self.config.get("dialogue_protocol", {})
        on_start = protocol.get("on_start", {})
        on_end = protocol.get("on_end", {})
        flow = protocol.get("standard_flow", [])

        content = """## 4.2 标准对话流程

### 4.2.0 对话开始时（强制）

> **每次新对话开始，AI 必须先恢复当前状态**

```
"""
        for i, f in enumerate(on_start.get("read_files", []), 1):
            content += f"{i}. 读取 {f}\n"
        for action in on_start.get("actions", []):
            content += f"{len(on_start.get('read_files', [])) + 1}. {action}\n"

        content += """```

**项目初始化约束**：
- 如果是新项目且没有 `.git` 目录，必须执行 `git init` 初始化 Git 仓库
- 初始化后立即执行首次提交：`git add -A && git commit -m "init: 项目初始化"`
- Git 是协作记录的基础，没有 Git 无法进行有效的版本追踪

### 4.2.1 对话结束时（强制）

> **每次对话结束前，AI 必须保存当前状态**

```
"""
        for i, f in enumerate(on_end.get("update_files", []), 1):
            content += f"{i}. 更新 {f}\n"
        if on_end.get("git_commit", True):
            content += f"{len(on_end.get('update_files', [])) + 1}. Git commit → 记录对话成果\n"

        content += """```

### 4.2.2 标准对话中流程

```
"""
        for step in flow:
            actor = "[人]" if step.get("actor") == "human" else "[AI]"
            action = step.get("action", "")
            condition = step.get("condition", "")
            line = f"{step.get('step', '')}. {actor} {action}"
            if condition:
                line += f" ← 条件: {condition}"
            content += f"{line}\n       ↓\n"

        content = content.rstrip("       ↓\n") + "\n```\n"
        self.sections.append(content)

    def _add_requirement_clarification(self):
        """添加需求澄清协议章节"""
        req_clarify = self.config.get("requirement_clarification", {})
        
        if not req_clarify.get("enabled", True):
            return
        
        content = """## 4.2.3 需求澄清协议（重要）

> **用户提出需求时可能是自然无意识的，AI 必须将模糊描述转化为结构化需求**

**触发条件**: 用户提出的需求存在以下情况
- 描述模糊或不完整
- 缺少具体的验收标准
- 可能有多种理解方式
- 涉及 S/A 级决策

**澄清流程**:
```
1. [AI] 识别用户意图，提取关键信息
2. [AI] 转化为结构化需求描述
3. [AI] 列出假设和待确认项
4. [人] 确认/修正/补充
5. [AI] 形成最终需求文档
```

**结构化需求模板**:

```markdown
## 需求: {需求标题}

**原始描述**: 
> {用户原话}

**需求分析**:
- 目标: {要达成什么}
- 场景: {在什么情况下使用}
- 用户: {谁会使用}

**功能要求**:
1. {具体功能点1}
2. {具体功能点2}

**验收标准**:
- [ ] {可验证的标准1}
- [ ] {可验证的标准2}

**待确认项**:
- [ ] {需要用户确认的假设1}
- [ ] {需要用户确认的假设2}

**决策等级**: {S/A/B/C}
**预估复杂度**: {高/中/低}
```

**快速澄清问句**:
- "你希望达到什么效果？"
- "有没有参考案例？"
- "这个功能谁会用？在什么场景下用？"
- "如何验证这个功能是否完成？"
- "有时间或资源约束吗？"

**示例**:

用户说: "加个导出功能"

AI 澄清后:
```markdown
## 需求: 数据导出功能

**原始描述**: 
> 加个导出功能

**需求分析**:
- 目标: 将系统数据导出为文件，便于备份或分享
- 场景: 用户需要离线查看或迁移数据时
- 用户: 所有用户

**功能要求**:
1. 支持导出为 JSON 格式
2. 支持导出为 CSV 格式（如有表格数据）
3. 导出文件包含时间戳命名

**验收标准**:
- [ ] 点击导出按钮后生成文件
- [ ] 文件可被其他工具正常打开
- [ ] 导出内容完整无丢失

**待确认项**:
- [ ] 需要导出哪些数据？全部还是部分？
- [ ] 是否需要导出格式选择？
- [ ] 文件大小有限制吗？

**决策等级**: B
**预估复杂度**: 中
```

"""
        self.sections.append(content)

    def _add_iteration_protocols(self):
        """添加迭代相关协议章节"""
        iteration = self.config.get("iteration", {})
        build = self.config.get("build", {})
        version_review = self.config.get("version_review", {})
        
        content = """## 4.3 迭代建议管理协议（重要）

> **QA 测试中产生的迭代建议，必须经过 PM 评审后决定是否纳入当前里程碑**

**迭代建议来源**:
- QA 测试过程中的体验反馈
- 开发过程中发现的改进点
- 用户/人类的直接建议

**PM 评审流程**:
```
1. 收集 → 记录到 docs/ROADMAP.md "迭代建议池"
2. 评审 → 分析优先级、冲突、成本
3. 决策 → 纳入/延后/拒绝
4. 排期 → 确定开发顺序
5. 执行 → 转为 TASK
```

"""
        # 版本回顾协议
        if version_review.get("enabled", True):
            content += """## 4.4 版本回顾协议（重要）

> **每次新版本规划前，必须回顾上个版本的测试表现和用户反馈**

**回顾时机**: 里程碑验收完成后，开始下一阶段规划前

**回顾内容**:
```
1. 测试表现
   - 通过率、问题分布
   - 稳定性评估
   
2. 用户体验反馈
   - 核心功能验证结果
   - 操作体验、视觉体验
   
3. 技术债务
   - 已知问题表
   - 性能瓶颈
   
4. 迭代建议池
   - 上版本积累的建议
   - 优先级重新评估
```

**产出**:
- 补充新的需求到下一阶段
- 调整任务优先级
- 记录设计决策

"""

        # 构建打包协议
        if build.get("enabled", True):
            build_cmd = build.get("command", "npm run build")
            dist_entry = build.get("dist_entry", "dist/index.html")
            content += f"""## 4.5 构建打包协议（重要）

> **全量验收前必须完成打包流程，打包是开发的一环**

**构建时机**:
- ✅ 里程碑全量验收前
- ✅ Bug 修复期集中测试
- ✅ 准备分发/演示版本
- ❌ 不需要每次提交都构建

**全量验收前 CheckList**:
```
[ ] 1. {build_cmd}
[ ] 2. 双击 {dist_entry} 测试
[ ] 3. 确认正常运行
[ ] 4. 更新操作说明（如有新功能）
```

"""

        # 配置级迭代协议
        config_iter = iteration.get("config_level_iteration", {})
        if config_iter.get("enabled", True):
            content += f"""## 4.6 配置级迭代协议（重要）

> **仅修改数值配置、不改动代码逻辑的迭代，可快速执行**

**定义**: 配置级迭代 = 仅调整现有参数值，不增删代码逻辑

**可快速执行的配置示例**:
"""
            for ex in config_iter.get("examples", []):
                content += f"- {ex}\n"
            
            content += f"""
**执行规则**:
1. 用户明确指出"配置调整"或"数值修改"
2. AI 直接修改对应配置值
3. 无需 PM 审批，无需创建 TASK
4. commit 使用 `{config_iter.get('commit_prefix', '[CONFIG]')}` 前缀

**不适用情况** (需 PM 审核排期):
- 需要新增函数/类/文件
- 涉及系统交互逻辑变更
- 可能影响其他模块
- 用户不确定该改什么

"""
        self.sections.append(content)

    def _add_qa_protocol(self):
        """添加 QA 验收协议章节"""
        testing = self.config.get("testing", {})
        product_qa = testing.get("product_qa", {})
        quick_acceptance = self.config.get("quick_acceptance", {})
        
        if not product_qa.get("enabled", True):
            return
        
        content = f"""## 4.7 QA 验收协议（重要）

> **每个功能完成后，必须同步更新 QA 测试用例，供验收使用**

**QA 测试用例要素**:
- 测试 ID ({product_qa.get('case_id_pattern', 'TC-{module}-{seq}')})
- 关联功能 (TASK-ID)
- 前置条件
- 测试步骤 (可复现的操作序列)
- 预期结果 (明确、可验证)
- 测试状态

**开发者责任**:
1. 功能完成时，在 `{product_qa.get('test_case_file', 'docs/QA_TEST_CASES.md')}` 添加测试用例
2. 提供清晰的操作步骤和预期表现
3. 标注已知限制或边界情况

**QA 责任**:
1. 按测试用例执行验收测试
2. 记录实际结果和问题
3. 更新测试状态 (通过/部分通过/未通过)
4. **验收失败时**: 附上日志/截图
5. 提交 Bug 到已知问题表

## 4.8 快速验收回复模板

功能开发完成后，AI 必须提供**快速验收清单**，用户可直接复制回复：

```markdown
## 🧪 快速验收

**启动**: `{quick_acceptance.get('start_command', 'npm run dev')}`

**验收项**:
- [ ] 功能A: {{操作}} → {{预期}}
- [ ] 功能B: {{操作}} → {{预期}}
- [ ] 功能C: {{操作}} → {{预期}}

**快速回复** (复制修改后发送):
✅ 全部通过
或
⚠️ 问题: {{描述问题}}
```

**用户回复格式**:
- `✅` 或 `通过` - 全部验收通过，继续下一步
- `⚠️ 问题: xxx` - 有问题需要修复
- `跳过` - 暂不验收，先继续

"""
        self.sections.append(content)

    def _add_prompt_engineering(self):
        """添加 Prompt 工程最佳实践章节"""
        prompt_eng = self.config.get("prompt_engineering", {})
        
        if not prompt_eng.get("enabled", True):
            return
        
        roles = self.config.get("roles", [])
        role_templates = prompt_eng.get("role_templates", {})
        
        content = """# Prompt 工程最佳实践

## 有效提问模板

"""
        # 为每个角色生成模板
        for role in roles[:4]:  # 只取前4个主要角色
            code = role.get("code", "")
            name = role.get("name", "")
            template = role_templates.get(code, f"[{code}] 请帮我{{任务描述}}")
            content += f"""### {name}讨论
```
{template}
```

"""

        content += """### 问题诊断
```
[QA] 遇到问题: {问题描述}
复现步骤: {步骤}
期望行为: {期望}
实际行为: {实际}
```

## 高价值引导词

| 场景 | 引导词 |
|-----|-------|
| 深入分析 | "请从{角色}视角分析"、"有哪些我没考虑到的" |
| 方案对比 | "给出2-3个方案并对比优劣" |
| 风险评估 | "这个方案最大的风险是什么" |
| 简化问题 | "MVP版本最少需要什么" |
| 扩展思考 | "如果未来要支持{X}，现在要预留什么" |
| Vibe 对齐 | "你理解我的意图了吗"、"我们先对齐一下理解" |

## Vibe Development 沟通技巧

### 不要说
- "帮我写一个XXX" (太直接，跳过思考)
- "直接给我代码" (跳过设计讨论)

### 推荐说
- "我想和你讨论一下XXX的设计"
- "你觉得这个方案有什么问题"
- "我们先对齐一下理解，再动手"
- "这个决策你怎么看"
- "把你的思考过程告诉我"

---
"""
        self.sections.append(content)

    def _add_decisions_summary(self):
        """添加已确认决策汇总章节"""
        decisions = self.config.get("confirmed_decisions", [])
        
        content = """# 已确认决策汇总

"""
        if decisions:
            content += "| ID | 决策 | 选择 | 理由 |\n"
            content += "|----|------|------|------|\n"
            for d in decisions:
                content += f"| {d.get('id', '')} | {d.get('title', '')} | {d.get('choice', '')} | {d.get('reason', '')} |\n"
        else:
            content += "*暂无已确认决策，将在项目进行中记录*\n"
        
        content += "\n---\n"
        self.sections.append(content)

    def _add_changelog(self):
        """添加文档迭代日志章节"""
        changelog = self.config.get("contributing_ai_changelog", [])
        
        content = """# CONTRIBUTING_AI.md 迭代日志

| 版本 | 日期 | 变更内容 |
|-----|------|---------|
"""
        if changelog:
            for entry in changelog:
                content += f"| {entry.get('version', '')} | {entry.get('date', '')} | {entry.get('changes', '')} |\n"
        else:
            content += f"| v1.0 | {datetime.now().strftime('%Y-%m-%d')} | 初始版本 |\n"
        
        content += "\n---\n"
        self.sections.append(content)

    def _add_git_history_reference(self):
        """添加 Git 提交历史参考章节"""
        content = """# Git 提交历史参考

本项目的 Git 历史记录了完整的设计演进过程：

```bash
# 查看提交历史
git log --oneline

# 查看某次提交详情
git show <commit-hash>

# 查看文件变更历史
git log --follow -p <file>
```

---
"""
        self.sections.append(content)

    def _add_git_workflow(self):
        """添加 Git 工作流章节"""
        git = self.config.get("git_workflow", {})
        branches = git.get("branches", {})
        prefixes = git.get("commit_prefixes", [])

        content = f"""## 4.3 Git 协作规范

### 分支策略
```
{branches.get('main', 'main')}                 # 稳定版本
├── {branches.get('dev', 'dev')}              # 开发主线
│   ├── {branches.get('feature_prefix', 'feature/')}{{特性名}}     # 功能开发
│   ├── {branches.get('design_prefix', 'design/')}{{设计文档}}    # 设计迭代
│   ├── {branches.get('refactor_prefix', 'refactor/')}{{模块名}}    # 重构优化
│   └── {branches.get('fix_prefix', 'fix/')}{{问题描述}}       # Bug修复
```

### Commit 前缀
```
"""
        for p in prefixes:
            content += f"{p.get('prefix', '')}  {p.get('description', '')}\n"

        content += """```
"""

        if git.get("commit_required", True):
            content += """
### Git 提交要求（重要）

> **每次有效对话都必须产生 Git 提交，记录思维演进**

Git 历史不仅是代码版本，更是**设计思维的演进记录**。

---
"""
        self.sections.append(content)

    def _add_testing(self):
        """添加测试体系章节"""
        testing = self.config.get("testing", {})
        unit_test = testing.get("unit_test", {})
        product_qa = testing.get("product_qa", {})

        content = """# 五、测试体系

"""

        # 单元测试
        if unit_test.get("enabled", True):
            coverage = unit_test.get('coverage_target', 0.8)
            patterns = unit_test.get('patterns', ['**/*.test.ts'])
            run_on = unit_test.get('run_on', ['pre-commit', 'ci'])
            
            content += f"""## 5.1 单元测试 (Unit Test)

> **开发者视角：验证代码逻辑正确性**

| 配置项 | 值 |
|-------|-----|
| 测试框架 | {unit_test.get('framework', 'jest')} |
| 覆盖率目标 | {int(coverage * 100)}% |
| 文件模式 | {', '.join(patterns)} |
| 运行时机 | {', '.join(run_on)} |

**单元测试原则**:
- 每个模块应有对应的测试文件
- 关键函数必须有测试覆盖
- 测试应该独立、可重复
- Mock 外部依赖

"""

        # 产品QA
        if product_qa.get("enabled", True):
            content += f"""## 5.2 产品QA验收 (Product QA)

> **用户视角：验证功能符合预期**

**测试用例文件**: `{product_qa.get('test_case_file', 'docs/QA_TEST_CASES.md')}`

**用例ID格式**: `{product_qa.get('case_id_pattern', 'TC-{module}-{seq}')}`

**测试用例要素**:
"""
            for field in product_qa.get("required_fields", []):
                content += f"- {field}\n"

            content += "\n**测试状态**:\n"
            for status in product_qa.get("statuses", []):
                if isinstance(status, dict):
                    content += f"- {status.get('symbol', '')} {status.get('meaning', '')}\n"
                else:
                    content += f"- {status}\n"

        content += """
## 5.3 Unit Test vs Product QA 区别

| 维度 | Unit Test | Product QA |
|------|-----------|------------|
| 视角 | 开发者 | 用户 |
| 目标 | 代码正确性 | 功能完整性 |
| 粒度 | 函数/模块级 | 功能/流程级 |
| 执行 | 自动化 | 可自动+人工 |
| 时机 | 提交时 | 功能完成时 |
| 工具 | 测试框架 | 测试用例手册 |

---
"""
        self.sections.append(content)

    def _add_milestone(self):
        """添加里程碑章节"""
        milestone = self.config.get("milestone", {})
        lifecycle = milestone.get("lifecycle", [])
        priorities = milestone.get("bug_priority", [])

        content = """# 六、里程碑定义

## 6.1 里程碑规范

> **里程碑 = 多个特性 + Bug修复期 + 全量验收**

### 里程碑生命周期

```
┌─────────────────────────────────────────────────────────┐
│                   里程碑生命周期                          │
├─────────────────────────────────────────────────────────┤
"""
        for i, phase in enumerate(lifecycle):
            content += f"""│  {i + 1}. {phase.get('phase', '')} - {phase.get('description', '')}
"""
            for criteria in phase.get("exit_criteria", []):
                content += f"│     └── {criteria}\n"
            if i < len(lifecycle) - 1:
                content += "├─────────────────────────────────────────────────────────┤\n"

        content += """└─────────────────────────────────────────────────────────┘
```
"""

        if priorities:
            content += """
### Bug 优先级

| 优先级 | 描述 |
|-------|------|
"""
            for p in priorities:
                content += f"| {p.get('level', '')} | {p.get('description', '')} |\n"

        tag_pattern = milestone.get('tag_pattern', 'v{major}.{minor}.{patch}')
        content += f"""
### 里程碑 Tag

```bash
git tag -a {tag_pattern} -m "描述"
```

---
"""
        self.sections.append(content)

    def _add_iteration(self):
        """添加迭代管理章节"""
        iteration = self.config.get("iteration", {})
        suggestion_pool = iteration.get("suggestion_pool", {})
        config_iter = iteration.get("config_level_iteration", {})
        dimensions = iteration.get("review_dimensions", [])

        content = """# 七、迭代管理

## 7.1 迭代建议管理协议

> **迭代建议必须经过 PM 评审后决定是否纳入当前里程碑**

**决策分类**:
"""
        for cat in suggestion_pool.get("categories", []):
            content += f"- {cat.get('symbol', '')} {cat.get('meaning', '')}\n"

        if dimensions:
            content += "\n**评审维度**:\n"
            for dim in dimensions:
                content += f"- {dim}\n"

        if config_iter.get("enabled", True):
            content += f"""
## 7.2 配置级迭代协议

> **仅修改配置、不改动代码逻辑的迭代，可快速执行**

**执行规则**:
- 用户明确指出"配置调整"
- AI 直接修改对应配置值
- 无需 PM 审批，无需创建 TASK
- commit 使用 `{config_iter.get('commit_prefix', '[CONFIG]')}` 前缀

**适用示例**:
"""
            for ex in config_iter.get("examples", []):
                content += f"- {ex}\n"

        content += "\n---\n"
        self.sections.append(content)

    def _add_lifecycle_rules(self):
        """添加阶段化协作规则章节"""
        lifecycle_manager = LifecycleManager(self.config)
        all_stages = lifecycle_manager.lifecycle_config.get("stages", {})
        
        content = """# 八、阶段化协作规则

## 8.1 项目生涯阶段说明

项目开发过程分为 4 个生涯阶段，每个阶段有不同的开发重点和协作原则。阶段信息由 PM 角色在 `docs/ROADMAP.md` 中维护，AI 在协作时应根据当前阶段调整工作方式。

### 阶段类型定义

项目生涯阶段按顺序演进，每个阶段都有明确的定义和规则：

"""
        
        # 添加所有阶段的规则（作为类型定义，不标注当前状态）
        stage_order = ["demo", "production", "commercial", "stable"]
        for stage_code in stage_order:
            stage_data = all_stages.get(stage_code, {})
            if not stage_data:
                continue
            
            content += f"""### {stage_data.get('name', stage_code)} ({stage_code})

**描述**: {stage_data.get('description', '')}

**阶段重点**:
{chr(10).join(f"- {focus}" for focus in stage_data.get('focus', []))}

**阶段原则**:
{chr(10).join(f"- {principle}" for principle in stage_data.get('principles', []))}

"""
        
        content += """## 8.2 阶段化协作指导

AI 在协作时应：

1. **读取当前阶段**: 在对话开始时，读取 `docs/ROADMAP.md` 了解项目当前处于哪个阶段
2. **应用阶段规则**: 根据当前阶段的重点和原则调整工作方式
3. **关注阶段变化**: 当项目升级到新阶段时，注意新阶段的原则变化，调整协作方式
4. **阶段里程碑**: 关注当前阶段的里程碑完成情况，协助推进里程碑达成

> **重要**: 具体的当前阶段信息请查看 `docs/ROADMAP.md` 中的"当前项目生涯阶段"章节。

---
"""
        self.sections.append(content)

    def _add_documentation(self):
        """添加文档体系章节"""
        docs = self.config.get("documentation", {})
        key_files = docs.get("key_files", [])

        content = """# 九、上下文管理

## 9.1 关键文件职责

| 文件 | 职责 | 更新时机 |
|-----|------|---------|
"""
        for f in key_files:
            content += f"| `{f.get('path', '')}` | {f.get('purpose', '')} | {f.get('update_trigger', '')} |\n"

        context_file = docs.get('context_file', 'docs/CONTEXT.md')
        decisions_file = docs.get('decisions_file', 'docs/DECISIONS.md')
        changelog_file = docs.get('changelog_file', 'docs/CHANGELOG.md')

        content += f"""
## 9.2 上下文恢复协议

当开启新对话时，AI 应：
1. 读取 `CONTRIBUTING_AI.md` 了解协作规则
2. 读取 `{context_file}` 恢复当前状态
3. 读取 `{decisions_file}` 了解已确认和待定决策
4. 运行 `git log --oneline -10` 了解最近进展
5. 询问用户本次对话目标

## 9.3 上下文保存协议

每次对话结束时，AI 应：
1. 更新 `{context_file}` 保存当前状态
2. 更新 `{changelog_file}` 记录本次产出
3. 如有新决策，更新 `{decisions_file}`
4. **必须执行 git commit** 记录本次对话产出

---
"""
        self.sections.append(content)

    def _add_multi_developer_protocol(self):
        """添加多开发者协作协议章节"""
        multi_dev = self.config.get("multi_developer", {})
        
        if not multi_dev.get("enabled", False):
            return
        
        identity_config = multi_dev.get("identity", {})
        context_config = multi_dev.get("context", {})
        collab_config = multi_dev.get("collaboration", {})
        dialogue_config = multi_dev.get("dialogue_protocol", {})
        
        content = """# 十、多开发者/Agent 协作协议

> **v0.5.0+ 支持多个开发者或多个 AI Agent 在同一项目中协同开发**

## 10.1 协作模式概述

VibeCollab 支持以下协作场景：
- 👥 **多人协作**: 多个开发者在同一项目上工作
- 🤖 **多 Agent 协作**: 多个 AI Agent 分工完成不同任务
- 🔀 **混合协作**: 人类开发者 + AI Agent 混合团队

### 核心原则

1. **独立工作空间**: 每个开发者维护自己的 `CONTEXT.md`，互不干扰
2. **智能聚合**: 系统自动聚合生成全局视图，提供整体状态
3. **明确协作关系**: 通过 `COLLABORATION.md` 记录任务依赖和交接
4. **自动身份识别**: 基于 Git 配置自动识别当前开发者
5. **冲突预防**: 提前检测潜在的跨开发者工作冲突

## 10.2 目录结构

多开发者模式下的项目结构：

```
project/
├── CONTRIBUTING_AI.md
├── project.yaml
└── docs/
    ├── CONTEXT.md            # 全局聚合视图（自动生成，只读）
    ├── CHANGELOG.md          # 全局变更日志
    ├── DECISIONS.md          # 全局决策记录
    └── developers/           # 开发者工作空间
        ├── COLLABORATION.md  # 协作关系文档
        ├── alice/            # 开发者 alice 的目录
        │   ├── CONTEXT.md    # alice 的工作上下文
        │   └── .metadata.yaml # 元数据（更新时间等）
        └── bob/              # 开发者 bob 的目录
            ├── CONTEXT.md
            └── .metadata.yaml
```

## 10.3 开发者身份识别

系统通过以下策略自动识别开发者身份：

"""
        
        primary = identity_config.get('primary', 'git_username')
        fallback = identity_config.get('fallback', 'system_user')
        normalize = identity_config.get('normalize', True)
        
        content += f"""**识别策略**:
- **主策略**: `{primary}` 
  - `git_username`: 使用 `git config user.name`
  - `system_user`: 使用系统用户名（$USER / $USERNAME）
  - `manual`: 手动指定（通过环境变量 `VIBECOLLAB_DEVELOPER`）
- **降级策略**: `{fallback}` (主策略失败时使用)
- **名称标准化**: {'开启' if normalize else '关闭'} (小写、空格转下划线、移除特殊字符)

**使用 CLI 命令查看当前身份**:
```bash
vibecollab dev whoami
```

## 10.4 上下文管理

### 10.4.1 独立上下文

每个开发者维护自己的 `CONTEXT.md`，记录：
- 当前正在进行的任务
- 最近完成的工作
- 待解决的问题
- 技术债务

**更新命令**:
```bash
# 手动更新时间戳（通常在对话结束时自动执行）
vibecollab dev sync
```

### 10.4.2 全局上下文聚合

"""
        
        agg_file = context_config.get('aggregation_file', 'docs/CONTEXT.md')
        auto_sync = context_config.get('auto_sync', True)
        
        content += f"""系统自动聚合所有开发者的上下文，生成全局视图（`{agg_file}`）：

- ⚠️ **只读文件**: 不要手动编辑全局 CONTEXT.md
- 📊 **聚合内容**: 
  - 项目整体状态
  - 各开发者工作进展
  - 跨开发者依赖关系
  - 全局技术债务
- 🔄 **更新时机**: {'对话结束时自动更新' if auto_sync else '手动执行 `vibecollab dev sync`'}

**手动触发聚合**:
```bash
vibecollab dev sync --aggregate
```

## 10.5 协作文档管理

"""
        
        collab_file = collab_config.get('file', 'docs/developers/COLLABORATION.md')
        
        content += f"""### 10.5.1 COLLABORATION.md

`{collab_file}` 记录跨开发者的协作关系：

**包含内容**:
1. **任务分配矩阵**: 谁负责什么任务，谁是协作者
2. **依赖关系**: 任务之间的依赖关系
3. **交接记录**: 任务从一个开发者移交给另一个开发者
4. **协作约定**: 团队的协作惯例和规则

**示例格式**:
```markdown
## 任务分配矩阵

| 任务 | 负责人 | 协作者 | 状态 | 依赖 |
|------|--------|--------|------|------|
| TASK-DEV-001: 用户认证 | alice | bob | IN_PROGRESS | - |
| TASK-DEV-002: 数据库设计 | bob | - | DONE | - |
| TASK-DEV-003: API 开发 | alice | - | TODO | TASK-DEV-002 |

## 交接记录

### TASK-DEV-001: 用户认证
- **交接时间**: 2026-02-10 14:30
- **交接人**: bob
- **接收人**: alice
- **交接原因**: bob 完成数据库设计，alice 接手前端集成
- **交接说明**: API 接口已完成，文档见 docs/api.md
```

### 10.5.2 查看协作状态

```bash
# 查看所有开发者状态
vibecollab dev list

# 查看特定开发者状态
vibecollab dev status alice

# 初始化新开发者上下文
vibecollab dev init --developer bob
```

## 10.6 对话流程适配

"""
        
        on_start = dialogue_config.get('on_start', {})
        on_end = dialogue_config.get('on_end', {})
        
        content += """### 10.6.1 对话开始时

多开发者模式下，AI 在对话开始时应：

```
1. 读取全局聚合 CONTEXT.md（了解整体状态）
2. 读取当前开发者的 CONTEXT.md（了解自己的进度）
3. 读取 COLLABORATION.md（了解协作关系）
4. 识别当前开发者身份（vibecollab dev whoami）
5. 确认本次对话目标
```

### 10.6.2 对话结束时

```
1. 更新当前开发者的 CONTEXT.md
2. 更新全局 CHANGELOG.md
3. 如有跨开发者协作，更新 COLLABORATION.md
4. 自动触发上下文聚合（生成新的全局 CONTEXT.md）
5. Git commit（记录当前开发者的提交）
```

### 10.6.3 多开发者场景的特殊考虑

**场景一：任务依赖**
- Alice 的任务依赖 Bob 的任务完成
- AI 应在 COLLABORATION.md 中标注依赖关系
- Alice 开始工作前检查依赖任务状态

**场景二：任务交接**
- Bob 完成阶段性工作，交接给 Alice
- 在 COLLABORATION.md 记录交接信息
- Alice 接手时读取交接说明

**场景三：并行开发**
- Alice 和 Bob 同时开发不同模块
- 各自维护独立的 CONTEXT.md
- 通过全局聚合了解对方进展

## 10.7 冲突检测与预防 (v0.5.1+)

> **新特性：自动检测跨开发者的潜在工作冲突**

### 10.7.1 冲突类型

系统会检测以下类型的冲突：

1. **文件冲突**: 多个开发者同时修改同一文件
2. **任务冲突**: 多个开发者负责相同或重叠的任务
3. **依赖冲突**: 任务依赖关系不一致或循环依赖
4. **命名冲突**: 多个开发者创建同名的函数/类/模块

### 10.7.2 冲突检测命令

```bash
# 检测当前开发者与其他开发者的冲突
vibecollab dev conflicts

# 详细模式（显示冲突详情）
vibecollab dev conflicts --verbose

# 检测特定开发者之间的冲突
vibecollab dev conflicts --between alice bob
```

### 10.7.3 冲突处理流程

```
1. [AI] 检测到潜在冲突
2. [AI] 在 CONTEXT.md 中标注冲突提醒
3. [AI] 提示用户检查冲突详情
4. [人] 决定处理方式：
   - 协调分工
   - 合并工作
   - 重新分配任务
5. [AI] 更新 COLLABORATION.md 记录解决方案
```

### 10.7.4 冲突预防建议

- ✅ 明确任务边界，避免职责重叠
- ✅ 及时更新 COLLABORATION.md 的任务分配
- ✅ 使用任务依赖标注避免循环依赖
- ✅ 定期执行 `vibecollab dev conflicts` 检查
- ✅ 重要修改前查看全局 CONTEXT.md 了解他人进展

## 10.8 CLI 命令参考

```bash
# 开发者身份
vibecollab dev whoami                    # 查看当前开发者身份

# 开发者管理
vibecollab dev list                      # 列出所有开发者
vibecollab dev status <developer>        # 查看开发者状态
vibecollab dev init --developer <name>   # 初始化新开发者

# 上下文同步
vibecollab dev sync                      # 更新元数据时间戳
vibecollab dev sync --aggregate          # 重新生成全局聚合

# 冲突检测 (v0.5.1+)
vibecollab dev conflicts                 # 检测冲突
vibecollab dev conflicts --verbose       # 详细冲突报告
```

## 10.9 最佳实践

### 对于 AI Agent

1. **对话开始时**: 始终先执行 `vibecollab dev whoami` 确认身份
2. **上下文恢复**: 同时读取全局和个人 CONTEXT.md
3. **协作意识**: 修改共享资源前检查 COLLABORATION.md
4. **及时同步**: 对话结束时更新上下文并触发聚合
5. **冲突敏感**: 发现潜在冲突立即提醒用户

### 对于人类开发者

1. **明确分工**: 在 COLLABORATION.md 中清晰记录任务分配
2. **定期同步**: 经常查看全局 CONTEXT.md 了解团队进展
3. **交接规范**: 任务交接时详细记录背景和状态
4. **冲突检查**: 重大变更前执行冲突检测
5. **文档及时性**: 完成阶段性工作及时更新个人 CONTEXT.md

### 迁移单开发者项目

如果项目原本是单开发者模式，可以平滑迁移：

```bash
# 方式一：使用 CLI 命令
vibecollab dev migrate

# 方式二：在 project.yaml 中启用
multi_developer:
  enabled: true

# 然后重新生成协议文档
vibecollab generate
```

迁移后：
- 原 `docs/CONTEXT.md` 会备份为 `docs/CONTEXT.md.backup`
- 创建 `docs/developers/{developer}/CONTEXT.md`
- 自动生成新的全局聚合 `docs/CONTEXT.md`

---
"""
        
        self.sections.append(content)

    def _add_symbology(self):
        """添加符号学标注系统章节"""
        symbology = self.config.get("symbology", {})

        if not symbology:
            return

        content = """# 十一、符号学标注系统

本协议使用统一的符号体系确保沟通一致性：

"""
        for category, symbols in symbology.items():
            title = category.replace('_', ' ').title()
            content += f"## {title}\n\n"
            content += "| 符号 | 含义 |\n|------|------|\n"
            for s in symbols:
                content += f"| `{s.get('symbol', '')}` | {s.get('meaning', '')} |\n"
            content += "\n"

        content += "---\n"
        self.sections.append(content)

    def _add_extension_sections(self):
        """添加扩展章节"""
        if not self.extension_processor.extensions:
            return
        
        # 获取当前领域
        domain = self.config.get("project", {}).get("domain", "")
        
        content = """# 附录：领域扩展

"""
        
        for ext_domain, ext in self.extension_processor.extensions.items():
            # 只渲染当前项目领域的扩展，或者渲染所有已加载的
            content += f"## {ext_domain.upper()} 领域扩展\n\n"
            
            # 钩子表格
            if ext.hooks:
                content += "### 流程钩子\n\n"
                content += "以下钩子在特定流程节点自动触发：\n\n"
                content += "| 触发点 | 动作 | 条件 | 说明 |\n"
                content += "|-------|------|------|------|\n"
                
                for hook in ext.hooks:
                    condition = f"`{hook.condition}`" if hook.condition else "-"
                    ctx = ext.contexts.get(hook.context_id, None)
                    desc = ctx.description if ctx else hook.context_id or "-"
                    content += f"| `{hook.trigger}` | {hook.action} | {condition} | {desc} |\n"
                content += "\n"
            
            # 上下文说明
            if ext.contexts:
                content += "### 可注入上下文\n\n"
                for ctx_id, ctx in ext.contexts.items():
                    content += f"**{ctx_id}** ({ctx.type})\n"
                    if ctx.description:
                        content += f": {ctx.description}\n"
                    if ctx.source:
                        content += f"- 来源: `{ctx.source}`\n"
                    if ctx.pattern:
                        content += f"- 匹配: `{ctx.pattern}`\n"
                    content += "\n"
            
            # 额外文件
            if ext.additional_files:
                content += "### 领域文件\n\n"
                content += "| 文件 | 用途 |\n|------|------|\n"
                for af in ext.additional_files:
                    content += f"| `{af.get('path', '')}` | {af.get('purpose', '')} |\n"
                content += "\n"
            
            content += "---\n\n"
        
        self.sections.append(content)

    def _add_protocol_check(self):
        """添加协议自检章节"""
        protocol_check = self.config.get("protocol_check", {})
        
        if not protocol_check.get("enabled", True):
            return
        
        content = """# 十二、协议自检机制

## 12.1 协议自检的重要性

> **使用协议时常常发现，有时候对话时会漏掉一些东西，比如没有记得提交 git，没有记得及时同步某个对应文档.md。**

协议自检机制帮助 AI 和用户确保遵循了协作协议中的各项要求。

## 12.2 自检触发方式

### 方式一：命令行检查

```bash
# 检查协议遵循情况
vibecollab check

# 严格模式（警告也视为失败）
vibecollab check --strict
```

### 方式二：对话中触发

在对话中使用以下触发词，AI 应主动执行协议自检：

- "检查协议"
- "协议自检"
- "检查是否遵循协议"
- "protocol check"
- "自检"

## 12.3 检查项说明

协议检查器会检查以下内容：

### Git 协议检查
- ✅ 项目是否已初始化 Git 仓库
- ✅ 是否有未提交的更改
- ⚠️  Git 提交频率（提醒长时间未提交）

### 文档更新检查
- ✅ 必需文档是否存在（CONTEXT.md, CHANGELOG.md 等）
- ⚠️  文档是否及时更新（24小时内）
- ✅ PRD.md 是否存在（如果启用）

### 对话流程检查
- ✅ 对话开始时应该读取的文件是否存在
- ✅ 对话结束时应该更新的文件是否存在

## 12.4 检查结果说明

检查结果分为三个级别：

| 级别 | 符号 | 说明 | 处理方式 |
|------|------|------|---------|
| **错误** | ❌ | 违反协议要求 | 必须修复 |
| **警告** | ⚠️  | 可能遗漏的协议步骤 | 建议处理 |
| **信息** | ℹ️  | 提醒信息 | 可选择性处理 |

## 12.5 AI 自检行为规范

当用户触发协议自检时，AI 应：

1. **执行检查**: 运行协议检查器，获取检查结果
2. **展示结果**: 清晰展示所有检查项的状态
3. **提供建议**: 对于未通过的检查项，提供具体的修复建议
4. **主动修复**: 对于可以自动修复的问题（如更新文档），主动执行修复
5. **记录提醒**: 对于需要人工处理的问题，明确提醒用户

## 12.6 自检最佳实践

### 对话开始时
- 在恢复上下文后，可以执行一次快速自检，确保环境正常

### 对话结束时
- 在执行 git commit 前，执行自检确保所有协议要求都已满足

### 定期检查
- 如果长时间未对话，重新开始对话时执行完整自检

---

"""
        self.sections.append(content)
    
    def _add_prd_management(self):
        """添加 PRD 管理章节"""
        prd_config = self.config.get("prd_management", {})
        
        if not prd_config.get("enabled", True):
            return
        
        prd_file = prd_config.get("prd_file", "docs/PRD.md")
        
        content = f"""# 十三、产品需求文档 (PRD) 管理

## 13.1 PRD 的作用

> **我们虽然是一个启发式对话，需求在对话中推进，不过我们目前没有一个记录原始需求和变化的 PRD.md。我认为项目需求也在随着对话变化和成长。**

PRD.md 用于：
- 📝 **记录原始需求**: 保存用户最初提出的需求描述
- 📊 **跟踪需求变化**: 记录需求在对话中的演进过程
- 🔍 **需求追溯**: 了解每个需求从提出到实现的完整历程
- 📈 **需求统计**: 了解项目需求的状态分布

## 13.2 PRD 文档结构

PRD.md 位于 `{prd_file}`，包含以下内容：

### 需求列表

每个需求包含：
- **需求 ID**: REQ-001, REQ-002, ...
- **需求标题**: 简洁的需求名称
- **原始描述**: 用户最初提出的需求描述
- **当前描述**: 经过澄清和演进后的需求描述
- **状态**: draft / confirmed / in_progress / completed / cancelled
- **优先级**: high / medium / low
- **创建时间**: 需求首次记录的时间
- **更新时间**: 需求最后修改的时间
- **需求变化历史**: 记录需求描述的变化轨迹

### 需求统计

自动统计各状态需求的数量。

## 13.3 PRD 使用流程

### 需求提出阶段

1. **用户提出需求**: 在对话中描述需求
2. **AI 记录需求**: 
   - 使用需求澄清协议，将模糊描述转化为结构化需求
   - 在 PRD.md 中创建新需求条目（REQ-XXX）
   - 记录原始描述和当前描述

### 需求演进阶段

1. **需求澄清**: 在对话中进一步明确需求细节
2. **更新 PRD**: 
   - 更新需求的当前描述
   - 在变化历史中记录变化原因
   - 更新需求状态（如从 draft → confirmed）

### 需求实现阶段

1. **开始实现**: 将需求状态更新为 in_progress
2. **完成实现**: 将需求状态更新为 completed
3. **记录关联**: 在需求中关联对应的 TASK-ID

## 13.4 PRD 管理触发词

在对话中使用以下触发词，AI 应主动管理 PRD：

- "记录需求"
- "更新 PRD"
- "查看需求"
- "需求状态"
- "PRD"
- "需求文档"

## 13.5 PRD 与需求澄清协议的关系

PRD 是需求澄清协议的**输出产物**：

```
用户提出需求
    ↓
需求澄清协议（结构化需求）
    ↓
记录到 PRD.md
    ↓
需求演进和实现
```

## 13.6 PRD 更新时机

AI 应在以下时机更新 PRD：

1. **新需求提出时**: 创建新需求条目
2. **需求澄清后**: 更新当前描述和变化历史
3. **需求状态变化时**: 更新状态字段
4. **需求实现完成时**: 更新状态为 completed，关联 TASK-ID

## 13.7 PRD 最佳实践

### 需求描述规范
- **原始描述**: 保持用户原话，不做修改
- **当前描述**: 经过澄清后的结构化描述
- **变化原因**: 清晰说明为什么需求发生变化

### 需求状态流转
```
draft → confirmed → in_progress → completed
  ↓                    ↓
cancelled          cancelled
```

### 需求关联
- 需求可以关联到 TASK-ID
- 一个需求可能对应多个任务
- 在需求中记录关联的任务 ID

---

"""
        self.sections.append(content)
    
    def _add_quick_reference(self):
        """添加快速参考章节"""
        docs = self.config.get("documentation", {})
        context_file = docs.get('context_file', 'docs/CONTEXT.md')

        content = f"""# 十四、快速参考

## 开始新对话时说

```
继续项目开发。
请先读取 CONTRIBUTING_AI.md 和 {context_file} 恢复上下文。
本次对话目标: {{你的目标}}
```

## 结束对话前说

```
请更新 {context_file} 保存当前进度。
总结本次对话的决策和产出。
然后 git commit 记录本次对话。
```

## 协议自检触发

```
检查协议
或
协议自检
或
vibecollab check
```

## Vibe Check

```
在继续之前，确认一下：
- 我们对齐理解了吗？
- 这个方向对吗？
- 有什么我没考虑到的？
```

---
"""
        self.sections.append(content)

    def _add_footer(self):
        """添加文档尾部"""
        self.sections.append(f"""
*本文档是活文档，记录人机协作的演进过程。*
*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*最珍贵的不是结果，而是我们共同思考的旅程。*
""")
