"""
LLMTxt Project - 项目管理
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from .generator import LLMTxtGenerator
from .templates import TemplateManager


class Project:
    """项目管理类"""

    def __init__(self, config: Dict[str, Any], output_dir: Path):
        self.config = config
        self.output_dir = output_dir
        self.docs_dir = output_dir / "docs"

    @classmethod
    def create(cls, name: str, domain: str, output_dir: Path) -> "Project":
        """创建新项目"""
        tm = TemplateManager()
        
        # 加载基础模板
        config = tm.load_config("default")
        
        # 更新项目信息
        config["project"]["name"] = name
        config["project"]["domain"] = domain
        
        # 合并领域扩展
        try:
            ext_config = tm.load_config(domain)
            cls._merge_extension(config, ext_config)
        except FileNotFoundError:
            pass  # 没有领域扩展，使用默认配置
        
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
        # 合并角色覆盖
        if "roles_override" in ext_config:
            existing_codes = {r["code"] for r in config.get("roles", [])}
            for role in ext_config["roles_override"]:
                config["roles"] = [
                    r for r in config.get("roles", [])
                    if r["code"] != role["code"]
                ]
                config["roles"].append(role)
        
        # 合并领域扩展
        if "domain_extensions" in ext_config:
            config.setdefault("domain_extensions", {})
            config["domain_extensions"].update(ext_config["domain_extensions"])

    def generate_all(self):
        """生成所有项目文件"""
        # 创建目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.docs_dir.mkdir(exist_ok=True)
        
        # 保存项目配置
        self._save_config()
        
        # 生成 llm.txt
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
        """生成 llm.txt"""
        generator = LLMTxtGenerator(self.config)
        content = generator.generate()
        
        llm_txt_path = self.output_dir / "llm.txt"
        llm_txt_path.write_text(content, encoding="utf-8")

    def _create_doc_templates(self):
        """创建文档模板"""
        project_name = self.config.get("project", {}).get("name", "Project")
        today = datetime.now().strftime("%Y-%m-%d")
        
        # CONTEXT.md
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
- [x] 生成 llm.txt

---
*最后更新: {today}*
"""
        
        # DECISIONS.md
        decisions_content = f"""# {project_name} 决策记录

## 待确认决策

(暂无)

## 已确认决策

(暂无)

---
*决策记录格式见 llm.txt*
"""
        
        # CHANGELOG.md
        changelog_content = f"""# {project_name} 变更日志

## [Unreleased]

### Added
- 项目初始化
- 生成 llm.txt 协作规则

---
"""
        
        # ROADMAP.md
        roadmap_content = f"""# {project_name} 路线图

## 当前里程碑: Phase 0 - 项目初始化

### 目标
- [ ] 确定项目方向
- [ ] 建立开发环境
- [ ] 完成核心决策

### 迭代建议池

(暂无)

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
        
        # 写入文件
        (self.docs_dir / "CONTEXT.md").write_text(context_content, encoding="utf-8")
        (self.docs_dir / "DECISIONS.md").write_text(decisions_content, encoding="utf-8")
        (self.docs_dir / "CHANGELOG.md").write_text(changelog_content, encoding="utf-8")
        (self.docs_dir / "ROADMAP.md").write_text(roadmap_content, encoding="utf-8")
        (self.docs_dir / "QA_TEST_CASES.md").write_text(qa_content, encoding="utf-8")

    def regenerate(self):
        """重新生成 llm.txt"""
        self._generate_llm_txt()
