"""
Insight CLI 命令组 — 沉淀系统的 CLI 接口

提供沉淀的 CRUD、搜索、使用、衰减、一致性校验等功能。

命令:
    vibecollab insight list               列出所有沉淀
    vibecollab insight show <id>          查看沉淀详情
    vibecollab insight add                交互式创建沉淀
    vibecollab insight search --tags ...  按标签搜索
    vibecollab insight use <id>           记录一次使用
    vibecollab insight decay              执行权重衰减
    vibecollab insight check              一致性校验
"""

import sys
from pathlib import Path

import click
import yaml


def _load_insight_manager(config_path: str = "project.yaml"):
    """加载 InsightManager 实例"""
    from .event_log import EventLog
    from .insight_manager import InsightManager

    project_root = Path.cwd()
    event_log = EventLog(project_root / ".vibecollab" / "events.jsonl")
    return InsightManager(project_root=project_root, event_log=event_log)


def _load_developer_manager(config_path: str = "project.yaml"):
    """加载 DeveloperManager 实例"""
    from .developer import DeveloperManager

    project_root = Path.cwd()
    config_file = project_root / config_path
    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
    else:
        config = {}
    return DeveloperManager(project_root, config)


@click.group()
def insight():
    """沉淀系统管理命令

    管理从开发实践中提炼的可复用知识单元。
    """
    pass


@insight.command("list")
@click.option("--active-only", is_flag=True, default=False, help="仅显示活跃沉淀")
@click.option("--json", "as_json", is_flag=True, default=False, help="JSON 格式输出")
def list_insights(active_only, as_json):
    """列出所有沉淀"""
    import json as json_mod

    mgr = _load_insight_manager()
    all_insights = mgr.list_all()
    entries, _ = mgr.get_registry()

    if active_only:
        active_ids = {iid for iid, e in entries.items() if e.active}
        all_insights = [ins for ins in all_insights if ins.id in active_ids]

    if as_json:
        data = []
        for ins in all_insights:
            entry = entries.get(ins.id)
            item = {
                "id": ins.id,
                "title": ins.title,
                "category": ins.category,
                "tags": ins.tags,
                "weight": round(entry.weight, 4) if entry else 1.0,
                "active": entry.active if entry else True,
                "used_count": entry.used_count if entry else 0,
            }
            data.append(item)
        click.echo(json_mod.dumps(data, ensure_ascii=False, indent=2))
        return

    if not all_insights:
        click.echo("暂无沉淀条目。使用 `vibecollab insight add` 创建。")
        return

    click.echo(f"共 {len(all_insights)} 条沉淀：\n")
    for ins in all_insights:
        entry = entries.get(ins.id)
        weight = f"{entry.weight:.2f}" if entry else "1.00"
        active_mark = "" if (entry and entry.active) else " [INACTIVE]"
        tags_str = ", ".join(ins.tags[:5])
        click.echo(f"  {ins.id}  [{ins.category}]  {ins.title}")
        click.echo(f"          tags: {tags_str}  weight: {weight}{active_mark}")


@insight.command("show")
@click.argument("insight_id")
def show_insight(insight_id):
    """查看沉淀详情"""
    mgr = _load_insight_manager()
    ins = mgr.get(insight_id)
    if not ins:
        click.echo(f"未找到沉淀: {insight_id}", err=True)
        sys.exit(1)

    entries, _ = mgr.get_registry()
    entry = entries.get(insight_id)

    click.echo(f"ID:       {ins.id}")
    click.echo(f"Title:    {ins.title}")
    click.echo(f"Category: {ins.category}")
    click.echo(f"Tags:     {', '.join(ins.tags)}")
    if ins.summary:
        click.echo(f"Summary:  {ins.summary}")
    click.echo(f"Origin:   created by {ins.origin.created_by} on {ins.origin.created_at}")
    if ins.origin.derived_from:
        click.echo(f"Derived:  {', '.join(ins.origin.derived_from)}")
    click.echo("\n--- Body ---")
    click.echo(f"Scenario:   {ins.body.get('scenario', '(none)')}")
    click.echo(f"Approach:   {ins.body.get('approach', '(none)')}")
    if ins.body.get("validation"):
        click.echo(f"Validation: {ins.body['validation']}")
    if ins.body.get("constraints"):
        click.echo(f"Constraints: {', '.join(ins.body['constraints'])}")
    if ins.artifacts:
        click.echo("\n--- Artifacts ---")
        for a in ins.artifacts:
            click.echo(f"  {a.path} ({a.type})")

    if entry:
        click.echo("\n--- Registry ---")
        click.echo(f"Weight:     {entry.weight:.4f}")
        click.echo(f"Used:       {entry.used_count} times")
        click.echo(f"Active:     {entry.active}")
        if entry.last_used_at:
            click.echo(f"Last used:  {entry.last_used_at} by {entry.last_used_by}")

    click.echo(f"\nFingerprint: {ins.fingerprint[:32]}...")


@insight.command("add")
@click.option("--title", "-t", required=True, help="沉淀标题")
@click.option("--tags", required=True, help="标签列表，逗号分隔")
@click.option("--category", "-c", required=True,
              type=click.Choice(["technique", "workflow", "decision", "debug", "tool", "integration"]),
              help="分类")
@click.option("--scenario", "-s", required=True, help="适用场景")
@click.option("--approach", "-a", required=True, help="方法/步骤")
@click.option("--summary", default="", help="一句话摘要")
@click.option("--validation", default="", help="验证方法")
@click.option("--source-type", default=None, type=click.Choice(["task", "decision", "insight", "external"]))
@click.option("--source-ref", default=None, help="来源 ID（如 TASK-DEV-001）")
@click.option("--derived-from", default=None, help="派生自的 insight ID，逗号分隔")
def add_insight(title, tags, category, scenario, approach, summary,
                validation, source_type, source_ref, derived_from):
    """创建新的沉淀条目"""
    mgr = _load_insight_manager()
    dm = _load_developer_manager()

    created_by = dm.get_current_developer()
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    derived_list = [d.strip() for d in derived_from.split(",") if d.strip()] if derived_from else []

    body = {"scenario": scenario, "approach": approach}
    if validation:
        body["validation"] = validation

    ins = mgr.create(
        title=title,
        tags=tag_list,
        category=category,
        body=body,
        created_by=created_by,
        summary=summary,
        source_type=source_type,
        source_ref=source_ref,
        derived_from=derived_list,
    )

    # 记录到 developer contributed
    dm.add_contributed(ins.id, created_by)

    click.echo(f"已创建沉淀: {ins.id} — {ins.title}")
    click.echo(f"  tags: {', '.join(ins.tags)}")
    click.echo(f"  category: {ins.category}")
    click.echo(f"  created_by: {created_by}")


@insight.command("search")
@click.option("--tags", default=None, help="按标签搜索，逗号分隔")
@click.option("--category", default=None, help="按分类搜索")
@click.option("--include-inactive", is_flag=True, default=False, help="包含非活跃沉淀")
def search_insights(tags, category, include_inactive):
    """搜索沉淀"""
    mgr = _load_insight_manager()

    if not tags and not category:
        click.echo("请指定 --tags 或 --category", err=True)
        sys.exit(1)

    results = []
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        results = mgr.search_by_tags(tag_list, active_only=not include_inactive)
    elif category:
        results = mgr.search_by_category(category)

    if not results:
        click.echo("未找到匹配的沉淀。")
        return

    click.echo(f"找到 {len(results)} 条匹配：\n")
    entries, _ = mgr.get_registry()
    for ins in results:
        entry = entries.get(ins.id)
        weight = f"{entry.weight:.2f}" if entry else "1.00"
        click.echo(f"  {ins.id}  [{ins.category}]  {ins.title}  (weight: {weight})")
        click.echo(f"          tags: {', '.join(ins.tags)}")


@insight.command("use")
@click.argument("insight_id")
def use_insight(insight_id):
    """记录一次沉淀使用，奖励权重"""
    mgr = _load_insight_manager()
    dm = _load_developer_manager()
    used_by = dm.get_current_developer()

    entry = mgr.record_use(insight_id, used_by=used_by)
    if not entry:
        click.echo(f"未找到注册条目: {insight_id}", err=True)
        sys.exit(1)

    click.echo(f"已记录使用: {insight_id}")
    click.echo(f"  weight: {entry.weight:.4f}  used_count: {entry.used_count}  by: {used_by}")


@insight.command("decay")
@click.option("--dry-run", is_flag=True, default=False, help="仅预览，不实际执行")
def decay_insights(dry_run):
    """对所有活跃沉淀执行权重衰减"""
    mgr = _load_insight_manager()

    if dry_run:
        entries, settings = mgr.get_registry()
        rate = settings["decay_rate"]
        threshold = settings["deactivate_threshold"]
        click.echo(f"衰减预览 (rate={rate}, threshold={threshold}):\n")
        for ins_id, entry in entries.items():
            if not entry.active:
                continue
            new_weight = entry.weight * rate
            will_deactivate = new_weight < threshold
            mark = " → DEACTIVATE" if will_deactivate else ""
            click.echo(f"  {ins_id}: {entry.weight:.4f} → {new_weight:.4f}{mark}")
        return

    deactivated = mgr.apply_decay()
    click.echo("权重衰减已执行。")
    if deactivated:
        click.echo(f"已停用 {len(deactivated)} 条沉淀: {', '.join(deactivated)}")
    else:
        click.echo("无沉淀被停用。")


@insight.command("check")
@click.option("--json", "as_json", is_flag=True, default=False, help="JSON 格式输出")
def check_insights(as_json):
    """沉淀系统一致性校验"""
    import json as json_mod

    mgr = _load_insight_manager()
    report = mgr.check_consistency()

    if as_json:
        click.echo(json_mod.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        if not report.ok:
            sys.exit(1)
        return

    if report.ok and not report.warnings:
        click.echo("一致性校验通过，无错误无警告。")
        return

    if report.errors:
        click.echo(f"发现 {len(report.errors)} 个错误：")
        for err in report.errors:
            click.echo(f"  [ERROR] {err}")

    if report.warnings:
        click.echo(f"发现 {len(report.warnings)} 个警告：")
        for warn in report.warnings:
            click.echo(f"  [WARN]  {warn}")

    if report.ok:
        click.echo("\n校验结果: 通过（有警告）")
    else:
        click.echo(f"\n校验结果: 失败（{len(report.errors)} 个错误）")
        sys.exit(1)


@insight.command("delete")
@click.argument("insight_id")
@click.option("--yes", "-y", is_flag=True, default=False, help="跳过确认")
def delete_insight(insight_id, yes):
    """删除沉淀条目"""
    mgr = _load_insight_manager()
    dm = _load_developer_manager()

    ins = mgr.get(insight_id)
    if not ins:
        click.echo(f"未找到沉淀: {insight_id}", err=True)
        sys.exit(1)

    if not yes:
        click.confirm(f"确认删除 {insight_id} ({ins.title})?", abort=True)

    deleted_by = dm.get_current_developer()
    mgr.delete(insight_id, deleted_by=deleted_by)

    # 移除 developer contributed 记录
    dm.remove_contributed(insight_id, deleted_by)

    click.echo(f"已删除: {insight_id}")
