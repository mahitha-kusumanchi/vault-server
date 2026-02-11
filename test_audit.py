
import requests
import os
import json
import time

BASE_URL = "http://localhost:8000"

def test_audit_logs():
    print("=" * 60)
    print("Audit Log Test Flow")
    print("=" * 60)
    
    # Register a user
    username = f"audittest_{os.urandom(4).hex()}"
    password = "TestPassword123!"
    
    # We need to simulate the hashing done in client
    # For this test we can just send dummy verifier since we are testing logs
    # But server verification might fail if we don't do it right.
    # Let's import the hashing function if possible or just use what we have.
    # Since we can't easily import client code here without path hacking, 
    # we will rely on server just accepting the register call.
    
    print(f"Registering user: {username}")
    r = requests.post(
        f"{BASE_URL}/register",
        json={
            "username": username,
            "salt": "dummy_salt",
            "verifier": "dummy_verifier",
        },
    )
    if r.status_code != 200:
        print(f"Registration failed: {r.text}")
        return

    # Login to get token
    print("Logging in...")
    r = requests.post(
        f"{BASE_URL}/login",
        json={"username": username, "verifier": "dummy_verifier"},
    )
    if r.status_code != 200:
        print(f"Login failed: {r.text}")
        return
    token = r.json()["token"]

    # Perform some actions
    print("Performing actions...")
    
    # Access vault (VAULT_ACCESS)
    requests.get(f"{BASE_URL}/vault", headers={"Authorization": token})
    
    # Update vault (VAULT_UPDATE)
    requests.post(
        f"{BASE_URL}/vault", 
        headers={"Authorization": token},
        json={"blob": {"entries": []}}
    )
    
    # Give some time for logs to be written (sync, but just in case)
    time.sleep(1)
    
    # Retrieve Logs
    print("Fetching logs...")
    r = requests.get(f"{BASE_URL}/logs", headers={"Authorization": token})
    if r.status_code != 200:
        print(f"Failed to fetch logs: {r.text}")
        return
        
    logs = r.json()["logs"]
    print(f"\nRetrieved {len(logs)} log entries:")
    
    expected_actions = ["REGISTER", "LOGIN", "VAULT_ACCESS", "VAULT_UPDATE"]
    found_actions = []
    
    for log in logs:
        print(f"- {log['timestamp']} | {log['action']} | {log['details']}")
        found_actions.append(log['action'])
        
    # Verify we found the expected actions
    # Note: logs are sorted by timestamp desc, so order might be reversed in list
    missing = [action for action in expected_actions if action not in found_actions]
    
    if not missing:
        print("\nSUCCESS: All expected actions were logged.")
    else:
        print(f"\nFAILURE: Missing log entries for: {missing}")

if __name__ == "__main__":
    try:
        test_audit_logs()
    except Exception as e:
        print(f"Error: {e}")
