#!/usr/bin/env python3
"""
VibeCollab Version Bump Tool

Single Source of Truth: src/vibecollab/__init__.py -> __version__

Usage:
    # Check current version across all files (dry-run):
    python scripts/bump_version.py

    # Bump to a new version and sync everywhere:
    python scripts/bump_version.py 0.11.0

    # Just sync current __init__.py version to all files:
    python scripts/bump_version.py --sync
"""

import re
import sys
from pathlib import Path

# Project root (relative to this script's location)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# === Single Source of Truth ===
INIT_FILE = PROJECT_ROOT / "src" / "vibecollab" / "__init__.py"

# === Files that contain version references to sync ===
VERSION_TARGETS = [
    {
        "file": INIT_FILE,
        "pattern": r'(__version__\s*=\s*")[^"]+(")',
        "replace": r"\g<1>{version}\g<2>",
        "description": "__init__.py (source of truth)",
    },
    {
        "file": PROJECT_ROOT / "README.md",
        "pattern": r"(Current version v)\d+\.\d+\.\d+(?:[a-zA-Z0-9\-]+(?:\.\d+)*)?",
        "replace": r"\g<1>{version}",
        "description": "README.md footer",
    },
    {
        "file": PROJECT_ROOT / "README.pypi.md",
        "pattern": r"(Current version v)\d+\.\d+\.\d+(?:[a-zA-Z0-9\-]+(?:\.\d+)*)?",
        "replace": r"\g<1>{version}",
        "description": "README.pypi.md footer",
    },
    {
        "file": PROJECT_ROOT / "README.zh-CN.md",
        "pattern": r"(当前版本 v)\d+\.\d+\.\d+(?:[a-zA-Z0-9\-]+(?:\.\d+)*)?",
        "replace": r"\g<1>{version}",
        "description": "README.zh-CN.md footer",
    },
    {
        "file": PROJECT_ROOT / "llms.txt",
        "pattern": r"(Current version: v)\d+\.\d+\.\d+(?:[a-zA-Z0-9\-]+(?:\.\d+)*)?",
        "replace": r"\g<1>{version}",
        "description": "llms.txt version line",
    },
    {
        "file": PROJECT_ROOT / "docs" / "CONTEXT.md",
        "pattern": r"(\*\*Version\*\*: v)\d+\.\d+\.\d+(?:[a-zA-Z0-9\-]+(?:\.\d+)*)?",
        "replace": r"\g<1>{version}",
        "description": "CONTEXT.md project status version",
    },
    {
        "file": PROJECT_ROOT / "docs" / "CONTEXT.md",
        "pattern": r"(## Architecture \(v)\d+\.\d+\.\d+(?:[a-zA-Z0-9\-]+(?:\.\d+)*)?(\))",
        "replace": r"\g<1>{version}\g<2>",
        "description": "CONTEXT.md architecture heading",
    },
]


def read_current_version() -> str:
    """Read the current version from __init__.py (single source of truth)."""
    content = INIT_FILE.read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
    if not match:
        print(f"ERROR: Cannot find __version__ in {INIT_FILE}")
        sys.exit(1)
    return match.group(1)


def check_versions() -> list[dict]:
    """Check version consistency across all files. Returns list of results."""
    current = read_current_version()
    results = []

    for target in VERSION_TARGETS:
        fpath = target["file"]
        if not fpath.exists():
            results.append({
                "file": target["description"],
                "path": str(fpath.relative_to(PROJECT_ROOT)),
                "status": "MISSING",
                "found": None,
                "expected": current,
            })
            continue

        content = fpath.read_text(encoding="utf-8")
        # Extract the version number from the pattern match
        match = re.search(target["pattern"], content)
        if not match:
            results.append({
                "file": target["description"],
                "path": str(fpath.relative_to(PROJECT_ROOT)),
                "status": "NO_MATCH",
                "found": None,
                "expected": current,
            })
            continue

        # Extract just the version number from the full match
        full_match = match.group(0)
        ver_match = re.search(r"\d+\.\d+\.\d+(?:[a-zA-Z0-9\-]+(?:\.\d+)*)?", full_match)
        found_version = ver_match.group(0) if ver_match else "?"

        status = "OK" if found_version == current else "MISMATCH"
        results.append({
            "file": target["description"],
            "path": str(fpath.relative_to(PROJECT_ROOT)),
            "status": status,
            "found": found_version,
            "expected": current,
        })

    return results


def sync_version(new_version: str) -> list[dict]:
    """Write the new version to __init__.py, then sync to all target files."""
    changes = []

    for target in VERSION_TARGETS:
        fpath = target["file"]
        if not fpath.exists():
            changes.append({
                "file": target["description"],
                "action": "SKIPPED (file not found)",
            })
            continue

        content = fpath.read_text(encoding="utf-8")
        replace_str = target["replace"].format(version=new_version)
        new_content, count = re.subn(target["pattern"], replace_str, content)

        if count > 0:
            fpath.write_text(new_content, encoding="utf-8")
            changes.append({
                "file": target["description"],
                "action": f"UPDATED ({count} replacement(s))",
            })
        else:
            changes.append({
                "file": target["description"],
                "action": "NO_MATCH (pattern not found)",
            })

    return changes


def print_check_report(results: list[dict], version: str) -> bool:
    """Print version check report. Returns True if all consistent."""
    print(f"\n{'=' * 60}")
    print(f"  VibeCollab Version Check")
    print(f"  Source of Truth: {version}")
    print(f"{'=' * 60}\n")

    all_ok = True
    for r in results:
        icon = {
            "OK": "[OK]",
            "MISMATCH": "[!!]",
            "MISSING": "[??]",
            "NO_MATCH": "[??]",
        }.get(r["status"], "[?]")

        if r["status"] == "OK":
            print(f"  {icon} {r['file']}")
            print(f"       {r['path']} -> {r['found']}")
        elif r["status"] == "MISMATCH":
            all_ok = False
            print(f"  {icon} {r['file']}")
            print(f"       {r['path']} -> {r['found']} (expected {r['expected']})")
        else:
            all_ok = False
            print(f"  {icon} {r['file']}")
            print(f"       {r['path']} -> {r['status']}")
        print()

    if all_ok:
        print(f"  [OK] All {len(results)} version references are consistent!\n")
    else:
        mismatches = sum(1 for r in results if r["status"] != "OK")
        print(f"  [!!] {mismatches} issue(s) found. Run with --sync to fix.\n")

    return all_ok


def print_sync_report(changes: list[dict], version: str):
    """Print sync result report."""
    print(f"\n{'=' * 60}")
    print(f"  VibeCollab Version Sync -> {version}")
    print(f"{'=' * 60}\n")

    for c in changes:
        icon = "[OK]" if "UPDATED" in c["action"] else "[??]"
        print(f"  {icon} {c['file']}: {c['action']}")

    print(f"\n  Done! Remember to update docs/CHANGELOG.md manually.\n")
    print(f"  Suggested commit:")
    print(f'    git add -A && git commit -m "chore(release): bump version to v{version}"')
    print()


def main():
    args = sys.argv[1:]

    if not args:
        # Default: check mode (dry-run)
        current = read_current_version()
        results = check_versions()
        print_check_report(results, current)
        return

    if args[0] == "--sync":
        # Sync current __init__.py version to all files
        current = read_current_version()
        changes = sync_version(current)
        print_sync_report(changes, current)
        return

    if args[0] == "--help" or args[0] == "-h":
        print(__doc__)
        return

    # Bump to a specific version
    new_version = args[0].lstrip("v")

    # Validate version format
    if not re.match(r"^\d+\.\d+\.\d+([a-zA-Z0-9.\-]+)?$", new_version):
        print(f"ERROR: Invalid version format: {new_version}")
        print(f"  Expected: MAJOR.MINOR.PATCH (e.g., 0.11.0, 1.0.0)")
        sys.exit(1)

    current = read_current_version()
    print(f"\n  Bumping version: {current} -> {new_version}\n")

    changes = sync_version(new_version)
    print_sync_report(changes, new_version)


if __name__ == "__main__":
    main()
