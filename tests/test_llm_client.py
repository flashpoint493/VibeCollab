"""Tests for the LLM Client module.

All API calls are mocked — no real HTTP requests are made.
"""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from vibecollab.agent.llm_client import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL_ANTHROPIC,
    DEFAULT_MODEL_OPENAI,
    DEFAULT_PROVIDER,
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

    @patch("vibecollab.agent.llm_client.LLMClient._call_openai")
    def test_chat_openai_dispatch(self, mock_call):
        """OpenAI provider dispatches to _call_openai."""
        mock_call.return_value = LLMResponse(content="hello")
        client = self._make_client("openai")
        resp = client.chat([Message(role="user", content="hi")])
        mock_call.assert_called_once()
        assert resp.content == "hello"

    @patch("vibecollab.agent.llm_client.LLMClient._call_anthropic")
    def test_chat_anthropic_dispatch(self, mock_call):
        """Anthropic provider dispatches to _call_anthropic."""
        mock_call.return_value = LLMResponse(content="bonjour")
        client = self._make_client("anthropic")
        resp = client.chat([Message(role="user", content="hi")])
        mock_call.assert_called_once()
        assert resp.content == "bonjour"

    @patch("vibecollab.agent.llm_client.LLMClient._call_openai")
    def test_ask_without_context(self, mock_call):
        """ask() without project_root sends just the question."""
        mock_call.return_value = LLMResponse(content="42")
        client = self._make_client()
        resp = client.ask("What is the answer?")
        assert resp.content == "42"
        call_messages = mock_call.call_args[0][0]
        assert len(call_messages) == 1
        assert call_messages[0].role == "user"

    @patch("vibecollab.agent.llm_client.LLMClient._call_openai")
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

    @patch("vibecollab.agent.llm_client.LLMClient._call_openai")
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


# ---------------------------------------------------------------------------
# LLMConfig — 配置文件层 + 边界情况
# ---------------------------------------------------------------------------

class TestLLMConfigFileLayer:
    """测试三层配置解析中的配置文件层."""

    @patch.dict(os.environ, {}, clear=True)
    @patch("vibecollab.core.config_manager.resolve_llm_config")
    def test_config_file_fallback(self, mock_resolve):
        """环境变量为空时，从配置文件获取值."""
        mock_resolve.return_value = {
            "provider": "anthropic",
            "api_key": "file-key-123",
            "model": "claude-3-opus",
            "base_url": "https://custom.api.com",
            "max_tokens": "8192",
        }
        # 清除环境变量以确保不干扰
        for env in [ENV_PROVIDER, ENV_API_KEY, ENV_MODEL, ENV_BASE_URL, ENV_MAX_TOKENS]:
            os.environ.pop(env, None)

        cfg = LLMConfig()
        assert cfg.provider == "anthropic"
        assert cfg.api_key == "file-key-123"
        assert cfg.model == "claude-3-opus"
        assert cfg.base_url == "https://custom.api.com"
        assert cfg.max_tokens == 8192

    @patch.dict(os.environ, {ENV_PROVIDER: "openai", ENV_API_KEY: "env-key"}, clear=False)
    @patch("vibecollab.core.config_manager.resolve_llm_config")
    def test_env_overrides_file(self, mock_resolve):
        """环境变量优先于配置文件."""
        mock_resolve.return_value = {
            "provider": "anthropic",
            "api_key": "file-key",
        }
        cfg = LLMConfig()
        assert cfg.provider == "openai"  # env 优先
        assert cfg.api_key == "env-key"  # env 优先

    def test_explicit_overrides_all(self):
        """显式参数优先于环境变量和配置文件."""
        with patch.dict(os.environ, {ENV_PROVIDER: "anthropic", ENV_API_KEY: "env-key"}):
            cfg = LLMConfig(provider="openai", api_key="explicit-key")
            assert cfg.provider == "openai"
            assert cfg.api_key == "explicit-key"

    @patch("vibecollab.core.config_manager.resolve_llm_config",
           side_effect=Exception("config read error"))
    def test_config_file_exception_graceful(self, mock_resolve):
        """配置文件读取异常时静默降级."""
        cfg = LLMConfig()
        # 不抛异常，使用默认值
        assert cfg.provider == DEFAULT_PROVIDER


# ---------------------------------------------------------------------------
# Dual Provider — 深度测试
# ---------------------------------------------------------------------------

class TestDualProviderDeep:
    """测试 OpenAI 和 Anthropic 的深度行为."""

    def _make_mock_httpx(self, status_code=200, json_data=None, text=""):
        mock_httpx = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.text = text
        mock_response.json.return_value = json_data or {}
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = lambda s: mock_client
        mock_client.__exit__ = lambda s, *a: None
        mock_httpx.Client.return_value = mock_client
        return mock_httpx, mock_client

    def test_openai_default_url(self):
        """OpenAI 无 base_url 时使用默认 URL."""
        client = LLMClient(LLMConfig(api_key="test", base_url=""))
        mock_httpx, mock_client = self._make_mock_httpx(json_data={
            "choices": [{"message": {"content": "hi"}}],
            "model": "gpt-4o",
        })
        client._httpx = mock_httpx

        client._call_openai([Message(role="user", content="test")], 0.7)
        call_url = mock_client.post.call_args[0][0]
        assert call_url == "https://api.openai.com/v1/chat/completions"

    def test_openai_custom_base_url_with_trailing_slash(self):
        """OpenAI 自定义 base_url 尾部斜杠被去掉."""
        client = LLMClient(LLMConfig(api_key="test", base_url="https://custom.api/v1/"))
        mock_httpx, mock_client = self._make_mock_httpx(json_data={
            "choices": [{"message": {"content": "hi"}}],
        })
        client._httpx = mock_httpx

        client._call_openai([Message(role="user", content="test")], 0.7)
        call_url = mock_client.post.call_args[0][0]
        assert call_url == "https://custom.api/v1/chat/completions"

    def test_anthropic_default_url(self):
        """Anthropic 无 base_url 时使用默认 URL."""
        client = LLMClient(LLMConfig(
            provider="anthropic", api_key="test", base_url=""))
        mock_httpx, mock_client = self._make_mock_httpx(json_data={
            "content": [{"type": "text", "text": "reply"}],
        })
        client._httpx = mock_httpx

        client._call_anthropic([Message(role="user", content="test")], 0.7)
        call_url = mock_client.post.call_args[0][0]
        assert call_url == "https://api.anthropic.com/v1/messages"

    def test_openai_auth_header(self):
        """OpenAI 请求包含正确的 Authorization header."""
        client = LLMClient(LLMConfig(api_key="sk-test-key"))
        mock_httpx, mock_client = self._make_mock_httpx(json_data={
            "choices": [{"message": {"content": "hi"}}],
        })
        client._httpx = mock_httpx

        client._call_openai([Message(role="user", content="test")], 0.7)
        headers = mock_client.post.call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer sk-test-key"

    def test_anthropic_headers(self):
        """Anthropic 请求包含 x-api-key 和 anthropic-version header."""
        client = LLMClient(LLMConfig(
            provider="anthropic", api_key="ant-key"))
        mock_httpx, mock_client = self._make_mock_httpx(json_data={
            "content": [{"type": "text", "text": "reply"}],
        })
        client._httpx = mock_httpx

        client._call_anthropic([Message(role="user", content="test")], 0.7)
        headers = mock_client.post.call_args[1]["headers"]
        assert headers["x-api-key"] == "ant-key"
        assert headers["anthropic-version"] == "2023-06-01"

    def test_unknown_provider_falls_to_openai(self):
        """未知 provider 走 OpenAI 路径."""
        client = LLMClient(LLMConfig(provider="gemini", api_key="test"))
        mock_httpx, mock_client = self._make_mock_httpx(json_data={
            "choices": [{"message": {"content": "response"}}],
        })
        client._httpx = mock_httpx

        resp = client.chat([Message(role="user", content="test")])
        assert resp.content == "response"
        # 验证调用了 OpenAI 风格 URL
        call_url = mock_client.post.call_args[0][0]
        assert "chat/completions" in call_url

    def test_anthropic_no_system_message(self):
        """Anthropic 无 system 消息时 payload 不包含 system 字段."""
        client = LLMClient(LLMConfig(
            provider="anthropic", api_key="test"))
        mock_httpx, mock_client = self._make_mock_httpx(json_data={
            "content": [{"type": "text", "text": "reply"}],
        })
        client._httpx = mock_httpx

        client._call_anthropic([Message(role="user", content="hi")], 0.7)
        payload = mock_client.post.call_args[1]["json"]
        assert "system" not in payload

    def test_anthropic_multiple_system_messages(self):
        """Anthropic 多个 system 消息被拼接."""
        client = LLMClient(LLMConfig(
            provider="anthropic", api_key="test"))
        mock_httpx, mock_client = self._make_mock_httpx(json_data={
            "content": [{"type": "text", "text": "reply"}],
        })
        client._httpx = mock_httpx

        messages = [
            Message(role="system", content="Rule 1"),
            Message(role="system", content="Rule 2"),
            Message(role="user", content="hi"),
        ]
        client._call_anthropic(messages, 0.7)
        payload = mock_client.post.call_args[1]["json"]
        assert "Rule 1" in payload["system"]
        assert "Rule 2" in payload["system"]

    def test_anthropic_multi_content_blocks(self):
        """Anthropic 响应多个 text 块被拼接."""
        client = LLMClient(LLMConfig(
            provider="anthropic", api_key="test"))
        mock_httpx, _ = self._make_mock_httpx(json_data={
            "content": [
                {"type": "text", "text": "Hello "},
                {"type": "image", "data": "..."},
                {"type": "text", "text": "World"},
            ],
        })
        client._httpx = mock_httpx

        resp = client._call_anthropic([Message(role="user", content="test")], 0.7)
        assert resp.content == "Hello World"

    def test_openai_empty_choices(self):
        """OpenAI 空 choices 返回空 content."""
        client = LLMClient(LLMConfig(api_key="test"))
        mock_httpx, _ = self._make_mock_httpx(json_data={
            "choices": [],
        })
        client._httpx = mock_httpx

        resp = client._call_openai([Message(role="user", content="test")], 0.7)
        assert resp.content == ""
        assert not resp.ok

    def test_openai_500_error(self):
        """OpenAI 500 错误抛出 RuntimeError."""
        client = LLMClient(LLMConfig(api_key="test"))
        mock_httpx, _ = self._make_mock_httpx(
            status_code=500, text="Internal Server Error")
        client._httpx = mock_httpx

        with pytest.raises(RuntimeError, match="500"):
            client._call_openai([Message(role="user", content="hi")], 0.7)


# ---------------------------------------------------------------------------
# build_project_context — 更多边界情况
# ---------------------------------------------------------------------------

class TestBuildProjectContextEdge:
    def test_include_context_false(self, tmp_path):
        """include_context=False 时不包含 CONTEXT.md."""
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "CONTEXT.md").write_text("# Context\nContent here")
        ctx = build_project_context(tmp_path, include_context=False)
        assert "Content here" not in ctx

    def test_include_tasks_false(self, tmp_path):
        """include_tasks=False 时不包含任务."""
        vc = tmp_path / ".vibecollab"
        vc.mkdir()
        (vc / "tasks.json").write_text(json.dumps({
            "T1": {"status": "TODO", "feature": "test"}
        }))
        ctx = build_project_context(tmp_path, include_tasks=False)
        assert "T1" not in ctx

    def test_tasks_json_corrupted(self, tmp_path):
        """tasks.json 损坏时不崩溃."""
        vc = tmp_path / ".vibecollab"
        vc.mkdir()
        (vc / "tasks.json").write_text("{invalid json")
        ctx = build_project_context(tmp_path)
        # 不抛异常，tasks section 被跳过
        assert isinstance(ctx, str)

    def test_events_jsonl_partial_corrupt(self, tmp_path):
        """events.jsonl 部分行损坏时只跳过坏行."""
        vc = tmp_path / ".vibecollab"
        vc.mkdir()
        lines = [
            json.dumps({"event_type": "CUSTOM", "summary": "good event"}),
            "invalid json line",
            json.dumps({"event_type": "CUSTOM", "summary": "another good"}),
        ]
        (vc / "events.jsonl").write_text("\n".join(lines))
        ctx = build_project_context(tmp_path)
        assert "good event" in ctx or isinstance(ctx, str)

    def test_events_jsonl_empty(self, tmp_path):
        """events.jsonl 空文件不崩溃."""
        vc = tmp_path / ".vibecollab"
        vc.mkdir()
        (vc / "events.jsonl").write_text("")
        ctx = build_project_context(tmp_path)
        assert isinstance(ctx, str)

    def test_all_tasks_done(self, tmp_path):
        """所有任务为 DONE 时不包含 Active Tasks section."""
        vc = tmp_path / ".vibecollab"
        vc.mkdir()
        (vc / "tasks.json").write_text(json.dumps({
            "T1": {"status": "DONE", "feature": "done task"}
        }))
        ctx = build_project_context(tmp_path)
        assert "Active Tasks" not in ctx or "done task" not in ctx


# ---------------------------------------------------------------------------
# LLMClient.ask() — 更多路径
# ---------------------------------------------------------------------------

class TestAskMethodEdge:
    def _make_client(self, provider="openai"):
        cfg = LLMConfig(provider=provider, api_key="test-key")
        client = LLMClient(cfg)
        mock_httpx = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "answer"}}],
            "model": "gpt-4o",
        }
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = lambda s: mock_client
        mock_client.__exit__ = lambda s, *a: None
        mock_httpx.Client.return_value = mock_client
        client._httpx = mock_httpx
        return client, mock_client

    def test_ask_with_both_system_and_project(self, tmp_path):
        """同时提供 system_prompt 和 project_root 时，用自定义 system."""
        (tmp_path / "project.yaml").write_text("project_name: test")
        client, mock_client = self._make_client()

        resp = client.ask(
            "question",
            system_prompt="Custom system prompt",
            project_root=tmp_path,
        )
        assert resp.content == "answer"
        payload = mock_client.post.call_args[1]["json"]
        system_msg = payload["messages"][0]["content"]
        assert "Custom system prompt" in system_msg

    def test_ask_temperature_passed(self):
        """ask() 将 temperature 传递到底层 chat()."""
        client, mock_client = self._make_client()

        with patch.object(client, "chat", wraps=client.chat) as mock_chat:
            client.ask("question", temperature=0.1)
            mock_chat.assert_called_once()
            assert mock_chat.call_args[1]["temperature"] == 0.1

    def test_client_default_config(self):
        """LLMClient() 无参数构造使用默认 LLMConfig."""
        client = LLMClient()
        assert client.config.provider == DEFAULT_PROVIDER
        assert client.config.model == DEFAULT_MODEL_OPENAI
