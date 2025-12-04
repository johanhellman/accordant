import os

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:8001"


def run_test():
    print("Starting Phase 3 Verification (Multi-Org)...")

    # 1. Register User A (Org Creator)
    user_a = "user_a_" + os.urandom(4).hex()
    password = "password123"
    print(f"1. Registering User A ({user_a})...")

    token_a = register_and_login(user_a, password)
    if not token_a:
        return
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Create New Organization
    print("2. Creating New Organization 'Test Org A'...")
    try:
        res = requests.post(
            f"{BASE_URL}/api/organizations/",
            json={"name": "Test Org A", "owner_email": "admin@testorg.com"},
            headers=headers_a,
        )

        if res.status_code == 200:
            org_data = res.json()
            org_id = org_data["id"]
            print(f"   Success: Created Org {org_id}")

            # Verify User A is now admin of this org
            me_res = requests.get(f"{BASE_URL}/api/auth/me", headers=headers_a)
            me_data = me_res.json()
            if me_data["org_id"] == org_id and me_data["is_admin"]:
                print("   Success: User A is Admin of new Org.")
            else:
                print(f"   Failed: User A org/role mismatch: {me_data}")
        else:
            print(f"   Failed: {res.status_code} {res.text}")
            return
    except Exception as e:
        print(f"   Error: {e}")
        return

    # 3. Generate Invitation Code
    print("3. Generating Invitation Code...")
    invite_code = None
    try:
        res = requests.post(f"{BASE_URL}/api/organizations/invitations", headers=headers_a)
        if res.status_code == 200:
            invite_data = res.json()
            invite_code = invite_data["code"]
            print(f"   Success: Generated code {invite_code}")
        else:
            print(f"   Failed: {res.status_code} {res.text}")
            return
    except Exception as e:
        print(f"   Error: {e}")
        return

    # 4. Register User B (Joiner)
    user_b = "user_b_" + os.urandom(4).hex()
    print(f"4. Registering User B ({user_b})...")
    token_b = register_and_login(user_b, password)
    if not token_b:
        return
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Check User B's initial org (should be Default or None)
    me_res = requests.get(f"{BASE_URL}/api/auth/me", headers=headers_b)
    initial_org = me_res.json().get("org_id")
    print(f"   User B initial Org: {initial_org}")

    # 5. Join Organization using Code
    print(f"5. User B joining Org using code {invite_code}...")
    try:
        res = requests.post(
            f"{BASE_URL}/api/organizations/join",
            json={"invite_code": invite_code},
            headers=headers_b,
        )

        if res.status_code == 200:
            print("   Success: Joined Organization.")

            # Verify User B is now in the new Org
            me_res = requests.get(f"{BASE_URL}/api/auth/me", headers=headers_b)
            me_data = me_res.json()
            if me_data["org_id"] == org_id:
                print(f"   Success: User B is now in Org {org_id}")
            else:
                print(f"   Failed: User B org mismatch: {me_data['org_id']}")
        else:
            print(f"   Failed: {res.status_code} {res.text}")
            return
    except Exception as e:
        print(f"   Error: {e}")
        return


def register_and_login(username, password):
    try:
        res = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={"username": username, "email": f"{username}@example.com", "password": password},
        )
        if res.status_code == 200:
            return res.json()["access_token"]
        elif res.status_code == 400:
            # Login
            res = requests.post(
                f"{BASE_URL}/api/auth/token", data={"username": username, "password": password}
            )
            res.raise_for_status()
            return res.json()["access_token"]
        else:
            print(f"   Failed to register/login {username}: {res.status_code} {res.text}")
            return None
    except Exception as e:
        print(f"   Error: {e}")
        return None


if __name__ == "__main__":
    run_test()
