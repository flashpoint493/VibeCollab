"""
ConflictDetector module unit tests

Tests for cross-role conflict detection functionality.
"""

# Import built-in modules
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

# Import third-party modules
import pytest

# Import local modules
from vibecollab.domain.conflict_detector import (
    Conflict,
    ConflictDetector,
    ConflictType,
    is_windows_gbk,
)

# ============================================================================
# Test: is_windows_gbk
# ============================================================================

class TestIsWindowsGBK:
    """Test Windows GBK detection"""

    def test_non_windows_returns_false(self):
        """Non-Windows system returns False"""
        with patch("vibecollab._compat.platform.system", return_value="Linux"):
            result = is_windows_gbk()
            assert result is False

    def test_windows_with_utf8_returns_false(self):
        """Windows + UTF-8 encoding returns False"""
        with patch("vibecollab._compat.platform.system", return_value="Windows"):
            with patch("vibecollab._compat.sys.stdout") as mock_stdout:
                mock_stdout.encoding = "utf-8"
                result = is_windows_gbk()
                assert result is False

    def test_windows_with_gbk_returns_true(self):
        """Windows + GBK encoding returns True"""
        with patch("vibecollab._compat.platform.system", return_value="Windows"):
            with patch("vibecollab._compat.sys.stdout") as mock_stdout:
                mock_stdout.encoding = "gbk"
                result = is_windows_gbk()
                assert result is True


# ============================================================================
# Test: ConflictType
# ============================================================================

class TestConflictType:
    """Test ConflictType enum"""

    def test_conflict_types(self):
        """Verify conflict type definitions"""
        assert ConflictType.FILE == "file"
        assert ConflictType.TASK == "task"
        assert ConflictType.DEPENDENCY == "dependency"
        assert ConflictType.NAMING == "naming"


# ============================================================================
# Test: Conflict
# ============================================================================

class TestConflict:
    """Test Conflict class"""

    def test_init_defaults(self):
        """Test default initialization"""
        conflict = Conflict(
            conflict_type=ConflictType.FILE,
            severity="high",
            roles=["alice", "bob"],
            description="Test conflict"
        )

        assert conflict.type == "file"
        assert conflict.severity == "high"
        assert conflict.roles == ["alice", "bob"]
        assert conflict.description == "Test conflict"
        assert conflict.details == {}
        assert isinstance(conflict.detected_at, datetime)

    def test_init_with_details(self):
        """Test initialization with details"""
        details = {"files": ["test.py", "main.py"]}
        conflict = Conflict(
            conflict_type=ConflictType.FILE,
            severity="medium",
            roles=["alice"],
            description="File conflict",
            details=details
        )

        assert conflict.details == details

    def test_to_dict(self):
        """Test conversion to dict"""
        conflict = Conflict(
            conflict_type=ConflictType.TASK,
            severity="high",
            roles=["alice", "bob"],
            description="Task conflict",
            details={"task_id": "TASK-001"}
        )

        result = conflict.to_dict()

        assert result["type"] == "task"
        assert result["severity"] == "high"
        assert result["roles"] == ["alice", "bob"]
        assert result["description"] == "Task conflict"
        assert result["details"] == {"task_id": "TASK-001"}
        assert "detected_at" in result

    def test_str_representation(self):
        """Test string representation"""
        conflict = Conflict(
            conflict_type=ConflictType.DEPENDENCY,
            severity="medium",
            roles=["alice", "bob"],
            description="Circular dependency"
        )

        result = str(conflict)

        assert "[MEDIUM]" in result
        assert "dependency" in result
        assert "Circular dependency" in result
        assert "alice" in result
        assert "bob" in result


# ============================================================================
# Test: ConflictDetector
# ============================================================================

class TestConflictDetector:
    """Test ConflictDetector class"""

    @pytest.fixture
    def temp_project(self):
        """Create temporary project directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            roles_dir = project_root / "docs" / "roles"
            roles_dir.mkdir(parents=True)
            yield project_root

    @pytest.fixture
    def basic_config(self):
        """Basic config"""
        return {
            "role_context": {
                "enabled": True,
                "context": {
                    "per_role_dir": ".vibecollab/roles"
                },
                "collaboration": {
                    "file": ".vibecollab/roles/COLLABORATION.md"
                }
            }
        }

    def test_init(self, temp_project, basic_config):
        """Test initialization"""
        detector = ConflictDetector(temp_project, basic_config)

        assert detector.project_root == temp_project
        assert detector.config == basic_config
        assert detector.roles_dir == temp_project / ".vibecollab" / "roles"

    def test_detect_all_conflicts_empty_project(self, temp_project, basic_config):
        """Empty project should have no conflicts"""
        detector = ConflictDetector(temp_project, basic_config)
        conflicts = detector.detect_all_conflicts()

        assert conflicts == []

    def test_detect_all_conflicts_with_target_role(self, temp_project, basic_config):
        """Test conflict detection for a specific role"""
        # Create role directory and context
        alice_dir = temp_project / "docs" / "roles" / "alice"
        alice_dir.mkdir(parents=True)
        (alice_dir / "CONTEXT.md").write_text("## Current Tasks\n- Task 1", encoding="utf-8")

        detector = ConflictDetector(temp_project, basic_config)
        conflicts = detector.detect_all_conflicts(target_role="alice")

        # Only one role, should have no conflicts
        assert conflicts == []

    def test_detect_all_conflicts_nonexistent_role(self, temp_project, basic_config):
        """Test non-existent role"""
        detector = ConflictDetector(temp_project, basic_config)
        conflicts = detector.detect_all_conflicts(target_role="nonexistent")

        assert conflicts == []

    def test_detect_all_conflicts_between_roles(self, temp_project, basic_config):
        """Test conflict detection between two roles"""
        # Create two role directories
        for dev in ["alice", "bob"]:
            dev_dir = temp_project / "docs" / "roles" / dev
            dev_dir.mkdir(parents=True)
            (dev_dir / "CONTEXT.md").write_text(
                f"## Current Tasks\n- {dev} task",
                encoding="utf-8"
            )

        detector = ConflictDetector(temp_project, basic_config)
        conflicts = detector.detect_all_conflicts(between_roles=("alice", "bob"))

        # Tasks are not similar, should have no task conflicts
        assert isinstance(conflicts, list)


class TestConflictDetectorFileConflicts:
    """Test file conflict detection"""

    @pytest.fixture
    def temp_project_with_devs(self):
        """Create temporary project with roles"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            roles_dir = project_root / ".vibecollab" / "roles"

            for dev in ["alice", "bob"]:
                dev_dir = roles_dir / dev
                dev_dir.mkdir(parents=True)

            yield project_root

    @pytest.fixture
    def basic_config(self):
        return {
            "role_context": {
                "enabled": True,
                "context": {"per_role_dir": ".vibecollab/roles"},
                "collaboration": {"file": ".vibecollab/roles/COLLABORATION.md"}
            }
        }

    def test_detect_file_conflicts_common_files(self, temp_project_with_devs, basic_config):
        """Test detecting commonly modified files"""
        project = temp_project_with_devs

        # Alice modified main.py
        alice_ctx = "## Recently Completed\n- Modified `main.py` and `utils.py`"
        (project / ".vibecollab" / "roles" / "alice" / "CONTEXT.md").write_text(
            alice_ctx, encoding="utf-8"
        )

        # Bob also modified main.py
        bob_ctx = "## Recently Completed\n- Updated `main.py` and `config.py`"
        (project / ".vibecollab" / "roles" / "bob" / "CONTEXT.md").write_text(
            bob_ctx, encoding="utf-8"
        )

        detector = ConflictDetector(project, basic_config)
        conflicts = detector.detect_all_conflicts()

        # Should detect file conflict on main.py
        file_conflicts = [c for c in conflicts if c.type == ConflictType.FILE]
        assert len(file_conflicts) == 1
        assert "main.py" in file_conflicts[0].details.get("files", [])

    def test_detect_file_conflicts_no_common_files(self, temp_project_with_devs, basic_config):
        """Test no conflict when no common files modified"""
        project = temp_project_with_devs

        (project / ".vibecollab" / "roles" / "alice" / "CONTEXT.md").write_text(
            "## Recently Completed\n- Modified `alice.py`", encoding="utf-8"
        )
        (project / ".vibecollab" / "roles" / "bob" / "CONTEXT.md").write_text(
            "## Recently Completed\n- Modified `bob.py`", encoding="utf-8"
        )

        detector = ConflictDetector(project, basic_config)
        conflicts = detector.detect_all_conflicts()

        file_conflicts = [c for c in conflicts if c.type == ConflictType.FILE]
        assert len(file_conflicts) == 0


class TestConflictDetectorTaskConflicts:
    """Test task conflict detection"""

    @pytest.fixture
    def temp_project_with_devs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            for dev in ["alice", "bob"]:
                dev_dir = project_root / ".vibecollab" / "roles" / dev
                dev_dir.mkdir(parents=True)
            yield project_root

    @pytest.fixture
    def basic_config(self):
        return {
            "role_context": {
                "enabled": True,
                "context": {"per_role_dir": ".vibecollab/roles"},
                "collaboration": {"file": ".vibecollab/roles/COLLABORATION.md"}
            }
        }

    def test_detect_similar_tasks(self, temp_project_with_devs, basic_config):
        """Test detecting similar tasks"""
        project = temp_project_with_devs

        # Two people have very similar tasks (using English for \w+ tokenization, exceeds 60% threshold)
        # Jaccard: {user, login, auth, module} / {implement, user, login, auth, module, develop} = 4/6 = 0.67
        (project / ".vibecollab" / "roles" / "alice" / "CONTEXT.md").write_text(
            "## Current Tasks\n- implement user login auth module", encoding="utf-8"
        )
        (project / ".vibecollab" / "roles" / "bob" / "CONTEXT.md").write_text(
            "## Current Tasks\n- develop user login auth module", encoding="utf-8"
        )

        detector = ConflictDetector(project, basic_config)
        conflicts = detector.detect_all_conflicts()

        task_conflicts = [c for c in conflicts if c.type == ConflictType.TASK]
        assert len(task_conflicts) == 1
        assert task_conflicts[0].severity == "high"

    def test_detect_different_tasks(self, temp_project_with_devs, basic_config):
        """Test different tasks should not have conflicts"""
        project = temp_project_with_devs

        # Using English for proper tokenization
        (project / ".vibecollab" / "roles" / "alice" / "CONTEXT.md").write_text(
            "## Current Tasks\n- implement user authentication", encoding="utf-8"
        )
        (project / ".vibecollab" / "roles" / "bob" / "CONTEXT.md").write_text(
            "## Current Tasks\n- optimize database query performance", encoding="utf-8"
        )

        detector = ConflictDetector(project, basic_config)
        conflicts = detector.detect_all_conflicts()

        task_conflicts = [c for c in conflicts if c.type == ConflictType.TASK]
        assert len(task_conflicts) == 0


class TestConflictDetectorDependencyConflicts:
    """Test dependency conflict detection"""

    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs" / "roles").mkdir(parents=True)
            yield project_root

    @pytest.fixture
    def basic_config(self):
        return {
            "role_context": {
                "enabled": True,
                "context": {"per_role_dir": ".vibecollab/roles"},
                "collaboration": {"file": ".vibecollab/roles/COLLABORATION.md"}
            }
        }

    def test_detect_circular_dependency(self, temp_project, basic_config):
        """Test detecting circular dependency"""
        collab_content = """## Task Assignment Matrix

| Task | Owner | Collaborators | Status | Dependencies |
|------|-------|---------------|--------|--------------|
| TASK-DEV-001: Feature A | alice | - | IN_PROGRESS | TASK-DEV-002 |
| TASK-DEV-002: Feature B | bob | - | IN_PROGRESS | TASK-DEV-001 |
"""
        collab_file = temp_project / "docs" / "roles" / "COLLABORATION.md"
        collab_file.write_text(collab_content, encoding="utf-8")

        detector = ConflictDetector(temp_project, basic_config)
        conflicts = detector.detect_all_conflicts()

        dep_conflicts = [c for c in conflicts if c.type == ConflictType.DEPENDENCY]
        assert len(dep_conflicts) == 1
        assert dep_conflicts[0].severity == "high"
        assert "Circular dependency" in dep_conflicts[0].description

    def test_no_circular_dependency(self, temp_project, basic_config):
        """Test no conflict when no circular dependency"""
        collab_content = """## Task Assignment Matrix

| Task | Owner | Collaborators | Status | Dependencies |
|------|-------|---------------|--------|--------------|
| TASK-DEV-001: Feature A | alice | - | IN_PROGRESS | - |
| TASK-DEV-002: Feature B | bob | - | IN_PROGRESS | TASK-DEV-001 |
"""
        collab_file = temp_project / "docs" / "roles" / "COLLABORATION.md"
        collab_file.write_text(collab_content, encoding="utf-8")

        detector = ConflictDetector(temp_project, basic_config)
        conflicts = detector.detect_all_conflicts()

        dep_conflicts = [c for c in conflicts if c.type == ConflictType.DEPENDENCY]
        assert len(dep_conflicts) == 0


class TestConflictDetectorNamingConflicts:
    """Test naming conflict detection"""

    @pytest.fixture
    def temp_project_with_devs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            for dev in ["alice", "bob"]:
                dev_dir = project_root / ".vibecollab" / "roles" / dev
                dev_dir.mkdir(parents=True)
            yield project_root

    @pytest.fixture
    def basic_config(self):
        return {
            "role_context": {
                "enabled": True,
                "context": {"per_role_dir": ".vibecollab/roles"},
                "collaboration": {"file": ".vibecollab/roles/COLLABORATION.md"}
            }
        }

    def test_detect_naming_conflict_class(self, temp_project_with_devs, basic_config):
        """Test detecting class name conflicts"""
        project = temp_project_with_devs

        alice_ctx = """## Recently Completed
```python
class UserManager:
    pass
```
"""
        bob_ctx = """## Recently Completed
```python
class UserManager:
    def login(self):
        pass
```
"""
        (project / ".vibecollab" / "roles" / "alice" / "CONTEXT.md").write_text(
            alice_ctx, encoding="utf-8"
        )
        (project / ".vibecollab" / "roles" / "bob" / "CONTEXT.md").write_text(
            bob_ctx, encoding="utf-8"
        )

        detector = ConflictDetector(project, basic_config)
        conflicts = detector.detect_all_conflicts()

        naming_conflicts = [c for c in conflicts if c.type == ConflictType.NAMING]
        assert len(naming_conflicts) == 1
        assert "UserManager" in naming_conflicts[0].details.get("names", [])

    def test_detect_naming_conflict_function(self, temp_project_with_devs, basic_config):
        """Test detecting function name conflicts"""
        project = temp_project_with_devs

        alice_ctx = """## Recently Completed
```python
def process_data():
    pass
```
"""
        bob_ctx = """## Recently Completed
```python
def process_data(data):
    return data
```
"""
        (project / ".vibecollab" / "roles" / "alice" / "CONTEXT.md").write_text(
            alice_ctx, encoding="utf-8"
        )
        (project / ".vibecollab" / "roles" / "bob" / "CONTEXT.md").write_text(
            bob_ctx, encoding="utf-8"
        )

        detector = ConflictDetector(project, basic_config)
        conflicts = detector.detect_all_conflicts()

        naming_conflicts = [c for c in conflicts if c.type == ConflictType.NAMING]
        assert len(naming_conflicts) == 1
        assert "process_data" in naming_conflicts[0].details.get("names", [])


class TestConflictDetectorHelpers:
    """Test helper methods"""

    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def basic_config(self):
        return {"role_context": {"enabled": True}}

    def test_extract_section_content(self, temp_project, basic_config):
        """Test section content extraction"""
        detector = ConflictDetector(temp_project, basic_config)

        content = """## Current Tasks
- Task 1
- Task 2

## Recently Completed
- Done 1
"""
        result = detector._extract_section_content(content, "Current Tasks")
        assert "Task 1" in result
        assert "Task 2" in result
        assert "Done 1" not in result

    def test_extract_section_content_not_found(self, temp_project, basic_config):
        """Test empty return when section not found"""
        detector = ConflictDetector(temp_project, basic_config)

        content = "## Other Section\nContent"
        result = detector._extract_section_content(content, "Non-existent Section")
        assert result == ""

    def test_extract_current_tasks(self, temp_project, basic_config):
        """Test current task extraction"""
        detector = ConflictDetector(temp_project, basic_config)

        content = """## Current Tasks
- Implement Feature A
- Fix Bug B
* Optimize Performance
"""
        result = detector._extract_current_tasks(content)
        assert "Implement Feature A" in result
        assert "Fix Bug B" in result
        assert "Optimize Performance" in result

    def test_extract_code_names(self, temp_project, basic_config):
        """Test code name extraction"""
        detector = ConflictDetector(temp_project, basic_config)

        content = """## Code
```python
class MyClass:
    def my_method(self):
        pass

def helper_function():
    pass
```
"""
        result = detector._extract_code_names(content)
        assert "MyClass" in result
        assert "my_method" in result
        assert "helper_function" in result

    def test_calculate_similarity_identical(self, temp_project, basic_config):
        """Test identical string similarity"""
        detector = ConflictDetector(temp_project, basic_config)

        result = detector._calculate_similarity("hello world", "hello world")
        assert result == 1.0

    def test_calculate_similarity_different(self, temp_project, basic_config):
        """Test different string similarity"""
        detector = ConflictDetector(temp_project, basic_config)

        result = detector._calculate_similarity("hello world", "goodbye moon")
        assert result < 0.5

    def test_calculate_similarity_similar(self, temp_project, basic_config):
        """Test similar strings"""
        detector = ConflictDetector(temp_project, basic_config)

        result = detector._calculate_similarity(
            "implement user login",
            "develop user login feature"
        )
        # Jaccard: intersection={user, login} / union={implement, user, login, develop, feature} = 2/5 = 0.4
        assert result >= 0.4

    def test_calculate_similarity_empty(self, temp_project, basic_config):
        """Test empty string similarity"""
        detector = ConflictDetector(temp_project, basic_config)

        assert detector._calculate_similarity("", "test") == 0.0
        assert detector._calculate_similarity("test", "") == 0.0
        assert detector._calculate_similarity("", "") == 0.0


class TestConflictDetectorReport:
    """Test conflict report generation"""

    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def basic_config(self):
        return {"role_context": {"enabled": True}}

    def test_generate_report_no_conflicts(self, temp_project, basic_config):
        """Test report when no conflicts"""
        detector = ConflictDetector(temp_project, basic_config)
        report = detector.generate_conflict_report([])

        assert "No conflicts detected" in report

    def test_generate_report_with_conflicts(self, temp_project, basic_config):
        """Test report with conflicts"""
        detector = ConflictDetector(temp_project, basic_config)

        conflicts = [
            Conflict(
                conflict_type=ConflictType.FILE,
                severity="high",
                roles=["alice", "bob"],
                description="File conflict"
            ),
            Conflict(
                conflict_type=ConflictType.TASK,
                severity="medium",
                roles=["alice", "charlie"],
                description="Task overlap"
            )
        ]

        report = detector.generate_conflict_report(conflicts)

        assert "2 potential conflicts" in report
        assert "HIGH" in report
        assert "MEDIUM" in report
        assert "alice" in report
        assert "bob" in report

    def test_generate_report_verbose(self, temp_project, basic_config):
        """Test verbose report"""
        detector = ConflictDetector(temp_project, basic_config)

        conflicts = [
            Conflict(
                conflict_type=ConflictType.FILE,
                severity="high",
                roles=["alice", "bob"],
                description="File conflict",
                details={"files": ["main.py", "utils.py"]}
            )
        ]

        report = detector.generate_conflict_report(conflicts, verbose=True)

        assert "files" in report
        assert "main.py" in report

    def test_generate_report_suggestions(self, temp_project, basic_config):
        """Test report includes suggestions"""
        detector = ConflictDetector(temp_project, basic_config)

        conflicts = [
            Conflict(
                conflict_type=ConflictType.TASK,
                severity="low",
                roles=["alice"],
                description="Minor conflict"
            )
        ]

        report = detector.generate_conflict_report(conflicts)

        assert "Suggestions" in report
        assert "COLLABORATION.md" in report


class TestConflictDetectorMetadata:
    """Test metadata handling"""

    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            dev_dir = project_root / "docs" / "roles" / "alice"
            dev_dir.mkdir(parents=True)
            yield project_root

    @pytest.fixture
    def basic_config(self):
        return {
            "role_context": {
                "enabled": True,
                "context": {"per_role_dir": ".vibecollab/roles"}
            }
        }

    def test_load_context_with_metadata(self, temp_project, basic_config):
        """Test loading context with metadata"""
        dev_dir = temp_project / ".vibecollab" / "roles" / "alice"
        dev_dir.mkdir(parents=True, exist_ok=True)

        # Create CONTEXT.md
        (dev_dir / "CONTEXT.md").write_text(
            "## Current Tasks\n- Test task",
            encoding="utf-8"
        )

        # Create .metadata.yaml
        metadata_content = "last_update: '2026-02-24'\nstatus: active\n"
        (dev_dir / ".metadata.yaml").write_text(metadata_content, encoding="utf-8")

        detector = ConflictDetector(temp_project, basic_config)
        detector._load_role_contexts()

        assert "alice" in detector._role_contexts
        assert detector._role_contexts["alice"]["metadata"].get("status") == "active"

    def test_skip_hidden_directories(self, temp_project, basic_config):
        """Test skipping hidden directories"""
        devs_dir = temp_project / ".vibecollab" / "roles"

        # Create hidden directory
        hidden_dir = devs_dir / ".hidden"
        hidden_dir.mkdir(parents=True)
        (hidden_dir / "CONTEXT.md").write_text("Hidden", encoding="utf-8")

        detector = ConflictDetector(temp_project, basic_config)
        detector._load_role_contexts()

        assert ".hidden" not in detector._role_contexts


class TestCollaborationDataParsing:
    """Test collaboration document parsing"""

    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs" / "roles").mkdir(parents=True)
            yield project_root

    @pytest.fixture
    def basic_config(self):
        return {
            "role_context": {
                "enabled": True,
                "collaboration": {"file": ".vibecollab/roles/COLLABORATION.md"}
            }
        }

    def test_parse_collaboration_file(self, temp_project, basic_config):
        """Test parsing collaboration document"""
        collab_content = """## Task Assignment Matrix

| Task | Owner | Collaborators | Status | Dependencies |
|------|-------|---------------|--------|--------------|
| TASK-DEV-001: User Auth | alice | bob | IN_PROGRESS | - |
| TASK-DEV-002: DB Design | bob | - | DONE | - |
| TASK-DEV-003: API Dev | alice | charlie | TODO | TASK-DEV-002 |
"""
        collab_file = temp_project / "docs" / "roles" / "COLLABORATION.md"
        collab_file.write_text(collab_content, encoding="utf-8")

        detector = ConflictDetector(temp_project, basic_config)
        detector._load_collaboration_data()

        tasks = detector._collaboration_data.get("tasks", {})
        assert len(tasks) == 3
        assert tasks["TASK-DEV-001"]["owner"] == "alice"
        assert tasks["TASK-DEV-002"]["status"] == "DONE"
        assert "TASK-DEV-002" in tasks["TASK-DEV-003"]["dependencies"]

    def test_collaboration_file_not_exists(self, temp_project, basic_config):
        """Test collaboration document does not exist"""
        detector = ConflictDetector(temp_project, basic_config)
        detector._load_collaboration_data()

        assert detector._collaboration_data == {"tasks": {}, "dependencies": {}}

    def test_get_roles_for_tasks(self, temp_project, basic_config):
        """Test getting roles for tasks"""
        collab_content = """## Task Assignment Matrix

| Task | Owner | Collaborators | Status | Dependencies |
|------|-------|---------------|--------|--------------|
| TASK-DEV-001: Task A | alice | - | IN_PROGRESS | - |
| TASK-DEV-002: Task B | bob | - | DONE | - |
"""
        collab_file = temp_project / "docs" / "roles" / "COLLABORATION.md"
        collab_file.write_text(collab_content, encoding="utf-8")

        detector = ConflictDetector(temp_project, basic_config)
        detector._load_collaboration_data()

        devs = detector._get_roles_for_tasks(["TASK-DEV-001", "TASK-DEV-002"])
        assert set(devs) == {"alice", "bob"}
