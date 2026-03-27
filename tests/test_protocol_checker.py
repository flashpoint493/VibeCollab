"""
Tests for Protocol Checker
"""

import tempfile
import time
from pathlib import Path

from vibecollab.core.protocol_checker import CheckResult, ProtocolChecker


class TestProtocolChecker:
    """Protocol checker tests"""

    def test_check_collaboration_missing(self):
        """Test detecting missing COLLABORATION.md"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create basic directory structure
            docs_dir = project_root / "docs" / "roles"
            docs_dir.mkdir(parents=True)

            # Configure multi-role mode
            config = {
                "role_context": {
                    "enabled": True,
                    "collaboration": {
                        "file": "docs/roles/COLLABORATION.md"
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

            # Should have a warning: missing COLLABORATION.md
            collab_check = [r for r in results if "Collaboration Doc" in r.name]
            assert len(collab_check) > 0
            assert collab_check[0].severity == "warning"
            assert not collab_check[0].passed

    def test_check_collaboration_exists(self):
        """Test detecting existing COLLABORATION.md"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create COLLABORATION.md
            collab_file = project_root / "docs" / "roles" / "COLLABORATION.md"
            collab_file.parent.mkdir(parents=True)
            collab_file.write_text("# Collaboration\n", encoding="utf-8")

            config = {
                "role_context": {
                    "enabled": True,
                    "collaboration": {
                        "file": "docs/roles/COLLABORATION.md"
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

            # Should not have missing collaboration doc errors
            collab_errors = [r for r in results
                           if "Collaboration Doc" in r.name
                           and r.severity == "warning"
                           and not r.passed]
            assert len(collab_errors) == 0

    def test_check_collaboration_disabled(self):
        """Test that COLLABORATION.md is not checked when multi-role mode is disabled"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            config = {
                "role_context": {
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

            # Should not have collaboration doc checks
            collab_check = [r for r in results if "Collaboration Doc" in r.name]
            assert len(collab_check) == 0

    def test_check_result_structure(self):
        """Test CheckResult data structure"""
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
        """Test check results summary"""
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

    def test_check_role_contexts(self):
        """Test checking role context files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Configure multi-role
            config = {
                "role_context": {
                    "enabled": True,
                    "roles": [
                        {"id": "alice", "name": "Alice", "role": "backend"},
                        {"id": "bob", "name": "Bob", "role": "frontend"}
                    ],
                    "collaboration": {
                        "file": "docs/roles/COLLABORATION.md"
                    }
                },
                "dialogue_protocol": {
                    "on_end": {"update_files": []},
                    "on_start": {"read_files": []}
                }
            }

            # Only create alice's context
            alice_dir = project_root / "docs" / "roles" / "alice"
            alice_dir.mkdir(parents=True)
            (alice_dir / "CONTEXT.md").write_text("# Alice Context\n", encoding="utf-8")
            (alice_dir / ".metadata.yaml").write_text("role: backend\n", encoding="utf-8")

            checker = ProtocolChecker(project_root, config)
            results = checker.check_all()

            # Should detect that bob is missing directory and files
            bob_checks = [r for r in results if "Bob" in r.message or "bob" in r.message]
            assert len(bob_checks) > 0

            # Should detect that alice's files exist
            alice_context_checks = [r for r in results
                                   if "Alice" in r.message and "CONTEXT.md" in r.message]
            assert any(r.passed for r in alice_context_checks)

    def test_check_role_missing_id(self):
        """Test checking role missing ID"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            config = {
                "role_context": {
                    "enabled": True,
                    "roles": [
                        {"name": "Alice"}  # missing id
                    ]
                },
                "dialogue_protocol": {
                    "on_end": {"update_files": []},
                    "on_start": {"read_files": []}
                }
            }

            checker = ProtocolChecker(project_root, config)
            results = checker.check_all()

            # Should have role ID error
            id_errors = [r for r in results if "Role ID" in r.name]
            assert len(id_errors) > 0
            assert id_errors[0].severity == "error"

    def test_check_role_no_roles(self):
        """Test multi-role mode enabled but no role config"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            config = {
                "role_context": {
                    "enabled": True,
                    "roles": []  # empty list
                },
                "dialogue_protocol": {
                    "on_end": {"update_files": []},
                    "on_start": {"read_files": []}
                }
            }

            checker = ProtocolChecker(project_root, config)
            results = checker.check_all()

            # Should have config warning (no static config and no role dirs)
            config_errors = [r for r in results if "Role Config" in r.name]
            assert len(config_errors) > 0
            assert config_errors[0].severity == "warning"

    def test_check_conflict_detection_disabled(self):
        """Test warning when conflict detection is disabled"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)

            # Create role directory
            alice_dir = project_root / "docs" / "roles" / "alice"
            alice_dir.mkdir(parents=True)
            (alice_dir / "CONTEXT.md").write_text("# Alice\n", encoding="utf-8")

            config = {
                "role_context": {
                    "enabled": True,
                    "roles": [{"id": "alice", "name": "Alice"}],
                    "conflict_detection": {
                        "enabled": False  # disable conflict detection
                    },
                    "collaboration": {
                        "file": "docs/roles/COLLABORATION.md"
                    }
                },
                "dialogue_protocol": {
                    "on_end": {"update_files": []},
                    "on_start": {"read_files": []}
                }
            }

            # Create collaboration document
            collab_file = project_root / "docs" / "roles" / "COLLABORATION.md"
            collab_file.write_text("# Collab\n", encoding="utf-8")

            checker = ProtocolChecker(project_root, config)
            results = checker.check_all()

            # Should have conflict detection warning
            conflict_warnings = [r for r in results if "Conflict Detection" in r.name]
            assert len(conflict_warnings) > 0
            assert conflict_warnings[0].severity == "warning"


class TestConfigurableThreshold:
    """Test configurable document update thresholds"""

    def test_threshold_from_config(self):
        """Test reading threshold from config"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            doc = project_root / "docs" / "CONTEXT.md"
            doc.parent.mkdir(parents=True)
            doc.write_text("# Context\n", encoding="utf-8")

            # Set threshold to 0.25h (15min), file just created so no timeout
            config = {
                "protocol_check": {"checks": {"documentation": {"update_threshold_hours": 0.25}}},
                "dialogue_protocol": {
                    "on_end": {"update_files": ["docs/CONTEXT.md"]},
                    "on_start": {"read_files": []},
                },
            }
            checker = ProtocolChecker(project_root, config)
            results = checker._check_documentation_protocol()

            # File just created, should not timeout
            update_warnings = [r for r in results if "Doc Update" in r.name and r.severity == "warning"]
            assert len(update_warnings) == 0

    def test_threshold_default_15min(self):
        """Test default threshold is 15 minutes"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            doc = project_root / "docs" / "CONTEXT.md"
            doc.parent.mkdir(parents=True)
            doc.write_text("# Context\n", encoding="utf-8")

            # No protocol_check config, should use default 0.25h
            config = {
                "dialogue_protocol": {
                    "on_end": {"update_files": ["docs/CONTEXT.md"]},
                    "on_start": {"read_files": []},
                },
            }
            checker = ProtocolChecker(project_root, config)
            results = checker._check_documentation_protocol()

            # File just created, even with default 15min should not timeout
            update_warnings = [r for r in results if "Doc Update" in r.name]
            assert len(update_warnings) == 0

    def test_threshold_warning_message_minutes(self):
        """Test warning message uses minutes when threshold < 1 hour"""
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            doc = project_root / "docs" / "OLD.md"
            doc.parent.mkdir(parents=True)
            doc.write_text("old\n", encoding="utf-8")
            # Set file modification time to 1 hour ago
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

            update_warnings = [r for r in results if "Doc Update" in r.name]
            assert len(update_warnings) == 1
            assert "15 minutes" in update_warnings[0].message


class TestDocumentConsistency:
    """Test linked document consistency checks"""

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
        """No results when consistency check is disabled"""
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
        """All files in group just modified, should not warn"""
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

            consistency_results = [r for r in results if "Doc Consistency" in r.name]
            assert len(consistency_results) == 0

    def test_mtime_consistency_one_stale(self):
        """One file just modified, another exceeds threshold, should warn"""
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs").mkdir()

            prd = project_root / "docs" / "PRD.md"
            dec = project_root / "docs" / "DECISIONS.md"

            # DECISIONS.md is very new (just written)
            dec.write_text("decisions\n", encoding="utf-8")

            # PRD.md was modified 2 hours ago
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

            consistency_results = [r for r in results if "Doc Consistency" in r.name]
            assert len(consistency_results) == 1
            assert "PRD.md" in consistency_results[0].message
            assert "DECISIONS.md" in consistency_results[0].message
            assert consistency_results[0].severity == "warning"

    def test_mtime_consistency_both_stale(self):
        """Both files not modified for a long time (>24h), should not warn (no active editing)"""
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs").mkdir()

            prd = project_root / "docs" / "PRD.md"
            dec = project_root / "docs" / "DECISIONS.md"

            prd.write_text("prd\n", encoding="utf-8")
            dec.write_text("dec\n", encoding="utf-8")

            # Both set to 48 hours ago
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

            consistency_results = [r for r in results if "Doc Consistency" in r.name]
            assert len(consistency_results) == 0

    def test_mtime_consistency_file_missing(self):
        """Group member file does not exist, should not crash"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs").mkdir()
            (project_root / "docs" / "PRD.md").write_text("prd\n", encoding="utf-8")
            # DECISIONS.md does not exist

            config = self._base_config([{
                "name": "PRD-DECISIONS",
                "files": ["docs/PRD.md", "docs/DECISIONS.md"],
                "level": "local_mtime",
                "threshold_minutes": 15,
            }])
            checker = ProtocolChecker(project_root, config)
            results = checker._check_document_consistency()

            # Should not crash, and since < 2 files have mtime, no consistency result
            consistency_results = [r for r in results if "Doc Consistency" in r.name]
            assert len(consistency_results) == 0

    def test_mtime_consistency_three_files(self):
        """Two stale files in a three-file group should produce two warnings"""
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs").mkdir()

            a = project_root / "docs" / "A.md"
            b = project_root / "docs" / "B.md"
            c = project_root / "docs" / "C.md"

            # A just modified
            a.write_text("a\n", encoding="utf-8")
            # B and C modified 2 hours ago
            b.write_text("b\n", encoding="utf-8")
            c.write_text("c\n", encoding="utf-8")
            old_time = time.time() - 7200
            os.utime(b, (old_time, old_time))
            os.utime(c, (old_time, old_time))

            config = self._base_config([{
                "name": "three-doc-group",
                "files": ["docs/A.md", "docs/B.md", "docs/C.md"],
                "level": "local_mtime",
                "threshold_minutes": 15,
            }])
            checker = ProtocolChecker(project_root, config)
            results = checker._check_document_consistency()

            consistency_results = [r for r in results if "Doc Consistency" in r.name]
            assert len(consistency_results) == 2

    def test_key_files_existence(self):
        """Check key_files declared file existence"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs").mkdir()
            (project_root / "docs" / "PRD.md").write_text("ok\n", encoding="utf-8")

            config = {
                "documentation": {
                    "key_files": [
                        {"path": "docs/PRD.md", "purpose": "Requirements doc"},
                        {"path": "docs/MISSING.md", "purpose": "Non-existent doc"},
                    ],
                    "consistency": {"enabled": True, "linked_groups": []},
                },
                "dialogue_protocol": {"on_end": {"update_files": []}, "on_start": {"read_files": []}},
            }
            checker = ProtocolChecker(project_root, config)
            results = checker._check_document_consistency()

            missing_results = [r for r in results if "Key Doc Existence" in r.name]
            assert len(missing_results) == 1
            assert "MISSING.md" in missing_results[0].message

    def test_default_level_used(self):
        """Groups without explicit level use default_level"""
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
                "name": "default-level-group",
                "files": ["docs/A.md", "docs/B.md"],
                # No level specified, uses default_level=local_mtime
                "threshold_minutes": 15,
            }])
            checker = ProtocolChecker(project_root, config)
            results = checker._check_document_consistency()

            # Should use local_mtime check
            consistency_results = [r for r in results if "Doc Consistency" in r.name]
            assert len(consistency_results) == 1

    def test_single_file_group_ignored(self):
        """Groups with only one file are ignored"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs").mkdir()
            (project_root / "docs" / "A.md").write_text("a\n", encoding="utf-8")

            config = self._base_config([{
                "name": "single-file-group",
                "files": ["docs/A.md"],
                "level": "local_mtime",
            }])
            checker = ProtocolChecker(project_root, config)
            results = checker._check_document_consistency()

            consistency_results = [r for r in results if "Doc Consistency" in r.name]
            assert len(consistency_results) == 0

    def test_key_files_staleness_triggered(self):
        """key_files with max_stale_days configured and file expired, should warn"""
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
                        {"path": "docs/QA.md", "purpose": "QA testing",
                         "update_trigger": "on feature completion", "max_stale_days": 7},
                    ],
                    "consistency": {"enabled": True, "linked_groups": []},
                },
            }
            checker = ProtocolChecker(project_root, config)
            results = checker._check_document_consistency()

            stale_results = [r for r in results if "Key Doc Stale" in r.name]
            assert len(stale_results) == 1
            assert "QA.md" in stale_results[0].message
            assert "7 days" in stale_results[0].message
            assert "on feature completion" in stale_results[0].suggestion

    def test_key_files_staleness_not_triggered(self):
        """key_files with max_stale_days configured and file just updated, should not warn"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs").mkdir()
            (project_root / "docs" / "QA.md").write_text("# QA\n", encoding="utf-8")

            config = {
                "documentation": {
                    "key_files": [
                        {"path": "docs/QA.md", "purpose": "QA testing",
                         "max_stale_days": 7},
                    ],
                    "consistency": {"enabled": True, "linked_groups": []},
                },
            }
            checker = ProtocolChecker(project_root, config)
            results = checker._check_document_consistency()

            stale_results = [r for r in results if "Key Doc Stale" in r.name]
            assert len(stale_results) == 0

    def test_key_files_no_max_stale_days(self):
        """key_files without max_stale_days, no staleness check"""
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
                        {"path": "docs/QA.md", "purpose": "QA testing"},
                    ],
                    "consistency": {"enabled": True, "linked_groups": []},
                },
            }
            checker = ProtocolChecker(project_root, config)
            results = checker._check_document_consistency()

            stale_results = [r for r in results if "Key Doc Stale" in r.name]
            assert len(stale_results) == 0

    def test_max_inactive_hours_always_check(self):
        """max_inactive_hours=-1 always checks, even if all group files > 24h old"""
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs").mkdir()

            prd = project_root / "docs" / "PRD.md"
            dec = project_root / "docs" / "DECISIONS.md"

            # DECISIONS.md modified 48h ago
            dec.write_text("decisions\n", encoding="utf-8")
            dec_time = time.time() - 48 * 3600
            os.utime(dec, (dec_time, dec_time))

            # PRD.md modified 72h ago (24h behind DECISIONS)
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

            # max_inactive_hours=-1 should always check, even if all > 24h
            consistency_results = [r for r in results if "Doc Consistency" in r.name]
            assert len(consistency_results) == 1
            assert "PRD.md" in consistency_results[0].message

    def test_max_inactive_hours_custom(self):
        """max_inactive_hours=48, newest file modified 30h ago should still check"""
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs").mkdir()

            a = project_root / "docs" / "A.md"
            b = project_root / "docs" / "B.md"

            # A modified 30h ago (within 48h window)
            a.write_text("a\n", encoding="utf-8")
            a_time = time.time() - 30 * 3600
            os.utime(a, (a_time, a_time))

            # B modified 60h ago
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

            # A is within 48h window, B is lagging, should warn
            consistency_results = [r for r in results if "Doc Consistency" in r.name]
            assert len(consistency_results) == 1

    def test_max_inactive_hours_default_24h(self):
        """max_inactive_hours=0 (default) uses 24h, exceeding skips check"""
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs").mkdir()

            a = project_root / "docs" / "A.md"
            b = project_root / "docs" / "B.md"

            # A modified 30h ago (exceeds default 24h)
            a.write_text("a\n", encoding="utf-8")
            a_time = time.time() - 30 * 3600
            os.utime(a, (a_time, a_time))

            # B modified 60h ago
            b.write_text("b\n", encoding="utf-8")
            b_time = time.time() - 60 * 3600
            os.utime(b, (b_time, b_time))

            config = self._base_config([{
                "name": "AB-GROUP",
                "files": ["docs/A.md", "docs/B.md"],
                "level": "local_mtime",
                "threshold_minutes": 15,
                # No max_inactive_hours, default is 0 -> 24h
            }])
            checker = ProtocolChecker(project_root, config)
            results = checker._check_document_consistency()

            # A exceeds 24h, should skip check
            consistency_results = [r for r in results if "Doc Consistency" in r.name]
            assert len(consistency_results) == 0

    def test_watch_files_triggered(self):
        """watch_files target updated but this file didn't follow, should warn"""
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs").mkdir()

            dec = project_root / "docs" / "DECISIONS.md"
            changelog = project_root / "docs" / "CHANGELOG.md"

            # DECISIONS.md modified 2h ago
            dec.write_text("# Decisions\n", encoding="utf-8")
            old_time = time.time() - 7200
            os.utime(dec, (old_time, old_time))

            # CHANGELOG.md just modified (newer than DECISIONS.md)
            changelog.write_text("# Changelog\n", encoding="utf-8")

            config = {
                "documentation": {
                    "key_files": [
                        {
                            "path": "docs/DECISIONS.md",
                            "purpose": "Decision records",
                            "update_trigger": "after each S/A level decision",
                            "watch_files": ["docs/CHANGELOG.md"],
                        },
                    ],
                    "consistency": {"enabled": True, "linked_groups": []},
                },
            }
            checker = ProtocolChecker(project_root, config)
            results = checker._check_document_consistency()

            lag_results = [r for r in results if "Key Doc Lag" in r.name]
            assert len(lag_results) == 1
            assert "DECISIONS.md" in lag_results[0].name
            assert "CHANGELOG.md" in lag_results[0].message

    def test_watch_files_not_triggered(self):
        """watch_files target and this file updated simultaneously, should not warn"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs").mkdir()

            dec = project_root / "docs" / "DECISIONS.md"
            changelog = project_root / "docs" / "CHANGELOG.md"

            # Both files created at the same time
            dec.write_text("# Decisions\n", encoding="utf-8")
            changelog.write_text("# Changelog\n", encoding="utf-8")

            config = {
                "documentation": {
                    "key_files": [
                        {
                            "path": "docs/DECISIONS.md",
                            "purpose": "Decision records",
                            "update_trigger": "after each S/A level decision",
                            "watch_files": ["docs/CHANGELOG.md"],
                        },
                    ],
                    "consistency": {"enabled": True, "linked_groups": []},
                },
            }
            checker = ProtocolChecker(project_root, config)
            results = checker._check_document_consistency()

            lag_results = [r for r in results if "Key Doc Lag" in r.name]
            assert len(lag_results) == 0

    def test_watch_files_missing_watch_target(self):
        """watch_files pointing to non-existent file, should not crash or warn"""
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
                            "purpose": "Decision records",
                            "watch_files": ["docs/NONEXISTENT.md"],
                        },
                    ],
                    "consistency": {"enabled": True, "linked_groups": []},
                },
            }
            checker = ProtocolChecker(project_root, config)
            results = checker._check_document_consistency()

            lag_results = [r for r in results if "Key Doc Lag" in r.name]
            assert len(lag_results) == 0

    def test_watch_files_no_config(self):
        """key_files without watch_files config, no follow-up check"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "docs").mkdir()
            (project_root / "docs" / "DECISIONS.md").write_text("ok\n", encoding="utf-8")

            config = {
                "documentation": {
                    "key_files": [
                        {"path": "docs/DECISIONS.md", "purpose": "Decision records"},
                    ],
                    "consistency": {"enabled": True, "linked_groups": []},
                },
            }
            checker = ProtocolChecker(project_root, config)
            results = checker._check_document_consistency()

            lag_results = [r for r in results if "Key Doc Lag" in r.name]
            assert len(lag_results) == 0
