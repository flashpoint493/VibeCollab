"""
LLMs.txt Integration - 与 llms.txt 标准集成
"""

import re
from pathlib import Path
from typing import Optional, Tuple


class LLMsTxtManager:
    """管理 llms.txt 文件的检测、更新和创建"""

    AI_COLLAB_SECTION = """## AI Collaboration

- [AI Collaboration Guidelines](CONTRIBUTING_AI.md): 
  Collaboration protocol, decision levels, task units, and workflow rules for AI-assisted development.
  This document defines how AI assistants should work with developers on this project.
"""

    @staticmethod
    def find_llmstxt(project_root: Path) -> Optional[Path]:
        """查找项目中的 llms.txt 文件"""
        llmstxt_path = project_root / "llms.txt"
        if llmstxt_path.exists():
            return llmstxt_path
        return None

    @staticmethod
    def has_ai_collab_section(content: str) -> bool:
        """检查内容中是否已包含 AI Collaboration 章节"""
        # 检查是否存在 AI Collaboration 相关的章节
        patterns = [
            r"##\s+AI\s+Collaboration",
            r"##\s+AI\s+.*[Cc]ollaboration",
            r"CONTRIBUTING_AI\.md",
            r"AI_COLLABORATION\.md",
        ]
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False

    @staticmethod
    def find_insertion_point(content: str) -> int:
        """找到插入 AI Collaboration 章节的最佳位置"""
        lines = content.split("\n")
        
        # 优先在 Documentation 章节后插入
        for i, line in enumerate(lines):
            if re.match(r"^##\s+Documentation", line, re.IGNORECASE):
                # 找到 Documentation 章节的结束位置
                for j in range(i + 1, len(lines)):
                    if re.match(r"^##\s+", lines[j]):
                        return j
                return len(lines)
        
        # 如果没有 Documentation，在最后插入
        return len(lines)

    @staticmethod
    def update_llmstxt(llmstxt_path: Path, contributing_ai_path: Path) -> bool:
        """更新现有的 llms.txt 文件，添加 AI Collaboration 引用"""
        try:
            with open(llmstxt_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 检查是否已存在
            if LLMsTxtManager.has_ai_collab_section(content):
                return False  # 已存在，无需更新
            
            # 确保引用路径正确（相对路径）
            rel_path = contributing_ai_path.relative_to(llmstxt_path.parent)
            section = LLMsTxtManager.AI_COLLAB_SECTION.replace(
                "CONTRIBUTING_AI.md", str(rel_path)
            )
            
            # 找到插入位置
            insert_pos = LLMsTxtManager.find_insertion_point(content)
            lines = content.split("\n")
            
            # 插入新章节
            lines.insert(insert_pos, "")
            lines.insert(insert_pos + 1, section)
            
            # 写回文件
            with open(llmstxt_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            
            return True
        except Exception as e:
            raise RuntimeError(f"更新 llms.txt 失败: {e}")

    @staticmethod
    def create_llmstxt(
        project_root: Path,
        project_name: str,
        project_description: str,
        contributing_ai_path: Path,
    ) -> Path:
        """创建新的 llms.txt 文件"""
        llmstxt_path = project_root / "llms.txt"
        
        # 确保引用路径正确
        rel_path = contributing_ai_path.relative_to(project_root)
        
        content = f"""# {project_name}

> {project_description}

## Overview

This project uses AI-assisted development with structured collaboration protocols.

## Quick Start

See [AI Collaboration Guidelines]({rel_path}) for how to work with AI assistants on this project.

## AI Collaboration

- [AI Collaboration Guidelines]({rel_path}): 
  Collaboration protocol, decision levels, task units, and workflow rules for AI-assisted development.
  This document defines how AI assistants should work with developers on this project.
"""
        
        with open(llmstxt_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return llmstxt_path

    @staticmethod
    def ensure_integration(
        project_root: Path,
        project_name: str,
        project_description: str,
        contributing_ai_path: Path,
    ) -> Tuple[bool, Optional[Path]]:
        """
        确保 llms.txt 集成完成
        
        Returns:
            (is_updated, llmstxt_path): 
                is_updated: 是否进行了更新（True=更新/创建，False=已存在）
                llmstxt_path: llms.txt 文件路径
        """
        llmstxt_path = LLMsTxtManager.find_llmstxt(project_root)
        
        if llmstxt_path:
            # 存在，尝试更新
            updated = LLMsTxtManager.update_llmstxt(llmstxt_path, contributing_ai_path)
            return updated, llmstxt_path
        else:
            # 不存在，创建新的
            new_path = LLMsTxtManager.create_llmstxt(
                project_root, project_name, project_description, contributing_ai_path
            )
            return True, new_path
