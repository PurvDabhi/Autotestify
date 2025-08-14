#!/usr/bin/env python3
"""
Quick script to test GitHub token validity
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_github_token():
    token = os.getenv('GITHUB_TOKEN')
    
    if not token:
        print("[ERROR] No GITHUB_TOKEN found in .env file")
        return False
    
    print(f"[INFO] Testing GitHub token: {token[:12]}...")
    
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    try:
        response = requests.get('https://api.github.com/user', headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            print("[SUCCESS] GitHub token is valid!")
            print(f"   User: {user_data.get('login', 'Unknown')}")
            print(f"   Rate limit remaining: {response.headers.get('X-RateLimit-Remaining', 'Unknown')}")
            return True
        elif response.status_code == 401:
            print("[ERROR] GitHub token is invalid or expired")
            print("   Error:", response.json().get('message', 'Bad credentials'))
            return False
        else:
            print(f"[WARNING] Unexpected response: {response.status_code}")
            print("   Response:", response.text)
            return False
            
    except Exception as e:
        print(f"[ERROR] Error testing token: {e}")
        return False

if __name__ == "__main__":
    print("=== GitHub Token Validation ===")
    is_valid = test_github_token()
    
    if not is_valid:
        print("\n[FIX] To fix this:")
        print("1. Go to https://github.com/settings/tokens")
        print("2. Click 'Generate new token (classic)'")
        print("3. Select scopes: 'repo', 'read:user'")
        print("4. Copy the new token")
        print("5. Update GITHUB_TOKEN in your .env file")
        print("6. Restart the application")