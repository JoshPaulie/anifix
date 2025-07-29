"""File renaming functionality for anifix."""

from pathlib import Path

from anifix.backup import load_backup_file, save_backup_file, update_backup_data
from anifix.episode import (
    extract_episode_title,
    find_season_for_episode,
    format_episode_name,
    get_episode_number_from_filename,
)

VIDEO_EXTENSIONS = {".mkv", ".mp4", ".avi", ".mov", ".m4v", ".wmv"}


def should_process_file(file_path: Path) -> bool:
    """Check if a file should be processed for renaming."""
    return file_path.is_file() and file_path.suffix.lower() in VIDEO_EXTENSIONS


def rename_episode_files(
    directory: Path,
    season_map: dict[int, tuple[int, int]],
    *,
    dry_run: bool = False,
) -> None:
    """Rename episode files in the directory according to the season mapping."""
    # Load existing backup data
    backup_data = load_backup_file(directory) if not dry_run else {}
    backup_updated = False

    for file_path in directory.iterdir():
        if not should_process_file(file_path):
            continue

        try:
            # Extract episode number from current filename
            episode_num = get_episode_number_from_filename(file_path.name)

            # Find which season this episode belongs to
            season, episode_in_season = find_season_for_episode(
                episode_num,
                season_map,
            )

            # Extract the title part
            title = extract_episode_title(file_path.name)

            # Create new filename: S01E01 - Title.ext
            new_name = format_episode_name(season, episode_in_season, title)
            new_path = file_path.parent / new_name

            # Skip if the file is already renamed to the target format
            if file_path.name == new_name:
                continue

            # Rename the file or show preview
            if dry_run:
                print(f"Would rename: {file_path.name} -> {new_name}")
            else:
                print(f"Renaming: {file_path.name} -> {new_name}")

                # Update backup data if this is not a dry run
                if new_name not in backup_data:
                    update_backup_data(backup_data, file_path.name, new_name)
                    backup_updated = True

                file_path.rename(new_path)

        except (ValueError, FileExistsError) as e:
            print(f"Warning: Could not process {file_path.name}: {e}")
            continue

    # Save backup data if it was updated
    if backup_updated and not dry_run:
        save_backup_file(directory, backup_data)
