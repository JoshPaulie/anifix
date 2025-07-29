"""Tests for edge cases and error handling in anifix."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from anifix.backup import load_backup_file, save_backup_file
from anifix.cli import validate_directory
from anifix.episode import find_season_for_episode, get_episode_number_from_filename
from anifix.renamer import rename_episode_files
from anifix.spec import parse_spec_file


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_parse_spec_file_malformed_lines(self, temp_dir: Path) -> None:
        """Test parsing spec file with malformed lines."""
        spec_content = """# Valid line
1 | 1-5
# Invalid lines below
invalid line without pipe
2 | invalid-range
3 | 
| 5-10
4 | 8-abc"""

        spec_file = temp_dir / "anifix.spec"
        spec_file.write_text(spec_content)

        # Should now throw an error on the first malformed line
        with pytest.raises(
            ValueError,
            match="Line 4: Invalid format. Expected 'season \\| episode_range'",
        ):
            parse_spec_file(spec_file)

    def test_episode_filename_with_special_characters(self) -> None:
        """Test episode filename parsing with special characters."""
        filenames = [
            "Episode 1 - Title with (parentheses).mkv",
            "Episode 2 - Title with [brackets].mp4",
            "Episode 3 - Title with & symbols.avi",
            "Episode 4 - Title with ñ accents.mkv",
        ]

        for i, filename in enumerate(filenames, 1):
            result = get_episode_number_from_filename(filename)
            assert result == i

    def test_rename_files_with_existing_target(self, temp_dir: Path) -> None:
        """Test renaming when target file already exists."""
        # Create original file
        original = temp_dir / "Episode 1 - Title.mkv"
        original.write_text("original content")

        # Create file with target name
        target = temp_dir / "S01E01 - Title.mkv"
        target.write_text("existing content")

        season_map = {1: (1, 5)}

        # This should rename the original file, overwriting the target
        rename_episode_files(temp_dir, season_map)

        # Original file should no longer exist, target should exist with new content
        assert not original.exists()
        assert target.exists()
        # The target file content should be from the original file (it was overwritten)
        assert target.read_text() == "original content"

    def test_backup_file_corruption_handling(self, temp_dir: Path) -> None:
        """Test handling of corrupted backup files."""
        # Create corrupted backup file
        backup_file = temp_dir / ".anifix-backup.json"
        backup_file.write_text("{ invalid json content")

        # Should return empty dict and not crash
        result = load_backup_file(temp_dir)
        assert result == {}

    def test_backup_file_permission_error(self, temp_dir: Path) -> None:
        """Test handling backup file permission errors."""
        backup_data = {"test.mkv": "original.mkv"}

        # Mock open to raise PermissionError
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            # Should not crash, just print warning
            save_backup_file(temp_dir, backup_data)

    def test_empty_directory_processing(self, temp_dir: Path) -> None:
        """Test processing empty directory."""
        season_map = {1: (1, 5)}

        # Should not crash on empty directory
        rename_episode_files(temp_dir, season_map)

        # No backup file should be created
        backup_file = temp_dir / ".anifix-backup.json"
        assert not backup_file.exists()

    def test_directory_with_non_video_files(self, temp_dir: Path) -> None:
        """Test processing directory with non-video files."""
        # Create various file types
        files = [
            "Episode 1 - Title.mkv",  # Video file
            "Episode 2 - Title.txt",  # Text file
            "Episode 3 - Title.jpg",  # Image file
            "README.md",  # Other file
            "anifix.spec",  # Spec file
        ]

        for filename in files:
            (temp_dir / filename).write_text("content")

        season_map = {1: (1, 5)}
        rename_episode_files(temp_dir, season_map)

        # Only video file should be renamed
        assert (temp_dir / "S01E01 - Title.mkv").exists()
        assert (temp_dir / "Episode 2 - Title.txt").exists()  # Unchanged
        assert (temp_dir / "Episode 3 - Title.jpg").exists()  # Unchanged

    def test_season_map_with_gaps(self) -> None:
        """Test season mapping with gaps in episode numbers."""
        season_map = {1: (1, 5), 3: (10, 15)}  # No season 2

        # Episodes in defined ranges should work
        assert find_season_for_episode(3, season_map) == (1, 3)
        assert find_season_for_episode(12, season_map) == (3, 3)

        # Episodes in gaps should raise error
        with pytest.raises(ValueError):
            find_season_for_episode(7, season_map)

    def test_large_episode_numbers(self) -> None:
        """Test handling of large episode numbers."""
        season_map = {1: (100, 200), 2: (1000, 1100)}

        # Should handle large numbers correctly
        assert find_season_for_episode(150, season_map) == (1, 51)
        assert find_season_for_episode(1050, season_map) == (2, 51)

    def test_single_episode_seasons(self) -> None:
        """Test seasons with only one episode."""
        season_map = {1: (1, 1), 2: (5, 5), 3: (10, 10)}

        assert find_season_for_episode(1, season_map) == (1, 1)
        assert find_season_for_episode(5, season_map) == (2, 1)
        assert find_season_for_episode(10, season_map) == (3, 1)


class TestErrorHandling:
    """Tests for error handling and validation."""

    def test_validate_directory_nonexistent(self, temp_dir: Path) -> None:
        """Test validation of nonexistent directory."""
        nonexistent = temp_dir / "nonexistent"

        with pytest.raises(SystemExit):
            validate_directory(nonexistent)

    def test_validate_directory_is_file(self, temp_dir: Path) -> None:
        """Test validation when path is a file, not directory."""
        file_path = temp_dir / "not_a_directory.txt"
        file_path.write_text("content")

        with pytest.raises(SystemExit):
            validate_directory(file_path)

    def test_parse_spec_file_with_duplicate_seasons(self, temp_dir: Path) -> None:
        """Test parsing spec file with duplicate season numbers."""
        spec_content = """1 | 1-5
1 | 6-10
2 | 11-15"""

        spec_file = temp_dir / "anifix.spec"
        spec_file.write_text(spec_content)

        result = parse_spec_file(spec_file)
        # Later definition should override earlier one
        expected = {1: (6, 10), 2: (11, 15)}
        assert result == expected

    def test_episode_filename_parsing_edge_cases(self) -> None:
        """Test episode filename parsing edge cases."""
        # Valid cases
        valid_cases = [
            ("Episode 001 - Title.mkv", 1),
            ("EPISODE 99 - TITLE.AVI", 99),
            ("episode    5   -   title.mp4", 5),
        ]

        for filename, expected in valid_cases:
            result = get_episode_number_from_filename(filename)
            assert result == expected

        # Invalid cases
        invalid_cases = [
            "No number here.mkv",
            "Episode - Missing Number.mkv",
            "Episode X - Non-numeric.mkv",
        ]

        for filename in invalid_cases:
            with pytest.raises(ValueError):
                get_episode_number_from_filename(filename)

    def test_overlapping_season_ranges(self, temp_dir: Path) -> None:
        """Test handling of overlapping season ranges in spec file."""
        # This should now raise an error during spec file parsing
        spec_content = """1 | 1-10
2 | 5-15"""

        spec_file = temp_dir / "anifix.spec"
        spec_file.write_text(spec_content)

        with pytest.raises(ValueError, match="Episode 5 appears in multiple seasons"):
            parse_spec_file(spec_file)

    def test_invalid_episode_ranges(self, temp_dir: Path) -> None:
        """Test handling of invalid episode ranges (end < start)."""
        spec_content = "1 | 10-5"

        spec_file = temp_dir / "anifix.spec"
        spec_file.write_text(spec_content)

        with pytest.raises(
            ValueError, match="Invalid episode range for season 1: 10-5"
        ):
            parse_spec_file(spec_file)

    def test_spec_file_missing_pipe_separator(self, temp_dir: Path) -> None:
        """Test handling of spec file lines without pipe separator."""
        spec_content = "1 1-5"

        spec_file = temp_dir / "anifix.spec"
        spec_file.write_text(spec_content)

        with pytest.raises(
            ValueError,
            match="Line 1: Invalid format. Expected 'season \\| episode_range'",
        ):
            parse_spec_file(spec_file)

    def test_spec_file_empty_episode_range(self, temp_dir: Path) -> None:
        """Test handling of empty episode ranges in spec file."""
        spec_content = "1 | "

        spec_file = temp_dir / "anifix.spec"
        spec_file.write_text(spec_content)

        with pytest.raises(
            ValueError, match="Line 1: Empty episode range for season 1"
        ):
            parse_spec_file(spec_file)

    def test_spec_file_invalid_range_format(self, temp_dir: Path) -> None:
        """Test handling of invalid episode range formats."""
        test_cases = [
            ("1 | 5-", "Line 1: Invalid episode range format: 5-"),
            ("1 | -10", "Line 1: Invalid episode range format: -10"),
            (
                "1 | 5--10",
                "Invalid episode range for season 1: 5--10 \\(end cannot be less than start\\)",
            ),
        ]

        for spec_content, expected_error in test_cases:
            spec_file = temp_dir / "anifix.spec"
            spec_file.write_text(spec_content)

            with pytest.raises(ValueError, match=expected_error):
                parse_spec_file(spec_file)

    def test_spec_file_invalid_numbers(self, temp_dir: Path) -> None:
        """Test handling of invalid numbers in spec file."""
        test_cases = [
            ("abc | 1-5", "Line 1: Invalid number in line: abc \\| 1-5"),
            ("1 | abc-5", "Line 1: Invalid number in line: 1 \\| abc-5"),
            ("1 | 1-abc", "Line 1: Invalid number in line: 1 \\| 1-abc"),
        ]

        for spec_content, expected_error in test_cases:
            spec_file = temp_dir / "anifix.spec"
            spec_file.write_text(spec_content)

            with pytest.raises(ValueError, match=expected_error):
                parse_spec_file(spec_file)

    def test_spec_file_empty_file(self, temp_dir: Path) -> None:
        """Test handling of completely empty spec file."""
        spec_file = temp_dir / "anifix.spec"
        spec_file.write_text("")

        with pytest.raises(
            ValueError, match="No valid season mappings found in spec file"
        ):
            parse_spec_file(spec_file)

    def test_spec_file_comments_only(self, temp_dir: Path) -> None:
        """Test handling of spec file with only comments."""
        spec_content = """# This is a comment
# Another comment
"""

        spec_file = temp_dir / "anifix.spec"
        spec_file.write_text(spec_content)

        with pytest.raises(
            ValueError, match="No valid season mappings found in spec file"
        ):
            parse_spec_file(spec_file)

    def test_spec_file_duplicate_seasons_warning(
        self, temp_dir: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test warning message for duplicate season definitions."""
        spec_content = """1 | 1-5
1 | 6-10
2 | 11-15"""

        spec_file = temp_dir / "anifix.spec"
        spec_file.write_text(spec_content)

        result = parse_spec_file(spec_file)
        captured = capsys.readouterr()

        # Should show warning but not fail
        assert "Warning: Duplicate season definitions found: 1" in captured.out
        # Should use last definition
        assert result == {1: (6, 10), 2: (11, 15)}

    def test_backup_file_with_missing_files(self, temp_dir: Path) -> None:
        """Test backup restoration when some files are missing."""
        backup_data = {
            "S01E01 - Title1.mkv": "Episode 1 - Title1.mkv",
            "S01E02 - Title2.mkv": "Episode 2 - Title2.mkv",
            "S01E03 - Title3.mkv": "Episode 3 - Title3.mkv",
        }

        # Create backup file
        backup_file = temp_dir / ".anifix-backup.json"
        with backup_file.open("w") as f:
            json.dump(backup_data, f)

        # Only create some of the files
        (temp_dir / "S01E01 - Title1.mkv").write_text("content")
        # S01E02 and S01E03 are missing

        # Should handle missing files gracefully
        from anifix.core import restore_files

        restore_files(temp_dir)

        # Should restore the one file that exists
        assert (temp_dir / "Episode 1 - Title1.mkv").exists()


class TestPerformance:
    """Tests for performance and scalability."""

    @pytest.mark.slow
    def test_large_number_of_files(self, temp_dir: Path) -> None:
        """Test processing a large number of files."""
        # Create many files
        num_files = 100
        for i in range(1, num_files + 1):
            filename = f"Episode {i} - Title {i}.mkv"
            (temp_dir / filename).write_text("content")

        season_map = {s: ((s - 1) * 25 + 1, s * 25) for s in range(1, 5)}

        # Should handle large number of files without issues
        rename_episode_files(temp_dir, season_map)

        # Verify some files were renamed correctly
        assert (temp_dir / "S01E01 - Title 1.mkv").exists()
        assert (temp_dir / "S04E25 - Title 100.mkv").exists()

    def test_deep_directory_structure(self, temp_dir: Path) -> None:
        """Test with files in nested directories (should be ignored)."""
        # Create nested structure
        nested_dir = temp_dir / "nested" / "deep" / "structure"
        nested_dir.mkdir(parents=True)

        # Create files at different levels
        (temp_dir / "Episode 1 - Root.mkv").write_text("content")
        (nested_dir / "Episode 2 - Nested.mkv").write_text("content")

        season_map = {1: (1, 5)}
        rename_episode_files(temp_dir, season_map)

        # Only root level file should be processed
        assert (temp_dir / "S01E01 - Root.mkv").exists()
        assert (nested_dir / "Episode 2 - Nested.mkv").exists()  # Unchanged
