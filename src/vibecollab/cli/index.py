"""
Index & Search CLI 命令 — 语义检索引擎 (v0.9.0)

命令:
    vibecollab index     索引项目文档和 Insight
    vibecollab search    全局语义搜索
"""

from pathlib import Path
from typing import Optional

import click
from rich.table import Table

from .._compat import BULLET, EMOJI, safe_console

console = safe_console()


@click.command()
@click.option("--config", "-c", default="project.yaml", help="项目配置文件路径")
@click.option(
    "--backend", "-b", default="auto",
    type=click.Choice(["auto", "openai", "local", "pure_python"]),
    help="Embedding 后端"
)
@click.option("--rebuild", is_flag=True, help="清除旧索引后重建")
def index_cmd(config: str, backend: str, rebuild: bool):
    """索引项目文档和 Insight

    将文档按标题拆分为 chunk，生成 embedding 向量，
    存入本地向量数据库 (.vibecollab/vectors/index.db)。

    Examples:

        vibecollab index                     # 增量索引

        vibecollab index --rebuild           # 清除后重建

        vibecollab index -b pure_python      # 强制使用零依赖后端
    """
    from ..insight.embedder import Embedder, EmbedderConfig
    from ..search.indexer import Indexer
    from ..search.vector_store import VectorStore

    config_path = Path(config)
    project_root = config_path.parent if config_path.parent != Path(".") else Path.cwd()

    # 配置 Embedder
    embedder_config = EmbedderConfig(backend=backend)

    # 如果是 openai 后端，尝试从配置加载 API key
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
        console.print(f"[red]Embedding 初始化失败:[/red] {e}")
        raise SystemExit(1)

    db_path = project_root / ".vibecollab" / "vectors" / "index.db"
    store = VectorStore(db_path=db_path, dimensions=embedder.dimensions)

    # 重建模式：清除旧数据
    if rebuild:
        old_count = store.count()
        store.delete_by_source_type("document")
        store.delete_by_source_type("insight")
        console.print(f"[dim]已清除 {old_count} 条旧索引[/dim]")

    indexer = Indexer(project_root=project_root, embedder=embedder, store=store)

    console.print(f"[cyan]正在索引... (后端: {embedder.model_name})[/cyan]")

    stats = indexer.index_all()

    # 结果展示
    console.print()
    table = Table(title="索引结果", show_header=True)
    table.add_column("类型", style="cyan")
    table.add_column("数量", justify="right")
    table.add_row("文档", str(stats.documents_indexed))
    table.add_row("Insight", str(stats.insights_indexed))
    table.add_row("Chunk 总计", str(stats.chunks_total))
    table.add_row("跳过", str(stats.skipped))
    console.print(table)

    if stats.errors:
        console.print()
        console.print(f"[yellow]{EMOJI.get('warning', '!')} 索引错误:[/yellow]")
        for err in stats.errors:
            console.print(f"  {BULLET} {err}")

    console.print()
    total = store.count()
    console.print(f"[green]{EMOJI.get('success', 'OK')} 索引完成[/green] — 共 {total} 条向量")
    console.print(f"[dim]存储: {db_path}[/dim]")

    store.close()


@click.command()
@click.argument("query")
@click.option("--top", "-k", default=5, help="返回结果数量")
@click.option(
    "--type", "-t", "source_type", default=None,
    type=click.Choice(["document", "insight"]),
    help="过滤来源类型"
)
@click.option("--min-score", default=0.0, type=float, help="最低相似度阈值 (0~1)")
@click.option("--config", "-c", default="project.yaml", help="项目配置文件路径")
def search_cmd(query: str, top: int, source_type: Optional[str], min_score: float, config: str):
    """全局语义搜索

    跨 Insight / 文档统一搜索。需先运行 `vibecollab index`。

    Examples:

        vibecollab search "编码兼容性"

        vibecollab search "测试策略" -k 3

        vibecollab search "模板引擎" -t insight

        vibecollab search "Git 规范" --min-score 0.3
    """
    from ..insight.embedder import Embedder, EmbedderConfig
    from ..search.vector_store import VectorStore

    config_path = Path(config)
    project_root = config_path.parent if config_path.parent != Path(".") else Path.cwd()

    db_path = project_root / ".vibecollab" / "vectors" / "index.db"
    if not db_path.exists():
        console.print("[red]索引不存在[/red] — 请先运行 `vibecollab index`")
        raise SystemExit(1)

    # 从已有索引推断维度
    import sqlite3
    conn = sqlite3.connect(str(db_path))
    row = conn.execute("SELECT dimensions FROM vectors LIMIT 1").fetchone()
    conn.close()
    if not row:
        console.print("[red]索引为空[/red] — 请先运行 `vibecollab index`")
        raise SystemExit(1)
    dims = row[0]

    embedder = Embedder(EmbedderConfig(backend="pure_python", dimensions=dims))
    store = VectorStore(db_path=db_path, dimensions=dims)

    query_vector = embedder.embed_text(query)
    results = store.search(query_vector, top_k=top, source_type=source_type, min_score=min_score)

    if not results:
        console.print(f"[yellow]未找到与 \"{query}\" 相关的结果[/yellow]")
        if min_score > 0:
            console.print(f"[dim]提示: 尝试降低 --min-score (当前: {min_score})[/dim]")
        store.close()
        return

    console.print()
    console.print(f"[bold]搜索: \"{query}\"[/bold] (Top {len(results)})")
    console.print()

    for i, r in enumerate(results, 1):
        score_color = "green" if r.score > 0.5 else "yellow" if r.score > 0.2 else "dim"
        type_label = {"document": "DOC", "insight": "INS"}.get(r.source_type, r.source_type)
        console.print(f"  [{score_color}]{i}. [{type_label}] {r.doc_id}[/{score_color}]")
        console.print(f"     [{score_color}]相似度: {r.score:.3f}[/{score_color}]")

        # 显示文本摘要（前 100 字符）
        preview = r.text[:150].replace("\n", " ")
        if len(r.text) > 150:
            preview += "..."
        console.print(f"     [dim]{preview}[/dim]")

        # 元数据
        if r.metadata:
            heading = r.metadata.get("heading", "")
            tags = r.metadata.get("tags", [])
            if heading:
                console.print(f"     [dim]标题: {heading}[/dim]")
            if tags:
                console.print(f"     [dim]标签: {', '.join(tags[:5])}[/dim]")

        console.print()

    store.close()
