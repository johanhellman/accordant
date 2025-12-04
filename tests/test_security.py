"""Tests for security.py encryption functions."""

import os

import pytest
from cryptography.fernet import Fernet

from backend.security import decrypt_value, encrypt_value


class TestSecurity:
    """Tests for security encryption functions."""

    @pytest.fixture
    def encryption_key(self, monkeypatch):
        """Set up a test encryption key."""
        # Generate a valid Fernet key (32-byte base64-encoded)
        test_key = Fernet.generate_key().decode()
        monkeypatch.setenv("ENCRYPTION_KEY", test_key)
        monkeypatch.setenv("ENVIRONMENT", "development")
        # Reload the module to pick up the new key
        import importlib

        import backend.security

        importlib.reload(backend.security)
        yield test_key

    def test_encrypt_value(self, encryption_key):
        """Test encrypting a value."""
        plaintext = "sensitive-data-123"

        encrypted = encrypt_value(plaintext)

        assert encrypted != plaintext
        assert len(encrypted) > 0
        assert isinstance(encrypted, str)

    def test_decrypt_value(self, encryption_key):
        """Test decrypting a value."""
        plaintext = "sensitive-data-123"
        encrypted = encrypt_value(plaintext)

        decrypted = decrypt_value(encrypted)

        assert decrypted == plaintext

    def test_encrypt_decrypt_roundtrip(self, encryption_key):
        """Test encrypt/decrypt roundtrip."""
        test_values = [
            "simple",
            "value-with-special-chars-!@#$%^&*()",
            "value with spaces",
            "value\nwith\nnewlines",
            "value-with-unicode-测试-🚀",
        ]

        for value in test_values:
            encrypted = encrypt_value(value)
            decrypted = decrypt_value(encrypted)
            assert decrypted == value, f"Failed for value: {value}"

    def test_encrypt_empty_string(self, encryption_key):
        """Test encrypting empty string."""
        result = encrypt_value("")
        assert result == ""

    def test_decrypt_empty_string(self, encryption_key):
        """Test decrypting empty string."""
        result = decrypt_value("")
        assert result == ""

    def test_decrypt_invalid_token(self, encryption_key):
        """Test decrypting invalid token raises ValueError."""
        with pytest.raises(ValueError, match="Decryption failed"):
            decrypt_value("invalid-token-not-encrypted")

    def test_decrypt_corrupted_token(self, encryption_key):
        """Test decrypting corrupted token raises ValueError."""
        # Create a valid encrypted value
        encrypted = encrypt_value("test")
        # Corrupt it
        corrupted = encrypted[:-5] + "xxxxx"

        with pytest.raises(ValueError, match="Decryption failed"):
            decrypt_value(corrupted)

    def test_encrypt_different_values_produce_different_outputs(self, encryption_key):
        """Test that encrypting the same value multiple times produces different outputs (due to nonce)."""
        plaintext = "test-value"
        encrypted1 = encrypt_value(plaintext)
        encrypted2 = encrypt_value(plaintext)

        # Fernet uses a nonce, so same plaintext produces different ciphertext
        assert encrypted1 != encrypted2

        # But both decrypt to the same value
        assert decrypt_value(encrypted1) == plaintext
        assert decrypt_value(encrypted2) == plaintext

