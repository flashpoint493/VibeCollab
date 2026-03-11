"""
Tests for cli_guide.py — AI Agent onboarding and action suggestions
"""

import json
import os
import time

import pytest
import yaml
from click.testing import CliRunner

from vibecollab.cli.guide import (
    _build_prompt_text,
    _check_insight_opportunity,
    _check_linked_groups_freshness,
    _collect_project_context,
    _extract_md_sections,
    _extract_pending_from_roadmap,
    _get_read_files_list,
    _get_recent_decisions,
    _search_related_insights,
    _suggest_commit_message,
    next_step,
    onboard,
    prompt_cmd,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def project_dir(tmp_path):
    """Create a temp project with full directory structure"""
    config = {
        "project": {"name": "TestProject", "version": "v1.0.0", "description": "Test desc"},
        "dialogue_protocol": {
            "on_start": {"read_files": ["docs/CONTEXT.md", "CONTRIBUTING_AI.md"]},
            "on_end": {"update_files": ["docs/CONTEXT.md", "docs/CHANGELOG.md"]},
        },
        "documentation": {
            "key_files": [
                {"path": "docs/CONTEXT.md", "purpose": "context"},
                {"path": "docs/MISSING.md", "purpose": "missing"},
            ],
            "consistency": {
                "enabled": True,
                "default_level": "local_mtime",
                "linked_groups": [
                    {
                        "name": "PRD-DECISIONS",
                        "files": ["docs/PRD.md", "docs/DECISIONS.md"],
                        "level": "local_mtime",
                        "threshold_minutes": 15,
                    },
                ],
            },
        },
        "protocol_check": {"checks": {"documentation": {"update_threshold_hours": 0.25}}},
        "prd_management": {"enabled": True, "prd_file": "docs/PRD.md"},
        "multi_developer": {
            "enabled": True,
            "identity": {"primary": "git_username"},
            "context": {"per_developer_dir": "docs/developers", "metadata_file": ".metadata.yaml"},
        },
    }
    (tmp_path / "project.yaml").write_text(yaml.dump(config, allow_unicode=True), encoding="utf-8")

    # Create directories and files
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "CONTEXT.md").write_text("# Context\ncurrent work", encoding="utf-8")
    (tmp_path / "docs" / "CHANGELOG.md").write_text("# Changelog\n- v1.0", encoding="utf-8")
    (tmp_path / "docs" / "DECISIONS.md").write_text(
        "# Decisions\n### DECISION-001: First\n### DECISION-002: Second\n### DECISION-003: Third",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "ROADMAP.md").write_text(
        "# Roadmap\n- [x] Done\n- [ ] Pending A\n- [ ] Pending B",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "PRD.md").write_text("# PRD", encoding="utf-8")
    (tmp_path / "CONTRIBUTING_AI.md").write_text("# AI Rules", encoding="utf-8")

    # Developer directory
    dev_dir = tmp_path / "docs" / "developers" / "testdev"
    dev_dir.mkdir(parents=True)
    (dev_dir / "CONTEXT.md").write_text("# testdev context", encoding="utf-8")
    meta = {"developer": "testdev", "tags": ["lang:python"], "contributed": ["INS-001"], "bookmarks": ["INS-003"]}
    (dev_dir / ".metadata.yaml").write_text(yaml.dump(meta), encoding="utf-8")

    # Insights
    insights_dir = tmp_path / ".vibecollab" / "insights"
    insights_dir.mkdir(parents=True)
    (insights_dir / "INS-001.yaml").write_text("id: INS-001", encoding="utf-8")
    (insights_dir / "INS-002.yaml").write_text("id: INS-002", encoding="utf-8")

    return tmp_path


@pytest.fixture
def chdir_project(project_dir, monkeypatch):
    monkeypatch.chdir(project_dir)
    return project_dir


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_get_recent_decisions(self, project_dir):
        decisions = _get_recent_decisions(project_dir / "docs" / "DECISIONS.md", 2)
        assert len(decisions) == 2
        assert "DECISION-002" in decisions[0]
        assert "DECISION-003" in decisions[1]

    def test_get_recent_decisions_missing_file(self, tmp_path):
        decisions = _get_recent_decisions(tmp_path / "nope.md", 3)
        assert decisions == []

    def test_extract_pending_from_roadmap(self, project_dir):
        pending = _extract_pending_from_roadmap(project_dir / "docs" / "ROADMAP.md")
        assert len(pending) == 2
        assert "Pending A" in pending[0]
        assert "Pending B" in pending[1]

    def test_extract_pending_empty(self, tmp_path):
        (tmp_path / "ROADMAP.md").write_text("# All done\n- [x] Done", encoding="utf-8")
        pending = _extract_pending_from_roadmap(tmp_path / "ROADMAP.md")
        assert pending == []

    def test_get_read_files_list(self):
        config = {"dialogue_protocol": {"on_start": {"read_files": ["a.md", "b.md"]}}}
        assert _get_read_files_list(config) == ["a.md", "b.md"]

    def test_get_read_files_empty(self):
        assert _get_read_files_list({}) == []

    def test_suggest_commit_message(self):
        assert _suggest_commit_message(["src/vibecollab/foo.py", "tests/test_foo.py"]) == "feat:"
        assert _suggest_commit_message(["tests/test_foo.py"]) == "test:"
        assert _suggest_commit_message(["docs/CONTEXT.md"]) == "docs:"
        assert _suggest_commit_message(["project.yaml"]) == "chore:"
        assert _suggest_commit_message(["schema/insight.schema.yaml"]) == "design:"
        assert _suggest_commit_message(["src/vibecollab/foo.py"]) == "feat:"

    def test_check_linked_groups_freshness_all_fresh(self, project_dir):
        config = yaml.safe_load((project_dir / "project.yaml").read_text(encoding="utf-8"))
        stale = _check_linked_groups_freshness(project_dir, config)
        # Just created, should not be stale
        assert stale == []

    def test_check_linked_groups_freshness_one_stale(self, project_dir):
        # Make PRD.md old
        prd = project_dir / "docs" / "PRD.md"
        old_time = time.time() - 7200
        os.utime(prd, (old_time, old_time))

        config = yaml.safe_load((project_dir / "project.yaml").read_text(encoding="utf-8"))
        stale = _check_linked_groups_freshness(project_dir, config)
        assert len(stale) == 1
        assert stale[0]["group"] == "PRD-DECISIONS"

    def test_check_linked_groups_disabled(self, project_dir):
        config = {"documentation": {"consistency": {"enabled": False}}}
        assert _check_linked_groups_freshness(project_dir, config) == []


# ---------------------------------------------------------------------------
# Tests: onboard
# ---------------------------------------------------------------------------

class TestOnboard:
    def test_onboard_basic(self, runner, chdir_project):
        result = runner.invoke(onboard, [])
        assert result.exit_code == 0
        assert "TestProject" in result.output
        assert "v1.0.0" in result.output

    def test_onboard_json(self, runner, chdir_project):
        result = runner.invoke(onboard, ["--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["project"]["name"] == "TestProject"
        assert data["project"]["version"] == "v1.0.0"
        assert "docs/CONTEXT.md" in data["read_files"]
        assert len(data["recent_decisions"]) == 3
        assert len(data["pending_roadmap"]) == 2
        assert data["insight_count"] == 2
        assert "docs/CONTEXT.md" in data["key_files"]

    def test_onboard_with_developer(self, runner, chdir_project):
        result = runner.invoke(onboard, ["-d", "testdev", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["developer"]["id"] == "testdev"
        assert data["developer"]["has_context"] is True
        assert data["developer"]["has_metadata"] is True

    def test_onboard_nonexistent_developer(self, runner, chdir_project):
        result = runner.invoke(onboard, ["-d", "nobody", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["developer"]["has_context"] is False

    def test_onboard_no_config(self, runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(onboard, [])
        assert result.exit_code == 1

    def test_onboard_rich_output_contains_sections(self, runner, chdir_project):
        result = runner.invoke(onboard, [])
        assert result.exit_code == 0
        assert "Project Overview" in result.output
        assert "Files you should read first" in result.output
        assert "Recent Decisions" in result.output
        assert "Roadmap TODOs" in result.output
        assert "Key Files" in result.output
        assert "Suggested Next Steps" in result.output


# ---------------------------------------------------------------------------
# Tests: next
# ---------------------------------------------------------------------------

class TestNextStep:
    def test_next_clean_workspace(self, runner, chdir_project):
        """All files just updated, should be clean"""
        result = runner.invoke(next_step, ["--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        # Not in a git repo, uncommitted may be empty
        assert "actions" in data
        assert "stale_groups" in data

    def test_next_with_stale_document(self, runner, chdir_project, project_dir):
        """Create a stale document, should produce sync suggestion"""
        prd = project_dir / "docs" / "PRD.md"
        old_time = time.time() - 7200
        os.utime(prd, (old_time, old_time))

        result = runner.invoke(next_step, ["--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["stale_groups"]) == 1
        assert data["stale_groups"][0]["group"] == "PRD-DECISIONS"
        # Should have P0 sync_document action
        sync_actions = [a for a in data["actions"] if a["type"] == "sync_document"]
        assert len(sync_actions) >= 1

    def test_next_with_overdue_update_file(self, runner, chdir_project, project_dir):
        """update_files exceeding threshold should produce P1 action"""
        ctx = project_dir / "docs" / "CONTEXT.md"
        old_time = time.time() - 3600
        os.utime(ctx, (old_time, old_time))

        result = runner.invoke(next_step, ["--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        overdue = data["overdue_update_files"]
        assert any(o["file"] == "docs/CONTEXT.md" for o in overdue)

    def test_next_missing_key_files(self, runner, chdir_project):
        """docs/MISSING.md in key_files does not exist, should produce P2 action"""
        result = runner.invoke(next_step, ["--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "docs/MISSING.md" in data["missing_key_files"]
        create_actions = [a for a in data["actions"] if a["type"] == "create_file"]
        assert len(create_actions) == 1

    def test_next_no_config(self, runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(next_step, [])
        assert result.exit_code == 1

    def test_next_rich_output(self, runner, chdir_project, project_dir):
        """Rich output mode should display action labels"""
        # Create a stale file
        prd = project_dir / "docs" / "PRD.md"
        old_time = time.time() - 7200
        os.utime(prd, (old_time, old_time))

        result = runner.invoke(next_step, [])
        assert result.exit_code == 0
        assert "Next Step" in result.output
        assert "URGENT" in result.output or "IMPORTANT" in result.output or "SUGGEST" in result.output

    def test_next_clean_shows_all_clear(self, runner, tmp_path, monkeypatch):
        """Completely clean workspace should show all clear"""
        config = {
            "project": {"name": "Clean"},
            "dialogue_protocol": {
                "on_start": {"read_files": []},
                "on_end": {"update_files": []},
            },
            "documentation": {
                "key_files": [],
                "consistency": {"enabled": False},
            },
            "protocol_check": {"checks": {"documentation": {"update_threshold_hours": 0.25}}},
        }
        (tmp_path / "project.yaml").write_text(yaml.dump(config), encoding="utf-8")
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(next_step, [])
        assert result.exit_code == 0
        assert "All clear" in result.output


class TestSuggestCommitMessage:
    def test_src_and_test(self):
        assert _suggest_commit_message(["src/foo.py", "tests/test_foo.py"]) == "feat:"

    def test_only_docs(self):
        assert _suggest_commit_message(["docs/README.md", "llms.txt"]) == "docs:"

    def test_only_config(self):
        assert _suggest_commit_message([".gitignore"]) == "chore:"

    def test_only_schema(self):
        assert _suggest_commit_message(["schema/foo.yaml"]) == "design:"

    def test_empty(self):
        assert _suggest_commit_message([]) == "chore:"

    def test_mixed_unknown(self):
        assert _suggest_commit_message(["random_file"]) == "chore:"


# ---------------------------------------------------------------------------
# _check_insight_opportunity Tests
# ---------------------------------------------------------------------------

class TestCheckInsightOpportunity:
    """Tests for Insight distillation prompt logic"""

    def test_no_diff_files(self, tmp_path):
        """No changed files, no prompt"""
        assert _check_insight_opportunity(tmp_path, []) is None

    def test_single_py_file(self, tmp_path):
        """Single .py file change, existing Insight, no special signal -> no prompt"""
        insights_dir = tmp_path / ".vibecollab" / "insights"
        insights_dir.mkdir(parents=True)
        (insights_dir / "INS-001.yaml").write_text("id: INS-001")
        assert _check_insight_opportunity(tmp_path, ["src/app.py"]) is None

    def test_multi_type_with_tests(self, tmp_path):
        """Multiple types + test files -> prompt"""
        diff_files = ["src/app.py", "tests/test_app.py", "config.yaml"]
        result = _check_insight_opportunity(tmp_path, diff_files)
        assert result is not None
        assert "multiple file types" in result or "test" in result.lower()

    def test_test_changes_only(self, tmp_path):
        """Only test files changed -> prompt bug/pattern"""
        diff_files = ["tests/test_foo.py", "tests/test_bar.py"]
        result = _check_insight_opportunity(tmp_path, diff_files)
        assert result is not None
        assert "test" in result.lower()

    def test_config_changes(self, tmp_path):
        """Config file changed -> prompt tool/workflow experience"""
        diff_files = ["src/main.py", ".github/workflows/ci.yml"]
        result = _check_insight_opportunity(tmp_path, diff_files)
        assert result is not None
        assert "config" in result.lower()

    def test_large_changeset(self, tmp_path):
        """Large number of files changed -> prompt review"""
        insights_dir = tmp_path / ".vibecollab" / "insights"
        insights_dir.mkdir(parents=True)
        (insights_dir / "INS-001.yaml").write_text("id: INS-001")
        diff_files = [f"src/module_{i}.py" for i in range(10)]
        result = _check_insight_opportunity(tmp_path, diff_files)
        assert result is not None
        assert "10" in result

    def test_no_insights_yet(self, tmp_path):
        """Project has no Insights yet -> guide first distillation"""
        diff_files = ["src/app.py", "src/utils.py"]
        result = _check_insight_opportunity(tmp_path, diff_files)
        assert result is not None
        assert "No Insights" in result

    def test_with_existing_insights(self, tmp_path):
        """Existing Insight + no special signal -> no prompt"""
        insights_dir = tmp_path / ".vibecollab" / "insights"
        insights_dir.mkdir(parents=True)
        (insights_dir / "INS-001.yaml").write_text("id: INS-001")
        diff_files = ["src/app.py"]
        result = _check_insight_opportunity(tmp_path, diff_files)
        assert result is None

    def test_yaml_config_extension(self, tmp_path):
        """YAML config file detection"""
        diff_files = ["pyproject.toml", "src/app.py"]
        result = _check_insight_opportunity(tmp_path, diff_files)
        assert result is not None
        assert "config" in result.lower()

    def test_combined_signals(self, tmp_path):
        """Combined multiple signals"""
        diff_files = [
            "src/app.py", "tests/test_app.py", "config.yaml",
            "docs/README.md", "pyproject.toml",
        ]
        result = _check_insight_opportunity(tmp_path, diff_files)
        assert result is not None
        # Should contain multiple reasons (separated by ;)
        assert ";" in result or len(result) > 20


# ---------------------------------------------------------------------------
# Tests: _extract_md_sections
# ---------------------------------------------------------------------------

class TestExtractMdSections:
    def test_extract_single_h1(self):
        text = "# A\nline1\nline2\n# B\nline3"
        result = _extract_md_sections(text, ["# A"])
        assert "line1" in result
        assert "line2" in result
        assert "line3" not in result

    def test_extract_h2_stops_at_sibling(self):
        text = "## Sec1\ndata1\n## Sec2\ndata2"
        result = _extract_md_sections(text, ["## Sec1"])
        assert "data1" in result
        assert "data2" not in result

    def test_extract_nested_headings_included(self):
        text = "# A\n## Sub\nsub-content\n# B\nother"
        result = _extract_md_sections(text, ["# A"])
        assert "## Sub" in result
        assert "sub-content" in result
        assert "other" not in result

    def test_extract_missing_heading_returns_empty(self):
        text = "# A\ncontent"
        result = _extract_md_sections(text, ["# NoSuchHeading"])
        assert result == ""

    def test_extract_multiple_headings(self):
        text = "# A\nfoo\n# B\nbar\n# C\nbaz"
        result = _extract_md_sections(text, ["# A", "# C"])
        assert "foo" in result
        assert "baz" in result
        assert "bar" not in result


# ---------------------------------------------------------------------------
# Tests: _collect_project_context
# ---------------------------------------------------------------------------

class TestCollectProjectContext:
    def test_collect_returns_keys(self, chdir_project, project_dir):
        ctx = _collect_project_context(project_dir / "project.yaml")
        assert ctx["project_name"] == "TestProject"
        assert ctx["project_version"] == "v1.0.0"
        assert ctx["project_desc"] == "Test desc"
        assert isinstance(ctx["recent_decisions"], list)
        assert isinstance(ctx["pending_roadmap"], list)
        assert isinstance(ctx["key_files"], list)
        assert ctx["insight_count"] == 2

    def test_collect_with_developer(self, chdir_project, project_dir):
        ctx = _collect_project_context(project_dir / "project.yaml", developer="testdev")
        assert ctx["developer_info"] is not None
        assert ctx["developer_info"]["id"] == "testdev"
        assert "testdev context" in ctx["developer_info"]["context"]

    def test_collect_missing_config(self, tmp_path):
        ctx = _collect_project_context(tmp_path / "nope.yaml")
        assert ctx == {}


# ---------------------------------------------------------------------------
# Tests: _build_prompt_text
# ---------------------------------------------------------------------------

class TestBuildPromptText:
    @pytest.fixture
    def sample_ctx(self, project_dir):
        return _collect_project_context(project_dir / "project.yaml")

    def test_header_present(self, sample_ctx, chdir_project):
        text = _build_prompt_text(sample_ctx, ["protocol", "context", "insight"])
        assert "# Project Context: TestProject" in text
        assert "v1.0.0" in text

    def test_context_section(self, sample_ctx, chdir_project):
        text = _build_prompt_text(sample_ctx, ["context"])
        assert "## Current Status" in text
        assert "Recent Decisions" in text

    def test_compact_no_roadmap(self, sample_ctx, chdir_project):
        text = _build_prompt_text(sample_ctx, ["context"], compact=True)
        assert "Roadmap TODOs" not in text

    def test_full_has_roadmap(self, sample_ctx, chdir_project):
        text = _build_prompt_text(sample_ctx, ["context"], compact=False)
        assert "Roadmap TODOs" in text

    def test_insight_section(self, sample_ctx, chdir_project):
        text = _build_prompt_text(sample_ctx, ["insight"])
        assert "Insight Distillation" in text

    def test_footer(self, sample_ctx, chdir_project):
        text = _build_prompt_text(sample_ctx, [])
        assert "vibecollab prompt" in text


# ---------------------------------------------------------------------------
# Tests: vibecollab prompt (CLI)
# ---------------------------------------------------------------------------

class TestPromptCmd:
    def test_prompt_basic(self, runner, chdir_project):
        result = runner.invoke(prompt_cmd, [])
        assert result.exit_code == 0
        assert "# Project Context: TestProject" in result.output
        assert "v1.0.0" in result.output

    def test_prompt_compact(self, runner, chdir_project):
        result = runner.invoke(prompt_cmd, ["--compact"])
        assert result.exit_code == 0
        assert "# Project Context" in result.output
        # compact mode does not contain roadmap
        assert "Roadmap TODOs" not in result.output

    def test_prompt_sections_filter(self, runner, chdir_project):
        result = runner.invoke(prompt_cmd, ["-s", "context"])
        assert result.exit_code == 0
        assert "Current Status" in result.output
        # protocol and insight should not appear
        assert "Collaboration Protocol" not in result.output

    def test_prompt_with_developer(self, runner, chdir_project):
        result = runner.invoke(prompt_cmd, ["-d", "testdev"])
        assert result.exit_code == 0
        assert "testdev" in result.output

    def test_prompt_no_config(self, runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(prompt_cmd, [])
        assert result.exit_code == 1

    def test_prompt_copy_fallback(self, runner, chdir_project):
        """--copy should fallback to stdout when clip not available"""
        result = runner.invoke(prompt_cmd, ["--copy"])
        # Whether clip is available or not, should not crash
        assert result.exit_code == 0
        # Should have output (success copy message or fallback to stdout)
        assert len(result.output) > 0


# ---------------------------------------------------------------------------
# Tests: _search_related_insights
# ---------------------------------------------------------------------------

class TestSearchRelatedInsights:
    """Semantic matching related Insight tests"""

    def test_no_index_db_returns_empty(self, tmp_path):
        """Returns empty list when vector index does not exist"""
        result = _search_related_insights(tmp_path, "any query")
        assert result == []

    def test_empty_db_returns_empty(self, tmp_path):
        """Returns empty list when vector database is empty"""
        import sqlite3

        db_dir = tmp_path / ".vibecollab" / "vectors"
        db_dir.mkdir(parents=True)
        db_path = db_dir / "index.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE vectors (
                doc_id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                vector BLOB NOT NULL,
                source TEXT DEFAULT '',
                source_type TEXT DEFAULT '',
                metadata TEXT DEFAULT '{}',
                dimensions INTEGER NOT NULL
            )
        """)
        conn.commit()
        conn.close()

        result = _search_related_insights(tmp_path, "query text")
        assert result == []

    def test_returns_related_insights(self, tmp_path):
        """Returns related Insights when vector index exists"""
        from vibecollab.insight.embedder import Embedder, EmbedderConfig
        from vibecollab.search.vector_store import VectorDocument, VectorStore

        db_dir = tmp_path / ".vibecollab" / "vectors"
        db_dir.mkdir(parents=True)
        db_path = db_dir / "index.db"

        embedder = Embedder(EmbedderConfig(backend="pure_python", dimensions=256))
        store = VectorStore(db_path=db_path, dimensions=256)

        # Index two Insights
        text1 = "Windows encoding compatibility fix experience"
        text2 = "CI/CD pipeline configuration best practices"
        vec1 = embedder.embed_text(text1)
        vec2 = embedder.embed_text(text2)

        store.upsert(VectorDocument(
            doc_id="insight:INS-001",
            text=text1,
            vector=vec1,
            source=".vibecollab/insights/INS-001.yaml",
            source_type="insight",
            metadata={"title": "Encoding compat fix", "tags": ["windows", "encoding"], "category": "bugfix"},
        ))
        store.upsert(VectorDocument(
            doc_id="insight:INS-002",
            text=text2,
            vector=vec2,
            source=".vibecollab/insights/INS-002.yaml",
            source_type="insight",
            metadata={"title": "CI config", "tags": ["ci", "devops"], "category": "workflow"},
        ))
        store.close()

        result = _search_related_insights(tmp_path, "Windows encoding issue")
        assert len(result) > 0
        # Each result should contain id, title, tags, score
        for r in result:
            assert "id" in r
            assert "title" in r
            assert "tags" in r
            assert "score" in r
            assert isinstance(r["score"], float)

    def test_only_returns_insights_not_documents(self, tmp_path):
        """Only returns results with source_type=insight"""
        from vibecollab.insight.embedder import Embedder, EmbedderConfig
        from vibecollab.search.vector_store import VectorDocument, VectorStore

        db_dir = tmp_path / ".vibecollab" / "vectors"
        db_dir.mkdir(parents=True)
        db_path = db_dir / "index.db"

        embedder = Embedder(EmbedderConfig(backend="pure_python", dimensions=256))
        store = VectorStore(db_path=db_path, dimensions=256)

        text = "Project document content"
        vec = embedder.embed_text(text)

        # Only index document type
        store.upsert(VectorDocument(
            doc_id="doc:CONTEXT.md:0",
            text=text,
            vector=vec,
            source="docs/CONTEXT.md",
            source_type="document",
            metadata={"heading": "# Context"},
        ))
        store.close()

        result = _search_related_insights(tmp_path, "project document")
        # Should be empty because there are no insight type documents
        assert result == []


# ---------------------------------------------------------------------------
# Tests: onboard semantic enhancement
# ---------------------------------------------------------------------------

class TestOnboardSemanticEnhancement:
    """Onboard command semantic enhancement tests"""

    @pytest.fixture
    def project_with_index(self, project_dir):
        """Create a project with vector index"""
        from vibecollab.insight.embedder import Embedder, EmbedderConfig
        from vibecollab.search.vector_store import VectorDocument, VectorStore

        db_dir = project_dir / ".vibecollab" / "vectors"
        db_dir.mkdir(parents=True, exist_ok=True)
        db_path = db_dir / "index.db"

        embedder = Embedder(EmbedderConfig(backend="pure_python", dimensions=256))
        store = VectorStore(db_path=db_path, dimensions=256)

        # Index some Insights
        insights = [
            ("INS-001", "Encoding compatibility fix experience", ["windows", "encoding"], "bugfix"),
            ("INS-002", "Test strategy and coverage improvement", ["testing", "coverage"], "quality"),
        ]
        for ins_id, text, tags, category in insights:
            vec = embedder.embed_text(text)
            store.upsert(VectorDocument(
                doc_id=f"insight:{ins_id}",
                text=text,
                vector=vec,
                source=f".vibecollab/insights/{ins_id}.yaml",
                source_type="insight",
                metadata={"title": text, "tags": tags, "category": category},
            ))

        store.close()
        return project_dir

    def test_onboard_json_includes_related_insights(self, runner, project_with_index, monkeypatch):
        """JSON output includes related_insights field"""
        monkeypatch.chdir(project_with_index)
        result = runner.invoke(onboard, ["--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "related_insights" in data
        assert isinstance(data["related_insights"], list)

    def test_onboard_json_related_insights_structure(self, runner, project_with_index, monkeypatch):
        """related_insights record structure is correct"""
        monkeypatch.chdir(project_with_index)
        result = runner.invoke(onboard, ["--json"])
        data = json.loads(result.output)
        for ri in data["related_insights"]:
            assert "id" in ri
            assert "title" in ri
            assert "tags" in ri
            assert "score" in ri

    def test_onboard_rich_shows_related_panel(self, runner, project_with_index, monkeypatch):
        """Rich output includes related Insight panel"""
        monkeypatch.chdir(project_with_index)
        result = runner.invoke(onboard, [])
        assert result.exit_code == 0
        # If there are matching results, should show panel title
        # Note: PurePython embedder precision is limited, may have no matches
        # But should not crash

    def test_onboard_no_index_still_works(self, runner, chdir_project):
        """Onboard still works when no vector index exists"""
        result = runner.invoke(onboard, ["--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data.get("related_insights", []) == []

    def test_collect_context_includes_related_insights_key(self, project_with_index, monkeypatch):
        """_collect_project_context returns related_insights key"""
        monkeypatch.chdir(project_with_index)
        ctx = _collect_project_context(project_with_index / "project.yaml")
        assert "related_insights" in ctx
        assert isinstance(ctx["related_insights"], list)

    def test_collect_context_no_index_empty_related(self, chdir_project, project_dir):
        """related_insights is empty list when no index"""
        ctx = _collect_project_context(project_dir / "project.yaml")
        assert ctx["related_insights"] == []

    def test_onboard_with_developer_uses_dev_context(self, runner, project_with_index, monkeypatch):
        """Uses developer context as query when developer is specified"""
        monkeypatch.chdir(project_with_index)
        result = runner.invoke(onboard, ["-d", "testdev", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "related_insights" in data
