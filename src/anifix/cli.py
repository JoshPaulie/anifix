"""Command-line interface and argument parsing for anifix."""

import argparse
import sys
from pathlib import Path


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Rename anime episode files to Jellyfin-compatible format",
        epilog="""
Examples:
  %(prog)s                    # Process current directory with default spec file
  %(prog)s -d /path/to/anime  # Process specific directory
  %(prog)s -s custom.spec     # Use custom spec file
  %(prog)s --dry-run          # Preview changes without renaming files
  %(prog)s --restore          # Restore files to original names
  %(prog)s --url-spec "https://www.thetvdb.com/series/the-sandman" -d /path/to/anime  # Use TVDB data directly
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-d",
        "--directory",
        type=Path,
        default=Path.cwd(),
        help="Directory containing episode files (default: current directory)",
    )

    parser.add_argument(
        "-s",
        "--spec-file",
        type=Path,
        help="Path to spec file (default: search for anifix.spec, .anifix, or anifix in directory)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without actually renaming files",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    parser.add_argument(
        "--restore",
        action="store_true",
        help="Restore files to their original names using backup data",
    )

    parser.add_argument(
        "--url-spec",
        metavar="TVDB_URL",
        help="Use TVDB series URL to generate spec data in-memory (requires scraping dependencies)",
    )

    return parser


def validate_directory(directory: Path) -> None:
    """Validate that the provided directory exists and is actually a directory."""
    if not directory.exists():
        print(f"Error: Directory '{directory}' does not exist")
        sys.exit(1)
    if not directory.is_dir():
        print(f"Error: '{directory}' is not a directory")
        sys.exit(1)


def find_spec_file(directory: Path, spec_file_arg: Path | None) -> Path:
    """Find the spec file to use, either from argument or by searching."""
    if spec_file_arg:
        spec_file = spec_file_arg.resolve()
        if not spec_file.exists():
            print(f"Error: Spec file '{spec_file}' not found")
            sys.exit(1)
        return spec_file

    # Try different spec file names in order of preference
    spec_filenames = ["anifix.spec", ".anifix", "anifix"]
    for filename in spec_filenames:
        candidate = directory / filename
        if candidate.exists():
            return candidate

    print("Error: No spec file found in target directory")
    print("Create a spec file with one of these names:")
    print("  - anifix.spec")
    print("  - .anifix")
    print("  - anifix")
    print("With the format:")
    print("# Season | Episode range")
    print("1 | 1-12")
    print("2 | 13-24")
    sys.exit(1)


def print_verbose_info(
    working_dir: Path,
    spec_file: Path,
    season_map: dict[int, tuple[int, int]],
) -> None:
    """Print verbose information about the operation."""
    print(f"Working directory: {working_dir}")
    print(f"Using spec file: {spec_file}")
    print(f"Found {len(season_map)} season(s) in spec file")
    for season, (start, end) in season_map.items():
        print(f"  Season {season}: Episodes {start}-{end}")
