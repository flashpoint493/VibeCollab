"""
Tests for Protocol Checker
"""

import tempfile
import time
from pathlib import Path

from vibecollab.core.protocol_checker import CheckResult, ProtocolChecker


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

            # 应该有配置警告（无静态配置且无开发者目录）
            config_errors = [r for r in results if "开发者配置" in r.name]
            assert len(config_errors) > 0
            assert config_errors[0].severity == "warning"

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


class TestConfigurableThreshold:
    """测试可配置的文档更新阈值"""

    def test_threshold_from_config(self):
        """测试从配置读取阈值"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            doc = project_root / "docs" / "CONTEXT.md"
            doc.parent.mkdir(parents=True)
            doc.write_text("# Context\n", encoding="utf-8")

            # 设置阈值为 0.25h (15min)，文件刚创建所以不会超时
            config = {
                "protocol_check": {"checks": {"documentation": {"update_threshold_hours": 0.25}}},
                "dialogue_protocol": {
                    "on_end": {"update_files": ["docs/CONTEXT.md"]},
                    "on_start": {"read_files": []},
                },
            }
            checker = ProtocolChecker(project_root, config)
            results = checker._check_documentation_protocol()

            # 文件刚创建，不应超时
            update_warnings = [r for r in results if "文档更新" in r.name and r.severity == "warning"]
            assert len(update_warnings) == 0

    def test_threshold_default_15min(self):
        """测试默认阈值为 15 分钟"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            doc = project_root / "docs" / "CONTEXT.md"
            doc.parent.mkdir(parents=True)
            doc.write_text("# Context\n", encoding="utf-8")

            # 不设置 protocol_check 配置，应使用默认 0.25h
            config = {
                "dialogue_protocol": {
                    "on_end": {"update_files": ["docs/CONTEXT.md"]},
                    "on_start": {"read_files": []},
                },
            }
            checker = ProtocolChecker(project_root, config)
            results = checker._check_documentation_protocol()

            # 文件刚创建，即使默认 15min 也不应超时
            update_warnings = [r for r in results if "文档更新" in r.name]
            assert len(update_warnings) == 0

    def test_threshold_warning_message_minutes(self):
        """测试阈值小于 1 小时时，消息使用分钟单位"""
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            doc = project_root / "docs" / "OLD.md"
            doc.parent.mkdir(parents=True)
            doc.write_text("old\n", encoding="utf-8")
            # 设置文件修改时间为 1 小时前
            old_time = time.time() - 3600
            os.utime(doc, (old_time, old_time))

            config = {
                "protocol_check": {"checks": {"documentation": {"update_threshold_hours": 0.25}}},
                "dialogue_protocol": {
                    "on_end": {"update_files": ["docs/OLD.md"]},
                    "on_start": {"read_files": []},
                },
            }
            checker = ProtocolChecker(project_root, config)
            results = checker._check_documentation_protocol()

            update_warnings = [r for r in results if "文档更新" in r.name]
            assert len(update_warnings) == 1
            assert "15 分钟" in update_warnings[0].message


class TestDocumentConsistency:
    """测试关联文档一致性检查"""

    def _base_config(self, linked_groups=None):
        return {
            "documentation": {
                "key_files": [],
                "consistency": {
                    "enabled": True,
                    "default_level": "local_mtime",
                    "linked_groups": linked_groups or [],
                },
            },
            "dialogue_protocol": {
                "on_end": {"update_files": []},
                "on_start": {"read_files": []},
            },
        }

    def test_consistency_disabled(self):
        """一致性检查禁用时不产生结果"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            config = {
                "documentation": {"consistency": {"enabled": False}},
                "dialogue_protocol": {"on_end": {"update_files": []}, "on_start": {"read_files": []}},
            }
            checker = ProtocolChecker(project_root, config)
            results = checker._check_document_consistency()
            assert len(results) == 0

    def test_mtime_consistency_all_fresh(self):
        """同组文件都刚修改，不应告警"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs").mkdir()
            (project_root / "docs" / "PRD.md").write_text("prd\n", encoding="utf-8")
            (project_root / "docs" / "DECISIONS.md").write_text("dec\n", encoding="utf-8")

            config = self._base_config([{
                "name": "PRD-DECISIONS",
                "files": ["docs/PRD.md", "docs/DECISIONS.md"],
                "level": "local_mtime",
                "threshold_minutes": 15,
            }])
            checker = ProtocolChecker(project_root, config)
            results = checker._check_document_consistency()

            consistency_results = [r for r in results if "文档关联性" in r.name]
            assert len(consistency_results) == 0

    def test_mtime_consistency_one_stale(self):
        """一个文件刚修改，另一个落后超过阈值，应告警"""
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs").mkdir()

            prd = project_root / "docs" / "PRD.md"
            dec = project_root / "docs" / "DECISIONS.md"

            # DECISIONS.md 很新（刚写）
            dec.write_text("decisions\n", encoding="utf-8")

            # PRD.md 是 2 小时前修改的
            prd.write_text("prd\n", encoding="utf-8")
            old_time = time.time() - 7200
            os.utime(prd, (old_time, old_time))

            config = self._base_config([{
                "name": "PRD-DECISIONS",
                "files": ["docs/PRD.md", "docs/DECISIONS.md"],
                "level": "local_mtime",
                "threshold_minutes": 15,
            }])
            checker = ProtocolChecker(project_root, config)
            results = checker._check_document_consistency()

            consistency_results = [r for r in results if "文档关联性" in r.name]
            assert len(consistency_results) == 1
            assert "PRD.md" in consistency_results[0].message
            assert "DECISIONS.md" in consistency_results[0].message
            assert consistency_results[0].severity == "warning"

    def test_mtime_consistency_both_stale(self):
        """两个文件都很久没改了（>24h），不应告警（没有活跃编辑）"""
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs").mkdir()

            prd = project_root / "docs" / "PRD.md"
            dec = project_root / "docs" / "DECISIONS.md"

            prd.write_text("prd\n", encoding="utf-8")
            dec.write_text("dec\n", encoding="utf-8")

            # 两个都设为 48 小时前
            old_time = time.time() - 48 * 3600
            os.utime(prd, (old_time, old_time))
            os.utime(dec, (old_time, old_time))

            config = self._base_config([{
                "name": "PRD-DECISIONS",
                "files": ["docs/PRD.md", "docs/DECISIONS.md"],
                "level": "local_mtime",
                "threshold_minutes": 15,
            }])
            checker = ProtocolChecker(project_root, config)
            results = checker._check_document_consistency()

            consistency_results = [r for r in results if "文档关联性" in r.name]
            assert len(consistency_results) == 0

    def test_mtime_consistency_file_missing(self):
        """组内文件不存在时，不崩溃"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs").mkdir()
            (project_root / "docs" / "PRD.md").write_text("prd\n", encoding="utf-8")
            # DECISIONS.md 不存在

            config = self._base_config([{
                "name": "PRD-DECISIONS",
                "files": ["docs/PRD.md", "docs/DECISIONS.md"],
                "level": "local_mtime",
                "threshold_minutes": 15,
            }])
            checker = ProtocolChecker(project_root, config)
            results = checker._check_document_consistency()

            # 不应崩溃，且因为 < 2 个文件有 mtime，不应产生 consistency 结果
            consistency_results = [r for r in results if "文档关联性" in r.name]
            assert len(consistency_results) == 0

    def test_mtime_consistency_three_files(self):
        """三文件组中两个过时应产生两个 warning"""
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs").mkdir()

            a = project_root / "docs" / "A.md"
            b = project_root / "docs" / "B.md"
            c = project_root / "docs" / "C.md"

            # A 刚修改
            a.write_text("a\n", encoding="utf-8")
            # B 和 C 是 2 小时前
            b.write_text("b\n", encoding="utf-8")
            c.write_text("c\n", encoding="utf-8")
            old_time = time.time() - 7200
            os.utime(b, (old_time, old_time))
            os.utime(c, (old_time, old_time))

            config = self._base_config([{
                "name": "三文档组",
                "files": ["docs/A.md", "docs/B.md", "docs/C.md"],
                "level": "local_mtime",
                "threshold_minutes": 15,
            }])
            checker = ProtocolChecker(project_root, config)
            results = checker._check_document_consistency()

            consistency_results = [r for r in results if "文档关联性" in r.name]
            assert len(consistency_results) == 2

    def test_key_files_existence(self):
        """检查 key_files 声明的文件存在性"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs").mkdir()
            (project_root / "docs" / "PRD.md").write_text("ok\n", encoding="utf-8")

            config = {
                "documentation": {
                    "key_files": [
                        {"path": "docs/PRD.md", "purpose": "需求文档"},
                        {"path": "docs/MISSING.md", "purpose": "不存在的文档"},
                    ],
                    "consistency": {"enabled": True, "linked_groups": []},
                },
                "dialogue_protocol": {"on_end": {"update_files": []}, "on_start": {"read_files": []}},
            }
            checker = ProtocolChecker(project_root, config)
            results = checker._check_document_consistency()

            missing_results = [r for r in results if "关键文档存在性" in r.name]
            assert len(missing_results) == 1
            assert "MISSING.md" in missing_results[0].message

    def test_default_level_used(self):
        """未指定 level 的组使用 default_level"""
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs").mkdir()

            a = project_root / "docs" / "A.md"
            b = project_root / "docs" / "B.md"
            a.write_text("a\n", encoding="utf-8")
            b.write_text("b\n", encoding="utf-8")
            old_time = time.time() - 7200
            os.utime(b, (old_time, old_time))

            config = self._base_config([{
                "name": "默认级别组",
                "files": ["docs/A.md", "docs/B.md"],
                # 不指定 level，使用 default_level=local_mtime
                "threshold_minutes": 15,
            }])
            checker = ProtocolChecker(project_root, config)
            results = checker._check_document_consistency()

            # 应使用 local_mtime 检查
            consistency_results = [r for r in results if "文档关联性" in r.name]
            assert len(consistency_results) == 1

    def test_single_file_group_ignored(self):
        """只有一个文件的组被忽略"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs").mkdir()
            (project_root / "docs" / "A.md").write_text("a\n", encoding="utf-8")

            config = self._base_config([{
                "name": "单文件组",
                "files": ["docs/A.md"],
                "level": "local_mtime",
            }])
            checker = ProtocolChecker(project_root, config)
            results = checker._check_document_consistency()

            consistency_results = [r for r in results if "文档关联性" in r.name]
            assert len(consistency_results) == 0

    def test_key_files_staleness_triggered(self):
        """key_files 配置 max_stale_days 且文件过期，应告警"""
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs").mkdir()
            qa_file = project_root / "docs" / "QA.md"
            qa_file.write_text("# QA\n", encoding="utf-8")
            old_time = time.time() - 10 * 86400
            os.utime(qa_file, (old_time, old_time))

            config = {
                "documentation": {
                    "key_files": [
                        {"path": "docs/QA.md", "purpose": "QA测试",
                         "update_trigger": "功能完成时", "max_stale_days": 7},
                    ],
                    "consistency": {"enabled": True, "linked_groups": []},
                },
            }
            checker = ProtocolChecker(project_root, config)
            results = checker._check_document_consistency()

            stale_results = [r for r in results if "关键文档陈旧" in r.name]
            assert len(stale_results) == 1
            assert "QA.md" in stale_results[0].message
            assert "7 天" in stale_results[0].message
            assert "功能完成时" in stale_results[0].suggestion

    def test_key_files_staleness_not_triggered(self):
        """key_files 配置 max_stale_days 且文件刚更新，不应告警"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs").mkdir()
            (project_root / "docs" / "QA.md").write_text("# QA\n", encoding="utf-8")

            config = {
                "documentation": {
                    "key_files": [
                        {"path": "docs/QA.md", "purpose": "QA测试",
                         "max_stale_days": 7},
                    ],
                    "consistency": {"enabled": True, "linked_groups": []},
                },
            }
            checker = ProtocolChecker(project_root, config)
            results = checker._check_document_consistency()

            stale_results = [r for r in results if "关键文档陈旧" in r.name]
            assert len(stale_results) == 0

    def test_key_files_no_max_stale_days(self):
        """key_files 未配置 max_stale_days，不做陈旧性检查"""
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs").mkdir()
            qa_file = project_root / "docs" / "QA.md"
            qa_file.write_text("# QA\n", encoding="utf-8")
            old_time = time.time() - 30 * 86400
            os.utime(qa_file, (old_time, old_time))

            config = {
                "documentation": {
                    "key_files": [
                        {"path": "docs/QA.md", "purpose": "QA测试"},
                    ],
                    "consistency": {"enabled": True, "linked_groups": []},
                },
            }
            checker = ProtocolChecker(project_root, config)
            results = checker._check_document_consistency()

            stale_results = [r for r in results if "关键文档陈旧" in r.name]
            assert len(stale_results) == 0

    def test_max_inactive_hours_always_check(self):
        """max_inactive_hours=-1 时始终检查，即使组内文件都超过 24h 未改"""
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs").mkdir()

            prd = project_root / "docs" / "PRD.md"
            dec = project_root / "docs" / "DECISIONS.md"

            # DECISIONS.md 48h 前修改
            dec.write_text("decisions\n", encoding="utf-8")
            dec_time = time.time() - 48 * 3600
            os.utime(dec, (dec_time, dec_time))

            # PRD.md 72h 前修改（落后 DECISIONS 24h）
            prd.write_text("prd\n", encoding="utf-8")
            prd_time = time.time() - 72 * 3600
            os.utime(prd, (prd_time, prd_time))

            config = self._base_config([{
                "name": "PRD-DECISIONS",
                "files": ["docs/PRD.md", "docs/DECISIONS.md"],
                "level": "local_mtime",
                "threshold_minutes": 15,
                "max_inactive_hours": -1,
            }])
            checker = ProtocolChecker(project_root, config)
            results = checker._check_document_consistency()

            # max_inactive_hours=-1 应始终检查，即使都超 24h
            consistency_results = [r for r in results if "文档关联性" in r.name]
            assert len(consistency_results) == 1
            assert "PRD.md" in consistency_results[0].message

    def test_max_inactive_hours_custom(self):
        """max_inactive_hours=48 时，最新文件 30h 前修改仍应检查"""
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs").mkdir()

            a = project_root / "docs" / "A.md"
            b = project_root / "docs" / "B.md"

            # A 30h 前修改（在 48h 窗口内）
            a.write_text("a\n", encoding="utf-8")
            a_time = time.time() - 30 * 3600
            os.utime(a, (a_time, a_time))

            # B 60h 前修改
            b.write_text("b\n", encoding="utf-8")
            b_time = time.time() - 60 * 3600
            os.utime(b, (b_time, b_time))

            config = self._base_config([{
                "name": "AB-GROUP",
                "files": ["docs/A.md", "docs/B.md"],
                "level": "local_mtime",
                "threshold_minutes": 15,
                "max_inactive_hours": 48,
            }])
            checker = ProtocolChecker(project_root, config)
            results = checker._check_document_consistency()

            # A 在 48h 窗口内，B 落后，应告警
            consistency_results = [r for r in results if "文档关联性" in r.name]
            assert len(consistency_results) == 1

    def test_max_inactive_hours_default_24h(self):
        """max_inactive_hours=0 (默认) 使用 24h，超过不检查"""
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs").mkdir()

            a = project_root / "docs" / "A.md"
            b = project_root / "docs" / "B.md"

            # A 30h 前修改（超过默认 24h）
            a.write_text("a\n", encoding="utf-8")
            a_time = time.time() - 30 * 3600
            os.utime(a, (a_time, a_time))

            # B 60h 前修改
            b.write_text("b\n", encoding="utf-8")
            b_time = time.time() - 60 * 3600
            os.utime(b, (b_time, b_time))

            config = self._base_config([{
                "name": "AB-GROUP",
                "files": ["docs/A.md", "docs/B.md"],
                "level": "local_mtime",
                "threshold_minutes": 15,
                # 不设 max_inactive_hours，默认为 0 → 24h
            }])
            checker = ProtocolChecker(project_root, config)
            results = checker._check_document_consistency()

            # A 超过 24h，应跳过检查
            consistency_results = [r for r in results if "文档关联性" in r.name]
            assert len(consistency_results) == 0

    def test_watch_files_triggered(self):
        """watch_files 中的文件更新了但本文件没跟上，应告警"""
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs").mkdir()

            dec = project_root / "docs" / "DECISIONS.md"
            changelog = project_root / "docs" / "CHANGELOG.md"

            # DECISIONS.md 2h 前修改
            dec.write_text("# Decisions\n", encoding="utf-8")
            old_time = time.time() - 7200
            os.utime(dec, (old_time, old_time))

            # CHANGELOG.md 刚修改（比 DECISIONS.md 新）
            changelog.write_text("# Changelog\n", encoding="utf-8")

            config = {
                "documentation": {
                    "key_files": [
                        {
                            "path": "docs/DECISIONS.md",
                            "purpose": "决策记录",
                            "update_trigger": "每次 S/A 级决策后",
                            "watch_files": ["docs/CHANGELOG.md"],
                        },
                    ],
                    "consistency": {"enabled": True, "linked_groups": []},
                },
            }
            checker = ProtocolChecker(project_root, config)
            results = checker._check_document_consistency()

            lag_results = [r for r in results if "关键文档滞后" in r.name]
            assert len(lag_results) == 1
            assert "DECISIONS.md" in lag_results[0].name
            assert "CHANGELOG.md" in lag_results[0].message

    def test_watch_files_not_triggered(self):
        """watch_files 中的文件和本文件同步更新，不应告警"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs").mkdir()

            dec = project_root / "docs" / "DECISIONS.md"
            changelog = project_root / "docs" / "CHANGELOG.md"

            # 两个文件同时创建
            dec.write_text("# Decisions\n", encoding="utf-8")
            changelog.write_text("# Changelog\n", encoding="utf-8")

            config = {
                "documentation": {
                    "key_files": [
                        {
                            "path": "docs/DECISIONS.md",
                            "purpose": "决策记录",
                            "update_trigger": "每次 S/A 级决策后",
                            "watch_files": ["docs/CHANGELOG.md"],
                        },
                    ],
                    "consistency": {"enabled": True, "linked_groups": []},
                },
            }
            checker = ProtocolChecker(project_root, config)
            results = checker._check_document_consistency()

            lag_results = [r for r in results if "关键文档滞后" in r.name]
            assert len(lag_results) == 0

    def test_watch_files_missing_watch_target(self):
        """watch_files 指向不存在的文件，不崩溃不告警"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs").mkdir()

            dec = project_root / "docs" / "DECISIONS.md"
            dec.write_text("# Decisions\n", encoding="utf-8")

            config = {
                "documentation": {
                    "key_files": [
                        {
                            "path": "docs/DECISIONS.md",
                            "purpose": "决策记录",
                            "watch_files": ["docs/NONEXISTENT.md"],
                        },
                    ],
                    "consistency": {"enabled": True, "linked_groups": []},
                },
            }
            checker = ProtocolChecker(project_root, config)
            results = checker._check_document_consistency()

            lag_results = [r for r in results if "关键文档滞后" in r.name]
            assert len(lag_results) == 0

    def test_watch_files_no_config(self):
        """key_files 没有 watch_files 配置时不做跟随检查"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs").mkdir()
            (project_root / "docs" / "DECISIONS.md").write_text("ok\n", encoding="utf-8")

            config = {
                "documentation": {
                    "key_files": [
                        {"path": "docs/DECISIONS.md", "purpose": "决策记录"},
                    ],
                    "consistency": {"enabled": True, "linked_groups": []},
                },
            }
            checker = ProtocolChecker(project_root, config)
            results = checker._check_document_consistency()

            lag_results = [r for r in results if "关键文档滞后" in r.name]
            assert len(lag_results) == 0

