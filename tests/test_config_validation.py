import pytest

from backend.config import validate_directory_path, validate_file_path


def test_validate_file_path_valid():
    """Test valid file paths."""
    # Relative path
    assert validate_file_path("test.txt", base_dir="/tmp") == "/tmp/test.txt"
    # Absolute path (allowed)
    assert validate_file_path("/tmp/test.txt", base_dir="/tmp") == "/tmp/test.txt"


def test_validate_file_path_traversal():
    """Test directory traversal attempts."""
    with pytest.raises(ValueError, match="Path outside allowed directory"):
        validate_file_path("../etc/passwd", base_dir="/tmp")

    with pytest.raises(ValueError, match="Path outside allowed directory"):
        validate_file_path("/etc/passwd", base_dir="/tmp")


def test_validate_file_path_no_absolute():
    """Test disallowing absolute paths."""
    with pytest.raises(ValueError, match="Absolute paths not allowed"):
        validate_file_path("/tmp/test.txt", allow_absolute=False)


def test_validate_file_path_empty():
    """Test empty path."""
    with pytest.raises(ValueError, match="Path cannot be empty"):
        validate_file_path("")


def test_validate_directory_path_valid():
    """Test valid directory paths."""
    assert validate_directory_path("subdir", base_dir="/tmp") == "/tmp/subdir"


def test_validate_directory_path_traversal():
    """Test directory traversal for directories."""
    with pytest.raises(ValueError, match="Path outside allowed directory"):
        validate_directory_path("../etc", base_dir="/tmp")
