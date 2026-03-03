"""
Internationalization (i18n) support for VibeCollab CLI.

Uses Python stdlib gettext for zero external dependencies.
Default language is English (source strings are English, no en.po needed).
Chinese translation is provided via zh_CN/LC_MESSAGES/vibecollab.po/.mo.

Language selection priority:
  1. --lang CLI option (pre-parsed from sys.argv before Click loads)
  2. VIBECOLLAB_LANG environment variable       -- e.g. "zh"
  3. Fallback to English (passthrough)

Usage in CLI modules:
    from vibecollab.i18n import _
    click.echo(_("Hello, world!"))

Note: setup_locale() is called automatically at import time using env var
and sys.argv pre-parsing, so that Click help= parameters (evaluated at
module import time) pick up the correct language.
"""

import gettext
import os
import sys
from pathlib import Path
from typing import Optional

# Directory containing locale/*/LC_MESSAGES/vibecollab.mo
_LOCALE_DIR = Path(__file__).parent / "locales"

# The active translation object; starts as NullTranslations (English passthrough)
_current: gettext.NullTranslations = gettext.NullTranslations()

# Language alias mapping (short codes -> full locale)
_LANG_ALIASES = {
    "zh": "zh_CN",
    "zh-cn": "zh_CN",
    "zh_cn": "zh_CN",
    "zh-tw": "zh_TW",
    "zh_tw": "zh_TW",
    "en": "en",
    "en_us": "en",
    "en-us": "en",
}


def setup_locale(lang: Optional[str] = None) -> None:
    """Initialize the translation for the given language.

    Args:
        lang: Language code (e.g. "zh", "en", "zh_CN").
              If None, checks VIBECOLLAB_LANG env var.
              Does NOT auto-detect system locale to keep default output in English.
    """
    global _current

    if lang is None:
        lang = os.environ.get("VIBECOLLAB_LANG", "").strip()

    if not lang or lang.lower().startswith("en"):
        # English: use NullTranslations (passthrough)
        _current = gettext.NullTranslations()
        return

    # Resolve aliases
    resolved = _LANG_ALIASES.get(lang.lower(), lang)

    try:
        _current = gettext.translation(
            "vibecollab",
            localedir=str(_LOCALE_DIR),
            languages=[resolved],
            fallback=True,  # fallback to English if .mo not found
        )
    except Exception:
        # Any error: fall back to English
        _current = gettext.NullTranslations()


def _(message: str) -> str:
    """Translate a string using the current locale.

    Usage:
        from vibecollab.i18n import _
        click.echo(_("Some message"))
    """
    return _current.gettext(message)


def ngettext(singular: str, plural: str, n: int) -> str:
    """Translate a string with plural form support.

    Usage:
        from vibecollab.i18n import ngettext
        msg = ngettext("{n} file processed", "{n} files processed", count)
    """
    return _current.ngettext(singular, plural, n)


def get_current_language() -> str:
    """Return the current language code, or 'en' if using passthrough."""
    info = _current.info()
    lang = info.get("language", "")
    return lang if lang else "en"


def _pre_parse_lang() -> Optional[str]:
    """Pre-parse --lang from sys.argv before Click processes commands.

    This allows the locale to be set before any CLI module is imported,
    ensuring that Click help= parameters are translated correctly.
    """
    try:
        argv = sys.argv[1:]
        for i, arg in enumerate(argv):
            if arg == "--lang" and i + 1 < len(argv):
                return argv[i + 1]
            if arg.startswith("--lang="):
                return arg.split("=", 1)[1]
    except Exception:
        pass
    return None


# Auto-initialize locale at import time:
# 1. Check --lang from sys.argv (pre-parse before Click)
# 2. Check VIBECOLLAB_LANG env var
# 3. Check system locale
# This ensures help= strings are translated when CLI modules are loaded.
_pre_lang = _pre_parse_lang()
if _pre_lang:
    setup_locale(_pre_lang)
else:
    setup_locale()
