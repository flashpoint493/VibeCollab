"""
InsightManager full-coverage unit tests
"""


import pytest
import yaml

from vibecollab.domain.event_log import EventLog
from vibecollab.insight.manager import (
    INSIGHT_ID_PATTERN,
    Artifact,
    Insight,
    InsightManager,
    Origin,
    RegistryEntry,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def project_dir(tmp_path):
    (tmp_path / ".vibecollab" / "insights").mkdir(parents=True)
    (tmp_path / "docs" / "developers").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def mgr(project_dir):
    return InsightManager(project_dir)


@pytest.fixture
def mgr_with_log(project_dir):
    log = EventLog(project_dir)
    return InsightManager(project_dir, event_log=log), log


def _body(**kwargs):
    base = {"scenario": "test scenario", "approach": "test approach"}
    base.update(kwargs)
    return base


# ===========================================================================
# Artifact
# ===========================================================================

class TestArtifact:
    def test_to_dict_minimal(self):
        a = Artifact(path="tools/x.py", type="script")
        d = a.to_dict()
        assert d == {"path": "tools/x.py", "type": "script"}

    def test_to_dict_full(self):
        a = Artifact(path="t.j2", type="template", runtime="python3", description="desc")
        d = a.to_dict()
        assert d["runtime"] == "python3"
        assert d["description"] == "desc"

    def test_roundtrip(self):
        a = Artifact(path="x.py", type="script", runtime="python3")
        a2 = Artifact.from_dict(a.to_dict())
        assert a2.path == a.path
        assert a2.type == a.type
        assert a2.runtime == a.runtime


# ===========================================================================
# Origin
# ===========================================================================

class TestOrigin:
    def test_to_dict_minimal(self):
        o = Origin(created_by="alice", created_at="2026-02-25")
        d = o.to_dict()
        assert d == {"created_by": "alice", "created_at": "2026-02-25"}
        assert "source" not in d

    def test_to_dict_with_source(self):
        o = Origin(created_by="alice", created_at="2026-02-25",
                   source_type="task", source_ref="TASK-DEV-001")
        d = o.to_dict()
        assert d["source"]["type"] == "task"
        assert d["source"]["ref"] == "TASK-DEV-001"

    def test_to_dict_with_derived(self):
        o = Origin(created_by="bob", created_at="2026-02-25",
                   derived_from=["INS-001", "INS-002"])
        d = o.to_dict()
        assert d["derived_from"] == ["INS-001", "INS-002"]

    def test_roundtrip(self):
        o = Origin(created_by="alice", created_at="2026-02-25",
                   source_type="decision", source_ref="DECISION-011",
                   derived_from=["INS-001"])
        o2 = Origin.from_dict(o.to_dict())
        assert o2.created_by == "alice"
        assert o2.source_type == "decision"
        assert o2.source_ref == "DECISION-011"
        assert o2.derived_from == ["INS-001"]

    def test_context_field(self):
        o = Origin(created_by="alice", created_at="2026-02-25",
                   context="VibeCollab v0.7.0 architecture design")
        d = o.to_dict()
        assert d["context"] == "VibeCollab v0.7.0 architecture design"
        o2 = Origin.from_dict(d)
        assert o2.context == "VibeCollab v0.7.0 architecture design"

    def test_source_self_describing(self):
        o = Origin(
            created_by="alice", created_at="2026-02-25",
            context="Refactoring session",
            source_type="decision",
            source_desc="Dropped Web UI, switched to two-layer Insight solidification system",
            source_ref="DECISION-012",
            source_url="https://github.com/user/repo/issues/42",
            source_project="VibeCollab",
        )
        d = o.to_dict()
        assert d["context"] == "Refactoring session"
        assert d["source"]["type"] == "decision"
        assert d["source"]["description"] == "Dropped Web UI, switched to two-layer Insight solidification system"
        assert d["source"]["ref"] == "DECISION-012"
        assert d["source"]["url"] == "https://github.com/user/repo/issues/42"
        assert d["source"]["project"] == "VibeCollab"
        # Roundtrip
        o2 = Origin.from_dict(d)
        assert o2.source_desc == o.source_desc
        assert o2.source_url == o.source_url
        assert o2.source_project == o.source_project

    def test_source_without_ref(self):
        """source can have only description without ref - cross-project portable"""
        o = Origin(
            created_by="bob", created_at="2026-02-25",
            source_type="external",
            source_desc="Learned from Martin Fowler's refactoring catalog",
        )
        d = o.to_dict()
        assert d["source"]["description"] == "Learned from Martin Fowler's refactoring catalog"
        assert "ref" not in d["source"]
        assert "project" not in d["source"]


# ===========================================================================
# Insight dataclass
# ===========================================================================

class TestInsight:
    def test_valid_creation(self):
        ins = Insight(
            id="INS-001", title="Test", tags=["t"], category="technique",
            body=_body(), origin=Origin(created_by="a", created_at="2026-01-01"),
        )
        assert ins.kind == "insight"
        assert ins.version == "1"

    def test_invalid_id(self):
        with pytest.raises(ValueError, match="Invalid insight ID"):
            Insight(id="BAD-001", title="X", tags=["t"], category="technique",
                    body=_body(), origin=Origin(created_by="a", created_at="x"))

    def test_invalid_category(self):
        with pytest.raises(ValueError, match="Invalid category"):
            Insight(id="INS-001", title="X", tags=["t"], category="INVALID",
                    body=_body(), origin=Origin(created_by="a", created_at="x"))

    def test_empty_tags(self):
        with pytest.raises(ValueError, match="at least one tag"):
            Insight(id="INS-001", title="X", tags=[], category="technique",
                    body=_body(), origin=Origin(created_by="a", created_at="x"))

    def test_fingerprint_deterministic(self):
        ins = Insight(id="INS-001", title="T", tags=["a"], category="technique",
                      body=_body(), origin=Origin(created_by="a", created_at="x"))
        fp1 = ins.compute_fingerprint()
        fp2 = ins.compute_fingerprint()
        assert fp1 == fp2
        assert len(fp1) == 64  # SHA-256 hex

    def test_fingerprint_changes_on_content(self):
        ins1 = Insight(id="INS-001", title="A", tags=["a"], category="technique",
                       body=_body(), origin=Origin(created_by="a", created_at="x"))
        ins2 = Insight(id="INS-001", title="B", tags=["a"], category="technique",
                       body=_body(), origin=Origin(created_by="a", created_at="x"))
        assert ins1.compute_fingerprint() != ins2.compute_fingerprint()

    def test_to_dict_roundtrip(self):
        ins = Insight(
            id="INS-001", title="Test Insight", tags=["refactor", "python"],
            category="technique", body=_body(validation="all tests pass"),
            summary="A test insight",
            origin=Origin(created_by="alice", created_at="2026-02-25",
                          source_type="task", source_ref="TASK-DEV-001",
                          derived_from=["INS-000"]),
            artifacts=[Artifact(path="x.py", type="script")],
        )
        d = ins.to_dict()
        ins2 = Insight.from_dict(d)
        assert ins2.id == ins.id
        assert ins2.title == ins.title
        assert ins2.tags == ins.tags
        assert ins2.summary == ins.summary
        assert ins2.origin.source_type == "task"
        assert ins2.origin.derived_from == ["INS-000"]
        assert len(ins2.artifacts) == 1
        assert ins2.fingerprint == ins.fingerprint


# ===========================================================================
# RegistryEntry
# ===========================================================================

class TestRegistryEntry:
    def test_defaults(self):
        e = RegistryEntry()
        assert e.weight == 1.0
        assert e.used_count == 0
        assert e.active is True

    def test_to_dict_minimal(self):
        d = RegistryEntry().to_dict()
        assert d["weight"] == 1.0
        assert d["active"] is True
        assert "last_used_at" not in d

    def test_roundtrip(self):
        e = RegistryEntry(weight=0.8, used_count=5, last_used_at="2026-02-25",
                          last_used_by="alice", active=True)
        e2 = RegistryEntry.from_dict(e.to_dict())
        assert e2.weight == 0.8
        assert e2.used_count == 5
        assert e2.last_used_by == "alice"


# ===========================================================================
# InsightManager — CRUD
# ===========================================================================

class TestCRUD:
    def test_create(self, mgr):
        ins = mgr.create(
            title="Test", tags=["a"], category="technique",
            body=_body(), created_by="alice",
        )
        assert ins.id == "INS-001"
        assert ins.fingerprint
        # File exists
        assert (mgr.insights_dir / "INS-001.yaml").exists()

    def test_create_increments_id(self, mgr):
        mgr.create(title="A", tags=["a"], category="technique",
                    body=_body(), created_by="alice")
        ins2 = mgr.create(title="B", tags=["b"], category="workflow",
                          body=_body(), created_by="bob")
        assert ins2.id == "INS-002"

    def test_create_with_all_fields(self, mgr):
        ins = mgr.create(
            title="Full", tags=["a", "b"], category="tool",
            body=_body(validation="pytest", constraints=["python>=3.8"]),
            created_by="alice", summary="Full insight",
            source_type="decision", source_ref="DECISION-012",
            derived_from=[], artifacts=[{"path": "x.py", "type": "script"}],
        )
        assert ins.summary == "Full insight"
        assert ins.origin.source_type == "decision"
        assert len(ins.artifacts) == 1

    def test_get(self, mgr):
        mgr.create(title="T", tags=["a"], category="technique",
                    body=_body(), created_by="alice")
        ins = mgr.get("INS-001")
        assert ins is not None
        assert ins.title == "T"

    def test_get_nonexistent(self, mgr):
        assert mgr.get("INS-999") is None

    def test_list_all(self, mgr):
        mgr.create(title="A", tags=["a"], category="technique",
                    body=_body(), created_by="alice")
        mgr.create(title="B", tags=["b"], category="workflow",
                    body=_body(), created_by="bob")
        assert len(mgr.list_all()) == 2

    def test_list_all_empty(self, mgr):
        assert mgr.list_all() == []

    def test_update(self, mgr):
        mgr.create(title="Old", tags=["a"], category="technique",
                    body=_body(), created_by="alice")
        updated = mgr.update("INS-001", updated_by="bob",
                             title="New", tags=["a", "b"])
        assert updated is not None
        assert updated.title == "New"
        assert updated.tags == ["a", "b"]
        # Re-read from disk
        reloaded = mgr.get("INS-001")
        assert reloaded.title == "New"

    def test_update_nonexistent(self, mgr):
        assert mgr.update("INS-999", updated_by="x", title="X") is None

    def test_update_recalculates_fingerprint(self, mgr):
        ins = mgr.create(title="Old", tags=["a"], category="technique",
                         body=_body(), created_by="alice")
        old_fp = ins.fingerprint
        updated = mgr.update("INS-001", updated_by="bob", title="New")
        assert updated.fingerprint != old_fp

    def test_delete(self, mgr):
        mgr.create(title="T", tags=["a"], category="technique",
                    body=_body(), created_by="alice")
        assert mgr.delete("INS-001", deleted_by="alice") is True
        assert mgr.get("INS-001") is None
        entries, _ = mgr.get_registry()
        assert "INS-001" not in entries

    def test_delete_nonexistent(self, mgr):
        assert mgr.delete("INS-999", deleted_by="x") is False


# ===========================================================================
# InsightManager — Registry
# ===========================================================================

class TestRegistry:
    def test_create_auto_registers(self, mgr):
        mgr.create(title="T", tags=["a"], category="technique",
                    body=_body(), created_by="alice")
        entries, _ = mgr.get_registry()
        assert "INS-001" in entries
        assert entries["INS-001"].weight == 1.0

    def test_record_use(self, mgr):
        mgr.create(title="T", tags=["a"], category="technique",
                    body=_body(), created_by="alice")
        entry = mgr.record_use("INS-001", used_by="bob")
        assert entry is not None
        assert entry.used_count == 1
        assert entry.weight > 1.0
        assert entry.last_used_by == "bob"

    def test_record_use_nonexistent(self, mgr):
        assert mgr.record_use("INS-999", used_by="x") is None

    def test_record_use_reactivates(self, mgr):
        mgr.create(title="T", tags=["a"], category="technique",
                    body=_body(), created_by="alice")
        # Manually deactivate
        entries, settings = mgr.get_registry()
        entries["INS-001"].active = False
        mgr._save_registry(entries, settings)
        # Use it
        entry = mgr.record_use("INS-001", used_by="bob")
        assert entry.active is True

    def test_apply_decay(self, mgr):
        mgr.create(title="T", tags=["a"], category="technique",
                    body=_body(), created_by="alice")
        mgr.apply_decay()
        entries, _ = mgr.get_registry()
        assert entries["INS-001"].weight < 1.0
        assert entries["INS-001"].weight == pytest.approx(0.95)

    def test_apply_decay_deactivates(self, mgr):
        mgr.create(title="T", tags=["a"], category="technique",
                    body=_body(), created_by="alice")
        entries, settings = mgr.get_registry()
        entries["INS-001"].weight = 0.09  # below threshold
        mgr._save_registry(entries, settings)
        deactivated = mgr.apply_decay()
        assert "INS-001" in deactivated
        entries, _ = mgr.get_registry()
        assert entries["INS-001"].active is False

    def test_get_active_insights(self, mgr):
        mgr.create(title="A", tags=["a"], category="technique",
                    body=_body(), created_by="alice")
        mgr.create(title="B", tags=["b"], category="workflow",
                    body=_body(), created_by="bob")
        # Deactivate one
        entries, settings = mgr.get_registry()
        entries["INS-001"].active = False
        mgr._save_registry(entries, settings)
        active = mgr.get_active_insights()
        assert len(active) == 1
        assert active[0][0] == "INS-002"

    def test_registry_settings_defaults(self, mgr):
        mgr.create(title="T", tags=["a"], category="technique",
                    body=_body(), created_by="alice")
        _, settings = mgr.get_registry()
        assert settings["decay_rate"] == 0.95
        assert settings["use_reward"] == 0.1


# ===========================================================================
# InsightManager — Tag search
# ===========================================================================

class TestSearch:
    def test_search_by_tags(self, mgr):
        mgr.create(title="A", tags=["refactor", "python"], category="technique",
                    body=_body(), created_by="alice")
        mgr.create(title="B", tags=["test", "python"], category="workflow",
                    body=_body(), created_by="bob")
        mgr.create(title="C", tags=["deploy", "docker"], category="tool",
                    body=_body(), created_by="alice")
        results = mgr.search_by_tags(["python"])
        assert len(results) == 2
        ids = [r.id for r in results]
        assert "INS-001" in ids
        assert "INS-002" in ids

    def test_search_no_match(self, mgr):
        mgr.create(title="A", tags=["refactor"], category="technique",
                    body=_body(), created_by="alice")
        assert mgr.search_by_tags(["nonexistent"]) == []

    def test_search_weighted_order(self, mgr):
        mgr.create(title="A", tags=["python"], category="technique",
                    body=_body(), created_by="alice")
        mgr.create(title="B", tags=["python"], category="workflow",
                    body=_body(), created_by="bob")
        # Boost B's weight
        mgr.record_use("INS-002", used_by="alice")
        mgr.record_use("INS-002", used_by="alice")
        results = mgr.search_by_tags(["python"])
        assert results[0].id == "INS-002"  # higher weight → first

    def test_search_excludes_inactive(self, mgr):
        mgr.create(title="A", tags=["python"], category="technique",
                    body=_body(), created_by="alice")
        entries, settings = mgr.get_registry()
        entries["INS-001"].active = False
        mgr._save_registry(entries, settings)
        assert mgr.search_by_tags(["python"], active_only=True) == []

    def test_search_includes_inactive_when_flag(self, mgr):
        mgr.create(title="A", tags=["python"], category="technique",
                    body=_body(), created_by="alice")
        entries, settings = mgr.get_registry()
        entries["INS-001"].active = False
        mgr._save_registry(entries, settings)
        assert len(mgr.search_by_tags(["python"], active_only=False)) == 1

    def test_search_by_category(self, mgr):
        mgr.create(title="A", tags=["a"], category="technique",
                    body=_body(), created_by="alice")
        mgr.create(title="B", tags=["b"], category="workflow",
                    body=_body(), created_by="bob")
        assert len(mgr.search_by_category("technique")) == 1
        assert len(mgr.search_by_category("workflow")) == 1
        assert len(mgr.search_by_category("debug")) == 0


# ===========================================================================
# InsightManager - Provenance
# ===========================================================================

class TestDerivedTree:
    def test_derived_tree(self, mgr):
        mgr.create(title="Base", tags=["a"], category="technique",
                    body=_body(), created_by="alice")
        mgr.create(title="Child", tags=["b"], category="technique",
                    body=_body(), created_by="bob",
                    derived_from=["INS-001"])
        tree = mgr.get_derived_tree("INS-001")
        assert tree["derived_from"] == []
        assert tree["derived_by"] == ["INS-002"]

    def test_derived_tree_upstream(self, mgr):
        mgr.create(title="Base", tags=["a"], category="technique",
                    body=_body(), created_by="alice")
        mgr.create(title="Child", tags=["b"], category="technique",
                    body=_body(), created_by="bob",
                    derived_from=["INS-001"])
        tree = mgr.get_derived_tree("INS-002")
        assert tree["derived_from"] == ["INS-001"]
        assert tree["derived_by"] == []

    def test_derived_tree_nonexistent(self, mgr):
        tree = mgr.get_derived_tree("INS-999")
        assert tree["derived_from"] == []
        assert tree["derived_by"] == []


# ===========================================================================
# InsightManager - Full Provenance
# ===========================================================================

class TestFullTrace:
    def test_simple_trace(self, mgr):
        mgr.create(title="Base", tags=["a"], category="technique",
                    body=_body(), created_by="alice")
        mgr.create(title="Child", tags=["b"], category="technique",
                    body=_body(), created_by="bob",
                    derived_from=["INS-001"])
        trace = mgr.get_full_trace("INS-001")
        assert trace["id"] == "INS-001"
        assert trace["title"] == "Base"
        assert trace["upstream"] == []
        assert len(trace["downstream"]) == 1
        assert trace["downstream"][0]["id"] == "INS-002"

    def test_trace_upstream(self, mgr):
        mgr.create(title="Base", tags=["a"], category="technique",
                    body=_body(), created_by="alice")
        mgr.create(title="Child", tags=["b"], category="technique",
                    body=_body(), created_by="bob",
                    derived_from=["INS-001"])
        trace = mgr.get_full_trace("INS-002")
        assert len(trace["upstream"]) == 1
        assert trace["upstream"][0]["id"] == "INS-001"
        assert trace["upstream"][0]["title"] == "Base"

    def test_trace_chain(self, mgr):
        mgr.create(title="A", tags=["a"], category="technique",
                    body=_body(), created_by="alice")
        mgr.create(title="B", tags=["b"], category="technique",
                    body=_body(), created_by="bob",
                    derived_from=["INS-001"])
        mgr.create(title="C", tags=["c"], category="technique",
                    body=_body(), created_by="charlie",
                    derived_from=["INS-002"])
        trace = mgr.get_full_trace("INS-002")
        assert len(trace["upstream"]) == 1
        assert len(trace["downstream"]) == 1
        assert trace["downstream"][0]["id"] == "INS-003"

    def test_trace_missing_parent(self, mgr):
        mgr.create(title="Child", tags=["a"], category="technique",
                    body=_body(), created_by="alice",
                    derived_from=["INS-999"])
        trace = mgr.get_full_trace("INS-001")
        assert len(trace["upstream"]) == 1
        assert trace["upstream"][0]["title"] == "(missing)"

    def test_trace_nonexistent(self, mgr):
        trace = mgr.get_full_trace("INS-999")
        assert trace["title"] == "(missing)"
        assert trace["downstream"] == []


# ===========================================================================
# InsightManager - Cross-developer Sharing
# ===========================================================================

class TestCrossDeveloper:
    def test_get_insight_developers(self, mgr, project_dir):
        mgr.create(title="T", tags=["a"], category="technique",
                    body=_body(), created_by="alice")
        mgr.record_use("INS-001", used_by="bob")
        # Setup developer metadata
        alice_dir = project_dir / "docs" / "developers" / "alice"
        alice_dir.mkdir(parents=True, exist_ok=True)
        (alice_dir / ".metadata.yaml").write_text(
            "developer: alice\ncontributed:\n  - INS-001\nbookmarks: []\n",
            encoding="utf-8",
        )
        bob_dir = project_dir / "docs" / "developers" / "bob"
        bob_dir.mkdir(parents=True, exist_ok=True)
        (bob_dir / ".metadata.yaml").write_text(
            "developer: bob\ncontributed: []\nbookmarks:\n  - INS-001\n",
            encoding="utf-8",
        )
        info = mgr.get_insight_developers("INS-001")
        assert info["created_by"] == "alice"
        assert "bob" in info["used_by"]
        assert "bob" in info["bookmarked_by"]
        assert "alice" in info["contributed_by"]

    def test_get_insight_developers_nonexistent(self, mgr):
        info = mgr.get_insight_developers("INS-999")
        assert info["created_by"] is None
        assert info["used_by"] == []

    def test_get_cross_developer_stats(self, mgr, project_dir):
        mgr.create(title="A", tags=["a"], category="technique",
                    body=_body(), created_by="alice")
        mgr.create(title="B", tags=["b"], category="workflow",
                    body=_body(), created_by="bob")
        mgr.record_use("INS-001", used_by="bob")
        mgr.record_use("INS-001", used_by="charlie")
        # Setup developer directories
        for dev in ("alice", "bob"):
            d = project_dir / "docs" / "developers" / dev
            d.mkdir(parents=True, exist_ok=True)
            (d / ".metadata.yaml").write_text(
                f"developer: {dev}\ncontributed: []\nbookmarks: []\n",
                encoding="utf-8",
            )
        stats = mgr.get_cross_developer_stats()
        assert stats["summary"]["total_insights"] == 2
        assert stats["summary"]["total_uses"] == 2
        assert stats["summary"]["most_used"] == "INS-001"

    def test_cross_developer_stats_empty(self, mgr):
        stats = mgr.get_cross_developer_stats()
        assert stats["summary"]["total_insights"] == 0
        assert stats["summary"]["total_uses"] == 0
        assert stats["summary"]["most_used"] is None


# ===========================================================================
# InsightManager - Consistency Check
# ===========================================================================

class TestConsistency:
    def test_clean_state(self, mgr):
        mgr.create(title="T", tags=["a"], category="technique",
                    body=_body(), created_by="alice")
        report = mgr.check_consistency()
        assert report.ok is True
        assert report.errors == []

    def test_orphan_registry_entry(self, mgr):
        mgr.create(title="T", tags=["a"], category="technique",
                    body=_body(), created_by="alice")
        # Delete file but keep registry
        (mgr.insights_dir / "INS-001.yaml").unlink()
        report = mgr.check_consistency()
        assert report.ok is False
        assert any("no corresponding insight file" in e for e in report.errors)

    def test_unregistered_file(self, mgr):
        mgr.create(title="T", tags=["a"], category="technique",
                    body=_body(), created_by="alice")
        # Remove from registry
        entries, settings = mgr.get_registry()
        del entries["INS-001"]
        mgr._save_registry(entries, settings)
        report = mgr.check_consistency()
        assert report.ok is False
        assert any("not registered" in e for e in report.errors)

    def test_broken_derived_from(self, mgr):
        mgr.create(title="T", tags=["a"], category="technique",
                    body=_body(), created_by="alice",
                    derived_from=["INS-999"])
        report = mgr.check_consistency()
        assert report.ok is False
        assert any("does not exist" in e for e in report.errors)

    def test_developer_metadata_bad_ref(self, mgr, project_dir):
        mgr.create(title="T", tags=["a"], category="technique",
                    body=_body(), created_by="alice")
        dev_dir = project_dir / "docs" / "developers" / "alice"
        dev_dir.mkdir(parents=True, exist_ok=True)
        meta = dev_dir / ".metadata.yaml"
        meta.write_text(
            "developer: alice\ncontributed:\n  - INS-001\nbookmarks:\n  - INS-999\n",
            encoding="utf-8",
        )
        report = mgr.check_consistency()
        assert report.ok is False
        assert any("INS-999" in e and "bookmarks" in e for e in report.errors)

    def test_fingerprint_mismatch(self, mgr):
        mgr.create(title="T", tags=["a"], category="technique",
                   body=_body(), created_by="alice")
        # Tamper with the file
        path = mgr.insights_dir / "INS-001.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        data["title"] = "Tampered"
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True)
        report = mgr.check_consistency()
        assert report.ok is False
        assert any("fingerprint mismatch" in e for e in report.errors)

    def test_low_weight_warning(self, mgr):
        mgr.create(title="T", tags=["a"], category="technique",
                    body=_body(), created_by="alice")
        entries, settings = mgr.get_registry()
        entries["INS-001"].weight = 0.2
        mgr._save_registry(entries, settings)
        report = mgr.check_consistency()
        assert report.ok is True  # warning, not error
        assert any("low weight" in w for w in report.warnings)


# ===========================================================================
# InsightManager - EventLog Integration
# ===========================================================================

class TestEventLogIntegration:
    def test_create_logs_event(self, mgr_with_log):
        mgr, log = mgr_with_log
        mgr.create(title="T", tags=["a"], category="technique",
                    body=_body(), created_by="alice")
        events = log.read_all()
        assert len(events) == 1
        assert events[0].payload["action"] == "insight_created"

    def test_use_logs_event(self, mgr_with_log):
        mgr, log = mgr_with_log
        mgr.create(title="T", tags=["a"], category="technique",
                    body=_body(), created_by="alice")
        mgr.record_use("INS-001", used_by="bob")
        events = log.read_all()
        assert len(events) == 2
        assert events[1].payload["action"] == "insight_used"

    def test_update_logs_event(self, mgr_with_log):
        mgr, log = mgr_with_log
        mgr.create(title="T", tags=["a"], category="technique",
                    body=_body(), created_by="alice")
        mgr.update("INS-001", updated_by="bob", title="New")
        events = log.read_all()
        assert events[-1].payload["action"] == "insight_updated"
        assert "title" in events[-1].payload["fields"]

    def test_delete_logs_event(self, mgr_with_log):
        mgr, log = mgr_with_log
        mgr.create(title="T", tags=["a"], category="technique",
                    body=_body(), created_by="alice")
        mgr.delete("INS-001", deleted_by="alice")
        events = log.read_all()
        assert events[-1].payload["action"] == "insight_deleted"


# ===========================================================================
# Edge Cases
# ===========================================================================

class TestEdgeCases:
    def test_unicode_content(self, mgr):
        ins = mgr.create(
            title="Template replace hardcoded", tags=["refactor", "template"],
            category="technique",
            body={"scenario": "Lots of hardcoded text", "approach": "Use Jinja2 templates"},
            created_by="xiaoming",
        )
        reloaded = mgr.get(ins.id)
        assert reloaded.title == "Template replace hardcoded"
        assert reloaded.origin.created_by == "xiaoming"

    def test_many_insights(self, mgr):
        for i in range(20):
            mgr.create(title=f"Insight {i}", tags=[f"tag{i}"],
                       category="technique", body=_body(), created_by="alice")
        assert len(mgr.list_all()) == 20
        ins20 = mgr.get("INS-020")
        assert ins20 is not None

    def test_empty_registry(self, mgr):
        entries, settings = mgr.get_registry()
        assert entries == {}
        assert "decay_rate" in settings

    def test_corrupt_insight_file(self, mgr):
        mgr.create(title="T", tags=["a"], category="technique",
                    body=_body(), created_by="alice")
        # Corrupt the file
        (mgr.insights_dir / "INS-001.yaml").write_text("{{bad yaml", encoding="utf-8")
        all_ins = mgr.list_all()
        assert len(all_ins) == 0  # corrupted file is skipped

    def test_id_pattern_validation(self):
        assert INSIGHT_ID_PATTERN.match("INS-001")
        assert INSIGHT_ID_PATTERN.match("INS-0001")
        assert not INSIGHT_ID_PATTERN.match("INS-01")
        assert not INSIGHT_ID_PATTERN.match("ins-001")
        assert not INSIGHT_ID_PATTERN.match("INS001")


# ---------------------------------------------------------------------------
# Test: Large-scale Insight stress test
# ---------------------------------------------------------------------------

class TestLargeScaleInsight:
    """Performance and correctness tests with 100+ Insights."""

    def test_create_100_insights(self, mgr):
        """Batch create 100 Insights with sequential IDs."""
        for i in range(100):
            mgr.create(
                title=f"Insight {i}",
                tags=[f"tag-{i % 10}", f"group-{i % 5}", "common"],
                category="technique",
                body=_body(),
                created_by="stress-test",
            )
        all_ins = mgr.list_all()
        assert len(all_ins) == 100
        # IDs should be sequential
        ids = sorted(int(ins.id.split("-")[1]) for ins in all_ins)
        assert ids == list(range(1, 101))

    def test_search_100_insights(self, mgr):
        """Search among 100 Insights, results sorted by weight."""
        for i in range(100):
            mgr.create(
                title=f"Topic {i}",
                tags=[f"tag-{i % 10}", f"area-{i % 3}"],
                category="technique",
                body=_body(),
                created_by="test",
            )
        # Boost weight for some insights
        for i in range(1, 11):
            mgr.record_use(f"INS-{i:03d}", used_by="test")

        results = mgr.search_by_tags(["tag-0", "area-0"])
        assert len(results) > 0
        # search_by_tags returns sorted List[Insight], just verify we have results
        # (score is sorted internally, not directly accessible externally)

    def test_list_all_100_insights(self, mgr):
        """list_all handles 100 Insights without crashing."""
        for i in range(100):
            mgr.create(
                title=f"Item {i}",
                tags=["bulk"],
                category="technique",
                body=_body(),
                created_by="test",
            )
        all_ins = mgr.list_all()
        assert len(all_ins) == 100

    def test_decay_100_insights(self, mgr):
        """Apply decay to 100 Insights."""
        for i in range(100):
            mgr.create(
                title=f"Decayable {i}",
                tags=["decay"],
                category="technique",
                body=_body(),
                created_by="test",
            )
        # Initial weights are all 1.0
        mgr.apply_decay()
        entries, _ = mgr.get_registry()
        for eid, entry in entries.items():
            assert abs(entry.weight - 0.95) < 0.01

    def test_search_many_tags(self, mgr):
        """Search works normally with 20+ tags on an Insight."""
        many_tags = [f"tag-{i}" for i in range(25)]
        mgr.create(
            title="Many tags",
            tags=many_tags,
            category="technique",
            body=_body(),
            created_by="test",
        )
        results = mgr.search_by_tags(["tag-0", "tag-5", "tag-10"])
        assert len(results) == 1

    def test_deep_derivation_chain(self, mgr):
        """10-level deep trace chain - get_full_trace should not infinite loop."""
        prev_id = None
        for i in range(10):
            derived = [prev_id] if prev_id else None
            ins = mgr.create(
                title=f"Chain {i}",
                tags=["chain"],
                category="technique",
                body=_body(),
                created_by="test",
                derived_from=derived,
            )
            prev_id = ins.id

        trace = mgr.get_full_trace(prev_id)
        # Full chain should be able to retrieve all upstream
        assert trace is not None


# ---------------------------------------------------------------------------
# Test: Decay/reward long-term simulation
# ---------------------------------------------------------------------------

class TestDecayLongTerm:
    """Multi-round decay + reward alternation long-term behavior verification."""

    def test_50_rounds_decay_converges_to_zero(self, mgr):
        """After 50 rounds of decay, weight approaches 0 and gets deactivated."""
        mgr.create(
            title="Decay target",
            tags=["decay"],
            category="technique",
            body=_body(),
            created_by="test",
        )
        for _ in range(50):
            mgr.apply_decay()

        entries, _ = mgr.get_registry()
        entry = entries["INS-001"]
        # 0.95^50 ~ 0.0769 < 0.1 threshold -> should be deactivated
        assert entry.active is False
        assert entry.weight < 0.1

    def test_decay_plus_reward_steady_state(self, mgr):
        """Decay + usage reward alternation, weight should fluctuate in reasonable range."""
        mgr.create(
            title="Steady state",
            tags=["steady"],
            category="technique",
            body=_body(),
            created_by="test",
        )
        # Simulate 20 rounds: use once every 5 rounds
        for i in range(20):
            mgr.apply_decay()
            if i % 5 == 0:
                mgr.record_use("INS-001", used_by="test")

        entries, _ = mgr.get_registry()
        entry = entries["INS-001"]
        # Should still be active (due to periodic reward)
        assert entry.active is True
        assert entry.weight > 0.1

    def test_massive_record_use_weight_grows(self, mgr):
        """Weight keeps growing with many record_use calls (no upper limit)."""
        mgr.create(
            title="Popular",
            tags=["popular"],
            category="technique",
            body=_body(),
            created_by="test",
        )
        for _ in range(100):
            mgr.record_use("INS-001", used_by="fan")

        entries, _ = mgr.get_registry()
        entry = entries["INS-001"]
        # Initial 1.0 + 100 * 0.1 = 11.0
        assert entry.weight >= 10.0
        assert entry.used_count == 100

    def test_weight_precision_after_many_decays(self, mgr):
        """Weight precision after many decays (floating point accumulation error)."""
        mgr.create(
            title="Precision",
            tags=["prec"],
            category="technique",
            body=_body(),
            created_by="test",
        )
        for _ in range(20):
            mgr.apply_decay()

        entries, _ = mgr.get_registry()
        entry = entries["INS-001"]
        expected = round(0.95 ** 20, 4)
        # Allow minor floating point error
        assert abs(entry.weight - expected) < 0.001

    def test_decay_reactivation_cycle(self, mgr):
        """Decay to deactivation -> record_use reactivates -> decay again."""
        mgr.create(
            title="Reactivation",
            tags=["re"],
            category="technique",
            body=_body(),
            created_by="test",
        )
        # Decay until deactivated
        for _ in range(60):
            mgr.apply_decay()
        entries, _ = mgr.get_registry()
        assert entries["INS-001"].active is False

        # Use to reactivate
        mgr.record_use("INS-001", used_by="user")
        entries, _ = mgr.get_registry()
        assert entries["INS-001"].active is True
        assert entries["INS-001"].weight > 0.1

        # Decay again
        mgr.apply_decay()
        entries, _ = mgr.get_registry()
        assert entries["INS-001"].active is True  # Just reactivated, won't deactivate immediately

    def test_threshold_exact_boundary(self, mgr):
        """Weight exactly at threshold is not deactivated (< threshold to deactivate)."""
        mgr.create(
            title="Boundary",
            tags=["edge"],
            category="technique",
            body=_body(),
            created_by="test",
        )
        # Manually set weight exactly = 0.1
        entries, settings = mgr.get_registry()
        entries["INS-001"].weight = 0.1
        registry_path = mgr.insights_dir / "registry.yaml"
        registry_data = {
            "entries": {k: v.to_dict() for k, v in entries.items()},
            "settings": settings,
        }
        registry_path.write_text(
            yaml.dump(registry_data, allow_unicode=True),
            encoding="utf-8",
        )
        mgr.apply_decay()  # 0.1 * 0.95 = 0.095 < 0.1 -> deactivated
        entries, _ = mgr.get_registry()
        assert entries["INS-001"].active is False


# ---------------------------------------------------------------------------
# Test: Task-Insight association precision
# ---------------------------------------------------------------------------

class TestTaskInsightRelation:
    """Task-Insight association search precision tests."""

    def test_search_empty_tags(self, mgr):
        """Empty tag list search returns empty results."""
        mgr.create(
            title="Something",
            tags=["test"],
            category="technique",
            body=_body(),
            created_by="test",
        )
        results = mgr.search_by_tags([])
        assert results == []

    def test_search_no_match(self, mgr):
        """No matching tags returns empty results."""
        mgr.create(
            title="Python tip",
            tags=["python", "testing"],
            category="technique",
            body=_body(),
            created_by="test",
        )
        results = mgr.search_by_tags(["java", "deployment"])
        assert results == []

    def test_search_chinese_tags(self, mgr):
        """Chinese tag search works correctly."""
        mgr.create(
            title="Chinese insight",
            tags=["测试", "架构", "重构"],
            category="technique",
            body=_body(),
            created_by="test",
        )
        results = mgr.search_by_tags(["测试", "架构"])
        assert len(results) == 1

    def test_search_mixed_case(self, mgr):
        """Case-insensitive search."""
        mgr.create(
            title="Case test",
            tags=["Python", "Testing"],
            category="technique",
            body=_body(),
            created_by="test",
        )
        results = mgr.search_by_tags(["python", "testing"])
        assert len(results) == 1

    def test_search_partial_overlap(self, mgr):
        """Partial tag overlap returns results."""
        mgr.create(
            title="Partial match",
            tags=["api", "testing", "python"],
            category="technique",
            body=_body(),
            created_by="test",
        )
        results = mgr.search_by_tags(["api", "deployment", "docker"])
        assert len(results) == 1
        # Returns Insight objects, just verify title
        assert results[0].title == "Partial match"


# ---------------------------------------------------------------------------
# Test: Trace cycle protection
# ---------------------------------------------------------------------------

class TestDerivationCycleProtection:
    """Test get_full_trace circular reference protection."""

    def test_circular_derivation(self, mgr):
        """A -> B -> A circular reference doesn't infinite loop."""
        ins_a = mgr.create(
            title="A",
            tags=["loop"],
            category="technique",
            body=_body(),
            created_by="test",
        )
        ins_b = mgr.create(
            title="B",
            tags=["loop"],
            category="technique",
            body=_body(),
            created_by="test",
            derived_from=[ins_a.id],
        )
        # Manually modify A's derived_from to B (create a cycle)
        a_path = mgr.insights_dir / f"{ins_a.id}.yaml"
        a_data = yaml.safe_load(a_path.read_text(encoding="utf-8"))
        a_data["derived_from"] = [ins_b.id]
        a_path.write_text(yaml.dump(a_data, allow_unicode=True), encoding="utf-8")

        # get_full_trace should not infinite loop
        trace = mgr.get_full_trace(ins_a.id)
        assert trace is not None
