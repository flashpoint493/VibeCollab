"""
VibeCollab - Generate AI collaboration protocols with Vibe Development philosophy

Usage:
    vibecollab init -n "MyProject" -d web -o ./my-project
    vibecollab generate -c project.yaml
    vibecollab validate -c project.yaml
"""

__version__ = "0.5.9"
__author__ = "VibeCollab Contributors"

from .event_log import Event, EventLog, EventType
from .extension import Context, Extension, ExtensionProcessor, Hook
from .generator import LLMContextGenerator
from .health import HealthExtractor, HealthReport, Signal, SignalLevel
from .insight_collection import InsightCollection, PRESET_COLLECTIONS
from .llm_client import LLMClient, LLMConfig, LLMResponse, Message
from .pattern_engine import PatternEngine
from .profile import DeveloperProfile, PRESET_PROFILES
# from .profile_adapter import ProjectAdapter  # 暂时注释，模块不存在
from .profile_manager import ProfileManager
from .project import Project
from .task_manager import Task, TaskManager, TaskStatus, ValidationResult

__all__ = [
    "LLMContextGenerator",
    "PatternEngine",
    "Project",
    # "ProjectAdapter",  # 暂时注释，模块不存在
    "ProfileManager",
    "DeveloperProfile",
    "InsightCollection",
    "PRESET_PROFILES",
    "PRESET_COLLECTIONS",
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
    "LLMClient",
    "LLMConfig",
    "LLMResponse",
    "Message",
    "HealthExtractor",
    "HealthReport",
    "Signal",
    "SignalLevel",
    "__version__",
]
