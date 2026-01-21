"""
LLMContext Generator - 文档生成器
"""

import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

from .extension import ExtensionProcessor


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
        self._add_documentation()
        self._add_prompt_engineering()
        self._add_symbology()
        self._add_decisions_summary()
        self._add_extension_sections()
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

    def _add_documentation(self):
        """添加文档体系章节"""
        docs = self.config.get("documentation", {})
        key_files = docs.get("key_files", [])

        content = """# 八、上下文管理

## 8.1 关键文件职责

| 文件 | 职责 | 更新时机 |
|-----|------|---------|
"""
        for f in key_files:
            content += f"| `{f.get('path', '')}` | {f.get('purpose', '')} | {f.get('update_trigger', '')} |\n"

        context_file = docs.get('context_file', 'docs/CONTEXT.md')
        decisions_file = docs.get('decisions_file', 'docs/DECISIONS.md')
        changelog_file = docs.get('changelog_file', 'docs/CHANGELOG.md')

        content += f"""
## 8.2 上下文恢复协议

当开启新对话时，AI 应：
1. 读取 `CONTRIBUTING_AI.md` 了解协作规则
2. 读取 `{context_file}` 恢复当前状态
3. 读取 `{decisions_file}` 了解已确认和待定决策
4. 运行 `git log --oneline -10` 了解最近进展
5. 询问用户本次对话目标

## 8.3 上下文保存协议

每次对话结束时，AI 应：
1. 更新 `{context_file}` 保存当前状态
2. 更新 `{changelog_file}` 记录本次产出
3. 如有新决策，更新 `{decisions_file}`
4. **必须执行 git commit** 记录本次对话产出

---
"""
        self.sections.append(content)

    def _add_symbology(self):
        """添加符号学标注系统章节"""
        symbology = self.config.get("symbology", {})

        if not symbology:
            return

        content = """# 九、符号学标注系统

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

    def _add_quick_reference(self):
        """添加快速参考章节"""
        docs = self.config.get("documentation", {})
        context_file = docs.get('context_file', 'docs/CONTEXT.md')

        content = f"""# 十、快速参考

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
