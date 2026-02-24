"""Tests for the LLM Client module.

All API calls are mocked — no real HTTP requests are made.
"""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from vibecollab.llm_client import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL_ANTHROPIC,
    DEFAULT_MODEL_OPENAI,
    ENV_API_KEY,
    ENV_BASE_URL,
    ENV_MAX_TOKENS,
    ENV_MODEL,
    ENV_PROVIDER,
    PROVIDER_ANTHROPIC,
    PROVIDER_OPENAI,
    LLMClient,
    LLMConfig,
    LLMResponse,
    Message,
    build_project_context,
)

# ---------------------------------------------------------------------------
# LLMConfig tests
# ---------------------------------------------------------------------------

class TestLLMConfig:
    """Tests for LLMConfig resolution."""

    def test_defaults(self):
        """Config fills defaults when no env vars set."""
        with patch.dict(os.environ, {}, clear=True):
            cfg = LLMConfig()
        assert cfg.provider == PROVIDER_OPENAI
        assert cfg.model == DEFAULT_MODEL_OPENAI
        assert cfg.max_tokens == DEFAULT_MAX_TOKENS
        assert not cfg.is_configured  # no API key

    def test_from_env_vars(self):
        """Config reads from environment variables."""
        env = {
            ENV_PROVIDER: "anthropic",
            ENV_API_KEY: "sk-test-key",
            ENV_MODEL: "claude-sonnet-4-20250514",
            ENV_BASE_URL: "https://custom.api.com",
            ENV_MAX_TOKENS: "8000",
        }
        with patch.dict(os.environ, env, clear=True):
            cfg = LLMConfig()
        assert cfg.provider == PROVIDER_ANTHROPIC
        assert cfg.api_key == "sk-test-key"
        assert cfg.model == "claude-sonnet-4-20250514"
        assert cfg.base_url == "https://custom.api.com"
        assert cfg.max_tokens == 8000
        assert cfg.is_configured

    def test_explicit_overrides_env(self):
        """Explicit init args override env vars."""
        env = {ENV_API_KEY: "env-key", ENV_MODEL: "env-model"}
        with patch.dict(os.environ, env, clear=True):
            cfg = LLMConfig(api_key="explicit-key", model="explicit-model")
        assert cfg.api_key == "explicit-key"
        assert cfg.model == "explicit-model"

    def test_anthropic_default_model(self):
        """Anthropic provider gets Anthropic default model."""
        with patch.dict(os.environ, {ENV_PROVIDER: "anthropic"}, clear=True):
            cfg = LLMConfig()
        assert cfg.model == DEFAULT_MODEL_ANTHROPIC

    def test_to_safe_dict_hides_key(self):
        """to_safe_dict masks the API key."""
        cfg = LLMConfig(api_key="secret-key-12345")
        d = cfg.to_safe_dict()
        assert d["api_key"] == "***"
        assert "secret" not in str(d)

    def test_to_safe_dict_no_key(self):
        """to_safe_dict shows (not set) when no key."""
        with patch.dict(os.environ, {}, clear=True):
            cfg = LLMConfig()
        d = cfg.to_safe_dict()
        assert d["api_key"] == "(not set)"

    def test_is_configured(self):
        """is_configured returns True only when API key is set."""
        with patch.dict(os.environ, {}, clear=True):
            assert not LLMConfig().is_configured
            assert LLMConfig(api_key="k").is_configured


# ---------------------------------------------------------------------------
# Message & LLMResponse tests
# ---------------------------------------------------------------------------

class TestMessageAndResponse:

    def test_message_fields(self):
        m = Message(role="user", content="Hello")
        assert m.role == "user"
        assert m.content == "Hello"

    def test_response_ok(self):
        r = LLMResponse(content="answer", model="gpt-4o")
        assert r.ok
        assert r.content == "answer"

    def test_response_not_ok(self):
        r = LLMResponse(content="")
        assert not r.ok

    def test_response_usage(self):
        r = LLMResponse(content="x",
                         usage={"prompt_tokens": 10, "completion_tokens": 5})
        assert r.usage["prompt_tokens"] == 10


# ---------------------------------------------------------------------------
# build_project_context tests
# ---------------------------------------------------------------------------

class TestBuildProjectContext:

    def test_empty_directory(self, tmp_path):
        """Empty directory returns empty context."""
        ctx = build_project_context(tmp_path)
        assert ctx == ""

    def test_includes_project_yaml(self, tmp_path):
        """Context includes project.yaml content."""
        (tmp_path / "project.yaml").write_text(
            "project:\n  name: TestProject\n", encoding="utf-8")
        ctx = build_project_context(tmp_path)
        assert "TestProject" in ctx

    def test_includes_context_md(self, tmp_path):
        """Context includes docs/CONTEXT.md."""
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "CONTEXT.md").write_text(
            "# Global context\nVersion: v1.0\n", encoding="utf-8")
        ctx = build_project_context(tmp_path)
        assert "Global context" in ctx

    def test_includes_active_tasks(self, tmp_path):
        """Context includes active tasks from tasks.json."""
        vc_dir = tmp_path / ".vibecollab"
        vc_dir.mkdir()
        tasks = {
            "TASK-DEV-001": {"status": "IN_PROGRESS", "feature": "Auth"},
            "TASK-DEV-002": {"status": "DONE", "feature": "Login"},
        }
        (vc_dir / "tasks.json").write_text(
            json.dumps(tasks), encoding="utf-8")
        ctx = build_project_context(tmp_path)
        assert "TASK-DEV-001" in ctx
        assert "TASK-DEV-002" not in ctx  # DONE tasks excluded

    def test_includes_recent_events(self, tmp_path):
        """Context includes recent events from events.jsonl."""
        vc_dir = tmp_path / ".vibecollab"
        vc_dir.mkdir()
        events = [
            json.dumps({"event_type": "task_created",
                         "summary": "Created task X"}),
        ]
        (vc_dir / "events.jsonl").write_text(
            "\n".join(events) + "\n", encoding="utf-8")
        ctx = build_project_context(tmp_path)
        assert "Created task X" in ctx

    def test_truncation(self, tmp_path):
        """Context respects max_chars limit."""
        (tmp_path / "project.yaml").write_text(
            "x" * 50000, encoding="utf-8")
        ctx = build_project_context(tmp_path, max_chars=1000)
        assert len(ctx) < 2000  # some overhead for headers
        assert "truncated" in ctx

    def test_disable_sections(self, tmp_path):
        """Can selectively disable context sections."""
        (tmp_path / "project.yaml").write_text("project: test\n",
                                                encoding="utf-8")
        (tmp_path / "CONTRIBUTING_AI.md").write_text("# Protocol\n",
                                                      encoding="utf-8")
        ctx = build_project_context(tmp_path, include_contributing=False)
        assert "Protocol" not in ctx

    def test_unicode_content(self, tmp_path):
        """Unicode content in project files is handled correctly."""
        (tmp_path / "project.yaml").write_text(
            "project:\n  name: 测试项目\n", encoding="utf-8")
        ctx = build_project_context(tmp_path)
        assert "测试项目" in ctx


# ---------------------------------------------------------------------------
# LLMClient tests (all API calls mocked)
# ---------------------------------------------------------------------------

class TestLLMClient:

    def _make_client(self, provider="openai"):
        """Create a configured client for testing."""
        cfg = LLMConfig(provider=provider, api_key="test-key")
        return LLMClient(config=cfg)

    def test_no_api_key_raises(self):
        """chat() raises ValueError when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            client = LLMClient(config=LLMConfig())
        with pytest.raises(ValueError, match="API key not set"):
            client.chat([Message(role="user", content="hi")])

    def test_missing_httpx_raises(self):
        """chat() raises ImportError when httpx is not available."""
        client = self._make_client()
        with patch.dict("sys.modules", {"httpx": None}):
            client._httpx = None  # force re-import
            with pytest.raises(ImportError, match="httpx"):
                client._ensure_httpx()

    @patch("vibecollab.llm_client.LLMClient._call_openai")
    def test_chat_openai_dispatch(self, mock_call):
        """OpenAI provider dispatches to _call_openai."""
        mock_call.return_value = LLMResponse(content="hello")
        client = self._make_client("openai")
        resp = client.chat([Message(role="user", content="hi")])
        mock_call.assert_called_once()
        assert resp.content == "hello"

    @patch("vibecollab.llm_client.LLMClient._call_anthropic")
    def test_chat_anthropic_dispatch(self, mock_call):
        """Anthropic provider dispatches to _call_anthropic."""
        mock_call.return_value = LLMResponse(content="bonjour")
        client = self._make_client("anthropic")
        resp = client.chat([Message(role="user", content="hi")])
        mock_call.assert_called_once()
        assert resp.content == "bonjour"

    @patch("vibecollab.llm_client.LLMClient._call_openai")
    def test_ask_without_context(self, mock_call):
        """ask() without project_root sends just the question."""
        mock_call.return_value = LLMResponse(content="42")
        client = self._make_client()
        resp = client.ask("What is the answer?")
        assert resp.content == "42"
        call_messages = mock_call.call_args[0][0]
        assert len(call_messages) == 1
        assert call_messages[0].role == "user"

    @patch("vibecollab.llm_client.LLMClient._call_openai")
    def test_ask_with_project_context(self, mock_call, tmp_path):
        """ask() with project_root includes system context."""
        (tmp_path / "project.yaml").write_text(
            "project:\n  name: MyProject\n", encoding="utf-8")
        mock_call.return_value = LLMResponse(content="suggestion")
        client = self._make_client()
        resp = client.ask("What next?", project_root=tmp_path)
        assert resp.content == "suggestion"
        call_messages = mock_call.call_args[0][0]
        assert len(call_messages) == 2
        assert call_messages[0].role == "system"
        assert "MyProject" in call_messages[0].content

    @patch("vibecollab.llm_client.LLMClient._call_openai")
    def test_ask_with_system_prompt(self, mock_call):
        """ask() with custom system_prompt uses it."""
        mock_call.return_value = LLMResponse(content="yes")
        client = self._make_client()
        client.ask("hi", system_prompt="You are a cat.")
        call_messages = mock_call.call_args[0][0]
        assert call_messages[0].content == "You are a cat."

    def test_openai_call_format(self):
        """_call_openai builds correct request payload."""
        client = self._make_client()

        # Mock httpx
        mock_httpx = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "reply"}}],
            "model": "gpt-4o",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }
        mock_client_instance = MagicMock()
        mock_client_instance.post.return_value = mock_response
        mock_client_instance.__enter__ = lambda s: mock_client_instance
        mock_client_instance.__exit__ = lambda s, *a: None
        mock_httpx.Client.return_value = mock_client_instance
        client._httpx = mock_httpx

        messages = [
            Message(role="system", content="Be helpful"),
            Message(role="user", content="Hello"),
        ]
        resp = client._call_openai(messages, temperature=0.5)

        assert resp.content == "reply"
        assert resp.model == "gpt-4o"
        # Verify request payload
        call_args = mock_client_instance.post.call_args
        payload = call_args[1]["json"]
        assert payload["model"] == DEFAULT_MODEL_OPENAI
        assert len(payload["messages"]) == 2
        assert payload["temperature"] == 0.5

    def test_anthropic_call_format(self):
        """_call_anthropic builds correct request payload with system separated."""
        client = self._make_client("anthropic")

        mock_httpx = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": "réponse"}],
            "model": "claude-sonnet-4-20250514",
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }
        mock_client_instance = MagicMock()
        mock_client_instance.post.return_value = mock_response
        mock_client_instance.__enter__ = lambda s: mock_client_instance
        mock_client_instance.__exit__ = lambda s, *a: None
        mock_httpx.Client.return_value = mock_client_instance
        client._httpx = mock_httpx

        messages = [
            Message(role="system", content="Be a cat"),
            Message(role="user", content="Meow?"),
        ]
        resp = client._call_anthropic(messages, temperature=0.3)

        assert resp.content == "réponse"
        # Verify system is separated
        payload = mock_client_instance.post.call_args[1]["json"]
        assert payload["system"] == "Be a cat"
        assert len(payload["messages"]) == 1  # only user message
        assert payload["messages"][0]["role"] == "user"

    def test_openai_error_raises(self):
        """OpenAI API error raises RuntimeError."""
        client = self._make_client()

        mock_httpx = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_client_instance = MagicMock()
        mock_client_instance.post.return_value = mock_response
        mock_client_instance.__enter__ = lambda s: mock_client_instance
        mock_client_instance.__exit__ = lambda s, *a: None
        mock_httpx.Client.return_value = mock_client_instance
        client._httpx = mock_httpx

        with pytest.raises(RuntimeError, match="429"):
            client._call_openai(
                [Message(role="user", content="hi")], 0.7)

    def test_anthropic_error_raises(self):
        """Anthropic API error raises RuntimeError."""
        client = self._make_client("anthropic")

        mock_httpx = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Invalid API key"
        mock_client_instance = MagicMock()
        mock_client_instance.post.return_value = mock_response
        mock_client_instance.__enter__ = lambda s: mock_client_instance
        mock_client_instance.__exit__ = lambda s, *a: None
        mock_httpx.Client.return_value = mock_client_instance
        client._httpx = mock_httpx

        with pytest.raises(RuntimeError, match="401"):
            client._call_anthropic(
                [Message(role="user", content="hi")], 0.7)
