"""
VibeCollab - Generate AI collaboration protocols with Vibe Development philosophy

Usage:
    vibecollab init -n "MyProject" -d web -o ./my-project
    vibecollab generate -c project.yaml
    vibecollab validate -c project.yaml
"""

__version__ = "0.5.6"
__author__ = "VibeCollab Contributors"

from .generator import LLMContextGenerator
from .project import Project
from .extension import ExtensionProcessor, Extension, Hook, Context
from .event_log import Event, EventLog, EventType
from .task_manager import Task, TaskManager, TaskStatus, ValidationResult

__all__ = [
    "LLMContextGenerator",
    "Project",
    "ExtensionProcessor",
    "Extension",
    "Hook",
    "Context",
    "Event",
    "EventLog",
    "EventType",
    "Task",
    "TaskManager",
    "TaskStatus",
    "ValidationResult",
    "__version__",
]
