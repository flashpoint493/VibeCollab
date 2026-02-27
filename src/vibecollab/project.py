"""
LLMContext Project - 项目管理
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import yaml

from .generator import LLMContextGenerator
from .git_utils import ensure_git_repo
from .lifecycle import LifecycleManager
from .llmstxt import LLMsTxtManager
from .templates import TemplateManager


class Project:
    """项目管理类"""

    def __init__(self, config: Dict[str, Any], output_dir: Path):
        self.config = config
        self.output_dir = output_dir
        self.docs_dir = output_dir / "docs"

    @classmethod
    def create(cls, name: str, domain: str, output_dir: Path, multi_dev: bool = False) -> "Project":
        """创建新项目

        Args:
            name: 项目名称
            domain: 业务领域
            output_dir: 输出目录
            multi_dev: 是否启用多开发者模式
        """
        tm = TemplateManager()

        # 加载基础模板
        config = tm.load_config("default")

        # 更新项目信息
        config["project"]["name"] = name
        config["project"]["domain"] = domain

        # 启用多开发者模式
        if multi_dev:
            if "multi_developer" not in config:
                config["multi_developer"] = {}
            config["multi_developer"]["enabled"] = True

        # 合并领域扩展
        try:
            ext_config = tm.load_config(domain)
            cls._merge_extension(config, ext_config)
        except FileNotFoundError:
            pass  # 没有领域扩展，使用默认配置

        # 初始化项目生涯配置
        lifecycle_manager = LifecycleManager.create_default(current_stage="demo")
        lifecycle_config = lifecycle_manager.to_config_dict()
        config.update(lifecycle_config)

        return cls(config, output_dir)

    @classmethod
    def load(cls, project_dir: Path) -> "Project":
        """加载已有项目"""
        config_path = project_dir / "project.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"项目配置不存在: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        return cls(config, project_dir)

    @staticmethod
    def _merge_extension(config: Dict, ext_config: Dict):
        """合并领域扩展配置"""
        if not ext_config:
            return

        # 合并角色覆盖
        if "roles_override" in ext_config and ext_config["roles_override"]:
            for role in ext_config["roles_override"]:
                config["roles"] = [
                    r for r in config.get("roles", [])
                    if r["code"] != role["code"]
                ]
                config["roles"].append(role)

        # 合并领域扩展
        domain_ext = ext_config.get("domain_extensions")
        if domain_ext:
            config.setdefault("domain_extensions", {})
            if config["domain_extensions"] is None:
                config["domain_extensions"] = {}
            config["domain_extensions"].update(domain_ext)

    def generate_all(self, auto_init_git: bool = False):
        """生成所有项目文件

        Args:
            auto_init_git: 如果项目不是 Git 仓库，是否自动初始化
        """
        # 创建目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.docs_dir.mkdir(exist_ok=True)

        # 创建 .vibecollab/ 目录（Insight / EventLog / vectors 等运行时数据）
        vibecollab_dir = self.output_dir / ".vibecollab"
        vibecollab_dir.mkdir(exist_ok=True)
        (vibecollab_dir / "insights").mkdir(exist_ok=True)

        # .vibecollab/.gitignore — 排除运行时数据但保留目录结构
        vc_gitignore = vibecollab_dir / ".gitignore"
        if not vc_gitignore.exists():
            vc_gitignore.write_text(
                "# VibeCollab 运行时数据 (由 vibecollab init 自动生成)\n"
                "events.jsonl\n"
                "vectors/\n"
                "*.local.yaml\n",
                encoding="utf-8",
            )

        # 检查并初始化 Git 仓库
        self._ensure_git_repo(auto_init_git)

        # 保存项目配置
        self._save_config()

        # 生成协作规则文档
        self._generate_llm_txt()

        # 创建文档模板
        self._create_doc_templates()

    def _save_config(self):
        """保存项目配置"""
        config_path = self.output_dir / "project.yaml"
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(
                self.config,
                f,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False
            )

    def _generate_llm_txt(self):
        """生成协作规则文档（CONTRIBUTING_AI.md）并集成 llms.txt"""
        generator = LLMContextGenerator(self.config, self.output_dir)
        content = generator.generate()

        # 输出为 CONTRIBUTING_AI.md
        contributing_ai_path = self.output_dir / "CONTRIBUTING_AI.md"
        contributing_ai_path.write_text(content, encoding="utf-8")

        # 集成 llms.txt
        project_name = self.config.get("project", {}).get("name", "Project")
        project_desc = self.config.get("project", {}).get("description", "AI-assisted development project")

        updated, llmstxt_path = LLMsTxtManager.ensure_integration(
            self.output_dir,
            project_name,
            project_desc,
            contributing_ai_path
        )

        # 保存 llms.txt 路径到配置（用于后续更新）
        if llmstxt_path:
            self.config.setdefault("_meta", {})["llmstxt_path"] = str(llmstxt_path)

    def _create_doc_templates(self):
        """创建文档模板"""
        project_name = self.config.get("project", {}).get("name", "Project")
        today = datetime.now().strftime("%Y-%m-%d")
        multi_dev_enabled = self.config.get("multi_developer", {}).get("enabled", False)

        # 多开发者模式：初始化开发者上下文
        if multi_dev_enabled:
            from .developer import ContextAggregator, DeveloperManager

            dm = DeveloperManager(self.output_dir, self.config)
            current_dev = dm.get_current_developer()

            # 初始化当前开发者的上下文
            dm.init_developer_context(current_dev)

            # 创建 COLLABORATION.md
            collab_config = self.config.get('multi_developer', {}).get('collaboration', {})
            collab_file = self.output_dir / collab_config.get('file', 'docs/developers/COLLABORATION.md')
            collab_file.parent.mkdir(parents=True, exist_ok=True)

            collab_content = f"""# {project_name} 开发者协作记录

## 当前协作关系

(暂无协作记录)

## 任务分配矩阵

| 任务 | 负责人 | 协作者 | 状态 | 依赖 |
|------|--------|--------|------|------|
| 项目初始化 | {current_dev} | - | DONE | - |

## 交接记录

(暂无交接记录)

---
*最后更新: {today}*
"""
            collab_file.write_text(collab_content, encoding='utf-8')

            # 生成全局聚合 CONTEXT.md
            aggregator = ContextAggregator(self.output_dir, self.config)
            aggregator.generate_and_save()

        # DECISIONS.md
        decisions_content = f"""# {project_name} 决策记录

## 待确认决策

(暂无)

## 已确认决策

(暂无)

---
*决策记录格式见 CONTRIBUTING_AI.md*
"""

        # CHANGELOG.md
        changelog_content = f"""# {project_name} 变更日志

## [Unreleased]

### Added
- 项目初始化
- 生成 CONTRIBUTING_AI.md 协作规则

---
"""

        # ROADMAP.md - 包含项目生涯阶段信息
        lifecycle_manager = LifecycleManager(self.config)
        current_stage = lifecycle_manager.get_current_stage()
        stage_info = lifecycle_manager.get_stage_info()
        stage_history = lifecycle_manager.get_stage_history()

        current_stage_entry = stage_history[-1] if stage_history else None
        started_at = current_stage_entry.get("started_at", today) if current_stage_entry else today

        roadmap_content = f"""# {project_name} 路线图

## 当前项目生涯阶段

**阶段**: {stage_info.get('name', '未知')} ({current_stage})
**开始时间**: {started_at}
**阶段描述**: {stage_info.get('description', '')}

### 阶段重点
{chr(10).join(f"- {focus}" for focus in stage_info.get('focus', []))}

### 阶段原则
{chr(10).join(f"- {principle}" for principle in stage_info.get('principles', []))}

### 当前阶段里程碑
{self._format_milestones(stage_info.get('milestones', []))}

---

## 当前里程碑: Phase 0 - 项目初始化

### 目标
- [ ] 确定项目方向
- [ ] 建立开发环境
- [ ] 完成核心决策

### 迭代建议池

(暂无)

---

## 阶段历史

{self._format_stage_history(stage_history)}

---
"""

        # QA_TEST_CASES.md
        qa_content = f"""# {project_name} 测试用例手册

## 测试用例格式

```
### TC-{{模块}}-{{序号}}: {{测试名称}}
- **关联**: TASK-XXX
- **前置**: {{前置条件}}
- **步骤**:
  1. {{步骤1}}
  2. {{步骤2}}
- **预期**: {{预期结果}}
- **状态**: 🟢/🟡/🔴/⚪
```

## Phase 0 测试用例

(待添加)

---
"""

        # PRD.md - 产品需求文档
        prd_content = f"""# {project_name} 产品需求文档 (PRD)

本文档记录项目的原始需求和需求变化历史。

## 需求列表

(待添加需求)

---

## 需求统计

| 状态 | 数量 |
|------|------|
| draft | 0 |
| confirmed | 0 |
| in_progress | 0 |
| completed | 0 |
| cancelled | 0 |

---

*最后更新: {today}*
"""

        # 写入文件
        if not multi_dev_enabled:
            # 单开发者模式才写入 CONTEXT.md（多开发者模式已通过聚合生成）
            context_content = f"""# {project_name} 当前上下文

## 当前状态
- **阶段**: Phase 0 - 项目初始化
- **进度**: 刚开始
- **下一步**: 确定首要任务

## 本次对话目标
(待填写)

## 待决策事项
(待填写)

## 已完成事项
- [x] 项目初始化
- [x] 生成 CONTRIBUTING_AI.md

---
*最后更新: {today}*
"""
            (self.docs_dir / "CONTEXT.md").write_text(context_content, encoding="utf-8")

        (self.docs_dir / "DECISIONS.md").write_text(decisions_content, encoding="utf-8")
        (self.docs_dir / "CHANGELOG.md").write_text(changelog_content, encoding="utf-8")
        (self.docs_dir / "ROADMAP.md").write_text(roadmap_content, encoding="utf-8")
        (self.docs_dir / "QA_TEST_CASES.md").write_text(qa_content, encoding="utf-8")
        (self.docs_dir / "PRD.md").write_text(prd_content, encoding="utf-8")

    def regenerate(self):
        """重新生成协作规则文档并更新 llms.txt"""
        # 检查 Git 仓库状态（不自动初始化，只提示）
        self._ensure_git_repo(auto_init=False)
        self._generate_llm_txt()

    def _ensure_git_repo(self, auto_init: bool = False):
        """确保项目是 Git 仓库

        Args:
            auto_init: 如果不存在是否自动初始化
        """
        success, message, is_new = ensure_git_repo(self.output_dir, auto_init=auto_init)

        if not success:
            # 保存警告信息到配置，供 CLI 显示
            self.config.setdefault("_meta", {})["git_warning"] = message
        elif is_new:
            # 记录已自动初始化
            self.config.setdefault("_meta", {})["git_auto_init"] = True

    def _format_milestones(self, milestones: list) -> str:
        """格式化里程碑列表

        Args:
            milestones: 里程碑列表

        Returns:
            str: 格式化后的里程碑文本
        """
        if not milestones:
            return "(暂无里程碑)"

        lines = []
        for i, milestone in enumerate(milestones, 1):
            name = milestone.get("name", f"里程碑 {i}")
            completed = milestone.get("completed", False)
            status = "✅" if completed else "⏳"
            lines.append(f"- {status} {name}")

        return "\n".join(lines)

    def _format_stage_history(self, history: list) -> str:
        """格式化阶段历史

        Args:
            history: 阶段历史列表

        Returns:
            str: 格式化后的历史文本
        """
        if not history:
            return "(暂无历史记录)"

        lines = []
        for entry in history:
            stage = entry.get("stage", "unknown")
            started = entry.get("started_at", "未知")
            ended = entry.get("ended_at")

            if ended:
                lines.append(f"- **{stage}**: {started} → {ended}")
            else:
                lines.append(f"- **{stage}**: {started} (进行中)")

        return "\n".join(lines)
