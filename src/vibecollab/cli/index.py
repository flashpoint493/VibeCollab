"""
Index & Search CLI Commands -- Semantic Search Engine (v0.9.0)

Commands:
    vibecollab index     Index project documents and Insights
    vibecollab search    Global semantic search
"""

from pathlib import Path
from typing import Optional

import click
from rich.table import Table

from .._compat import BULLET, EMOJI, safe_console
from ..i18n import _

console = safe_console()


@click.command()
@click.option("--config", "-c", default="project.yaml", help=_("Project config file path"))
@click.option(
    "--backend", "-b", default="auto",
    type=click.Choice(["auto", "openai", "local", "pure_python"]),
    help=_("Embedding backend")
)
@click.option("--rebuild", is_flag=True, help=_("Rebuild after clearing old index"))
def index_cmd(config: str, backend: str, rebuild: bool):
    """Index project documents and Insights

    Split documents by heading into chunks, generate embedding vectors,
    and store in local vector database (.vibecollab/vectors/index.db).

    Examples:

        vibecollab index                     # Incremental index

        vibecollab index --rebuild           # Clear and rebuild

        vibecollab index -b pure_python      # Force zero-dependency backend
    """
    from ..insight.embedder import Embedder, EmbedderConfig
    from ..search.indexer import Indexer
    from ..search.vector_store import VectorStore

    config_path = Path(config)
    project_root = config_path.parent if config_path.parent != Path(".") else Path.cwd()

    # Configure Embedder
    embedder_config = EmbedderConfig(backend=backend)

    # If openai backend, try loading API key from config
    if backend == "openai" or (backend == "auto" and not embedder_config.api_key):
        try:
            from ..core.config_manager import resolve_llm_config
            llm_cfg = resolve_llm_config()
            if llm_cfg.api_key:
                embedder_config.api_key = llm_cfg.api_key
                embedder_config.base_url = llm_cfg.base_url or "https://api.openai.com/v1"
        except Exception:
            pass

    try:
        embedder = Embedder(embedder_config)
    except Exception as e:
        console.print(f"[red]{_('Embedding initialization failed:')}[/red] {e}")
        raise SystemExit(1)

    db_path = project_root / ".vibecollab" / "vectors" / "index.db"
    store = VectorStore(db_path=db_path, dimensions=embedder.dimensions)

    # Rebuild mode: clear old data
    if rebuild:
        old_count = store.count()
        store.delete_by_source_type("document")
        store.delete_by_source_type("insight")
        console.print(f"[dim]{_('Cleared {n} old index entries').format(n=old_count)}[/dim]")

    indexer = Indexer(project_root=project_root, embedder=embedder, store=store)

    console.print(f"[cyan]{_('Indexing... (backend: {name})').format(name=embedder.model_name)}[/cyan]")

    stats = indexer.index_all()

    # Display results
    console.print()
    table = Table(title=_("Index Results"), show_header=True)
    table.add_column(_("Type"), style="cyan")
    table.add_column(_("Count"), justify="right")
    table.add_row(_("Documents"), str(stats.documents_indexed))
    table.add_row(_("Insights"), str(stats.insights_indexed))
    table.add_row(_("Chunks Total"), str(stats.chunks_total))
    table.add_row(_("Skipped"), str(stats.skipped))
    console.print(table)

    if stats.errors:
        console.print()
        console.print(f"[yellow]{EMOJI.get('warning', '!')} {_('Index errors:')}[/yellow]")
        for err in stats.errors:
            console.print(f"  {BULLET} {err}")

    console.print()
    total = store.count()
    console.print(f"[green]{EMOJI.get('success', 'OK')} {_('Index complete')}[/green] -- {total} {_('vectors total')}")
    console.print(f"[dim]{_('Storage:')} {db_path}[/dim]")

    store.close()


@click.command()
@click.argument("query")
@click.option("--top", "-k", default=5, help=_("Number of results"))
@click.option(
    "--type", "-t", "source_type", default=None,
    type=click.Choice(["document", "insight"]),
    help=_("Filter source type")
)
@click.option("--min-score", default=0.0, type=float, help=_("Minimum similarity threshold (0~1)"))
@click.option("--config", "-c", default="project.yaml", help=_("Project config file path"))
def search_cmd(query: str, top: int, source_type: Optional[str], min_score: float, config: str):
    """Global semantic search

    Unified search across Insights / documents. Run `vibecollab index` first.

    Examples:

        vibecollab search "encoding compatibility"

        vibecollab search "test strategy" -k 3

        vibecollab search "template engine" -t insight

        vibecollab search "Git conventions" --min-score 0.3
    """
    from ..insight.embedder import Embedder, EmbedderConfig
    from ..search.vector_store import VectorStore

    config_path = Path(config)
    project_root = config_path.parent if config_path.parent != Path(".") else Path.cwd()

    db_path = project_root / ".vibecollab" / "vectors" / "index.db"
    if not db_path.exists():
        console.print(f"[red]{_('Index does not exist')}[/red] -- {_('please run `vibecollab index` first')}")
        raise SystemExit(1)

    # Infer dimensions from existing index
    import sqlite3
    conn = sqlite3.connect(str(db_path))
    row = conn.execute("SELECT dimensions FROM vectors LIMIT 1").fetchone()
    conn.close()
    if not row:
        console.print(f"[red]{_('Index is empty')}[/red] -- {_('please run `vibecollab index` first')}")
        raise SystemExit(1)
    dims = row[0]

    embedder = Embedder(EmbedderConfig(backend="pure_python", dimensions=dims))
    store = VectorStore(db_path=db_path, dimensions=dims)

    query_vector = embedder.embed_text(query)
    results = store.search(query_vector, top_k=top, source_type=source_type, min_score=min_score)

    if not results:
        msg = _('No results found for "{query}"').format(query=query)
        console.print(f"[yellow]{msg}[/yellow]")
        if min_score > 0:
            console.print(f"[dim]{_('Hint: Try lowering --min-score (current: {score})').format(score=min_score)}[/dim]")
        store.close()
        return

    console.print()
    console.print(f"[bold]{_('Search:')} \"{query}\"[/bold] ({_('Top')} {len(results)})")
    console.print()

    for i, r in enumerate(results, 1):
        score_color = "green" if r.score > 0.5 else "yellow" if r.score > 0.2 else "dim"
        type_label = {"document": "DOC", "insight": "INS"}.get(r.source_type, r.source_type)
        console.print(f"  [{score_color}]{i}. [{type_label}] {r.doc_id}[/{score_color}]")
        console.print(f"     [{score_color}]{_('Similarity:')} {r.score:.3f}[/{score_color}]")

        # Show text preview (first 100 chars)
        preview = r.text[:150].replace("\n", " ")
        if len(r.text) > 150:
            preview += "..."
        console.print(f"     [dim]{preview}[/dim]")

        # Metadata
        if r.metadata:
            heading = r.metadata.get("heading", "")
            tags = r.metadata.get("tags", [])
            if heading:
                console.print(f"     [dim]Heading: {heading}[/dim]")
            if tags:
                console.print(f"     [dim]Tags: {', '.join(tags[:5])}[/dim]")

        console.print()

    store