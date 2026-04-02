"""
Insight Signal -- structured signal collection and candidate Insight recommendation.

Extracts candidate Insights from git incremental history, document change diffs,
and Task state changes, replacing pure LLM-based reasoning for insight distillation.

Storage structure:
    .vibecollab/
    └── insight_signal.json    # Signal snapshot (last distillation timestamp + commit hash)

Core flow:
    1. Read insight_signal.json for the last snapshot
    2. Collect incremental signals from snapshot to HEAD (git log, doc diff, Task changes)
    3. Analyze signals to generate candidate Insight list
    4. After user confirmation, call InsightManager.create() to persist
    5. Update snapshot to current HEAD
"""

import json
import re
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class SignalSnapshot:
    """Signal snapshot -- records the state of last insight distillation"""

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
    """Single commit signal"""

    hash: str
    subject: str
    author: str
    date: str
    files_changed: List[str] = field(default_factory=list)


@dataclass
class InsightCandidate:
    """Candidate Insight -- recommended item from suggest output"""

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
    """Collect candidate Insights from structured signals

    Usage:
        collector = InsightSignalCollector(project_root=Path("."))
        candidates = collector.suggest()
        # After user selection...
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
        """Load signal snapshot"""
        if not self.signal_path.exists():
            return SignalSnapshot()
        try:
            with open(self.signal_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return SignalSnapshot.from_dict(data)
        except Exception:
            return SignalSnapshot()

    def save_snapshot(self, snapshot: SignalSnapshot) -> None:
        """Save signal snapshot"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self.signal_path, "w", encoding="utf-8") as f:
            json.dump(snapshot.to_dict(), f, indent=2, ensure_ascii=False)

    def update_snapshot(
        self,
        commit_hash: str = "",
        insight_id: str = "",
    ) -> SignalSnapshot:
        """Update snapshot to current state"""
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
        """Collect incremental git commit signals"""
        cmd = ["git", "log", "--pretty=format:%H|%s|%an|%aI", "--no-merges"]
        if since_commit:
            cmd.append(f"{since_commit}..HEAD")
        else:
            cmd.extend(["-20"])  # No snapshot, get latest 20 entries

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
        """Detect changes in key documents

        Returns:
            {doc_name: [change summary lines]} dict
        """
        key_docs = [
            "docs/CONTEXT.md",
            "docs/context.yaml",
            "docs/DECISIONS.md",
            "docs/decisions.yaml",
            "docs/ROADMAP.md",
            "docs/roadmap.yaml",
            "docs/CHANGELOG.md",
            "docs/changelog.yaml",
        ]
        changes: Dict[str, List[str]] = {}

        for doc in key_docs:
            diff_lines = self._get_doc_diff(doc, since_commit)
            if diff_lines:
                changes[doc] = diff_lines
        return changes

    def collect_task_changes(self) -> Dict[str, Any]:
        """Detect Task changes"""
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
    # Suggest -- candidate Insight generation
    # ------------------------------------------------------------------

    def suggest(self) -> List[InsightCandidate]:
        """Recommend candidate Insights based on structured signals

        Analysis flow:
        1. Load snapshot for last distillation point
        2. Collect incremental git commits
        3. Collect document change diffs
        4. Collect Task changes
        5. Extract candidate Insights from signals
        """
        snapshot = self.load_snapshot()
        since = snapshot.last_commit

        # Collect three types of signals
        git_signals = self.collect_git_signals(since)
        doc_changes = self.collect_doc_changes(since)
        task_changes = self.collect_task_changes()

        candidates: List[InsightCandidate] = []

        # 1. Extract from git commits
        candidates.extend(self._analyze_git_signals(git_signals))

        # 2. Extract from document changes
        candidates.extend(self._analyze_doc_changes(doc_changes))

        # 3. Extract from Task completions
        candidates.extend(self._analyze_task_changes(task_changes))

        # Deduplicate by title similarity
        candidates = self._deduplicate(candidates)

        # Sort by confidence
        candidates.sort(key=lambda c: c.confidence, reverse=True)

        return candidates

    # ------------------------------------------------------------------
    # Signal analysis -- extract candidates from signals
    # ------------------------------------------------------------------

    def _analyze_git_signals(
        self, signals: List[CommitSignal]
    ) -> List[InsightCandidate]:
        """Extract candidate Insights from git commit history"""
        candidates: List[InsightCandidate] = []
        if not signals:
            return candidates

        # Strategy 1: Identify new features / major changes (feat/fix/refactor)
        feature_commits = [
            s for s in signals
            if any(p in s.subject.lower() for p in
                   ("feat", "feature", "add", "implement"))
        ]
        if feature_commits:
            candidates.append(InsightCandidate(
                title=self._summarize_commits(feature_commits, "feature"),
                tags=self._extract_tags_from_commits(feature_commits),
                category="workflow",
                reason=f"Detected {len(feature_commits)} new feature commits",
                source_signal="git_feature",
                confidence=0.7,
            ))

        # Strategy 2: Identify bug fix patterns
        fix_commits = [
            s for s in signals
            if any(p in s.subject.lower() for p in
                   ("fix", "bug", "hotfix", "patch"))
        ]
        if fix_commits:
            candidates.append(InsightCandidate(
                title=self._summarize_commits(fix_commits, "debug"),
                tags=self._extract_tags_from_commits(fix_commits) + ["debug"],
                category="debug",
                reason=f"Detected {len(fix_commits)} bug fix commits",
                source_signal="git_bugfix",
                confidence=0.6,
            ))

        # Strategy 3: Identify refactoring patterns
        refactor_commits = [
            s for s in signals
            if any(p in s.subject.lower() for p in
                   ("refactor", "cleanup", "optimize"))
        ]
        if refactor_commits:
            candidates.append(InsightCandidate(
                title=self._summarize_commits(refactor_commits, "technique"),
                tags=self._extract_tags_from_commits(refactor_commits)
                + ["refactor"],
                category="technique",
                reason=f"Detected {len(refactor_commits)} refactoring commits",
                source_signal="git_refactor",
                confidence=0.6,
            ))

        # Strategy 4: Large file changes (possible major decision)
        large_commits = [s for s in signals if len(s.files_changed) >= 10]
        if large_commits:
            candidates.append(InsightCandidate(
                title=f"Large-scale change: {large_commits[0].subject}",
                tags=["architecture", "large-change"],
                category="decision",
                reason=(
                    f"Detected {len(large_commits)} large-scale commits"
                    f" (>=10 files)"
                ),
                source_signal="git_large_change",
                confidence=0.5,
            ))

        return candidates

    def _analyze_doc_changes(
        self, changes: Dict[str, List[str]]
    ) -> List[InsightCandidate]:
        """Extract candidate Insights from document changes"""
        candidates: List[InsightCandidate] = []
        if not changes:
            return candidates

        # DECISIONS changes -> decision-type Insight
        decisions_changes = changes.get("docs/DECISIONS.md", []) + changes.get("docs/decisions.yaml", [])
        if decisions_changes:
            new_decisions = [
                line for line in decisions_changes
                if line.startswith("+") and "DECISION-" in line
            ]
            if new_decisions:
                candidates.append(InsightCandidate(
                    title="New decision record: " + self._extract_decision_title(
                        new_decisions
                    ),
                    tags=["decision", "architecture"],
                    category="decision",
                    reason=f"Added {len(new_decisions)} decisions in DECISIONS.md",
                    source_signal="doc_decisions",
                    confidence=0.8,
                ))

        # ROADMAP changes -> planning-type Insight
        roadmap_changes = changes.get("docs/ROADMAP.md", []) + changes.get("docs/roadmap.yaml", [])
        if roadmap_changes:
            completed = [
                line for line in roadmap_changes
                if line.startswith("+") and ("[DONE]" in line or "\u2705" in line or "[x]" in line)
            ]
            if completed:
                candidates.append(InsightCandidate(
                    title="Milestone completion experience",
                    tags=["milestone", "planning"],
                    category="workflow",
                    reason=(
                        f"Added {len(completed)} completed items in ROADMAP.md"
                    ),
                    source_signal="doc_roadmap",
                    confidence=0.6,
                ))

        # CONTEXT major changes -> context switch signal
        context_changes = changes.get("docs/CONTEXT.md", []) + changes.get("docs/context.yaml", [])
        if context_changes:
            added = [line for line in context_changes if line.startswith("+")]
            if len(added) > 10:
                candidates.append(InsightCandidate(
                    title="Development direction switch experience",
                    tags=["context-switch", "workflow"],
                    category="workflow",
                    reason=(
                        f"CONTEXT.md major change ({len(added)} lines added)"
                    ),
                    source_signal="doc_context",
                    confidence=0.4,
                ))

        return candidates

    def _analyze_task_changes(
        self, task_changes: Dict[str, Any]
    ) -> List[InsightCandidate]:
        """Extract candidate Insights from Task completions"""
        candidates: List[InsightCandidate] = []
        completed = task_changes.get("completed", [])
        if len(completed) >= 3:
            candidates.append(InsightCandidate(
                title=f"Batch task completion: {len(completed)} Tasks closed",
                tags=["task-management", "productivity"],
                category="workflow",
                reason=f"{len(completed)} Tasks completed",
                source_signal="task_completed",
                confidence=0.5,
            ))
        return candidates

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def _get_head_commit(self) -> str:
        """Get HEAD commit hash"""
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
        """Get list of files changed in a commit"""
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
        """Get incremental diff of a document"""
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
        """Generate candidate title from multiple commits"""
        if not commits:
            return f"Unnamed {kind}"
        if len(commits) == 1:
            return commits[0].subject
        # Use the latest commit's subject as the main title
        return f"{commits[0].subject} and {len(commits)} other changes"

    def _extract_tags_from_commits(
        self, commits: List[CommitSignal]
    ) -> List[str]:
        """Extract tags from commit changed files"""
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
                # Extract module name from path
                if "/" in f:
                    module = f.split("/")[-1].replace(".py", "")
                    if module and not module.startswith("_"):
                        tags.add(module)
        return list(tags)[:8]  # Max 8 tags

    def _extract_decision_title(self, lines: List[str]) -> str:
        """Extract decision title from new lines in DECISIONS.md"""
        for line in lines:
            match = re.search(r"DECISION-\d+[:\s]+(.+)", line)
            if match:
                return match.group(1).strip().strip("#").strip()
        return "New architecture/technical decision"

    def _deduplicate(
        self, candidates: List[InsightCandidate]
    ) -> List[InsightCandidate]:
        """Deduplicate by title similarity"""
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
        """Simple title similarity (Jaccard)"""
        words_a = set(a.lower().split())
        words_b = set(b.lower().split())
        if not words_a or not words_b:
            return 0.0
        intersection = words_a & words_b
        union = words_a | words_b
        return len(intersection) / len(union)
