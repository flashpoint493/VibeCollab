"""
PRDManager 模块单元测试

测试产品需求文档管理功能。
"""

# Import built-in modules
import tempfile
from datetime import datetime
from pathlib import Path

# Import third-party modules
import pytest

# Import local modules
from vibecollab.prd_manager import PRDManager, Requirement


# ============================================================================
# Test: Requirement dataclass
# ============================================================================

class TestRequirement:
    """测试 Requirement 数据类"""

    def test_init_defaults(self):
        """测试默认初始化"""
        req = Requirement(
            id="REQ-001",
            title="Test Requirement",
            original_description="Test description"
        )

        assert req.id == "REQ-001"
        assert req.title == "Test Requirement"
        assert req.original_description == "Test description"
        assert req.current_description == "Test description"  # 默认等于原始描述
        assert req.status == "draft"
        assert req.priority == "medium"
        assert req.changes == []
        assert req.created_at  # 自动生成
        assert req.updated_at  # 自动生成

    def test_init_with_explicit_values(self):
        """测试显式初始化"""
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
        """测试 __post_init__ 设置 current_description"""
        req = Requirement(
            id="REQ-003",
            title="Test",
            original_description="Original"
        )

        assert req.current_description == "Original"

    def test_post_init_sets_dates(self):
        """测试 __post_init__ 设置日期"""
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
    """测试 PRDManager 初始化"""

    def test_init_with_nonexistent_file(self):
        """测试文件不存在时的初始化"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "PRD.md"
            manager = PRDManager(prd_path)

            assert manager.prd_path == prd_path
            assert manager.requirements == {}

    def test_init_with_existing_markdown_file(self):
        """测试从现有 Markdown 文件初始化"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "PRD.md"
            prd_content = """# PRD

## REQ-001: Test Feature

**原始描述**:
> This is the original description

**状态**: confirmed
**优先级**: high
**创建时间**: 2026-01-15
**更新时间**: 2026-02-20
"""
            prd_path.write_text(prd_content, encoding="utf-8")

            manager = PRDManager(prd_path)

            assert "REQ-001" in manager.requirements
            req = manager.requirements["REQ-001"]
            assert req.title == "Test Feature"
            assert req.status == "confirmed"
            assert req.priority == "high"

    def test_init_markdown_parse_no_requirements(self):
        """测试 Markdown 解析无需求时返回空"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 有效的 Markdown 但没有 REQ- 格式的需求
            prd_path = Path(tmpdir) / "PRD.md"
            content = """# Some Document

This is just a regular markdown file without requirements.

## Section 1
Some content here.
"""
            prd_path.write_text(content, encoding="utf-8")

            manager = PRDManager(prd_path)

            # 应该成功加载但没有需求
            assert len(manager.requirements) == 0


# ============================================================================
# Test: PRDManager CRUD operations
# ============================================================================

class TestPRDManagerCRUD:
    """测试 PRDManager CRUD 操作"""

    @pytest.fixture
    def manager(self):
        """创建临时 PRDManager"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "PRD.md"
            yield PRDManager(prd_path)

    def test_add_requirement(self, manager):
        """测试添加需求"""
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
        """测试添加多个需求"""
        req1 = manager.add_requirement("Feature 1", "Desc 1")
        req2 = manager.add_requirement("Feature 2", "Desc 2")
        req3 = manager.add_requirement("Feature 3", "Desc 3")

        assert req1.id == "REQ-001"
        assert req2.id == "REQ-002"
        assert req3.id == "REQ-003"
        assert len(manager.requirements) == 3

    def test_get_requirement(self, manager):
        """测试获取需求"""
        manager.add_requirement("Test", "Description")

        req = manager.get_requirement("REQ-001")
        assert req is not None
        assert req.title == "Test"

    def test_get_nonexistent_requirement(self, manager):
        """测试获取不存在的需求"""
        req = manager.get_requirement("REQ-999")
        assert req is None

    def test_list_requirements(self, manager):
        """测试列出所有需求"""
        manager.add_requirement("Feature 1", "Desc 1")
        manager.add_requirement("Feature 2", "Desc 2")

        reqs = manager.list_requirements()
        assert len(reqs) == 2

    def test_list_requirements_by_status(self, manager):
        """测试按状态列出需求"""
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
    """测试 PRDManager 更新操作"""

    @pytest.fixture
    def manager_with_req(self):
        """创建带需求的 PRDManager"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "PRD.md"
            manager = PRDManager(prd_path)
            manager.add_requirement("Test Feature", "Original description")
            yield manager

    def test_update_requirement(self, manager_with_req):
        """测试更新需求"""
        manager = manager_with_req

        manager.update_requirement(
            "REQ-001",
            "Updated description",
            "Clarified requirements"
        )

        req = manager.get_requirement("REQ-001")
        assert req.current_description == "Updated description"
        assert req.original_description == "Original description"  # 原始描述不变
        assert len(req.changes) == 1
        assert req.changes[0]["reason"] == "Clarified requirements"

    def test_update_requirement_multiple_times(self, manager_with_req):
        """测试多次更新需求"""
        manager = manager_with_req

        manager.update_requirement("REQ-001", "Version 2", "First update")
        manager.update_requirement("REQ-001", "Version 3", "Second update")

        req = manager.get_requirement("REQ-001")
        assert req.current_description == "Version 3"
        assert len(req.changes) == 2

    def test_update_nonexistent_requirement(self, manager_with_req):
        """测试更新不存在的需求"""
        manager = manager_with_req

        with pytest.raises(ValueError, match="需求不存在"):
            manager.update_requirement("REQ-999", "New desc", "Reason")

    def test_set_status(self, manager_with_req):
        """测试设置状态"""
        manager = manager_with_req

        manager.set_status("REQ-001", "confirmed")

        req = manager.get_requirement("REQ-001")
        assert req.status == "confirmed"

    def test_set_status_nonexistent(self, manager_with_req):
        """测试设置不存在需求的状态"""
        manager = manager_with_req

        with pytest.raises(ValueError, match="需求不存在"):
            manager.set_status("REQ-999", "confirmed")

    def test_status_workflow(self, manager_with_req):
        """测试状态工作流"""
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
    """测试 PRDManager 持久化"""

    def test_save_and_load(self):
        """测试保存和加载"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "docs" / "PRD.md"

            # 创建并保存
            manager1 = PRDManager(prd_path)
            manager1.add_requirement("Feature A", "Description A", "high")
            manager1.add_requirement("Feature B", "Description B", "low")
            manager1.set_status("REQ-001", "confirmed")
            manager1.save()

            # 重新加载
            manager2 = PRDManager(prd_path)

            assert len(manager2.requirements) == 2
            assert "REQ-001" in manager2.requirements
            assert "REQ-002" in manager2.requirements

    def test_save_creates_directory(self):
        """测试保存时创建目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "nested" / "dir" / "PRD.md"

            manager = PRDManager(prd_path)
            manager.add_requirement("Test", "Desc")
            manager.save()

            assert prd_path.exists()
            assert prd_path.parent.exists()

    def test_save_with_changes_history(self):
        """测试保存包含变更历史的需求"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "PRD.md"

            manager = PRDManager(prd_path)
            manager.add_requirement("Feature", "Original")
            manager.update_requirement("REQ-001", "Updated", "Clarification")
            manager.save()

            # 验证文件内容
            content = prd_path.read_text(encoding="utf-8")
            assert "需求变化历史" in content
            assert "Clarification" in content


# ============================================================================
# Test: PRDManager markdown generation
# ============================================================================

class TestPRDManagerMarkdown:
    """测试 PRDManager Markdown 生成"""

    @pytest.fixture
    def manager(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "PRD.md"
            yield PRDManager(prd_path)

    def test_generate_markdown_empty(self, manager):
        """测试空 PRD 的 Markdown 生成"""
        content = manager._generate_markdown()

        assert "# 产品需求文档 (PRD)" in content
        assert "## 需求统计" in content

    def test_generate_markdown_with_requirements(self, manager):
        """测试带需求的 Markdown 生成"""
        manager.add_requirement("Feature A", "Description A", "high")
        manager.add_requirement("Feature B", "Description B", "low")

        content = manager._generate_markdown()

        assert "## REQ-001: Feature A" in content
        assert "## REQ-002: Feature B" in content
        assert "Description A" in content
        assert "Description B" in content

    def test_generate_markdown_status_table(self, manager):
        """测试状态统计表"""
        manager.add_requirement("F1", "D1")
        manager.add_requirement("F2", "D2")
        manager.set_status("REQ-001", "confirmed")

        content = manager._generate_markdown()

        assert "| 状态 | 数量 |" in content
        assert "| draft | 1 |" in content
        assert "| confirmed | 1 |" in content

    def test_generate_markdown_with_updated_description(self, manager):
        """测试包含更新描述的 Markdown"""
        manager.add_requirement("Feature", "Original description")
        manager.update_requirement("REQ-001", "New description", "Updated")

        content = manager._generate_markdown()

        assert "**原始描述**:" in content
        assert "Original description" in content
        assert "**当前描述**:" in content
        assert "New description" in content


# ============================================================================
# Test: PRDManager markdown parsing
# ============================================================================

class TestPRDManagerParsing:
    """测试 PRDManager Markdown 解析"""

    def test_parse_basic_requirement(self):
        """测试解析基本需求"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "PRD.md"
            content = """# PRD

## REQ-001: Basic Feature

> This is the description

**状态**: draft
**优先级**: medium
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
        """测试解析多个需求"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "PRD.md"
            content = """# PRD

## REQ-001: Feature A

> Description A

**状态**: confirmed

---

## REQ-002: Feature B

> Description B

**状态**: in_progress
"""
            prd_path.write_text(content, encoding="utf-8")

            manager = PRDManager(prd_path)

            assert len(manager.requirements) == 2
            assert manager.requirements["REQ-001"].status == "confirmed"
            assert manager.requirements["REQ-002"].status == "in_progress"

    def test_parse_requirement_with_dates(self):
        """测试解析带日期的需求"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "PRD.md"
            content = """# PRD

## REQ-001: Dated Feature

> Description

**状态**: draft
**优先级**: high
**创建时间**: 2026-01-15
**更新时间**: 2026-02-20
"""
            prd_path.write_text(content, encoding="utf-8")

            manager = PRDManager(prd_path)

            req = manager.requirements["REQ-001"]
            assert req.created_at == "2026-01-15"
            assert req.updated_at == "2026-02-20"

    def test_parse_empty_file(self):
        """测试解析空文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "PRD.md"
            prd_path.write_text("", encoding="utf-8")

            manager = PRDManager(prd_path)

            assert len(manager.requirements) == 0

    def test_parse_malformed_content(self):
        """测试解析格式错误的内容"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "PRD.md"
            content = """This is not a valid PRD format
Just some random text
Without proper structure
"""
            prd_path.write_text(content, encoding="utf-8")

            # 应该不抛出异常，只是没有解析到需求
            manager = PRDManager(prd_path)
            assert len(manager.requirements) == 0


# ============================================================================
# Test: PRDManager edge cases
# ============================================================================

class TestPRDManagerEdgeCases:
    """测试边界情况"""

    def test_requirement_with_special_characters(self):
        """测试包含特殊字符的需求"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "PRD.md"
            manager = PRDManager(prd_path)

            req = manager.add_requirement(
                "Feature with: colons & special <chars>",
                "Description with \"quotes\" and 'apostrophes'"
            )

            manager.save()

            # 重新加载验证
            manager2 = PRDManager(prd_path)
            assert "REQ-001" in manager2.requirements

    def test_requirement_with_unicode(self):
        """测试包含 Unicode 字符的需求"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "PRD.md"
            manager = PRDManager(prd_path)

            req = manager.add_requirement(
                "功能：用户认证 🔐",
                "实现用户登录和注册功能，支持多语言 🌍"
            )

            manager.save()

            # 重新加载验证
            manager2 = PRDManager(prd_path)
            assert "REQ-001" in manager2.requirements
            assert "用户认证" in manager2.requirements["REQ-001"].title

    def test_long_description(self):
        """测试长描述"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "PRD.md"
            manager = PRDManager(prd_path)

            long_desc = "This is a very long description. " * 100
            req = manager.add_requirement("Long Feature", long_desc)

            manager.save()

            # 验证保存成功
            assert prd_path.exists()
            content = prd_path.read_text(encoding="utf-8")
            assert "Long Feature" in content

    def test_update_preserves_original(self):
        """测试更新保留原始描述"""
        with tempfile.TemporaryDirectory() as tmpdir:
            prd_path = Path(tmpdir) / "PRD.md"
            manager = PRDManager(prd_path)

            manager.add_requirement("Feature", "Original")
            manager.update_requirement("REQ-001", "Update 1", "Reason 1")
            manager.update_requirement("REQ-001", "Update 2", "Reason 2")
            manager.update_requirement("REQ-001", "Update 3", "Reason 3")

            req = manager.get_requirement("REQ-001")

            # 原始描述应该保持不变
            assert req.original_description == "Original"
            # 当前描述应该是最新的
            assert req.current_description == "Update 3"
            # 应该有 3 条变更记录
            assert len(req.changes) == 3


# ============================================================================
# Test: PRDManager sorting
# ============================================================================

class TestPRDManagerSorting:
    """测试需求排序"""

    @pytest.fixture
    def manager_with_mixed_reqs(self):
        """创建带混合状态需求的 PRDManager"""
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
        """测试 Markdown 按状态和优先级排序"""
        manager = manager_with_mixed_reqs
        content = manager._generate_markdown()

        # 找到各需求在内容中的位置
        pos_draft_high = content.find("REQ-002")  # draft, high
        pos_draft_low = content.find("REQ-001")   # draft, low
        pos_confirmed = content.find("REQ-003")   # confirmed
        pos_in_progress = content.find("REQ-004") # in_progress

        # draft 应该在 confirmed 之前
        assert pos_draft_high < pos_confirmed
        # confirmed 应该在 in_progress 之前
        assert pos_confirmed < pos_in_progress
        # 同状态下，high 优先级在 low 之前
        assert pos_draft_high < pos_draft_low
