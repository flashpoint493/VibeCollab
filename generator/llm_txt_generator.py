#!/usr/bin/env python3
"""
LLM.TXT Generator
从 YAML 配置文件生成标准化的 llm.txt 协作文档

Usage:
    python llm_txt_generator.py --config project.yaml --output llm.txt
"""

import argparse
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


class LLMTxtGenerator:
    """LLM.TXT 文档生成器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.sections: List[str] = []

    def generate(self) -> str:
        """生成完整的 llm.txt 文档"""
        self._add_header()
        self._add_philosophy()
        self._add_roles()
        self._add_decision_levels()
        self._add_task_unit()
        self._add_dialogue_protocol()
        self._add_git_workflow()
        self._add_testing()
        self._add_milestone()
        self._add_iteration()
        self._add_documentation()
        self._add_symbology()
        self._add_quick_reference()
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

        content += f"""
## 1.2 决策质量观

> **大量决策，{int(decision_quality.get('target_rate', 0.9) * 100)}% 正确率，关键决策零失误**

项目是一系列决策的集合：
- 只有做对 {int(decision_quality.get('target_rate', 0.9) * 100)}% 以上的决策，项目才有望成功
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
- llm.txt 是**活文档**，随项目成长
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
        if gatekeepers:
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

        content += f"""└── 状态: {' / '.join(task_unit.get('statuses', ['TODO', 'IN_PROGRESS', 'REVIEW', 'DONE']))}
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
            content += f"""## 5.1 单元测试 (Unit Test)

> **开发者视角：验证代码逻辑正确性**

| 配置项 | 值 |
|-------|-----|
| 测试框架 | {unit_test.get('framework', 'jest')} |
| 覆盖率目标 | {int(unit_test.get('coverage_target', 0.8) * 100)}% |
| 文件模式 | {', '.join(unit_test.get('patterns', ['**/*.test.ts']))} |
| 运行时机 | {', '.join(unit_test.get('run_on', ['pre-commit', 'ci']))} |

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
        for phase in lifecycle:
            content += f"""│  {lifecycle.index(phase) + 1}. {phase.get('phase', '')} - {phase.get('description', '')}
"""
            for criteria in phase.get("exit_criteria", []):
                content += f"│     └── {criteria}\n"
            content += "├─────────────────────────────────────────────────────────┤\n"

        content = content.rstrip("├─────────────────────────────────────────────────────────┤\n")
        content += """
└─────────────────────────────────────────────────────────┘
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

        content += f"""
### 里程碑 Tag

```bash
git tag -a {milestone.get('tag_pattern', 'v{major}.{minor}.{patch}')} -m "描述"
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

        content += f"""
## 8.2 上下文恢复协议

当开启新对话时，AI 应：
1. 读取 `llm.txt` 了解协作规则
2. 读取 `{docs.get('context_file', 'docs/CONTEXT.md')}` 恢复当前状态
3. 读取 `{docs.get('decisions_file', 'docs/DECISIONS.md')}` 了解已确认和待定决策
4. 运行 `git log --oneline -10` 了解最近进展
5. 询问用户本次对话目标

## 8.3 上下文保存协议

每次对话结束时，AI 应：
1. 更新 `{docs.get('context_file', 'docs/CONTEXT.md')}` 保存当前状态
2. 更新 `{docs.get('changelog_file', 'docs/CHANGELOG.md')}` 记录本次产出
3. 如有新决策，更新 `{docs.get('decisions_file', 'docs/DECISIONS.md')}`
4. **必须执行 git commit** 记录本次对话产出

---
"""
        self.sections.append(content)

    def _add_symbology(self):
        """添加符号学标注系统章节"""
        symbology = self.config.get("symbology", {})

        content = """# 九、符号学标注系统

本协议使用统一的符号体系确保沟通一致性：

"""
        for category, symbols in symbology.items():
            content += f"## {category.replace('_', ' ').title()}\n\n"
            content += "| 符号 | 含义 |\n|------|------|\n"
            for s in symbols:
                content += f"| `{s.get('symbol', '')}` | {s.get('meaning', '')} |\n"
            content += "\n"

        content += "---\n"
        self.sections.append(content)

    def _add_quick_reference(self):
        """添加快速参考章节"""
        docs = self.config.get("documentation", {})

        content = f"""# 十、快速参考

## 开始新对话时说

```
继续项目开发。
请先读取 llm.txt 和 {docs.get('context_file', 'docs/CONTEXT.md')} 恢复上下文。
本次对话目标: {{你的目标}}
```

## 结束对话前说

```
请更新 {docs.get('context_file', 'docs/CONTEXT.md')} 保存当前进度。
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


def main():
    parser = argparse.ArgumentParser(description="LLM.TXT Generator")
    parser.add_argument("--config", "-c", required=True, help="YAML 配置文件路径")
    parser.add_argument("--output", "-o", default="llm.txt", help="输出文件路径")
    args = parser.parse_args()

    # 读取配置
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"错误: 配置文件不存在: {config_path}")
        return 1

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 生成文档
    generator = LLMTxtGenerator(config)
    content = generator.generate()

    # 输出
    output_path = Path(args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ 已生成: {output_path}")
    return 0


if __name__ == "__main__":
    exit(main())
