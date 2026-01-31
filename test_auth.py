"""
Test script for email-only authentication
Run this after starting the server with: python run.py
"""
import requests
import json

BASE_URL = "http://localhost:5000/api/v1/auth"


def test_login(email):
    """Test email-only login (finds or creates user)"""
    print(f"\n=== Testing Login with {email} ===")
    data = {
        "email": email
    }
    response = requests.post(f"{BASE_URL}/login", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response


def test_get_current_user(session):
    """Test getting current user"""
    print("\n=== Testing Get Current User ===")
    response = requests.get(f"{BASE_URL}/me", cookies=session.cookies)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response


def test_signout(session):
    """Test sign out"""
    print("\n=== Testing Sign Out ===")
    response = requests.post(f"{BASE_URL}/signout", cookies=session.cookies)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response


if __name__ == "__main__":
    print("Testing Email-Only Authentication API")
    print("=" * 50)
    print("\nNOTE: This is MVP authentication - email only, no password")
    print("Anyone with an email can access that account")
    print("Suitable for local/personal use only\n")

    try:
        # Test login with first email (will create user if doesn't exist)
        print("\n--- First Login (creates user) ---")
        session1 = test_login("test@example.com")
        test_get_current_user(session1)

        # Test login with same email again (will find existing user)
        print("\n--- Second Login (finds existing user) ---")
        session2 = test_login("test@example.com")
        test_get_current_user(session2)

        # Test login with different email
        print("\n--- Login with different email ---")
        session3 = test_login("another@example.com")
        test_get_current_user(session3)

        # Test sign out
        test_signout(session3)

        # Verify sign out worked
        print("\n--- After Sign Out (should fail) ---")
        response = requests.get(f"{BASE_URL}/me", cookies=session3.cookies)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")

        print("\n" + "=" * 50)
        print("All tests completed!")

    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to server.")
        print("Make sure the server is running: python run.py")
