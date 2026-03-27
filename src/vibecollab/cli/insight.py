"""
Insight CLI command group -- CLI interface for the distillation system

Provides CRUD, search, usage, decay, consistency check, cross-role sharing, traceability visualization, etc.

Commands:
    vibecollab insight list               List all insights
    vibecollab insight show <id>          View insight details
    vibecollab insight add                Interactively create an insight
    vibecollab insight search --tags ...  Search by tags
    vibecollab insight use <id>           Record a usage
    vibecollab insight decay              Execute weight decay
    vibecollab insight check              Consistency check
    vibecollab insight delete <id>        Delete an insight
    vibecollab insight bookmark <id>      Bookmark an insight
    vibecollab insight unbookmark <id>    Remove bookmark
    vibecollab insight trace <id>         Traceability tree visualization
    vibecollab insight who <id>           View cross-role usage info
    vibecollab insight stats              Cross-role sharing statistics
"""

from pathlib import Path

import click
import yaml

from .._compat import EMOJI
from ..i18n import _


def _load_insight_manager(config_path: str = "project.yaml"):
    """Load InsightManager instance"""
    from ..domain.event_log import EventLog
    from ..insight.manager import InsightManager

    project_root = Path.cwd()
    vibecollab_dir = project_root / ".vibecollab"
    if not vibecollab_dir.exists():
        click.echo("Error: .vibecollab/ directory not found. Please run vibecollab init first", err=True)
        raise SystemExit(1)
    event_log = EventLog(vibecollab_dir / "events.jsonl")
    return InsightManager(project_root=project_root, event_log=event_log)


def _load_role_manager(config_path: str = "project.yaml"):
    """Load RoleManager instance"""
    from ..domain.role import RoleManager

    project_root = Path.cwd()
    config_file = project_root / config_path
    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
    else:
        config = {}
    return RoleManager(project_root, config)


@click.group()
def insight():
    """Insight system management commands

    Manage reusable knowledge units distilled from development practices.
    """
    pass


@insight.command("list")
@click.option("--active-only", is_flag=True, default=False, help=_("Show active insights only"))
@click.option("--json", "as_json", is_flag=True, default=False, help=_("JSON output"))
def list_insights(active_only, as_json):
    """List all insights"""
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
        click.echo("No insight entries yet. Use `vibecollab insight add` to create one.")
        return

    click.echo(f"Total {len(all_insights)} insights:\n")
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
    """View insight details"""
    mgr = _load_insight_manager()
    ins = mgr.get(insight_id)
    if not ins:
        click.echo(f"Insight not found: {insight_id}", err=True)
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
@click.option("--title", "-t", required=True, help=_("Insight title"))
@click.option("--tags", required=True, help=_("Tag list, comma separated"))
@click.option("--category", "-c", required=True,
              type=click.Choice(["technique", "workflow", "decision", "debug", "tool", "integration"]),
              help=_("Category"))
@click.option("--scenario", "-s", required=True, help=_("Applicable scenario"))
@click.option("--approach", "-a", required=True, help=_("Method/steps"))
@click.option("--summary", default="", help=_("One-line summary"))
@click.option("--validation", default="", help=_("Validation method"))
@click.option("--context", "origin_context", default="", help=_("Creation context (natural language)"))
@click.option("--source-type", default=None, type=click.Choice(["task", "decision", "insight", "external"]))
@click.option("--source-desc", default=None, help=_("Source description (natural language, cross-project readable)"))
@click.option("--source-ref", default=None, help=_("Source internal ID (optional hint, e.g. DECISION-012)"))
@click.option("--source-url", default=None, help=_("Source external link (e.g. GitHub issue URL)"))
@click.option("--source-project", default=None, help=_("Source project name"))
@click.option("--derived-from", default=None, help=_("Derived from insight IDs, comma separated"))
@click.option("--force", "-f", is_flag=True, default=False, help=_("Skip dedup check, force create"))
def add_insight(title, tags, category, scenario, approach, summary,
                validation, origin_context, source_type, source_desc,
                source_ref, source_url, source_project, derived_from, force):
    """Create a new insight entry"""
    mgr = _load_insight_manager()
    dm = _load_role_manager()

    created_by = dm.get_current_role()
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    derived_list = [d.strip() for d in derived_from.split(",") if d.strip()] if derived_from else []

    body = {"scenario": scenario, "approach": approach}
    if validation:
        body["validation"] = validation

    # Dedup check (v0.9.4)
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

    # Record to role contributed
    dm.add_contributed(ins.id, created_by)

    # Update signal snapshot
    try:
        from ..insight.signal import InsightSignalCollector
        collector = InsightSignalCollector(Path.cwd())
        collector.update_snapshot(insight_id=ins.id)
    except Exception:
        pass

    click.echo(f"Created insight: {ins.id} -- {ins.title}")
    click.echo(f"  tags: {', '.join(ins.tags)}")
    click.echo(f"  category: {ins.category}")
    click.echo(f"  created_by: {created_by}")


@insight.command("search")
@click.option("--tags", default=None, help=_("Search by tags, comma separated"))
@click.option("--category", default=None, help=_("Search by category"))
@click.option("--semantic", "-q", default=None, help=_("Semantic search (requires vibecollab index first)"))
@click.option("--include-inactive", is_flag=True, default=False, help=_("Include inactive insights"))
@click.option("--top", "-k", default=10, help=_("Number of semantic search results"))
def search_insights(tags, category, semantic, include_inactive, top):
    """Search insights

    Supports tag search, category search, and semantic search modes.

    Examples:

        vibecollab insight search --tags "python,encoding"

        vibecollab insight search --category debug

        vibecollab insight search --semantic "Windows encoding compatibility"
    """
    # Semantic search mode
    if semantic:
        _semantic_search_insights(semantic, top)
        return

    mgr = _load_insight_manager()

    if not tags and not category:
        click.echo("Please specify --tags, --category, or --semantic", err=True)
        raise SystemExit(1)

    results = []
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        results = mgr.search_by_tags(tag_list, active_only=not include_inactive)
    elif category:
        results = mgr.search_by_category(category)

    if not results:
        click.echo("No matching insights found.")
        return

    click.echo(f"Found {len(results)} matches:\n")
    entries, _ = mgr.get_registry()
    for ins in results:
        entry = entries.get(ins.id)
        weight = f"{entry.weight:.2f}" if entry else "1.00"
        click.echo(f"  {ins.id}  [{ins.category}]  {ins.title}  (weight: {weight})")
        click.echo(f"          tags: {', '.join(ins.tags)}")


def _semantic_search_insights(query: str, top_k: int):
    """Semantic search for Insights (uses vector index)"""
    from pathlib import Path

    project_root = Path.cwd()
    db_path = project_root / ".vibecollab" / "vectors" / "index.db"
    if not db_path.exists():
        click.echo("Semantic index does not exist -- please run `vibecollab index` first", err=True)
        raise SystemExit(1)

    import sqlite3
    conn = sqlite3.connect(str(db_path))
    row = conn.execute("SELECT dimensions FROM vectors LIMIT 1").fetchone()
    conn.close()
    if not row:
        click.echo("Index is empty -- please run `vibecollab index` first", err=True)
        raise SystemExit(1)

    from ..insight.embedder import Embedder, EmbedderConfig
    from ..search.vector_store import VectorStore

    dims = row[0]
    embedder = Embedder(EmbedderConfig(backend="pure_python", dimensions=dims))
    store = VectorStore(db_path=db_path, dimensions=dims)

    query_vector = embedder.embed_text(query)
    results = store.search(query_vector, top_k=top_k, source_type="insight")

    if not results:
        click.echo(f"No Insights related to \"{query}\" found.")
        store.close()
        return

    click.echo(f"Semantic search: \"{query}\" (Top {len(results)})\n")
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
    """Record an insight usage, reward weight"""
    mgr = _load_insight_manager()
    dm = _load_role_manager()
    used_by = dm.get_current_role()

    entry = mgr.record_use(insight_id, used_by=used_by)
    if not entry:
        click.echo(f"Registry entry not found: {insight_id}", err=True)
        raise SystemExit(1)

    click.echo(f"Usage recorded: {insight_id}")
    click.echo(f"  weight: {entry.weight:.4f}  used_count: {entry.used_count}  by: {used_by}")


@insight.command("decay")
@click.option("--dry-run", is_flag=True, default=False, help=_("Preview only, do not execute"))
def decay_insights(dry_run):
    """Execute weight decay on all active insights"""
    mgr = _load_insight_manager()

    if dry_run:
        entries, settings = mgr.get_registry()
        rate = settings["decay_rate"]
        threshold = settings["deactivate_threshold"]
        click.echo(f"Decay preview (rate={rate}, threshold={threshold}):\n")
        for ins_id, entry in entries.items():
            if not entry.active:
                continue
            new_weight = entry.weight * rate
            will_deactivate = new_weight < threshold
            mark = " → DEACTIVATE" if will_deactivate else ""
            click.echo(f"  {ins_id}: {entry.weight:.4f} → {new_weight:.4f}{mark}")
        return

    deactivated = mgr.apply_decay()
    click.echo("Weight decay executed.")
    if deactivated:
        click.echo(f"Deactivated {len(deactivated)} insights: {', '.join(deactivated)}")
    else:
        click.echo("No insights deactivated.")


@insight.command("check")
@click.option("--json", "as_json", is_flag=True, default=False, help=_("JSON output"))
def check_insights(as_json):
    """Insight system consistency check"""
    import json as json_mod

    mgr = _load_insight_manager()
    report = mgr.check_consistency()

    if as_json:
        click.echo(json_mod.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        if not report.ok:
            raise SystemExit(1)
        return

    if report.ok and not report.warnings:
        click.echo("Consistency check passed, no errors or warnings.")
        return

    if report.errors:
        click.echo(f"Found {len(report.errors)} error(s):")
        for err in report.errors:
            click.echo(f"  [ERROR] {err}")

    if report.warnings:
        click.echo(f"Found {len(report.warnings)} warning(s):")
        for warn in report.warnings:
            click.echo(f"  [WARN]  {warn}")

    if report.ok:
        click.echo("\nCheck result: Passed (with warnings)")
    else:
        click.echo(f"\nCheck result: Failed ({len(report.errors)} error(s))")
        raise SystemExit(1)


@insight.command("delete")
@click.argument("insight_id")
@click.option("--yes", "-y", is_flag=True, default=False, help=_("Skip confirmation"))
def delete_insight(insight_id, yes):
    """Delete an insight entry"""
    mgr = _load_insight_manager()
    dm = _load_role_manager()

    ins = mgr.get(insight_id)
    if not ins:
        click.echo(f"Insight not found: {insight_id}", err=True)
        raise SystemExit(1)

    if not yes:
        click.confirm(f"Confirm delete {insight_id} ({ins.title})?", abort=True)

    deleted_by = dm.get_current_role()
    mgr.delete(insight_id, deleted_by=deleted_by)

    # Remove role contributed record
    dm.remove_contributed(insight_id, deleted_by)

    click.echo(f"Deleted: {insight_id}")


@insight.command("bookmark")
@click.argument("insight_id")
def bookmark_insight(insight_id):
    """Bookmark an insight"""
    mgr = _load_insight_manager()
    dm = _load_role_manager()

    ins = mgr.get(insight_id)
    if not ins:
        click.echo(f"Insight not found: {insight_id}", err=True)
        raise SystemExit(1)

    role = dm.get_current_role()
    added = dm.add_bookmark(insight_id, role)
    if added:
        click.echo(f"Bookmarked: {insight_id} ({ins.title})")
        click.echo(f"  by: {role}")
    else:
        click.echo(f"Already bookmarked: {insight_id}")


@insight.command("unbookmark")
@click.argument("insight_id")
def unbookmark_insight(insight_id):
    """Remove bookmark from an insight"""
    dm = _load_role_manager()

    role = dm.get_current_role()
    removed = dm.remove_bookmark(insight_id, role)
    if removed:
        click.echo(f"Bookmark removed: {insight_id}")
    else:
        click.echo(f"Bookmark not found: {insight_id}")


@insight.command("trace")
@click.argument("insight_id")
@click.option("--json", "as_json", is_flag=True, default=False, help=_("JSON output"))
def trace_insight(insight_id, as_json):
    """Traceability tree visualization -- show insight derivation relationships"""
    import json as json_mod

    mgr = _load_insight_manager()
    ins = mgr.get(insight_id)
    if not ins:
        click.echo(f"Insight not found: {insight_id}", err=True)
        raise SystemExit(1)

    trace = mgr.get_full_trace(insight_id)

    if as_json:
        click.echo(json_mod.dumps(trace, ensure_ascii=False, indent=2))
        return

    # ASCII tree visualization
    click.echo(f"\nTraceability Tree: {insight_id} -- {ins.title}\n")

    # Upstream
    if trace["upstream"]:
        click.echo("  Upstream (derived from):")
        _render_tree(trace["upstream"], prefix="    ", direction="up")
    else:
        click.echo("  Upstream: (none)")

    click.echo(f"\n  {EMOJI['circle']} {insight_id} -- {ins.title}")

    # Downstream
    if trace["downstream"]:
        click.echo("\n  Downstream (derived by):")
        _render_tree(trace["downstream"], prefix="    ", direction="down")
    else:
        click.echo("\n  Downstream: (none)")

    click.echo()


def _render_tree(nodes, prefix="", direction="down"):
    """Recursively render ASCII tree"""
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
@click.option("--json", "as_json", is_flag=True, default=False, help=_("JSON output"))
def who_insight(insight_id, as_json):
    """View who created/used/bookmarked an insight"""
    import json as json_mod

    mgr = _load_insight_manager()
    ins = mgr.get(insight_id)
    if not ins:
        click.echo(f"Insight not found: {insight_id}", err=True)
        raise SystemExit(1)

    info = mgr.get_insight_roles(insight_id)

    if as_json:
        click.echo(json_mod.dumps(info, ensure_ascii=False, indent=2))
        return

    click.echo(f"\n{insight_id} -- {ins.title}\n")
    click.echo(f"  Creator:      {info['created_by'] or '(unknown)'}")
    click.echo(f"  Used by:      {', '.join(info['used_by']) or '(none)'}")
    click.echo(f"  Bookmarked:   {', '.join(info['bookmarked_by']) or '(none)'}")
    click.echo(f"  Contributors: {', '.join(info['contributed_by']) or '(none)'}")
    click.echo()


@insight.command("stats")
@click.option("--json", "as_json", is_flag=True, default=False, help=_("JSON output"))
def stats_insights(as_json):
    """Cross-role sharing statistics"""
    import json as json_mod

    mgr = _load_insight_manager()
    stats = mgr.get_cross_role_stats()

    if as_json:
        click.echo(json_mod.dumps(stats, ensure_ascii=False, indent=2))
        return

    summary = stats["summary"]
    click.echo("\n=== Insight Sharing Statistics ===\n")
    click.echo(f"  Total insights:    {summary['total_insights']}")
    click.echo(f"  Total roles:  {summary['total_roles']}")
    click.echo(f"  Total uses:        {summary['total_uses']}")
    if summary["most_used"]:
        click.echo(f"  Most used:         {summary['most_used']}")
    if summary["most_shared"]:
        click.echo(f"  Most shared:       {summary['most_shared']}")

    if stats["roles"]:
        click.echo("\n--- Roles ---")
        for dev, data in stats["roles"].items():
            contributed = len(data["contributed"])
            bookmarks = len(data["bookmarks"])
            used = len(data["used"])
            click.echo(f"  {dev}: contributed {contributed}, bookmarked {bookmarks}, used {used}")

    if stats["insights"]:
        click.echo("\n--- Insights ---")
        for ins_id, data in stats["insights"].items():
            click.echo(
                f"  {ins_id}: "
                f"contributors {data['contributors']}, "
                f"users {data['users']}, "
                f"bookmarks {data['bookmarks']}"
            )

    click.echo()


@insight.command("suggest")
@click.option("--json", "as_json", is_flag=True, help=_("JSON output"))
@click.option("--auto-confirm", is_flag=True,
              help=_("Auto-confirm all candidates (non-interactive mode)"))
def suggest_insights(as_json, auto_confirm):
    """Suggest candidate Insights based on structured signals

    Extract candidate Insights from git incremental history, document change diffs,
    Task changes, and other signals. Auto-creates Insights after user confirmation
    and updates signal snapshot.
    """
    from ..insight.signal import InsightSignalCollector

    project_root = Path.cwd()
    collector = InsightSignalCollector(project_root)

    # Collect candidates
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
        click.echo(f"{EMOJI['ok']} No candidate Insights found to solidify")
        click.echo("  Hint: Try again after more development activity")
        return

    click.echo(f"\n=== Insight Candidate Recommendations ({len(candidates)}) ===\n")

    snapshot = collector.load_snapshot()
    if snapshot.last_commit:
        click.echo(f"  Last snapshot: {snapshot.last_commit[:8]}... "
                    f"({snapshot.last_timestamp[:10]})")
    else:
        click.echo("  First recommendation (no historical snapshot)")
    click.echo()

    # Display candidates
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
        # Non-interactive mode: create all
        _create_from_candidates(project_root, candidates, collector)
        return

    # Interactive mode: let user select
    click.echo("Enter candidate numbers to create (comma separated, e.g. 1,3), "
               "or 'all' to create all, 'q' to quit:")
    try:
        choice = input("> ").strip()
    except (EOFError, KeyboardInterrupt):
        click.echo("\nCancelled")
        return

    if choice.lower() == "q":
        click.echo("Cancelled")
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
        click.echo("No candidates selected")
        return

    _create_from_candidates(project_root, selected, collector)


def _create_from_candidates(project_root, candidates, collector):
    """Create Insights from candidate list"""
    mgr = _load_insight_manager()
    dm = None
    try:
        dm = _load_role_manager()
    except Exception:
        pass

    created_by = "unknown"
    if dm:
        try:
            created_by = dm.get_current_role()
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

    # Update snapshot
    last_id = created_ids[-1] if created_ids else ""
    collector.update_snapshot(insight_id=last_id)
    click.echo(f"\nCreated {len(created_ids)} Insight(s), signal snapshot updated")


# ------------------------------------------------------------------
# Graph commands (v0.9.4)
# ------------------------------------------------------------------

@insight.command("graph")
@click.option("--format", "fmt", type=click.Choice(["mermaid", "json", "text"]),
              default="text", help=_("Output format"))
@click.option("--json", "json_output", is_flag=True, default=False, help=_("JSON output (alias for --format json)"))
def insight_graph(fmt, json_output):
    """Insight association graph visualization

    Display derivation/association relationships between all Insights.

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

    # text format: human-readable graph summary
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
# Export / Import commands (v0.9.4)
# ------------------------------------------------------------------

@insight.command("export")
@click.option("--ids", default=None, help=_("Insight IDs to export, comma separated (default all)"))
@click.option("--output", "-o", default=None, help=_("Output file path (default stdout)"))
@click.option("--include-registry", is_flag=True, default=False, help=_("Include registry state"))
def export_insights(ids, output, include_registry):
    """Export Insights to portable YAML format

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
              default="skip", help=_("ID conflict strategy: skip/rename/overwrite"))
@click.option("--json", "json_output", is_flag=True, default=False, help=_("JSON output"))
def import_insights(filepath, strategy, json_output):
    """Import Insights from YAML file

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
    dm = _load_role_manager()
    imported_by = dm.get_current_role()

    results = mgr.import_insights(bundle, imported_by=imported_by, strategy=strategy)

    if json_output:
        click.echo(json_mod.dumps(results, ensure_ascii=False, indent=2))
        return

    # Update role contributed
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
