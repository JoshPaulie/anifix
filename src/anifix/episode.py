"""Episode number extraction and season mapping for anifix."""

import re


def get_episode_number_from_filename(filename: str) -> int:
    """Extract episode number from filename like 'Episode 1 - Title.mkv'."""
    match = re.match(r"Episode\s+(\d+)", filename, re.IGNORECASE)
    if match:
        return int(match.group(1))

    # Fallback: look for any number at the start
    match = re.match(r"(\d+)", filename)
    if match:
        return int(match.group(1))

    msg = f"Could not extract episode number from: {filename}"
    raise ValueError(msg)


def find_season_for_episode(
    episode_num: int,
    season_map: dict[int, tuple[int, int]],
) -> tuple[int, int]:
    """
    Find which season an episode belongs to and its episode number within that season.

    Returns:
        Tuple of (season_number, episode_in_season)

    """
    for season, (start, end) in season_map.items():
        if start <= episode_num <= end:
            episode_in_season = episode_num - start + 1
            return season, episode_in_season

    msg = f"Episode {episode_num} not found in any season"
    raise ValueError(msg)


def extract_episode_title(filename: str) -> str:
    """Extract the title part from an episode filename."""
    # Extract the title part (everything after "Episode X - ")
    title_match = re.match(
        r"Episode\s+\d+\s*-\s*(.+)",
        filename,
        re.IGNORECASE,
    )
    if title_match:
        return title_match.group(1)

    # Fallback: use everything after the episode number
    title_match = re.match(r"\d+\s*-?\s*(.+)", filename)
    if title_match:
        return title_match.group(1)

    # Last resort: use the filename stem
    return filename.rsplit(".", 1)[0] if "." in filename else filename


def format_episode_name(season: int, episode_in_season: int, title: str) -> str:
    """Format episode name in Jellyfin-compatible format: S01E01 - Title."""
    return f"S{season:02d}E{episode_in_season:02d} - {title}"
