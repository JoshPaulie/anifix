"""Shared fixtures and utilities for anifix tests."""

import json
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_spec_content() -> str:
    """Sample spec file content for testing."""
    return """# Season | Episode range
1 | 1-4
2 | 5-7
3 | 8-10"""


@pytest.fixture
def sample_spec_file(temp_dir: Path, sample_spec_content: str) -> Path:
    """Create a sample spec file for testing."""
    spec_file = temp_dir / "anifix.spec"
    spec_file.write_text(sample_spec_content)
    return spec_file


@pytest.fixture
def sample_episode_files(temp_dir: Path) -> list[Path]:
    """Create sample episode files for testing."""
    files = []
    episode_titles = [
        "My First Episode",
        "My Second Episode",
        "My Third Episode",
        "My Fourth Episode",
        "My Fifth Episode",
        "My Sixth Episode",
        "My Seventh Episode",
        "My Eighth Episode",
        "My Ninth Episode",
        "My Tenth Episode",
    ]

    for i, title in enumerate(episode_titles, 1):
        filename = f"Episode {i} - {title}.mkv"
        file_path = temp_dir / filename
        file_path.write_text("dummy video content")
        files.append(file_path)

    return files


@pytest.fixture
def sample_backup_data() -> dict[str, str]:
    """Sample backup data for testing restore functionality."""
    return {
        "S01E01 - My First Episode.mkv": "Episode 1 - My First Episode.mkv",
        "S01E02 - My Second Episode.mkv": "Episode 2 - My Second Episode.mkv",
        "S02E01 - My Fifth Episode.mkv": "Episode 5 - My Fifth Episode.mkv",
    }


@pytest.fixture
def backup_file(temp_dir: Path, sample_backup_data: dict[str, str]) -> Path:
    """Create a backup file for testing restore functionality."""
    backup_file = temp_dir / ".anifix-backup.json"
    with backup_file.open("w") as f:
        json.dump(sample_backup_data, f, indent=2)
    return backup_file


def create_renamed_files(temp_dir: Path, backup_data: dict[str, str]) -> list[Path]:
    """Create renamed files based on backup data."""
    files = []
    for current_name in backup_data.keys():
        file_path = temp_dir / current_name
        file_path.write_text("dummy video content")
        files.append(file_path)
    return files
