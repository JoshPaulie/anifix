"""Tests for anifix CLI functionality."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from anifix.core import create_argument_parser, main


class TestArgumentParser:
    """Tests for the argument parser."""

    def test_create_argument_parser(self) -> None:
        """Test that argument parser is created correctly."""
        parser = create_argument_parser()

        # Test that parser has expected arguments
        args = parser.parse_args([])

        # Check default values
        assert args.directory == Path.cwd()
        assert args.spec_file is None
        assert args.dry_run is False
        assert args.verbose is False
        assert args.restore is False

    def test_argument_parser_with_all_args(self) -> None:
        """Test argument parser with all arguments provided."""
        parser = create_argument_parser()

        test_args = [
            "-d",
            "/tmp/test",
            "-s",
            "/tmp/test.spec",
            "--dry-run",
            "--verbose",
            "--restore",
        ]

        args = parser.parse_args(test_args)

        assert args.directory == Path("/tmp/test")
        assert args.spec_file == Path("/tmp/test.spec")
        assert args.dry_run is True
        assert args.verbose is True
        assert args.restore is True

    def test_argument_parser_short_flags(self) -> None:
        """Test argument parser with short flags."""
        parser = create_argument_parser()

        test_args = ["-d", "/tmp", "-s", "test.spec", "-v"]
        args = parser.parse_args(test_args)

        assert args.directory == Path("/tmp")
        assert args.spec_file == Path("test.spec")
        assert args.verbose is True

    def test_argument_parser_url_spec(self) -> None:
        """Test argument parser with --url-spec argument."""
        parser = create_argument_parser()

        test_args = ["--url-spec", "https://www.thetvdb.com/series/test-series"]
        args = parser.parse_args(test_args)

        assert args.url_spec == "https://www.thetvdb.com/series/test-series"

    def test_argument_parser_with_url_spec_and_directory(self) -> None:
        """Test argument parser with both --url-spec and directory."""
        parser = create_argument_parser()

        test_args = [
            "--url-spec",
            "https://www.thetvdb.com/series/test-series",
            "-d",
            "/tmp/anime",
            "--dry-run",
        ]
        args = parser.parse_args(test_args)

        assert args.url_spec == "https://www.thetvdb.com/series/test-series"
        assert args.directory == Path("/tmp/anime")
        assert args.dry_run is True


class TestMainFunction:
    """Tests for the main function."""

    @patch("anifix.core.validate_directory")
    @patch("anifix.core.restore_files")
    def test_main_restore_mode(self, mock_restore: Mock, mock_validate: Mock) -> None:
        """Test main function in restore mode."""
        test_args = ["--restore", "-d", "/tmp/test"]

        with patch("sys.argv", ["anifix"] + test_args):
            main()

        mock_validate.assert_called_once()
        mock_restore.assert_called_once()

    @patch("anifix.core.validate_directory")
    @patch("anifix.core.find_spec_file")
    @patch("anifix.core.parse_spec_file")
    @patch("anifix.core.rename_episode_files")
    def test_main_normal_mode(
        self,
        mock_rename: Mock,
        mock_parse: Mock,
        mock_find: Mock,
        mock_validate: Mock,
    ) -> None:
        """Test main function in normal rename mode."""
        # Setup mocks
        mock_find.return_value = Path("/tmp/anifix.spec")
        mock_parse.return_value = {1: (1, 10)}

        test_args = ["-d", "/tmp/test"]

        with patch("sys.argv", ["anifix"] + test_args):
            main()

        mock_validate.assert_called_once()
        mock_find.assert_called_once()
        mock_parse.assert_called_once()
        mock_rename.assert_called_once()

    @patch("anifix.core.validate_directory")
    @patch("anifix.core.find_spec_file")
    @patch("anifix.core.parse_spec_file")
    def test_main_empty_season_map(
        self,
        mock_parse: Mock,
        mock_find: Mock,
        mock_validate: Mock,
    ) -> None:
        """Test main function with empty season map."""
        # Setup mocks
        mock_find.return_value = Path("/tmp/anifix.spec")
        mock_parse.return_value = {}

        test_args = ["-d", "/tmp/test"]

        with patch("sys.argv", ["anifix"] + test_args):
            with pytest.raises(SystemExit):
                main()

    @patch("anifix.core.validate_directory")
    @patch("anifix.core.find_spec_file")
    @patch("anifix.core.parse_spec_file")
    @patch("anifix.core.rename_episode_files")
    def test_main_dry_run_mode(
        self,
        mock_rename: Mock,
        mock_parse: Mock,
        mock_find: Mock,
        mock_validate: Mock,
    ) -> None:
        """Test main function in dry run mode."""
        # Setup mocks
        mock_find.return_value = Path("/tmp/anifix.spec")
        mock_parse.return_value = {1: (1, 10)}

        test_args = ["--dry-run", "-d", "/tmp/test"]

        with patch("sys.argv", ["anifix"] + test_args):
            main()

        # Check that rename was called with dry_run=True
        mock_rename.assert_called_once()
        call_args = mock_rename.call_args
        assert call_args.kwargs["dry_run"] is True

    @patch("anifix.core.validate_directory")
    @patch("anifix.core.find_spec_file")
    @patch("anifix.core.parse_spec_file")
    @patch("anifix.core.print_verbose_info")
    @patch("anifix.core.rename_episode_files")
    def test_main_verbose_mode(
        self,
        mock_rename: Mock,
        mock_verbose: Mock,
        mock_parse: Mock,
        mock_find: Mock,
        mock_validate: Mock,
    ) -> None:
        """Test main function in verbose mode."""
        # Setup mocks
        spec_file = Path("/tmp/anifix.spec")
        season_map = {1: (1, 10)}
        mock_find.return_value = spec_file
        mock_parse.return_value = season_map

        test_args = ["--verbose", "-d", "/tmp/test"]

        with patch("sys.argv", ["anifix"] + test_args):
            main()

        # Check that verbose info was printed
        mock_verbose.assert_called_once()
        call_args = mock_verbose.call_args[0]
        assert call_args[1] == spec_file
        assert call_args[2] == season_map

    @patch("anifix.core.validate_directory")
    @patch("anifix.core.handle_url_spec")
    @patch("anifix.core.rename_episode_files")
    def test_main_url_spec_mode(
        self,
        mock_rename: Mock,
        mock_handle_url_spec: Mock,
        mock_validate: Mock,
    ) -> None:
        """Test main function with --url-spec argument."""
        # Setup mocks
        mock_handle_url_spec.return_value = {1: (1, 11), 2: (12, 23)}

        test_args = [
            "--url-spec",
            "https://www.thetvdb.com/series/test-series",
            "-d",
            "/tmp/test",
        ]

        with patch("sys.argv", ["anifix"] + test_args):
            main()

        mock_validate.assert_called_once()
        mock_handle_url_spec.assert_called_once()
        mock_rename.assert_called_once()

        # Check that rename was called with the correct season map
        call_args = mock_rename.call_args
        season_map = call_args[0][1]  # Second positional argument
        assert season_map == {1: (1, 11), 2: (12, 23)}

    @patch("anifix.tvdb.SCRAPING_AVAILABLE", new=False)
    def test_main_url_spec_missing_dependencies(self) -> None:
        """Test main function with --url-spec when dependencies are missing."""
        test_args = ["--url-spec", "https://www.thetvdb.com/series/test-series"]

        with patch("sys.argv", ["anifix", *test_args]), pytest.raises(SystemExit):
            main()
