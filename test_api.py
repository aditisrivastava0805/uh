# test_api.py (updated)
import os
import requests
from dotenv import load_dotenv
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
load_dotenv()

# Get the API token
api_token = os.getenv("LLM_API_TOKEN")
print(f"API Token loaded: {'Yes' if api_token else 'No'}")
if api_token:
    print(f"Token length: {len(api_token)}")
    print(f"Token preview: {api_token[:10]}...")

# Test the API endpoint
api_url = "https://gateway.eli.gaia.gic.ericsson.se/api/v1/llm/generate"

# Simple test payload
test_payload = {
    "prompt": "Hello, this is a test message.",
    "model": "Mistral-12b",
    "max_new_tokens": 50,
    "temperature": 0.1
}

# Headers with API token
headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json"
}

print(f"\nTesting API connection to: {api_url}")

try:
    # Disable SSL verification
    response = requests.post(
        api_url, 
        json=test_payload, 
        headers=headers, 
        timeout=30,
        verify=False  # This bypasses SSL verification
    )
    print(f"Response status: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        print("✅ API is working!")
        print(f"Response: {response.text[:200]}...")
    else:
        print(f"❌ API returned error: {response.status_code}")
        print(f"Error details: {response.text}")
        
except requests.exceptions.ConnectionError as e:
    print(f"❌ Connection error: {e}")
except requests.exceptions.Timeout as e:
    print(f"❌ Timeout error: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")