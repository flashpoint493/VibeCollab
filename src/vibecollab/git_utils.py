"""
Git 工具函数 - 检查和管理 Git 仓库
"""

import subprocess
import shutil
from pathlib import Path
from typing import Optional, Tuple


def check_git_installed() -> bool:
    """检查 Git 是否已安装
    
    Returns:
        bool: Git 是否可用
    """
    return shutil.which("git") is not None


def is_git_repo(path: Path) -> bool:
    """检查路径是否是 Git 仓库
    
    Args:
        path: 要检查的路径
        
    Returns:
        bool: 是否是 Git 仓库
    """
    git_dir = path / ".git"
    return git_dir.exists() and git_dir.is_dir()


def init_git_repo(path: Path, initial_commit: bool = True) -> Tuple[bool, Optional[str]]:
    """初始化 Git 仓库
    
    Args:
        path: 项目根目录
        initial_commit: 是否创建初始提交
        
    Returns:
        Tuple[bool, Optional[str]]: (是否成功, 错误信息)
    """
    if not check_git_installed():
        return False, "Git 未安装，请先安装 Git"
    
    if is_git_repo(path):
        return True, None  # 已经是 Git 仓库
    
    try:
        # 初始化仓库
        subprocess.run(
            ["git", "init"],
            cwd=path,
            check=True,
            capture_output=True,
            text=True
        )
        
        # 创建初始提交（如果请求）
        if initial_commit:
            # 检查是否有文件需要提交
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=path,
                capture_output=True,
                text=True
            )
            
            if result.stdout.strip():
                # 添加所有文件
                subprocess.run(
                    ["git", "add", "."],
                    cwd=path,
                    check=True,
                    capture_output=True,
                    text=True
                )
                
                # 创建初始提交
                subprocess.run(
                    ["git", "commit", "-m", "chore: initial commit with vibe-collab setup"],
                    cwd=path,
                    check=True,
                    capture_output=True,
                    text=True
                )
        
        return True, None
    except subprocess.CalledProcessError as e:
        return False, f"Git 初始化失败: {e.stderr}"
    except Exception as e:
        return False, f"Git 初始化出错: {str(e)}"


def ensure_git_repo(path: Path, auto_init: bool = False) -> Tuple[bool, Optional[str], bool]:
    """确保路径是 Git 仓库
    
    Args:
        path: 项目根目录
        auto_init: 如果不存在是否自动初始化
        
    Returns:
        Tuple[bool, Optional[str], bool]: (是否成功, 错误信息, 是否是新初始化的)
    """
    # 检查 Git 是否安装
    if not check_git_installed():
        if auto_init:
            return False, "Git 未安装，无法自动初始化仓库。请先安装 Git: https://git-scm.com/", False
        return False, "Git 未安装", False
    
    # 检查是否已是仓库
    if is_git_repo(path):
        return True, None, False
    
    # 如果需要自动初始化
    if auto_init:
        success, error = init_git_repo(path, initial_commit=True)
        if success:
            return True, None, True
        return False, error, False
    
    # 不需要自动初始化，返回提示
    return False, "项目目录不是 Git 仓库。建议运行 'git init' 初始化仓库。", False


def get_git_status(path: Path) -> Optional[dict]:
    """获取 Git 仓库状态信息
    
    Args:
        path: 项目根目录
        
    Returns:
        Optional[dict]: Git 状态信息，如果不是仓库则返回 None
    """
    if not is_git_repo(path):
        return None
    
    try:
        # 获取当前分支
        branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True
        )
        branch = branch_result.stdout.strip()
        
        # 获取提交数量
        commit_result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True
        )
        commit_count = commit_result.stdout.strip()
        
        # 检查是否有未提交的更改
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True
        )
        has_changes = bool(status_result.stdout.strip())
        
        return {
            "branch": branch,
            "commit_count": int(commit_count) if commit_count else 0,
            "has_uncommitted_changes": has_changes
        }
    except Exception:
        return None
