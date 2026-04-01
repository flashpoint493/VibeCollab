"""
Tests for RoleManager permission system (role.py DEV-027).

Covers: _load_permissions_config, get_developer_roles, get_primary_role,
        can_create_task_for, can_transition_to, can_write_file,
        can_approve_decision, get_role_permissions, get_effective_permissions.

Uses real RoleManager with project.yaml-style config dicts (no mocks on SUT).
"""

from pathlib import Path
from typing import Dict

import pytest

from vibecollab.domain.role import RoleManager

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config(
    *,
    roles: list | None = None,
    developers: list | None = None,
) -> Dict:
    """Build a minimal project.yaml dict with role/developer sections."""
    return {
        "project": {"name": "TestProject", "version": "v1.0"},
        "roles": roles or [],
        "developers": developers or [],
    }


def _make_rm(tmp_path: Path, config: Dict) -> RoleManager:
    """Create a RoleManager pointed at *tmp_path* with the given config."""
    # Ensure the docs/roles dir exists so RoleManager init doesn't fail
    (tmp_path / "docs" / "roles").mkdir(parents=True, exist_ok=True)
    return RoleManager(project_root=tmp_path, config=config)


# ---------------------------------------------------------------------------
# Fixtures – reusable project configs
# ---------------------------------------------------------------------------

FULL_ROLES = [
    {
        "code": "DEV",
        "name": "Development",
        "permissions": {
            "file_patterns": ["src/**", "tests/**", "docs/**"],
            "can_create_task_for": ["DEV", "TEST"],
            "can_transition_to": ["TODO", "IN_PROGRESS", "REVIEW"],
            "can_approve_decisions": ["C"],
        },
    },
    {
        "code": "ARCH",
        "name": "Architecture",
        "permissions": {
            "file_patterns": ["src/core/**", "docs/architecture/**", "docs/DECISIONS.md"],
            "can_create_task_for": ["DEV", "ARCH", "DESIGN"],
            "can_transition_to": ["TODO", "IN_PROGRESS", "REVIEW", "DONE"],
            "can_approve_decisions": ["S", "A", "B", "C"],
        },
    },
    {
        "code": "PM",
        "name": "Project Management",
        "permissions": {
            "file_patterns": ["docs/ROADMAP.md", "docs/CHANGELOG.md"],
            "can_create_task_for": ["PM", "DEV", "DESIGN"],
            "can_transition_to": ["TODO", "IN_PROGRESS", "REVIEW", "DONE"],
            "can_approve_decisions": ["A", "B", "C"],
        },
    },
    {
        "code": "QA",
        "name": "Quality Assurance",
        "permissions": {
            "file_patterns": ["tests/**"],
            "can_create_task_for": ["QA", "TEST"],
            "can_transition_to": ["REVIEW", "DONE"],
            "can_approve_decisions": ["B", "C"],
        },
    },
    {
        "code": "TEST",
        "name": "Unit Testing",
        "permissions": {
            "file_patterns": ["tests/**"],
            "can_create_task_for": ["TEST", "DEV"],
            "can_transition_to": ["TODO", "IN_PROGRESS", "REVIEW"],
        },
    },
]

FULL_DEVELOPERS = [
    {"name": "alice", "primary_role": "ARCH", "roles": ["ARCH", "DEV"]},
    {"name": "bob", "primary_role": "DEV", "roles": ["DEV"]},
    {"name": "carol", "primary_role": "PM", "roles": ["PM", "DEV"]},
    {"name": "dave", "primary_role": "QA", "roles": ["QA"]},
    {"name": "eve", "primary_role": "TEST", "roles": ["TEST"]},
]


@pytest.fixture
def full_config():
    return _make_config(roles=FULL_ROLES, developers=FULL_DEVELOPERS)


@pytest.fixture
def rm(tmp_path, full_config):
    """RoleManager with full role/dev config."""
    return _make_rm(tmp_path, full_config)


@pytest.fixture
def empty_rm(tmp_path):
    """RoleManager with no roles or developers (backward compat)."""
    return _make_rm(tmp_path, _make_config())


# ---------------------------------------------------------------------------
# _load_permissions_config
# ---------------------------------------------------------------------------

class TestLoadPermissionsConfig:
    def test_loads_roles_and_developers(self, rm):
        """Config is parsed and lookup dicts built."""
        cfg = rm._load_permissions_config()
        assert "developers" in cfg
        assert "roles" in cfg
        assert "alice" in rm._developers_lookup
        assert "DEV" in rm._roles_lookup

    def test_cache_returns_same_object(self, rm):
        """Successive calls return the cached dict."""
        a = rm._load_permissions_config()
        b = rm._load_permissions_config()
        assert a is b

    def test_empty_config(self, empty_rm):
        """Empty config produces empty lookups."""
        cfg = empty_rm._load_permissions_config()
        assert cfg["developers"] == []
        assert cfg["roles"] == []


# ---------------------------------------------------------------------------
# get_developer_roles
# ---------------------------------------------------------------------------

class TestGetDeveloperRoles:
    def test_known_developer_multi_roles(self, rm):
        """Alice has ARCH + DEV roles."""
        assert rm.get_developer_roles("alice") == ["ARCH", "DEV"]

    def test_known_developer_single_role(self, rm):
        """Bob has only DEV."""
        assert rm.get_developer_roles("bob") == ["DEV"]

    def test_unknown_developer_fallback(self, rm):
        """Unknown developer falls back to [developer_name]."""
        roles = rm.get_developer_roles("unknown_user")
        assert roles == ["unknown_user"]

    def test_empty_config_fallback(self, empty_rm):
        """With no developers configured, fallback to [name]."""
        roles = empty_rm.get_developer_roles("anyone")
        assert roles == ["anyone"]


# ---------------------------------------------------------------------------
# get_primary_role
# ---------------------------------------------------------------------------

class TestGetPrimaryRole:
    def test_explicit_primary(self, rm):
        assert rm.get_primary_role("alice") == "ARCH"

    def test_single_role_developer(self, rm):
        assert rm.get_primary_role("bob") == "DEV"

    def test_unknown_developer(self, rm):
        """Unknown developer's primary is the first item from fallback roles."""
        assert rm.get_primary_role("unknown") == "unknown"

    def test_developer_primary_differs_from_first_role(self, rm):
        """Carol's primary is PM (not DEV which is also in her roles)."""
        assert rm.get_primary_role("carol") == "PM"


# ---------------------------------------------------------------------------
# can_create_task_for
# ---------------------------------------------------------------------------

class TestCanCreateTaskFor:
    def test_dev_can_create_for_dev(self, rm):
        assert rm.can_create_task_for("DEV", developer="bob") is True

    def test_dev_can_create_for_test(self, rm):
        assert rm.can_create_task_for("TEST", developer="bob") is True

    def test_dev_cannot_create_for_pm(self, rm):
        """DEV role can only create for DEV and TEST."""
        assert rm.can_create_task_for("PM", developer="bob") is False

    def test_dev_cannot_create_for_arch(self, rm):
        assert rm.can_create_task_for("ARCH", developer="bob") is False

    def test_arch_can_create_for_dev(self, rm):
        assert rm.can_create_task_for("DEV", developer="alice") is True

    def test_arch_can_create_for_design(self, rm):
        assert rm.can_create_task_for("DESIGN", developer="alice") is True

    def test_pm_can_create_for_dev(self, rm):
        assert rm.can_create_task_for("DEV", developer="carol") is True

    def test_pm_cannot_create_for_arch(self, rm):
        assert rm.can_create_task_for("ARCH", developer="carol") is False

    def test_qa_can_create_for_test(self, rm):
        assert rm.can_create_task_for("TEST", developer="dave") is True

    def test_qa_cannot_create_for_dev(self, rm):
        assert rm.can_create_task_for("DEV", developer="dave") is False

    def test_unknown_developer_allows_all(self, rm):
        """No restrictions for unknown developers (backward compat)."""
        assert rm.can_create_task_for("PM", developer="unknown") is True

    def test_empty_config_allows_all(self, empty_rm):
        """No roles = no restrictions."""
        assert empty_rm.can_create_task_for("ANY", developer="anyone") is True


# ---------------------------------------------------------------------------
# can_transition_to
# ---------------------------------------------------------------------------

class TestCanTransitionTo:
    def test_dev_can_transition_to_in_progress(self, rm):
        assert rm.can_transition_to("IN_PROGRESS", developer="bob") is True

    def test_dev_can_transition_to_review(self, rm):
        assert rm.can_transition_to("REVIEW", developer="bob") is True

    def test_dev_cannot_transition_to_done(self, rm):
        """DEV cannot finalize tasks to DONE."""
        assert rm.can_transition_to("DONE", developer="bob") is False

    def test_arch_can_transition_to_done(self, rm):
        assert rm.can_transition_to("DONE", developer="alice") is True

    def test_qa_only_review_and_done(self, rm):
        assert rm.can_transition_to("REVIEW", developer="dave") is True
        assert rm.can_transition_to("DONE", developer="dave") is True
        assert rm.can_transition_to("TODO", developer="dave") is False
        assert rm.can_transition_to("IN_PROGRESS", developer="dave") is False

    def test_pm_full_transitions(self, rm):
        for status in ["TODO", "IN_PROGRESS", "REVIEW", "DONE"]:
            assert rm.can_transition_to(status, developer="carol") is True

    def test_unknown_developer_allows_all(self, rm):
        assert rm.can_transition_to("DONE", developer="unknown") is True

    def test_empty_config_allows_all(self, empty_rm):
        assert empty_rm.can_transition_to("DONE", developer="anyone") is True


# ---------------------------------------------------------------------------
# can_write_file
# ---------------------------------------------------------------------------

class TestCanWriteFile:
    def test_dev_can_write_src(self, rm):
        assert rm.can_write_file("src/vibecollab/core/pipeline.py", developer="bob") is True

    def test_dev_can_write_tests(self, rm):
        assert rm.can_write_file("tests/test_guard.py", developer="bob") is True

    def test_dev_can_write_docs(self, rm):
        assert rm.can_write_file("docs/CONTEXT.md", developer="bob") is True

    def test_arch_can_write_core(self, rm):
        assert rm.can_write_file("src/core/pipeline.py", developer="alice") is True

    def test_arch_can_write_decisions(self, rm):
        assert rm.can_write_file("docs/DECISIONS.md", developer="alice") is True

    def test_arch_cannot_write_tests(self, rm):
        """ARCH file_patterns don't include tests/**."""
        assert rm.can_write_file("tests/test_foo.py", developer="alice") is False

    def test_arch_cannot_write_random_src(self, rm):
        """ARCH only has src/core/**, not src/**."""
        assert rm.can_write_file("src/vibecollab/cli/main.py", developer="alice") is False

    def test_pm_can_write_roadmap(self, rm):
        assert rm.can_write_file("docs/ROADMAP.md", developer="carol") is True

    def test_pm_can_write_changelog(self, rm):
        assert rm.can_write_file("docs/CHANGELOG.md", developer="carol") is True

    def test_pm_cannot_write_src(self, rm):
        assert rm.can_write_file("src/foo.py", developer="carol") is False

    def test_qa_can_write_tests(self, rm):
        assert rm.can_write_file("tests/test_qa.py", developer="dave") is True

    def test_qa_cannot_write_src(self, rm):
        assert rm.can_write_file("src/main.py", developer="dave") is False

    def test_unknown_developer_allows_all(self, rm):
        """No restrictions for developers without configured role."""
        assert rm.can_write_file("anything.py", developer="unknown") is True

    def test_empty_config_allows_all(self, empty_rm):
        assert empty_rm.can_write_file("anything.py", developer="anyone") is True

    def test_fnmatch_double_star(self, rm):
        """Ensure ** glob works for nested paths."""
        assert rm.can_write_file("src/vibecollab/domain/guard.py", developer="bob") is True

    def test_exact_filename_match(self, rm):
        """PM pattern 'docs/ROADMAP.md' matches exact file."""
        assert rm.can_write_file("docs/ROADMAP.md", developer="carol") is True
        assert rm.can_write_file("docs/ROADMAP.md.bak", developer="carol") is False


# ---------------------------------------------------------------------------
# can_approve_decision
# ---------------------------------------------------------------------------

class TestCanApproveDecision:
    def test_arch_approves_s_level(self, rm):
        """ARCH has S-level approval."""
        assert rm.can_approve_decision("S", developer="alice") is True

    def test_arch_approves_all_levels(self, rm):
        for level in ["S", "A", "B", "C"]:
            assert rm.can_approve_decision(level, developer="alice") is True

    def test_dev_approves_only_c(self, rm):
        assert rm.can_approve_decision("C", developer="bob") is True
        assert rm.can_approve_decision("B", developer="bob") is False
        assert rm.can_approve_decision("A", developer="bob") is False
        assert rm.can_approve_decision("S", developer="bob") is False

    def test_pm_approves_a_b_c(self, rm):
        assert rm.can_approve_decision("A", developer="carol") is True
        assert rm.can_approve_decision("B", developer="carol") is True
        assert rm.can_approve_decision("C", developer="carol") is True
        assert rm.can_approve_decision("S", developer="carol") is False

    def test_qa_approves_b_c(self, rm):
        assert rm.can_approve_decision("B", developer="dave") is True
        assert rm.can_approve_decision("C", developer="dave") is True
        assert rm.can_approve_decision("A", developer="dave") is False
        assert rm.can_approve_decision("S", developer="dave") is False

    def test_unknown_developer_default_policy(self, rm):
        """No explicit permissions: S/A denied, B/C allowed."""
        assert rm.can_approve_decision("S", developer="unknown") is False
        assert rm.can_approve_decision("A", developer="unknown") is False
        assert rm.can_approve_decision("B", developer="unknown") is True
        assert rm.can_approve_decision("C", developer="unknown") is True

    def test_empty_config_default_policy(self, empty_rm):
        """Same default policy when no config at all."""
        assert empty_rm.can_approve_decision("S", developer="anyone") is False
        assert empty_rm.can_approve_decision("A", developer="anyone") is False
        assert empty_rm.can_approve_decision("B", developer="anyone") is True
        assert empty_rm.can_approve_decision("C", developer="anyone") is True

    def test_role_without_approve_field(self, tmp_path):
        """TEST role has no can_approve_decisions → default policy kicks in."""
        config = _make_config(
            roles=FULL_ROLES,
            developers=[{"name": "tester", "primary_role": "TEST", "roles": ["TEST"]}],
        )
        rm = _make_rm(tmp_path, config)
        assert rm.can_approve_decision("S", developer="tester") is False
        assert rm.can_approve_decision("C", developer="tester") is True


# ---------------------------------------------------------------------------
# get_role_permissions
# ---------------------------------------------------------------------------

class TestGetRolePermissions:
    def test_known_role(self, rm):
        perms = rm.get_role_permissions("DEV")
        assert "file_patterns" in perms
        assert "can_create_task_for" in perms
        assert "can_transition_to" in perms
        assert perms["can_approve_decisions"] == ["C"]

    def test_unknown_role_empty(self, rm):
        perms = rm.get_role_permissions("NONEXISTENT")
        assert perms == {}

    def test_each_role_has_permissions(self, rm):
        for code in ["DEV", "ARCH", "PM", "QA"]:
            perms = rm.get_role_permissions(code)
            assert isinstance(perms, dict)
            assert len(perms) > 0


# ---------------------------------------------------------------------------
# get_effective_permissions
# ---------------------------------------------------------------------------

class TestGetEffectivePermissions:
    def test_structure(self, rm):
        ep = rm.get_effective_permissions(developer="alice")
        assert ep["developer"] == "alice"
        assert ep["primary_role"] == "ARCH"
        assert set(ep["all_roles"]) == {"ARCH", "DEV"}
        assert "file_patterns" in ep["permissions"]

    def test_single_role_developer(self, rm):
        ep = rm.get_effective_permissions(developer="bob")
        assert ep["primary_role"] == "DEV"
        assert ep["all_roles"] == ["DEV"]

    def test_unknown_developer(self, rm):
        ep = rm.get_effective_permissions(developer="unknown")
        assert ep["developer"] == "unknown"
        assert ep["primary_role"] == "unknown"
        assert ep["all_roles"] == ["unknown"]
        assert ep["permissions"] == {}

    def test_empty_config(self, empty_rm):
        ep = empty_rm.get_effective_permissions(developer="anyone")
        assert ep["permissions"] == {}

    def test_permissions_match_role(self, rm):
        """Effective permissions should equal the primary role's permissions."""
        ep = rm.get_effective_permissions(developer="carol")
        assert ep["permissions"] == rm.get_role_permissions("PM")


# ---------------------------------------------------------------------------
# Cross-cutting / edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_developer_with_empty_roles_list(self, tmp_path):
        """Developer with explicit empty roles list falls back to [name]."""
        config = _make_config(
            roles=FULL_ROLES,
            developers=[{"name": "ghost", "roles": []}],
        )
        rm = _make_rm(tmp_path, config)
        assert rm.get_developer_roles("ghost") == ["ghost"]

    def test_developer_without_primary_role_field(self, tmp_path):
        """Missing primary_role → first item from roles list."""
        config = _make_config(
            roles=FULL_ROLES,
            developers=[{"name": "frank", "roles": ["QA", "TEST"]}],
        )
        rm = _make_rm(tmp_path, config)
        assert rm.get_primary_role("frank") == "QA"

    def test_permission_methods_idempotent(self, rm):
        """Calling permission methods multiple times gives same results."""
        for _ in range(3):
            assert rm.can_create_task_for("DEV", developer="bob") is True
            assert rm.can_write_file("src/foo.py", developer="bob") is True
            assert rm.can_approve_decision("C", developer="bob") is True

    def test_all_roles_consistent(self, rm):
        """get_effective_permissions contains roles from get_developer_roles."""
        for dev in ["alice", "bob", "carol", "dave", "eve"]:
            ep = rm.get_effective_permissions(developer=dev)
            assert ep["all_roles"] == rm.get_developer_roles(dev)
            assert ep["primary_role"] == rm.get_primary_role(dev)

    def test_multiple_developers_isolated(self, rm):
        """Each developer gets their own permissions, no leaking."""
        assert rm.can_create_task_for("PM", developer="bob") is False
        assert rm.can_create_task_for("PM", developer="carol") is True  # PM can create for PM

    def test_cache_not_corrupted_across_devs(self, rm):
        """Loading config for one developer doesn't corrupt another's result."""
        rm.get_effective_permissions(developer="alice")
        bob_ep = rm.get_effective_permissions(developer="bob")
        assert bob_ep["primary_role"] == "DEV"
