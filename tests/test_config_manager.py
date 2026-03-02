"""Tests for config_manager and cli_config modules."""

import textwrap
from pathlib import Path

import pytest

from vibecollab.core.config_manager import (
    get_config_dir,
    get_config_path,
    get_config_value,
    load_config,
    parse_dotenv,
    resolve_llm_config,
    save_config,
    set_config_value,
)

# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    """Redirect ~/.vibecollab/ to a temp dir."""
    config_dir = tmp_path / ".vibecollab"
    monkeypatch.setattr(
        "vibecollab.core.config_manager.get_config_dir",
        lambda: config_dir,
    )
    monkeypatch.setattr(
        "vibecollab.core.config_manager.get_config_path",
        lambda: config_dir / "config.yaml",
    )
    return config_dir


@pytest.fixture
def project_dir(tmp_path):
    """A temporary project directory."""
    return tmp_path / "project"


# ===========================================================================
# Tests: Config file operations
# ===========================================================================

class TestConfigPaths:
    def test_get_config_dir_in_home(self):
        d = get_config_dir()
        assert d.name == ".vibecollab"
        assert d.parent == Path.home()

    def test_get_config_path(self):
        p = get_config_path()
        assert p.name == "config.yaml"
        assert p.parent.name == ".vibecollab"


class TestLoadSaveConfig:
    def test_load_empty_returns_dict(self, fake_home):
        assert load_config() == {}

    def test_save_and_load_roundtrip(self, fake_home):
        data = {"llm": {"provider": "openai", "api_key": "sk-test"}}
        save_config(data)
        loaded = load_config()
        assert loaded["llm"]["provider"] == "openai"
        assert loaded["llm"]["api_key"] == "sk-test"

    def test_save_creates_directory(self, fake_home):
        assert not fake_home.exists()
        save_config({"hello": "world"})
        assert fake_home.exists()
        assert (fake_home / "config.yaml").exists()

    def test_load_invalid_yaml_returns_empty(self, fake_home):
        fake_home.mkdir(parents=True, exist_ok=True)
        (fake_home / "config.yaml").write_text(":::invalid", encoding="utf-8")
        assert load_config() == {}

    def test_load_non_dict_returns_empty(self, fake_home):
        fake_home.mkdir(parents=True, exist_ok=True)
        (fake_home / "config.yaml").write_text("- just\n- a\n- list",
                                                encoding="utf-8")
        assert load_config() == {}


class TestGetSetConfigValue:
    def test_get_nested_value(self, fake_home):
        save_config({"llm": {"provider": "anthropic", "model": "claude-3"}})
        assert get_config_value("llm.provider") == "anthropic"
        assert get_config_value("llm.model") == "claude-3"

    def test_get_missing_returns_default(self, fake_home):
        save_config({"llm": {"provider": "openai"}})
        assert get_config_value("llm.api_key") is None
        assert get_config_value("llm.api_key", "fallback") == "fallback"
        assert get_config_value("nonexist.key", "def") == "def"

    def test_set_creates_nested_structure(self, fake_home):
        set_config_value("llm.provider", "openai")
        assert get_config_value("llm.provider") == "openai"

    def test_set_preserves_existing(self, fake_home):
        save_config({"llm": {"provider": "openai"}, "other": "data"})
        set_config_value("llm.model", "gpt-4o-mini")
        config = load_config()
        assert config["llm"]["provider"] == "openai"
        assert config["llm"]["model"] == "gpt-4o-mini"
        assert config["other"] == "data"

    def test_set_overwrites_value(self, fake_home):
        set_config_value("llm.provider", "openai")
        set_config_value("llm.provider", "anthropic")
        assert get_config_value("llm.provider") == "anthropic"


# ===========================================================================
# Tests: .env parsing
# ===========================================================================

class TestParseDotenv:
    def test_parse_basic(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text(
            "VIBECOLLAB_LLM_API_KEY=sk-test123\n"
            "VIBECOLLAB_LLM_PROVIDER=openai\n",
            encoding="utf-8",
        )
        result = parse_dotenv(env_file)
        assert result["VIBECOLLAB_LLM_API_KEY"] == "sk-test123"
        assert result["VIBECOLLAB_LLM_PROVIDER"] == "openai"

    def test_parse_with_quotes(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text(
            'VIBECOLLAB_LLM_API_KEY="sk-quoted"\n'
            "VIBECOLLAB_LLM_MODEL='gpt-4o'\n",
            encoding="utf-8",
        )
        result = parse_dotenv(env_file)
        assert result["VIBECOLLAB_LLM_API_KEY"] == "sk-quoted"
        assert result["VIBECOLLAB_LLM_MODEL"] == "gpt-4o"

    def test_parse_with_export_prefix(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text(
            "export VIBECOLLAB_LLM_API_KEY=sk-export\n",
            encoding="utf-8",
        )
        result = parse_dotenv(env_file)
        assert result["VIBECOLLAB_LLM_API_KEY"] == "sk-export"

    def test_ignores_comments_and_blanks(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text(
            "# This is a comment\n"
            "\n"
            "VIBECOLLAB_LLM_API_KEY=sk-test\n"
            "# Another comment\n"
            "NOT_VIBECOLLAB=ignored\n",
            encoding="utf-8",
        )
        result = parse_dotenv(env_file)
        assert len(result) == 1
        assert result["VIBECOLLAB_LLM_API_KEY"] == "sk-test"

    def test_ignores_non_vibecollab_keys(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text(
            "PYPI_API_TOKEN=pypi-xxx\n"
            "GITHUB_TOKEN=ghp-xxx\n"
            "VIBECOLLAB_LLM_API_KEY=sk-only-this\n",
            encoding="utf-8",
        )
        result = parse_dotenv(env_file)
        assert len(result) == 1
        assert "PYPI_API_TOKEN" not in result

    def test_nonexistent_file(self, tmp_path):
        result = parse_dotenv(tmp_path / "nonexistent.env")
        assert result == {}

    def test_parse_spaces_around_equals(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text(
            "VIBECOLLAB_LLM_API_KEY = sk-spaced\n",
            encoding="utf-8",
        )
        result = parse_dotenv(env_file)
        assert result["VIBECOLLAB_LLM_API_KEY"] == "sk-spaced"

    def test_parse_all_llm_vars(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text(textwrap.dedent("""\
            VIBECOLLAB_LLM_PROVIDER=anthropic
            VIBECOLLAB_LLM_API_KEY=sk-ant-xxx
            VIBECOLLAB_LLM_MODEL=claude-3
            VIBECOLLAB_LLM_BASE_URL=https://custom.api.com
            VIBECOLLAB_LLM_MAX_TOKENS=8192
        """), encoding="utf-8")
        result = parse_dotenv(env_file)
        assert len(result) == 5
        assert result["VIBECOLLAB_LLM_MAX_TOKENS"] == "8192"


# ===========================================================================
# Tests: Unified resolution
# ===========================================================================

class TestResolveLLMConfig:
    def test_empty_returns_empty(self, fake_home):
        """No config anywhere → empty dict."""
        result = resolve_llm_config()
        assert result == {}

    def test_config_file_values(self, fake_home):
        save_config({"llm": {"provider": "anthropic", "api_key": "sk-file"}})
        result = resolve_llm_config()
        assert result["provider"] == "anthropic"
        assert result["api_key"] == "sk-file"

    def test_env_overrides_file(self, fake_home, monkeypatch):
        save_config({"llm": {"provider": "openai", "api_key": "sk-file"}})
        monkeypatch.setenv("VIBECOLLAB_LLM_API_KEY", "sk-env")
        result = resolve_llm_config()
        assert result["api_key"] == "sk-env"
        assert result["provider"] == "openai"  # from file (no env override)

    def test_dotenv_overrides_file(self, fake_home, tmp_path):
        save_config({"llm": {"api_key": "sk-file", "provider": "openai"}})
        dotenv = tmp_path / ".env"
        dotenv.write_text(
            "VIBECOLLAB_LLM_API_KEY=sk-dotenv\n", encoding="utf-8")
        result = resolve_llm_config(project_root=tmp_path)
        assert result["api_key"] == "sk-dotenv"

    def test_env_overrides_dotenv(self, fake_home, tmp_path, monkeypatch):
        dotenv = tmp_path / ".env"
        dotenv.write_text(
            "VIBECOLLAB_LLM_API_KEY=sk-dotenv\n", encoding="utf-8")
        monkeypatch.setenv("VIBECOLLAB_LLM_API_KEY", "sk-env-wins")
        result = resolve_llm_config(project_root=tmp_path)
        assert result["api_key"] == "sk-env-wins"

    def test_ignores_empty_config_values(self, fake_home):
        save_config({"llm": {"provider": "openai", "api_key": "",
                              "model": "  "}})
        result = resolve_llm_config()
        assert "api_key" not in result
        assert "model" not in result
        assert result["provider"] == "openai"

    def test_max_tokens_as_string(self, fake_home):
        save_config({"llm": {"max_tokens": "8192"}})
        result = resolve_llm_config()
        assert result["max_tokens"] == "8192"


# ===========================================================================
# Tests: LLMConfig integration with config file
# ===========================================================================

class TestLLMConfigWithFile:
    def test_reads_from_config_file(self, fake_home):
        save_config({"llm": {"provider": "anthropic", "api_key": "sk-cfg"}})
        from vibecollab.agent.llm_client import LLMConfig
        cfg = LLMConfig()
        assert cfg.is_configured
        assert cfg.api_key == "sk-cfg"
        assert cfg.provider == "anthropic"

    def test_env_overrides_config_file(self, fake_home, monkeypatch):
        save_config({"llm": {"api_key": "sk-cfg", "provider": "openai"}})
        monkeypatch.setenv("VIBECOLLAB_LLM_API_KEY", "sk-env")
        from vibecollab.agent.llm_client import LLMConfig
        cfg = LLMConfig()
        assert cfg.api_key == "sk-env"

    def test_explicit_arg_overrides_all(self, fake_home, monkeypatch):
        save_config({"llm": {"api_key": "sk-cfg"}})
        monkeypatch.setenv("VIBECOLLAB_LLM_API_KEY", "sk-env")
        from vibecollab.agent.llm_client import LLMConfig
        cfg = LLMConfig(api_key="sk-explicit")
        assert cfg.api_key == "sk-explicit"

    def test_no_config_file_still_works(self, fake_home):
        from vibecollab.agent.llm_client import LLMConfig
        cfg = LLMConfig()
        assert not cfg.is_configured
        assert cfg.provider == "openai"  # default


# ===========================================================================
# Tests: CLI commands
# ===========================================================================

class TestCLIConfig:
    def test_config_show_no_config(self, fake_home):
        from click.testing import CliRunner

        from vibecollab.cli.config import config_group

        runner = CliRunner()
        result = runner.invoke(config_group, ["show"])
        assert result.exit_code == 0
        assert "未创建" in result.output or "config.yaml" in result.output

    def test_config_show_with_config(self, fake_home):
        save_config({"llm": {"provider": "openai", "api_key": "sk-testkey123456"}})
        from click.testing import CliRunner

        from vibecollab.cli.config import config_group

        runner = CliRunner()
        result = runner.invoke(config_group, ["show"])
        assert result.exit_code == 0
        assert "openai" in result.output
        # Key should be masked
        assert "sk-testk...3456" in result.output
        assert "sk-testkey123456" not in result.output

    def test_config_set_known_key(self, fake_home):
        from click.testing import CliRunner

        from vibecollab.cli.config import config_group

        runner = CliRunner()
        result = runner.invoke(config_group, ["set", "llm.provider", "anthropic"])
        assert result.exit_code == 0
        assert get_config_value("llm.provider") == "anthropic"

    def test_config_set_api_key_masked(self, fake_home):
        from click.testing import CliRunner

        from vibecollab.cli.config import config_group

        runner = CliRunner()
        result = runner.invoke(config_group, ["set", "llm.api_key", "sk-verylongapikey123"])
        assert result.exit_code == 0
        # Full key should not appear in output
        assert "sk-verylongapikey123" not in result.output
        assert "sk-veryl" in result.output
        # But it should be saved
        assert get_config_value("llm.api_key") == "sk-verylongapikey123"

    def test_config_path(self, fake_home):
        from click.testing import CliRunner

        from vibecollab.cli.config import config_group

        runner = CliRunner()
        result = runner.invoke(config_group, ["path"])
        assert result.exit_code == 0
        assert "config.yaml" in result.output

    def test_config_setup_interactive(self, fake_home):
        from click.testing import CliRunner

        from vibecollab.cli.config import config_group

        runner = CliRunner()
        # Simulate: provider=1(openai), api_key=sk-test, base_url=1(default), model=(empty)
        result = runner.invoke(config_group, ["setup"],
                               input="1\nsk-test-key-12345678\n1\n\n")
        assert result.exit_code == 0
        assert "已保存" in result.output

        config = load_config()
        assert config["llm"]["provider"] == "openai"
        assert config["llm"]["api_key"] == "sk-test-key-12345678"

    def test_config_setup_anthropic(self, fake_home):
        from click.testing import CliRunner

        from vibecollab.cli.config import config_group

        runner = CliRunner()
        # Simulate: provider=2(anthropic), api_key=sk-ant, model=(empty)
        result = runner.invoke(config_group, ["setup"],
                               input="2\nsk-ant-test-123456789\n\n")
        assert result.exit_code == 0
        config = load_config()
        assert config["llm"]["provider"] == "anthropic"
