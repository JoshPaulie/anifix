"""TVDB scraping functionality for generating spec files."""

import re
import sys
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup

    SCRAPING_AVAILABLE = True
except ImportError:
    SCRAPING_AVAILABLE = False


def check_scraping_dependencies() -> None:
    """Check if scraping dependencies are available and provide helpful error message."""
    if not SCRAPING_AVAILABLE:
        print("Error: Scraping feature requires additional dependencies.")
        print("Install them with:")
        print("  uv sync --group scraping")
        print("Or if using pip:")
        print("  pip install beautifulsoup4 requests")
        sys.exit(1)


def extract_series_id_from_url(url: str) -> str:
    """Extract series ID from TVDB URL."""
    # Handle various TVDB URL formats:
    # https://www.thetvdb.com/series/the-sandman
    # https://thetvdb.com/series/the-sandman/
    # https://www.thetvdb.com/series/the-sandman/seasons/official/1

    patterns = [
        r"thetvdb\.com/series/([^/]+)",
        r"thetvdb\.com/deriving/series/(\d+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    msg = f"Could not extract series ID from URL: {url}"
    raise ValueError(msg)


def scrape_tvdb_seasons(series_url: str) -> list[tuple[int, int]]:
    """
    Scrape TVDB series page to extract season and episode count information.

    Args:
        series_url: TVDB series URL

    Returns:
        List of tuples (season_number, episode_count) for regular seasons

    """
    check_scraping_dependencies()

    try:
        # Ensure we're getting the main series page (not a specific season)
        series_id = extract_series_id_from_url(series_url)
        main_url = f"https://www.thetvdb.com/series/{series_id}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        }

        response = requests.get(main_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        return _parse_seasons_table(soup)

    except requests.RequestException as e:
        msg = f"Failed to fetch TVDB page: {e}"
        raise ValueError(msg) from e
    except Exception as e:
        msg = f"Error parsing TVDB page: {e}"
        raise ValueError(msg) from e


def _parse_seasons_table(soup) -> list[tuple[int, int]]:  # type: ignore[misc]
    """Parse the seasons table from TVDB page soup."""
    # Find the seasons table
    table = soup.find("table", class_=["table", "table-bordered"])
    if not table:
        msg = "Could not find seasons table on TVDB page"
        raise ValueError(msg)

    seasons_data: list[tuple[int, int]] = []
    tbody = table.find("tbody")
    if not tbody:
        return seasons_data

    rows = tbody.find_all("tr")
    minimum_cells = 4

    for row in rows:
        cells = row.find_all("td")
        if len(cells) < minimum_cells:
            continue

        season_data = _extract_season_from_row(cells)
        if season_data:
            seasons_data.append(season_data)

    if not seasons_data:
        msg = "No valid seasons found on TVDB page"
        raise ValueError(msg)

    # Sort by season number
    seasons_data.sort(key=lambda x: x[0])
    return seasons_data


def _extract_season_from_row(cells) -> tuple[int, int] | None:  # type: ignore[misc]
    """Extract season number and episode count from table row cells."""
    # Get season info from the first cell
    season_cell = cells[0]
    season_link = season_cell.find("a")

    if not season_link:
        return None

    season_text = season_link.get_text(strip=True)

    # Skip non-season rows (All Seasons, Specials, Unassigned)
    if not season_text.startswith("Season "):
        return None

    # Extract season number
    season_match = re.search(r"Season (\d+)", season_text)
    if not season_match:
        return None

    season_num = int(season_match.group(1))

    # Get episode count from the fourth cell
    episode_count_text = cells[3].get_text(strip=True)
    if not episode_count_text.isdigit():
        return None

    episode_count = int(episode_count_text)

    # Skip seasons with 0 episodes
    if episode_count > 0:
        return (season_num, episode_count)

    return None


def generate_spec_from_tvdb(series_url: str, output_path: Path | None = None) -> str:
    """
    Generate a spec file from TVDB series information.

    Args:
        series_url: TVDB series URL
        output_path: Optional path to write the spec file

    Returns:
        The generated spec file content as a string

    """
    seasons_data = scrape_tvdb_seasons(series_url)

    # Generate spec content
    lines = ["# Season | Episode range"]

    current_episode = 1
    for season_num, episode_count in seasons_data:
        end_episode = current_episode + episode_count - 1
        lines.append(f"{season_num} | {current_episode}-{end_episode}")
        current_episode = end_episode + 1

    spec_content = "\n".join(lines) + "\n"

    # Write to file if path provided
    if output_path:
        output_path.write_text(spec_content)
        print(f"Generated spec file: {output_path}")

    return spec_content


def generate_season_map_from_tvdb(series_url: str) -> dict[int, tuple[int, int]]:
    """
    Generate a season map directly from TVDB series information for in-memory use.

    Args:
        series_url: TVDB series URL

    Returns:
        Dictionary mapping season numbers to (start_episode, end_episode) tuples

    """
    seasons_data = scrape_tvdb_seasons(series_url)
    season_map: dict[int, tuple[int, int]] = {}

    current_episode = 1
    for season_num, episode_count in seasons_data:
        end_episode = current_episode + episode_count - 1
        season_map[season_num] = (current_episode, end_episode)
        current_episode = end_episode + 1

    return season_map


def print_tvdb_info(series_url: str) -> None:
    """Print information about TVDB series without generating a file."""
    try:
        seasons_data = scrape_tvdb_seasons(series_url)
        series_id = extract_series_id_from_url(series_url)

        print(f"TVDB Series: {series_id}")
        print(f"Found {len(seasons_data)} season(s):")

        current_episode = 1
        for season_num, episode_count in seasons_data:
            end_episode = current_episode + episode_count - 1
            print(
                f"  Season {season_num}: {episode_count} episodes (would map to episodes {current_episode}-{end_episode})",
            )
            current_episode = end_episode + 1

    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
