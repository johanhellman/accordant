import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:8001"


def run_test():
    print("Starting Phase 2 Verification...")

    # 1. Register
    username = "phase2_test_user"
    password = "password123"
    print(f"1. Registering user {username}...")
    try:
        res = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={"username": username, "email": f"{username}@example.com", "password": password},
        )
        if res.status_code == 200:
            token = res.json()["access_token"]
            print("   Success: Registered and got token.")
        elif res.status_code == 400 and "already registered" in res.text:
            print("   User already exists, logging in...")
            res = requests.post(
                f"{BASE_URL}/api/auth/token", data={"username": username, "password": password}
            )
            res.raise_for_status()
            token = res.json()["access_token"]
            print("   Success: Logged in.")
        else:
            print(f"   Failed: {res.status_code} {res.text}")
            return

    except Exception as e:
        print(f"   Error: {e}")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Conversation
    print("2. Creating conversation...")
    try:
        res = requests.post(
            f"{BASE_URL}/api/conversations", json={"title": "Test"}, headers=headers
        )
        res.raise_for_status()
        conv_id = res.json()["id"]
        print(f"   Success: Created conversation {conv_id}")
    except Exception as e:
        print(f"   Error: {e}")
        return

    # 3. Send Message (Expect Failure if no key configured)
    print("3. Sending message (Expect Failure if key not set)...")
    try:
        res = requests.post(
            f"{BASE_URL}/api/conversations/{conv_id}/message",
            json={"content": "Hello"},
            headers=headers,
        )
        if res.status_code == 400:
            print("   Success: Got expected 400 error (Key not configured).")
        elif res.status_code == 200:
            print(
                "   Unexpected Success: Message sent (Key might be configured from previous run or fallback)."
            )
        else:
            print(f"   Unexpected Status: {res.status_code} {res.text}")
    except Exception as e:
        print(f"   Error: {e}")

    # 4. Configure API Key
    print("4. Configuring API Key via Admin API...")
    test_key = "sk-test-key-12345"

    try:
        # Update Settings
        res = requests.put(f"{BASE_URL}/api/settings", json={"api_key": test_key}, headers=headers)
        if res.status_code == 200:
            print("   Success: Settings updated.")
        else:
            print(f"   Failed: {res.status_code} {res.text}")
            return

        # Verify Masking
        res = requests.get(f"{BASE_URL}/api/settings", headers=headers)
        if res.status_code == 200:
            data = res.json()
            if data["api_key"] == "********":
                print("   Success: API Key is masked in response.")
            else:
                print(f"   Failed: API Key not masked: {data['api_key']}")
        else:
            print(f"   Failed to get settings: {res.status_code}")

        # Verify Encryption on Disk
        import json

        with open("data/organizations.json") as f:
            orgs = json.load(f)
            # Find our org (we don't know the ID easily, but we can search)
            # Or just check if any org has api_config with encrypted key
            found_encrypted = False
            for org in orgs:
                if "api_config" in org and org["api_config"] and "api_key" in org["api_config"]:
                    key_val = org["api_config"]["api_key"]
                    if key_val.startswith("gAAAA"):  # Fernet tokens start with gAAAA
                        found_encrypted = True
                        print(f"   Success: Found encrypted key on disk: {key_val[:10]}...")
                        break

            if not found_encrypted:
                print("   Failed: No encrypted key found in data/organizations.json")

    except Exception as e:
        print(f"   Error: {e}")
        return

    # 5. Send Message (Expect Success)
    print("5. Sending message (Expect Success)...")
    try:
        res = requests.post(
            f"{BASE_URL}/api/conversations/{conv_id}/message",
            json={"content": "Hello again"},
            headers=headers,
        )
        if res.status_code == 200:
            print("   Success: Message sent successfully.")
        else:
            print(f"   Failed: {res.status_code} {res.text}")
    except Exception as e:
        print(f"   Error: {e}")


if __name__ == "__main__":
    run_test()
