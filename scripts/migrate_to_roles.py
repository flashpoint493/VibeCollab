"""
Data migration script: Developer-based → Role-based architecture

This script migrates existing project data from developer-based to role-based architecture.
Run this once after upgrading to v0.11.0+.

Usage:
    python migrate_to_roles.py [project_path]

Migration steps:
1. Convert events.jsonl (DEVELOPER_* → ROLE_*)
2. Convert session files (developer → role)
3. Move docs/developers → docs/roles
4. Update .metadata.yaml files
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def migrate_events_jsonl(project_root: Path):
    """Migrate events.jsonl file"""
    events_file = project_root / ".vibecollab" / "events.jsonl"
    if not events_file.exists():
        print(f"  No events.jsonl found, skipping")
        return

    backup_file = events_file.with_suffix(".jsonl.bak")

    # Create backup
    import shutil

    shutil.copy(events_file, backup_file)
    print(f"  Created backup: {backup_file}")

    # Migrate events
    migrated_count = 0
    new_lines = []

    with open(events_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                event = json.loads(line.strip())

                # Update event type
                if event.get("type") == "DEVELOPER_REGISTERED":
                    event["type"] = "ROLE_REGISTERED"
                    migrated_count += 1
                elif event.get("type") == "DEVELOPER_SYNC":
                    event["type"] = "ROLE_SYNC"
                    migrated_count += 1

                # Update actor field (if it was a developer name)
                # Note: We keep the name but it's now considered a role

                new_lines.append(json.dumps(event, ensure_ascii=False))
            except json.JSONDecodeError:
                new_lines.append(line.strip())

    # Write migrated events
    with open(events_file, "w", encoding="utf-8") as f:
        for line in new_lines:
            f.write(line + "\n")

    print(f"  Migrated {migrated_count} events")


def migrate_session_files(project_root: Path):
    """Migrate session files"""
    sessions_dir = project_root / ".vibecollab" / "sessions"
    if not sessions_dir.exists():
        print(f"  No sessions directory found, skipping")
        return

    migrated_count = 0
    for session_file in sessions_dir.glob("*.json"):
        try:
            with open(session_file, "r", encoding="utf-8") as f:
                session = json.load(f)

            # Rename field: developer → role
            if "developer" in session:
                session["role"] = session.pop("developer")
                migrated_count += 1

            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(session, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"  Warning: Failed to migrate {session_file}: {e}")

    print(f"  Migrated {migrated_count} session files")


def migrate_docs_developers(project_root: Path):
    """Migrate docs/developers to docs/roles"""
    dev_dir = project_root / "docs" / "developers"
    role_dir = project_root / "docs" / "roles"

    if not dev_dir.exists():
        print(f"  No docs/developers directory found, skipping")
        return

    # Create roles directory if not exists
    role_dir.mkdir(parents=True, exist_ok=True)

    migrated_count = 0
    for dev_subdir in dev_dir.iterdir():
        if dev_subdir.is_dir():
            role_name = dev_subdir.name
            role_subdir = role_dir / role_name

            # Copy directory
            import shutil

            if role_subdir.exists():
                shutil.rmtree(role_subdir)
            shutil.copytree(dev_subdir, role_subdir)
            migrated_count += 1

            # Update metadata files
            for meta_file in role_subdir.glob(".metadata.yaml"):
                try:
                    import yaml

                    with open(meta_file, "r", encoding="utf-8") as f:
                        meta = yaml.safe_load(f) or {}

                    # Update fields
                    if "developer" in meta:
                        meta["role"] = meta.pop("developer")

                    with open(meta_file, "w", encoding="utf-8") as f:
                        yaml.dump(meta, f, allow_unicode=True)
                except Exception as e:
                    print(f"  Warning: Failed to update {meta_file}: {e}")

    print(f"  Migrated {migrated_count} role directories")
    print(f"  Note: Original docs/developers preserved. Remove manually after verification.")


def update_project_yaml(project_root: Path):
    """Update project.yaml configuration"""
    config_file = project_root / "project.yaml"
    if not config_file.exists():
        print(f"  No project.yaml found, skipping")
        return

    try:
        import yaml

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}

        # Check if already migrated
        if "role_context" in config:
            print(f"  project.yaml already has role_context, skipping")
            return

        # Migrate multi_developer → role_context
        if "multi_developer" in config:
            multi_dev = config.pop("multi_developer")

            role_context = {
                "enabled": multi_dev.get("enabled", True),
                "current_role": "dev",  # Default role
                "identity_source": "manual",
            }

            # Migrate context settings
            if "context" in multi_dev:
                ctx = multi_dev["context"]
                role_context["context"] = {
                    "per_role_dir": ctx.get("per_developer_dir", "docs/roles").replace(
                        "developers", "roles"
                    ),
                    "global_aggregation": ctx.get("global_aggregation", True),
                    "aggregation_file": ctx.get("aggregation_file", "docs/CONTEXT.md"),
                    "metadata_file": ctx.get("metadata_file", ".metadata.yaml"),
                    "auto_sync": ctx.get("auto_sync", True),
                }

            # Migrate collaboration settings
            if "collaboration" in multi_dev:
                collab = multi_dev["collaboration"]
                role_context["collaboration"] = {
                    "enabled": collab.get("enabled", True),
                    "file": collab.get("file", "docs/roles/COLLABORATION.md").replace(
                        "developers", "roles"
                    ),
                    "track_dependencies": collab.get("track_dependencies", True),
                    "track_handoffs": collab.get("track_handoffs", True),
                }

            # Migrate dialogue protocol
            if "dialogue_protocol" in multi_dev:
                dp = multi_dev["dialogue_protocol"]
                role_context["dialogue_protocol"] = dp
                # Update paths in dialogue protocol
                for key in ["read_files", "update_files"]:
                    if key in dp:
                        dp[key] = [p.replace("developers", "roles") for p in dp[key]]

            # Create default role assignments
            role_context["role_assignments"] = [
                {
                    "role": "dev",
                    "description": "Core development work",
                    "insights": [],
                    "preferences": {},
                }
            ]

            config["role_context"] = role_context

            # Write updated config
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.dump(config, f, allow_unicode=True, sort_keys=False)

            print(f"  Migrated multi_developer → role_context")
        else:
            print(f"  No multi_developer config found, adding default role_context")
            config["role_context"] = {
                "enabled": True,
                "current_role": "dev",
                "role_assignments": [
                    {
                        "role": "dev",
                        "description": "Core development work",
                        "insights": [],
                        "preferences": {},
                    }
                ],
            }
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.dump(config, f, allow_unicode=True, sort_keys=False)

    except Exception as e:
        print(f"  Error updating project.yaml: {e}")


def main():
    """Main migration function"""
    project_path = sys.argv[1] if len(sys.argv) > 1 else "."
    project_root = Path(project_path).resolve()

    print(f"Migrating project: {project_root}")
    print(f"Started at: {datetime.now().isoformat()}")
    print()

    # Run migrations
    print("1. Migrating events.jsonl...")
    migrate_events_jsonl(project_root)
    print()

    print("2. Migrating session files...")
    migrate_session_files(project_root)
    print()

    print("3. Migrating docs/developers → docs/roles...")
    migrate_docs_developers(project_root)
    print()

    print("4. Updating project.yaml...")
    update_project_yaml(project_root)
    print()

    print(f"Migration completed at: {datetime.now().isoformat()}")
    print()
    print("Next steps:")
    print("  1. Review migrated data in docs/roles/")
    print("  2. Run 'vibecollab role whoami' to verify")
    print("  3. Run 'pytest' to verify all tests pass")
    print("  4. Remove docs/developers/ manually after verification")
    print()
    print("Note: Backup files created with .bak extension")


if __name__ == "__main__":
    main()
