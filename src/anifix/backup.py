"""Backup and restore functionality for anifix."""

import json
from pathlib import Path


def load_backup_file(directory: Path) -> dict[str, str]:
    """Load the backup file mapping current names to original names."""
    backup_file = directory / ".anifix-backup.json"
    if not backup_file.exists():
        return {}

    try:
        with backup_file.open() as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Warning: Could not read backup file: {e}")
        return {}


def save_backup_file(directory: Path, backup_data: dict[str, str]) -> None:
    """Save the backup file mapping current names to original names."""
    backup_file = directory / ".anifix-backup.json"
    try:
        with backup_file.open("w") as f:
            json.dump(backup_data, f, indent=2)
    except OSError as e:
        print(f"Warning: Could not save backup file: {e}")


def update_backup_data(
    backup_data: dict[str, str],
    old_name: str,
    new_name: str,
) -> None:
    """Update backup data when renaming a file."""
    # Check if this file was already renamed before
    original_name = old_name
    for current, orig in list(backup_data.items()):
        if current == old_name:
            # This file was already renamed, use its original name
            original_name = orig
            del backup_data[current]
            break

    # Store the mapping from new name to original name
    backup_data[new_name] = original_name


def restore_files(directory: Path) -> None:
    """Restore files to their original names using the backup file."""
    backup_data = load_backup_file(directory)

    if not backup_data:
        print("No backup file found or backup file is empty")
        print("Files can only be restored if they were renamed using anifix")
        return

    restored_count = 0
    failed_count = 0

    for current_name, original_name in backup_data.items():
        current_path = directory / current_name
        original_path = directory / original_name

        if not current_path.exists():
            print(f"Warning: File '{current_name}' not found, skipping")
            failed_count += 1
            continue

        if original_path.exists() and original_path != current_path:
            print(
                f"Warning: Target '{original_name}' already exists, skipping '{current_name}'",
            )
            failed_count += 1
            continue

        try:
            print(f"Restoring: {current_name} -> {original_name}")
            current_path.rename(original_path)
            restored_count += 1
        except OSError as e:
            print(f"Error restoring '{current_name}': {e}")
            failed_count += 1

    if restored_count > 0:
        # Remove the backup file after successful restoration
        backup_file = directory / ".anifix-backup.json"
        try:
            backup_file.unlink()
            print(f"\nRestored {restored_count} files and removed backup file")
        except OSError:
            print(f"\nRestored {restored_count} files (backup file removal failed)")

    if failed_count > 0:
        print(f"Failed to restore {failed_count} files")
