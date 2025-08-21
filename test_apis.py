"""
API connectivity test suite

This module tests connectivity and basic functionality for all external APIs
used by the Jockey AI investor research workflow.

Tests:
- OpenAI API: basic chat completion
- Airtable API: base access and table listing
- Apollo.io API: health endpoint
- Gmail API: profile access (requires OAuth setup)
- Google Calendar API: calendar listing (requires OAuth setup)

Usage:
    python test_apis.py
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_env_vars():
    """Check for required environment variables and provide guidance.

    Validates that all required API keys are present in the .env file
    and provides helpful links for obtaining missing credentials.

    Returns:
        bool: True if all required vars are present, False otherwise
    """
    required_vars = {
        'OPENAI_API_KEY': 'Get from https://platform.openai.com/api-keys',
        'AIRTABLE_API_KEY': 'Get from https://airtable.com/account',
        'AIRTABLE_BASE_ID': 'Found in your Airtable base URL',
        'APOLLO_API_KEY': 'Get from https://app.apollo.io/#/settings/integrations/api',
    }

    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"{var}: {description}")

    if missing_vars:
        print("⚠️  Missing environment variables in .env file:")
        for var in missing_vars:
            print(f"   {var}")
        print("\n💡 Create a .env file with these variables to test all APIs.")
        return False
    return True

def test_openai():
    """Test OpenAI API connectivity and basic functionality.

    Attempts a simple chat completion to verify the API key is valid
    and the service is accessible.

    Returns:
        bool: True if test passes, False otherwise
    """
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello, this is a test"}],
            max_tokens=100,
        )
        print("✅ OpenAI API: Working")
        print(f"Response: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"❌ OpenAI API: {e}")
        return False

def test_airtable():
    """Test Airtable API connectivity and basic functionality.

    Verifies API key and base ID are valid by attempting to list
    tables in the specified base.

    Returns:
        bool: True if test passes, False otherwise
    """
    try:
        from pyairtable import Api
        api_key = os.getenv('AIRTABLE_API_KEY')
        base_id = os.getenv('AIRTABLE_BASE_ID')

        if not api_key:
            print("❌ Airtable API: Missing AIRTABLE_API_KEY in .env")
            print("   Add: AIRTABLE_API_KEY=your_api_key_here")
            return False

        if not base_id:
            print("❌ Airtable API: Missing AIRTABLE_BASE_ID in .env")
            print("   Add: AIRTABLE_BASE_ID=your_base_id_here")
            return False

        api = Api(api_key)
        # Try to access the base to test connectivity
        base = api.base(base_id)
        # List tables to verify access
        tables = base.tables()
        print("✅ Airtable API: Working")
        print(f"Available tables: {[table.name for table in tables]}")
        return True
    except Exception as e:
        print(f"❌ Airtable API: {e}")
        return False

def test_apollo():
    """Test Apollo.io API connectivity and basic functionality.

    Tests the health endpoint to verify API key is valid and
    the service is accessible.

    Returns:
        bool: True if test passes, False otherwise
    """
    try:
        import requests
        api_key = os.getenv('APOLLO_API_KEY')

        if not api_key:
            print("❌ Apollo API: Missing APOLLO_API_KEY in .env")
            print("   Add: APOLLO_API_KEY=your_api_key_here")
            return False

        # Test basic API connectivity using same auth as the service
        headers = {
            'X-Api-Key': api_key,
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        # Simple test to get user info
        response = requests.get('https://api.apollo.io/v1/auth/health', headers=headers)
        response.raise_for_status()

        print("✅ Apollo API: Working")
        print(f"Status: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Apollo API: {e}")
        return False

def test_gmail():
    """Test Gmail API connectivity and basic functionality.

    Requires OAuth setup via setup_google_oauth.py. Tests by accessing
    the user's Gmail profile to verify credentials are valid.

    Returns:
        bool: True if test passes, False otherwise
    """
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from google.auth.transport.requests import Request
        import pickle
        import os.path

        # Check for credentials file
        creds = None
        token_path = 'token.pickle'

        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)

        # If no valid credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                print("❌ Gmail API: No valid credentials found.")
                print("   Run: python setup_google_oauth.py")
                return False

        # Build the Gmail service
        service = build('gmail', 'v1', credentials=creds)

        # Test by getting user profile
        profile = service.users().getProfile(userId='me').execute()
        print("✅ Gmail API: Working")
        print(f"Email: {profile.get('emailAddress')}")
        return True
    except Exception as e:
        print(f"❌ Gmail API: {e}")
        return False

def test_google_calendar():
    """Test Google Calendar API connectivity and basic functionality.

    Requires OAuth setup via setup_google_oauth.py. Tests by listing
    available calendars to verify credentials are valid.

    Returns:
        bool: True if test passes, False otherwise
    """
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from google.auth.transport.requests import Request
        import pickle
        import os.path

        # Check for credentials file
        creds = None
        token_path = 'token.pickle'

        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)

        # If no valid credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                print("❌ Google Calendar API: No valid credentials found.")
                print("   Run: python setup_google_oauth.py")
                return False

        # Build the Calendar service
        service = build('calendar', 'v3', credentials=creds)

        # Test by getting calendar list
        calendars = service.calendarList().list().execute()
        print("✅ Google Calendar API: Working")
        print(f"Available calendars: {len(calendars.get('items', []))}")
        return True
    except Exception as e:
        print(f"❌ Google Calendar API: {e}")
        return False

def test_all_apis():
    """Run all API tests and provide summary.

    Executes connectivity tests for all external APIs and provides
    a summary of working vs failed APIs with troubleshooting guidance.

    Returns:
        bool: True if all APIs work, False if any fail
    """
    print("🔍 Testing all APIs...\n")

    # Check environment variables first
    check_env_vars()
    print()

    results = {
        "OpenAI": test_openai(),
        "Airtable": test_airtable(),
        "Apollo": test_apollo(),
        "Gmail": test_gmail(),
        "Google Calendar": test_google_calendar()
    }

    print("\n" + "="*50)
    print("📊 API TEST SUMMARY")
    print("="*50)

    working_apis = []
    failed_apis = []

    for api_name, result in results.items():
        if result:
            working_apis.append(api_name)
            print(f"✅ {api_name}: Working")
        else:
            failed_apis.append(api_name)
            print(f"❌ {api_name}: Failed")

    print(f"\nWorking APIs: {len(working_apis)}/{len(results)}")
    if failed_apis:
        print(f"Failed APIs: {', '.join(failed_apis)}")
        print("\n💡 To fix failed APIs:")
        print("1. Check your .env file has the correct API keys")
        print("2. For Google services, run OAuth authentication")
        print("3. Verify API quotas and permissions")

    return all(results.values())

if __name__ == "__main__":
    """Main entry point: run all API connectivity tests."""
    test_all_apis()
