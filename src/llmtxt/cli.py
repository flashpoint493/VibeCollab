"""
LLMTxt CLI - 命令行接口
"""

import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from . import __version__
from .generator import LLMTxtGenerator
from .project import Project
from .templates import TemplateManager

console = Console()

DOMAINS = ["generic", "game", "web", "data", "mobile", "infra"]


@click.group()
@click.version_option(version=__version__, prog_name="llmtxt")
def main():
    """LLMTxt - AI 协作规则文档生成器
    
    从 YAML 配置生成标准化的 llm.txt 文档，
    支持 Vibe Development 哲学的人机协作工程化部署。
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
    
        llmtxt init -n "MyProject" -d web -o ./my-project
        
        llmtxt init -n "GameProject" -d game -o ./game --force
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
    table.add_row("llm.txt", "AI 协作规则文档")
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
    console.print("  3. llmtxt generate -c project.yaml  # 重新生成")
    console.print("  4. 开始你的 Vibe Development 之旅!")


@main.command()
@click.option("--config", "-c", required=True, help="YAML 配置文件路径")
@click.option("--output", "-o", default="llm.txt", help="输出文件路径")
def generate(config: str, output: str):
    """从配置文件生成 llm.txt
    
    Examples:
    
        llmtxt generate -c project.yaml -o llm.txt
        
        llmtxt generate -c my-config.yaml
    """
    config_path = Path(config)
    output_path = Path(output)
    
    if not config_path.exists():
        console.print(f"[red]错误:[/red] 配置文件不存在: {config}")
        raise SystemExit(1)
    
    with console.status("[bold green]正在生成 llm.txt..."):
        try:
            generator = LLMTxtGenerator.from_file(config_path)
            content = generator.generate()
            output_path.write_text(content, encoding="utf-8")
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
    
        llmtxt validate -c project.yaml
    """
    config_path = Path(config)
    
    if not config_path.exists():
        console.print(f"[red]错误:[/red] 配置文件不存在: {config}")
        raise SystemExit(1)
    
    with console.status("[bold green]正在验证配置..."):
        try:
            generator = LLMTxtGenerator.from_file(config_path)
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
    
        llmtxt export-template -t default -o my-project.yaml
        
        llmtxt export-template -t game -o game-project.yaml
    """
    tm = TemplateManager()
    output_path = Path(output)
    
    try:
        content = tm.get_template(template)
        output_path.write_text(content, encoding="utf-8")
        console.print(f"[green]✅ 已导出模板:[/green] {output_path}")
    except FileNotFoundError:
        console.print(f"[red]错误:[/red] 模板不存在: {template}")
        console.print("[dim]使用 'llmtxt templates' 查看可用模板[/dim]")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
