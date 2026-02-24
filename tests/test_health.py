"""Tests for the Project Health Signal Extractor."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from vibecollab.health import (
    HealthExtractor,
    HealthReport,
    Signal,
    SignalLevel,
)

# ── Data Classes ──────────────────────────────────────────────


class TestSignal:
    def test_basic_signal(self):
        s = Signal(
            name="test", level=SignalLevel.INFO, category="test",
            value=42, message="hello",
        )
        assert s.name == "test"
        assert s.level == SignalLevel.INFO
        assert s.value == 42

    def test_to_dict(self):
        s = Signal(
            name="x", level=SignalLevel.CRITICAL, category="c",
            value=1, message="m", suggestion="fix it",
        )
        d = s.to_dict()
        assert d["level"] == "critical"
        assert d["suggestion"] == "fix it"

    def test_signal_levels(self):
        assert SignalLevel.CRITICAL.value == "critical"
        assert SignalLevel.WARNING.value == "warning"
        assert SignalLevel.INFO.value == "info"


class TestHealthReport:
    def test_empty_report(self):
        r = HealthReport()
        assert r.critical_count == 0
        assert r.warning_count == 0
        assert r.info_count == 0
        assert r.timestamp != ""

    def test_counts(self):
        r = HealthReport(signals=[
            Signal("a", SignalLevel.CRITICAL, "x", 1, "m"),
            Signal("b", SignalLevel.CRITICAL, "x", 2, "m"),
            Signal("c", SignalLevel.WARNING, "x", 3, "m"),
            Signal("d", SignalLevel.INFO, "x", 4, "m"),
        ])
        assert r.critical_count == 2
        assert r.warning_count == 1
        assert r.info_count == 1

    def test_to_dict(self):
        r = HealthReport(signals=[
            Signal("a", SignalLevel.INFO, "x", 1, "m"),
        ])
        r.score = 90.0
        d = r.to_dict()
        assert d["score"] == 90.0
        assert d["infos"] == 1
        assert len(d["signals"]) == 1


class TestScoring:
    def test_perfect_score(self):
        r = HealthReport(signals=[
            Signal("a", SignalLevel.INFO, "x", 1, "ok"),
        ])
        score = HealthExtractor._calculate_score(r)
        assert score == 100.0

    def test_critical_deduction(self):
        r = HealthReport(signals=[
            Signal("a", SignalLevel.CRITICAL, "x", 1, "bad"),
        ])
        score = HealthExtractor._calculate_score(r)
        assert score == 75.0

    def test_warning_deduction(self):
        r = HealthReport(signals=[
            Signal("a", SignalLevel.WARNING, "x", 1, "eh"),
        ])
        score = HealthExtractor._calculate_score(r)
        assert score == 90.0

    def test_mixed_deduction(self):
        r = HealthReport(signals=[
            Signal("a", SignalLevel.CRITICAL, "x", 1, "bad"),
            Signal("b", SignalLevel.WARNING, "x", 1, "eh"),
            Signal("c", SignalLevel.WARNING, "x", 1, "eh"),
        ])
        score = HealthExtractor._calculate_score(r)
        assert score == 55.0

    def test_floor_at_zero(self):
        r = HealthReport(signals=[
            Signal("a", SignalLevel.CRITICAL, "x", 1, "bad"),
            Signal("b", SignalLevel.CRITICAL, "x", 1, "bad"),
            Signal("c", SignalLevel.CRITICAL, "x", 1, "bad"),
            Signal("d", SignalLevel.CRITICAL, "x", 1, "bad"),
            Signal("e", SignalLevel.CRITICAL, "x", 1, "bad"),
        ])
        score = HealthExtractor._calculate_score(r)
        assert score == 0.0

    def test_grade_A(self):
        assert HealthExtractor._score_to_grade(95) == "A"
        assert HealthExtractor._score_to_grade(90) == "A"

    def test_grade_B(self):
        assert HealthExtractor._score_to_grade(80) == "B"
        assert HealthExtractor._score_to_grade(70) == "B"

    def test_grade_C(self):
        assert HealthExtractor._score_to_grade(60) == "C"

    def test_grade_D(self):
        assert HealthExtractor._score_to_grade(40) == "D"

    def test_grade_F(self):
        assert HealthExtractor._score_to_grade(20) == "F"
        assert HealthExtractor._score_to_grade(0) == "F"


# ── Protocol Signals ──────────────────────────────────────────


class TestProtocolSignals:
    def _make_extractor(self, tmpdir):
        config = {"dialogue_protocol": {"on_end": {"update_files": []}, "on_start": {"read_files": []}}}
        return HealthExtractor(Path(tmpdir), config)

    def test_protocol_all_passed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ext = self._make_extractor(tmpdir)
            mock_summary = {"total": 3, "passed": 3, "errors": 0, "warnings": 0, "infos": 3, "all_passed": True}
            mock_results = []
            with patch("vibecollab.health.ProtocolChecker") as MockChecker:
                instance = MockChecker.return_value
                instance.check_all.return_value = mock_results
                instance.get_summary.return_value = mock_summary
                report = HealthReport()
                ext._extract_protocol_signals(report)

            names = [s.name for s in report.signals]
            assert "protocol_compliance" in names
            assert "protocol_errors" not in names

    def test_protocol_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ext = self._make_extractor(tmpdir)
            mock_summary = {"errors": 2, "warnings": 1, "all_passed": False}
            with patch("vibecollab.health.ProtocolChecker") as MockChecker:
                instance = MockChecker.return_value
                instance.check_all.return_value = []
                instance.get_summary.return_value = mock_summary
                report = HealthReport()
                ext._extract_protocol_signals(report)

            error_signals = [s for s in report.signals if s.name == "protocol_errors"]
            assert len(error_signals) == 1
            assert error_signals[0].level == SignalLevel.CRITICAL
            assert error_signals[0].value == 2

            warn_signals = [s for s in report.signals if s.name == "protocol_warnings"]
            assert len(warn_signals) == 1

    def test_protocol_checker_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ext = self._make_extractor(tmpdir)
            with patch("vibecollab.health.ProtocolChecker", side_effect=Exception("boom")):
                report = HealthReport()
                ext._extract_protocol_signals(report)

            assert len(report.signals) == 1
            assert report.signals[0].name == "protocol_checker_unavailable"


# ── EventLog Signals ──────────────────────────────────────────


class TestEventLogSignals:
    def _make_extractor(self, tmpdir):
        return HealthExtractor(Path(tmpdir), {})

    def test_log_integrity_clean(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ext = self._make_extractor(tmpdir)
            with patch("vibecollab.health.EventLog") as MockLog:
                instance = MockLog.return_value
                instance.verify_integrity.return_value = []
                instance.count.return_value = 10
                instance.query.return_value = [MagicMock()]  # recent activity

                report = HealthReport()
                ext._extract_eventlog_signals(report)

            integrity = [s for s in report.signals if s.name == "log_integrity"]
            assert len(integrity) == 1
            assert integrity[0].level == SignalLevel.INFO

    def test_log_integrity_violated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ext = self._make_extractor(tmpdir)
            with patch("vibecollab.health.EventLog") as MockLog:
                instance = MockLog.return_value
                instance.verify_integrity.return_value = [{"line": 1, "error": "bad"}]
                instance.count.return_value = 5
                instance.query.return_value = []

                report = HealthReport()
                ext._extract_eventlog_signals(report)

            integrity = [s for s in report.signals if s.name == "log_integrity"]
            assert integrity[0].level == SignalLevel.CRITICAL

    def test_project_inactive(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ext = self._make_extractor(tmpdir)
            with patch("vibecollab.health.EventLog") as MockLog:
                instance = MockLog.return_value
                instance.verify_integrity.return_value = []
                instance.count.return_value = 50
                instance.query.return_value = []  # no recent events

                report = HealthReport()
                ext._extract_eventlog_signals(report)

            inactive = [s for s in report.signals if s.name == "project_inactive"]
            assert len(inactive) == 1
            assert inactive[0].level == SignalLevel.WARNING

    def test_unresolved_conflicts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ext = self._make_extractor(tmpdir)
            with patch("vibecollab.health.EventLog") as MockLog:
                instance = MockLog.return_value
                instance.verify_integrity.return_value = []
                instance.count.return_value = 10

                def mock_query(event_type=None, since=None, **kw):
                    from vibecollab.event_log import EventType
                    if event_type == EventType.CONFLICT_DETECTED.value:
                        return [MagicMock(), MagicMock(), MagicMock()]
                    elif event_type == EventType.CONFLICT_RESOLVED.value:
                        return [MagicMock()]
                    return [MagicMock()]

                instance.query.side_effect = mock_query

                report = HealthReport()
                ext._extract_eventlog_signals(report)

            conflicts = [s for s in report.signals if s.name == "unresolved_conflicts"]
            assert len(conflicts) == 1
            assert conflicts[0].value == 2

    def test_high_validation_fail_rate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ext = self._make_extractor(tmpdir)
            with patch("vibecollab.health.EventLog") as MockLog:
                instance = MockLog.return_value
                instance.verify_integrity.return_value = []
                instance.count.return_value = 10

                def mock_query(event_type=None, since=None, **kw):
                    from vibecollab.event_log import EventType
                    if event_type == EventType.VALIDATION_FAILED.value:
                        return [MagicMock()] * 4
                    elif event_type == EventType.VALIDATION_PASSED.value:
                        return [MagicMock()] * 1
                    return [MagicMock()]

                instance.query.side_effect = mock_query

                report = HealthReport()
                ext._extract_eventlog_signals(report)

            fail_rate = [s for s in report.signals if s.name == "validation_fail_rate"]
            assert len(fail_rate) == 1
            assert fail_rate[0].level == SignalLevel.WARNING
            assert fail_rate[0].value == 0.8


# ── Task Signals ──────────────────────────────────────────────


class TestTaskSignals:
    def _make_extractor(self, tmpdir):
        return HealthExtractor(Path(tmpdir), {})

    def _make_task(self, id="T-1", status="TODO", assignee=None, deps=None):
        t = MagicMock()
        t.id = id
        t.status = status
        t.assignee = assignee
        t.dependencies = deps or []
        return t

    def test_no_tasks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ext = self._make_extractor(tmpdir)
            with patch("vibecollab.health.TaskManager") as MockTM:
                MockTM.return_value.count.return_value = 0
                report = HealthReport()
                ext._extract_task_signals(report)

            no_task = [s for s in report.signals if s.name == "no_tasks"]
            assert len(no_task) == 1

    def test_task_completion_rate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ext = self._make_extractor(tmpdir)
            with patch("vibecollab.health.TaskManager") as MockTM:
                instance = MockTM.return_value
                instance.count.side_effect = lambda status=None: {
                    None: 10, "DONE": 7, "TODO": 1, "IN_PROGRESS": 1, "REVIEW": 1,
                }.get(status, 0)
                instance.list_tasks.return_value = []

                report = HealthReport()
                ext._extract_task_signals(report)

            rate = [s for s in report.signals if s.name == "task_completion_rate"]
            assert len(rate) == 1
            assert rate[0].value == 0.7

    def test_task_backlog_warning(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ext = self._make_extractor(tmpdir)
            with patch("vibecollab.health.TaskManager") as MockTM:
                instance = MockTM.return_value
                instance.count.side_effect = lambda status=None: {
                    None: 12, "DONE": 2, "TODO": 8, "IN_PROGRESS": 1, "REVIEW": 1,
                }.get(status, 0)
                instance.list_tasks.return_value = []

                report = HealthReport()
                ext._extract_task_signals(report)

            backlog = [s for s in report.signals if s.name == "task_backlog"]
            assert len(backlog) == 1
            assert backlog[0].level == SignalLevel.WARNING

    def test_review_bottleneck(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ext = self._make_extractor(tmpdir)
            with patch("vibecollab.health.TaskManager") as MockTM:
                instance = MockTM.return_value
                instance.count.side_effect = lambda status=None: {
                    None: 6, "DONE": 1, "TODO": 0, "IN_PROGRESS": 1, "REVIEW": 4,
                }.get(status, 0)
                instance.list_tasks.return_value = []

                report = HealthReport()
                ext._extract_task_signals(report)

            bottleneck = [s for s in report.signals if s.name == "review_bottleneck"]
            assert len(bottleneck) == 1

    def test_dependency_blocked(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ext = self._make_extractor(tmpdir)
            dep_task = self._make_task("T-1", "IN_PROGRESS")
            blocked_task = self._make_task("T-2", "TODO", deps=["T-1"])
            with patch("vibecollab.health.TaskManager") as MockTM:
                instance = MockTM.return_value
                instance.count.side_effect = lambda status=None: {
                    None: 2, "DONE": 0, "TODO": 1, "IN_PROGRESS": 1, "REVIEW": 0,
                }.get(status, 0)
                instance.list_tasks.return_value = [dep_task, blocked_task]
                instance.get_task.side_effect = lambda id: {"T-1": dep_task, "T-2": blocked_task}.get(id)

                report = HealthReport()
                ext._extract_task_signals(report)

            blocked = [s for s in report.signals if s.name == "dependency_blocked"]
            assert len(blocked) == 1
            assert blocked[0].value == 1

    def test_load_imbalance(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ext = self._make_extractor(tmpdir)
            tasks = [
                self._make_task("T-1", "IN_PROGRESS", "alice"),
                self._make_task("T-2", "IN_PROGRESS", "alice"),
                self._make_task("T-3", "IN_PROGRESS", "alice"),
                self._make_task("T-4", "IN_PROGRESS", "alice"),
                self._make_task("T-5", "TODO", "bob"),
            ]
            with patch("vibecollab.health.TaskManager") as MockTM:
                instance = MockTM.return_value
                instance.count.side_effect = lambda status=None: {
                    None: 5, "DONE": 0, "TODO": 1, "IN_PROGRESS": 4, "REVIEW": 0,
                }.get(status, 0)
                instance.list_tasks.return_value = tasks

                report = HealthReport()
                ext._extract_task_signals(report)

            imbalance = [s for s in report.signals if s.name == "load_imbalance"]
            assert len(imbalance) == 1


# ── Full Integration ──────────────────────────────────────────


class TestFullExtract:
    def test_extract_returns_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ext = HealthExtractor(Path(tmpdir), {})
            report = ext.extract()
            assert isinstance(report, HealthReport)
            assert report.score >= 0
            assert report.score <= 100
            assert "grade" in report.summary

    def test_extract_with_minimal_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ext = HealthExtractor(Path(tmpdir), {"project": {"name": "test"}})
            report = ext.extract()
            assert isinstance(report, HealthReport)
            assert len(report.signals) > 0
