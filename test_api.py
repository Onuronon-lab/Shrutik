#!/usr/bin/env python3
"""
Quick script to test the script management API authentication flow.
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_admin_api_flow():
    """Test the complete admin authentication and API flow."""
    
    # 1. Register an admin user
    print("1. Registering admin user...")
    register_data = {
        "name": "Admin User",
        "email": "admin@example.com",
        "password": "adminpassword123",
        "role": "admin"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
    if response.status_code == 201:
        print("✅ User registered successfully")
    elif response.status_code == 400 and "Email already registered" in response.text:
        print("ℹ️  Admin user already exists, continuing...")
    else:
        print(f"❌ Registration failed: {response.status_code} - {response.text}")
        return

    print("\n2. Logging in as admin...")
    login_data = {
        "email": "admin@example.com",
        "password": "adminpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return
    
    token_data = response.json()
    access_token = token_data["access_token"]
    print("✅ Login successful, got access token")

    print("\n3. Testing random script endpoint...")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(f"{BASE_URL}/api/scripts/random?duration_category=2_minutes", headers=headers)
    if response.status_code == 404:
        print("ℹ️  No scripts found (expected if database is empty)")
        print("   Response:", response.json())
    elif response.status_code == 200:
        print("✅ Got random script successfully")
        print("   Script:", response.json())
    else:
        print(f"❌ Random script request failed: {response.status_code} - {response.text}")

    print("\n4. Testing user info endpoint...")
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    if response.status_code == 200:
        user_info = response.json()
        print("✅ Got user info successfully")
        print(f"   User: {user_info['name']} ({user_info['email']}) - Role: {user_info['role']}")
    else:
        print(f"❌ User info request failed: {response.status_code} - {response.text}")

    print("\n5. Testing script management endpoints...")
    
    response = requests.get(f"{BASE_URL}/api/scripts/", headers=headers)
    if response.status_code == 200:
        scripts_data = response.json()
        print(f"✅ Listed scripts successfully - Total: {scripts_data['total']}")
    else:
        print(f"❌ List scripts failed: {response.status_code} - {response.text}")

    response = requests.get(f"{BASE_URL}/api/scripts/statistics", headers=headers)
    if response.status_code == 200:
        stats = response.json()
        print(f"✅ Got script statistics - Total scripts: {stats['total_scripts']}")
    else:
        print(f"❌ Script statistics failed: {response.status_code} - {response.text}")

    print("\n6. Testing voice recording endpoints...")

    response = requests.get(f"{BASE_URL}/api/recordings/", headers=headers)
    if response.status_code == 200:
        recordings_data = response.json()
        print(f"✅ Listed user recordings successfully - Total: {recordings_data['total']}")
    else:
        print(f"❌ List recordings failed: {response.status_code} - {response.text}")

    response = requests.get(f"{BASE_URL}/api/recordings/admin/all", headers=headers)
    if response.status_code == 200:
        all_recordings = response.json()
        print(f"✅ Listed all recordings successfully - Total: {all_recordings['total']}")
    else:
        print(f"❌ List all recordings failed: {response.status_code} - {response.text}")

    response = requests.get(f"{BASE_URL}/api/recordings/admin/statistics", headers=headers)
    if response.status_code == 200:
        rec_stats = response.json()
        print(f"✅ Got recording statistics - Total recordings: {rec_stats['total_recordings']}")
        print(f"   Duration: {rec_stats['total_duration_hours']} hours")
    else:
        print(f"❌ Recording statistics failed: {response.status_code} - {response.text}")

    print("\n7. Testing recording session creation...")

    response = requests.get(f"{BASE_URL}/api/scripts/random?duration_category=2_minutes", headers=headers)
    if response.status_code == 200:
        script = response.json()
        script_id = script['id']

        session_data = {
            "script_id": script_id,
            "language_id": script['language_id']
        }
        response = requests.post(f"{BASE_URL}/api/recordings/sessions", json=session_data, headers=headers)
        if response.status_code == 201:
            session = response.json()
            print(f"✅ Created recording session successfully")
            print(f"   Session ID: {session['session_id']}")
            print(f"   Script: {script['text'][:50]}...")
        else:
            print(f"❌ Create recording session failed: {response.status_code} - {response.text}")
    else:
        print("ℹ️  No scripts available for session creation test")
    
    print(f"\n🎉 Complete API testing finished!")
    print(f"💡 Your admin access token: {access_token}")
    print(f"💡 Use this in your requests: -H 'Authorization: Bearer {access_token}'")
    print(f"\n📋 Available endpoints to test:")
    print(f"   Scripts: GET /api/scripts/, POST /api/scripts/, GET /api/scripts/statistics")
    print(f"   Recordings: GET /api/recordings/, POST /api/recordings/sessions")
    print(f"   Admin: GET /api/recordings/admin/all, GET /api/recordings/admin/statistics")

if __name__ == "__main__":
    test_admin_api_flow()