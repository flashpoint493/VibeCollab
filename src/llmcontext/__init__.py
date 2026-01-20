"""
LLMContext - 从 YAML 配置生成标准化的 AI 协作规则文档

Usage:
    llmcontext init -n "MyProject" -d web -o ./my-project
    llmcontext generate -c project.yaml -o llm.txt
    llmcontext validate -c project.yaml
"""

__version__ = "0.2.0"
__author__ = "LLMContextGenerator Contributors"

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
