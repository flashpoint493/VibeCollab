"""
ConflictDetector 模块单元测试

测试跨开发者冲突检测功能。
"""

# Import built-in modules
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

# Import third-party modules
import pytest

# Import local modules
from vibecollab.conflict_detector import (
    Conflict,
    ConflictDetector,
    ConflictType,
    is_windows_gbk,
)

# ============================================================================
# Test: is_windows_gbk
# ============================================================================

class TestIsWindowsGBK:
    """测试 Windows GBK 检测"""

    def test_non_windows_returns_false(self):
        """非 Windows 系统返回 False"""
        with patch("vibecollab.conflict_detector.platform.system", return_value="Linux"):
            result = is_windows_gbk()
            assert result is False

    def test_windows_with_utf8_returns_false(self):
        """Windows + UTF-8 编码返回 False"""
        with patch("vibecollab.conflict_detector.platform.system", return_value="Windows"):
            with patch("vibecollab.conflict_detector.sys.stdout") as mock_stdout:
                mock_stdout.encoding = "utf-8"
                result = is_windows_gbk()
                assert result is False

    def test_windows_with_gbk_returns_true(self):
        """Windows + GBK 编码返回 True"""
        with patch("vibecollab.conflict_detector.platform.system", return_value="Windows"):
            with patch("vibecollab.conflict_detector.sys.stdout") as mock_stdout:
                mock_stdout.encoding = "gbk"
                result = is_windows_gbk()
                assert result is True


# ============================================================================
# Test: ConflictType
# ============================================================================

class TestConflictType:
    """测试 ConflictType 枚举"""

    def test_conflict_types(self):
        """验证冲突类型定义"""
        assert ConflictType.FILE == "file"
        assert ConflictType.TASK == "task"
        assert ConflictType.DEPENDENCY == "dependency"
        assert ConflictType.NAMING == "naming"


# ============================================================================
# Test: Conflict
# ============================================================================

class TestConflict:
    """测试 Conflict 类"""

    def test_init_defaults(self):
        """测试默认初始化"""
        conflict = Conflict(
            conflict_type=ConflictType.FILE,
            severity="high",
            developers=["alice", "bob"],
            description="Test conflict"
        )

        assert conflict.type == "file"
        assert conflict.severity == "high"
        assert conflict.developers == ["alice", "bob"]
        assert conflict.description == "Test conflict"
        assert conflict.details == {}
        assert isinstance(conflict.detected_at, datetime)

    def test_init_with_details(self):
        """测试带详情的初始化"""
        details = {"files": ["test.py", "main.py"]}
        conflict = Conflict(
            conflict_type=ConflictType.FILE,
            severity="medium",
            developers=["alice"],
            description="File conflict",
            details=details
        )

        assert conflict.details == details

    def test_to_dict(self):
        """测试转字典"""
        conflict = Conflict(
            conflict_type=ConflictType.TASK,
            severity="high",
            developers=["alice", "bob"],
            description="Task conflict",
            details={"task_id": "TASK-001"}
        )

        result = conflict.to_dict()

        assert result["type"] == "task"
        assert result["severity"] == "high"
        assert result["developers"] == ["alice", "bob"]
        assert result["description"] == "Task conflict"
        assert result["details"] == {"task_id": "TASK-001"}
        assert "detected_at" in result

    def test_str_representation(self):
        """测试字符串表示"""
        conflict = Conflict(
            conflict_type=ConflictType.DEPENDENCY,
            severity="medium",
            developers=["alice", "bob"],
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
    """测试 ConflictDetector 类"""

    @pytest.fixture
    def temp_project(self):
        """创建临时项目目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            developers_dir = project_root / "docs" / "developers"
            developers_dir.mkdir(parents=True)
            yield project_root

    @pytest.fixture
    def basic_config(self):
        """基础配置"""
        return {
            "multi_developer": {
                "enabled": True,
                "context": {
                    "per_developer_dir": "docs/developers"
                },
                "collaboration": {
                    "file": "docs/developers/COLLABORATION.md"
                }
            }
        }

    def test_init(self, temp_project, basic_config):
        """测试初始化"""
        detector = ConflictDetector(temp_project, basic_config)

        assert detector.project_root == temp_project
        assert detector.config == basic_config
        assert detector.developers_dir == temp_project / "docs" / "developers"

    def test_detect_all_conflicts_empty_project(self, temp_project, basic_config):
        """空项目不应有冲突"""
        detector = ConflictDetector(temp_project, basic_config)
        conflicts = detector.detect_all_conflicts()

        assert conflicts == []

    def test_detect_all_conflicts_with_target_developer(self, temp_project, basic_config):
        """测试针对特定开发者的冲突检测"""
        # 创建开发者目录和上下文
        alice_dir = temp_project / "docs" / "developers" / "alice"
        alice_dir.mkdir(parents=True)
        (alice_dir / "CONTEXT.md").write_text("## 当前任务\n- Task 1", encoding="utf-8")

        detector = ConflictDetector(temp_project, basic_config)
        conflicts = detector.detect_all_conflicts(target_developer="alice")

        # 只有一个开发者，不应有冲突
        assert conflicts == []

    def test_detect_all_conflicts_nonexistent_developer(self, temp_project, basic_config):
        """测试不存在的开发者"""
        detector = ConflictDetector(temp_project, basic_config)
        conflicts = detector.detect_all_conflicts(target_developer="nonexistent")

        assert conflicts == []

    def test_detect_all_conflicts_between_developers(self, temp_project, basic_config):
        """测试两个开发者之间的冲突检测"""
        # 创建两个开发者目录
        for dev in ["alice", "bob"]:
            dev_dir = temp_project / "docs" / "developers" / dev
            dev_dir.mkdir(parents=True)
            (dev_dir / "CONTEXT.md").write_text(
                f"## 当前任务\n- {dev} task",
                encoding="utf-8"
            )

        detector = ConflictDetector(temp_project, basic_config)
        conflicts = detector.detect_all_conflicts(between_developers=("alice", "bob"))

        # 任务不相似，不应有任务冲突
        assert isinstance(conflicts, list)


class TestConflictDetectorFileConflicts:
    """测试文件冲突检测"""

    @pytest.fixture
    def temp_project_with_devs(self):
        """创建带开发者的临时项目"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            developers_dir = project_root / "docs" / "developers"

            for dev in ["alice", "bob"]:
                dev_dir = developers_dir / dev
                dev_dir.mkdir(parents=True)

            yield project_root

    @pytest.fixture
    def basic_config(self):
        return {
            "multi_developer": {
                "enabled": True,
                "context": {"per_developer_dir": "docs/developers"},
                "collaboration": {"file": "docs/developers/COLLABORATION.md"}
            }
        }

    def test_detect_file_conflicts_common_files(self, temp_project_with_devs, basic_config):
        """测试检测共同修改的文件"""
        project = temp_project_with_devs

        # Alice 修改了 main.py
        alice_ctx = "## 最近完成\n- 修改了 `main.py` 和 `utils.py`"
        (project / "docs" / "developers" / "alice" / "CONTEXT.md").write_text(
            alice_ctx, encoding="utf-8"
        )

        # Bob 也修改了 main.py
        bob_ctx = "## 最近完成\n- 更新了 `main.py` 和 `config.py`"
        (project / "docs" / "developers" / "bob" / "CONTEXT.md").write_text(
            bob_ctx, encoding="utf-8"
        )

        detector = ConflictDetector(project, basic_config)
        conflicts = detector.detect_all_conflicts()

        # 应该检测到 main.py 的文件冲突
        file_conflicts = [c for c in conflicts if c.type == ConflictType.FILE]
        assert len(file_conflicts) == 1
        assert "main.py" in file_conflicts[0].details.get("files", [])

    def test_detect_file_conflicts_no_common_files(self, temp_project_with_devs, basic_config):
        """测试无共同修改文件时不应有冲突"""
        project = temp_project_with_devs

        (project / "docs" / "developers" / "alice" / "CONTEXT.md").write_text(
            "## 最近完成\n- 修改了 `alice.py`", encoding="utf-8"
        )
        (project / "docs" / "developers" / "bob" / "CONTEXT.md").write_text(
            "## 最近完成\n- 修改了 `bob.py`", encoding="utf-8"
        )

        detector = ConflictDetector(project, basic_config)
        conflicts = detector.detect_all_conflicts()

        file_conflicts = [c for c in conflicts if c.type == ConflictType.FILE]
        assert len(file_conflicts) == 0


class TestConflictDetectorTaskConflicts:
    """测试任务冲突检测"""

    @pytest.fixture
    def temp_project_with_devs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            for dev in ["alice", "bob"]:
                dev_dir = project_root / "docs" / "developers" / dev
                dev_dir.mkdir(parents=True)
            yield project_root

    @pytest.fixture
    def basic_config(self):
        return {
            "multi_developer": {
                "enabled": True,
                "context": {"per_developer_dir": "docs/developers"},
                "collaboration": {"file": "docs/developers/COLLABORATION.md"}
            }
        }

    def test_detect_similar_tasks(self, temp_project_with_devs, basic_config):
        """测试检测相似任务"""
        project = temp_project_with_devs

        # 两人的任务非常相似 (使用英文确保 \w+ 分词正常，超过 60% 阈值)
        # Jaccard: {user, login, auth, module} / {implement, user, login, auth, module, develop} = 4/6 = 0.67
        (project / "docs" / "developers" / "alice" / "CONTEXT.md").write_text(
            "## 当前任务\n- implement user login auth module", encoding="utf-8"
        )
        (project / "docs" / "developers" / "bob" / "CONTEXT.md").write_text(
            "## 当前任务\n- develop user login auth module", encoding="utf-8"
        )

        detector = ConflictDetector(project, basic_config)
        conflicts = detector.detect_all_conflicts()

        task_conflicts = [c for c in conflicts if c.type == ConflictType.TASK]
        assert len(task_conflicts) == 1
        assert task_conflicts[0].severity == "high"

    def test_detect_different_tasks(self, temp_project_with_devs, basic_config):
        """测试不同任务不应有冲突"""
        project = temp_project_with_devs

        # 使用英文，确保分词正常
        (project / "docs" / "developers" / "alice" / "CONTEXT.md").write_text(
            "## 当前任务\n- implement user authentication", encoding="utf-8"
        )
        (project / "docs" / "developers" / "bob" / "CONTEXT.md").write_text(
            "## 当前任务\n- optimize database query performance", encoding="utf-8"
        )

        detector = ConflictDetector(project, basic_config)
        conflicts = detector.detect_all_conflicts()

        task_conflicts = [c for c in conflicts if c.type == ConflictType.TASK]
        assert len(task_conflicts) == 0


class TestConflictDetectorDependencyConflicts:
    """测试依赖冲突检测"""

    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs" / "developers").mkdir(parents=True)
            yield project_root

    @pytest.fixture
    def basic_config(self):
        return {
            "multi_developer": {
                "enabled": True,
                "context": {"per_developer_dir": "docs/developers"},
                "collaboration": {"file": "docs/developers/COLLABORATION.md"}
            }
        }

    def test_detect_circular_dependency(self, temp_project, basic_config):
        """测试检测循环依赖"""
        collab_content = """## 任务分配矩阵

| 任务 | 负责人 | 协作者 | 状态 | 依赖 |
|------|--------|--------|------|------|
| TASK-DEV-001: 功能A | alice | - | IN_PROGRESS | TASK-DEV-002 |
| TASK-DEV-002: 功能B | bob | - | IN_PROGRESS | TASK-DEV-001 |
"""
        collab_file = temp_project / "docs" / "developers" / "COLLABORATION.md"
        collab_file.write_text(collab_content, encoding="utf-8")

        detector = ConflictDetector(temp_project, basic_config)
        conflicts = detector.detect_all_conflicts()

        dep_conflicts = [c for c in conflicts if c.type == ConflictType.DEPENDENCY]
        assert len(dep_conflicts) == 1
        assert dep_conflicts[0].severity == "high"
        assert "循环依赖" in dep_conflicts[0].description

    def test_no_circular_dependency(self, temp_project, basic_config):
        """测试无循环依赖时不应有冲突"""
        collab_content = """## 任务分配矩阵

| 任务 | 负责人 | 协作者 | 状态 | 依赖 |
|------|--------|--------|------|------|
| TASK-DEV-001: 功能A | alice | - | IN_PROGRESS | - |
| TASK-DEV-002: 功能B | bob | - | IN_PROGRESS | TASK-DEV-001 |
"""
        collab_file = temp_project / "docs" / "developers" / "COLLABORATION.md"
        collab_file.write_text(collab_content, encoding="utf-8")

        detector = ConflictDetector(temp_project, basic_config)
        conflicts = detector.detect_all_conflicts()

        dep_conflicts = [c for c in conflicts if c.type == ConflictType.DEPENDENCY]
        assert len(dep_conflicts) == 0


class TestConflictDetectorNamingConflicts:
    """测试命名冲突检测"""

    @pytest.fixture
    def temp_project_with_devs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            for dev in ["alice", "bob"]:
                dev_dir = project_root / "docs" / "developers" / dev
                dev_dir.mkdir(parents=True)
            yield project_root

    @pytest.fixture
    def basic_config(self):
        return {
            "multi_developer": {
                "enabled": True,
                "context": {"per_developer_dir": "docs/developers"},
                "collaboration": {"file": "docs/developers/COLLABORATION.md"}
            }
        }

    def test_detect_naming_conflict_class(self, temp_project_with_devs, basic_config):
        """测试检测类名冲突"""
        project = temp_project_with_devs

        alice_ctx = """## 最近完成
```python
class UserManager:
    pass
```
"""
        bob_ctx = """## 最近完成
```python
class UserManager:
    def login(self):
        pass
```
"""
        (project / "docs" / "developers" / "alice" / "CONTEXT.md").write_text(
            alice_ctx, encoding="utf-8"
        )
        (project / "docs" / "developers" / "bob" / "CONTEXT.md").write_text(
            bob_ctx, encoding="utf-8"
        )

        detector = ConflictDetector(project, basic_config)
        conflicts = detector.detect_all_conflicts()

        naming_conflicts = [c for c in conflicts if c.type == ConflictType.NAMING]
        assert len(naming_conflicts) == 1
        assert "UserManager" in naming_conflicts[0].details.get("names", [])

    def test_detect_naming_conflict_function(self, temp_project_with_devs, basic_config):
        """测试检测函数名冲突"""
        project = temp_project_with_devs

        alice_ctx = """## 最近完成
```python
def process_data():
    pass
```
"""
        bob_ctx = """## 最近完成
```python
def process_data(data):
    return data
```
"""
        (project / "docs" / "developers" / "alice" / "CONTEXT.md").write_text(
            alice_ctx, encoding="utf-8"
        )
        (project / "docs" / "developers" / "bob" / "CONTEXT.md").write_text(
            bob_ctx, encoding="utf-8"
        )

        detector = ConflictDetector(project, basic_config)
        conflicts = detector.detect_all_conflicts()

        naming_conflicts = [c for c in conflicts if c.type == ConflictType.NAMING]
        assert len(naming_conflicts) == 1
        assert "process_data" in naming_conflicts[0].details.get("names", [])


class TestConflictDetectorHelpers:
    """测试辅助方法"""

    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def basic_config(self):
        return {"multi_developer": {"enabled": True}}

    def test_extract_section_content(self, temp_project, basic_config):
        """测试章节内容提取"""
        detector = ConflictDetector(temp_project, basic_config)

        content = """## 当前任务
- Task 1
- Task 2

## 最近完成
- Done 1
"""
        result = detector._extract_section_content(content, "当前任务")
        assert "Task 1" in result
        assert "Task 2" in result
        assert "Done 1" not in result

    def test_extract_section_content_not_found(self, temp_project, basic_config):
        """测试章节不存在时返回空"""
        detector = ConflictDetector(temp_project, basic_config)

        content = "## 其他章节\n内容"
        result = detector._extract_section_content(content, "不存在的章节")
        assert result == ""

    def test_extract_current_tasks(self, temp_project, basic_config):
        """测试当前任务提取"""
        detector = ConflictDetector(temp_project, basic_config)

        content = """## 当前任务
- 实现功能A
- 修复Bug B
* 优化性能
"""
        result = detector._extract_current_tasks(content)
        assert "实现功能A" in result
        assert "修复Bug B" in result
        assert "优化性能" in result

    def test_extract_code_names(self, temp_project, basic_config):
        """测试代码命名提取"""
        detector = ConflictDetector(temp_project, basic_config)

        content = """## 代码
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
        """测试相同字符串相似度"""
        detector = ConflictDetector(temp_project, basic_config)

        result = detector._calculate_similarity("hello world", "hello world")
        assert result == 1.0

    def test_calculate_similarity_different(self, temp_project, basic_config):
        """测试不同字符串相似度"""
        detector = ConflictDetector(temp_project, basic_config)

        result = detector._calculate_similarity("hello world", "goodbye moon")
        assert result < 0.5

    def test_calculate_similarity_similar(self, temp_project, basic_config):
        """测试相似字符串"""
        detector = ConflictDetector(temp_project, basic_config)

        result = detector._calculate_similarity(
            "implement user login",
            "develop user login feature"
        )
        # Jaccard: intersection={user, login} / union={implement, user, login, develop, feature} = 2/5 = 0.4
        assert result >= 0.4

    def test_calculate_similarity_empty(self, temp_project, basic_config):
        """测试空字符串相似度"""
        detector = ConflictDetector(temp_project, basic_config)

        assert detector._calculate_similarity("", "test") == 0.0
        assert detector._calculate_similarity("test", "") == 0.0
        assert detector._calculate_similarity("", "") == 0.0


class TestConflictDetectorReport:
    """测试冲突报告生成"""

    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def basic_config(self):
        return {"multi_developer": {"enabled": True}}

    def test_generate_report_no_conflicts(self, temp_project, basic_config):
        """测试无冲突时的报告"""
        detector = ConflictDetector(temp_project, basic_config)
        report = detector.generate_conflict_report([])

        assert "未检测到冲突" in report

    def test_generate_report_with_conflicts(self, temp_project, basic_config):
        """测试有冲突时的报告"""
        detector = ConflictDetector(temp_project, basic_config)

        conflicts = [
            Conflict(
                conflict_type=ConflictType.FILE,
                severity="high",
                developers=["alice", "bob"],
                description="File conflict"
            ),
            Conflict(
                conflict_type=ConflictType.TASK,
                severity="medium",
                developers=["alice", "charlie"],
                description="Task overlap"
            )
        ]

        report = detector.generate_conflict_report(conflicts)

        assert "2 个潜在冲突" in report
        assert "HIGH" in report
        assert "MEDIUM" in report
        assert "alice" in report
        assert "bob" in report

    def test_generate_report_verbose(self, temp_project, basic_config):
        """测试详细报告"""
        detector = ConflictDetector(temp_project, basic_config)

        conflicts = [
            Conflict(
                conflict_type=ConflictType.FILE,
                severity="high",
                developers=["alice", "bob"],
                description="File conflict",
                details={"files": ["main.py", "utils.py"]}
            )
        ]

        report = detector.generate_conflict_report(conflicts, verbose=True)

        assert "files" in report
        assert "main.py" in report

    def test_generate_report_suggestions(self, temp_project, basic_config):
        """测试报告包含建议"""
        detector = ConflictDetector(temp_project, basic_config)

        conflicts = [
            Conflict(
                conflict_type=ConflictType.TASK,
                severity="low",
                developers=["alice"],
                description="Minor conflict"
            )
        ]

        report = detector.generate_conflict_report(conflicts)

        assert "建议" in report
        assert "COLLABORATION.md" in report


class TestConflictDetectorMetadata:
    """测试元数据处理"""

    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            dev_dir = project_root / "docs" / "developers" / "alice"
            dev_dir.mkdir(parents=True)
            yield project_root

    @pytest.fixture
    def basic_config(self):
        return {
            "multi_developer": {
                "enabled": True,
                "context": {"per_developer_dir": "docs/developers"}
            }
        }

    def test_load_context_with_metadata(self, temp_project, basic_config):
        """测试加载带元数据的上下文"""
        dev_dir = temp_project / "docs" / "developers" / "alice"

        # 创建 CONTEXT.md
        (dev_dir / "CONTEXT.md").write_text(
            "## 当前任务\n- Test task",
            encoding="utf-8"
        )

        # 创建 .metadata.yaml
        metadata_content = "last_update: '2026-02-24'\nstatus: active\n"
        (dev_dir / ".metadata.yaml").write_text(metadata_content, encoding="utf-8")

        detector = ConflictDetector(temp_project, basic_config)
        detector._load_developer_contexts()

        assert "alice" in detector._developer_contexts
        assert detector._developer_contexts["alice"]["metadata"].get("status") == "active"

    def test_skip_hidden_directories(self, temp_project, basic_config):
        """测试跳过隐藏目录"""
        devs_dir = temp_project / "docs" / "developers"

        # 创建隐藏目录
        hidden_dir = devs_dir / ".hidden"
        hidden_dir.mkdir(parents=True)
        (hidden_dir / "CONTEXT.md").write_text("Hidden", encoding="utf-8")

        detector = ConflictDetector(temp_project, basic_config)
        detector._load_developer_contexts()

        assert ".hidden" not in detector._developer_contexts


class TestCollaborationDataParsing:
    """测试协作文档解析"""

    @pytest.fixture
    def temp_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs" / "developers").mkdir(parents=True)
            yield project_root

    @pytest.fixture
    def basic_config(self):
        return {
            "multi_developer": {
                "enabled": True,
                "collaboration": {"file": "docs/developers/COLLABORATION.md"}
            }
        }

    def test_parse_collaboration_file(self, temp_project, basic_config):
        """测试解析协作文档"""
        collab_content = """## 任务分配矩阵

| 任务 | 负责人 | 协作者 | 状态 | 依赖 |
|------|--------|--------|------|------|
| TASK-DEV-001: 用户认证 | alice | bob | IN_PROGRESS | - |
| TASK-DEV-002: 数据库设计 | bob | - | DONE | - |
| TASK-DEV-003: API开发 | alice | charlie | TODO | TASK-DEV-002 |
"""
        collab_file = temp_project / "docs" / "developers" / "COLLABORATION.md"
        collab_file.write_text(collab_content, encoding="utf-8")

        detector = ConflictDetector(temp_project, basic_config)
        detector._load_collaboration_data()

        tasks = detector._collaboration_data.get("tasks", {})
        assert len(tasks) == 3
        assert tasks["TASK-DEV-001"]["owner"] == "alice"
        assert tasks["TASK-DEV-002"]["status"] == "DONE"
        assert "TASK-DEV-002" in tasks["TASK-DEV-003"]["dependencies"]

    def test_collaboration_file_not_exists(self, temp_project, basic_config):
        """测试协作文档不存在"""
        detector = ConflictDetector(temp_project, basic_config)
        detector._load_collaboration_data()

        assert detector._collaboration_data == {"tasks": {}, "dependencies": {}}

    def test_get_developers_for_tasks(self, temp_project, basic_config):
        """测试获取任务对应的开发者"""
        collab_content = """## 任务分配矩阵

| 任务 | 负责人 | 协作者 | 状态 | 依赖 |
|------|--------|--------|------|------|
| TASK-DEV-001: 任务A | alice | - | IN_PROGRESS | - |
| TASK-DEV-002: 任务B | bob | - | DONE | - |
"""
        collab_file = temp_project / "docs" / "developers" / "COLLABORATION.md"
        collab_file.write_text(collab_content, encoding="utf-8")

        detector = ConflictDetector(temp_project, basic_config)
        detector._load_collaboration_data()

        devs = detector._get_developers_for_tasks(["TASK-DEV-001", "TASK-DEV-002"])
        assert set(devs) == {"alice", "bob"}
