#!/usr/bin/env python3
"""
LLM Collaboration Project Initializer
快速初始化一个遵循 LLM Collaboration Protocol 的项目

Usage:
    python init_project.py --name "MyProject" --domain web --output ./my-project
"""

import argparse
import shutil
from pathlib import Path
import yaml


DOMAINS = ["generic", "game", "web", "data", "mobile", "infra"]


def init_project(name: str, domain: str, output_dir: Path, base_dir: Path):
    """初始化项目结构"""
    
    # 创建项目目录
    output_dir.mkdir(parents=True, exist_ok=True)
    docs_dir = output_dir / "docs"
    docs_dir.mkdir(exist_ok=True)

    # 复制基础模板
    base_template = base_dir / "templates" / "default.project.yaml"
    project_config = output_dir / "project.yaml"
    
    # 读取并修改配置
    with open(base_template, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    config["project"]["name"] = name
    config["project"]["domain"] = domain
    
    # 如果有领域扩展，合并配置
    domain_ext = base_dir / "templates" / "domains" / f"{domain}.extension.yaml"
    if domain_ext.exists():
        with open(domain_ext, "r", encoding="utf-8") as f:
            ext_config = yaml.safe_load(f)
        
        # 合并角色覆盖
        if "roles_override" in ext_config:
            existing_codes = {r["code"] for r in config.get("roles", [])}
            for role in ext_config["roles_override"]:
                # 替换或添加角色
                config["roles"] = [
                    r for r in config.get("roles", []) 
                    if r["code"] != role["code"]
                ]
                config["roles"].append(role)
        
        # 合并领域扩展
        if "domain_extensions" in ext_config:
            config.setdefault("domain_extensions", {})
            config["domain_extensions"].update(ext_config["domain_extensions"])
    
    # 写入项目配置
    with open(project_config, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    
    # 创建文档模板
    create_doc_templates(docs_dir, name)
    
    # 复制生成器
    generator_src = base_dir / "generator" / "llm_txt_generator.py"
    generator_dst = output_dir / "llm_txt_generator.py"
    shutil.copy(generator_src, generator_dst)
    
    # 生成 llm.txt
    from generator.llm_txt_generator import LLMTxtGenerator
    generator = LLMTxtGenerator(config)
    llm_txt_content = generator.generate()
    
    with open(output_dir / "llm.txt", "w", encoding="utf-8") as f:
        f.write(llm_txt_content)
    
    print(f"✅ 项目已初始化: {output_dir}")
    print(f"   - project.yaml: 项目配置")
    print(f"   - llm.txt: AI 协作规则")
    print(f"   - docs/: 文档目录")
    print(f"\n下一步:")
    print(f"   1. 编辑 project.yaml 自定义配置")
    print(f"   2. 运行 python llm_txt_generator.py -c project.yaml -o llm.txt 重新生成")
    print(f"   3. 开始你的 Vibe Development 之旅!")


def create_doc_templates(docs_dir: Path, project_name: str):
    """创建文档模板"""
    
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
*最后更新: {project_name} 初始化*
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
    (docs_dir / "CONTEXT.md").write_text(context_content, encoding="utf-8")
    (docs_dir / "DECISIONS.md").write_text(decisions_content, encoding="utf-8")
    (docs_dir / "CHANGELOG.md").write_text(changelog_content, encoding="utf-8")
    (docs_dir / "ROADMAP.md").write_text(roadmap_content, encoding="utf-8")
    (docs_dir / "QA_TEST_CASES.md").write_text(qa_content, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="LLM Collaboration Project Initializer")
    parser.add_argument("--name", "-n", required=True, help="项目名称")
    parser.add_argument("--domain", "-d", choices=DOMAINS, default="generic", help="业务领域")
    parser.add_argument("--output", "-o", required=True, help="输出目录")
    args = parser.parse_args()
    
    base_dir = Path(__file__).parent
    output_dir = Path(args.output)
    
    init_project(args.name, args.domain, output_dir, base_dir)


if __name__ == "__main__":
    main()
