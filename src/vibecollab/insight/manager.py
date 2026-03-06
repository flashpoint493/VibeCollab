"""
Insight Manager - Core module for the insight distillation system

Manages reusable knowledge units (Insights) distilled from development practices:
- CRUD: Create, read, update, delete insight entries
- Registry: Project-level usage state management (weight, count, decay)
- Tag matching: Tag-based insight recommendations
- Traceability: Track insight origin and derivation relationships
- Consistency check: Insight entity <-> registry <-> Developer metadata sync verification
- Fingerprint: SHA-256 content integrity

Storage structure:
    .vibecollab/
    ├── insights/
    │   ├── registry.yaml       # Project registry (weight, usage state)
    │   ├── INS-001.yaml        # Insight entity
    │   ├── INS-002.yaml
    │   └── tools/              # Associated tools/scripts (future)
    │       └── INS-002/
    ├── tasks.json
    └── events.jsonl

Design principles:
- Insight entity and project registry are strictly separated
- Insight entity is a portable knowledge package without project-specific state
- Registry records project usage state of insights
- Developer .metadata.yaml records personal contributions and bookmarks
- Consistency check covers all associated data synchronization
"""

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from ..domain.event_log import Event, EventLog, EventType

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

INSIGHT_ID_PATTERN = re.compile(r"^INS-\d{3,}$")

VALID_CATEGORIES = frozenset([
    "technique", "workflow", "decision", "debug", "tool", "integration",
])

VALID_ARTIFACT_TYPES = frozenset([
    "script", "template", "config", "schema", "reference",
])

VALID_SOURCE_TYPES = frozenset([
    "task", "decision", "insight", "external",
])

# Default registry settings
DEFAULT_SETTINGS = {
    "decay_rate": 0.95,
    "decay_interval_days": 30,
    "use_reward": 0.1,
    "deactivate_threshold": 0.1,
}


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class Artifact:
    """Artifact associated with an insight (tool/script/template etc.)"""
    path: str
    type: str
    runtime: Optional[str] = None
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {"path": self.path, "type": self.type}
        if self.runtime:
            d["runtime"] = self.runtime
        if self.description:
            d["description"] = self.description
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Artifact":
        return cls(
            path=data["path"],
            type=data["type"],
            runtime=data.get("runtime"),
            description=data.get("description"),
        )


@dataclass
class Origin:
    """Traceability info for an insight

    Design principle: Traceability info must be self-describing, not dependent on any project's internal ID system.
    - context: One-line description of creation background (human-readable)
    - source.description: Natural language description of the source (required when source exists)
    - source.ref: Source project internal ID (optional hint, only for reference across projects)
    - source.url: External accessible link (optional, e.g. GitHub issue/PR)
    - source.project: Source project name (optional)
    """
    created_by: str
    created_at: str
    context: str = ""
    source_type: Optional[str] = None
    source_desc: Optional[str] = None
    source_ref: Optional[str] = None
    source_url: Optional[str] = None
    source_project: Optional[str] = None
    derived_from: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "created_by": self.created_by,
            "created_at": self.created_at,
        }
        if self.context:
            d["context"] = self.context
        if self.source_type or self.source_desc or self.source_project or self.source_url or self.source_ref:
            source: Dict[str, str] = {}
            if self.source_type:
                source["type"] = self.source_type
            if self.source_desc:
                source["description"] = self.source_desc
            if self.source_url:
                source["url"] = self.source_url
            if self.source_project:
                source["project"] = self.source_project
            if self.source_ref:
                source["ref"] = self.source_ref
            d["source"] = source
        if self.derived_from:
            d["derived_from"] = self.derived_from
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Origin":
        source = data.get("source", {})
        return cls(
            created_by=data.get("created_by", "unknown"),
            created_at=data.get("created_at", ""),
            context=data.get("context", ""),
            source_type=source.get("type"),
            source_desc=source.get("description"),
            source_ref=source.get("ref"),
            source_url=source.get("url"),
            source_project=source.get("project"),
            derived_from=data.get("derived_from", []),
        )


@dataclass
class Insight:
    """Insight entity -- a portable knowledge unit"""
    id: str
    title: str
    tags: List[str]
    category: str
    body: Dict[str, Any]
    origin: Origin
    summary: str = ""
    artifacts: List[Artifact] = field(default_factory=list)
    fingerprint: str = ""

    # Fixed fields
    kind: str = "insight"
    version: str = "1"

    def __post_init__(self):
        if not INSIGHT_ID_PATTERN.match(self.id):
            raise ValueError(f"Invalid insight ID format: {self.id} (expected INS-NNN)")
        if self.category not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category: {self.category} (valid: {VALID_CATEGORIES})")
        if not self.tags:
            raise ValueError("Insight must have at least one tag")

    def compute_fingerprint(self) -> str:
        """Compute SHA-256 content fingerprint"""
        canonical = {
            "kind": self.kind,
            "version": self.version,
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "tags": sorted(self.tags),
            "category": self.category,
            "body": self.body,
            "artifacts": [a.to_dict() for a in self.artifacts],
            "origin": self.origin.to_dict(),
        }
        raw = json.dumps(canonical, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict (for YAML output)"""
        if not self.fingerprint:
            self.fingerprint = self.compute_fingerprint()
        d: Dict[str, Any] = {
            "kind": self.kind,
            "version": self.version,
            "id": self.id,
            "title": self.title,
        }
        if self.summary:
            d["summary"] = self.summary
        d["tags"] = self.tags
        d["category"] = self.category
        d["body"] = self.body
        if self.artifacts:
            d["artifacts"] = [a.to_dict() for a in self.artifacts]
        else:
            d["artifacts"] = []
        d["origin"] = self.origin.to_dict()
        d["fingerprint"] = self.fingerprint
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Insight":
        """Deserialize from dict"""
        artifacts = [Artifact.from_dict(a) for a in data.get("artifacts", [])]
        origin = Origin.from_dict(data.get("origin", {}))
        return cls(
            id=data["id"],
            title=data.get("title", ""),
            tags=data.get("tags", []),
            category=data.get("category", "technique"),
            body=data.get("body", {}),
            origin=origin,
            summary=data.get("summary", ""),
            artifacts=artifacts,
            fingerprint=data.get("fingerprint", ""),
            kind=data.get("kind", "insight"),
            version=data.get("version", "1"),
        )


@dataclass
class RegistryEntry:
    """Registry entry -- project usage state of an insight"""
    weight: float = 1.0
    used_count: int = 0
    last_used_at: Optional[str] = None
    last_used_by: Optional[str] = None
    active: bool = True
    used_by: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "weight": round(self.weight, 4),
            "used_count": self.used_count,
            "active": self.active,
        }
        if self.last_used_at:
            d["last_used_at"] = self.last_used_at
        if self.last_used_by:
            d["last_used_by"] = self.last_used_by
        if self.used_by:
            d["used_by"] = self.used_by
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RegistryEntry":
        return cls(
            weight=data.get("weight", 1.0),
            used_count=data.get("used_count", 0),
            last_used_at=data.get("last_used_at"),
            last_used_by=data.get("last_used_by"),
            active=data.get("active", True),
            used_by=data.get("used_by", []),
        )


# ---------------------------------------------------------------------------
# Consistency check result
# ---------------------------------------------------------------------------

@dataclass
class ConsistencyReport:
    """Consistency check report"""
    ok: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# InsightManager
# ---------------------------------------------------------------------------

class InsightManager:
    """Insight distillation system manager

    Usage:
        mgr = InsightManager(project_root=Path("."))
        insight = mgr.create(
            title="Replace hardcoded values with templates",
            tags=["refactor", "jinja2"],
            category="technique",
            body={"scenario": "...", "approach": "..."},
            created_by="dev",
        )
        mgr.record_use(insight.id, used_by="qa")
        results = mgr.search_by_tags(["refactor"])
        report = mgr.check_consistency()
    """

    INSIGHTS_DIR = "insights"
    REGISTRY_FILE = "registry.yaml"

    def __init__(self, project_root: Path, data_dir: Optional[str] = None,
                 event_log: Optional[EventLog] = None):
        self.project_root = Path(project_root)
        self.data_dir = self.project_root / (data_dir or ".vibecollab")
        self.insights_dir = self.data_dir / self.INSIGHTS_DIR
        self.registry_path = self.insights_dir / self.REGISTRY_FILE
        self.event_log = event_log

    # ------------------------------------------------------------------
    # CRUD -- Insight entity
    # ------------------------------------------------------------------

    def create(self, title: str, tags: List[str], category: str,
               body: Dict[str, Any], created_by: str,
               summary: str = "",
               context: str = "",
               source_type: Optional[str] = None,
               source_desc: Optional[str] = None,
               source_ref: Optional[str] = None,
               source_url: Optional[str] = None,
               source_project: Optional[str] = None,
               derived_from: Optional[List[str]] = None,
               artifacts: Optional[List[Dict[str, Any]]] = None) -> Insight:
        """Create a new insight entry"""
        insight_id = self._next_id()
        origin = Origin(
            created_by=created_by,
            created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            context=context,
            source_type=source_type,
            source_desc=source_desc,
            source_ref=source_ref,
            source_url=source_url,
            source_project=source_project,
            derived_from=derived_from or [],
        )
        artifact_objs = [Artifact.from_dict(a) for a in (artifacts or [])]
        insight = Insight(
            id=insight_id,
            title=title,
            tags=tags,
            category=category,
            body=body,
            origin=origin,
            summary=summary,
            artifacts=artifact_objs,
        )
        self._save_insight(insight)
        self._ensure_registry_entry(insight_id)
        self._log_event(
            EventType.CUSTOM,
            created_by,
            f"Created insight {insight_id}: {title}",
            {"insight_id": insight_id, "action": "insight_created", "tags": tags},
        )
        return insight

    def get(self, insight_id: str) -> Optional[Insight]:
        """Get insight by ID"""
        path = self._insight_path(insight_id)
        if not path.exists():
            return None
        return self._load_insight(path)

    def list_all(self) -> List[Insight]:
        """List all insights"""
        if not self.insights_dir.exists():
            return []
        insights = []
        for path in sorted(self.insights_dir.glob("INS-*.yaml")):
            try:
                ins = self._load_insight(path)
                if ins:
                    insights.append(ins)
            except Exception:
                continue
        return insights

    def update(self, insight_id: str, updated_by: str, **kwargs) -> Optional[Insight]:
        """Update insight fields

        Supported kwargs: title, summary, tags, category, body, artifacts
        """
        insight = self.get(insight_id)
        if not insight:
            return None

        for key in ("title", "summary", "tags", "category", "body"):
            if key in kwargs:
                setattr(insight, key, kwargs[key])
        if "artifacts" in kwargs:
            insight.artifacts = [Artifact.from_dict(a) for a in kwargs["artifacts"]]

        # Recompute fingerprint
        insight.fingerprint = ""
        self._save_insight(insight)
        self._log_event(
            EventType.CUSTOM,
            updated_by,
            f"Updated insight {insight_id}",
            {"insight_id": insight_id, "action": "insight_updated",
             "fields": list(kwargs.keys())},
        )
        return insight

    def delete(self, insight_id: str, deleted_by: str) -> bool:
        """Delete an insight"""
        path = self._insight_path(insight_id)
        if not path.exists():
            return False
        path.unlink()
        self._remove_registry_entry(insight_id)
        self._log_event(
            EventType.CUSTOM,
            deleted_by,
            f"Deleted insight {insight_id}",
            {"insight_id": insight_id, "action": "insight_deleted"},
        )
        return True

    # ------------------------------------------------------------------
    # Registry -- project usage state
    # ------------------------------------------------------------------

    def get_registry(self) -> Tuple[Dict[str, RegistryEntry], Dict[str, Any]]:
        """Read registry, returns (entries, settings)"""
        if not self.registry_path.exists():
            return {}, dict(DEFAULT_SETTINGS)
        data = self._load_yaml(self.registry_path)
        entries = {}
        for k, v in data.get("entries", {}).items():
            entries[k] = RegistryEntry.from_dict(v)
        settings = {**DEFAULT_SETTINGS, **data.get("settings", {})}
        return entries, settings

    def record_use(self, insight_id: str, used_by: str) -> Optional[RegistryEntry]:
        """Record one insight usage, reward weight"""
        entries, settings = self.get_registry()
        entry = entries.get(insight_id)
        if entry is None:
            return None
        entry.used_count += 1
        entry.weight += settings["use_reward"]
        entry.last_used_at = datetime.now(timezone.utc).isoformat()
        entry.last_used_by = used_by
        if used_by not in entry.used_by:
            entry.used_by.append(used_by)
        if not entry.active:
            entry.active = True  # Reactivate on use
        entries[insight_id] = entry
        self._save_registry(entries, settings)
        self._log_event(
            EventType.CUSTOM,
            used_by,
            f"Used insight {insight_id} (weight={entry.weight:.2f})",
            {"insight_id": insight_id, "action": "insight_used",
             "weight": entry.weight, "used_count": entry.used_count},
        )
        return entry

    def apply_decay(self) -> List[str]:
        """Apply weight decay to all active insights

        Returns:
            List of deactivated insight IDs
        """
        entries, settings = self.get_registry()
        deactivated = []
        rate = settings["decay_rate"]
        threshold = settings["deactivate_threshold"]

        for ins_id, entry in entries.items():
            if not entry.active:
                continue
            entry.weight *= rate
            if entry.weight < threshold:
                entry.active = False
                deactivated.append(ins_id)

        self._save_registry(entries, settings)
        return deactivated

    def get_active_insights(self) -> List[Tuple[str, float]]:
        """Get all active insights and their weights, sorted by weight descending"""
        entries, _ = self.get_registry()
        active = [
            (k, e.weight) for k, e in entries.items() if e.active
        ]
        return sorted(active, key=lambda x: x[1], reverse=True)

    # ------------------------------------------------------------------
    # Tag matching and search
    # ------------------------------------------------------------------

    def search_by_tags(self, tags: List[str], active_only: bool = True) -> List[Insight]:
        """Search insights by tags, results sorted by match_score * weight"""
        all_insights = self.list_all()
        entries, _ = self.get_registry()

        scored: List[Tuple[float, Insight]] = []
        query_tags = set(t.lower() for t in tags)

        for ins in all_insights:
            if active_only:
                entry = entries.get(ins.id)
                if entry and not entry.active:
                    continue

            ins_tags = set(t.lower() for t in ins.tags)
            overlap = query_tags & ins_tags
            if not overlap:
                continue

            # Match score = intersection / union (Jaccard)
            match_score = len(overlap) / len(query_tags | ins_tags)

            # Weight bonus
            weight = 1.0
            entry = entries.get(ins.id)
            if entry:
                weight = entry.weight

            scored.append((match_score * weight, ins))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [ins for _, ins in scored]

    def search_by_category(self, category: str) -> List[Insight]:
        """Search insights by category"""
        return [ins for ins in self.list_all() if ins.category == category]

    # ------------------------------------------------------------------
    # Traceability
    # ------------------------------------------------------------------

    def get_derived_tree(self, insight_id: str) -> Dict[str, List[str]]:
        """Get insight derivation tree: who references it, and what it references"""
        all_insights = self.list_all()
        result: Dict[str, List[str]] = {
            "derived_from": [],   # Upstream references of this insight
            "derived_by": [],     # Downstream references to this insight
        }
        target = self.get(insight_id)
        if target:
            result["derived_from"] = list(target.origin.derived_from)

        for ins in all_insights:
            if insight_id in ins.origin.derived_from:
                result["derived_by"].append(ins.id)

        return result

    def get_full_trace(self, insight_id: str) -> Dict[str, Any]:
        """Get full traceability info for an insight (recursively expand derivation tree)

        Returns:
            {
                "id": "INS-001",
                "title": "...",
                "upstream": [{"id": ..., "title": ..., "upstream": [...]}],
                "downstream": [{"id": ..., "title": ..., "downstream": [...]}],
            }
        """
        visited: set = set()

        def _trace_upstream(iid: str) -> List[Dict[str, Any]]:
            if iid in visited:
                return []
            visited.add(iid)
            ins = self.get(iid)
            if not ins:
                return [{"id": iid, "title": "(missing)", "upstream": []}]
            result = []
            for parent_id in ins.origin.derived_from:
                node: Dict[str, Any] = {
                    "id": parent_id,
                    "title": "",
                    "upstream": [],
                }
                parent = self.get(parent_id)
                if parent:
                    node["title"] = parent.title
                    node["upstream"] = _trace_upstream(parent_id)
                else:
                    node["title"] = "(missing)"
                result.append(node)
            return result

        visited_down: set = set()
        all_insights = self.list_all()

        def _trace_downstream(iid: str) -> List[Dict[str, Any]]:
            if iid in visited_down:
                return []
            visited_down.add(iid)
            result = []
            for ins in all_insights:
                if iid in ins.origin.derived_from:
                    node: Dict[str, Any] = {
                        "id": ins.id,
                        "title": ins.title,
                        "downstream": _trace_downstream(ins.id),
                    }
                    result.append(node)
            return result

        target = self.get(insight_id)
        return {
            "id": insight_id,
            "title": target.title if target else "(missing)",
            "upstream": _trace_upstream(insight_id),
            "downstream": _trace_downstream(insight_id),
        }

    # ------------------------------------------------------------------
    # Cross-developer sharing
    # ------------------------------------------------------------------

    def get_insight_developers(self, insight_id: str) -> Dict[str, Any]:
        """Get cross-developer info for a given insight

        Returns:
            {
                "created_by": "dev",
                "used_by": ["qa", "pm"],
                "bookmarked_by": ["qa"],
                "contributed_by": ["dev"],
            }
        """
        result: Dict[str, Any] = {
            "created_by": None,
            "used_by": [],
            "bookmarked_by": [],
            "contributed_by": [],
        }

        # Get creator from insight entity
        ins = self.get(insight_id)
        if ins:
            result["created_by"] = ins.origin.created_by

        # Get users from registry
        entries, _ = self.get_registry()
        entry = entries.get(insight_id)
        if entry:
            result["used_by"] = list(entry.used_by)

        # Reverse lookup contributed and bookmarks from developer metadata
        developers_dir = self.project_root / "docs" / "developers"
        if developers_dir.exists():
            for dev_dir in sorted(developers_dir.iterdir()):
                if not dev_dir.is_dir() or dev_dir.name.startswith("."):
                    continue
                meta_path = dev_dir / ".metadata.yaml"
                if not meta_path.exists():
                    continue
                try:
                    meta = self._load_yaml(meta_path)
                    if insight_id in meta.get("contributed", []):
                        result["contributed_by"].append(dev_dir.name)
                    if insight_id in meta.get("bookmarks", []):
                        result["bookmarked_by"].append(dev_dir.name)
                except Exception:
                    continue

        return result

    def get_cross_developer_stats(self) -> Dict[str, Any]:
        """Aggregate cross-developer sharing statistics

        Returns:
            {
                "developers": {
                    "dev": {"contributed": [...], "bookmarks": [...], "used": [...]},
                    "qa": {...},
                },
                "insights": {
                    "INS-001": {"contributors": 1, "users": 2, "bookmarks": 1},
                },
                "summary": {
                    "total_insights": N,
                    "total_developers": N,
                    "total_uses": N,
                    "most_used": "INS-001",
                    "most_shared": "INS-002",
                },
            }
        """
        all_insights = self.list_all()
        entries, _ = self.get_registry()

        # Collect developer metadata
        dev_stats: Dict[str, Dict[str, list]] = {}
        developers_dir = self.project_root / "docs" / "developers"
        if developers_dir.exists():
            for dev_dir in sorted(developers_dir.iterdir()):
                if not dev_dir.is_dir() or dev_dir.name.startswith("."):
                    continue
                meta_path = dev_dir / ".metadata.yaml"
                dev_name = dev_dir.name
                dev_stats[dev_name] = {
                    "contributed": [],
                    "bookmarks": [],
                    "used": [],
                }
                if meta_path.exists():
                    try:
                        meta = self._load_yaml(meta_path)
                        dev_stats[dev_name]["contributed"] = meta.get("contributed", [])
                        dev_stats[dev_name]["bookmarks"] = meta.get("bookmarks", [])
                    except Exception:
                        pass

        # Supplement usage data from registry used_by
        for ins_id, entry in entries.items():
            for user in entry.used_by:
                if user not in dev_stats:
                    dev_stats[user] = {"contributed": [], "bookmarks": [], "used": []}
                if ins_id not in dev_stats[user]["used"]:
                    dev_stats[user]["used"].append(ins_id)

        # Build insight-level statistics
        insight_stats: Dict[str, Dict[str, int]] = {}
        for ins in all_insights:
            ins_id = ins.id
            entry = entries.get(ins_id)
            contributors = sum(
                1 for d in dev_stats.values() if ins_id in d["contributed"]
            )
            users = len(entry.used_by) if entry else 0
            bookmarks = sum(
                1 for d in dev_stats.values() if ins_id in d["bookmarks"]
            )
            insight_stats[ins_id] = {
                "contributors": contributors,
                "users": users,
                "bookmarks": bookmarks,
            }

        # Summary
        total_uses = sum(e.used_count for e in entries.values())
        most_used = max(entries.items(), key=lambda x: x[1].used_count)[0] if entries else None
        # most_shared = highest combined (users + bookmarks)
        most_shared = None
        if insight_stats:
            most_shared = max(
                insight_stats.items(),
                key=lambda x: x[1]["users"] + x[1]["bookmarks"],
            )[0]

        return {
            "developers": dev_stats,
            "insights": insight_stats,
            "summary": {
                "total_insights": len(all_insights),
                "total_developers": len(dev_stats),
                "total_uses": total_uses,
                "most_used": most_used,
                "most_shared": most_shared,
            },
        }

    # ------------------------------------------------------------------
    # Consistency check
    # ------------------------------------------------------------------

    def check_consistency(self) -> ConsistencyReport:
        """Full consistency check

        Check items:
        1. All IDs in registry have corresponding insight files
        2. All insight files are registered in registry
        3. derived_from referenced IDs all exist
        4. Developer .metadata.yaml contributed/bookmarks IDs all exist
        5. Fingerprint consistency (file content not tampered)
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Collect all insight files
        all_insights = self.list_all()
        file_ids = {ins.id for ins in all_insights}

        # Collect registry entries
        entries, _ = self.get_registry()
        registry_ids = set(entries.keys())

        # 1. Registry entry exists but file missing
        orphan_registry = registry_ids - file_ids
        for oid in orphan_registry:
            errors.append(f"Registry entry '{oid}' has no corresponding insight file")

        # 2. File exists but not registered
        unregistered = file_ids - registry_ids
        for uid in unregistered:
            errors.append(f"Insight file '{uid}' is not registered in registry.yaml")

        # 3. derived_from reference check
        for ins in all_insights:
            for ref_id in ins.origin.derived_from:
                if ref_id not in file_ids:
                    errors.append(
                        f"Insight '{ins.id}' derives from '{ref_id}' which does not exist"
                    )

        # 4. Developer metadata reference check
        dev_meta_errors = self._check_developer_metadata(file_ids)
        errors.extend(dev_meta_errors)

        # 5. Fingerprint consistency
        for ins in all_insights:
            if ins.fingerprint:
                expected = ins.compute_fingerprint()
                if ins.fingerprint != expected:
                    errors.append(
                        f"Insight '{ins.id}' fingerprint mismatch "
                        f"(stored={ins.fingerprint[:16]}... expected={expected[:16]}...)"
                    )

        # Warnings: low weight but still active
        for ins_id, entry in entries.items():
            if entry.active and entry.weight < 0.3:
                warnings.append(
                    f"Insight '{ins_id}' has low weight ({entry.weight:.2f}) but is still active"
                )

        return ConsistencyReport(
            ok=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _check_developer_metadata(self, valid_ids: set) -> List[str]:
        """Check insight references in developer .metadata.yaml"""
        errors = []
        developers_dir = self.project_root / "docs" / "developers"
        if not developers_dir.exists():
            return errors

        for dev_dir in developers_dir.iterdir():
            if not dev_dir.is_dir() or dev_dir.name.startswith("."):
                continue
            meta_path = dev_dir / ".metadata.yaml"
            if not meta_path.exists():
                continue
            try:
                meta = self._load_yaml(meta_path)
                for field_name in ("contributed", "bookmarks"):
                    for ref_id in meta.get(field_name, []):
                        if ref_id not in valid_ids:
                            errors.append(
                                f"Developer '{dev_dir.name}' {field_name} "
                                f"references '{ref_id}' which does not exist"
                            )
            except Exception:
                continue

        return errors

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _next_id(self) -> str:
        """Generate next INS-NNN ID"""
        self.insights_dir.mkdir(parents=True, exist_ok=True)
        existing = [p.stem for p in self.insights_dir.glob("INS-*.yaml")]
        if not existing:
            return "INS-001"
        nums = []
        for name in existing:
            m = re.match(r"INS-(\d+)", name)
            if m:
                nums.append(int(m.group(1)))
        next_num = max(nums) + 1 if nums else 1
        return f"INS-{next_num:03d}"

    def _insight_path(self, insight_id: str) -> Path:
        return self.insights_dir / f"{insight_id}.yaml"

    def _save_insight(self, insight: Insight) -> None:
        """Save insight to YAML file"""
        self.insights_dir.mkdir(parents=True, exist_ok=True)
        if not insight.fingerprint:
            insight.fingerprint = insight.compute_fingerprint()
        path = self._insight_path(insight.id)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(insight.to_dict(), f, allow_unicode=True, sort_keys=False,
                      default_flow_style=False)

    def _load_insight(self, path: Path) -> Optional[Insight]:
        """Load insight from YAML file"""
        data = self._load_yaml(path)
        if not data:
            return None
        return Insight.from_dict(data)

    def _ensure_registry_entry(self, insight_id: str) -> None:
        """Ensure the registry has an entry for this ID"""
        entries, settings = self.get_registry()
        if insight_id not in entries:
            entries[insight_id] = RegistryEntry()
            self._save_registry(entries, settings)

    def _remove_registry_entry(self, insight_id: str) -> None:
        """Remove entry from registry"""
        entries, settings = self.get_registry()
        if insight_id in entries:
            del entries[insight_id]
            self._save_registry(entries, settings)

    def _save_registry(self, entries: Dict[str, RegistryEntry],
                       settings: Dict[str, Any]) -> None:
        """Save registry"""
        self.insights_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "schema_version": "1",
            "entries": {k: v.to_dict() for k, v in entries.items()},
            "settings": settings,
        }
        with open(self.registry_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False,
                      default_flow_style=False)

    def _load_yaml(self, path: Path) -> dict:
        """Safely load YAML"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    # ------------------------------------------------------------------
    # Duplicate detection (v0.9.4)
    # ------------------------------------------------------------------

    def find_duplicates(
        self,
        title: str,
        tags: List[str],
        body: Optional[Dict[str, Any]] = None,
        threshold: float = 0.6,
    ) -> List[Dict[str, Any]]:
        """Detect similarity with existing Insights, return possible duplicates.

        Three-level detection strategy:
        1. Fingerprint exact match (score=1.0) -- title+tags+body completely identical
        2. Title similarity (Jaccard on words)
        3. Tag overlap (Jaccard on tags)
        Combined score = 0.5 * title_sim + 0.5 * tag_sim

        Args:
            title: New Insight title
            tags: New Insight tag list
            body: New Insight body (optional, for fingerprint exact match)
            threshold: Similarity threshold (0~1), above this is considered potential duplicate

        Returns:
            List of duplicate candidates sorted by similarity descending:
            [{"id": "INS-001", "title": "...", "score": 0.85, "reason": "..."}, ...]
        """
        all_insights = self.list_all()
        if not all_insights:
            return []

        # 1. Exact content match (title + sorted tags + body)
        if body is not None:
            new_content_key = self._content_key(title, tags, body)
            for ins in all_insights:
                existing_key = self._content_key(ins.title, ins.tags, ins.body)
                if new_content_key == existing_key:
                    return [{"id": ins.id, "title": ins.title,
                             "score": 1.0, "reason": "exact_content"}]

        # 2+3. Title + tag combined similarity
        new_title_tokens = set(title.lower().split())
        new_tags_set = set(t.lower() for t in tags)
        candidates: List[Dict[str, Any]] = []

        for ins in all_insights:
            # Title Jaccard
            ins_title_tokens = set(ins.title.lower().split())
            title_union = new_title_tokens | ins_title_tokens
            title_sim = (len(new_title_tokens & ins_title_tokens) / len(title_union)
                         if title_union else 0.0)

            # Tag Jaccard
            ins_tags_set = set(t.lower() for t in ins.tags)
            tag_union = new_tags_set | ins_tags_set
            tag_sim = (len(new_tags_set & ins_tags_set) / len(tag_union)
                       if tag_union else 0.0)

            score = 0.5 * title_sim + 0.5 * tag_sim
            if score >= threshold:
                reason_parts = []
                if title_sim >= threshold:
                    reason_parts.append(f"title_sim={title_sim:.2f}")
                if tag_sim >= threshold:
                    reason_parts.append(f"tag_sim={tag_sim:.2f}")
                candidates.append({
                    "id": ins.id,
                    "title": ins.title,
                    "score": round(score, 3),
                    "reason": ", ".join(reason_parts) or f"combined={score:.2f}",
                })

        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates

    def _content_key(self, title: str, tags: List[str],
                     body: Dict[str, Any]) -> str:
        """Compute content digest key for exact deduplication (ignores id/origin)"""
        canonical = {
            "title": title,
            "tags": sorted(t.lower() for t in tags),
            "body": body,
        }
        raw = json.dumps(canonical, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    # ------------------------------------------------------------------
    # Global association graph (v0.9.4)
    # ------------------------------------------------------------------

    def build_graph(self) -> Dict[str, Any]:
        """Build the global association graph of all Insights.

        Returns:
            {
                "nodes": [{"id": "INS-001", "title": "...", "category": "...",
                            "tags": [...], "weight": 1.0, "active": True}],
                "edges": [{"from": "INS-001", "to": "INS-002",
                            "type": "derived_from"}],
                "stats": {"node_count": N, "edge_count": M,
                           "isolated_count": K, "components": C}
            }
        """
        all_insights = self.list_all()
        entries, _ = self.get_registry()

        nodes = []
        edges = []
        connected_ids: set = set()

        for ins in all_insights:
            entry = entries.get(ins.id)
            nodes.append({
                "id": ins.id,
                "title": ins.title,
                "category": ins.category,
                "tags": ins.tags,
                "weight": entry.weight if entry else 1.0,
                "active": entry.active if entry else True,
            })
            for parent_id in ins.origin.derived_from:
                edges.append({
                    "from": parent_id,
                    "to": ins.id,
                    "type": "derived_from",
                })
                connected_ids.add(parent_id)
                connected_ids.add(ins.id)

        all_ids = {ins.id for ins in all_insights}
        isolated_count = len(all_ids - connected_ids)

        # Count connected components
        components = self._count_components(all_ids, edges)

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "node_count": len(nodes),
                "edge_count": len(edges),
                "isolated_count": isolated_count,
                "components": components,
            },
        }

    def _count_components(self, all_ids: set, edges: List[Dict[str, str]]) -> int:
        """Union-Find algorithm to count connected components"""
        parent: Dict[str, str] = {i: i for i in all_ids}

        def find(x: str) -> str:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a: str, b: str) -> None:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

        for e in edges:
            f, t = e["from"], e["to"]
            if f in all_ids and t in all_ids:
                union(f, t)

        return len({find(i) for i in all_ids}) if all_ids else 0

    def to_mermaid(self, graph: Optional[Dict[str, Any]] = None) -> str:
        """Convert graph to Mermaid flowchart format."""
        if graph is None:
            graph = self.build_graph()

        lines = ["graph LR"]
        for node in graph["nodes"]:
            label = node["title"].replace('"', "'")
            lines.append(f'    {node["id"]}["{node["id"]}: {label}"]')

        for edge in graph["edges"]:
            lines.append(f'    {edge["from"]} --> {edge["to"]}')

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Import / Export (v0.9.4)
    # ------------------------------------------------------------------

    def export_insights(self, insight_ids: Optional[List[str]] = None,
                        include_registry: bool = False) -> Dict[str, Any]:
        """Export Insights to a portable dictionary format.

        Args:
            insight_ids: List of IDs to export, None means all
            include_registry: Whether to include registry state (weight/count)

        Returns:
            {
                "format": "vibecollab-insight-export",
                "version": "1",
                "exported_at": "...",
                "source_project": "...",
                "insights": [{...}, ...],
                "registry": {...}  # Only when include_registry=True
            }
        """
        all_insights = self.list_all()

        if insight_ids is not None:
            ids_set = set(insight_ids)
            selected = [ins for ins in all_insights if ins.id in ids_set]
        else:
            selected = all_insights

        # Read project name
        project_name = ""
        project_yaml_path = self.project_root / "project.yaml"
        if project_yaml_path.exists():
            pdata = self._load_yaml(project_yaml_path)
            project_name = pdata.get("project_name", "")

        bundle: Dict[str, Any] = {
            "format": "vibecollab-insight-export",
            "version": "1",
            "exported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source_project": project_name,
            "count": len(selected),
            "insights": [ins.to_dict() for ins in selected],
        }

        if include_registry:
            entries, settings = self.get_registry()
            reg_data = {}
            for ins in selected:
                if ins.id in entries:
                    reg_data[ins.id] = entries[ins.id].to_dict()
            bundle["registry"] = reg_data

        return bundle

    def import_insights(self, bundle: Dict[str, Any],
                        imported_by: str,
                        strategy: str = "skip") -> Dict[str, Any]:
        """Import Insights from an export bundle.

        Args:
            bundle: Dictionary produced by export_insights()
            imported_by: Operator performing the import
            strategy: ID conflict strategy
                - "skip": Skip already existing IDs
                - "rename": Automatically assign new IDs
                - "overwrite": Overwrite existing Insights

        Returns:
            {"imported": [...ids], "skipped": [...ids],
             "renamed": {old_id: new_id, ...}, "errors": [...]}
        """
        if bundle.get("format") != "vibecollab-insight-export":
            return {"imported": [], "skipped": [], "renamed": {},
                    "errors": ["Invalid bundle format"]}

        results: Dict[str, Any] = {
            "imported": [],
            "skipped": [],
            "renamed": {},
            "errors": [],
        }

        source_project = bundle.get("source_project", "unknown")
        insights_data = bundle.get("insights", [])

        for ins_data in insights_data:
            try:
                old_id = ins_data.get("id", "")
                existing = self.get(old_id)

                if existing and strategy == "skip":
                    results["skipped"].append(old_id)
                    continue
                elif existing and strategy == "rename":
                    new_id = self._next_id()
                    ins_data["id"] = new_id
                    results["renamed"][old_id] = new_id
                elif existing and strategy == "overwrite":
                    pass  # Overwrite directly
                elif not existing:
                    pass  # New ID, write directly

                # Mark source project (if original doesn't have one)
                if "origin" not in ins_data:
                    ins_data["origin"] = {}
                origin = ins_data["origin"]
                if "source" not in origin:
                    origin["source"] = {}
                if not origin["source"].get("project"):
                    origin["source"]["project"] = source_project

                insight = Insight.from_dict(ins_data)
                self._save_insight(insight)
                self._ensure_registry_entry(insight.id)

                actual_id = ins_data["id"]
                if actual_id not in results.get("renamed", {}).values():
                    results["imported"].append(actual_id)
                else:
                    results["imported"].append(actual_id)

                self._log_event(
                    EventType.CUSTOM, imported_by,
                    f"Imported insight {actual_id} from {source_project}",
                    {"insight_id": actual_id, "action": "insight_imported",
                     "source_project": source_project,
                     "original_id": old_id},
                )
            except Exception as e:
                results["errors"].append(f"{old_id}: {e}")

        # Import registry state (optional)
        if "registry" in bundle:
            entries, settings = self.get_registry()
            for ins_id, reg_data in bundle["registry"].items():
                # If ID was renamed, map to new ID
                mapped_id = results["renamed"].get(ins_id, ins_id)
                if mapped_id in entries:
                    # Keep local weight, but merge usage count
                    entries[mapped_id].used_count += reg_data.get("used_count", 0)
            self._save_registry(entries, settings)

        return results

    def _log_event(self, event_type: str, actor: str, summary: str,
                   payload: Dict[str, Any]) -> None:
        """Record audit event"""
        if self.event_log:
            self.event_log.append(Event(
                event_type=event_type,
                actor=actor,
                summary=summary,
                payload=payload,
            ))
