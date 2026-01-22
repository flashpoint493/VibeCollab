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
