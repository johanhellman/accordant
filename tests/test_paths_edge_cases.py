"""Edge case tests for config/paths.py to improve coverage."""

import os
import tempfile

import pytest

from backend.config.paths import validate_directory_path, validate_file_path


def test_validate_file_path_relative_with_base_dir():
    """Test validate_file_path with relative path and base directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = validate_file_path("subdir/file.txt", base_dir=tmpdir)

        assert result == os.path.join(tmpdir, "subdir", "file.txt")
        assert os.path.commonpath([tmpdir, result]) == tmpdir


def test_validate_file_path_absolute_within_base():
    """Test validate_file_path with absolute path within base directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        abs_path = os.path.join(tmpdir, "file.txt")
        result = validate_file_path(abs_path, base_dir=tmpdir)

        assert result == abs_path
        assert os.path.commonpath([tmpdir, result]) == tmpdir


def test_validate_file_path_traversal_with_base():
    """Test validate_file_path prevents directory traversal with base directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Try to escape base directory
        with pytest.raises(ValueError, match="Path outside allowed directory"):
            validate_file_path("../../etc/passwd", base_dir=tmpdir)


def test_validate_file_path_traversal_absolute():
    """Test validate_file_path prevents absolute path outside base directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Try to access file outside base directory
        outside_path = os.path.join(os.path.dirname(tmpdir), "outside.txt")
        with pytest.raises(ValueError, match="Path outside allowed directory"):
            validate_file_path(outside_path, base_dir=tmpdir)


def test_validate_file_path_no_absolute_flag():
    """Test validate_file_path rejects absolute paths when allow_absolute=False."""
    with tempfile.TemporaryDirectory() as tmpdir:
        abs_path = os.path.join(tmpdir, "file.txt")
        with pytest.raises(ValueError, match="Absolute paths not allowed"):
            validate_file_path(abs_path, allow_absolute=False)


def test_validate_file_path_relative_no_absolute_flag():
    """Test validate_file_path allows relative paths when allow_absolute=False."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = validate_file_path("file.txt", base_dir=tmpdir, allow_absolute=False)

        assert result == os.path.join(tmpdir, "file.txt")


def test_validate_file_path_normalizes_path():
    """Test validate_file_path normalizes path separators."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Use mixed separators (if on Windows)
        path = "subdir\\file.txt" if os.sep == "\\" else "subdir/file.txt"

        result = validate_file_path(path, base_dir=tmpdir)

        assert os.path.normpath(result) == result


def test_validate_file_path_empty_string():
    """Test validate_file_path raises error for empty string."""
    with pytest.raises(ValueError, match="Path cannot be empty"):
        validate_file_path("")


def test_validate_file_path_none():
    """Test validate_file_path raises error for None."""
    with pytest.raises((ValueError, TypeError)):
        validate_file_path(None)


def test_validate_file_path_dot_dot_in_middle():
    """Test validate_file_path handles .. in middle of path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Path with .. in middle (should be normalized)
        result = validate_file_path("subdir/../file.txt", base_dir=tmpdir)

        assert result == os.path.join(tmpdir, "file.txt")
        assert os.path.commonpath([tmpdir, result]) == tmpdir


def test_validate_file_path_multiple_dot_dot():
    """Test validate_file_path prevents multiple .. sequences."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(ValueError, match="Path outside allowed directory"):
            validate_file_path("../../../../etc/passwd", base_dir=tmpdir)


def test_validate_file_path_no_base_dir():
    """Test validate_file_path works without base_dir."""
    # Should use current working directory
    result = validate_file_path("test.txt")

    assert os.path.isabs(result)
    assert result.endswith("test.txt")


def test_validate_directory_path_delegates_to_file_path():
    """Test validate_directory_path delegates to validate_file_path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = validate_directory_path("subdir", base_dir=tmpdir)

        assert result == os.path.join(tmpdir, "subdir")
        assert os.path.commonpath([tmpdir, result]) == tmpdir


def test_validate_directory_path_traversal():
    """Test validate_directory_path prevents directory traversal."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(ValueError, match="Path outside allowed directory"):
            validate_directory_path("../etc", base_dir=tmpdir)


def test_validate_file_path_windows_different_drives():
    """Test validate_file_path handles Windows different drives."""
    if os.name != "nt":
        pytest.skip("Windows-specific test")

    # On Windows, paths on different drives raise ValueError in commonpath
    # The code should handle this gracefully
    with tempfile.TemporaryDirectory() as tmpdir:
        # Try to access C: drive from temp directory (likely on different drive)
        c_drive_path = "C:\\Windows\\System32"
        if os.path.commonpath([tmpdir, c_drive_path]) != tmpdir:
            with pytest.raises(ValueError, match="Path outside allowed directory"):
                validate_file_path(c_drive_path, base_dir=tmpdir)


def test_validate_file_path_symlink():
    """Test validate_file_path handles symlinks correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a file
        file_path = os.path.join(tmpdir, "file.txt")
        with open(file_path, "w") as f:
            f.write("test")

        # Create symlink (if supported)
        try:
            symlink_path = os.path.join(tmpdir, "link.txt")
            os.symlink(file_path, symlink_path)

            # Should resolve symlink
            result = validate_file_path("link.txt", base_dir=tmpdir)
            assert os.path.isabs(result)
        except (OSError, NotImplementedError):
            # Symlinks not supported on this platform
            pytest.skip("Symlinks not supported")


def test_validate_file_path_current_directory():
    """Test validate_file_path handles current directory reference."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = validate_file_path(".", base_dir=tmpdir)

        assert result == tmpdir
        assert os.path.commonpath([tmpdir, result]) == tmpdir


def test_validate_file_path_parent_directory():
    """Test validate_file_path handles parent directory reference."""
    with tempfile.TemporaryDirectory() as tmpdir:
        subdir = os.path.join(tmpdir, "subdir")
        os.makedirs(subdir, exist_ok=True)

        # Should resolve to base directory
        result = validate_file_path("..", base_dir=subdir)

        # Should be normalized to base directory
        assert os.path.commonpath([tmpdir, result]) == tmpdir
