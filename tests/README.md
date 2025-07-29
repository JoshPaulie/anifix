# Test Documentation

This directory contains the comprehensive test suite for anifix.

## Test Structure

- `conftest.py` - Shared fixtures and test utilities
- `test_core.py` - Tests for core functionality (parsing, renaming, backup/restore)
- `test_cli.py` - Tests for command-line interface and argument parsing
- `test_edge_cases.py` - Tests for edge cases, error handling, and performance

## Running Tests

### Basic test run
```bash
uv run pytest
```

### Run with verbose output
```bash
uv run pytest -v
```

### Run specific test file
```bash
uv run pytest tests/test_core.py -v
```

### Run with coverage report
```bash
uv run pytest --cov=src/anifix --cov-report=html
```

### Run only fast tests (exclude slow tests)
```bash
uv run pytest -m "not slow"
```

## Test Categories

### Core Functionality Tests (`test_core.py`)
- **Spec file parsing**: Tests for valid/invalid spec files, comments, empty lines
- **Episode filename parsing**: Tests for extracting episode numbers from various filename formats
- **Season mapping**: Tests for finding correct season and episode numbers
- **File renaming**: Tests for the core renaming functionality with backup
- **Backup/restore**: Tests for backup file creation and restoration functionality
- **Integration tests**: End-to-end workflow tests

### CLI Tests (`test_cli.py`)
- **Argument parsing**: Tests for all command-line arguments and options
- **Main function**: Tests for different execution modes (normal, dry-run, restore, verbose)
- **Error handling**: Tests for invalid arguments and error conditions

### Edge Cases Tests (`test_edge_cases.py`)
- **Malformed input**: Tests for handling corrupted spec files and filenames
- **File system edge cases**: Tests for permission errors, missing files, existing targets
- **Performance tests**: Tests with large numbers of files
- **Boundary conditions**: Tests for extreme values and edge cases

## Test Fixtures

The test suite uses several fixtures defined in `conftest.py`:

- `temp_dir`: Creates isolated temporary directories for each test
- `sample_spec_content`: Provides standard spec file content
- `sample_spec_file`: Creates a sample spec file in temp directory
- `sample_episode_files`: Creates sample episode files for testing
- `sample_backup_data`: Provides backup data for restore testing
- `backup_file`: Creates a backup file with sample data

## Coverage

The test suite aims for high code coverage (80%+). Run with coverage to see detailed reports:

```bash
uv run pytest --cov=src/anifix --cov-report=term-missing --cov-report=html
```

This will generate:
- Terminal coverage report showing missing lines
- HTML coverage report in `htmlcov/` directory

## Test Markers

- `@pytest.mark.slow`: Marks tests that take longer to run
- `@pytest.mark.integration`: Marks integration tests

## Continuous Integration

The test suite is designed to run in CI environments. All tests should pass before merging code changes.

## Known Test Issues

1. **Path resolution**: Some tests may fail due to macOS `/private/var` vs `/var` path resolution differences (cosmetic issue)
2. **Error handling**: Some edge case tests expect specific error handling behavior that may change

## Contributing

When adding new functionality:

1. Write tests first (TDD approach)
2. Ensure all existing tests still pass
3. Add appropriate test markers for slow or integration tests
4. Update this documentation if adding new test categories
