"""
任务管理器模块
"""

from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime


class TaskStatus(Enum):
    """任务状态枚举"""
    CREATED = "created"
    VALIDATED = "validated"
    SOLIDIFIED = "solidified"
    ROLLED_BACK = "rolled_back"


class Task:
    """任务实体"""

    def __init__(
        self,
        task_id: str,
        title: str,
        description: str,
        status: TaskStatus = TaskStatus.CREATED,
        created_at: Optional[str] = None,
        assigned_to: Optional[str] = None
    ):
        self.task_id = task_id
        self.title = title
        self.description = description
        self.status = status
        self.created_at = created_at or datetime.now().isoformat()
        self.assigned_to = assigned_to
        self.related_insights: List[str] = []

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at,
            "assigned_to": self.assigned_to,
            "related_insights": self.related_insights
        }


class ValidationResult:
    """验证结果"""

    def __init__(
        self,
        is_valid: bool,
        message: str,
        warnings: Optional[List[str]] = None
    ):
        self.is_valid = is_valid
        self.message = message
        self.warnings = warnings or []


class TaskManager:
    """任务管理器"""

    def __init__(self, project_root):
        self.project_root = project_root
        self.tasks: Dict[str, Task] = {}

    def create_task(
        self,
        title: str,
        description: str,
        assigned_to: Optional[str] = None
    ) -> Task:
        """创建任务"""
        task_id = f"TASK-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        task = Task(
            task_id=task_id,
            title=title,
            description=description,
            status=TaskStatus.CREATED,
            assigned_to=assigned_to
        )
        self.tasks[task_id] = task
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self.tasks.get(task_id)

    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[Task]:
        """列出任务"""
        tasks = list(self.tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return tasks

    def count(self, status: Optional[TaskStatus] = None) -> int:
        """统计任务数量

        Args:
            status: 可选的状态过滤器

        Returns:
            任务数量
        """
        if status:
            return len([t for t in self.tasks.values() if t.status == status])
        return len(self.tasks)

    def validate_task(self, task_id: str) -> ValidationResult:
        """验证任务"""
        task = self.get_task(task_id)
        if not task:
            return ValidationResult(False, f"任务 {task_id} 不存在")

        task.status = TaskStatus.VALIDATED
        return ValidationResult(True, f"任务 {task_id} 验证通过")

    def solidify_task(self, task_id: str) -> ValidationResult:
        """固化任务"""
        task = self.get_task(task_id)
        if not task:
            return ValidationResult(False, f"任务 {task_id} 不存在")

        task.status = TaskStatus.SOLIDIFIED
        return ValidationResult(True, f"任务 {task_id} 已固化")
