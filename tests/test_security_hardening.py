import json
import os

# We need to reload security module to test environment variable changes
import sys
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet


def test_security_fail_fast_in_production():
    """Test that security module raises ValueError if ENCRYPTION_KEY is missing in production."""
    with patch.dict(os.environ, {"ENVIRONMENT": "production", "ENCRYPTION_KEY": ""}):
        # Remove from modules to force reload
        if "backend.security" in sys.modules:
            del sys.modules["backend.security"]

        with pytest.raises(ValueError, match="ENCRYPTION_KEY must be set in production"):
            import backend.security  # noqa: F401


def test_security_warn_in_development():
    """Test that security module generates key in development if missing."""
    with patch.dict(os.environ, {"ENVIRONMENT": "development", "ENCRYPTION_KEY": ""}):
        if "backend.security" in sys.modules:
            del sys.modules["backend.security"]

        import backend.security

        assert backend.security._ENCRYPTION_KEY is not None


def test_rotate_keys_script(tmp_path):
    """Test the key rotation logic."""
    from backend.scripts.rotate_keys import rotate_keys

    # Setup
    old_key = Fernet.generate_key().decode()
    new_key = Fernet.generate_key().decode()

    old_fernet = Fernet(old_key.encode())
    new_fernet = Fernet(new_key.encode())

    original_secret = "my-secret-api-key"
    encrypted_secret = old_fernet.encrypt(original_secret.encode()).decode()

    # Create mock organizations.json
    orgs_data = [{"id": "org1", "api_config": {"api_key": encrypted_secret}}]

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    orgs_file = data_dir / "organizations.json"

    with open(orgs_file, "w") as f:
        json.dump(orgs_data, f)

    # Mock PROJECT_ROOT to point to tmp_path
    with patch("backend.scripts.rotate_keys.PROJECT_ROOT", str(tmp_path)):
        rotate_keys(old_key, new_key)

    # Verify
    with open(orgs_file) as f:
        new_data = json.load(f)

    new_encrypted_secret = new_data[0]["api_config"]["api_key"]
    decrypted_secret = new_fernet.decrypt(new_encrypted_secret.encode()).decode()

    assert decrypted_secret == original_secret
    assert new_encrypted_secret != encrypted_secret
