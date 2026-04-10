"""
VibeCollab - Generate AI collaboration protocols with Vibe Development philosophy

Usage:
    vibecollab init -n "MyProject" -d web -o ./my-project
    vibecollab generate -c project.yaml
    vibecollab validate -c project.yaml
"""

__version__ = "0.12.4"
__author__ = "VibeCollab Contributors"

from .agent.llm_client import LLMClient, LLMConfig, LLMResponse, Message
from .core.extension import Context, Extension, ExtensionProcessor, Hook
from .core.generator import LLMContextGenerator
from .core.health import HealthExtractor, HealthReport, Signal, SignalLevel
from .core.pattern_engine import PatternEngine
from .core.project import Project
from .domain.event_log import Event, EventLog, EventType
from .domain.roadmap_parser import Milestone, RoadmapParser, RoadmapStatus
from .domain.task_manager import Task, TaskManager, TaskStatus, ValidationResult

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
