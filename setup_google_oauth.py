#!/usr/bin/env python3
"""
Google OAuth Setup Script

This script helps you set up OAuth authentication for Google services (Gmail, Calendar).
It handles the OAuth flow, token refresh, and credential persistence.

Prerequisites:
- credentials.json file from Google Cloud Console
- Gmail API and Google Calendar API enabled in your project

Output:
- token.pickle file with persistent credentials
"""

import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar.readonly'
]

def setup_google_oauth():
    """Set up Google OAuth authentication for Gmail and Calendar access.

    This function:
    1. Checks for existing valid credentials in token.pickle
    2. Refreshes expired tokens if possible
    3. Initiates OAuth flow if no valid credentials exist
    4. Saves credentials to token.pickle for future use

    Returns:
        bool: True if setup successful, False if credentials.json missing

    Raises:
        FileNotFoundError: If credentials.json is not present
        OAuthError: If OAuth flow fails
    """
    creds = None

    # The file token.pickle stores the user's access and refresh tokens.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Check if credentials.json exists
            if not os.path.exists('credentials.json'):
                print("❌ credentials.json not found!")
                print("\n📋 To set up Google OAuth:")
                print("1. Go to https://console.cloud.google.com/")
                print("2. Create a new project or select existing one")
                print("3. Enable Gmail API and Google Calendar API")
                print("4. Go to 'Credentials' → 'Create Credentials' → 'OAuth 2.0 Client IDs'")
                print("5. Choose 'Desktop application'")
                print("6. Download the JSON file and rename it to 'credentials.json'")
                print("7. Place it in this directory")
                return False

            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    print("✅ Google OAuth setup complete!")
    print("   You can now run: python test_apis.py")
    return True

if __name__ == '__main__':
    setup_google_oauth()
