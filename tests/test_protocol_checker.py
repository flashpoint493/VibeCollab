"""
Tests for Protocol Checker
"""

import pytest
from pathlib import Path
import tempfile
import yaml

from vibecollab.protocol_checker import ProtocolChecker, CheckResult


class TestProtocolChecker:
    """协议检查器测试"""

    def test_check_collaboration_missing(self):
        """测试检测缺失的 COLLABORATION.md"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            # 创建基本目录结构
            docs_dir = project_root / "docs" / "developers"
            docs_dir.mkdir(parents=True)
            
            # 配置多开发者模式
            config = {
                "multi_developer": {
                    "enabled": True,
                    "collaboration": {
                        "file": "docs/developers/COLLABORATION.md"
                    }
                },
                "dialogue_protocol": {
                    "on_end": {
                        "update_files": []
                    },
                    "on_start": {
                        "read_files": []
                    }
                }
            }
            
            checker = ProtocolChecker(project_root, config)
            results = checker.check_all()
            
            # 应该有一个警告：缺少 COLLABORATION.md
            collab_check = [r for r in results if "协作文档" in r.name]
            assert len(collab_check) > 0
            assert collab_check[0].severity == "warning"
            assert not collab_check[0].passed

    def test_check_collaboration_exists(self):
        """测试检测存在的 COLLABORATION.md"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            # 创建 COLLABORATION.md
            collab_file = project_root / "docs" / "developers" / "COLLABORATION.md"
            collab_file.parent.mkdir(parents=True)
            collab_file.write_text("# Collaboration\n", encoding="utf-8")
            
            config = {
                "multi_developer": {
                    "enabled": True,
                    "collaboration": {
                        "file": "docs/developers/COLLABORATION.md"
                    }
                },
                "dialogue_protocol": {
                    "on_end": {
                        "update_files": []
                    },
                    "on_start": {
                        "read_files": []
                    }
                }
            }
            
            checker = ProtocolChecker(project_root, config)
            results = checker.check_all()
            
            # 不应该有缺失协作文档的错误
            collab_errors = [r for r in results 
                           if "协作文档" in r.name 
                           and r.severity == "warning" 
                           and not r.passed]
            assert len(collab_errors) == 0

    def test_check_collaboration_disabled(self):
        """测试多开发者模式禁用时不检查 COLLABORATION.md"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            config = {
                "multi_developer": {
                    "enabled": False
                },
                "dialogue_protocol": {
                    "on_end": {
                        "update_files": []
                    },
                    "on_start": {
                        "read_files": []
                    }
                }
            }
            
            checker = ProtocolChecker(project_root, config)
            results = checker.check_all()
            
            # 不应该有协作文档检查
            collab_check = [r for r in results if "协作文档" in r.name]
            assert len(collab_check) == 0

    def test_check_result_structure(self):
        """测试 CheckResult 数据结构"""
        result = CheckResult(
            name="Test Check",
            passed=True,
            message="Test message",
            severity="info",
            suggestion="Test suggestion"
        )
        
        assert result.name == "Test Check"
        assert result.passed is True
        assert result.message == "Test message"
        assert result.severity == "info"
        assert result.suggestion == "Test suggestion"

    def test_get_summary(self):
        """测试检查结果摘要"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            config = {"dialogue_protocol": {"on_end": {"update_files": []}, "on_start": {"read_files": []}}}
            checker = ProtocolChecker(project_root, config)
            
            results = [
                CheckResult("Test 1", True, "msg", "info"),
                CheckResult("Test 2", False, "msg", "error"),
                CheckResult("Test 3", False, "msg", "warning"),
            ]
            
            summary = checker.get_summary(results)
            
            assert summary["total"] == 3
            assert summary["passed"] == 1
            assert summary["errors"] == 1
            assert summary["warnings"] == 1
            assert summary["infos"] == 1
            assert summary["all_passed"] is False

    def test_check_developer_contexts(self):
        """测试检查开发者上下文文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            # 配置多开发者
            config = {
                "multi_developer": {
                    "enabled": True,
                    "developers": [
                        {"id": "alice", "name": "Alice", "role": "backend"},
                        {"id": "bob", "name": "Bob", "role": "frontend"}
                    ],
                    "collaboration": {
                        "file": "docs/developers/COLLABORATION.md"
                    }
                },
                "dialogue_protocol": {
                    "on_end": {"update_files": []},
                    "on_start": {"read_files": []}
                }
            }
            
            # 只创建 alice 的上下文
            alice_dir = project_root / "docs" / "developers" / "alice"
            alice_dir.mkdir(parents=True)
            (alice_dir / "CONTEXT.md").write_text("# Alice Context\n", encoding="utf-8")
            (alice_dir / ".metadata.yaml").write_text("role: backend\n", encoding="utf-8")
            
            checker = ProtocolChecker(project_root, config)
            results = checker.check_all()
            
            # 应该检测到 bob 缺少目录和文件
            bob_checks = [r for r in results if "Bob" in r.message or "bob" in r.message]
            assert len(bob_checks) > 0
            
            # 应该检测到 alice 的文件存在
            alice_context_checks = [r for r in results 
                                   if "Alice" in r.message and "CONTEXT.md" in r.message]
            assert any(r.passed for r in alice_context_checks)

    def test_check_developer_missing_id(self):
        """测试检查开发者缺少 ID"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            config = {
                "multi_developer": {
                    "enabled": True,
                    "developers": [
                        {"name": "Alice"}  # 缺少 id
                    ]
                },
                "dialogue_protocol": {
                    "on_end": {"update_files": []},
                    "on_start": {"read_files": []}
                }
            }
            
            checker = ProtocolChecker(project_root, config)
            results = checker.check_all()
            
            # 应该有开发者ID错误
            id_errors = [r for r in results if "开发者ID" in r.name]
            assert len(id_errors) > 0
            assert id_errors[0].severity == "error"

    def test_check_developer_no_developers(self):
        """测试多开发者模式启用但无开发者配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            config = {
                "multi_developer": {
                    "enabled": True,
                    "developers": []  # 空列表
                },
                "dialogue_protocol": {
                    "on_end": {"update_files": []},
                    "on_start": {"read_files": []}
                }
            }
            
            checker = ProtocolChecker(project_root, config)
            results = checker.check_all()
            
            # 应该有配置错误
            config_errors = [r for r in results if "开发者配置" in r.name]
            assert len(config_errors) > 0
            assert config_errors[0].severity == "error"

    def test_check_conflict_detection_disabled(self):
        """测试冲突检测禁用时的警告"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            # 创建开发者目录
            alice_dir = project_root / "docs" / "developers" / "alice"
            alice_dir.mkdir(parents=True)
            (alice_dir / "CONTEXT.md").write_text("# Alice\n", encoding="utf-8")
            
            config = {
                "multi_developer": {
                    "enabled": True,
                    "developers": [{"id": "alice", "name": "Alice"}],
                    "conflict_detection": {
                        "enabled": False  # 禁用冲突检测
                    },
                    "collaboration": {
                        "file": "docs/developers/COLLABORATION.md"
                    }
                },
                "dialogue_protocol": {
                    "on_end": {"update_files": []},
                    "on_start": {"read_files": []}
                }
            }
            
            # 创建协作文档
            collab_file = project_root / "docs" / "developers" / "COLLABORATION.md"
            collab_file.write_text("# Collab\n", encoding="utf-8")
            
            checker = ProtocolChecker(project_root, config)
            results = checker.check_all()
            
            # 应该有冲突检测警告
            conflict_warnings = [r for r in results if "冲突检测" in r.name]
            assert len(conflict_warnings) > 0
            assert conflict_warnings[0].severity == "warning"

