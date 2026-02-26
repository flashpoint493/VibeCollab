"""
Configuration Manager — Persistent LLM and agent configuration.

Provides a three-layer configuration resolution:
  CLI args > Environment variables > Config file (~/.vibecollab/config.yaml) > Defaults

The config file lives in the user's home directory (never in the project)
so API keys are never committed to version control.

Also supports loading VIBECOLLAB_LLM_* variables from a project-local .env file.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def get_config_dir() -> Path:
    """Get the global VibeCollab config directory (~/.vibecollab/)."""
    return Path.home() / ".vibecollab"


def get_config_path() -> Path:
    """Get the global config file path (~/.vibecollab/config.yaml)."""
    return get_config_dir() / "config.yaml"


# ---------------------------------------------------------------------------
# Config file read / write
# ---------------------------------------------------------------------------

def load_config() -> Dict[str, Any]:
    """Load configuration from ~/.vibecollab/config.yaml.

    Returns an empty dict if the file doesn't exist or is invalid.
    """
    path = get_config_path()
    if not path.exists():
        return {}
    try:
        import yaml
        text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_config(config: Dict[str, Any]) -> Path:
    """Save configuration to ~/.vibecollab/config.yaml.

    Creates the directory if it doesn't exist.
    Returns the config file path.
    """
    import yaml

    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.dump(config, default_flow_style=False, allow_unicode=True,
                     sort_keys=False)
    path.write_text(text, encoding="utf-8")
    return path


def get_config_value(key: str, default: Any = None) -> Any:
    """Get a nested config value using dot notation.

    Example: get_config_value("llm.api_key") -> config["llm"]["api_key"]
    """
    config = load_config()
    parts = key.split(".")
    current = config
    for part in parts:
        if not isinstance(current, dict):
            return default
        current = current.get(part)
        if current is None:
            return default
    return current


def set_config_value(key: str, value: Any) -> Path:
    """Set a nested config value using dot notation and save.

    Example: set_config_value("llm.api_key", "sk-xxx")
    """
    config = load_config()
    parts = key.split(".")
    current = config
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value
    return save_config(config)


# ---------------------------------------------------------------------------
# .env file parsing (lightweight, no python-dotenv dependency)
# ---------------------------------------------------------------------------

_ENV_LINE_RE = re.compile(
    r"""
    ^\s*
    (?:export\s+)?          # optional 'export' prefix
    (VIBECOLLAB_\w+)        # key: must start with VIBECOLLAB_
    \s*=\s*
    (.+?)                   # value
    \s*$
    """,
    re.VERBOSE,
)


def parse_dotenv(dotenv_path: Path) -> Dict[str, str]:
    """Parse VIBECOLLAB_* variables from a .env file.

    Only extracts lines matching VIBECOLLAB_* keys.
    Supports optional 'export' prefix and quoted values.
    Does NOT modify os.environ.

    Returns:
        Dict of key-value pairs found.
    """
    result = {}
    if not dotenv_path.exists():
        return result

    try:
        for line in dotenv_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = _ENV_LINE_RE.match(line)
            if m:
                key, value = m.group(1), m.group(2)
                # Strip surrounding quotes
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                    value = value[1:-1]
                result[key] = value
    except OSError:
        pass
    return result


# ---------------------------------------------------------------------------
# Unified LLM config resolution
# ---------------------------------------------------------------------------

def resolve_llm_config(project_root: Optional[Path] = None) -> Dict[str, str]:
    """Resolve LLM configuration from all sources.

    Priority (highest first):
    1. Environment variables (VIBECOLLAB_LLM_*)
    2. Project .env file (if project_root provided)
    3. Global config file (~/.vibecollab/config.yaml)

    Returns a dict with keys: provider, api_key, model, base_url, max_tokens.
    Only non-empty values are included.
    """
    result = {}

    # Layer 3: Global config file (lowest priority)
    file_config = load_config()
    llm_section = file_config.get("llm", {})
    if isinstance(llm_section, dict):
        for key in ("provider", "api_key", "model", "base_url", "max_tokens"):
            val = llm_section.get(key)
            if val is not None and str(val).strip():
                result[key] = str(val).strip()

    # Layer 2: Project .env file
    if project_root:
        dotenv_vars = parse_dotenv(project_root / ".env")
        _ENV_KEY_MAP = {
            "VIBECOLLAB_LLM_PROVIDER": "provider",
            "VIBECOLLAB_LLM_API_KEY": "api_key",
            "VIBECOLLAB_LLM_MODEL": "model",
            "VIBECOLLAB_LLM_BASE_URL": "base_url",
            "VIBECOLLAB_LLM_MAX_TOKENS": "max_tokens",
        }
        for env_key, config_key in _ENV_KEY_MAP.items():
            val = dotenv_vars.get(env_key)
            if val:
                result[config_key] = val

    # Layer 1: Environment variables (highest priority)
    _ENV_KEY_MAP = {
        "VIBECOLLAB_LLM_PROVIDER": "provider",
        "VIBECOLLAB_LLM_API_KEY": "api_key",
        "VIBECOLLAB_LLM_MODEL": "model",
        "VIBECOLLAB_LLM_BASE_URL": "base_url",
        "VIBECOLLAB_LLM_MAX_TOKENS": "max_tokens",
    }
    for env_key, config_key in _ENV_KEY_MAP.items():
        val = os.environ.get(env_key)
        if val:
            result[config_key] = val

    return result
