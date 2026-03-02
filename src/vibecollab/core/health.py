"""
Project Health Signal Extractor

从 EventLog、TaskManager、ProtocolChecker 提取项目健康信号，
生成结构化的健康报告，用于项目演进决策和自动化监控。

DECISION-009 Iteration 4: Auto-evolution — Signal extraction pattern.

信号分级:
  - CRITICAL: 必须立即处理 (完整性破坏、协议严重违规)
  - WARNING:  需要关注 (积压、瓶颈、过期文档)
  - INFO:     参考信息 (活跃度、进度、趋势)
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..domain.event_log import EventLog, EventType
from .protocol_checker import ProtocolChecker
from ..domain.task_manager import TaskManager


class SignalLevel(str, Enum):
    """信号严重等级"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Signal:
    """单个健康信号"""
    name: str
    level: SignalLevel
    category: str
    value: Any
    message: str
    suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["level"] = self.level.value
        return d


@dataclass
class HealthReport:
    """项目健康报告"""
    timestamp: str = ""
    signals: List[Signal] = field(default_factory=list)
    score: float = 0.0
    summary: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    @property
    def critical_count(self) -> int:
        return sum(1 for s in self.signals if s.level == SignalLevel.CRITICAL)

    @property
    def warning_count(self) -> int:
        return sum(1 for s in self.signals if s.level == SignalLevel.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for s in self.signals if s.level == SignalLevel.INFO)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "score": round(self.score, 1),
            "critical": self.critical_count,
            "warnings": self.warning_count,
            "infos": self.info_count,
            "signals": [s.to_dict() for s in self.signals],
            "summary": self.summary,
        }


class HealthExtractor:
    """项目健康信号提取器

    从三大数据源提取信号:
      1. ProtocolChecker — 协议遵循检查
      2. EventLog — 审计日志分析 (活跃度、完整性、冲突)
      3. TaskManager — 任务进度与质量
    """

    def __init__(self, project_root: Path, config: Dict[str, Any]):
        self.project_root = Path(project_root)
        self.config = config

    def extract(self) -> HealthReport:
        """执行全量信号提取，返回健康报告"""
        report = HealthReport()

        self._extract_protocol_signals(report)
        self._extract_eventlog_signals(report)
        self._extract_task_signals(report)

        report.score = self._calculate_score(report)
        report.summary = {
            "score": round(report.score, 1),
            "grade": self._score_to_grade(report.score),
            "critical": report.critical_count,
            "warnings": report.warning_count,
            "infos": report.info_count,
            "total_signals": len(report.signals),
        }
        return report

    # ── Protocol Checker Signals ──────────────────────────────

    def _extract_protocol_signals(self, report: HealthReport):
        """从 ProtocolChecker 提取协议合规信号"""
        try:
            checker = ProtocolChecker(self.project_root, self.config)
            results = checker.check_all()
            summary = checker.get_summary(results)
        except Exception:
            report.signals.append(Signal(
                name="protocol_checker_unavailable",
                level=SignalLevel.WARNING,
                category="protocol",
                value=None,
                message="协议检查器初始化失败",
                suggestion="检查项目配置是否完整",
            ))
            return

        errors = summary.get("errors", 0)
        warnings = summary.get("warnings", 0)

        if errors > 0:
            report.signals.append(Signal(
                name="protocol_errors",
                level=SignalLevel.CRITICAL,
                category="protocol",
                value=errors,
                message=f"发现 {errors} 个协议违规错误",
                suggestion="运行 `vibecollab check` 查看详情并修复",
            ))

        if warnings > 0:
            report.signals.append(Signal(
                name="protocol_warnings",
                level=SignalLevel.WARNING,
                category="protocol",
                value=warnings,
                message=f"发现 {warnings} 个协议警告",
                suggestion="检查文档是否需要更新",
            ))

        if summary.get("all_passed", False):
            report.signals.append(Signal(
                name="protocol_compliance",
                level=SignalLevel.INFO,
                category="protocol",
                value=True,
                message="所有协议检查通过",
            ))

    # ── EventLog Signals ──────────────────────────────────────

    def _extract_eventlog_signals(self, report: HealthReport):
        """从 EventLog 提取审计日志信号"""
        try:
            log = EventLog(self.project_root)
        except Exception:
            return

        # 信号1: 日志完整性
        try:
            violations = log.verify_integrity()
            if violations:
                report.signals.append(Signal(
                    name="log_integrity",
                    level=SignalLevel.CRITICAL,
                    category="integrity",
                    value=len(violations),
                    message=f"事件日志存在 {len(violations)} 处完整性问题",
                    suggestion="检查 .vibecollab/events.jsonl 是否被非法修改",
                ))
            else:
                report.signals.append(Signal(
                    name="log_integrity",
                    level=SignalLevel.INFO,
                    category="integrity",
                    value=0,
                    message="事件日志完整性验证通过",
                ))
        except Exception:
            pass

        # 信号2: 项目活跃度
        try:
            total_events = log.count()
            report.signals.append(Signal(
                name="total_events",
                level=SignalLevel.INFO,
                category="activity",
                value=total_events,
                message=f"累计 {total_events} 个事件记录",
            ))

            seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
            recent = log.query(since=seven_days_ago)
            if len(recent) == 0 and total_events > 0:
                report.signals.append(Signal(
                    name="project_inactive",
                    level=SignalLevel.WARNING,
                    category="activity",
                    value=0,
                    message="过去 7 天无项目活动",
                    suggestion="检查项目是否处于停滞状态",
                ))
        except Exception:
            pass

        # 信号3: 未解决冲突
        try:
            conflicts_detected = log.query(event_type=EventType.CONFLICT_DETECTED.value)
            conflicts_resolved = log.query(event_type=EventType.CONFLICT_RESOLVED.value)
            unresolved = len(conflicts_detected) - len(conflicts_resolved)
            if unresolved > 0:
                report.signals.append(Signal(
                    name="unresolved_conflicts",
                    level=SignalLevel.WARNING,
                    category="collaboration",
                    value=unresolved,
                    message=f"{unresolved} 个冲突尚未解决",
                    suggestion="运行 `vibecollab dev conflicts` 查看冲突详情",
                ))
        except Exception:
            pass

        # 信号4: 验证失败率
        try:
            failures = log.query(event_type=EventType.VALIDATION_FAILED.value)
            passes = log.query(event_type=EventType.VALIDATION_PASSED.value)
            total_validations = len(failures) + len(passes)
            if total_validations > 0:
                fail_rate = len(failures) / total_validations
                level = (SignalLevel.WARNING if fail_rate > 0.3
                         else SignalLevel.INFO)
                report.signals.append(Signal(
                    name="validation_fail_rate",
                    level=level,
                    category="quality",
                    value=round(fail_rate, 2),
                    message=f"验证失败率 {fail_rate:.0%} ({len(failures)}/{total_validations})",
                    suggestion="检查任务质量和固化流程" if fail_rate > 0.3 else None,
                ))
        except Exception:
            pass

    # ── Task Manager Signals ──────────────────────────────────

    def _extract_task_signals(self, report: HealthReport):
        """从 TaskManager 提取任务进度信号"""
        try:
            mgr = TaskManager(self.project_root)
        except Exception:
            return

        total = mgr.count()
        if total == 0:
            report.signals.append(Signal(
                name="no_tasks",
                level=SignalLevel.INFO,
                category="tasks",
                value=0,
                message="暂无任务记录",
            ))
            return

        done = mgr.count(status="DONE")
        todo = mgr.count(status="TODO")
        in_progress = mgr.count(status="IN_PROGRESS")
        in_review = mgr.count(status="REVIEW")

        # 信号1: 任务完成率
        completion_rate = done / total
        report.signals.append(Signal(
            name="task_completion_rate",
            level=SignalLevel.INFO,
            category="tasks",
            value=round(completion_rate, 2),
            message=f"任务完成率 {completion_rate:.0%} ({done}/{total})",
        ))

        # 信号2: 积压检测
        if todo > 5:
            report.signals.append(Signal(
                name="task_backlog",
                level=SignalLevel.WARNING,
                category="tasks",
                value=todo,
                message=f"{todo} 个待办任务积压",
                suggestion="考虑优先级排序或拆分任务",
            ))

        # 信号3: 审核瓶颈
        active = in_progress + in_review + todo
        if active > 0 and in_review / active > 0.5:
            report.signals.append(Signal(
                name="review_bottleneck",
                level=SignalLevel.WARNING,
                category="tasks",
                value=in_review,
                message=f"{in_review} 个任务等待审核 (占活跃任务 {in_review/active:.0%})",
                suggestion="加速审核流程，避免阻塞",
            ))

        # 信号4: 任务分布
        report.signals.append(Signal(
            name="task_distribution",
            level=SignalLevel.INFO,
            category="tasks",
            value={"todo": todo, "in_progress": in_progress, "review": in_review, "done": done},
            message=f"任务分布: TODO={todo} IN_PROGRESS={in_progress} REVIEW={in_review} DONE={done}",
        ))

        # 信号5: 依赖阻塞
        try:
            all_tasks = mgr.list_tasks()
            blocked = []
            for task in all_tasks:
                if task.status == "DONE":
                    continue
                for dep_id in (task.dependencies or []):
                    dep = mgr.get_task(dep_id)
                    if dep and dep.status != "DONE":
                        blocked.append(task.id)
                        break

            if blocked:
                report.signals.append(Signal(
                    name="dependency_blocked",
                    level=SignalLevel.WARNING,
                    category="tasks",
                    value=len(blocked),
                    message=f"{len(blocked)} 个任务被依赖阻塞: {', '.join(blocked[:5])}",
                    suggestion="优先完成阻塞链上的前置任务",
                ))
        except Exception:
            pass

        # 信号6: 负载均衡
        try:
            from collections import Counter
            active_tasks = [t for t in mgr.list_tasks() if t.status != "DONE" and t.assignee]
            if len(active_tasks) >= 2:
                load = Counter(t.assignee for t in active_tasks)
                values = list(load.values())
                avg = sum(values) / len(values)
                if len(values) > 1:
                    variance = sum((v - avg) ** 2 for v in values) / len(values)
                    std_dev = variance ** 0.5
                    if std_dev > avg * 0.5 and avg > 0:
                        report.signals.append(Signal(
                            name="load_imbalance",
                            level=SignalLevel.WARNING,
                            category="collaboration",
                            value=dict(load),
                            message=f"负载不均衡: {dict(load)}",
                            suggestion="考虑重新分配任务",
                        ))
        except Exception:
            pass

    # ── Scoring ───────────────────────────────────────────────

    @staticmethod
    def _calculate_score(report: HealthReport) -> float:
        """根据信号计算健康评分 (0-100)

        评分规则:
          - 基础分 100
          - 每个 CRITICAL: -25
          - 每个 WARNING: -10
          - 最低 0 分
        """
        score = 100.0
        score -= report.critical_count * 25
        score -= report.warning_count * 10
        return max(0.0, min(100.0, score))

    @staticmethod
    def _score_to_grade(score: float) -> str:
        """分数转等级"""
        if score >= 90:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 50:
            return "C"
        elif score >= 30:
            return "D"
        else:
            return "F"
