"""
VibeCollab - Generate AI collaboration protocols with Vibe Development philosophy

Usage:
    vibecollab init -n "MyProject" -d web -o ./my-project
    vibecollab generate -c project.yaml
    vibecollab validate -c project.yaml
"""

__version__ = "0.3.0"
__author__ = "VibeCollab Contributors"

from .generator import LLMContextGenerator
from .project import Project
from .extension import ExtensionProcessor, Extension, Hook, Context

__all__ = [
    "LLMContextGenerator",
    "Project",
    "ExtensionProcessor",
    "Extension",
    "Hook",
    "Context",
    "__version__",
]
