"""
PRDManager module unit tests

Tests for Product Requirements Document management functionality.
"""

# Import built-in modules
import tempfile
from datetime import datetime
from pathlib import Path

# Import third-party modules
import pytest

# Import local modules
from vibecollab.domain.prd_manager import PRDManager, Requirement

# ============================================================================
# Test: Requirement dataclass
# ============================================================================

class TestRequirement:
    """Test Requirement dataclass"""

    def test_init_defaults(self):
        """Test default initialization"""
        req = Requirement(
            id="REQ-001",
            title="Test Requirement",
            original_description="Test description"
        )

        assert req.id == "REQ-001"
        assert req.title == "Test Requirement"
        assert req.original_description == "Test description"
        assert req.current_description == "Test description"  # default equals original
        assert req.status == "draft"
        assert req.priority == "medium"
        assert req.changes == []
        assert req.created_at  # auto-generated
        assert req.updated_at  # auto-generated

    def test_init_with_explicit_values(self):
        """Test explicit initialization"""
        req = Requirement(
            id="REQ-002",
            title="Feature X",
            original_description="Original desc",
            current_description="Updated desc",
            status="confirmed",
            priority="high",
            created_at="2026-01-01",
            updated_at="2026-02-01",
            changes=[{"date": "2026-02-01", "reason": "Clarification"}]
        )

        assert req.id == "REQ-002"
        assert req.current_description == "Updated desc"
        assert req.status == "confirmed"
        assert req.priority == "high"
        assert req.created_at == "2026-01-01"
        assert req.updated_at == "2026-02-01"
        assert len(req.changes) == 1

    def test_post_init_sets_current_description(self):
        """Test __post_init__ sets current_description"""
        req = Requirement(
            id="REQ-003",
            title="Test",
            original_description="Original"
        )

        assert req.current_description == "Original"

    def test_post_init_sets_dates(self):
        """Test __post_init__ sets dates"""
        req = Requirement(
            id="REQ-004",
            title="Test",
            original_description="Desc"
        )

        today = datetime.now().strftime("%Y-%m-%d")
        assert req.created_at == today
        assert req.updated_at == today


# ============================================================================
# Test: PRDManager initialization
# ============================================================================

class TestPRDManagerInit:
    """Test PRDManager initialization"""

    def test_init_with_nonexistent_file(self):
        """Test initialization when file does not exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "PRD.md"
            manager = PRDManager(prd_path)

            assert manager.prd_path == prd_path
            assert manager.requirements == {}

    def test_init_with_existing_markdown_file(self):
        """Test initialization from existing Markdown file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "PRD.md"
            prd_content = """# PRD

## REQ-001: Test Feature

**Original Description**:
> This is the original description

**Status**: confirmed
**Priority**: high
**Created**: 2026-01-15
**Updated**: 2026-02-20
"""
            prd_path.write_text(prd_content, encoding="utf-8")

            manager = PRDManager(prd_path)

            assert "REQ-001" in manager.requirements
            req = manager.requirements["REQ-001"]
            assert req.title == "Test Feature"
            assert req.status == "confirmed"
            assert req.priority == "high"

    def test_init_markdown_parse_no_requirements(self):
        """Test Markdown parsing returns empty when no requirements"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Valid Markdown but no REQ- formatted requirements
            prd_path = Path(tmpdir) / "PRD.md"
            content = """# Some Document

This is just a regular markdown file without requirements.

## Section 1
Some content here.
"""
            prd_path.write_text(content, encoding="utf-8")

            manager = PRDManager(prd_path)

            # Should load successfully but with no requirements
            assert len(manager.requirements) == 0


# ============================================================================
# Test: PRDManager CRUD operations
# ============================================================================

class TestPRDManagerCRUD:
    """Test PRDManager CRUD operations"""

    @pytest.fixture
    def manager(self):
        """Create temporary PRDManager"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "PRD.md"
            yield PRDManager(prd_path)

    def test_add_requirement(self, manager):
        """Test adding requirement"""
        req = manager.add_requirement(
            title="New Feature",
            description="Feature description",
            priority="high"
        )

        assert req.id == "REQ-001"
        assert req.title == "New Feature"
        assert req.original_description == "Feature description"
        assert req.priority == "high"
        assert req.status == "draft"
        assert "REQ-001" in manager.requirements

    def test_add_multiple_requirements(self, manager):
        """Test adding multiple requirements"""
        req1 = manager.add_requirement("Feature 1", "Desc 1")
        req2 = manager.add_requirement("Feature 2", "Desc 2")
        req3 = manager.add_requirement("Feature 3", "Desc 3")

        assert req1.id == "REQ-001"
        assert req2.id == "REQ-002"
        assert req3.id == "REQ-003"
        assert len(manager.requirements) == 3

    def test_get_requirement(self, manager):
        """Test getting requirement"""
        manager.add_requirement("Test", "Description")

        req = manager.get_requirement("REQ-001")
        assert req is not None
        assert req.title == "Test"

    def test_get_nonexistent_requirement(self, manager):
        """Test getting non-existent requirement"""
        req = manager.get_requirement("REQ-999")
        assert req is None

    def test_list_requirements(self, manager):
        """Test listing all requirements"""
        manager.add_requirement("Feature 1", "Desc 1")
        manager.add_requirement("Feature 2", "Desc 2")

        reqs = manager.list_requirements()
        assert len(reqs) == 2

    def test_list_requirements_by_status(self, manager):
        """Test listing requirements by status"""
        manager.add_requirement("Feature 1", "Desc 1")
        manager.add_requirement("Feature 2", "Desc 2")
        manager.set_status("REQ-001", "confirmed")

        draft_reqs = manager.list_requirements(status="draft")
        confirmed_reqs = manager.list_requirements(status="confirmed")

        assert len(draft_reqs) == 1
        assert len(confirmed_reqs) == 1
        assert draft_reqs[0].id == "REQ-002"
        assert confirmed_reqs[0].id == "REQ-001"


# ============================================================================
# Test: PRDManager update operations
# ============================================================================

class TestPRDManagerUpdate:
    """Test PRDManager update operations"""

    @pytest.fixture
    def manager_with_req(self):
        """Create PRDManager with a requirement"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "PRD.md"
            manager = PRDManager(prd_path)
            manager.add_requirement("Test Feature", "Original description")
            yield manager

    def test_update_requirement(self, manager_with_req):
        """Test updating requirement"""
        manager = manager_with_req

        manager.update_requirement(
            "REQ-001",
            "Updated description",
            "Clarified requirements"
        )

        req = manager.get_requirement("REQ-001")
        assert req.current_description == "Updated description"
        assert req.original_description == "Original description"  # original unchanged
        assert len(req.changes) == 1
        assert req.changes[0]["reason"] == "Clarified requirements"

    def test_update_requirement_multiple_times(self, manager_with_req):
        """Test updating requirement multiple times"""
        manager = manager_with_req

        manager.update_requirement("REQ-001", "Version 2", "First update")
        manager.update_requirement("REQ-001", "Version 3", "Second update")

        req = manager.get_requirement("REQ-001")
        assert req.current_description == "Version 3"
        assert len(req.changes) == 2

    def test_update_nonexistent_requirement(self, manager_with_req):
        """Test updating non-existent requirement"""
        manager = manager_with_req

        with pytest.raises(ValueError, match="Requirement not found"):
            manager.update_requirement("REQ-999", "New desc", "Reason")

    def test_set_status(self, manager_with_req):
        """Test setting status"""
        manager = manager_with_req

        manager.set_status("REQ-001", "confirmed")

        req = manager.get_requirement("REQ-001")
        assert req.status == "confirmed"

    def test_set_status_nonexistent(self, manager_with_req):
        """Test setting status of non-existent requirement"""
        manager = manager_with_req

        with pytest.raises(ValueError, match="Requirement not found"):
            manager.set_status("REQ-999", "confirmed")

    def test_status_workflow(self, manager_with_req):
        """Test status workflow"""
        manager = manager_with_req

        # draft -> confirmed -> in_progress -> completed
        manager.set_status("REQ-001", "confirmed")
        assert manager.get_requirement("REQ-001").status == "confirmed"

        manager.set_status("REQ-001", "in_progress")
        assert manager.get_requirement("REQ-001").status == "in_progress"

        manager.set_status("REQ-001", "completed")
        assert manager.get_requirement("REQ-001").status == "completed"


# ============================================================================
# Test: PRDManager save and load
# ============================================================================

class TestPRDManagerPersistence:
    """Test PRDManager persistence"""

    def test_save_and_load(self):
        """Test save and load"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "docs" / "PRD.md"

            # Create and save
            manager1 = PRDManager(prd_path)
            manager1.add_requirement("Feature A", "Description A", "high")
            manager1.add_requirement("Feature B", "Description B", "low")
            manager1.set_status("REQ-001", "confirmed")
            manager1.save()

            # Reload
            manager2 = PRDManager(prd_path)

            assert len(manager2.requirements) == 2
            assert "REQ-001" in manager2.requirements
            assert "REQ-002" in manager2.requirements

    def test_save_creates_directory(self):
        """Test save creates directory (outputs YAML)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "nested" / "dir" / "PRD.md"

            manager = PRDManager(prd_path)
            manager.add_requirement("Test", "Desc")
            manager.save()

            # save() now outputs .yaml sibling
            yaml_path = prd_path.parent / "prd.yaml"
            assert yaml_path.exists()
            assert yaml_path.parent.exists()

    def test_save_with_changes_history(self):
        """Test saving requirement with change history (YAML output)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "PRD.md"

            manager = PRDManager(prd_path)
            manager.add_requirement("Feature", "Original")
            manager.update_requirement("REQ-001", "Updated", "Clarification")
            manager.save()

            # save() now outputs prd.yaml
            yaml_path = Path(tmpdir) / "prd.yaml"
            content = yaml_path.read_text(encoding="utf-8")
            assert "change_history" in content
            assert "Clarification" in content


# ============================================================================
# Test: PRDManager markdown generation
# ============================================================================

class TestPRDManagerMarkdown:
    """Test PRDManager Markdown generation"""

    @pytest.fixture
    def manager(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "PRD.md"
            yield PRDManager(prd_path)

    def test_generate_markdown_empty(self, manager):
        """Test Markdown generation for empty PRD"""
        content = manager._generate_markdown()

        assert "# Product Requirements Document (PRD)" in content
        assert "## Requirement Statistics" in content

    def test_generate_markdown_with_requirements(self, manager):
        """Test Markdown generation with requirements"""
        manager.add_requirement("Feature A", "Description A", "high")
        manager.add_requirement("Feature B", "Description B", "low")

        content = manager._generate_markdown()

        assert "## REQ-001: Feature A" in content
        assert "## REQ-002: Feature B" in content
        assert "Description A" in content
        assert "Description B" in content

    def test_generate_markdown_status_table(self, manager):
        """Test status statistics table"""
        manager.add_requirement("F1", "D1")
        manager.add_requirement("F2", "D2")
        manager.set_status("REQ-001", "confirmed")

        content = manager._generate_markdown()

        assert "| Status | Count |" in content
        assert "| draft | 1 |" in content
        assert "| confirmed | 1 |" in content

    def test_generate_markdown_with_updated_description(self, manager):
        """Test Markdown with updated description"""
        manager.add_requirement("Feature", "Original description")
        manager.update_requirement("REQ-001", "New description", "Updated")

        content = manager._generate_markdown()

        assert "**Original Description**:" in content
        assert "Original description" in content
        assert "**Current Description**:" in content
        assert "New description" in content


# ============================================================================
# Test: PRDManager markdown parsing
# ============================================================================

class TestPRDManagerParsing:
    """Test PRDManager Markdown parsing"""

    def test_parse_basic_requirement(self):
        """Test parsing basic requirement"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "PRD.md"
            content = """# PRD

## REQ-001: Basic Feature

> This is the description

**Status**: draft
**Priority**: medium
"""
            prd_path.write_text(content, encoding="utf-8")

            manager = PRDManager(prd_path)

            assert "REQ-001" in manager.requirements
            req = manager.requirements["REQ-001"]
            assert req.title == "Basic Feature"
            assert req.original_description == "This is the description"
            assert req.status == "draft"
            assert req.priority == "medium"

    def test_parse_multiple_requirements(self):
        """Test parsing multiple requirements"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "PRD.md"
            content = """# PRD

## REQ-001: Feature A

> Description A

**Status**: confirmed

---

## REQ-002: Feature B

> Description B

**Status**: in_progress
"""
            prd_path.write_text(content, encoding="utf-8")

            manager = PRDManager(prd_path)

            assert len(manager.requirements) == 2
            assert manager.requirements["REQ-001"].status == "confirmed"
            assert manager.requirements["REQ-002"].status == "in_progress"

    def test_parse_requirement_with_dates(self):
        """Test parsing requirement with dates"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "PRD.md"
            content = """# PRD

## REQ-001: Dated Feature

> Description

**Status**: draft
**Priority**: high
**Created**: 2026-01-15
**Updated**: 2026-02-20
"""
            prd_path.write_text(content, encoding="utf-8")

            manager = PRDManager(prd_path)

            req = manager.requirements["REQ-001"]
            assert req.created_at == "2026-01-15"
            assert req.updated_at == "2026-02-20"

    def test_parse_empty_file(self):
        """Test parsing empty file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "PRD.md"
            prd_path.write_text("", encoding="utf-8")

            manager = PRDManager(prd_path)

            assert len(manager.requirements) == 0

    def test_parse_malformed_content(self):
        """Test parsing malformed content"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "PRD.md"
            content = """This is not a valid PRD format
Just some random text
Without proper structure
"""
            prd_path.write_text(content, encoding="utf-8")

            # Should not throw exception, just no requirements parsed
            manager = PRDManager(prd_path)
            assert len(manager.requirements) == 0


# ============================================================================
# Test: PRDManager edge cases
# ============================================================================

class TestPRDManagerEdgeCases:
    """Test edge cases"""

    def test_requirement_with_special_characters(self):
        """Test requirement with special characters"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "PRD.md"
            manager = PRDManager(prd_path)

            manager.add_requirement(
                "Feature with: colons & special <chars>",
                "Description with \"quotes\" and 'apostrophes'"
            )

            manager.save()

            # Reload and verify
            manager2 = PRDManager(prd_path)
            assert "REQ-001" in manager2.requirements

    def test_requirement_with_unicode(self):
        """Test requirement with Unicode characters"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "PRD.md"
            manager = PRDManager(prd_path)

            manager.add_requirement(
                "Feature: User Auth",
                "Implement user login and registration with multi-language support"
            )

            manager.save()

            # Reload from yaml (save outputs prd.yaml)
            yaml_path = Path(tmpdir) / "prd.yaml"
            manager2 = PRDManager(yaml_path)
            assert "REQ-001" in manager2.requirements
            assert "User Auth" in manager2.requirements["REQ-001"].title

    def test_long_description(self):
        """Test long description"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "PRD.md"
            manager = PRDManager(prd_path)

            long_desc = "This is a very long description. " * 100
            manager.add_requirement("Long Feature", long_desc)

            manager.save()

            # save() now outputs prd.yaml
            yaml_path = Path(tmpdir) / "prd.yaml"
            assert yaml_path.exists()
            content = yaml_path.read_text(encoding="utf-8")
            assert "Long Feature" in content

    def test_update_preserves_original(self):
        """Test update preserves original description"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "PRD.md"
            manager = PRDManager(prd_path)

            manager.add_requirement("Feature", "Original")
            manager.update_requirement("REQ-001", "Update 1", "Reason 1")
            manager.update_requirement("REQ-001", "Update 2", "Reason 2")
            manager.update_requirement("REQ-001", "Update 3", "Reason 3")

            req = manager.get_requirement("REQ-001")

            # Original description should remain unchanged
            assert req.original_description == "Original"
            # Current description should be the latest
            assert req.current_description == "Update 3"
            # Should have 3 change records
            assert len(req.changes) == 3


# ============================================================================
# Test: PRDManager sorting
# ============================================================================

class TestPRDManagerSorting:
    """Test requirement sorting"""

    @pytest.fixture
    def manager_with_mixed_reqs(self):
        """Create PRDManager with mixed status requirements"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "PRD.md"
            manager = PRDManager(prd_path)

            manager.add_requirement("Draft Low", "Desc", "low")
            manager.add_requirement("Draft High", "Desc", "high")
            manager.add_requirement("Confirmed", "Desc", "medium")
            manager.add_requirement("In Progress", "Desc", "medium")

            manager.set_status("REQ-003", "confirmed")
            manager.set_status("REQ-004", "in_progress")

            yield manager

    def test_markdown_sorts_by_status_and_priority(self, manager_with_mixed_reqs):
        """Test Markdown sorts by status and priority"""
        manager = manager_with_mixed_reqs
        content = manager._generate_markdown()

        # Find position of each requirement in content
        pos_draft_high = content.find("REQ-002")  # draft, high
        pos_draft_low = content.find("REQ-001")   # draft, low
        pos_confirmed = content.find("REQ-003")   # confirmed
        pos_in_progress = content.find("REQ-004") # in_progress

        # draft should be before confirmed
        assert pos_draft_high < pos_confirmed
        # confirmed should be before in_progress
        assert pos_confirmed < pos_in_progress
        # Same status, high priority before low
        assert pos_draft_high < pos_draft_low
