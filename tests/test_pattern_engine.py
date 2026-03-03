"""
PatternEngine unit tests.
"""

from pathlib import Path

import pytest

from vibecollab.core.generator import LLMContextGenerator
from vibecollab.core.pattern_engine import (
    PATTERNS_DIR,
    PatternEngine,
    _filter_format_review,
    _filter_join_list,
    _filter_quote_list,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def minimal_config():
    """Minimal renderable config."""
    return {
        "project": {"name": "TestProject", "version": "v1.0"},
        "philosophy": {
            "vibe_development": {"enabled": True, "principles": ["Test principle"]},
            "decision_quality": {"target_rate": 0.9, "critical_tolerance": 0},
        },
        "roles": [
            {
                "code": "DEV",
                "name": "Development",
                "focus": ["Implementation"],
                "triggers": ["develop"],
                "is_gatekeeper": False,
            }
        ],
        "decision_levels": [
            {
                "level": "S",
                "name": "Strategic",
                "scope": "Overall direction",
                "review": {"required": True, "mode": "sync"},
            }
        ],
        "documentation": {"key_files": []},
    }


@pytest.fixture
def full_config():
    """Full config (load project.yaml)."""
    import yaml

    project_yaml = Path(__file__).parent.parent / "project.yaml"
    if not project_yaml.exists():
        pytest.skip("project.yaml not found")
    with open(project_yaml, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# PatternEngine initialization
# ---------------------------------------------------------------------------

class TestPatternEngineInit:
    def test_init_default_patterns_dir(self, minimal_config):
        engine = PatternEngine(minimal_config)
        assert engine.patterns_dir == PATTERNS_DIR
        assert engine.manifest is not None
        assert "sections" in engine.manifest

    def test_init_custom_patterns_dir(self, minimal_config):
        engine = PatternEngine(minimal_config, patterns_dir=PATTERNS_DIR)
        assert engine.patterns_dir == PATTERNS_DIR

    def test_manifest_has_sections(self, minimal_config):
        engine = PatternEngine(minimal_config)
        sections = engine.manifest["sections"]
        assert len(sections) >= 20
        assert sections[0]["id"] == "header"
        assert sections[-1]["id"] == "footer"

    def test_list_patterns(self, minimal_config):
        engine = PatternEngine(minimal_config)
        patterns = engine.list_patterns()
        assert len(patterns) >= 20
        ids = [p["id"] for p in patterns]
        assert "header" in ids
        assert "philosophy" in ids
        assert "footer" in ids


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

class TestPatternEngineRender:
    def test_render_produces_content(self, minimal_config):
        engine = PatternEngine(minimal_config)
        output = engine.render()
        assert len(output) > 1000
        assert "# TestProject AI Collaboration Rules" in output
        assert "# I. Core Philosophy" in output

    def test_render_contains_all_mandatory_sections(self, minimal_config):
        engine = PatternEngine(minimal_config)
        output = engine.render()
        mandatory = [
            "# I. Core Philosophy",
            "# II. Role Definitions",
            "# III. Decision Classification System",
            "# IV. Development Workflow Protocol",
            "# V. Testing System",
            "# VI. Milestone Definition",
            "# VII. Iteration Management",
            "# VIII. Phase-Based Collaboration Rules",
            "# IX. Context Management",
        ]
        for section in mandatory:
            assert section in output, f"Missing section: {section}"

    def test_render_conditional_sections_excluded(self, minimal_config):
        """multi_developer not enabled should not render section X."""
        engine = PatternEngine(minimal_config)
        output = engine.render()
        assert "# X. Multi-Developer/Agent Collaboration Protocol" not in output

    def test_render_conditional_sections_included(self, minimal_config):
        """multi_developer enabled should render section X."""
        minimal_config["multi_developer"] = {
            "enabled": True,
            "identity": {"primary": "git_username", "fallback": "system_user", "normalize": True},
        }
        engine = PatternEngine(minimal_config)
        output = engine.render()
        assert "# X. Multi-Developer/Agent Collaboration Protocol" in output

    def test_render_default_true_conditions(self, minimal_config):
        """protocol_check not in config but enabled by default."""
        engine = PatternEngine(minimal_config)
        output = engine.render()
        assert "# XII. Protocol Self-Check Mechanism" in output

    def test_render_full_config(self, full_config):
        """Render with full project.yaml."""
        engine = PatternEngine(full_config, project_root=Path(__file__).parent.parent)
        output = engine.render()
        assert "AI Collaboration Rules" in output
        assert len(output) > 15000

    def test_render_footer_has_timestamp(self, minimal_config):
        engine = PatternEngine(minimal_config)
        output = engine.render()
        assert "*This is a living document" in output
        assert "*Generated at:" in output


# ---------------------------------------------------------------------------
# Condition evaluation
# ---------------------------------------------------------------------------

class TestConditionEvaluation:
    def test_simple_bool_true(self, minimal_config):
        minimal_config["multi_developer"] = {"enabled": True}
        engine = PatternEngine(minimal_config)
        assert engine._evaluate_condition("config.multi_developer.enabled") is True

    def test_simple_bool_false(self, minimal_config):
        minimal_config["multi_developer"] = {"enabled": False}
        engine = PatternEngine(minimal_config)
        assert engine._evaluate_condition("config.multi_developer.enabled") is False

    def test_missing_key_returns_false(self, minimal_config):
        engine = PatternEngine(minimal_config)
        assert engine._evaluate_condition("config.nonexistent.enabled") is False

    def test_missing_key_with_default_true(self, minimal_config):
        engine = PatternEngine(minimal_config)
        assert engine._evaluate_condition("config.nonexistent.enabled|true") is True

    def test_missing_key_with_default_false(self, minimal_config):
        engine = PatternEngine(minimal_config)
        assert engine._evaluate_condition("config.nonexistent.enabled|false") is False

    def test_deep_path(self, minimal_config):
        minimal_config["testing"] = {"product_qa": {"enabled": True}}
        engine = PatternEngine(minimal_config)
        assert engine._evaluate_condition("config.testing.product_qa.enabled") is True

    def test_dict_non_empty(self, minimal_config):
        minimal_config["symbology"] = {"test": [{"symbol": "X", "meaning": "Y"}]}
        engine = PatternEngine(minimal_config)
        assert engine._evaluate_condition("config.symbology") is True

    def test_dict_empty(self, minimal_config):
        minimal_config["symbology"] = {}
        engine = PatternEngine(minimal_config)
        assert engine._evaluate_condition("config.symbology") is False

    def test_has_extensions_false(self, minimal_config):
        engine = PatternEngine(minimal_config)
        assert engine._evaluate_condition("has_extensions") is False

    def test_unknown_condition_returns_true(self, minimal_config):
        engine = PatternEngine(minimal_config)
        assert engine._evaluate_condition("something_else") is True


# ---------------------------------------------------------------------------
# Custom Jinja2 Filters
# ---------------------------------------------------------------------------

class TestFilters:
    def test_join_list_default(self):
        assert _filter_join_list(["a", "b", "c"]) == "a, b, c"

    def test_join_list_custom_sep(self):
        assert _filter_join_list(["a", "b"], " | ") == "a | b"

    def test_join_list_non_list(self):
        assert _filter_join_list("hello") == "hello"

    def test_quote_list(self):
        assert _filter_quote_list(["design", "protocol"]) == '"design", "protocol"'

    def test_quote_list_custom_sep(self):
        assert _filter_quote_list(["a", "b"], " | ") == '"a" | "b"'

    def test_format_review_sync(self):
        r = {"required": True, "mode": "sync"}
        assert _filter_format_review(r) == "Must be manually confirmed, record decision rationale"

    def test_format_review_async(self):
        r = {"required": True, "mode": "async"}
        assert _filter_format_review(r) == "Human review, async confirmation allowed"

    def test_format_review_auto(self):
        r = {"required": False, "mode": "auto"}
        assert _filter_format_review(r) == "AI suggests, human can quickly confirm or auto-approve"

    def test_format_review_none(self):
        r = {"required": False, "mode": "none"}
        assert _filter_format_review(r) == "AI decides autonomously, adjustable afterwards"

    def test_format_review_required_fallback(self):
        r = {"required": True}
        assert _filter_format_review(r) == "Review required"


# ---------------------------------------------------------------------------
# Integration with LLMContextGenerator
# ---------------------------------------------------------------------------

class TestGeneratorIntegration:
    def test_generate_uses_patterns(self, minimal_config):
        gen = LLMContextGenerator(minimal_config)
        output = gen.generate()
        assert "# TestProject AI Collaboration Rules" in output

    def test_generate_full_config(self, full_config):
        """Generate with full project.yaml via Generator."""
        project_root = Path(__file__).parent.parent
        gen = LLMContextGenerator(full_config, project_root)
        output = gen.generate()
        assert "AI Collaboration Rules" in output
        assert len(output) > 15000


# ---------------------------------------------------------------------------
# Template Overlay
# ---------------------------------------------------------------------------

class TestTemplateOverlay:
    """Test user local template override/extension."""

    @pytest.fixture
    def overlay_project(self, tmp_path, minimal_config):
        """Create a temp project with local overlay."""
        patterns_dir = tmp_path / ".vibecollab" / "patterns"
        patterns_dir.mkdir(parents=True)
        return {
            "root": tmp_path,
            "patterns_dir": patterns_dir,
            "config": minimal_config,
        }

    def test_no_overlay_dir(self, minimal_config, tmp_path):
        """No local patterns directory should work normally."""
        engine = PatternEngine(minimal_config, project_root=tmp_path)
        assert engine.local_patterns_dir is None
        assert not engine.has_local_overlay
        output = engine.render()
        assert len(output) > 1000

    def test_overlay_detected(self, overlay_project):
        """Detect local patterns directory."""
        engine = PatternEngine(
            overlay_project["config"],
            project_root=overlay_project["root"],
        )
        assert engine.local_patterns_dir is not None
        assert engine.has_local_overlay

    def test_overlay_template_override(self, overlay_project):
        """Local template overrides built-in template."""
        local_footer = overlay_project["patterns_dir"] / "26_footer.md.j2"
        local_footer.write_text(
            "*Custom footer by {{ project.name }}*\n",
            encoding="utf-8",
        )
        engine = PatternEngine(
            overlay_project["config"],
            project_root=overlay_project["root"],
        )
        output = engine.render()
        assert "*Custom footer by TestProject*" in output
        assert "*This is a living document" not in output

    def test_overlay_manifest_add_section(self, overlay_project):
        """Local manifest adds new section."""
        import yaml

        custom_tmpl = overlay_project["patterns_dir"] / "custom_section.md.j2"
        custom_tmpl.write_text(
            "# Custom Section\n\nProject-specific collaboration rules.\n",
            encoding="utf-8",
        )
        local_manifest = {
            "sections": [
                {
                    "id": "custom_rules",
                    "template": "custom_section.md.j2",
                    "description": "Project custom rules",
                    "after": "changelog",
                }
            ]
        }
        manifest_path = overlay_project["patterns_dir"] / "manifest.yaml"
        with open(manifest_path, "w", encoding="utf-8") as f:
            yaml.dump(local_manifest, f, allow_unicode=True)

        engine = PatternEngine(
            overlay_project["config"],
            project_root=overlay_project["root"],
        )
        output = engine.render()
        assert "# Custom Section" in output
        assert "Project-specific collaboration rules" in output

    def test_overlay_manifest_exclude_section(self, overlay_project):
        """Local manifest excludes sections."""
        import yaml

        local_manifest = {
            "exclude": ["prompt_engineering", "prd_management"],
        }
        manifest_path = overlay_project["patterns_dir"] / "manifest.yaml"
        with open(manifest_path, "w", encoding="utf-8") as f:
            yaml.dump(local_manifest, f, allow_unicode=True)

        engine = PatternEngine(
            overlay_project["config"],
            project_root=overlay_project["root"],
        )
        patterns = engine.list_patterns()
        ids = [p["id"] for p in patterns]
        assert "prompt_engineering" not in ids
        assert "prd_management" not in ids
        assert "header" in ids
        assert "footer" in ids

    def test_overlay_manifest_replace_condition(self, overlay_project):
        """Local manifest replaces section condition."""
        import yaml

        local_manifest = {
            "sections": [
                {
                    "id": "multi_developer",
                    "template": "16_multi_developer.md.j2",
                    "description": "Multi-developer collaboration (forced enabled)",
                }
            ]
        }
        manifest_path = overlay_project["patterns_dir"] / "manifest.yaml"
        with open(manifest_path, "w", encoding="utf-8") as f:
            yaml.dump(local_manifest, f, allow_unicode=True)

        engine = PatternEngine(
            overlay_project["config"],
            project_root=overlay_project["root"],
        )
        for entry in engine.manifest["sections"]:
            if entry["id"] == "multi_developer":
                assert entry.get("condition") is None
                break

    def test_overlay_list_patterns_source(self, overlay_project):
        """list_patterns correctly annotates template source."""
        local_footer = overlay_project["patterns_dir"] / "26_footer.md.j2"
        local_footer.write_text("*Custom*\n", encoding="utf-8")

        engine = PatternEngine(
            overlay_project["config"],
            project_root=overlay_project["root"],
        )
        patterns = engine.list_patterns()
        sources = {p["id"]: p["source"] for p in patterns}
        assert sources["footer"] == "local"
        assert sources["header"] == "builtin"

    def test_merge_manifests_static(self):
        """Static test of _merge_manifests merge logic."""
        builtin = {
            "sections": [
                {"id": "a", "template": "a.j2", "description": "A"},
                {"id": "b", "template": "b.j2", "description": "B"},
                {"id": "c", "template": "c.j2", "description": "C"},
            ]
        }
        local = {
            "exclude": ["b"],
            "sections": [
                {"id": "a", "template": "a_custom.j2", "description": "A Custom"},
                {"id": "d", "template": "d.j2", "description": "D", "after": "a"},
            ],
        }
        result = PatternEngine._merge_manifests(builtin, local)
        ids = [s["id"] for s in result["sections"]]

        assert "b" not in ids
        a_entry = next(s for s in result["sections"] if s["id"] == "a")
        assert a_entry["template"] == "a_custom.j2"
        assert ids.index("d") == ids.index("a") + 1
        assert "c" in ids


# ---------------------------------------------------------------------------
# Insight workflow template rendering
# ---------------------------------------------------------------------------

class TestInsightWorkflowTemplate:
    """Tests for 27_insight_workflow.md.j2 template rendering."""

    def test_insight_section_in_manifest(self, minimal_config):
        """manifest should contain insight_workflow section."""
        engine = PatternEngine(minimal_config)
        ids = [s["id"] for s in engine.manifest["sections"]]
        assert "insight_workflow" in ids

    def test_insight_rendered_by_default(self, minimal_config):
        """insight enabled by default, should appear in rendered output."""
        engine = PatternEngine(minimal_config)
        output = engine.render()
        assert "Insight Accumulation Workflow" in output
        assert "vibecollab insight add" in output

    def test_insight_disabled(self, minimal_config):
        """insight.enabled=false should not render."""
        minimal_config["insight"] = {"enabled": False}
        engine = PatternEngine(minimal_config)
        output = engine.render()
        assert "Insight Accumulation Workflow" not in output

    def test_insight_section_position(self, minimal_config):
        """insight_workflow should be before footer."""
        engine = PatternEngine(minimal_config)
        ids = [s["id"] for s in engine.manifest["sections"]]
        assert ids.index("insight_workflow") < ids.index("footer")

    def test_dialogue_protocol_includes_insight_step(self, minimal_config):
        """Dialogue end flow should include insight check step."""
        minimal_config["dialogue_protocol"] = {
            "on_start": {"read_files": ["CONTRIBUTING_AI.md"]},
            "on_end": {"update_files": ["docs/CONTEXT.md"], "git_commit": True},
            "standard_flow": [],
        }
        engine = PatternEngine(minimal_config)
        output = engine.render()
        assert "Insight check" in output
