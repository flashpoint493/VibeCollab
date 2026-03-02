"""
LLM Client - Lightweight, provider-agnostic LLM integration.

Provides a unified interface to call LLM APIs (OpenAI-compatible and
Anthropic) from CLI or programmatic usage, completely decoupled from
VibeCollab's existing offline functionality.

Design principles:
- Zero impact on existing offline features (pure additive module)
- Provider-agnostic: any OpenAI-compatible endpoint or Anthropic API
- Three-layer config: env vars > ~/.vibecollab/config.yaml > defaults
- Lazy dependency: httpx imported only when LLM is actually called
- Context-aware: automatically builds project context for prompts
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Supported providers
PROVIDER_OPENAI = "openai"
PROVIDER_ANTHROPIC = "anthropic"

# Environment variable names
ENV_PROVIDER = "VIBECOLLAB_LLM_PROVIDER"       # "openai" or "anthropic"
ENV_API_KEY = "VIBECOLLAB_LLM_API_KEY"          # API key
ENV_MODEL = "VIBECOLLAB_LLM_MODEL"             # Model name
ENV_BASE_URL = "VIBECOLLAB_LLM_BASE_URL"       # Custom endpoint (OpenAI-compatible)
ENV_MAX_TOKENS = "VIBECOLLAB_LLM_MAX_TOKENS"   # Max response tokens

# Defaults
DEFAULT_PROVIDER = PROVIDER_OPENAI
DEFAULT_MODEL_OPENAI = "gpt-4o"
DEFAULT_MODEL_ANTHROPIC = "claude-sonnet-4-20250514"
DEFAULT_MAX_TOKENS = 4096


@dataclass
class LLMConfig:
    """LLM configuration, resolved from multiple sources.

    Priority: explicit init args > env vars > config file > defaults.

    Config file: ~/.vibecollab/config.yaml (created by `vibecollab config setup`)
    """
    provider: str = ""
    api_key: str = ""
    model: str = ""
    base_url: str = ""
    max_tokens: int = 0

    def __post_init__(self):
        # Load config file values as fallback (lowest priority layer)
        file_cfg = {}
        try:
            from ..core.config_manager import resolve_llm_config
            file_cfg = resolve_llm_config()
        except Exception:
            pass

        self.provider = (self.provider
                         or os.getenv(ENV_PROVIDER)
                         or file_cfg.get("provider")
                         or DEFAULT_PROVIDER)
        self.api_key = (self.api_key
                        or os.getenv(ENV_API_KEY)
                        or file_cfg.get("api_key")
                        or "")
        self.base_url = (self.base_url
                         or os.getenv(ENV_BASE_URL)
                         or file_cfg.get("base_url")
                         or "")
        self.max_tokens = (self.max_tokens
                           or int(os.getenv(ENV_MAX_TOKENS, "0"))
                           or int(file_cfg.get("max_tokens", "0") or "0")
                           or DEFAULT_MAX_TOKENS)

        if not self.model:
            self.model = (os.getenv(ENV_MODEL)
                          or file_cfg.get("model")
                          or "")
            if not self.model:
                self.model = (DEFAULT_MODEL_ANTHROPIC
                              if self.provider == PROVIDER_ANTHROPIC
                              else DEFAULT_MODEL_OPENAI)

    @property
    def is_configured(self) -> bool:
        """Check if the LLM client is properly configured."""
        return bool(self.api_key)

    def to_safe_dict(self) -> Dict[str, Any]:
        """Serialize config without exposing the API key."""
        return {
            "provider": self.provider,
            "model": self.model,
            "base_url": self.base_url or "(default)",
            "max_tokens": self.max_tokens,
            "api_key": "***" if self.api_key else "(not set)",
        }


# ---------------------------------------------------------------------------
# Message types
# ---------------------------------------------------------------------------

@dataclass
class Message:
    """A single message in a conversation."""
    role: str       # "system", "user", or "assistant"
    content: str


@dataclass
class LLMResponse:
    """Response from an LLM call."""
    content: str
    model: str = ""
    usage: Dict[str, int] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return bool(self.content)


# ---------------------------------------------------------------------------
# Context builder
# ---------------------------------------------------------------------------

def build_project_context(project_root: Path,
                          include_contributing: bool = True,
                          include_context: bool = True,
                          include_tasks: bool = True,
                          max_chars: int = 30000) -> str:
    """Build a project context string for LLM prompts.

    Reads relevant project files and assembles a concise context
    that the LLM can use to understand the project state.

    Args:
        project_root: Project root directory.
        include_contributing: Include CONTRIBUTING_AI.md (truncated).
        include_context: Include developer/global CONTEXT.md.
        include_tasks: Include active tasks from tasks.json.
        max_chars: Maximum total context characters.

    Returns:
        Formatted context string.
    """
    parts = []
    chars_remaining = max_chars

    def _read_truncated(path: Path, label: str, limit: int = 0) -> None:
        nonlocal chars_remaining
        if not path.exists() or chars_remaining <= 0:
            return
        text = path.read_text(encoding="utf-8", errors="replace")
        effective_limit = min(limit, chars_remaining) if limit else chars_remaining
        if len(text) > effective_limit:
            text = text[:effective_limit] + "\n... (truncated)"
        parts.append(f"## {label}\n\n{text}")
        chars_remaining -= len(text)

    # Project config summary
    yaml_path = project_root / "project.yaml"
    if yaml_path.exists():
        _read_truncated(yaml_path, "Project Configuration (project.yaml)",
                        limit=3000)

    # CONTRIBUTING_AI.md — first 5000 chars (core protocol)
    if include_contributing:
        _read_truncated(project_root / "CONTRIBUTING_AI.md",
                        "AI Collaboration Protocol (CONTRIBUTING_AI.md)",
                        limit=5000)

    # Global CONTEXT.md
    if include_context:
        _read_truncated(project_root / "docs" / "CONTEXT.md",
                        "Current Project Context")

    # Active tasks
    if include_tasks:
        tasks_path = project_root / ".vibecollab" / "tasks.json"
        if tasks_path.exists() and chars_remaining > 0:
            try:
                tasks = json.loads(
                    tasks_path.read_text(encoding="utf-8"))
                active = {k: v for k, v in tasks.items()
                          if v.get("status") != "DONE"}
                if active:
                    text = json.dumps(active, ensure_ascii=False, indent=2)
                    if len(text) > 3000:
                        text = text[:3000] + "\n... (truncated)"
                    parts.append(f"## Active Tasks\n\n```json\n{text}\n```")
                    chars_remaining -= len(text)
            except (json.JSONDecodeError, OSError):
                pass

    # Recent events
    events_path = project_root / ".vibecollab" / "events.jsonl"
    if events_path.exists() and chars_remaining > 500:
        try:
            lines = events_path.read_text(encoding="utf-8").strip().split("\n")
            recent = lines[-10:] if len(lines) > 10 else lines
            summaries = []
            for line in recent:
                try:
                    evt = json.loads(line)
                    summaries.append(
                        f"- [{evt.get('event_type')}] {evt.get('summary')}")
                except json.JSONDecodeError:
                    pass
            if summaries:
                parts.append(
                    "## Recent Events\n\n" + "\n".join(summaries))
        except OSError:
            pass

    return "\n\n---\n\n".join(parts)


# ---------------------------------------------------------------------------
# LLM Client
# ---------------------------------------------------------------------------

class LLMClient:
    """Provider-agnostic LLM client.

    Supports OpenAI-compatible APIs and Anthropic Claude.
    Dependencies (httpx) are imported lazily on first call.

    Usage:
        client = LLMClient()  # reads config from env vars
        resp = client.chat([Message(role="user", content="Hello")])
        print(resp.content)

    With project context:
        context = build_project_context(Path("."))
        resp = client.chat([
            Message(role="system", content=f"Project context:\\n{context}"),
            Message(role="user", content="What should I work on next?"),
        ])
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self._httpx = None  # lazy import

    def _ensure_httpx(self):
        """Lazily import httpx to avoid dependency when not using LLM."""
        if self._httpx is None:
            try:
                import httpx
                self._httpx = httpx
            except ImportError:
                raise ImportError(
                    "httpx is required for LLM features. "
                    "Install it with: pip install httpx"
                )

    def _check_config(self):
        """Verify configuration is valid before making a call."""
        if not self.config.api_key:
            raise ValueError(
                f"LLM API key not set. Set {ENV_API_KEY} environment variable "
                f"or pass api_key to LLMConfig."
            )

    def chat(self, messages: List[Message],
             temperature: float = 0.7) -> LLMResponse:
        """Send a chat completion request.

        Args:
            messages: List of conversation messages.
            temperature: Sampling temperature (0.0-1.0).

        Returns:
            LLMResponse with the assistant's reply.

        Raises:
            ImportError: If httpx is not installed.
            ValueError: If API key is not configured.
            RuntimeError: If the API call fails.
        """
        self._check_config()
        self._ensure_httpx()

        if self.config.provider == PROVIDER_ANTHROPIC:
            return self._call_anthropic(messages, temperature)
        else:
            return self._call_openai(messages, temperature)

    def _call_openai(self, messages: List[Message],
                     temperature: float) -> LLMResponse:
        """Call an OpenAI-compatible API."""
        base_url = (self.config.base_url or
                    "https://api.openai.com/v1").rstrip("/")

        payload = {
            "model": self.config.model,
            "messages": [{"role": m.role, "content": m.content}
                         for m in messages],
            "max_tokens": self.config.max_tokens,
            "temperature": temperature,
        }

        with self._httpx.Client(timeout=120) as client:
            resp = client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

        if resp.status_code != 200:
            raise RuntimeError(
                f"OpenAI API error {resp.status_code}: {resp.text[:500]}")

        data = resp.json()
        choices = data.get("choices", [])
        choice = choices[0] if choices else {}
        return LLMResponse(
            content=choice.get("message", {}).get("content", ""),
            model=data.get("model", self.config.model),
            usage=data.get("usage", {}),
            raw=data,
        )

    def _call_anthropic(self, messages: List[Message],
                        temperature: float) -> LLMResponse:
        """Call the Anthropic Messages API."""
        base_url = (self.config.base_url or
                    "https://api.anthropic.com").rstrip("/")

        # Anthropic requires system message separately
        system_msg = ""
        api_messages = []
        for m in messages:
            if m.role == "system":
                system_msg += m.content + "\n"
            else:
                api_messages.append({"role": m.role, "content": m.content})

        payload = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "temperature": temperature,
            "messages": api_messages,
        }
        if system_msg.strip():
            payload["system"] = system_msg.strip()

        with self._httpx.Client(timeout=120) as client:
            resp = client.post(
                f"{base_url}/v1/messages",
                headers={
                    "x-api-key": self.config.api_key,
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01",
                },
                json=payload,
            )

        if resp.status_code != 200:
            raise RuntimeError(
                f"Anthropic API error {resp.status_code}: {resp.text[:500]}")

        data = resp.json()
        content_blocks = data.get("content", [])
        text = "".join(
            block.get("text", "") for block in content_blocks
            if block.get("type") == "text"
        )
        return LLMResponse(
            content=text,
            model=data.get("model", self.config.model),
            usage=data.get("usage", {}),
            raw=data,
        )

    def ask(self, question: str,
            system_prompt: str = "",
            project_root: Optional[Path] = None,
            temperature: float = 0.7) -> LLMResponse:
        """Convenience method: ask a single question with optional project context.

        Args:
            question: The question to ask.
            system_prompt: Optional system prompt override.
            project_root: If provided, automatically builds project context.
            temperature: Sampling temperature.

        Returns:
            LLMResponse with the answer.
        """
        messages = []

        if project_root:
            context = build_project_context(Path(project_root))
            system = (system_prompt or
                      "You are an AI development assistant for the VibeCollab project. "
                      "Follow the project's collaboration protocol.")
            system += f"\n\n# Project Context\n\n{context}"
            messages.append(Message(role="system", content=system))
        elif system_prompt:
            messages.append(Message(role="system", content=system_prompt))

        messages.append(Message(role="user", content=question))
        return self.chat(messages, temperature=temperature)
