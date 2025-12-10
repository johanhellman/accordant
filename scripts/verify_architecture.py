
import requests
import os
import sqlite3
import sys

port = os.getenv("PORT", "8002")
BASE_URL = os.getenv("BASE_URL", f"http://localhost:{port}/api")

def check_db_exists(path):
    if os.path.exists(path):
        print(f"✅ Database found: {path}")
        return True
    else:
        print(f"❌ Database MISSING: {path}")
        return False

def check_table_has_rows(db_path, table, min_rows=1):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        if count >= min_rows:
            print(f"✅ Table '{table}' in {os.path.basename(db_path)} has {count} rows.")
            return True
        else:
            print(f"❌ Table '{table}' in {os.path.basename(db_path)} is empty (expected >= {min_rows}).")
            return False
    except Exception as e:
        print(f"❌ Error querying {table}: {e}")
        return False
    finally:
        conn.close()

def run_verification():
    print("--- Starting Architecture Verification ---")
    
    # 1. Check System DB exists
    system_db_path = "data/system.db"
    if not check_db_exists(system_db_path):
        sys.exit(1)

    # 2. Register New User/Org
    username = "verify_user_01"
    password = "password123"
    org_name = "Verification Org"
    
    print(f"\nRegistering user '{username}'...")
    response = requests.post(f"{BASE_URL}/auth/register", json={
        "username": username,
        "password": password,
        "mode": "create_org",
        "org_name": org_name
    })
    
    if response.status_code != 200:
        if "already registered" in response.text:
             print("User already exists, logging in instead.")
             response = requests.post(f"{BASE_URL}/auth/token", data={
                "username": username,
                "password": password
             })
        else:
            print(f"❌ Registration failed: {response.text}")
            sys.exit(1)
            
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get Org ID
    me_resp = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    org_id = me_resp.json()["org_id"]
    print(f"✅ Logged in as user. Org ID: {org_id}")
    
    # 3. Check Tenant DB exists (Lazy creation might mean it doesn't exist yet until we access it?)
    # Just registering created the folders, but usually get_tenant_session does the DB file creation
    # Let's hit an endpoint that uses storage to force creation
    
    print("\nCreating Conversation (Forces DB init)...")
    conv_resp = requests.post(f"{BASE_URL}/conversations", json={}, headers=headers)
    if conv_resp.status_code != 200:
        print(f"❌ Create conversation failed: {conv_resp.text}")
        sys.exit(1)
    
    conv_id = conv_resp.json()["id"]
    
    # NOW check Tenant DB
    tenant_db_path = f"data/organizations/{org_id}/tenant.db"
    if not check_db_exists(tenant_db_path):
        sys.exit(1)
        
    # Check if Conversations table exists and has row
    if not check_table_has_rows(tenant_db_path, "conversations"):
        sys.exit(1)

    # 4. Check Messages Table (Normalization verification)
    print("\nSending Message (Test Normalized Storage)...")
    # This might fail if LLM is not configured/mocked, but we just want to see if the User message gets saved first
    # The API saves user message BEFORE calling LLM
    try:
        msg_resp = requests.post(f"{BASE_URL}/conversations/{conv_id}/message", json={
            "content": "Hello World verification"
        }, headers=headers, timeout=5) # Short timeout as we might not have LLM keys
    except Exception:
        print("(Ignored LLM timeout/error, checking DB for user message persistence)")
    
    # Check messages table
    if not check_table_has_rows(tenant_db_path, "messages", min_rows=1):
        print("❌ Message not saved to new 'messages' table!")
        sys.exit(1)
        
    print("\n✅ VERIFICATION SUCCESSFUL: Multi-Tenant Architecture is Active")

if __name__ == "__main__":
    run_verification()
