"""
LLMTxt Templates - 模板管理
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
import importlib.resources


class TemplateManager:
    """模板管理器"""

    def __init__(self, templates_dir: Optional[Path] = None):
        if templates_dir:
            self.templates_dir = templates_dir
        else:
            # 默认使用包内模板目录
            self.templates_dir = self._get_package_templates_dir()

    def _get_package_templates_dir(self) -> Path:
        """获取包内模板目录"""
        # 尝试从包资源获取
        try:
            # Python 3.9+
            import importlib.resources as pkg_resources
            ref = pkg_resources.files("llmtxt") / "templates"
            return Path(str(ref))
        except (ImportError, TypeError, AttributeError):
            pass
        
        # 回退到相对路径
        package_dir = Path(__file__).parent
        templates_dir = package_dir / "templates"
        
        if templates_dir.exists():
            return templates_dir
        
        # 尝试项目根目录
        root_templates = package_dir.parent.parent / "templates"
        if root_templates.exists():
            return root_templates
        
        raise FileNotFoundError("无法找到模板目录")

    def list_templates(self) -> List[Dict[str, Any]]:
        """列出所有可用模板"""
        templates = []
        
        # 主模板
        for yaml_file in self.templates_dir.glob("*.yaml"):
            templates.append({
                "name": yaml_file.stem.replace(".project", ""),
                "type": "project",
                "path": yaml_file
            })
        
        # 领域扩展
        domains_dir = self.templates_dir / "domains"
        if domains_dir.exists():
            for yaml_file in domains_dir.glob("*.yaml"):
                templates.append({
                    "name": yaml_file.stem.replace(".extension", ""),
                    "type": "extension",
                    "path": yaml_file
                })
        
        return templates

    def get_template(self, name: str) -> str:
        """获取模板内容"""
        # 尝试主模板
        template_path = self.templates_dir / f"{name}.project.yaml"
        if template_path.exists():
            return template_path.read_text(encoding="utf-8")
        
        # 尝试领域扩展
        template_path = self.templates_dir / "domains" / f"{name}.extension.yaml"
        if template_path.exists():
            return template_path.read_text(encoding="utf-8")
        
        # 尝试无后缀
        template_path = self.templates_dir / f"{name}.yaml"
        if template_path.exists():
            return template_path.read_text(encoding="utf-8")
        
        raise FileNotFoundError(f"模板不存在: {name}")

    def load_config(self, name: str) -> Dict[str, Any]:
        """加载并解析模板配置"""
        content = self.get_template(name)
        return yaml.safe_load(content)

    def save_template(self, name: str, config: Dict[str, Any], template_type: str = "project"):
        """保存自定义模板"""
        if template_type == "extension":
            template_path = self.templates_dir / "domains" / f"{name}.extension.yaml"
            template_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            template_path = self.templates_dir / f"{name}.project.yaml"
        
        with open(template_path, "w", encoding="utf-8") as f:
            yaml.dump(
                config,
                f,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False
            )
