"""Tests for TVDB scraping functionality."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from anifix.core import handle_url_spec


class MockResponse:
    """Mock HTTP response for testing."""

    def __init__(self, content: str) -> None:
        """Initialize mock response with HTML content."""
        self.content = content.encode("utf-8")

    def raise_for_status(self) -> None:
        """Mock raise_for_status method."""
        pass


@pytest.fixture
def sample_tvdb_html() -> str:
    """Sample TVDB HTML table for testing."""
    return """
    <table class="table table-bordered table-hover table-colored">
      <thead>
        <tr>
          <th>Season</th>
          <th>From</th>
          <th>To</th>
          <th>Episodes</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>
            <a href="/series/the-sandman/allseasons/official"> All Seasons </a>
          </td>
          <td></td>
          <td></td>
          <td></td>
        </tr>
        <tr>
          <td>
            <a href="https://www.thetvdb.com/series/the-sandman/seasons/official/0"> Specials </a>
          </td>
          <td></td>
          <td></td>
          <td>0</td>
        </tr>
        <tr>
          <td>
            <a href="https://www.thetvdb.com/series/the-sandman/seasons/official/1"> Season 1 </a>
          </td>
          <td>August 2022</td>
          <td>August 2022</td>
          <td>11</td>
        </tr>
        <tr>
          <td>
            <a href="https://www.thetvdb.com/series/the-sandman/seasons/official/2"> Season 2 </a>
          </td>
          <td>July 2025</td>
          <td>July 2025</td>
          <td>12</td>
        </tr>
        <tr>
          <td>Unassigned Episodes</td>
          <td></td>
          <td></td>
          <td>0</td>
        </tr>
      </tbody>
    </table>
    """


class TestTVDBScraping:
    """Tests for TVDB scraping functionality."""

    def test_extract_series_id_from_url(self) -> None:
        """Test extracting series ID from various TVDB URL formats."""
        pytest.importorskip("requests")
        from anifix.tvdb import extract_series_id_from_url

        test_cases = [
            ("https://www.thetvdb.com/series/the-sandman", "the-sandman"),
            ("https://thetvdb.com/series/attack-on-titan", "attack-on-titan"),
            (
                "https://www.thetvdb.com/series/one-piece/seasons/official/1",
                "one-piece",
            ),
        ]

        for url, expected_id in test_cases:
            result = extract_series_id_from_url(url)
            assert result == expected_id

    def test_extract_series_id_invalid_url(self) -> None:
        """Test error handling for invalid URLs."""
        pytest.importorskip("requests")
        from anifix.tvdb import extract_series_id_from_url

        with pytest.raises(ValueError, match="Could not extract series ID"):
            extract_series_id_from_url("https://example.com/not-tvdb")

    def test_parse_seasons_table(self, sample_tvdb_html: str) -> None:
        """Test parsing TVDB seasons table."""
        pytest.importorskip("bs4")
        from bs4 import BeautifulSoup

        from anifix.tvdb import _parse_seasons_table

        soup = BeautifulSoup(sample_tvdb_html, "html.parser")
        result = _parse_seasons_table(soup)

        expected = [(1, 11), (2, 12)]
        assert result == expected

    def test_parse_seasons_table_no_table(self) -> None:
        """Test error handling when no seasons table is found."""
        pytest.importorskip("bs4")
        from bs4 import BeautifulSoup

        from anifix.tvdb import _parse_seasons_table

        html = "<div>No table here</div>"
        soup = BeautifulSoup(html, "html.parser")

        with pytest.raises(ValueError, match="Could not find seasons table"):
            _parse_seasons_table(soup)

    def test_generate_season_map_from_tvdb(self, sample_tvdb_html: str) -> None:
        """Test generating season map from TVDB data."""
        pytest.importorskip("requests")
        pytest.importorskip("bs4")

        with patch("requests.get") as mock_get:
            mock_get.return_value = MockResponse(sample_tvdb_html)

            from anifix.tvdb import generate_season_map_from_tvdb

            result = generate_season_map_from_tvdb(
                "https://www.thetvdb.com/series/test-series"
            )

            expected = {1: (1, 11), 2: (12, 23)}
            assert result == expected

    def test_generate_spec_from_tvdb(self, sample_tvdb_html: str) -> None:
        """Test generating spec file content from TVDB data."""
        pytest.importorskip("requests")
        pytest.importorskip("bs4")

        with patch("requests.get") as mock_get:
            mock_get.return_value = MockResponse(sample_tvdb_html)

            from anifix.tvdb import generate_spec_from_tvdb

            result = generate_spec_from_tvdb(
                "https://www.thetvdb.com/series/test-series"
            )

            expected_lines = [
                "# Season | Episode range",
                "1 | 1-11",
                "2 | 12-23",
                "",  # Final newline
            ]
            expected = "\n".join(expected_lines)
            assert result == expected

    def test_generate_spec_from_tvdb_with_output_file(
        self, sample_tvdb_html: str, temp_dir: Path
    ) -> None:
        """Test generating spec file and writing to disk."""
        pytest.importorskip("requests")
        pytest.importorskip("bs4")

        with patch("requests.get") as mock_get:
            mock_get.return_value = MockResponse(sample_tvdb_html)

            from anifix.tvdb import generate_spec_from_tvdb

            output_path = temp_dir / "generated.spec"
            result = generate_spec_from_tvdb(
                "https://www.thetvdb.com/series/test-series", output_path
            )

            # Check file was created and contains expected content
            assert output_path.exists()
            file_content = output_path.read_text()
            assert file_content == result

            expected_lines = [
                "# Season | Episode range",
                "1 | 1-11",
                "2 | 12-23",
                "",
            ]
            expected = "\n".join(expected_lines)
            assert file_content == expected

    def test_scraping_dependencies_not_available(self) -> None:
        """Test error handling when scraping dependencies are not available."""
        # Mock the SCRAPING_AVAILABLE flag
        with patch("anifix.tvdb.SCRAPING_AVAILABLE", False):
            from anifix.tvdb import check_scraping_dependencies

            with pytest.raises(SystemExit):
                check_scraping_dependencies()

    def test_handle_url_spec_without_dependencies(self) -> None:
        """Test handle_url_spec when dependencies are missing."""
        # Create a mock args object
        mock_args = Mock()
        mock_args.url_spec = "https://www.thetvdb.com/series/test"

        # Mock the SCRAPING_AVAILABLE flag to simulate missing dependencies
        with patch("anifix.tvdb.SCRAPING_AVAILABLE", new=False):
            with pytest.raises(SystemExit):
                handle_url_spec(mock_args)

    def test_handle_url_spec_with_dependencies(self, sample_tvdb_html: str) -> None:
        """Test handle_url_spec with dependencies available."""
        pytest.importorskip("requests")
        pytest.importorskip("bs4")

        # Create a mock args object
        mock_args = Mock()
        mock_args.url_spec = "https://www.thetvdb.com/series/test-series"

        with patch("requests.get") as mock_get:
            mock_get.return_value = MockResponse(sample_tvdb_html)

            result = handle_url_spec(mock_args)

            expected = {1: (1, 11), 2: (12, 23)}
            assert result == expected


class TestTVDBIntegration:
    """Integration tests for TVDB functionality with the main CLI."""

    def test_url_spec_with_file_operations(
        self, sample_tvdb_html: str, temp_dir: Path
    ) -> None:
        """Test --url-spec functionality with actual file operations."""
        pytest.importorskip("requests")
        pytest.importorskip("bs4")

        # Create test episode files
        test_files = [
            "Episode 1 - First Episode.mkv",
            "Episode 2 - Second Episode.mkv",
            "Episode 11 - Eleventh Episode.mkv",
            "Episode 12 - Twelfth Episode.mkv",
        ]

        for filename in test_files:
            (temp_dir / filename).touch()

        with patch("requests.get") as mock_get:
            mock_get.return_value = MockResponse(sample_tvdb_html)

            from anifix.renamer import rename_episode_files
            from anifix.tvdb import generate_season_map_from_tvdb

            # Generate season map from TVDB
            season_map = generate_season_map_from_tvdb(
                "https://www.thetvdb.com/series/test-series"
            )

            # Test the renaming (dry run)
            rename_episode_files(temp_dir, season_map, dry_run=True)

            # Files should still exist with original names in dry run
            for filename in test_files:
                assert (temp_dir / filename).exists()

            # Now test actual renaming
            rename_episode_files(temp_dir, season_map, dry_run=False)

            # Check expected renamed files exist
            expected_renamed = [
                "S01E01 - First Episode.mkv",
                "S01E02 - Second Episode.mkv",
                "S01E11 - Eleventh Episode.mkv",
                "S02E01 - Twelfth Episode.mkv",  # Episode 12 maps to Season 2 Episode 1
            ]

            for filename in expected_renamed:
                assert (temp_dir / filename).exists(), (
                    f"Expected file {filename} not found"
                )

            # Original files should be gone
            for filename in test_files:
                assert not (temp_dir / filename).exists(), (
                    f"Original file {filename} still exists"
                )
