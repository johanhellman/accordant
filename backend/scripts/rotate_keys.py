"""
Script to rotate encryption keys.
Usage: python -m backend.scripts.rotate_keys <OLD_KEY> <NEW_KEY>
"""

import json
import logging
import os
import sys

from cryptography.fernet import Fernet

from backend.config import PROJECT_ROOT

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def rotate_keys(old_key: str, new_key: str):
    """
    Rotate encryption keys for all encrypted data.
    Currently, only organization API keys are encrypted.
    """
    try:
        old_fernet = Fernet(old_key.encode() if isinstance(old_key, str) else old_key)
        new_fernet = Fernet(new_key.encode() if isinstance(new_key, str) else new_key)
    except Exception as e:
        logger.error(f"Invalid keys provided: {e}")
        sys.exit(1)

    orgs_file = os.path.join(PROJECT_ROOT, "data", "organizations.json")

    if not os.path.exists(orgs_file):
        logger.info("No organizations file found. Nothing to rotate.")
        return

    try:
        with open(orgs_file) as f:
            orgs_data = json.load(f)

        rotated_count = 0
        for org in orgs_data:
            api_config = org.get("api_config", {})
            encrypted_api_key = api_config.get("api_key")

            if encrypted_api_key:
                try:
                    # Decrypt with old key
                    decrypted = old_fernet.decrypt(encrypted_api_key.encode()).decode()
                    # Encrypt with new key
                    re_encrypted = new_fernet.encrypt(decrypted.encode()).decode()
                    # Update
                    api_config["api_key"] = re_encrypted
                    rotated_count += 1
                except Exception as e:
                    logger.error(f"Failed to rotate key for org {org.get('id')}: {e}")
                    # Continue or abort? Aborting to prevent partial state
                    sys.exit(1)

        # Save back
        with open(orgs_file, "w") as f:
            json.dump(orgs_data, f, indent=2)

        logger.info(f"Successfully rotated keys for {rotated_count} organizations.")

    except Exception as e:
        logger.error(f"Error during rotation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m backend.scripts.rotate_keys <OLD_KEY> <NEW_KEY>")
        sys.exit(1)

    old_key_arg = sys.argv[1]
    new_key_arg = sys.argv[2]

    rotate_keys(old_key_arg, new_key_arg)
