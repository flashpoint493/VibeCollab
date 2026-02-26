"""
Protocol Checker - 协议遵循情况检查器
用于检查 AI 是否遵循了协作协议中的各项要求
"""

import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .git_utils import get_git_status, is_git_repo


@dataclass
class CheckResult:
    """检查结果"""
    name: str
    passed: bool
    message: str
    severity: str  # "error", "warning", "info"
    suggestion: Optional[str] = None


class ProtocolChecker:
    """协议检查器"""

    def __init__(self, project_root: Path, config: Optional[Dict] = None):
        self.project_root = Path(project_root)
        self.config = config or {}
        self.docs_dir = self.project_root / "docs"

    def check_all(self) -> List[CheckResult]:
        """执行所有协议检查

        Returns:
            List[CheckResult]: 检查结果列表
        """
        results = []

        # 检查 Git 相关
        results.extend(self._check_git_protocol())

        # 检查文档更新
        results.extend(self._check_documentation_protocol())

        # 检查对话流程协议
        results.extend(self._check_dialogue_protocol())

        # 检查多开发者协议
        results.extend(self._check_multi_developer_protocol())

        # 检查关联文档一致性
        results.extend(self._check_document_consistency())

        return results

    def _check_git_protocol(self) -> List[CheckResult]:
        """检查 Git 协议遵循情况"""
        results = []

        # 检查是否是 Git 仓库
        if not is_git_repo(self.project_root):
            results.append(CheckResult(
                name="Git 仓库初始化",
                passed=False,
                message="项目目录不是 Git 仓库",
                severity="error",
                suggestion="运行 'git init' 初始化仓库，或使用 'vibecollab init' 创建新项目"
            ))
            return results  # 如果不是 Git 仓库，其他检查无意义

        # 检查是否有未提交的更改
        git_status = get_git_status(self.project_root)
        if git_status and git_status.get("has_uncommitted_changes"):
            results.append(CheckResult(
                name="Git 提交要求",
                passed=False,
                message="存在未提交的更改",
                severity="warning",
                suggestion="根据协议，每次有效对话后应执行 git commit。运行 'git status' 查看更改，然后提交"
            ))

        # 检查最近的提交时间（如果可能）
        last_commit_time = self._get_last_commit_time()
        if last_commit_time:
            hours_since_commit = (datetime.now() - last_commit_time).total_seconds() / 3600
            if hours_since_commit > 24:
                results.append(CheckResult(
                    name="Git 提交频率",
                    passed=True,
                    message=f"距离上次提交已过去 {int(hours_since_commit)} 小时",
                    severity="info",
                    suggestion="如果最近有对话产出，记得提交到 Git"
                ))

        return results

    def _check_documentation_protocol(self) -> List[CheckResult]:
        """检查文档更新协议"""
        results = []

        # 从配置读取更新阈值，默认 0.25 小时 = 15 分钟
        check_config = self.config.get("protocol_check", {}).get("checks", {}).get("documentation", {})
        threshold_hours = check_config.get("update_threshold_hours", 0.25)

        dialogue_protocol = self.config.get("dialogue_protocol", {})
        on_end = dialogue_protocol.get("on_end", {})
        required_files = on_end.get("update_files", [])

        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                results.append(CheckResult(
                    name=f"文档存在性: {file_path}",
                    passed=False,
                    message=f"必需文档不存在: {file_path}",
                    severity="error",
                    suggestion=f"创建文件 {file_path}，或使用 'vibecollab init' 初始化项目"
                ))
                continue

            # 检查文件是否在阈值时间内更新
            file_mtime = datetime.fromtimestamp(full_path.stat().st_mtime)
            hours_since_update = (datetime.now() - file_mtime).total_seconds() / 3600

            if hours_since_update > threshold_hours:
                if threshold_hours < 1:
                    time_desc = f"{int(threshold_hours * 60)} 分钟"
                else:
                    time_desc = f"{int(threshold_hours)} 小时"
                results.append(CheckResult(
                    name=f"文档更新: {file_path}",
                    passed=False,
                    message=f"文档 {file_path} 超过 {time_desc} 未更新",
                    severity="warning",
                    suggestion=f"根据协议，对话结束后应更新 {file_path}。如果最近有对话，请更新此文档"
                ))

        # 检查 PRD.md（如果配置要求）
        prd_config = self.config.get("prd_management", {})
        if prd_config.get("enabled", False):
            prd_path = self.project_root / prd_config.get("prd_file", "docs/PRD.md")
            if not prd_path.exists():
                results.append(CheckResult(
                    name="PRD 文档",
                    passed=False,
                    message="PRD.md 文档不存在",
                    severity="warning",
                    suggestion="创建 docs/PRD.md 记录项目需求和需求变化"
                ))

        # 检查多开发者协作文档（如果启用多开发者模式）
        multi_dev_config = self.config.get("multi_developer", {})
        if multi_dev_config.get("enabled", False):
            collab_config = multi_dev_config.get("collaboration", {})
            collab_file = collab_config.get("file", "docs/developers/COLLABORATION.md")
            collab_path = self.project_root / collab_file

            if not collab_path.exists():
                results.append(CheckResult(
                    name="协作文档",
                    passed=False,
                    message=f"多开发者协作文档不存在: {collab_file}",
                    severity="warning",
                    suggestion=f"创建 {collab_file} 记录开发者之间的协作关系、任务分配和依赖关系"
                ))
            else:
                # 检查文件是否最近更新（7天内）
                file_mtime = datetime.fromtimestamp(collab_path.stat().st_mtime)
                days_since_update = (datetime.now() - file_mtime).total_seconds() / 86400

                if days_since_update > 7:
                    results.append(CheckResult(
                        name="协作文档更新",
                        passed=True,
                        message=f"{collab_file} 已超过 7 天未更新",
                        severity="info",
                        suggestion="建议定期（每周）更新协作文档，记录任务进展和团队变更"
                    ))

        return results

    def _check_dialogue_protocol(self) -> List[CheckResult]:
        """检查对话流程协议"""
        results = []

        dialogue_protocol = self.config.get("dialogue_protocol", {})
        on_start = dialogue_protocol.get("on_start", {})
        required_reads = on_start.get("read_files", [])

        # 检查对话开始时应该读取的文件是否存在
        for file_path in required_reads:
            full_path = self.project_root / file_path
            if not full_path.exists():
                results.append(CheckResult(
                    name=f"对话开始文件: {file_path}",
                    passed=False,
                    message=f"对话开始时应该读取的文件不存在: {file_path}",
                    severity="error",
                    suggestion=f"确保文件 {file_path} 存在，或使用 'vibecollab init' 初始化项目"
                ))

        return results

    def _check_multi_developer_protocol(self) -> List[CheckResult]:
        """检查多开发者协议遵循情况"""
        results = []

        multi_dev_config = self.config.get("multi_developer", {})
        if not multi_dev_config.get("enabled", False):
            # 多开发者模式未启用，跳过检查
            return results

        developers = multi_dev_config.get("developers", [])

        developers_dir_name = multi_dev_config.get("context", {}).get(
            "per_developer_dir", "docs/developers"
        )
        developers_dir = self.project_root / developers_dir_name

        # 如果没有静态配置开发者列表，从文件系统动态发现
        if not developers:
            if developers_dir.exists():
                discovered = []
                for d in sorted(developers_dir.iterdir()):
                    if d.is_dir() and not d.name.startswith("."):
                        discovered.append({"id": d.name, "name": d.name})
                developers = discovered

            if not developers:
                results.append(CheckResult(
                    name="开发者配置",
                    passed=False,
                    message="多开发者模式已启用但未发现任何开发者",
                    severity="warning",
                    suggestion=(
                        "使用 'vibecollab dev init -d <name>' 初始化开发者，"
                        "或在 multi_developer.developers 中静态配置"
                    )
                ))
                return results

        # 检查每个开发者的上下文文件
        for dev in developers:
            dev_id = dev.get("id") if isinstance(dev, dict) else dev
            dev_name = (dev.get("name", dev_id) if isinstance(dev, dict) else dev)

            if not dev_id:
                results.append(CheckResult(
                    name="开发者ID",
                    passed=False,
                    message=f"开发者 '{dev_name}' 缺少必需的 'id' 字段",
                    severity="error",
                    suggestion="为每个开发者配置唯一的 id 标识符"
                ))
                continue

            dev_dir = developers_dir / dev_id

            # 检查开发者目录是否存在
            if not dev_dir.exists():
                results.append(CheckResult(
                    name=f"开发者目录: {dev_name}",
                    passed=False,
                    message=f"开发者 '{dev_name}' 的目录不存在: docs/developers/{dev_id}",
                    severity="error",
                    suggestion=f"创建目录 docs/developers/{dev_id} 并添加 CONTEXT.md 和 .metadata.yaml"
                ))
                continue

            # 检查 CONTEXT.md
            context_file = dev_dir / "CONTEXT.md"
            if not context_file.exists():
                results.append(CheckResult(
                    name=f"开发者上下文: {dev_name}",
                    passed=False,
                    message=f"开发者 '{dev_name}' 的 CONTEXT.md 不存在",
                    severity="error",
                    suggestion=f"创建 docs/developers/{dev_id}/CONTEXT.md 记录该开发者的工作上下文"
                ))
            else:
                # 检查 CONTEXT.md 是否最近更新（7天内有活动）
                file_mtime = datetime.fromtimestamp(context_file.stat().st_mtime)
                days_since_update = (datetime.now() - file_mtime).total_seconds() / 86400

                if days_since_update > 7:
                    results.append(CheckResult(
                        name=f"开发者上下文更新: {dev_name}",
                        passed=True,
                        message=f"开发者 '{dev_name}' 的 CONTEXT.md 已超过 {int(days_since_update)} 天未更新",
                        severity="info",
                        suggestion=f"如果 {dev_name} 最近有开发活动，记得更新其 CONTEXT.md"
                    ))
                else:
                    results.append(CheckResult(
                        name=f"开发者上下文更新: {dev_name}",
                        passed=True,
                        message=f"开发者 '{dev_name}' 的 CONTEXT.md 在 {int(days_since_update)} 天前更新",
                        severity="info"
                    ))

            # 检查 .metadata.yaml
            metadata_file = dev_dir / ".metadata.yaml"
            if not metadata_file.exists():
                results.append(CheckResult(
                    name=f"开发者元数据: {dev_name}",
                    passed=False,
                    message=f"开发者 '{dev_name}' 的 .metadata.yaml 不存在",
                    severity="warning",
                    suggestion=f"创建 docs/developers/{dev_id}/.metadata.yaml 记录开发者信息（角色、专长等）"
                ))

            # 检查 Git 提交中是否包含该开发者的上下文更新
            if context_file.exists():
                git_tracked = self._is_file_tracked_in_git(context_file)
                if not git_tracked:
                    results.append(CheckResult(
                        name=f"Git 追踪: {dev_name} CONTEXT.md",
                        passed=False,
                        message=f"开发者 '{dev_name}' 的 CONTEXT.md 未纳入 Git 版本控制",
                        severity="warning",
                        suggestion=f"运行 'git add docs/developers/{dev_id}/CONTEXT.md' 并提交"
                    ))

        # 检查协作文档
        collab_config = multi_dev_config.get("collaboration", {})
        collab_file = collab_config.get("file", "docs/developers/COLLABORATION.md")
        collab_path = self.project_root / collab_file

        if not collab_path.exists():
            results.append(CheckResult(
                name="多开发者协作文档",
                passed=False,
                message=f"协作文档不存在: {collab_file}",
                severity="error",
                suggestion=f"创建 {collab_file} 记录团队任务分配、里程碑和协作规则"
            ))
        else:
            # 检查协作文档更新频率
            file_mtime = datetime.fromtimestamp(collab_path.stat().st_mtime)
            days_since_update = (datetime.now() - file_mtime).total_seconds() / 86400

            if days_since_update > 7:
                results.append(CheckResult(
                    name="协作文档更新频率",
                    passed=True,
                    message=f"协作文档已超过 {int(days_since_update)} 天未更新",
                    severity="info",
                    suggestion="建议每周更新协作文档，记录任务进展和团队变更"
                ))

        # 检查冲突检测配置
        conflict_config = multi_dev_config.get("conflict_detection", {})
        if not conflict_config.get("enabled", True):
            results.append(CheckResult(
                name="冲突检测",
                passed=True,
                message="多开发者冲突检测已禁用",
                severity="warning",
                suggestion="建议启用冲突检测以避免多个开发者修改同一文件产生冲突"
            ))

        return results

    def _check_document_consistency(self) -> List[CheckResult]:
        """检查关联文档之间的一致性

        通过 project.yaml 中 documentation.consistency.linked_groups 配置关联文档组，
        检查同组文档的修改时间是否同步。

        支持三级检查粒度 (consistency_level):
          - local_mtime: 本地文件修改时间级别（最敏感，默认 15min 差异阈值）
          - git_commit:  git 提交时间级别（检查最近一次 commit 是否同步修改了组内文件）
          - release:     发布版本级别（最宽松，仅检查标签时的文件状态）
        """
        results = []

        doc_config = self.config.get("documentation", {})
        consistency_config = doc_config.get("consistency", {})
        if not consistency_config.get("enabled", False):
            return results

        linked_groups = consistency_config.get("linked_groups", [])
        default_level = consistency_config.get("default_level", "local_mtime")

        for group in linked_groups:
            group_name = group.get("name", "未命名组")
            files = group.get("files", [])
            level = group.get("level", default_level)
            threshold_minutes = group.get("threshold_minutes", 15)

            if len(files) < 2:
                continue

            if level == "local_mtime":
                max_inactive = group.get("max_inactive_hours", 0)
                results.extend(
                    self._check_mtime_consistency(
                        group_name, files, threshold_minutes, max_inactive
                    )
                )
            elif level == "git_commit":
                results.extend(
                    self._check_git_commit_consistency(group_name, files)
                )
            elif level == "release":
                results.extend(
                    self._check_release_consistency(group_name, files)
                )

        # 检查 key_files 中声明的所有文件存在性 + 可选陈旧性
        key_files = doc_config.get("key_files", [])
        for kf in key_files:
            path = kf.get("path", "")
            if not path:
                continue
            full_path = self.project_root / path
            if not full_path.exists():
                results.append(CheckResult(
                    name=f"关键文档存在性: {path}",
                    passed=False,
                    message=f"关键文档不存在: {path} (用途: {kf.get('purpose', '未知')})",
                    severity="warning",
                    suggestion=f"创建 {path}，它被声明为关键文档"
                ))
                continue

            # 可选陈旧性检查: max_stale_days
            max_stale_days = kf.get("max_stale_days")
            if max_stale_days is not None and max_stale_days > 0:
                file_mtime = datetime.fromtimestamp(full_path.stat().st_mtime)
                days_since_update = (datetime.now() - file_mtime).total_seconds() / 86400
                if days_since_update > max_stale_days:
                    results.append(CheckResult(
                        name=f"关键文档陈旧: {path}",
                        passed=False,
                        message=(
                            f"关键文档 {path} 已超过 {max_stale_days} 天未更新"
                            f"（上次更新: {int(days_since_update)} 天前）"
                        ),
                        severity="warning",
                        suggestion=(
                            f"根据触发条件「{kf.get('update_trigger', '未知')}」，"
                            f"请检查 {path} 是否需要更新"
                        )
                    ))

            # 可选跟随检查: watch_files — 当 watch 的文件更新了但本文件没跟上时告警
            watch_files = kf.get("watch_files", [])
            if watch_files and full_path.exists():
                my_mtime = datetime.fromtimestamp(full_path.stat().st_mtime)
                for wf in watch_files:
                    wf_path = self.project_root / wf
                    if wf_path.exists():
                        wf_mtime = datetime.fromtimestamp(wf_path.stat().st_mtime)
                        lag_minutes = (wf_mtime - my_mtime).total_seconds() / 60
                        if lag_minutes > 15:
                            results.append(CheckResult(
                                name=f"关键文档滞后: {path}",
                                passed=False,
                                message=(
                                    f"{wf} 已更新，但 {path} 落后 "
                                    f"{int(lag_minutes)} 分钟未同步"
                                ),
                                severity="warning",
                                suggestion=(
                                    f"触发条件「{kf.get('update_trigger', '未知')}」"
                                    f"可能已满足，请检查 {path} 是否需要更新"
                                )
                            ))

        return results

    def _check_mtime_consistency(
        self, group_name: str, files: List[str], threshold_minutes: float,
        max_inactive_hours: float = 0
    ) -> List[CheckResult]:
        """本地文件修改时间级别的一致性检查

        检查同组文件的 mtime 差异是否超过阈值。如果某个文件刚被修改，
        而关联文件没有跟随修改，产生 warning。

        Args:
            max_inactive_hours: 组级可配置的非活跃窗口（小时）。
                为 0 时使用默认值 24h。设为 -1 表示始终检查（禁用非活跃跳过）。
        """
        results = []
        file_mtimes: Dict[str, datetime] = {}

        for f in files:
            full_path = self.project_root / f
            if full_path.exists():
                file_mtimes[f] = datetime.fromtimestamp(full_path.stat().st_mtime)

        if len(file_mtimes) < 2:
            return results

        # 找到最近修改和最早修改的文件
        sorted_files = sorted(file_mtimes.items(), key=lambda x: x[1], reverse=True)
        newest_file, newest_time = sorted_files[0]
        oldest_file, oldest_time = sorted_files[-1]

        diff_minutes = (newest_time - oldest_time).total_seconds() / 60

        if diff_minutes > threshold_minutes:
            hours_since_newest = (datetime.now() - newest_time).total_seconds() / 3600
            # max_inactive_hours: -1 = 始终检查; 0 = 默认 24h; >0 = 自定义
            inactive_limit = (
                float("inf") if max_inactive_hours < 0
                else (max_inactive_hours if max_inactive_hours > 0 else 24)
            )
            if hours_since_newest < inactive_limit:
                stale_files = [
                    f for f, t in sorted_files[1:]
                    if (newest_time - t).total_seconds() / 60 > threshold_minutes
                ]
                for stale_f in stale_files:
                    stale_t = file_mtimes[stale_f]
                    diff_min = int((newest_time - stale_t).total_seconds() / 60)
                    results.append(CheckResult(
                        name=f"文档关联性: {group_name}",
                        passed=False,
                        message=(
                            f"{newest_file} 已修改，但关联文档 {stale_f} "
                            f"落后 {diff_min} 分钟未同步更新"
                        ),
                        severity="warning",
                        suggestion=(
                            f"关联组 [{group_name}] 要求同步更新。"
                            f"请检查 {stale_f} 是否需要跟随修改"
                        )
                    ))

        return results

    def _check_git_commit_consistency(
        self, group_name: str, files: List[str]
    ) -> List[CheckResult]:
        """Git 提交时间级别的一致性检查

        检查同组文件在最近一次 commit 中是否同时被修改。
        如果某文件在最近 commit 中被修改了，但关联文件不在同一次 commit 中，产生 warning。
        """
        results = []

        if not is_git_repo(self.project_root):
            return results

        # 获取每个文件最近一次被修改的 commit hash
        file_last_commits: Dict[str, Optional[str]] = {}
        for f in files:
            full_path = self.project_root / f
            if not full_path.exists():
                continue
            try:
                result = subprocess.run(
                    ["git", "log", "-1", "--format=%H", "--", f],
                    cwd=self.project_root,
                    capture_output=True, text=True
                )
                commit_hash = result.stdout.strip() if result.returncode == 0 else None
                file_last_commits[f] = commit_hash
            except BaseException:
                file_last_commits[f] = None

        if len(file_last_commits) < 2:
            return results

        # 找到最近被 commit 的文件
        commits_with_time: Dict[str, Optional[datetime]] = {}
        for f, commit_hash in file_last_commits.items():
            if commit_hash:
                try:
                    result = subprocess.run(
                        ["git", "log", "-1", "--format=%ct", commit_hash],
                        cwd=self.project_root,
                        capture_output=True, text=True
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        commits_with_time[f] = datetime.fromtimestamp(
                            int(result.stdout.strip())
                        )
                    else:
                        commits_with_time[f] = None
                except BaseException:
                    commits_with_time[f] = None
            else:
                commits_with_time[f] = None

        # 找到最近 commit 的文件
        valid_entries = [(f, t) for f, t in commits_with_time.items() if t is not None]
        if len(valid_entries) < 2:
            return results

        valid_entries.sort(key=lambda x: x[1], reverse=True)
        newest_file, newest_time = valid_entries[0]
        newest_commit = file_last_commits[newest_file]

        # 检查其他文件是否在同一次 commit 中
        for f, commit_hash in file_last_commits.items():
            if f == newest_file:
                continue
            if commit_hash != newest_commit:
                results.append(CheckResult(
                    name=f"文档 Git 关联性: {group_name}",
                    passed=False,
                    message=(
                        f"{newest_file} 在最近 commit 中被修改，"
                        f"但关联文档 {f} 不在同一次 commit 中"
                    ),
                    severity="warning",
                    suggestion=(
                        f"关联组 [{group_name}] 要求 git 提交同步。"
                        f"建议在修改 {newest_file} 时同步更新 {f}"
                    )
                ))

        return results

    def _check_release_consistency(
        self, group_name: str, files: List[str]
    ) -> List[CheckResult]:
        """发布版本级别的一致性检查

        检查在最近的版本标签时，组内所有文件是否都有被修改（相比上个标签）。
        这是最宽松的检查，适合文档间不需要每次都同步但版本发布时应一致的场景。
        """
        results = []

        if not is_git_repo(self.project_root):
            return results

        try:
            # 获取最近两个版本标签
            tag_result = subprocess.run(
                ["git", "tag", "--sort=-v:refname", "-l", "v*"],
                cwd=self.project_root,
                capture_output=True, text=True
            )
            if tag_result.returncode != 0:
                return results

            tags = [t.strip() for t in tag_result.stdout.strip().split("\n") if t.strip()]
            if len(tags) < 2:
                return results

            latest_tag = tags[0]
            prev_tag = tags[1]

            # 获取两个标签之间修改的文件
            diff_result = subprocess.run(
                ["git", "diff", "--name-only", prev_tag, latest_tag],
                cwd=self.project_root,
                capture_output=True, text=True
            )
            if diff_result.returncode != 0:
                return results

            changed_files = set(diff_result.stdout.strip().split("\n"))

            # 检查组内文件是否都在变更列表中
            group_in_diff = {f: f in changed_files for f in files}
            some_changed = any(group_in_diff.values())
            all_changed = all(group_in_diff.values())

            if some_changed and not all_changed:
                missing = [f for f, changed in group_in_diff.items() if not changed]
                for f in missing:
                    results.append(CheckResult(
                        name=f"文档版本关联性: {group_name}",
                        passed=False,
                        message=(
                            f"版本 {prev_tag} → {latest_tag} 中，"
                            f"关联组内部分文档已更新，但 {f} 未同步修改"
                        ),
                        severity="info",
                        suggestion=(
                            f"关联组 [{group_name}] 在版本发布时应保持一致。"
                            f"请检查 {f} 是否需要更新"
                        )
                    ))
        except BaseException:
            pass

        return results

    def _is_file_tracked_in_git(self, file_path: Path) -> bool:
        """检查文件是否在 Git 版本控制中

        Args:
            file_path: 文件路径

        Returns:
            bool: 是否被追踪
        """
        if not is_git_repo(self.project_root):
            return False

        try:
            result = subprocess.run(
                ["git", "ls-files", "--error-unmatch", str(file_path.relative_to(self.project_root))],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except BaseException:
            return False

    def _get_last_commit_time(self) -> Optional[datetime]:
        """获取最后一次提交的时间"""
        if not is_git_repo(self.project_root):
            return None

        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%ct"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            timestamp = int(result.stdout.strip())
            return datetime.fromtimestamp(timestamp)
        except BaseException:
            return None

    def get_summary(self, results: List[CheckResult]) -> Dict:
        """获取检查结果摘要

        Args:
            results: 检查结果列表

        Returns:
            Dict: 摘要信息
        """
        total = len(results)
        errors = sum(1 for r in results if r.severity == "error")
        warnings = sum(1 for r in results if r.severity == "warning")
        infos = sum(1 for r in results if r.severity == "info")
        passed = sum(1 for r in results if r.passed)

        return {
            "total": total,
            "passed": passed,
            "errors": errors,
            "warnings": warnings,
            "infos": infos,
            "all_passed": errors == 0
        }
