"""
Insight Manager - 沉淀系统核心模块

管理从开发实践中提炼的可复用知识单元（Insight），提供：
- CRUD：创建、读取、更新、删除沉淀条目
- Registry：项目级使用状态管理（权重、计数、衰减）
- Tag 匹配：基于标签的沉淀推荐
- 溯源：追踪沉淀的来源和派生关系
- 一致性校验：沉淀本体 ↔ 注册表 ↔ Developer 元数据的同步检查
- 指纹：SHA-256 内容完整性

存储结构：
    .vibecollab/
    ├── insights/
    │   ├── registry.yaml       # 项目注册表（权重、使用状态）
    │   ├── INS-001.yaml        # 沉淀本体
    │   ├── INS-002.yaml
    │   └── tools/              # 关联工具/脚本（未来）
    │       └── INS-002/
    ├── tasks.json
    └── events.jsonl

Design principles:
- 沉淀本体与项目注册表严格分离
- 沉淀本体是可移植的知识包，不含项目特定状态
- 注册表记录项目对沉淀的使用状态
- Developer .metadata.yaml 记录个人贡献和收藏
- 一致性校验覆盖所有关联数据的同步
"""

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from .event_log import Event, EventLog, EventType

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
    """沉淀关联的制品（工具/脚本/模板等）"""
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
    """沉淀的溯源信息"""
    created_by: str
    created_at: str
    source_type: Optional[str] = None
    source_ref: Optional[str] = None
    derived_from: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "created_by": self.created_by,
            "created_at": self.created_at,
        }
        if self.source_type or self.source_ref:
            d["source"] = {}
            if self.source_type:
                d["source"]["type"] = self.source_type
            if self.source_ref:
                d["source"]["ref"] = self.source_ref
        if self.derived_from:
            d["derived_from"] = self.derived_from
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Origin":
        source = data.get("source", {})
        return cls(
            created_by=data.get("created_by", "unknown"),
            created_at=data.get("created_at", ""),
            source_type=source.get("type"),
            source_ref=source.get("ref"),
            derived_from=data.get("derived_from", []),
        )


@dataclass
class Insight:
    """沉淀本体 — 可移植的知识单元"""
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
        """计算 SHA-256 内容指纹"""
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
        """序列化为 dict（用于 YAML 输出）"""
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
        """从 dict 反序列化"""
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
    """注册表条目 — 项目对某条沉淀的使用状态"""
    weight: float = 1.0
    used_count: int = 0
    last_used_at: Optional[str] = None
    last_used_by: Optional[str] = None
    active: bool = True

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
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RegistryEntry":
        return cls(
            weight=data.get("weight", 1.0),
            used_count=data.get("used_count", 0),
            last_used_at=data.get("last_used_at"),
            last_used_by=data.get("last_used_by"),
            active=data.get("active", True),
        )


# ---------------------------------------------------------------------------
# Consistency check result
# ---------------------------------------------------------------------------

@dataclass
class ConsistencyReport:
    """一致性校验报告"""
    ok: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# InsightManager
# ---------------------------------------------------------------------------

class InsightManager:
    """沉淀系统管理器

    Usage:
        mgr = InsightManager(project_root=Path("."))
        insight = mgr.create(
            title="模板替换硬编码",
            tags=["refactor", "jinja2"],
            category="technique",
            body={"scenario": "...", "approach": "..."},
            created_by="ocarina",
        )
        mgr.record_use(insight.id, used_by="alice")
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
    # CRUD — Insight 本体
    # ------------------------------------------------------------------

    def create(self, title: str, tags: List[str], category: str,
               body: Dict[str, Any], created_by: str,
               summary: str = "",
               source_type: Optional[str] = None,
               source_ref: Optional[str] = None,
               derived_from: Optional[List[str]] = None,
               artifacts: Optional[List[Dict[str, Any]]] = None) -> Insight:
        """创建新的沉淀条目"""
        insight_id = self._next_id()
        origin = Origin(
            created_by=created_by,
            created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            source_type=source_type,
            source_ref=source_ref,
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
        """按 ID 获取沉淀"""
        path = self._insight_path(insight_id)
        if not path.exists():
            return None
        return self._load_insight(path)

    def list_all(self) -> List[Insight]:
        """列出所有沉淀"""
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
        """更新沉淀字段

        支持的 kwargs: title, summary, tags, category, body, artifacts
        """
        insight = self.get(insight_id)
        if not insight:
            return None

        for key in ("title", "summary", "tags", "category", "body"):
            if key in kwargs:
                setattr(insight, key, kwargs[key])
        if "artifacts" in kwargs:
            insight.artifacts = [Artifact.from_dict(a) for a in kwargs["artifacts"]]

        # 重新计算指纹
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
        """删除沉淀"""
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
    # Registry — 项目使用状态
    # ------------------------------------------------------------------

    def get_registry(self) -> Tuple[Dict[str, RegistryEntry], Dict[str, Any]]:
        """读取注册表，返回 (entries, settings)"""
        if not self.registry_path.exists():
            return {}, dict(DEFAULT_SETTINGS)
        data = self._load_yaml(self.registry_path)
        entries = {}
        for k, v in data.get("entries", {}).items():
            entries[k] = RegistryEntry.from_dict(v)
        settings = {**DEFAULT_SETTINGS, **data.get("settings", {})}
        return entries, settings

    def record_use(self, insight_id: str, used_by: str) -> Optional[RegistryEntry]:
        """记录一次沉淀使用，奖励权重"""
        entries, settings = self.get_registry()
        entry = entries.get(insight_id)
        if entry is None:
            return None
        entry.used_count += 1
        entry.weight += settings["use_reward"]
        entry.last_used_at = datetime.now(timezone.utc).isoformat()
        entry.last_used_by = used_by
        if not entry.active:
            entry.active = True  # 使用时重新激活
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
        """对所有活跃沉淀应用权重衰减

        Returns:
            被停用的 insight ID 列表
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
        """获取所有活跃沉淀及其权重，按权重降序"""
        entries, _ = self.get_registry()
        active = [
            (k, e.weight) for k, e in entries.items() if e.active
        ]
        return sorted(active, key=lambda x: x[1], reverse=True)

    # ------------------------------------------------------------------
    # Tag 匹配与搜索
    # ------------------------------------------------------------------

    def search_by_tags(self, tags: List[str], active_only: bool = True) -> List[Insight]:
        """按标签搜索沉淀，结果按匹配度 * 权重排序"""
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

            # 匹配度 = 交集 / 并集 (Jaccard)
            match_score = len(overlap) / len(query_tags | ins_tags)

            # 权重加成
            weight = 1.0
            entry = entries.get(ins.id)
            if entry:
                weight = entry.weight

            scored.append((match_score * weight, ins))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [ins for _, ins in scored]

    def search_by_category(self, category: str) -> List[Insight]:
        """按分类搜索沉淀"""
        return [ins for ins in self.list_all() if ins.category == category]

    # ------------------------------------------------------------------
    # 溯源
    # ------------------------------------------------------------------

    def get_derived_tree(self, insight_id: str) -> Dict[str, List[str]]:
        """获取沉淀的派生树：谁引用了它，它引用了谁"""
        all_insights = self.list_all()
        result: Dict[str, List[str]] = {
            "derived_from": [],   # 该沉淀引用的上游
            "derived_by": [],     # 引用该沉淀的下游
        }
        target = self.get(insight_id)
        if target:
            result["derived_from"] = list(target.origin.derived_from)

        for ins in all_insights:
            if insight_id in ins.origin.derived_from:
                result["derived_by"].append(ins.id)

        return result

    # ------------------------------------------------------------------
    # 一致性校验
    # ------------------------------------------------------------------

    def check_consistency(self) -> ConsistencyReport:
        """全量一致性校验

        检查项：
        1. 注册表中的 ID 都有对应的 insight 文件
        2. 所有 insight 文件都在注册表中注册
        3. derived_from 引用的 ID 都存在
        4. Developer .metadata.yaml 中的 contributed/bookmarks ID 都存在
        5. 指纹一致性（文件内容未被篡改）
        """
        errors: List[str] = []
        warnings: List[str] = []

        # 收集所有 insight 文件
        all_insights = self.list_all()
        file_ids = {ins.id for ins in all_insights}

        # 收集注册表 entries
        entries, _ = self.get_registry()
        registry_ids = set(entries.keys())

        # 1. 注册表中有但文件不存在
        orphan_registry = registry_ids - file_ids
        for oid in orphan_registry:
            errors.append(f"Registry entry '{oid}' has no corresponding insight file")

        # 2. 文件存在但未注册
        unregistered = file_ids - registry_ids
        for uid in unregistered:
            errors.append(f"Insight file '{uid}' is not registered in registry.yaml")

        # 3. derived_from 引用检查
        for ins in all_insights:
            for ref_id in ins.origin.derived_from:
                if ref_id not in file_ids:
                    errors.append(
                        f"Insight '{ins.id}' derives from '{ref_id}' which does not exist"
                    )

        # 4. Developer metadata 引用检查
        dev_meta_errors = self._check_developer_metadata(file_ids)
        errors.extend(dev_meta_errors)

        # 5. 指纹一致性
        for ins in all_insights:
            if ins.fingerprint:
                expected = ins.compute_fingerprint()
                if ins.fingerprint != expected:
                    errors.append(
                        f"Insight '{ins.id}' fingerprint mismatch "
                        f"(stored={ins.fingerprint[:16]}... expected={expected[:16]}...)"
                    )

        # Warnings: 低权重但仍 active 的
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
        """检查 developer .metadata.yaml 中的 insight 引用"""
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
        """生成下一个 INS-NNN ID"""
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
        """保存 insight 到 YAML 文件"""
        self.insights_dir.mkdir(parents=True, exist_ok=True)
        if not insight.fingerprint:
            insight.fingerprint = insight.compute_fingerprint()
        path = self._insight_path(insight.id)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(insight.to_dict(), f, allow_unicode=True, sort_keys=False,
                      default_flow_style=False)

    def _load_insight(self, path: Path) -> Optional[Insight]:
        """从 YAML 文件加载 insight"""
        data = self._load_yaml(path)
        if not data:
            return None
        return Insight.from_dict(data)

    def _ensure_registry_entry(self, insight_id: str) -> None:
        """确保注册表中有该条目"""
        entries, settings = self.get_registry()
        if insight_id not in entries:
            entries[insight_id] = RegistryEntry()
            self._save_registry(entries, settings)

    def _remove_registry_entry(self, insight_id: str) -> None:
        """从注册表中移除条目"""
        entries, settings = self.get_registry()
        if insight_id in entries:
            del entries[insight_id]
            self._save_registry(entries, settings)

    def _save_registry(self, entries: Dict[str, RegistryEntry],
                       settings: Dict[str, Any]) -> None:
        """保存注册表"""
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
        """安全加载 YAML"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def _log_event(self, event_type: str, actor: str, summary: str,
                   payload: Dict[str, Any]) -> None:
        """记录审计事件"""
        if self.event_log:
            self.event_log.append(Event(
                event_type=event_type,
                actor=actor,
                summary=summary,
                payload=payload,
            ))
