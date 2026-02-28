"""
Insight CLI 命令组 — 沉淀系统的 CLI 接口

提供沉淀的 CRUD、搜索、使用、衰减、一致性校验、跨开发者共享、溯源可视化等功能。

命令:
    vibecollab insight list               列出所有沉淀
    vibecollab insight show <id>          查看沉淀详情
    vibecollab insight add                交互式创建沉淀
    vibecollab insight search --tags ...  按标签搜索
    vibecollab insight use <id>           记录一次使用
    vibecollab insight decay              执行权重衰减
    vibecollab insight check              一致性校验
    vibecollab insight delete <id>        删除沉淀
    vibecollab insight bookmark <id>      收藏沉淀
    vibecollab insight unbookmark <id>    取消收藏
    vibecollab insight trace <id>         溯源树可视化
    vibecollab insight who <id>           查看跨开发者使用信息
    vibecollab insight stats              跨开发者共享统计
"""

from pathlib import Path

import click
import yaml

from ._compat import EMOJI


def _load_insight_manager(config_path: str = "project.yaml"):
    """加载 InsightManager 实例"""
    from .event_log import EventLog
    from .insight_manager import InsightManager

    project_root = Path.cwd()
    vibecollab_dir = project_root / ".vibecollab"
    if not vibecollab_dir.exists():
        click.echo("错误: 未找到 .vibecollab/ 目录。请先运行 vibecollab init", err=True)
        raise SystemExit(1)
    event_log = EventLog(vibecollab_dir / "events.jsonl")
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
        raise SystemExit(1)

    entries, _ = mgr.get_registry()
    entry = entries.get(insight_id)

    click.echo(f"ID:       {ins.id}")
    click.echo(f"Title:    {ins.title}")
    click.echo(f"Category: {ins.category}")
    click.echo(f"Tags:     {', '.join(ins.tags)}")
    if ins.summary:
        click.echo(f"Summary:  {ins.summary}")
    click.echo(f"Origin:   created by {ins.origin.created_by} on {ins.origin.created_at}")
    if ins.origin.context:
        click.echo(f"Context:  {ins.origin.context}")
    if ins.origin.source_type:
        source_info = f"Source:   [{ins.origin.source_type}]"
        if ins.origin.source_desc:
            source_info += f" {ins.origin.source_desc}"
        if ins.origin.source_project:
            source_info += f" (project: {ins.origin.source_project})"
        if ins.origin.source_ref:
            source_info += f" [ref: {ins.origin.source_ref}]"
        click.echo(source_info)
        if ins.origin.source_url:
            click.echo(f"URL:      {ins.origin.source_url}")
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
@click.option("--context", "origin_context", default="", help="创建背景（自然语言描述）")
@click.option("--source-type", default=None, type=click.Choice(["task", "decision", "insight", "external"]))
@click.option("--source-desc", default=None, help="来源描述（自然语言，跨项目可读）")
@click.option("--source-ref", default=None, help="来源内部 ID（可选 hint，如 DECISION-012）")
@click.option("--source-url", default=None, help="来源外部链接（如 GitHub issue URL）")
@click.option("--source-project", default=None, help="来源项目名")
@click.option("--derived-from", default=None, help="派生自的 insight ID，逗号分隔")
@click.option("--force", "-f", is_flag=True, default=False, help="跳过去重检测，强制创建")
def add_insight(title, tags, category, scenario, approach, summary,
                validation, origin_context, source_type, source_desc,
                source_ref, source_url, source_project, derived_from, force):
    """创建新的沉淀条目"""
    mgr = _load_insight_manager()
    dm = _load_developer_manager()

    created_by = dm.get_current_developer()
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    derived_list = [d.strip() for d in derived_from.split(",") if d.strip()] if derived_from else []

    body = {"scenario": scenario, "approach": approach}
    if validation:
        body["validation"] = validation

    # 去重检测 (v0.9.4)
    if not force:
        duplicates = mgr.find_duplicates(title, tag_list, body)
        if duplicates:
            click.echo(f"\n{EMOJI['warn']} Potential duplicates detected:")
            for dup in duplicates:
                click.echo(f"  - {dup['id']}: {dup['title']} (score={dup['score']}, {dup['reason']})")
            click.echo("\nUse --force to create anyway, or adjust title/tags.")
            raise SystemExit(1)

    ins = mgr.create(
        title=title,
        tags=tag_list,
        category=category,
        body=body,
        created_by=created_by,
        summary=summary,
        context=origin_context,
        source_type=source_type,
        source_desc=source_desc,
        source_ref=source_ref,
        source_url=source_url,
        source_project=source_project,
        derived_from=derived_list,
    )

    # 记录到 developer contributed
    dm.add_contributed(ins.id, created_by)

    # 更新信号快照
    try:
        from .insight_signal import InsightSignalCollector
        collector = InsightSignalCollector(Path.cwd())
        collector.update_snapshot(insight_id=ins.id)
    except Exception:
        pass

    click.echo(f"已创建沉淀: {ins.id} — {ins.title}")
    click.echo(f"  tags: {', '.join(ins.tags)}")
    click.echo(f"  category: {ins.category}")
    click.echo(f"  created_by: {created_by}")


@insight.command("search")
@click.option("--tags", default=None, help="按标签搜索，逗号分隔")
@click.option("--category", default=None, help="按分类搜索")
@click.option("--semantic", "-q", default=None, help="语义搜索 (需先 vibecollab index)")
@click.option("--include-inactive", is_flag=True, default=False, help="包含非活跃沉淀")
@click.option("--top", "-k", default=10, help="语义搜索返回数量")
def search_insights(tags, category, semantic, include_inactive, top):
    """搜索沉淀

    支持标签搜索、分类搜索、语义搜索三种模式。

    Examples:

        vibecollab insight search --tags "python,encoding"

        vibecollab insight search --category debug

        vibecollab insight search --semantic "Windows 编码兼容"
    """
    # 语义搜索模式
    if semantic:
        _semantic_search_insights(semantic, top)
        return

    mgr = _load_insight_manager()

    if not tags and not category:
        click.echo("请指定 --tags、--category 或 --semantic", err=True)
        raise SystemExit(1)

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


def _semantic_search_insights(query: str, top_k: int):
    """语义搜索 Insight（调用向量索引）"""
    from pathlib import Path

    project_root = Path.cwd()
    db_path = project_root / ".vibecollab" / "vectors" / "index.db"
    if not db_path.exists():
        click.echo("语义索引不存在 — 请先运行 `vibecollab index`", err=True)
        raise SystemExit(1)

    import sqlite3
    conn = sqlite3.connect(str(db_path))
    row = conn.execute("SELECT dimensions FROM vectors LIMIT 1").fetchone()
    conn.close()
    if not row:
        click.echo("索引为空 — 请先运行 `vibecollab index`", err=True)
        raise SystemExit(1)

    from .embedder import Embedder, EmbedderConfig
    from .vector_store import VectorStore

    dims = row[0]
    embedder = Embedder(EmbedderConfig(backend="pure_python", dimensions=dims))
    store = VectorStore(db_path=db_path, dimensions=dims)

    query_vector = embedder.embed_text(query)
    results = store.search(query_vector, top_k=top_k, source_type="insight")

    if not results:
        click.echo(f"未找到与 \"{query}\" 相关的 Insight。")
        store.close()
        return

    click.echo(f"语义搜索: \"{query}\" (Top {len(results)})\n")
    for i, r in enumerate(results, 1):
        title = r.metadata.get("title", "")
        tags = r.metadata.get("tags", [])
        category = r.metadata.get("category", "")
        tags_str = f"  tags: {', '.join(tags)}" if tags else ""
        cat_str = f"  [{category}]" if category else ""
        click.echo(f"  {i}. {r.doc_id}{cat_str}  {title}  (score: {r.score:.3f})")
        if tags_str:
            click.echo(f"     {tags_str}")

    store.close()


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
        raise SystemExit(1)

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
            raise SystemExit(1)
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
        raise SystemExit(1)


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
        raise SystemExit(1)

    if not yes:
        click.confirm(f"确认删除 {insight_id} ({ins.title})?", abort=True)

    deleted_by = dm.get_current_developer()
    mgr.delete(insight_id, deleted_by=deleted_by)

    # 移除 developer contributed 记录
    dm.remove_contributed(insight_id, deleted_by)

    click.echo(f"已删除: {insight_id}")


@insight.command("bookmark")
@click.argument("insight_id")
def bookmark_insight(insight_id):
    """收藏沉淀"""
    mgr = _load_insight_manager()
    dm = _load_developer_manager()

    ins = mgr.get(insight_id)
    if not ins:
        click.echo(f"未找到沉淀: {insight_id}", err=True)
        raise SystemExit(1)

    developer = dm.get_current_developer()
    added = dm.add_bookmark(insight_id, developer)
    if added:
        click.echo(f"已收藏: {insight_id} ({ins.title})")
        click.echo(f"  by: {developer}")
    else:
        click.echo(f"已存在收藏: {insight_id}")


@insight.command("unbookmark")
@click.argument("insight_id")
def unbookmark_insight(insight_id):
    """取消收藏沉淀"""
    dm = _load_developer_manager()

    developer = dm.get_current_developer()
    removed = dm.remove_bookmark(insight_id, developer)
    if removed:
        click.echo(f"已取消收藏: {insight_id}")
    else:
        click.echo(f"未找到收藏: {insight_id}")


@insight.command("trace")
@click.argument("insight_id")
@click.option("--json", "as_json", is_flag=True, default=False, help="JSON 格式输出")
def trace_insight(insight_id, as_json):
    """溯源树可视化 — 显示沉淀的派生关系"""
    import json as json_mod

    mgr = _load_insight_manager()
    ins = mgr.get(insight_id)
    if not ins:
        click.echo(f"未找到沉淀: {insight_id}", err=True)
        raise SystemExit(1)

    trace = mgr.get_full_trace(insight_id)

    if as_json:
        click.echo(json_mod.dumps(trace, ensure_ascii=False, indent=2))
        return

    # ASCII 树形可视化
    click.echo(f"\n溯源树: {insight_id} — {ins.title}\n")

    # 上游
    if trace["upstream"]:
        click.echo("  上游 (derived from):")
        _render_tree(trace["upstream"], prefix="    ", direction="up")
    else:
        click.echo("  上游: (无)")

    click.echo(f"\n  {EMOJI['circle']} {insight_id} — {ins.title}")

    # 下游
    if trace["downstream"]:
        click.echo("\n  下游 (derived by):")
        _render_tree(trace["downstream"], prefix="    ", direction="down")
    else:
        click.echo("\n  下游: (无)")

    click.echo()


def _render_tree(nodes, prefix="", direction="down"):
    """递归渲染 ASCII 树"""
    child_key = "downstream" if direction == "down" else "upstream"
    for i, node in enumerate(nodes):
        is_last = i == len(nodes) - 1
        connector = "└── " if is_last else "├── "
        click.echo(f"{prefix}{connector}{node['id']} — {node['title']}")
        if node.get(child_key):
            extension = "    " if is_last else "│   "
            _render_tree(node[child_key], prefix=prefix + extension, direction=direction)


@insight.command("who")
@click.argument("insight_id")
@click.option("--json", "as_json", is_flag=True, default=False, help="JSON 格式输出")
def who_insight(insight_id, as_json):
    """查看谁创建/使用/收藏了某条沉淀"""
    import json as json_mod

    mgr = _load_insight_manager()
    ins = mgr.get(insight_id)
    if not ins:
        click.echo(f"未找到沉淀: {insight_id}", err=True)
        raise SystemExit(1)

    info = mgr.get_insight_developers(insight_id)

    if as_json:
        click.echo(json_mod.dumps(info, ensure_ascii=False, indent=2))
        return

    click.echo(f"\n{insight_id} — {ins.title}\n")
    click.echo(f"  创建者:  {info['created_by'] or '(unknown)'}")
    click.echo(f"  使用者:  {', '.join(info['used_by']) or '(无)'}")
    click.echo(f"  收藏者:  {', '.join(info['bookmarked_by']) or '(无)'}")
    click.echo(f"  贡献者:  {', '.join(info['contributed_by']) or '(无)'}")
    click.echo()


@insight.command("stats")
@click.option("--json", "as_json", is_flag=True, default=False, help="JSON 格式输出")
def stats_insights(as_json):
    """跨开发者共享统计"""
    import json as json_mod

    mgr = _load_insight_manager()
    stats = mgr.get_cross_developer_stats()

    if as_json:
        click.echo(json_mod.dumps(stats, ensure_ascii=False, indent=2))
        return

    summary = stats["summary"]
    click.echo("\n=== Insight 共享统计 ===\n")
    click.echo(f"  沉淀总数:    {summary['total_insights']}")
    click.echo(f"  开发者总数:  {summary['total_developers']}")
    click.echo(f"  总使用次数:  {summary['total_uses']}")
    if summary["most_used"]:
        click.echo(f"  最常使用:    {summary['most_used']}")
    if summary["most_shared"]:
        click.echo(f"  最多共享:    {summary['most_shared']}")

    if stats["developers"]:
        click.echo("\n--- 开发者 ---")
        for dev, data in stats["developers"].items():
            contributed = len(data["contributed"])
            bookmarks = len(data["bookmarks"])
            used = len(data["used"])
            click.echo(f"  {dev}: 贡献 {contributed}, 收藏 {bookmarks}, 使用 {used}")

    if stats["insights"]:
        click.echo("\n--- 沉淀 ---")
        for ins_id, data in stats["insights"].items():
            click.echo(
                f"  {ins_id}: "
                f"贡献者 {data['contributors']}, "
                f"使用者 {data['users']}, "
                f"收藏 {data['bookmarks']}"
            )

    click.echo()


@insight.command("suggest")
@click.option("--json", "as_json", is_flag=True, help="JSON 输出")
@click.option("--auto-confirm", is_flag=True,
              help="自动确认所有候选 (非交互模式)")
def suggest_insights(as_json, auto_confirm):
    """基于结构化信号推荐候选 Insight

    从 git 增量历史、文档变更 diff、Task 变化等信号中提取候选 Insight。
    用户确认后自动创建 Insight 并更新信号快照。
    """
    from .insight_signal import InsightSignalCollector

    project_root = Path.cwd()
    collector = InsightSignalCollector(project_root)

    # 收集候选
    candidates = collector.suggest()

    if as_json:
        import json as json_mod
        output = {
            "candidates": [c.to_dict() for c in candidates],
            "count": len(candidates),
            "snapshot": collector.load_snapshot().to_dict(),
        }
        click.echo(json_mod.dumps(output, indent=2, ensure_ascii=False))
        return

    if not candidates:
        click.echo(f"{EMOJI['ok']} 未发现需要沉淀的候选 Insight")
        click.echo("  提示: 进行更多开发活动后再试")
        return

    click.echo(f"\n=== Insight 候选推荐 ({len(candidates)} 条) ===\n")

    snapshot = collector.load_snapshot()
    if snapshot.last_commit:
        click.echo(f"  上次快照: {snapshot.last_commit[:8]}... "
                    f"({snapshot.last_timestamp[:10]})")
    else:
        click.echo("  首次推荐（无历史快照）")
    click.echo()

    # 展示候选
    for i, c in enumerate(candidates, 1):
        conf_bar = "#" * int(c.confidence * 10)
        click.echo(f"  [{i}] {c.title}")
        click.echo(f"      tags: {', '.join(c.tags)}")
        click.echo(f"      category: {c.category}")
        click.echo(f"      reason: {c.reason}")
        click.echo(f"      signal: {c.source_signal}")
        click.echo(f"      confidence: {conf_bar} {c.confidence:.1f}")
        click.echo()

    if auto_confirm:
        # 非交互模式：全部创建
        _create_from_candidates(project_root, candidates, collector)
        return

    # 交互模式：让用户选择
    click.echo("输入要创建的候选编号 (逗号分隔，如 1,3)，"
               "或 'all' 全部创建，'q' 退出:")
    try:
        choice = input("> ").strip()
    except (EOFError, KeyboardInterrupt):
        click.echo("\n已取消")
        return

    if choice.lower() == "q":
        click.echo("已取消")
        return

    if choice.lower() == "all":
        selected = candidates
    else:
        indices = []
        for part in choice.split(","):
            part = part.strip()
            if part.isdigit():
                idx = int(part) - 1
                if 0 <= idx < len(candidates):
                    indices.append(idx)
        selected = [candidates[i] for i in indices]

    if not selected:
        click.echo("未选择任何候选")
        return

    _create_from_candidates(project_root, selected, collector)


def _create_from_candidates(project_root, candidates, collector):
    """从候选列表创建 Insight"""
    mgr = _load_insight_manager()
    dm = None
    try:
        dm = _load_developer_manager()
    except Exception:
        pass

    created_by = "unknown"
    if dm:
        try:
            created_by = dm.get_current_developer()
        except Exception:
            pass

    created_ids = []
    for c in candidates:
        body = {
            "scenario": c.reason,
            "approach": c.title,
            "validation": f"signal: {c.source_signal}",
        }
        ins = mgr.create(
            title=c.title,
            tags=c.tags,
            category=c.category,
            body=body,
            created_by=created_by,
            summary=c.reason,
            context=f"auto-suggest via {c.source_signal}",
            source_type="signal",
            source_desc=c.source_signal,
        )
        click.echo(f"  {EMOJI['ok']} created {ins.id}: {c.title}")
        created_ids.append(ins.id)

        if dm:
            try:
                dm.add_contributed(ins.id, created_by)
            except Exception:
                pass

    # 更新快照
    last_id = created_ids[-1] if created_ids else ""
    collector.update_snapshot(insight_id=last_id)
    click.echo(f"\nCreated {len(created_ids)} Insight(s), signal snapshot updated")


# ------------------------------------------------------------------
# Graph 命令 (v0.9.4)
# ------------------------------------------------------------------

@insight.command("graph")
@click.option("--format", "fmt", type=click.Choice(["mermaid", "json", "text"]),
              default="text", help="Output format")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output (alias for --format json)")
def insight_graph(fmt, json_output):
    """Insight 关联图谱可视化

    展示所有 Insight 之间的派生/关联关系。

    Examples:

        vibecollab insight graph

        vibecollab insight graph --format mermaid

        vibecollab insight graph --json
    """
    import json as json_mod

    mgr = _load_insight_manager()
    graph = mgr.build_graph()

    if json_output or fmt == "json":
        click.echo(json_mod.dumps(graph, ensure_ascii=False, indent=2))
        return

    if fmt == "mermaid":
        click.echo(mgr.to_mermaid(graph))
        return

    # text format: 人类可读的图谱摘要
    stats = graph["stats"]
    click.echo(f"Insight Graph: {stats['node_count']} nodes, {stats['edge_count']} edges")
    click.echo(f"  Components: {stats['components']}, Isolated: {stats['isolated_count']}")
    click.echo()

    if graph["edges"]:
        click.echo("Relations:")
        for edge in graph["edges"]:
            from_node = next((n for n in graph["nodes"] if n["id"] == edge["from"]), None)
            to_node = next((n for n in graph["nodes"] if n["id"] == edge["to"]), None)
            from_title = from_node["title"] if from_node else "(missing)"
            to_title = to_node["title"] if to_node else "(missing)"
            click.echo(f"  {edge['from']} ({from_title})")
            click.echo(f"    --> {edge['to']} ({to_title})")
    else:
        click.echo("No relations found (all Insights are isolated).")

    click.echo()
    click.echo("Nodes:")
    for node in graph["nodes"]:
        status = "" if node["active"] else " [inactive]"
        click.echo(f"  {node['id']}: {node['title']} [{node['category']}]{status}")


# ------------------------------------------------------------------
# Export / Import 命令 (v0.9.4)
# ------------------------------------------------------------------

@insight.command("export")
@click.option("--ids", default=None, help="要导出的 Insight ID，逗号分隔 (默认全部)")
@click.option("--output", "-o", default=None, help="输出文件路径 (默认 stdout)")
@click.option("--include-registry", is_flag=True, default=False, help="包含注册表状态")
def export_insights(ids, output, include_registry):
    """导出 Insight 为可移植的 YAML 格式

    Examples:

        vibecollab insight export -o insights_bundle.yaml

        vibecollab insight export --ids INS-001,INS-002

        vibecollab insight export --include-registry -o full_export.yaml
    """
    mgr = _load_insight_manager()

    id_list = [i.strip() for i in ids.split(",") if i.strip()] if ids else None
    bundle = mgr.export_insights(insight_ids=id_list, include_registry=include_registry)

    yaml_content = yaml.dump(bundle, allow_unicode=True, sort_keys=False,
                             default_flow_style=False)

    if output:
        Path(output).write_text(yaml_content, encoding="utf-8")
        click.echo(f"{EMOJI['ok']} Exported {bundle['count']} Insight(s) to {output}")
    else:
        click.echo(yaml_content)


@insight.command("import")
@click.argument("filepath")
@click.option("--strategy", type=click.Choice(["skip", "rename", "overwrite"]),
              default="skip", help="ID conflict strategy: skip/rename/overwrite")
@click.option("--json", "json_output", is_flag=True, default=False, help="JSON output")
def import_insights(filepath, strategy, json_output):
    """从 YAML 文件导入 Insight

    Examples:

        vibecollab insight import insights_bundle.yaml

        vibecollab insight import bundle.yaml --strategy rename

        vibecollab insight import bundle.yaml --strategy overwrite
    """
    import json as json_mod

    path = Path(filepath)
    if not path.exists():
        click.echo(f"{EMOJI['fail']} File not found: {filepath}")
        raise SystemExit(1)

    try:
        with open(path, "r", encoding="utf-8") as f:
            bundle = yaml.safe_load(f)
    except Exception as e:
        click.echo(f"{EMOJI['fail']} Failed to parse YAML: {e}")
        raise SystemExit(1)

    if not isinstance(bundle, dict) or bundle.get("format") != "vibecollab-insight-export":
        click.echo(f"{EMOJI['fail']} Invalid bundle format. Expected 'vibecollab-insight-export'.")
        raise SystemExit(1)

    mgr = _load_insight_manager()
    dm = _load_developer_manager()
    imported_by = dm.get_current_developer()

    results = mgr.import_insights(bundle, imported_by=imported_by, strategy=strategy)

    if json_output:
        click.echo(json_mod.dumps(results, ensure_ascii=False, indent=2))
        return

    # 更新 developer contributed
    for ins_id in results["imported"]:
        try:
            dm.add_contributed(ins_id, imported_by)
        except Exception:
            pass

    click.echo(f"\nImport results (strategy={strategy}):")
    click.echo(f"  {EMOJI['ok']} Imported:  {len(results['imported'])}")
    if results["skipped"]:
        click.echo(f"  {EMOJI['warn']} Skipped:   {len(results['skipped'])} ({', '.join(results['skipped'])})")
    if results["renamed"]:
        click.echo(f"  {EMOJI['info']} Renamed:   {len(results['renamed'])}")
        for old_id, new_id in results["renamed"].items():
            click.echo(f"    {old_id} -> {new_id}")
    if results["errors"]:
        click.echo(f"  {EMOJI['fail']} Errors:    {len(results['errors'])}")
        for err in results["errors"]:
            click.echo(f"    {err}")
