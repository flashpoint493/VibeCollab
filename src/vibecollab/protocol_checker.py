"""
Protocol Checker - 协议遵循情况检查器
用于检查 AI 是否遵循了协作协议中的各项要求
"""

import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from .git_utils import is_git_repo, get_git_status


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
            
            # 检查文件是否最近更新（24小时内）
            file_mtime = datetime.fromtimestamp(full_path.stat().st_mtime)
            hours_since_update = (datetime.now() - file_mtime).total_seconds() / 3600
            
            if hours_since_update > 24:
                results.append(CheckResult(
                    name=f"文档更新: {file_path}",
                    passed=False,
                    message=f"文档 {file_path} 超过 24 小时未更新",
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
        if not developers:
            results.append(CheckResult(
                name="开发者配置",
                passed=False,
                message="多开发者模式已启用但未配置任何开发者",
                severity="error",
                suggestion="在 project.yaml 的 multi_developer.developers 中配置开发者信息"
            ))
            return results
        
        developers_dir = self.project_root / "docs" / "developers"
        
        # 检查每个开发者的上下文文件
        for dev in developers:
            dev_id = dev.get("id")
            dev_name = dev.get("name", dev_id)
            
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
        except Exception:
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
        except Exception:
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
