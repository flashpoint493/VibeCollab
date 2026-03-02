"""
Insight Signal — 结构化信号收集与候选 Insight 推荐

从 git 增量历史 + 文档变更 diff + Task 变化等结构化信号中提取候选 Insight，
替代纯 LLM 推理的沉淀方式。

存储结构：
    .vibecollab/
    └── insight_signal.json    # 信号快照（上次沉淀时间点 + commit hash）

核心流程：
    1. 读取 insight_signal.json 获取上次快照
    2. 从快照到 HEAD 收集增量信号（git log、文档 diff、Task 变化）
    3. 分析信号生成候选 Insight 列表
    4. 用户 confirm 后调用 InsightManager.create() 入库
    5. 更新快照到当前 HEAD
"""

import json
import re
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class SignalSnapshot:
    """信号快照 — 记录上次 insight 沉淀的状态"""

    last_commit: str = ""
    last_timestamp: str = ""
    last_insight_id: str = ""
    total_suggests: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SignalSnapshot":
        return cls(
            last_commit=data.get("last_commit", ""),
            last_timestamp=data.get("last_timestamp", ""),
            last_insight_id=data.get("last_insight_id", ""),
            total_suggests=data.get("total_suggests", 0),
        )


@dataclass
class CommitSignal:
    """单条 commit 信号"""

    hash: str
    subject: str
    author: str
    date: str
    files_changed: List[str] = field(default_factory=list)


@dataclass
class InsightCandidate:
    """候选 Insight — suggest 输出的推荐条目"""

    title: str
    tags: List[str] = field(default_factory=list)
    category: str = "workflow"
    reason: str = ""
    source_signal: str = ""
    confidence: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Signal collector
# ---------------------------------------------------------------------------


class InsightSignalCollector:
    """从结构化信号中收集候选 Insight

    Usage:
        collector = InsightSignalCollector(project_root=Path("."))
        candidates = collector.suggest()
        # 用户选择后...
        collector.update_snapshot(commit_hash="abc123", insight_id="INS-016")
    """

    SIGNAL_FILE = "insight_signal.json"

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.data_dir = self.project_root / ".vibecollab"
        self.signal_path = self.data_dir / self.SIGNAL_FILE

    # ------------------------------------------------------------------
    # Snapshot CRUD
    # ------------------------------------------------------------------

    def load_snapshot(self) -> SignalSnapshot:
        """加载信号快照"""
        if not self.signal_path.exists():
            return SignalSnapshot()
        try:
            with open(self.signal_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return SignalSnapshot.from_dict(data)
        except Exception:
            return SignalSnapshot()

    def save_snapshot(self, snapshot: SignalSnapshot) -> None:
        """保存信号快照"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self.signal_path, "w", encoding="utf-8") as f:
            json.dump(snapshot.to_dict(), f, indent=2, ensure_ascii=False)

    def update_snapshot(
        self,
        commit_hash: str = "",
        insight_id: str = "",
    ) -> SignalSnapshot:
        """更新快照到当前状态"""
        snapshot = self.load_snapshot()
        if commit_hash:
            snapshot.last_commit = commit_hash
        else:
            snapshot.last_commit = self._get_head_commit()
        snapshot.last_timestamp = datetime.now(timezone.utc).isoformat()
        if insight_id:
            snapshot.last_insight_id = insight_id
        snapshot.total_suggests += 1
        self.save_snapshot(snapshot)
        return snapshot

    # ------------------------------------------------------------------
    # Signal collection
    # ------------------------------------------------------------------

    def collect_git_signals(
        self, since_commit: str = ""
    ) -> List[CommitSignal]:
        """收集 git 增量 commit 信号"""
        cmd = ["git", "log", "--pretty=format:%H|%s|%an|%aI", "--no-merges"]
        if since_commit:
            cmd.append(f"{since_commit}..HEAD")
        else:
            cmd.extend(["-20"])  # 没有快照时取最近 20 条

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=15,
                encoding="utf-8",
                errors="replace",
            )
            if result.returncode != 0:
                return []
        except BaseException:
            return []

        signals = []
        stdout = result.stdout or ""
        for line in stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("|", 3)
            if len(parts) < 4:
                continue
            commit_hash, subject, author, date = parts
            files = self._get_commit_files(commit_hash.strip())
            signals.append(CommitSignal(
                hash=commit_hash.strip(),
                subject=subject.strip(),
                author=author.strip(),
                date=date.strip(),
                files_changed=files,
            ))
        return signals

    def collect_doc_changes(
        self, since_commit: str = ""
    ) -> Dict[str, List[str]]:
        """检测关键文档的变更

        Returns:
            {doc_name: [变更摘要行]} 字典
        """
        key_docs = [
            "docs/CONTEXT.md",
            "docs/DECISIONS.md",
            "docs/ROADMAP.md",
            "docs/CHANGELOG.md",
        ]
        changes: Dict[str, List[str]] = {}

        for doc in key_docs:
            diff_lines = self._get_doc_diff(doc, since_commit)
            if diff_lines:
                changes[doc] = diff_lines
        return changes

    def collect_task_changes(self) -> Dict[str, Any]:
        """检测 Task 变化"""
        tasks_file = self.data_dir / "tasks.json"
        if not tasks_file.exists():
            return {"new": [], "completed": [], "total": 0}
        try:
            with open(tasks_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            tasks = data if isinstance(data, list) else data.get("tasks", [])
            new_tasks = [
                t for t in tasks
                if isinstance(t, dict) and t.get("status") in ("TODO", "IN_PROGRESS")
            ]
            done_tasks = [
                t for t in tasks
                if isinstance(t, dict) and t.get("status") == "DONE"
            ]
            return {
                "new": [t.get("id", "?") for t in new_tasks],
                "completed": [t.get("id", "?") for t in done_tasks],
                "total": len(tasks),
            }
        except Exception:
            return {"new": [], "completed": [], "total": 0}

    # ------------------------------------------------------------------
    # Suggest — 候选 Insight 生成
    # ------------------------------------------------------------------

    def suggest(self) -> List[InsightCandidate]:
        """基于结构化信号推荐候选 Insight

        分析流程：
        1. 加载快照获取上次沉淀时间点
        2. 收集 git 增量 commit
        3. 收集文档变更 diff
        4. 收集 Task 变化
        5. 从信号中提取候选 Insight
        """
        snapshot = self.load_snapshot()
        since = snapshot.last_commit

        # 收集三类信号
        git_signals = self.collect_git_signals(since)
        doc_changes = self.collect_doc_changes(since)
        task_changes = self.collect_task_changes()

        candidates: List[InsightCandidate] = []

        # 1. 从 git commit 中提取
        candidates.extend(self._analyze_git_signals(git_signals))

        # 2. 从文档变更中提取
        candidates.extend(self._analyze_doc_changes(doc_changes))

        # 3. 从 Task 完成中提取
        candidates.extend(self._analyze_task_changes(task_changes))

        # 去重：按 title 相似度去重
        candidates = self._deduplicate(candidates)

        # 按 confidence 排序
        candidates.sort(key=lambda c: c.confidence, reverse=True)

        return candidates

    # ------------------------------------------------------------------
    # Signal analysis — 从信号中提取候选
    # ------------------------------------------------------------------

    def _analyze_git_signals(
        self, signals: List[CommitSignal]
    ) -> List[InsightCandidate]:
        """从 git commit 历史中提取候选 Insight"""
        candidates: List[InsightCandidate] = []
        if not signals:
            return candidates

        # 策略1: 识别新功能/重大变更 (feat/fix/refactor)
        feature_commits = [
            s for s in signals
            if any(p in s.subject.lower() for p in
                   ("feat", "feature", "新增", "实现", "add", "implement"))
        ]
        if feature_commits:
            subjects = [c.subject for c in feature_commits[:5]]
            candidates.append(InsightCandidate(
                title=self._summarize_commits(feature_commits, "feature"),
                tags=self._extract_tags_from_commits(feature_commits),
                category="workflow",
                reason=f"检测到 {len(feature_commits)} 个新功能 commit",
                source_signal="git_feature",
                confidence=0.7,
            ))

        # 策略2: 识别 bug 修复模式
        fix_commits = [
            s for s in signals
            if any(p in s.subject.lower() for p in
                   ("fix", "bug", "修复", "hotfix", "patch"))
        ]
        if fix_commits:
            candidates.append(InsightCandidate(
                title=self._summarize_commits(fix_commits, "debug"),
                tags=self._extract_tags_from_commits(fix_commits) + ["debug"],
                category="debug",
                reason=f"检测到 {len(fix_commits)} 个 bug 修复 commit",
                source_signal="git_bugfix",
                confidence=0.6,
            ))

        # 策略3: 识别重构模式
        refactor_commits = [
            s for s in signals
            if any(p in s.subject.lower() for p in
                   ("refactor", "重构", "cleanup", "清理", "optimize", "优化"))
        ]
        if refactor_commits:
            candidates.append(InsightCandidate(
                title=self._summarize_commits(refactor_commits, "technique"),
                tags=self._extract_tags_from_commits(refactor_commits)
                + ["refactor"],
                category="technique",
                reason=f"检测到 {len(refactor_commits)} 个重构 commit",
                source_signal="git_refactor",
                confidence=0.6,
            ))

        # 策略4: 大量文件变更 (可能是重大决策)
        large_commits = [s for s in signals if len(s.files_changed) >= 10]
        if large_commits:
            candidates.append(InsightCandidate(
                title=f"大规模变更: {large_commits[0].subject}",
                tags=["architecture", "large-change"],
                category="decision",
                reason=(
                    f"检测到 {len(large_commits)} 个大规模变更 commit"
                    f" (≥10 文件)"
                ),
                source_signal="git_large_change",
                confidence=0.5,
            ))

        return candidates

    def _analyze_doc_changes(
        self, changes: Dict[str, List[str]]
    ) -> List[InsightCandidate]:
        """从文档变更中提取候选 Insight"""
        candidates: List[InsightCandidate] = []
        if not changes:
            return candidates

        # DECISIONS.md 变更 → 决策类 Insight
        if "docs/DECISIONS.md" in changes:
            decision_lines = changes["docs/DECISIONS.md"]
            new_decisions = [
                line for line in decision_lines
                if line.startswith("+") and "DECISION-" in line
            ]
            if new_decisions:
                candidates.append(InsightCandidate(
                    title="新决策记录: " + self._extract_decision_title(
                        new_decisions
                    ),
                    tags=["decision", "architecture"],
                    category="decision",
                    reason=f"DECISIONS.md 中新增 {len(new_decisions)} 条决策",
                    source_signal="doc_decisions",
                    confidence=0.8,
                ))

        # ROADMAP.md 变更 → 规划类 Insight
        if "docs/ROADMAP.md" in changes:
            roadmap_lines = changes["docs/ROADMAP.md"]
            completed = [
                line for line in roadmap_lines
                if line.startswith("+") and ("✅" in line or "[x]" in line)
            ]
            if completed:
                candidates.append(InsightCandidate(
                    title="里程碑完成经验",
                    tags=["milestone", "planning"],
                    category="workflow",
                    reason=(
                        f"ROADMAP.md 中新增 {len(completed)} 个已完成项"
                    ),
                    source_signal="doc_roadmap",
                    confidence=0.6,
                ))

        # CONTEXT.md 大幅变更 → 上下文切换信号
        if "docs/CONTEXT.md" in changes:
            context_lines = changes["docs/CONTEXT.md"]
            added = [l for l in context_lines if l.startswith("+")]
            if len(added) > 10:
                candidates.append(InsightCandidate(
                    title="开发方向切换经验",
                    tags=["context-switch", "workflow"],
                    category="workflow",
                    reason=(
                        f"CONTEXT.md 大幅变更 ({len(added)} 行新增)"
                    ),
                    source_signal="doc_context",
                    confidence=0.4,
                ))

        return candidates

    def _analyze_task_changes(
        self, task_changes: Dict[str, Any]
    ) -> List[InsightCandidate]:
        """从 Task 完成中提取候选 Insight"""
        candidates: List[InsightCandidate] = []
        completed = task_changes.get("completed", [])
        if len(completed) >= 3:
            candidates.append(InsightCandidate(
                title=f"批量任务完成: {len(completed)} 个 Task 关闭",
                tags=["task-management", "productivity"],
                category="workflow",
                reason=f"{len(completed)} 个 Task 已完成",
                source_signal="task_completed",
                confidence=0.5,
            ))
        return candidates

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def _get_head_commit(self) -> str:
        """获取 HEAD commit hash"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=5,
                encoding="utf-8",
                errors="replace",
            )
            return (result.stdout or "").strip() if result.returncode == 0 else ""
        except BaseException:
            return ""

    def _get_commit_files(self, commit_hash: str) -> List[str]:
        """获取某个 commit 变更的文件列表"""
        try:
            result = subprocess.run(
                ["git", "diff-tree", "--no-commit-id", "--name-only", "-r",
                 commit_hash],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=5,
                encoding="utf-8",
                errors="replace",
            )
            if result.returncode != 0:
                return []
            return [
                f for f in (result.stdout or "").strip().split("\n") if f.strip()
            ]
        except BaseException:
            return []

    def _get_doc_diff(
        self, doc_path: str, since_commit: str = ""
    ) -> List[str]:
        """获取文档的增量 diff"""
        full_path = self.project_root / doc_path
        if not full_path.exists():
            return []

        cmd = ["git", "diff"]
        if since_commit:
            cmd.append(since_commit)
        cmd.extend(["--", doc_path])

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=10,
                encoding="utf-8",
                errors="replace",
            )
            if result.returncode != 0:
                return []
            lines = (result.stdout or "").strip().split("\n")
            return [
                line for line in lines
                if line.startswith("+") or line.startswith("-")
                if not line.startswith("+++") and not line.startswith("---")
            ]
        except BaseException:
            return []

    def _summarize_commits(
        self, commits: List[CommitSignal], kind: str
    ) -> str:
        """从多个 commit 中生成候选标题"""
        if not commits:
            return f"未命名 {kind}"
        if len(commits) == 1:
            return commits[0].subject
        # 取最新 commit 的 subject 作为主标题
        return f"{commits[0].subject} 等 {len(commits)} 项变更"

    def _extract_tags_from_commits(
        self, commits: List[CommitSignal]
    ) -> List[str]:
        """从 commit 变更文件中提取标签"""
        tags = set()
        for commit in commits:
            for f in commit.files_changed:
                if f.endswith(".py"):
                    tags.add("python")
                elif f.endswith((".js", ".ts", ".tsx")):
                    tags.add("frontend")
                elif f.endswith((".yaml", ".yml", ".json", ".toml")):
                    tags.add("config")
                if f.startswith("tests/"):
                    tags.add("testing")
                if f.startswith("docs/"):
                    tags.add("docs")
                # 从路径提取模块名
                if "/" in f:
                    module = f.split("/")[-1].replace(".py", "")
                    if module and not module.startswith("_"):
                        tags.add(module)
        return list(tags)[:8]  # 最多 8 个 tag

    def _extract_decision_title(self, lines: List[str]) -> str:
        """从 DECISIONS.md 新增行中提取决策标题"""
        for line in lines:
            match = re.search(r"DECISION-\d+[:\s]+(.+)", line)
            if match:
                return match.group(1).strip().strip("#").strip()
        return "新的架构/技术决策"

    def _deduplicate(
        self, candidates: List[InsightCandidate]
    ) -> List[InsightCandidate]:
        """按 title 相似度去重"""
        if len(candidates) <= 1:
            return candidates

        seen_titles: List[str] = []
        result: List[InsightCandidate] = []
        for c in candidates:
            is_dup = False
            for existing in seen_titles:
                if self._title_similarity(c.title, existing) > 0.6:
                    is_dup = True
                    break
            if not is_dup:
                result.append(c)
                seen_titles.append(c.title)
        return result

    @staticmethod
    def _title_similarity(a: str, b: str) -> float:
        """简单的标题相似度（Jaccard）"""
        words_a = set(a.lower().split())
        words_b = set(b.lower().split())
        if not words_a or not words_b:
            return 0.0
        intersection = words_a & words_b
        union = words_a | words_b
        return len(intersection) / len(union)
