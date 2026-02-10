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
import sys
import platform
from typing import Optional, Tuple

from . import __version__
from .generator import LLMContextGenerator
from .project import Project
from .templates import TemplateManager
from .llmstxt import LLMsTxtManager
from .git_utils import is_git_repo
from .lifecycle import LifecycleManager
from .protocol_checker import ProtocolChecker

# 检测是否为 Windows 且使用 GBK 编码
def is_windows_gbk():
    """检测是否为 Windows 且使用 GBK 编码"""
    if platform.system() != "Windows":
        return False
    try:
        # 尝试编码 emoji，如果失败说明不支持
        "✅⚠️❌ℹ️".encode(sys.stdout.encoding or "utf-8")
        return False
    except (UnicodeEncodeError, LookupError):
        return True

# 根据环境选择是否使用 emoji
USE_EMOJI = not is_windows_gbk()

# emoji 和特殊字符替代方案
EMOJI_MAP = {
    "error": "X" if not USE_EMOJI else "❌",
    "warning": "!" if not USE_EMOJI else "⚠️",
    "info": "i" if not USE_EMOJI else "ℹ️",
    "success": "OK" if not USE_EMOJI else "✅",
    "lock": "[保留]" if not USE_EMOJI else "🔒",
    "sparkles": "+" if not USE_EMOJI else "✨"
}

# bullet point 替代
BULLET = "-" if is_windows_gbk() else "•"

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
@click.option("--no-git", is_flag=True, help="不自动初始化 Git 仓库")
@click.option("--multi-dev", is_flag=True, help="启用多开发者模式")
def init(name: str, domain: str, output: str, force: bool, no_git: bool, multi_dev: bool):
    """初始化新项目
    
    Examples:
    
        vibecollab init -n "MyProject" -d web -o ./my-project
        
        vibecollab init -n "GameProject" -d game -o ./game --force
        
        vibecollab init -n "TeamProject" -o ./team --multi-dev  # 多开发者模式
    """
    output_path = Path(output)
    
    if output_path.exists() and not force:
        if any(output_path.iterdir()):
            console.print(f"[red]错误:[/red] 目录 {output} 已存在且非空。使用 --force 强制覆盖。")
            raise SystemExit(1)
    
    with console.status(f"[bold green]正在初始化项目 {name}..."):
        try:
            project = Project.create(name=name, domain=domain, output_dir=output_path, multi_dev=multi_dev)
            project.generate_all(auto_init_git=not no_git)
        except Exception as e:
            console.print(f"[red]错误:[/red] {e}")
            raise SystemExit(1)
    
    # 成功提示
    console.print()
    mode_text = "多开发者" if multi_dev else "单开发者"
    console.print(Panel.fit(
        f"[bold green]{EMOJI_MAP['success']} 项目 {name} 初始化成功![/bold green]\n\n"
        f"[dim]目录:[/dim] {output_path.absolute()}\n"
        f"[dim]领域:[/dim] {domain}\n"
        f"[dim]模式:[/dim] {mode_text}",
        title="完成"
    ))
    
    # 生成的文件列表
    table = Table(title="生成的文件", show_header=True)
    table.add_column("文件", style="cyan")
    table.add_column("说明")
    table.add_row("CONTRIBUTING_AI.md", "AI 协作规则文档")
    table.add_row("llms.txt", "项目上下文文档（已集成协作规则引用）")
    table.add_row("project.yaml", "项目配置 (可编辑)")
    
    if multi_dev:
        table.add_row("docs/CONTEXT.md", "全局聚合上下文（自动生成）")
        table.add_row("docs/developers/{dev}/CONTEXT.md", "各开发者上下文")
        table.add_row("docs/developers/COLLABORATION.md", "协作文档")
    else:
        table.add_row("docs/CONTEXT.md", "当前上下文")
    
    table.add_row("docs/DECISIONS.md", "决策记录")
    table.add_row("docs/CHANGELOG.md", "变更日志")
    table.add_row("docs/ROADMAP.md", "路线图")
    table.add_row("docs/QA_TEST_CASES.md", "测试用例")
    console.print(table)
    
    # Git 状态提示
    git_warning = project.config.get("_meta", {}).get("git_warning")
    git_auto_init = project.config.get("_meta", {}).get("git_auto_init", False)
    
    if git_auto_init:
        console.print()
        console.print(f"[green]{EMOJI_MAP['success']} Git 仓库已自动初始化[/green]")
    elif git_warning:
        console.print()
        console.print(f"[yellow]{EMOJI_MAP['warning']} {git_warning}[/yellow]")
        console.print("[dim]提示: 建议初始化 Git 仓库以跟踪项目变更[/dim]")
    
    # 多开发者模式额外提示
    if multi_dev:
        from .developer import DeveloperManager
        dm = DeveloperManager(output_path, project.config)
        current_dev = dm.get_current_developer()
        
        console.print()
        console.print(f"[bold cyan]多开发者模式已启用[/bold cyan]")
        console.print(f"  {BULLET} 当前开发者: {current_dev}")
        console.print(f"  {BULLET} 使用 'vibecollab dev' 查看相关命令")
    
    # 下一步提示
    console.print()
    console.print("[bold]下一步:[/bold]")
    console.print(f"  1. cd {output}")
    step = 2
    if not is_git_repo(output_path):
        console.print(f"  {step}. git init  # 初始化 Git 仓库（如未自动初始化）")
        step += 1
    if multi_dev:
        console.print(f"  {step}. vibecollab dev whoami  # 查看当前开发者")
        step += 1
    console.print(f"  {step}. 编辑 project.yaml 自定义配置")
    step += 1
    console.print(f"  {step}. vibecollab generate -c project.yaml  # 重新生成")
    step += 1
    console.print(f"  {step}. 开始你的 Vibe Development 之旅!")


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
                        console.print(f"[green]{EMOJI_MAP['success']} 已更新:[/green] {llmstxt_path}")
                    else:
                        console.print(f"[green]{EMOJI_MAP['success']} 已创建:[/green] {llmstxt_path}")
                else:
                    console.print(f"[dim]Info: llms.txt 已包含协作规则引用[/dim]")
        except Exception as e:
            console.print(f"[red]错误:[/red] {e}")
            raise SystemExit(1)
    
    console.print(f"[green]{EMOJI_MAP['success']} 已生成:[/green] {output_path}")
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
        console.print(f"[red]{EMOJI_MAP['error']} 发现 {len(errors)} 个问题:[/red]")
        for err in errors:
            console.print(f"  - {err}")
        raise SystemExit(1)
    else:
        console.print(f"[green]{EMOJI_MAP['success']} 配置有效:[/green] {config}")


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
        console.print(f"[green]{EMOJI_MAP['success']} 已导出模板:[/green] {output_path}")
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
        "multi_developer": user_config.get("multi_developer"),  # v0.5.0+ 保留多开发者配置
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
        console.print(f"[bold]{EMOJI_MAP['lock']} 将保留以下用户配置:[/bold]")
        console.print(f"  {BULLET} project.name: {user_preserved['project'].get('name', '(未设置)')}")
        console.print(f"  {BULLET} project.domain: {user_preserved['project'].get('domain', '(未设置)')}")
        if user_preserved.get('roles'):
            console.print(f"  {BULLET} roles: {len(user_preserved['roles'])} 个角色")
        if user_preserved.get('confirmed_decisions'):
            console.print(f"  {BULLET} confirmed_decisions: {len(user_preserved['confirmed_decisions'])} 条决策")
        
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
    
    # 检查并初始化多开发者目录结构
    multi_dev_config = merged.get("multi_developer", {})
    if multi_dev_config.get("enabled", False):
        from .developer import DeveloperManager, ContextAggregator
        from datetime import datetime
        
        dm = DeveloperManager(config_path.parent, merged)
        developers_dir = config_path.parent / "docs" / "developers"
        
        # 检查是否需要初始化
        initialized = False
        
        # 初始化每个开发者的上下文
        developers = multi_dev_config.get("developers", [])
        for dev in developers:
            dev_id = dev.get("id")
            if not dev_id:
                continue
            
            dev_dir = developers_dir / dev_id
            if not dev_dir.exists():
                dm.init_developer_context(dev_id)
                console.print(f"  [green]{EMOJI_MAP['sparkles']} 已初始化开发者目录: docs/developers/{dev_id}/[/green]")
                initialized = True
        
        # 创建 COLLABORATION.md
        collab_config = multi_dev_config.get('collaboration', {})
        collab_file = config_path.parent / collab_config.get('file', 'docs/developers/COLLABORATION.md')
        
        if not collab_file.exists():
            collab_file.parent.mkdir(parents=True, exist_ok=True)
            today = datetime.now().strftime("%Y-%m-%d")
            
            collab_content = f"""# {project_name} 开发者协作记录

## 当前协作关系

(暂无协作记录)

## 任务分配矩阵

| 任务 | 负责人 | 协作者 | 状态 | 依赖 |
|------|--------|--------|------|------|
| (待分配) | - | - | - | - |

## 里程碑追踪

(暂无里程碑)

## 协作规则约定

1. **文档更新**: 每次任务完成后更新自己的 CONTEXT.md
2. **冲突避免**: 修改共享文档前先检查是否有其他开发者正在编辑
3. **交接流程**: 任务交接时在本文档记录交接内容

## 交接记录

(暂无交接记录)

---
*最后更新: {today}*
"""
            collab_file.write_text(collab_content, encoding='utf-8')
            console.print(f"  [green]{EMOJI_MAP['sparkles']} 已创建协作文档: {collab_config.get('file', 'docs/developers/COLLABORATION.md')}[/green]")
            initialized = True
        
        # 生成全局聚合 CONTEXT.md
        aggregator = ContextAggregator(config_path.parent, merged)
        global_context = config_path.parent / "docs" / "CONTEXT.md"
        if not global_context.exists() or initialized:
            aggregator.generate_and_save()
            console.print(f"  [green]{EMOJI_MAP['sparkles']} 已生成全局上下文聚合: docs/CONTEXT.md[/green]")
    
    # 成功提示
    console.print()
    console.print(Panel.fit(
        f"[bold green]{EMOJI_MAP['success']} 协议已升级到 v{__version__}[/bold green]",
        title="升级完成"
    ))
    
    if new_sections:
        console.print()
        console.print("[bold]📦 新增配置项:[/bold]")
        for section in new_sections:
            console.print(f"  [green]+ {section}[/green]")
    
    console.print()
    console.print("[bold]已更新文件:[/bold]")
    console.print(f"  {BULLET} {config_path}")
    console.print(f"  {BULLET} {contributing_ai_path}")
    
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


@main.command()
@click.option("--config", "-c", default="project.yaml", help="项目配置文件路径")
@click.option("--strict", is_flag=True, help="严格模式：任何警告都视为失败")
def check(config: str, strict: bool):
    """检查协议遵循情况
    
    检查项目是否遵循了 CONTRIBUTING_AI.md 中定义的协作协议。
    
    Examples:
    
        vibecollab check                    # 检查当前目录的项目
        
        vibecollab check -c project.yaml    # 指定配置文件
        
        vibecollab check --strict           # 严格模式
    """
    config_path = Path(config)
    project_root = config_path.parent
    
    if not config_path.exists():
        console.print(f"[red]错误:[/red] 配置文件不存在: {config}")
        console.print("[dim]提示: 在项目目录下运行，或使用 -c 指定配置文件路径[/dim]")
        raise SystemExit(1)
    
    # 加载配置
    with open(config_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)
    
    # 执行检查
    checker = ProtocolChecker(project_root, project_config)
    results = checker.check_all()
    summary = checker.get_summary(results)
    
    # 显示结果
    console.print()
    console.print(Panel.fit(
        f"[bold]协议遵循情况检查[/bold]",
        title="Protocol Check"
    ))
    console.print()
    
    # 按严重程度分组显示
    errors = [r for r in results if r.severity == "error"]
    warnings = [r for r in results if r.severity == "warning"]
    infos = [r for r in results if r.severity == "info"]
    
    if errors:
        console.print(f"[bold red]{EMOJI_MAP['error']} 错误:[/bold red]")
        for result in errors:
            console.print(f"  {BULLET} {result.name}: {result.message}")
            if result.suggestion:
                console.print(f"    [dim]建议: {result.suggestion}[/dim]")
        console.print()
    
    if warnings:
        console.print(f"[bold yellow]{EMOJI_MAP['warning']} 警告:[/bold yellow]")
        for result in warnings:
            console.print(f"  {BULLET} {result.name}: {result.message}")
            if result.suggestion:
                console.print(f"    [dim]建议: {result.suggestion}[/dim]")
        console.print()
    
    if infos:
        console.print(f"[bold blue]{EMOJI_MAP['info']} 信息:[/bold blue]")
        for result in infos:
            console.print(f"  {BULLET} {result.name}: {result.message}")
            if result.suggestion:
                console.print(f"    [dim]建议: {result.suggestion}[/dim]")
        console.print()
    
    # 显示摘要
    if summary["all_passed"] and not (strict and warnings):
        console.print(Panel.fit(
            f"[bold green]{EMOJI_MAP['success']} 所有检查通过[/bold green]\n\n"
            f"总计: {summary['total']} 项检查",
            title="检查完成"
        ))
    else:
        status = "失败" if errors or (strict and warnings) else "有警告"
        color = "red" if errors or (strict and warnings) else "yellow"
        emoji = EMOJI_MAP['error'] if errors or (strict and warnings) else EMOJI_MAP['warning']
        console.print(Panel.fit(
            f"[bold {color}]{emoji} 检查{status}[/bold {color}]\n\n"
            f"总计: {summary['total']} 项\n"
            f"错误: {summary['errors']} 项\n"
            f"警告: {summary['warnings']} 项",
            title="检查完成"
        ))
        if strict and warnings:
            console.print()
            console.print("[dim]提示: 使用 --strict 时，警告也会被视为失败[/dim]")
    
    # 返回退出码
    if errors or (strict and warnings):
        raise SystemExit(1)


# 导入生涯管理命令
from .cli_lifecycle import lifecycle as lifecycle_group
main.add_command(lifecycle_group)


# ============================================
# 多开发者管理命令组 (v0.5.0+)
# ============================================

@main.group()
def dev():
    """多开发者管理命令
    
    管理多开发者协同开发的项目。
    """
    pass


@dev.command("whoami")
@click.option("--config", "-c", default="project.yaml", help="项目配置文件路径")
def dev_whoami(config: str):
    """显示当前开发者身份
    
    Examples:
    
        vibecollab dev whoami
    """
    from .developer import DeveloperManager
    
    config_path = Path(config)
    project_root = config_path.parent
    
    if not config_path.exists():
        console.print(f"[red]错误:[/red] 配置文件不存在: {config}")
        raise SystemExit(1)
    
    with open(config_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)
    
    dm = DeveloperManager(project_root, project_config)
    current_dev = dm.get_current_developer()
    
    multi_dev_enabled = project_config.get('multi_developer', {}).get('enabled', False)
    
    console.print()
    console.print(Panel.fit(
        f"[bold cyan]{current_dev}[/bold cyan]\n\n"
        f"多开发者模式: {'[green]启用[/green]' if multi_dev_enabled else '[yellow]未启用[/yellow]'}\n"
        f"识别方式: {project_config.get('multi_developer', {}).get('identity', {}).get('primary', 'git_username')}",
        title="当前开发者"
    ))
    console.print()


@dev.command("list")
@click.option("--config", "-c", default="project.yaml", help="项目配置文件路径")
def dev_list(config: str):
    """列出所有开发者
    
    Examples:
    
        vibecollab dev list
    """
    from .developer import DeveloperManager
    
    config_path = Path(config)
    project_root = config_path.parent
    
    if not config_path.exists():
        console.print(f"[red]错误:[/red] 配置文件不存在: {config}")
        raise SystemExit(1)
    
    with open(config_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)
    
    multi_dev_enabled = project_config.get('multi_developer', {}).get('enabled', False)
    if not multi_dev_enabled:
        console.print(f"[yellow]{EMOJI_MAP['warning']} 多开发者模式未启用[/yellow]")
        console.print("[dim]在 project.yaml 中设置 multi_developer.enabled: true[/dim]")
        raise SystemExit(1)
    
    dm = DeveloperManager(project_root, project_config)
    developers = dm.list_developers()
    current_dev = dm.get_current_developer()
    
    if not developers:
        console.print()
        console.print("[yellow]暂无开发者[/yellow]")
        console.print("[dim]使用 'vibecollab init --multi-dev' 初始化多开发者项目[/dim]")
        console.print()
        return
    
    table = Table(title="开发者列表", show_header=True)
    table.add_column("开发者", style="cyan")
    table.add_column("状态")
    table.add_column("上次更新")
    table.add_column("更新次数")
    
    for dev in developers:
        status_info = dm.get_developer_status(dev)
        is_current = " (当前)" if dev == current_dev else ""
        status = f"{EMOJI_MAP['success']} 活跃{is_current}" if status_info['exists'] else f"{EMOJI_MAP['warning']} 未初始化"
        last_updated = status_info.get('last_updated', '-') or '-'
        if last_updated != '-' and len(last_updated) > 19:
            last_updated = last_updated[:19]  # 截取日期时间部分
        total_updates = str(status_info.get('total_updates', 0))
        
        table.add_row(dev, status, last_updated, total_updates)
    
    console.print()
    console.print(table)
    console.print()


@dev.command("status")
@click.argument("developer", required=False)
@click.option("--config", "-c", default="project.yaml", help="项目配置文件路径")
def dev_status(developer: Optional[str], config: str):
    """查看开发者状态
    
    Examples:
    
        vibecollab dev status           # 查看所有开发者
        
        vibecollab dev status alice     # 查看特定开发者
    """
    from .developer import DeveloperManager
    
    config_path = Path(config)
    project_root = config_path.parent
    
    if not config_path.exists():
        console.print(f"[red]错误:[/red] 配置文件不存在: {config}")
        raise SystemExit(1)
    
    with open(config_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)
    
    multi_dev_enabled = project_config.get('multi_developer', {}).get('enabled', False)
    if not multi_dev_enabled:
        console.print(f"[yellow]{EMOJI_MAP['warning']} 多开发者模式未启用[/yellow]")
        raise SystemExit(1)
    
    dm = DeveloperManager(project_root, project_config)
    
    if developer:
        # 显示特定开发者
        developers = [developer]
    else:
        # 显示所有开发者
        developers = dm.list_developers()
    
    if not developers:
        console.print()
        console.print("[yellow]暂无开发者[/yellow]")
        console.print()
        return
    
    for dev in developers:
        context_file = dm.get_developer_context_file(dev)
        if context_file.exists():
            console.print()
            console.print(Panel.fit(
                f"[bold]{dev}[/bold]",
                title="开发者状态"
            ))
            console.print()
            
            # 读取并显示 CONTEXT.md 摘要
            try:
                content = context_file.read_text(encoding='utf-8')
                # 显示前20行
                lines = content.split('\n')[:20]
                console.print('\n'.join(lines))
                if len(content.split('\n')) > 20:
                    console.print(f"\n[dim]... (更多内容见 {context_file})[/dim]")
            except Exception as e:
                console.print(f"[red]读取失败:[/red] {e}")
            
            console.print()
        else:
            console.print(f"[yellow]{EMOJI_MAP['warning']} 开发者 {dev} 未初始化[/yellow]")


@dev.command("sync")
@click.option("--config", "-c", default="project.yaml", help="项目配置文件路径")
def dev_sync(config: str):
    """手动触发全局 CONTEXT 聚合
    
    Examples:
    
        vibecollab dev sync
    """
    from .developer import ContextAggregator
    
    config_path = Path(config)
    project_root = config_path.parent
    
    if not config_path.exists():
        console.print(f"[red]错误:[/red] 配置文件不存在: {config}")
        raise SystemExit(1)
    
    with open(config_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)
    
    multi_dev_enabled = project_config.get('multi_developer', {}).get('enabled', False)
    if not multi_dev_enabled:
        console.print(f"[yellow]{EMOJI_MAP['warning']} 多开发者模式未启用[/yellow]")
        raise SystemExit(1)
    
    console.print()
    console.print("[cyan]正在聚合全局 CONTEXT...[/cyan]")
    
    try:
        aggregator = ContextAggregator(project_root, project_config)
        output_file = aggregator.generate_and_save()
        
        console.print(f"[green]{EMOJI_MAP['success']} 聚合完成:[/green] {output_file}")
        console.print()
    except Exception as e:
        console.print(f"[red]聚合失败:[/red] {e}")
        raise SystemExit(1)


@dev.command("init")
@click.option("--config", "-c", default="project.yaml", help="项目配置文件路径")
@click.option("--developer", "-d", help="开发者名称（留空则自动识别）")
def dev_init(config: str, developer: Optional[str]):
    """初始化当前开发者的上下文
    
    Examples:
    
        vibecollab dev init                 # 自动识别当前开发者
        
        vibecollab dev init -d alice        # 为 alice 初始化
    """
    from .developer import DeveloperManager
    
    config_path = Path(config)
    project_root = config_path.parent
    
    if not config_path.exists():
        console.print(f"[red]错误:[/red] 配置文件不存在: {config}")
        raise SystemExit(1)
    
    with open(config_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)
    
    multi_dev_enabled = project_config.get('multi_developer', {}).get('enabled', False)
    if not multi_dev_enabled:
        console.print(f"[yellow]{EMOJI_MAP['warning']} 多开发者模式未启用[/yellow]")
        console.print("[dim]在 project.yaml 中设置 multi_developer.enabled: true[/dim]")
        raise SystemExit(1)
    
    dm = DeveloperManager(project_root, project_config)
    
    if developer is None:
        developer = dm.get_current_developer()
    
    console.print()
    console.print(f"[cyan]正在初始化开发者:[/cyan] {developer}")
    
    try:
        dm.init_developer_context(developer)
        context_file = dm.get_developer_context_file(developer)
        
        console.print(f"[green]{EMOJI_MAP['success']} 初始化完成:[/green]")
        console.print(f"  {BULLET} 上下文文件: {context_file}")
        console.print()
    except Exception as e:
        console.print(f"[red]初始化失败:[/red] {e}")
        raise SystemExit(1)


@dev.command("conflicts")
@click.option("--config", "-c", default="project.yaml", help="项目配置文件路径")
@click.option("--verbose", "-v", is_flag=True, help="显示详细冲突信息")
@click.option("--between", nargs=2, help="检测两个特定开发者之间的冲突 (例: --between alice bob)")
def dev_conflicts(config: str, verbose: bool, between: Optional[Tuple[str, str]]):
    """检测跨开发者工作冲突
    
    检测多个开发者之间的潜在冲突，包括文件冲突、任务冲突、依赖冲突等。
    
    Examples:
    
        vibecollab dev conflicts                 # 检测所有开发者的冲突
        
        vibecollab dev conflicts -v              # 显示详细信息
        
        vibecollab dev conflicts --between alice bob  # 检测特定两人之间的冲突
    """
    from .conflict_detector import ConflictDetector
    
    config_path = Path(config)
    project_root = config_path.parent
    
    if not config_path.exists():
        console.print(f"[red]错误:[/red] 配置文件不存在: {config}")
        raise SystemExit(1)
    
    with open(config_path, encoding="utf-8") as f:
        project_config = yaml.safe_load(f)
    
    multi_dev_enabled = project_config.get('multi_developer', {}).get('enabled', False)
    if not multi_dev_enabled:
        console.print(f"[yellow]{EMOJI_MAP['warning']} 多开发者模式未启用[/yellow]")
        console.print("[dim]在 project.yaml 中设置 multi_developer.enabled: true[/dim]")
        raise SystemExit(1)
    
    console.print()
    console.print("[cyan]正在检测跨开发者冲突...[/cyan]")
    console.print()
    
    try:
        detector = ConflictDetector(project_root, project_config)
        
        # 执行冲突检测
        conflicts = detector.detect_all_conflicts(
            target_developer=None,
            between_developers=between
        )
        
        # 生成并显示报告
        report = detector.generate_conflict_report(conflicts, verbose=verbose)
        console.print(report)
        
        # 如果有冲突，返回非零退出码
        if conflicts:
            raise SystemExit(1)
        
    except Exception as e:
        console.print(f"[red]冲突检测失败:[/red] {e}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise SystemExit(1)




if __name__ == "__main__":
    main()
