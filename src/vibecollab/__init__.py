"""
VibeCollab - Generate AI collaboration protocols with Vibe Development philosophy

Usage:
    vibecollab init -n "MyProject" -d web -o ./my-project
    vibecollab generate -c project.yaml
    vibecollab validate -c project.yaml
"""

__version__ = "0.9.8"
__author__ = "VibeCollab Contributors"

from .event_log import Event, EventLog, EventType
from .extension import Context, Extension, ExtensionProcessor, Hook
from .generator import LLMContextGenerator
from .health import HealthExtractor, HealthReport, Signal, SignalLevel
from .llm_client import LLMClient, LLMConfig, LLMResponse, Message
from .pattern_engine import PatternEngine
from .project import Project
from .roadmap_parser import Milestone, RoadmapParser, RoadmapStatus
from .task_manager import Task, TaskManager, TaskStatus, ValidationResult

__all__ = [
    "LLMContextGenerator",
    "PatternEngine",
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
    "LLMClient",
    "LLMConfig",
    "LLMResponse",
    "Message",
    "HealthExtractor",
    "HealthReport",
    "Signal",
    "SignalLevel",
    "RoadmapParser",
    "Milestone",
    "RoadmapStatus",
    "__version__",
]
