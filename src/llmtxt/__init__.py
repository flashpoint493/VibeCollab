"""
LLMTxt - 从 YAML 配置生成标准化的 AI 协作规则文档

Usage:
    llmtxt init -n "MyProject" -d web -o ./my-project
    llmtxt generate -c project.yaml -o llm.txt
    llmtxt validate -c project.yaml
"""

__version__ = "0.1.0"
__author__ = "LLMTXTGenerator Contributors"

from .generator import LLMTxtGenerator
from .project import Project
from .extension import ExtensionProcessor, Extension, Hook, Context

__all__ = [
    "LLMTxtGenerator",
    "Project",
    "ExtensionProcessor",
    "Extension",
    "Hook",
    "Context",
    "__version__",
]
