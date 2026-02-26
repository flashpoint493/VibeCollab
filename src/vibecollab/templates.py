"""
模板管理器模块
"""

from pathlib import Path
from typing import Dict, List, Optional
import yaml


class TemplateManager:
    """模板管理器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.templates_dir = project_root / "src" / "vibecollab" / "templates"

    def get_template(self, name: str) -> Optional[Dict]:
        """获取模板配置"""
        template_file = self.templates_dir / name
        if template_file.exists():
            with open(template_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return None

    def list_templates(self) -> List[str]:
        """列出所有模板"""
        if not self.templates_dir.exists():
            return []

        templates = []
        for item in self.templates_dir.rglob("*.yaml"):
            templates.append(str(item.relative_to(self.templates_dir)))

        return templates
