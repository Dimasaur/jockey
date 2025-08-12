# API Setup Guide

This guide helps you set up all the APIs needed for the Investor Research Prototype.

## Quick Start

1. **Copy environment template:**
   ```bash
   cp env_template.txt .env
   ```

2. **Fill in your API keys in the `.env` file**

3. **Run the API tests:**
   ```bash
   python test_apis.py
   ```

## API Setup Instructions

### 1. OpenAI API
- **Purpose**: Natural language query processing
- **Setup**:
  1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
  2. Create a new API key
  3. Add to `.env`: `OPENAI_API_KEY=your_key_here`

### 2. Airtable API
- **Purpose**: Access to existing investor database
- **Setup**:
  1. Go to [Airtable Account](https://airtable.com/account)
  2. Generate an API key
  3. Find your Base ID in the URL: `https://airtable.com/appXXXXXXXXXXXXXX`
  4. Add to `.env`:
     ```
     AIRTABLE_API_KEY=your_key_here
     AIRTABLE_BASE_ID=your_base_id_here
     ```

### 3. Apollo.io API
- **Purpose**: External investor data enrichment
- **Setup**:
  1. Go to [Apollo.io API Settings](https://app.apollo.io/#/settings/integrations/api)
  2. Generate an API key
  3. Add to `.env`: `APOLLO_API_KEY=your_key_here`

### 4. Google Services (Gmail & Calendar)
- **Purpose**: Email drafting and calendar availability
- **Setup**:
  1. Go to [Google Cloud Console](https://console.cloud.google.com/)
  2. Create a new project or select existing one
  3. Enable Gmail API and Google Calendar API
  4. Go to Credentials → Create Credentials → OAuth 2.0 Client IDs
  5. Choose "Desktop application"
  6. Download the JSON file and rename it to `credentials.json`
  7. Place it in the project directory
  8. Run: `python setup_google_oauth.py`

## Testing Your Setup

Run the comprehensive API test:
```bash
python test_apis.py
```

This will test all APIs and provide detailed feedback on what's working and what needs to be fixed.

## Troubleshooting

### Missing API Keys
- Check that your `.env` file exists and contains the correct API keys
- Verify API keys are valid and have proper permissions

### Google OAuth Issues
- Ensure `credentials.json` is in the project directory
- Delete `token.pickle` if you need to re-authenticate
- Check that Gmail and Calendar APIs are enabled in Google Cloud Console

### Rate Limits
- Some APIs have rate limits that may cause temporary failures
- Wait a few minutes and retry the tests

## File Structure
```
Jockey/
├── .env                    # Your API keys (create from env_template.txt)
├── credentials.json        # Google OAuth credentials (download from Google Cloud)
├── token.pickle           # Google OAuth tokens (created automatically)
├── test_apis.py           # API testing script
├── setup_google_oauth.py  # Google OAuth setup helper
└── env_template.txt       # Environment variables template
```
