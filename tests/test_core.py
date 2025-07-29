"""Tests for anifix core functionality."""

import json
from pathlib import Path

import pytest

from anifix.backup import load_backup_file, restore_files, save_backup_file
from anifix.cli import find_spec_file, validate_directory
from anifix.episode import find_season_for_episode, get_episode_number_from_filename
from anifix.renamer import rename_episode_files
from anifix.spec import parse_spec_file


class TestParseSpecFile:
    """Tests for parse_spec_file function."""

    def test_parse_valid_spec_file(self, sample_spec_file: Path) -> None:
        """Test parsing a valid spec file."""
        result = parse_spec_file(sample_spec_file)

        expected = {
            1: (1, 4),
            2: (5, 7),
            3: (8, 10),
        }
        assert result == expected

    def test_parse_spec_file_with_single_episode(self, temp_dir: Path) -> None:
        """Test parsing spec file with single episode seasons."""
        spec_content = """# Season | Episode range
1 | 5
2 | 10"""
        spec_file = temp_dir / "anifix.spec"
        spec_file.write_text(spec_content)

        result = parse_spec_file(spec_file)
        expected = {1: (5, 5), 2: (10, 10)}
        assert result == expected

    def test_parse_spec_file_with_comments_and_empty_lines(
        self, temp_dir: Path
    ) -> None:
        """Test parsing spec file with comments and empty lines."""
        spec_content = """# This is a comment
# Another comment

1 | 1-5

# More comments
2 | 6-10

"""
        spec_file = temp_dir / "anifix.spec"
        spec_file.write_text(spec_content)

        result = parse_spec_file(spec_file)
        expected = {1: (1, 5), 2: (6, 10)}
        assert result == expected

    def test_parse_nonexistent_spec_file(self, temp_dir: Path) -> None:
        """Test parsing a nonexistent spec file."""
        nonexistent_file = temp_dir / "nonexistent.spec"

        with pytest.raises(FileNotFoundError, match="Spec file not found"):
            parse_spec_file(nonexistent_file)

    def test_parse_invalid_spec_file(self, temp_dir: Path) -> None:
        """Test parsing an invalid spec file."""
        spec_content = "invalid content without proper format"
        spec_file = temp_dir / "anifix.spec"
        spec_file.write_text(spec_content)

        with pytest.raises(
            ValueError, match="Invalid format. Expected 'season \\| episode_range'"
        ):
            parse_spec_file(spec_file)


class TestGetEpisodeNumberFromFilename:
    """Tests for get_episode_number_from_filename function."""

    def test_extract_episode_number_standard_format(self) -> None:
        """Test extracting episode number from standard format."""
        filename = "Episode 5 - Great Episode Title.mkv"
        result = get_episode_number_from_filename(filename)
        assert result == 5

    def test_extract_episode_number_case_insensitive(self) -> None:
        """Test case insensitive episode number extraction."""
        filename = "episode 12 - Another Title.mp4"
        result = get_episode_number_from_filename(filename)
        assert result == 12

    def test_extract_episode_number_fallback(self) -> None:
        """Test fallback episode number extraction."""
        filename = "7 - Simple Title.avi"
        result = get_episode_number_from_filename(filename)
        assert result == 7

    def test_extract_episode_number_no_match(self) -> None:
        """Test extraction when no episode number is found."""
        filename = "No Episode Number Here.mkv"

        with pytest.raises(ValueError, match="Could not extract episode number"):
            get_episode_number_from_filename(filename)


class TestFindSeasonForEpisode:
    """Tests for find_season_for_episode function."""

    def test_find_season_for_episode_valid(self) -> None:
        """Test finding season for valid episode numbers."""
        season_map = {1: (1, 4), 2: (5, 7), 3: (8, 10)}

        # Test various episodes
        assert find_season_for_episode(1, season_map) == (1, 1)
        assert find_season_for_episode(4, season_map) == (1, 4)
        assert find_season_for_episode(5, season_map) == (2, 1)
        assert find_season_for_episode(7, season_map) == (2, 3)
        assert find_season_for_episode(8, season_map) == (3, 1)
        assert find_season_for_episode(10, season_map) == (3, 3)

    def test_find_season_for_episode_invalid(self) -> None:
        """Test finding season for invalid episode number."""
        season_map = {1: (1, 4), 2: (5, 7)}

        with pytest.raises(ValueError, match="Episode 15 not found in any season"):
            find_season_for_episode(15, season_map)


class TestBackupFunctions:
    """Tests for backup file functions."""

    def test_load_backup_file_exists(
        self, backup_file: Path, sample_backup_data: dict[str, str]
    ) -> None:
        """Test loading an existing backup file."""
        result = load_backup_file(backup_file.parent)
        assert result == sample_backup_data

    def test_load_backup_file_not_exists(self, temp_dir: Path) -> None:
        """Test loading backup file when it doesn't exist."""
        result = load_backup_file(temp_dir)
        assert result == {}

    def test_load_backup_file_invalid_json(self, temp_dir: Path) -> None:
        """Test loading backup file with invalid JSON."""
        backup_file = temp_dir / ".anifix-backup.json"
        backup_file.write_text("invalid json content")

        result = load_backup_file(temp_dir)
        assert result == {}

    def test_save_backup_file(self, temp_dir: Path) -> None:
        """Test saving backup file."""
        backup_data = {"new_name.mkv": "old_name.mkv"}
        save_backup_file(temp_dir, backup_data)

        backup_file = temp_dir / ".anifix-backup.json"
        assert backup_file.exists()

        with backup_file.open() as f:
            saved_data = json.load(f)
        assert saved_data == backup_data


class TestRestoreFiles:
    """Tests for restore_files function."""

    def test_restore_files_success(
        self, temp_dir: Path, sample_backup_data: dict[str, str]
    ) -> None:
        """Test successful file restoration."""
        # Create backup file
        backup_file = temp_dir / ".anifix-backup.json"
        with backup_file.open("w") as f:
            json.dump(sample_backup_data, f)

        # Create renamed files
        for current_name in sample_backup_data:
            file_path = temp_dir / current_name
            file_path.write_text("content")

        # Test restoration
        restore_files(temp_dir)

        # Check that original files exist
        for original_name in sample_backup_data.values():
            assert (temp_dir / original_name).exists()

        # Check that backup file is removed
        assert not backup_file.exists()

    def test_restore_files_no_backup(self, temp_dir: Path) -> None:
        """Test restoration when no backup file exists."""
        restore_files(temp_dir)  # Should not raise an error

    def test_restore_files_missing_current_file(
        self, temp_dir: Path, sample_backup_data: dict[str, str]
    ) -> None:
        """Test restoration when current file is missing."""
        # Create backup file
        backup_file = temp_dir / ".anifix-backup.json"
        with backup_file.open("w") as f:
            json.dump(sample_backup_data, f)

        # Don't create the renamed files
        restore_files(temp_dir)


class TestRenameEpisodeFiles:
    """Tests for rename_episode_files function."""

    def test_rename_episode_files_success(
        self, temp_dir: Path, sample_episode_files: list[Path]
    ) -> None:
        """Test successful episode file renaming."""
        season_map = {1: (1, 4), 2: (5, 7), 3: (8, 10)}

        rename_episode_files(temp_dir, season_map)

        # Check that files were renamed correctly
        expected_names = [
            "S01E01 - My First Episode.mkv",
            "S01E02 - My Second Episode.mkv",
            "S01E03 - My Third Episode.mkv",
            "S01E04 - My Fourth Episode.mkv",
            "S02E01 - My Fifth Episode.mkv",
            "S02E02 - My Sixth Episode.mkv",
            "S02E03 - My Seventh Episode.mkv",
            "S03E01 - My Eighth Episode.mkv",
            "S03E02 - My Ninth Episode.mkv",
            "S03E03 - My Tenth Episode.mkv",
        ]

        for name in expected_names:
            assert (temp_dir / name).exists()

        # Check that backup file was created
        backup_file = temp_dir / ".anifix-backup.json"
        assert backup_file.exists()

    def test_rename_episode_files_dry_run(
        self, temp_dir: Path, sample_episode_files: list[Path]
    ) -> None:
        """Test dry run mode doesn't rename files."""
        season_map = {1: (1, 4), 2: (5, 7), 3: (8, 10)}

        rename_episode_files(temp_dir, season_map, dry_run=True)

        # Check that original files still exist
        for file_path in sample_episode_files:
            assert file_path.exists()

        # Check that backup file was not created
        backup_file = temp_dir / ".anifix-backup.json"
        assert not backup_file.exists()

    def test_rename_episode_files_already_renamed(self, temp_dir: Path) -> None:
        """Test renaming files that are already in the correct format."""
        # Create already renamed file
        renamed_file = temp_dir / "S01E01 - My Episode.mkv"
        renamed_file.write_text("content")

        season_map = {1: (1, 4)}

        rename_episode_files(temp_dir, season_map)

        # File should still exist and not be renamed again
        assert renamed_file.exists()


class TestFindSpecFile:
    """Tests for find_spec_file function."""

    def test_find_spec_file_with_argument(self, sample_spec_file: Path) -> None:
        """Test finding spec file when provided as argument."""
        result = find_spec_file(sample_spec_file.parent, sample_spec_file)
        assert result.resolve() == sample_spec_file.resolve()

    def test_find_spec_file_search_priority(self, temp_dir: Path) -> None:
        """Test spec file search priority."""
        # Create multiple spec files
        spec1 = temp_dir / "anifix"
        spec2 = temp_dir / ".anifix"
        spec3 = temp_dir / "anifix.spec"

        spec1.write_text("1 | 1-5")
        spec2.write_text("1 | 1-5")
        spec3.write_text("1 | 1-5")

        # Should find anifix.spec first (highest priority)
        result = find_spec_file(temp_dir, None)
        assert result == spec3

    def test_find_spec_file_not_found(self, temp_dir: Path) -> None:
        """Test when no spec file is found."""
        with pytest.raises(SystemExit):
            find_spec_file(temp_dir, None)

    def test_find_spec_file_argument_not_exists(self, temp_dir: Path) -> None:
        """Test when provided spec file doesn't exist."""
        nonexistent = temp_dir / "nonexistent.spec"

        with pytest.raises(SystemExit):
            find_spec_file(temp_dir, nonexistent)


class TestIntegration:
    """Integration tests for the full workflow."""

    def test_full_rename_and_restore_workflow(
        self, temp_dir: Path, sample_episode_files: list[Path]
    ) -> None:
        """Test complete rename and restore workflow."""
        # Create spec file
        spec_content = "1 | 1-10"
        spec_file = temp_dir / "anifix.spec"
        spec_file.write_text(spec_content)

        season_map = parse_spec_file(spec_file)

        # Store original filenames
        original_names = [f.name for f in sample_episode_files]

        # Rename files
        rename_episode_files(temp_dir, season_map)

        # Check files were renamed
        for original_name in original_names:
            assert not (temp_dir / original_name).exists()

        # Restore files
        restore_files(temp_dir)

        # Check files were restored
        for original_name in original_names:
            assert (temp_dir / original_name).exists()

        # Check backup file was removed
        backup_file = temp_dir / ".anifix-backup.json"
        assert not backup_file.exists()

    @pytest.mark.slow
    def test_multiple_rename_cycles(
        self, temp_dir: Path, sample_episode_files: list[Path]
    ) -> None:
        """Test multiple rename cycles maintain backup integrity."""
        # Create spec file
        spec_content = "1 | 1-10"
        spec_file = temp_dir / "anifix.spec"
        spec_file.write_text(spec_content)

        season_map = parse_spec_file(spec_file)
        original_names = [f.name for f in sample_episode_files]

        # First rename
        rename_episode_files(temp_dir, season_map)

        # Modify spec file for different mapping
        spec_content2 = """1 | 1-5
2 | 6-10"""
        spec_file.write_text(spec_content2)
        season_map2 = parse_spec_file(spec_file)

        # Second rename
        rename_episode_files(temp_dir, season_map2)

        # Restore should still work
        restore_files(temp_dir)

        # Check all original files are restored
        for original_name in original_names:
            assert (temp_dir / original_name).exists()
