"""
Pattern Engine — 基于 Jinja2 的 CONTRIBUTING_AI.md 模板渲染引擎

将原 generator.py 中 27 个硬编码 _add_*() 方法外化为独立的 .md.j2 模板文件，
由 manifest.yaml 驱动章节顺序和条件开关。

向后兼容: LLMContextGenerator.generate() 内部改为调用 PatternEngine，外部 API 不变。

Template Overlay 机制:
  用户可在项目根目录下创建 .vibecollab/patterns/ 目录，放置自定义模板和 manifest.yaml。
  - 自定义模板优先于内置模板（同名覆盖）
  - 自定义 manifest.yaml 可新增/覆盖/排除章节
  - 合并策略: 按 section id 合并，本地 manifest 条目覆盖内置同 id 条目
"""

import copy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from jinja2 import ChoiceLoader, Environment, FileSystemLoader, select_autoescape

from .project_adapter import ProjectAdapter

# Pattern 目录（包内）
PATTERNS_DIR = Path(__file__).parent / "patterns"

# 用户本地自定义模板目录名（相对于 project_root）
LOCAL_PATTERNS_SUBDIR = Path(".vibecollab") / "patterns"


class PatternEngine:
    """Jinja2 驱动的协议文档渲染引擎

    支持 template overlay: 用户在 {project_root}/.vibecollab/patterns/ 下
    放置自定义 .md.j2 模板和/或 manifest.yaml，可覆盖/扩展内置模板。
    """

    def __init__(
        self,
        config: Dict[str, Any],
        project_root: Optional[Path] = None,
        patterns_dir: Optional[Path] = None,
    ):
        self.config = config
        self.project_root = project_root or Path.cwd()
        self.patterns_dir = patterns_dir or PATTERNS_DIR

        # 创建配置适配器（支持向后兼容和扩展）
        self.adapter = ProjectAdapter(config)

        # 检测用户本地 patterns 目录
        self.local_patterns_dir: Optional[Path] = None
        local_candidate = self.project_root / LOCAL_PATTERNS_SUBDIR
        if local_candidate.is_dir():
            self.local_patterns_dir = local_candidate

        # 加载并合并 manifest
        self.manifest = self._load_manifest()

        # Jinja2 环境 — 使用 ChoiceLoader 实现本地优先
        loaders = []
        if self.local_patterns_dir:
            loaders.append(FileSystemLoader(str(self.local_patterns_dir)))
        loaders.append(FileSystemLoader(str(self.patterns_dir)))

        self.env = Environment(
            loader=ChoiceLoader(loaders),
            autoescape=select_autoescape([]),
            keep_trailing_newline=True,
            trim_blocks=False,
            lstrip_blocks=False,
        )
        # 注册自定义 filter
        self.env.filters["join_list"] = _filter_join_list
        self.env.filters["format_review"] = _filter_format_review
        self.env.filters["quote_list"] = _filter_quote_list

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def render(self) -> str:
        """渲染完整的 CONTRIBUTING_AI.md 文档"""
        sections: List[str] = []

        for entry in self.manifest.get("sections", []):
            template_file = entry["template"]
            condition = entry.get("condition")

            # 条件检查
            if condition and not self._evaluate_condition(condition):
                continue

            template = self.env.get_template(template_file)
            ctx = self._build_context(entry)
            rendered = template.render(**ctx)

            if rendered.strip():
                sections.append(rendered)

        return "\n".join(sections)

    def list_patterns(self) -> List[Dict[str, Any]]:
        """列出所有注册的 Pattern（含 overlay 来源标注）"""
        result = []
        for entry in self.manifest.get("sections", []):
            info = {
                "id": entry.get("id", ""),
                "template": entry["template"],
                "description": entry.get("description", ""),
                "condition": entry.get("condition"),
            }
            # 标注模板来源
            if self.local_patterns_dir:
                local_tmpl = self.local_patterns_dir / entry["template"]
                info["source"] = "local" if local_tmpl.is_file() else "builtin"
            else:
                info["source"] = "builtin"
            result.append(info)
        return result

    @property
    def has_local_overlay(self) -> bool:
        """是否启用了用户本地模板覆盖"""
        return self.local_patterns_dir is not None

    # ------------------------------------------------------------------
    # Manifest loading & merging
    # ------------------------------------------------------------------

    def _load_manifest(self) -> Dict[str, Any]:
        """加载 manifest，支持本地覆盖合并

        合并策略:
        1. 加载内置 manifest.yaml 作为基础
        2. 如果存在本地 manifest.yaml，按 section id 合并:
           - 同 id: 本地条目覆盖内置条目
           - 本地新 id: 追加到对应位置（通过 'after' 字段）或末尾
           - 本地 exclude 列表: 排除指定 id 的章节
        """
        # 加载内置 manifest
        builtin_path = self.patterns_dir / "manifest.yaml"
        with open(builtin_path, "r", encoding="utf-8") as f:
            builtin_manifest = yaml.safe_load(f) or {}

        if not self.local_patterns_dir:
            return builtin_manifest

        # 检查本地 manifest
        local_manifest_path = self.local_patterns_dir / "manifest.yaml"
        if not local_manifest_path.is_file():
            return builtin_manifest

        with open(local_manifest_path, "r", encoding="utf-8") as f:
            local_manifest = yaml.safe_load(f) or {}

        return self._merge_manifests(builtin_manifest, local_manifest)

    @staticmethod
    def _merge_manifests(
        builtin: Dict[str, Any],
        local: Dict[str, Any],
    ) -> Dict[str, Any]:
        """合并内置 manifest 和本地 manifest

        local manifest 支持的字段:
        - sections: 章节列表，按 id 与内置合并
        - exclude: 要排除的章节 id 列表
        """
        result = copy.deepcopy(builtin)
        builtin_sections = result.get("sections", [])

        # 排除列表
        exclude_ids = set(local.get("exclude", []))
        if exclude_ids:
            builtin_sections = [
                s for s in builtin_sections if s.get("id") not in exclude_ids
            ]

        # 建立 id → index 映射
        id_to_idx = {s.get("id"): i for i, s in enumerate(builtin_sections)}

        # 合并本地 sections
        local_sections = local.get("sections", [])
        append_sections = []

        for local_entry in local_sections:
            sid = local_entry.get("id")
            if sid and sid in id_to_idx:
                # 覆盖: 用本地条目替换内置条目
                builtin_sections[id_to_idx[sid]] = local_entry
            else:
                # 新增: 检查 after 字段确定插入位置
                after_id = local_entry.get("after")
                if after_id and after_id in id_to_idx:
                    insert_idx = id_to_idx[after_id] + 1
                    builtin_sections.insert(insert_idx, local_entry)
                    # 重建索引
                    id_to_idx = {
                        s.get("id"): i for i, s in enumerate(builtin_sections)
                    }
                else:
                    append_sections.append(local_entry)

        # 追加没有指定位置的新章节（在 footer 之前）
        if append_sections:
            footer_idx = id_to_idx.get("footer")
            if footer_idx is not None:
                for i, s in enumerate(append_sections):
                    builtin_sections.insert(footer_idx + i, s)
            else:
                builtin_sections.extend(append_sections)

        result["sections"] = builtin_sections
        return result

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _build_context(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """构建模板渲染上下文"""
        ctx: Dict[str, Any] = {
            "config": self.config,
            "adapter": self.adapter,  # 新增：ProjectAdapter
            "project": self.config.get("project", {}),
            "custom": self.config.get("custom", {}),  # 新增：自定义字段
            "now": datetime.now(),
        }

        # 把常用配置节直接展开到顶层方便模板引用
        for key in [
            "philosophy", "decision_levels", "task_unit",
            "dialogue_protocol", "requirement_clarification",
            "git_workflow", "testing", "milestone", "iteration",
            "version_review", "build", "quick_acceptance",
            "prompt_engineering", "confirmed_decisions",
            "contributing_ai_changelog", "documentation",
            "multi_developer", "protocol_check", "prd_management",
            "symbology", "domain_extensions",
        ]:
            ctx[key] = self.config.get(key, {} if key not in (
                "decision_levels", "confirmed_decisions",
                "contributing_ai_changelog",
            ) else [])

        # 特殊处理 roles: 使用 adapter 合并用户定义和默认角色
        ctx["roles"] = self.adapter.get_roles()

        # 扩展处理器上下文
        ctx["extensions"] = self._get_extensions_context()

        return ctx

    def _get_extensions_context(self) -> Dict[str, Any]:
        """获取扩展信息用于模板渲染"""
        from .extension import ExtensionProcessor
        processor = ExtensionProcessor(self.project_root)

        # 从 domain_extensions 加载
        if "domain_extensions" in self.config:
            processor.load_from_config(self.config)

        # 从独立扩展文件加载
        ext_files = self.config.get("extension_files", [])
        for ext_file in ext_files:
            ext_path = self.project_root / ext_file
            if ext_path.exists():
                with open(ext_path, "r", encoding="utf-8") as f:
                    ext_data = yaml.safe_load(f)
                processor.load_from_config(ext_data)

        return {
            "has_extensions": bool(processor.extensions),
            "extensions": processor.extensions,
        }

    def _evaluate_condition(self, condition: str) -> bool:
        """评估 manifest 中的条件表达式

        支持的条件:
        - "config.multi_developer.enabled" → self.config["multi_developer"]["enabled"]
        - "config.protocol_check.enabled|true" → 默认 True（key 不存在时）
        - "config.testing.product_qa.enabled" → ...
        - "has_extensions" → 是否有扩展加载
        - "config.symbology" → symbology 非空
        """
        if condition == "has_extensions":
            ctx = self._get_extensions_context()
            return ctx["has_extensions"]

        if condition.startswith("config."):
            # 支持 "|default" 语法: "config.x.enabled|true"
            default_val = None
            expr = condition[len("config."):]
            if "|" in expr:
                expr, default_str = expr.split("|", 1)
                default_val = default_str.strip().lower() in ("true", "1", "yes")

            parts = expr.split(".")
            val = self.config
            for part in parts:
                if isinstance(val, dict):
                    val = val.get(part)
                else:
                    return default_val if default_val is not None else False
                if val is None:
                    return default_val if default_val is not None else False

            # 布尔值直接返回; 非空集合/字典返回 True
            if isinstance(val, bool):
                return val
            if isinstance(val, (dict, list)):
                return bool(val)
            return bool(val)

        return True


# ------------------------------------------------------------------
# Jinja2 custom filters
# ------------------------------------------------------------------

def _filter_join_list(value, separator="、"):
    """将列表用指定分隔符连接"""
    if isinstance(value, list):
        return separator.join(str(v) for v in value)
    return str(value)


def _filter_quote_list(value, separator="、"):
    """将列表中每个元素加引号后用分隔符连接"""
    if isinstance(value, list):
        return separator.join(f'"{v}"' for v in value)
    return str(value)


def _filter_format_review(review: Dict) -> str:
    """格式化 Review 要求描述"""
    if not isinstance(review, dict):
        return str(review)
    if not review.get("required", False):
        if review.get("mode") == "auto":
            return "AI 提出建议，人工可快速确认或默认通过"
        return "AI 自主决策，事后可调整"

    if review.get("mode") == "sync":
        return "必须人工确认，记录决策理由"
    elif review.get("mode") == "async":
        return "人工Review，可异步确认"
    return "需要 Review"
