# MCP Connector Setup Guide

## Overview

Morning Brief AGI uses Google Workspace APIs to fetch data from Gmail, Calendar, and Tasks. This guide will help you set up the OAuth credentials needed for MCP connectors.

## 🎯 What You Get

Once configured, the system will automatically fetch:
- **Gmail**: Unread and important emails
- **Google Calendar**: Today's and tomorrow's events
- **Google Tasks**: Pending and due tasks

All data is normalized into a uniform format and ready for ranking and synthesis.

## 📋 Prerequisites

- Google account with Gmail, Calendar, and Tasks
- Google Cloud Console access
- Python 3.11+

## 🔧 Setup Steps

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project: "Morning Brief AGI"
3. Note the project ID

### 2. Enable APIs

Enable these APIs for your project:

```
1. Gmail API
2. Google Calendar API
3. Google Tasks API
```

Steps:
- Go to "APIs & Services" → "Library"
- Search for each API
- Click "Enable"

### 3. Create OAuth 2.0 Credentials

#### Configure OAuth Consent Screen

1. Go to "APIs & Services" → "OAuth consent screen"
2. Choose "External" (unless you have Google Workspace)
3. Fill in:
   - App name: "Morning Brief AGI"
   - User support email: your email
   - Developer contact: your email
4. Click "Save and Continue"
5. Add scopes:
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/calendar.readonly`
   - `https://www.googleapis.com/auth/tasks.readonly`
6. Add test users (your Google account email)
7. Save

#### Create Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Application type: "Desktop app"
4. Name: "Morning Brief Desktop Client"
5. Click "Create"
6. Download JSON file

### 4. Set Up Credentials Directory

```bash
# Create credentials directory
mkdir -p backend/credentials

# Move downloaded file
mv ~/Downloads/client_secret_*.json backend/credentials/gmail_credentials.json

# Copy for other services (they can share the same OAuth app)
cp backend/credentials/gmail_credentials.json backend/credentials/calendar_credentials.json
cp backend/credentials/gmail_credentials.json backend/credentials/tasks_credentials.json
```

### 5. Run First-Time Authentication

```bash
cd backend

# Set up environment
export GMAIL_CREDENTIALS_PATH="credentials/gmail_credentials.json"
export GMAIL_TOKEN_PATH="credentials/gmail_token.json"
export CALENDAR_CREDENTIALS_PATH="credentials/calendar_credentials.json"
export CALENDAR_TOKEN_PATH="credentials/calendar_token.json"
export TASKS_CREDENTIALS_PATH="credentials/tasks_credentials.json"
export TASKS_TOKEN_PATH="credentials/tasks_token.json"

# Test Gmail connector
python -c "
import asyncio
from packages.connectors import GmailConnector

async def test():
    connector = GmailConnector()
    connected = await connector.connect()
    print(f'Gmail connected: {connected}')
    if connected:
        result = await connector.fetch(limit=5)
        print(f'Fetched {len(result.items)} emails')

asyncio.run(test())
"
```

This will:
1. Open a browser window
2. Ask you to sign in with Google
3. Request permission to access Gmail (read-only)
4. Save the token to `backend/credentials/gmail_token.json`

**Repeat for Calendar and Tasks:**

```bash
# Test Calendar connector
python -c "
import asyncio
from packages.connectors import CalendarConnector

async def test():
    connector = CalendarConnector()
    connected = await connector.connect()
    print(f'Calendar connected: {connected}')
    if connected:
        result = await connector.fetch(limit=5)
        print(f'Fetched {len(result.items)} events')

asyncio.run(test())
"

# Test Tasks connector
python -c "
import asyncio
from packages.connectors import TasksConnector

async def test():
    connector = TasksConnector()
    connected = await connector.connect()
    print(f'Tasks connected: {connected}')
    if connected:
        result = await connector.fetch(limit=5)
        print(f'Fetched {len(result.items)} tasks')

asyncio.run(test())
"
```

### 6. Update Docker Environment

Add to `.env`:

```bash
# MCP Connectors
MCP_GMAIL_ENABLED=true
MCP_CALENDAR_ENABLED=true
MCP_TASKS_ENABLED=true

# Credential paths (inside container)
GMAIL_CREDENTIALS_PATH=/app/credentials/gmail_credentials.json
GMAIL_TOKEN_PATH=/app/credentials/gmail_token.json
CALENDAR_CREDENTIALS_PATH=/app/credentials/calendar_credentials.json
CALENDAR_TOKEN_PATH=/app/credentials/calendar_token.json
TASKS_CREDENTIALS_PATH=/app/credentials/tasks_credentials.json
TASKS_TOKEN_PATH=/app/credentials/tasks_token.json
```

Update `docker-compose.yml` to mount credentials:

```yaml
  backend:
    volumes:
      - ./backend:/app
      - ./backend/credentials:/app/credentials  # Add this line
```

## 🧪 Testing Connectors

### Test Individual Connectors

```bash
cd backend

# Test Gmail
python -m packages.connectors.gmail

# Test Calendar
python -m packages.connectors.calendar

# Test Tasks
python -m packages.connectors.tasks
```

### Test via API

```bash
# Start backend
docker-compose up -d backend

# Trigger brief run (will use connectors)
curl -X POST http://localhost:8000/api/brief/run

# View results
curl http://localhost:8000/api/brief/latest | jq
```

## 📁 File Structure

After setup, you should have:

```
backend/
├── credentials/
│   ├── gmail_credentials.json      # OAuth client secrets
│   ├── gmail_token.json            # Access token (auto-generated)
│   ├── calendar_credentials.json
│   ├── calendar_token.json
│   ├── tasks_credentials.json
│   └── tasks_token.json
└── packages/
    ├── connectors/
    │   ├── gmail.py
    │   ├── calendar.py
    │   └── tasks.py
    └── normalizer/
        └── normalizer.py
```

## 🔒 Security Notes

1. **Never commit credentials to git**  
   The `.gitignore` already excludes `credentials/` directory

2. **Token refresh**  
   Tokens auto-refresh when expired (valid for 7 days by default)

3. **Read-only scopes**  
   All connectors use read-only permissions - they cannot send emails, delete events, or modify tasks

4. **Revoke access**  
   You can revoke access anytime at: https://myaccount.google.com/permissions

## 🐛 Troubleshooting

### "Credentials not found"

```bash
# Check file exists
ls -la backend/credentials/

# Check permissions
chmod 600 backend/credentials/*.json
```

### "Invalid grant" error

Token expired or invalid:

```bash
# Delete token and re-authenticate
rm backend/credentials/*_token.json
# Run test script again
```

### "Access denied" or "403"

1. Make sure APIs are enabled in Google Cloud Console
2. Check OAuth consent screen configuration
3. Ensure your email is added as a test user
4. Check scopes are correctly configured

### "Quota exceeded"

Google APIs have daily quotas:
- Gmail: 1 billion quota units/day (reading ~25,000 emails)
- Calendar: 1 million requests/day
- Tasks: 50,000 requests/day

For development, these are more than enough.

## 📊 Connector Features

### Gmail Connector
- Fetches unread and important emails
- Filters by timestamp (only new emails)
- Extracts subject, sender, snippet, body
- Supports custom queries
- **Limit:** 50 emails per fetch (configurable)

### Calendar Connector
- Fetches upcoming events (next 2 days by default)
- Includes all-day events
- Extracts attendees, location, meeting links
- Calculates duration
- **Limit:** 50 events per fetch

### Tasks Connector
- Fetches incomplete tasks from all lists
- Filters by due date
- Marks overdue tasks
- Organizes by priority
- **Limit:** 50 tasks per fetch

## 🚀 Next Steps

Once connectors are working:

1. **Phase 4:** Memory System - Implement novelty detection
2. **Phase 5:** Ranking - Add importance scoring
3. **Phase 6:** Synthesis - Generate "why it matters"

## 💡 Tips

- **Test in development first** before running in production
- **Start with Gmail only** to verify OAuth flow
- **Monitor API usage** in Google Cloud Console
- **Set reasonable fetch limits** to avoid quota issues

---

**Need help?** Check the troubleshooting section or open an issue!
