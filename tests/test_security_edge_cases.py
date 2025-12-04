"""Edge case tests for security.py to improve coverage."""

import os

import pytest
from cryptography.fernet import Fernet

from backend.security import decrypt_value, encrypt_value


@pytest.fixture
def encryption_key(monkeypatch):
    """Set up a test encryption key."""
    test_key = Fernet.generate_key().decode()
    monkeypatch.setenv("ENCRYPTION_KEY", test_key)
    monkeypatch.setenv("ENVIRONMENT", "development")
    # Reload the module to pick up the new key
    import importlib

    import backend.security

    importlib.reload(backend.security)
    yield test_key


def test_encrypt_value_none_input(encryption_key):
    """Test encrypt_value handles None input."""
    # None should be treated as empty string
    result = encrypt_value(None)
    assert result == ""


def test_decrypt_value_none_input(encryption_key):
    """Test decrypt_value handles None input."""
    # None should be treated as empty string
    result = decrypt_value(None)
    assert result == ""


def test_decrypt_value_invalid_base64(encryption_key):
    """Test decrypt_value handles invalid base64 encoding."""
    invalid_token = "not-valid-base64-encoding!!!"

    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt_value(invalid_token)


def test_decrypt_value_wrong_key(encryption_key):
    """Test decrypt_value fails with wrong encryption key."""
    # Encrypt with current key
    plaintext = "test-value"
    encrypted = encrypt_value(plaintext)

    # Change encryption key
    new_key = Fernet.generate_key().decode()
    import backend.security

    backend.security._ENCRYPTION_KEY = new_key
    backend.security._fernet = Fernet(new_key.encode())

    # Should fail to decrypt
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt_value(encrypted)


def test_encrypt_value_very_long_string(encryption_key):
    """Test encrypt_value handles very long strings."""
    long_string = "x" * 10000
    encrypted = encrypt_value(long_string)
    decrypted = decrypt_value(encrypted)

    assert decrypted == long_string


def test_encrypt_value_special_characters(encryption_key):
    """Test encrypt_value handles special characters."""
    special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
    encrypted = encrypt_value(special_chars)
    decrypted = decrypt_value(encrypted)

    assert decrypted == special_chars


def test_encrypt_value_unicode(encryption_key):
    """Test encrypt_value handles unicode characters."""
    unicode_string = "测试 🚀 émojis 日本語"
    encrypted = encrypt_value(unicode_string)
    decrypted = decrypt_value(encrypted)

    assert decrypted == unicode_string


def test_encrypt_value_binary_like_string(encryption_key):
    """Test encrypt_value handles binary-like strings."""
    binary_like = "\x00\x01\x02\xff\xfe\xfd"
    encrypted = encrypt_value(binary_like)
    decrypted = decrypt_value(encrypted)

    assert decrypted == binary_like


def test_encrypt_decrypt_roundtrip_multiple_times(encryption_key):
    """Test encrypt/decrypt roundtrip multiple times."""
    plaintext = "test-value"

    for _ in range(10):
        encrypted = encrypt_value(plaintext)
        decrypted = decrypt_value(encrypted)
        assert decrypted == plaintext


def test_encrypt_value_empty_after_strip(encryption_key):
    """Test encrypt_value handles strings that become empty after strip."""
    # This shouldn't happen in practice, but test edge case
    result = encrypt_value("")
    assert result == ""


def test_decrypt_value_empty_after_strip(encryption_key):
    """Test decrypt_value handles strings that become empty after strip."""
    result = decrypt_value("")
    assert result == ""

