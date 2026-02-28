"""
LLMContext Generator - 文档生成器
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .extension import ExtensionProcessor


class LLMContextGenerator:
    """AI 协作协议文档生成器

    使用 PatternEngine (Jinja2 模板) 生成 CONTRIBUTING_AI.md 文档。
    """

    def __init__(self, config: Dict[str, Any], project_root: Optional[Path] = None):
        self.config = config
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
        from .pattern_engine import PatternEngine
        engine = PatternEngine(self.config, self.project_root)
        return engine.render()

    def generate_ide_rules_summary(self) -> str:
        """Generate IDE rules/skills body from project config (schema-driven, same as README/context)."""
        from .pattern_engine import PatternEngine
        engine = PatternEngine(self.config, self.project_root)
        return engine.render_ide_rules_summary()
