"""
PRD Manager - 产品需求文档管理器
用于管理和跟踪项目需求的原始描述和变化历史
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class Requirement:
    """需求项"""
    id: str
    title: str
    original_description: str
    current_description: Optional[str] = None
    status: str = "draft"  # draft, confirmed, in_progress, completed, cancelled
    priority: str = "medium"  # high, medium, low
    created_at: str = ""
    updated_at: str = ""
    changes: List[Dict] = None  # 需求变化历史
    
    def __post_init__(self):
        if self.changes is None:
            self.changes = []
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d")
        if not self.updated_at:
            self.updated_at = self.created_at
        if not self.current_description:
            self.current_description = self.original_description


class PRDManager:
    """PRD 管理器"""
    
    def __init__(self, prd_path: Path):
        self.prd_path = Path(prd_path)
        self.requirements: Dict[str, Requirement] = {}
        self._load()
    
    def _load(self):
        """从文件加载 PRD"""
        if not self.prd_path.exists():
            return
        
        try:
            content = self.prd_path.read_text(encoding="utf-8")
            # 解析 Markdown 格式的 PRD
            self._parse_markdown(content)
        except Exception as e:
            # 如果解析失败，尝试作为 YAML 加载（向后兼容）
            try:
                with open(self.prd_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data and "requirements" in data:
                        for req_data in data["requirements"]:
                            req = Requirement(**req_data)
                            self.requirements[req.id] = req
            except Exception:
                pass
    
    def _parse_markdown(self, content: str):
        """解析 Markdown 格式的 PRD"""
        lines = content.split("\n")
        current_req = None
        in_requirement = False
        
        for line in lines:
            # 检测需求标题 (## REQ-XXX: Title)
            if line.startswith("## REQ-"):
                # 保存上一个需求
                if current_req:
                    self.requirements[current_req.id] = current_req
                
                # 解析新需求
                parts = line[2:].split(":", 1)
                req_id = parts[0].strip()
                title = parts[1].strip() if len(parts) > 1 else ""
                
                current_req = Requirement(
                    id=req_id,
                    title=title,
                    original_description="",
                    created_at=datetime.now().strftime("%Y-%m-%d")
                )
                in_requirement = True
                continue
            
            if not in_requirement or not current_req:
                continue
            
            # 解析需求内容
            if line.startswith("**原始描述**:"):
                continue
            elif line.startswith("**当前描述**:"):
                continue
            elif line.startswith("**状态**:"):
                status = line.split(":", 1)[1].strip()
                current_req.status = status
            elif line.startswith("**优先级**:"):
                priority = line.split(":", 1)[1].strip()
                current_req.priority = priority
            elif line.startswith("**创建时间**:"):
                created_at = line.split(":", 1)[1].strip()
                current_req.created_at = created_at
            elif line.startswith("**更新时间**:"):
                updated_at = line.split(":", 1)[1].strip()
                current_req.updated_at = updated_at
            elif line.strip().startswith(">") and not current_req.original_description:
                # 原始描述通常在引用块中
                current_req.original_description = line.strip()[1:].strip()
            elif line.strip() and not line.startswith("#") and not line.startswith("|"):
                # 普通文本，可能是描述的一部分
                if not current_req.original_description:
                    current_req.original_description = line.strip()
                elif not current_req.current_description or current_req.current_description == current_req.original_description:
                    current_req.current_description = line.strip()
        
        # 保存最后一个需求
        if current_req:
            self.requirements[current_req.id] = current_req
    
    def add_requirement(self, title: str, description: str, priority: str = "medium") -> Requirement:
        """添加新需求
        
        Args:
            title: 需求标题
            description: 需求描述
            priority: 优先级
            
        Returns:
            Requirement: 创建的需求对象
        """
        # 生成需求 ID
        req_id = f"REQ-{len(self.requirements) + 1:03d}"
        
        req = Requirement(
            id=req_id,
            title=title,
            original_description=description,
            current_description=description,
            status="draft",
            priority=priority,
            created_at=datetime.now().strftime("%Y-%m-%d"),
            updated_at=datetime.now().strftime("%Y-%m-%d")
        )
        
        self.requirements[req_id] = req
        return req
    
    def update_requirement(self, req_id: str, new_description: str, change_reason: str = ""):
        """更新需求
        
        Args:
            req_id: 需求 ID
            new_description: 新的需求描述
            change_reason: 变化原因
        """
        if req_id not in self.requirements:
            raise ValueError(f"需求不存在: {req_id}")
        
        req = self.requirements[req_id]
        old_description = req.current_description
        
        # 记录变化
        change_entry = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "from": old_description,
            "to": new_description,
            "reason": change_reason
        }
        req.changes.append(change_entry)
        
        # 更新需求
        req.current_description = new_description
        req.updated_at = datetime.now().strftime("%Y-%m-%d")
    
    def set_status(self, req_id: str, status: str):
        """设置需求状态
        
        Args:
            req_id: 需求 ID
            status: 新状态
        """
        if req_id not in self.requirements:
            raise ValueError(f"需求不存在: {req_id}")
        
        req = self.requirements[req_id]
        req.status = status
        req.updated_at = datetime.now().strftime("%Y-%m-%d")
    
    def save(self):
        """保存 PRD 到文件"""
        content = self._generate_markdown()
        self.prd_path.parent.mkdir(parents=True, exist_ok=True)
        self.prd_path.write_text(content, encoding="utf-8")
    
    def _generate_markdown(self) -> str:
        """生成 Markdown 格式的 PRD"""
        lines = [
            "# 产品需求文档 (PRD)",
            "",
            "本文档记录项目的原始需求和需求变化历史。",
            "",
            "## 需求列表",
            ""
        ]
        
        # 按状态和优先级排序
        sorted_reqs = sorted(
            self.requirements.values(),
            key=lambda r: (
                {"draft": 0, "confirmed": 1, "in_progress": 2, "completed": 3, "cancelled": 4}.get(r.status, 5),
                {"high": 0, "medium": 1, "low": 2}.get(r.priority, 3),
                r.created_at
            )
        )
        
        for req in sorted_reqs:
            lines.append(f"## {req.id}: {req.title}")
            lines.append("")
            lines.append(f"**原始描述**:")
            lines.append(f"> {req.original_description}")
            lines.append("")
            
            if req.current_description != req.original_description:
                lines.append(f"**当前描述**:")
                lines.append(f"> {req.current_description}")
                lines.append("")
            
            lines.append(f"**状态**: {req.status}")
            lines.append(f"**优先级**: {req.priority}")
            lines.append(f"**创建时间**: {req.created_at}")
            lines.append(f"**更新时间**: {req.updated_at}")
            lines.append("")
            
            if req.changes:
                lines.append("**需求变化历史**:")
                lines.append("")
                for change in req.changes:
                    lines.append(f"- **{change['date']}**: {change['reason'] or '需求更新'}")
                    if change['from'] != change['to']:
                        lines.append(f"  - 从: {change['from'][:100]}...")
                        lines.append(f"  - 到: {change['to'][:100]}...")
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        # 添加需求统计
        lines.append("## 需求统计")
        lines.append("")
        status_counts = {}
        for req in self.requirements.values():
            status_counts[req.status] = status_counts.get(req.status, 0) + 1
        
        lines.append("| 状态 | 数量 |")
        lines.append("|------|------|")
        for status, count in sorted(status_counts.items()):
            lines.append(f"| {status} | {count} |")
        lines.append("")
        
        lines.append(f"*最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
        return "\n".join(lines)
    
    def get_requirement(self, req_id: str) -> Optional[Requirement]:
        """获取需求
        
        Args:
            req_id: 需求 ID
            
        Returns:
            Optional[Requirement]: 需求对象，如果不存在返回 None
        """
        return self.requirements.get(req_id)
    
    def list_requirements(self, status: Optional[str] = None) -> List[Requirement]:
        """列出需求
        
        Args:
            status: 可选的状态过滤
            
        Returns:
            List[Requirement]: 需求列表
        """
        reqs = list(self.requirements.values())
        if status:
            reqs = [r for r in reqs if r.status == status]
        return sorted(reqs, key=lambda r: r.created_at)
