"""
LLMContext CLI - 命令行接口
"""

import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
import yaml

from . import __version__
from .generator import LLMContextGenerator
from .project import Project
from .templates import TemplateManager
from .llmstxt import LLMsTxtManager

console = Console()

DOMAINS = ["generic", "game", "web", "data", "mobile", "infra"]


def deep_merge(base: dict, override: dict) -> dict:
    """深度合并两个字典，override 优先"""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


@click.group()
@click.version_option(version=__version__, prog_name="vibecollab")
def main():
    """VibeCollab - AI 协作协议生成器
    
    从 YAML 配置生成标准化的 AI 协作协议文档，
    支持 Vibe Development 哲学的人机协作工程化部署。
    自动集成 llms.txt 标准。
    """
    pass


@main.command()
@click.option("--name", "-n", required=True, help="项目名称")
@click.option(
    "--domain", "-d",
    type=click.Choice(DOMAINS),
    default="generic",
    help="业务领域"
)
@click.option("--output", "-o", required=True, help="输出目录")
@click.option("--force", "-f", is_flag=True, help="强制覆盖已存在的目录")
def init(name: str, domain: str, output: str, force: bool):
    """初始化新项目
    
    Examples:
    
        vibecollab init -n "MyProject" -d web -o ./my-project
        
        vibecollab init -n "GameProject" -d game -o ./game --force
    """
    output_path = Path(output)
    
    if output_path.exists() and not force:
        if any(output_path.iterdir()):
            console.print(f"[red]错误:[/red] 目录 {output} 已存在且非空。使用 --force 强制覆盖。")
            raise SystemExit(1)
    
    with console.status(f"[bold green]正在初始化项目 {name}..."):
        try:
            project = Project.create(name=name, domain=domain, output_dir=output_path)
            project.generate_all()
        except Exception as e:
            console.print(f"[red]错误:[/red] {e}")
            raise SystemExit(1)
    
    # 成功提示
    console.print()
    console.print(Panel.fit(
        f"[bold green]✅ 项目 {name} 初始化成功![/bold green]\n\n"
        f"[dim]目录:[/dim] {output_path.absolute()}\n"
        f"[dim]领域:[/dim] {domain}",
        title="完成"
    ))
    
    # 生成的文件列表
    table = Table(title="生成的文件", show_header=True)
    table.add_column("文件", style="cyan")
    table.add_column("说明")
    table.add_row("CONTRIBUTING_AI.md", "AI 协作规则文档")
    table.add_row("llms.txt", "项目上下文文档（已集成协作规则引用）")
    table.add_row("project.yaml", "项目配置 (可编辑)")
    table.add_row("docs/CONTEXT.md", "当前上下文")
    table.add_row("docs/DECISIONS.md", "决策记录")
    table.add_row("docs/CHANGELOG.md", "变更日志")
    table.add_row("docs/ROADMAP.md", "路线图")
    table.add_row("docs/QA_TEST_CASES.md", "测试用例")
    console.print(table)
    
    # 下一步提示
    console.print()
    console.print("[bold]下一步:[/bold]")
    console.print(f"  1. cd {output}")
    console.print("  2. 编辑 project.yaml 自定义配置")
    console.print("  3. vibecollab generate -c project.yaml  # 重新生成")
    console.print("  4. 开始你的 Vibe Development 之旅!")


@main.command()
@click.option("--config", "-c", required=True, help="YAML 配置文件路径")
@click.option("--output", "-o", default="CONTRIBUTING_AI.md", help="输出文件路径")
@click.option("--no-llmstxt", is_flag=True, help="不集成 llms.txt")
def generate(config: str, output: str, no_llmstxt: bool):
    """从配置文件生成 AI 协作规则文档并集成 llms.txt
    
    Examples:
    
        vibecollab generate -c project.yaml -o CONTRIBUTING_AI.md
        
        vibecollab generate -c my-config.yaml --no-llmstxt
    """
    config_path = Path(config)
    output_path = Path(output)
    project_root = config_path.parent
    
    if not config_path.exists():
        console.print(f"[red]错误:[/red] 配置文件不存在: {config}")
        raise SystemExit(1)
    
    with console.status("[bold green]正在生成协作规则文档..."):
        try:
            generator = LLMContextGenerator.from_file(config_path, project_root)
            content = generator.generate()
            output_path.write_text(content, encoding="utf-8")
            
            # 集成 llms.txt（除非指定不集成）
            if not no_llmstxt:
                project_config = generator.config
                project_name = project_config.get("project", {}).get("name", "Project")
                project_desc = project_config.get("project", {}).get("description", "AI-assisted development project")
                
                updated, llmstxt_path = LLMsTxtManager.ensure_integration(
                    project_root,
                    project_name,
                    project_desc,
                    output_path
                )
                
                if updated:
                    if llmstxt_path and llmstxt_path.exists():
                        console.print(f"[green]✅ 已更新:[/green] {llmstxt_path}")
                    else:
                        console.print(f"[green]✅ 已创建:[/green] {llmstxt_path}")
                else:
                    console.print(f"[dim]ℹ️  llms.txt 已包含协作规则引用[/dim]")
        except Exception as e:
            console.print(f"[red]错误:[/red] {e}")
            raise SystemExit(1)
    
    console.print(f"[green]✅ 已生成:[/green] {output_path}")
    console.print(f"[dim]配置:[/dim] {config_path}")


@main.command()
@click.option("--config", "-c", required=True, help="YAML 配置文件路径")
def validate(config: str):
    """验证配置文件
    
    Examples:
    
        vibecollab validate -c project.yaml
    """
    config_path = Path(config)
    
    if not config_path.exists():
        console.print(f"[red]错误:[/red] 配置文件不存在: {config}")
        raise SystemExit(1)
    
    with console.status("[bold green]正在验证配置..."):
        try:
            generator = LLMContextGenerator.from_file(config_path)
            errors = generator.validate()
        except Exception as e:
            console.print(f"[red]错误:[/red] 解析失败: {e}")
            raise SystemExit(1)
    
    if errors:
        console.print(f"[red]❌ 发现 {len(errors)} 个问题:[/red]")
        for err in errors:
            console.print(f"  - {err}")
        raise SystemExit(1)
    else:
        console.print(f"[green]✅ 配置有效:[/green] {config}")


@main.command()
def domains():
    """列出支持的业务领域"""
    table = Table(title="支持的业务领域", show_header=True)
    table.add_column("领域", style="cyan")
    table.add_column("说明")
    table.add_column("特有配置")
    
    domain_info = {
        "generic": ("通用项目", "基础配置"),
        "game": ("游戏开发", "GM 控制台、GDD 文档"),
        "web": ("Web 应用", "API 文档、部署环境"),
        "data": ("数据工程", "ETL 管道、数据质量"),
        "mobile": ("移动应用", "平台适配、发布流程"),
        "infra": ("基础设施", "IaC、监控告警"),
    }
    
    for domain in DOMAINS:
        desc, features = domain_info.get(domain, ("", ""))
        table.add_row(domain, desc, features)
    
    console.print(table)


@main.command()
def templates():
    """列出可用的模板"""
    tm = TemplateManager()
    available = tm.list_templates()
    
    table = Table(title="可用模板", show_header=True)
    table.add_column("模板", style="cyan")
    table.add_column("类型")
    table.add_column("路径")
    
    for tpl in available:
        table.add_row(tpl["name"], tpl["type"], str(tpl["path"]))
    
    console.print(table)


@main.command()
@click.option("--template", "-t", default="default", help="模板名称")
@click.option("--output", "-o", default="project.yaml", help="输出文件路径")
def export_template(template: str, output: str):
    """导出模板配置文件
    
    Examples:
    
        vibecollab export-template -t default -o my-project.yaml
        
        vibecollab export-template -t game -o game-project.yaml
    """
    tm = TemplateManager()
    output_path = Path(output)
    
    try:
        content = tm.get_template(template)
        output_path.write_text(content, encoding="utf-8")
        console.print(f"[green]✅ 已导出模板:[/green] {output_path}")
    except FileNotFoundError:
        console.print(f"[red]错误:[/red] 模板不存在: {template}")
        console.print("[dim]使用 'vibecollab templates' 查看可用模板[/dim]")
        raise SystemExit(1)


@main.command()
@click.option("--config", "-c", default="project.yaml", help="项目配置文件路径")
@click.option("--dry-run", is_flag=True, help="仅显示变更，不实际修改")
@click.option("--force", "-f", is_flag=True, help="强制升级，不备份")
def upgrade(config: str, dry_run: bool, force: bool):
    """升级协议到最新版本
    
    智能合并：保留用户自定义配置，同时获取最新协议功能。
    
    Examples:
    
        vibecollab upgrade                    # 升级当前目录的项目
        
        vibecollab upgrade -c project.yaml    # 指定配置文件
        
        vibecollab upgrade --dry-run          # 预览变更
    """
    config_path = Path(config)
    
    if not config_path.exists():
        console.print(f"[red]错误:[/red] 配置文件不存在: {config}")
        console.print("[dim]提示: 在项目目录下运行，或使用 -c 指定配置文件路径[/dim]")
        raise SystemExit(1)
    
    # 读取用户配置
    with open(config_path, encoding="utf-8") as f:
        user_config = yaml.safe_load(f)
    
    # 获取最新模板
    tm = TemplateManager()
    latest_template = yaml.safe_load(tm.get_template("default"))
    
    # 记录用户自定义的关键字段（不应被覆盖）
    user_preserved = {
        "project": user_config.get("project", {}),
        "roles": user_config.get("roles"),
        "confirmed_decisions": user_config.get("confirmed_decisions"),
        "domain_extensions": user_config.get("domain_extensions"),
    }
    
    # 深度合并：latest 为 base，user_preserved 覆盖
    merged = deep_merge(latest_template, {k: v for k, v in user_preserved.items() if v is not None})
    
    # 分析变更
    new_sections = []
    for key in latest_template:
        if key not in user_config:
            new_sections.append(key)
    
    if dry_run:
        console.print(Panel.fit(
            f"[bold yellow]预览模式[/bold yellow] - 不会修改任何文件",
            title="Dry Run"
        ))
        console.print()
        
        if new_sections:
            console.print("[bold]📦 将新增以下配置项:[/bold]")
            for section in new_sections:
                console.print(f"  [green]+ {section}[/green]")
        else:
            console.print("[dim]没有新增配置项[/dim]")
        
        console.print()
        console.print("[bold]🔒 将保留以下用户配置:[/bold]")
        console.print(f"  • project.name: {user_preserved['project'].get('name', '(未设置)')}")
        console.print(f"  • project.domain: {user_preserved['project'].get('domain', '(未设置)')}")
        if user_preserved.get('roles'):
            console.print(f"  • roles: {len(user_preserved['roles'])} 个角色")
        if user_preserved.get('confirmed_decisions'):
            console.print(f"  • confirmed_decisions: {len(user_preserved['confirmed_decisions'])} 条决策")
        
        console.print()
        console.print(f"[dim]移除 --dry-run 执行实际升级[/dim]")
        return
    
    # 备份原配置
    if not force:
        backup_path = config_path.with_suffix(".yaml.bak")
        config_path.rename(backup_path)
        console.print(f"[dim]已备份原配置到: {backup_path}[/dim]")
    
    # 写入合并后的配置
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(merged, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    # 重新生成协作规则文档并集成 llms.txt
    contributing_ai_path = config_path.parent / "CONTRIBUTING_AI.md"
    generator = LLMContextGenerator(merged, config_path.parent)
    contributing_ai_path.write_text(generator.generate(), encoding="utf-8")
    
    # 集成 llms.txt
    project_name = merged.get("project", {}).get("name", "Project")
    project_desc = merged.get("project", {}).get("description", "AI-assisted development project")
    LLMsTxtManager.ensure_integration(
        config_path.parent,
        project_name,
        project_desc,
        contributing_ai_path
    )
    
    # 成功提示
    console.print()
    console.print(Panel.fit(
        f"[bold green]✅ 协议已升级到 v{__version__}[/bold green]",
        title="升级完成"
    ))
    
    if new_sections:
        console.print()
        console.print("[bold]📦 新增配置项:[/bold]")
        for section in new_sections:
            console.print(f"  [green]+ {section}[/green]")
    
    console.print()
    console.print("[bold]已更新文件:[/bold]")
    console.print(f"  • {config_path}")
    console.print(f"  • {llm_txt_path}")
    
    console.print()
    console.print("[dim]提示: 使用 git diff 查看具体变更[/dim]")


@main.command()
def version_info():
    """显示版本和协议信息"""
    console.print(Panel.fit(
        f"[bold]LLMContext[/bold] v{__version__}\n\n"
        f"[dim]协议版本:[/dim] 1.0\n"
        f"[dim]支持领域:[/dim] {', '.join(DOMAINS)}\n"
        f"[dim]Python:[/dim] 3.8+",
        title="版本信息"
    ))


if __name__ == "__main__":
    main()
