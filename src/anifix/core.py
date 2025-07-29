"""Main entry point and orchestration for anifix - anime episode file renaming tool."""

import argparse
import sys

from anifix.backup import restore_files
from anifix.cli import (
    create_argument_parser,
    find_spec_file,
    print_verbose_info,
    validate_directory,
)
from anifix.renamer import rename_episode_files
from anifix.spec import parse_spec_file


def handle_url_spec(args: argparse.Namespace) -> dict[int, tuple[int, int]]:
    """Handle in-memory spec generation from TVDB URL."""
    from anifix.tvdb import generate_season_map_from_tvdb  # noqa: PLC0415

    return generate_season_map_from_tvdb(args.url_spec)


def main() -> None:
    """Run the anifix tool."""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Validate working directory
    working_dir = args.directory.resolve()
    validate_directory(working_dir)

    # Handle restore mode
    if args.restore:
        restore_files(working_dir)
        return

    try:
        # Handle URL spec mode (scrape and use in-memory)
        if args.url_spec:
            season_map = handle_url_spec(args)
            spec_source = f"TVDB URL: {args.url_spec}"
        else:
            # Find and parse spec file (normal operation)
            spec_file = find_spec_file(working_dir, args.spec_file)
            season_map = parse_spec_file(spec_file)
            spec_source = f"spec file: {spec_file.name}"

        # Print information based on verbosity settings
        if args.verbose:
            if args.url_spec:
                print(f"Working directory: {working_dir}")
                print(f"Using TVDB URL: {args.url_spec}")
                print(f"Found {len(season_map)} season(s)")
                for season, (start, end) in season_map.items():
                    print(f"  Season {season}: Episodes {start}-{end}")
            else:
                print_verbose_info(working_dir, spec_file, season_map)
        elif not args.dry_run:
            print(f"Using {spec_source}")

        # Show dry run notice if needed
        if args.dry_run:
            print("DRY RUN - No files will be renamed")
            print()

        # Rename files (or preview if dry run)
        rename_episode_files(working_dir, season_map, dry_run=args.dry_run)

        if not args.dry_run:
            print("Done!")

    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}")
        sys.exit(1)
