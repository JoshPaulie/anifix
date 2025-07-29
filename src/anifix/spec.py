"""Spec file parsing and validation for anifix."""

from pathlib import Path


def validate_season_map(season_map: dict[int, tuple[int, int]]) -> None:
    """
    Validate the season mapping for conflicts and invalid ranges.

    Raises:
        ValueError: If validation fails with detailed error message

    """
    if not season_map:
        msg = "No valid season mappings found in spec file"
        raise ValueError(msg)

    # Check for invalid ranges (end < start)
    for season, (start, end) in season_map.items():
        if end < start:
            msg = f"Invalid episode range for season {season}: {start}-{end} (end cannot be less than start)"
            raise ValueError(msg)

    # Check for overlapping episode ranges between seasons
    all_episodes: dict[int, int] = {}  # episode_num -> season_num

    for season, (start, end) in season_map.items():
        for episode in range(start, end + 1):
            if episode in all_episodes:
                existing_season = all_episodes[episode]
                msg = (
                    f"Episode {episode} appears in multiple seasons: "
                    f"season {existing_season} and season {season}. "
                    f"Each episode can only belong to one season."
                )
                raise ValueError(msg)
            all_episodes[episode] = season


def _parse_episode_range(
    range_part: str,
    season: int,
    line_number: int,
) -> tuple[int, int]:
    """Parse episode range from spec file line."""
    if not range_part:
        msg = f"Line {line_number}: Empty episode range for season {season}"
        raise ValueError(msg)

    if "-" in range_part:
        parts = range_part.split("-", 1)
        expected_parts = 2
        if len(parts) != expected_parts or not parts[0].strip() or not parts[1].strip():
            msg = f"Line {line_number}: Invalid episode range format: {range_part}"
            raise ValueError(msg)
        return int(parts[0].strip()), int(parts[1].strip())

    # Single episode
    episode = int(range_part)
    return episode, episode


def _parse_spec_line(line: str, line_number: int) -> tuple[int, tuple[int, int]]:
    """Parse a single line from the spec file."""
    if "|" not in line:
        msg = f"Line {line_number}: Invalid format. Expected 'season | episode_range' but got: {line}"
        raise ValueError(msg)

    season_part, range_part = line.split("|", 1)
    season = int(season_part.strip())
    range_part = range_part.strip()

    start, end = _parse_episode_range(range_part, season, line_number)
    return season, (start, end)


def parse_spec_file(spec_path: Path) -> dict[int, tuple[int, int]]:
    """
    Parse the anifix.spec file and return season mapping.

    Returns:
        Dict mapping season number to (start_episode, end_episode) tuple

    Raises:
        ValueError: If spec file contains invalid data
        FileNotFoundError: If spec file doesn't exist

    """
    season_map = {}
    line_number = 0
    duplicate_seasons = []

    try:
        with spec_path.open() as f:
            for line_content in f:
                line_number += 1
                line = line_content.strip()
                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue

                try:
                    season, episode_range = _parse_spec_line(line, line_number)

                    # Check for duplicate season definitions
                    if season in season_map:
                        duplicate_seasons.append(season)

                    season_map[season] = episode_range

                except ValueError as e:
                    if "invalid literal" in str(e):
                        msg = f"Line {line_number}: Invalid number in line: {line}"
                        raise ValueError(msg) from e
                    raise

    except FileNotFoundError as e:
        msg = f"Spec file not found at {spec_path}"
        raise FileNotFoundError(msg) from e

    # Warn about duplicate seasons but don't fail (last definition wins)
    if duplicate_seasons:
        seasons_str = ", ".join(map(str, duplicate_seasons))
        print(
            f"Warning: Duplicate season definitions found: {seasons_str}. Using last definition for each.",
        )

    # Validate the final season map
    validate_season_map(season_map)

    return season_map
