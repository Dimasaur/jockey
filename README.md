
# Investor Research Prototype
Project: Jockey AI
Author: Dima (solo-founder)
Kick-off date: 11 Aug 2025

## Overview
AI-powered investor research tool that processes natural language queries to generate targeted investor lists, create project records, and draft client communications.

## Tech Stack
| Component | Technology | Description |
|-----------|------------|-------------|
| **API Framework** | FastAPI | Modern Python web framework for building REST APIs |
| **Natural Language Processing** | OpenAI GPT API | Converts natural language queries into structured data |
| **Data Sources** | Airtable API | Existing investor database and project management |
| **Data Sources** | Apollo.io API | External investor data and company information |
| **Email & Calendar** | Google APIs (Gmail, Calendar) | Email drafting and calendar availability |
| **Data Export** | CSV | Export investor lists to downloadable files |
| **Authentication** | OAuth 2.0 | Google services authentication |
| **Development** | Python 3.10+ | Core programming language |

## Prototype Scope
1. Generate investor lists from natural language queries using Airtable + Apollo.io APIs
2. Export CSV and draft client emails with calendar availability
3. Create Airtable projects and mark warm leads from previous projects

### Example Query
> "Generate a list of Investors that invest in automotive space in Germany, I just need companies names, website and LinkedIn URL. Take investors from Project ENIGMA and add additional investors from Apollo.io that do tickets between 5-10 million and have a dry powder available."

## Architecture

```
.
├── .env                          # Environment variables
├── main.py                       # FastAPI application entry point
├── models/
│   └── schemas.py               # Pydantic data models
├── services/
│   ├── airtable.py              # Airtable API integration
│   ├── apollo.py                # Apollo.io API integration
│   ├── gmail.py                 # Gmail API integration
│   ├── google_calendar.py       # Google Calendar API integration
│   ├── openai_service.py        # OpenAI GPT API integration
│   └── orchestrator.py          # Main workflow orchestration
├── utils/
│   └── csv_export.py            # CSV export utilities
├── setup_google_oauth.py        # Google OAuth setup script
├── test_apis.py                 # API connectivity testing
└── requirements.txt             # Python dependencies
```

## High-Level Workflow

Natural Language Query → AI Parser → Data Retrieval → Processing → Output Generation

## Detailed Flow Diagram

1. **USER INPUT**
   ```
   "Generate automotive investors in Germany with 5-10M tickets from Project ENIGMA, create Project NEXUS"
   ```

2. **OPENAI PARSING**
   ```json
   {
     "industry": "automotive",
     "location": "Germany",
     "ticket_size": {"minimum": 5000000, "maximum": 10000000},
     "source_project": "ENIGMA",
     "new_project": "NEXUS",
     "requirements": ["dry powder available"]
   }
   ```

3. **DATA RETRIEVAL (Parallel)**
   ```
   ┌─ Airtable Query ────────────┐    ┌─ Apollo.io Search ──────────┐
   │ • Search Project ENIGMA     │    │ • Industry: automotive       │
   │ • Filter by criteria        │    │ • Location: Germany          │
   │ • Mark as "warm leads"      │    │ • Ticket size: 5-10M         │
   │ • Get investor details      │    │ • Active investors only      │
   └─────────────────────────────┘    └──────────────────────────────┘
   ```

4. **DATA PROCESSING**
   ```
   • Merge Airtable + Apollo results
   • Remove duplicates
   • Apply filters (ticket size, requirements)
   • Mark warm vs cold leads
   • Format for output
   ```

5. **OUTPUT GENERATION (Parallel)**
   ```
   ┌─ CSV Export ────────────────┐    ┌─ Email Draft ───────────────┐    ┌─ Airtable Project ─────────┐
   │ • Company names             │    │ • Professional summary      │    │ • Create "Project NEXUS"    │
   │ • Websites                  │    │ • Calendar availability     │    │ • Add investor list         │
   │ • Investment focus          │    │ • Call scheduling           │    │ • Mark warm lead status     │
   │ • Ticket sizes              │    │ • Attachment reference      │    │ • Link to source data       │
   └─────────────────────────────┘    └──────────────────────────────┘    └─────────────────────────────┘
   ```

## API Endpoints

### Core Workflow
- `POST /orchestrate` - Execute the complete investor research workflow
- `GET /runs/{run_id}` - Get status and results of a workflow run

### Direct Search (New)
- `POST /search/companies` - Search for companies using Apollo.io
- `POST /search/people` - Search for people/contacts using Apollo.io

### Health Check
- `GET /health` - API health check
- `GET /docs` - Interactive API documentation

## Technical Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                        FastAPI Server                       │
├─────────────────────────────────────────────────────────────┤
│  POST /orchestrate                                          │
│  └─ Input: { "query": "natural language string" }          │
│  └─ Output: { "run_id": "uuid", "status": "running" }      │
│                                                             │
│  GET /runs/{run_id}                                        │
│  └─ Output: { "investors": [], "csv_path": "", "email": ""} │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                            │
├─────────────────────────────────────────────────────────────┤
│  OpenAIService     │  AirtableService  │  ApolloService     │
│  • parse_query()   │  • get_projects() │  • search_companies│
│  • generate_email()│  • create_project │  • search_people   │
│                    │  • mark_leads()   │                    │
├─────────────────────────────────────────────────────────────┤
│  GmailService      │  CalendarService  │  CSVService        │
│  • draft_email()   │  • get_availability│ • export_data()   │
│  • send_email()    │  • suggest_slots  │  • format_output() │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                               │
├─────────────────────────────────────────────────────────────┤
│  Airtable API      │  Apollo.io API    │  Google APIs       │
│  • Existing data   │  • External data  │  • Gmail/Calendar  │
│  • Project mgmt    │  • Fresh leads    │  • Authentication  │
└─────────────────────────────────────────────────────────────┘
```

## Setup & Installation

### Prerequisites
- Python 3.10+
- API keys for: OpenAI, Airtable, Apollo.io, Google (Gmail/Calendar)

### Quick Start
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and add your API keys
4. Run the server: `uvicorn main:app --host 127.0.0.1 --port 8000`
5. Access the API docs at: `http://127.0.0.1:8000/docs`

### Environment Variables
```bash
# OpenAI
OPENAI_API_KEY=your_openai_key

# Airtable
AIRTABLE_API_KEY=your_airtable_key
AIRTABLE_BASE_ID=your_base_id

# Apollo.io
APOLLO_API_KEY=your_apollo_key
APOLLO_ENABLE_MOCK=0  # Set to 1 for testing without API calls

# Google (for Gmail/Calendar)
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
```

## Usage Examples

### Basic Investor Search
```bash
curl -X POST "http://127.0.0.1:8000/orchestrate" \
  -H "Content-Type: application/json" \
  -d '{"query": "find automotive investors in Germany", "options": {"max_results": 10}}'
```

### Direct Company Search
```bash
curl -X POST "http://127.0.0.1:8000/search/companies" \
  -H "Content-Type: application/json" \
  -d '{"keywords": "tech startups", "industry": "Technology", "location": "San Francisco", "max_results": 5}'
```

### People Search
```bash
curl -X POST "http://127.0.0.1:8000/search/people" \
  -H "Content-Type: application/json" \
  -d '{"job_title": "CEO", "department": "Engineering", "location": "San Francisco", "max_results": 5}'
```

## Development

### Testing APIs
```bash
python test_apis.py
```

### Google OAuth Setup
```bash
python setup_google_oauth.py
```

### Mock Mode
Set `APOLLO_ENABLE_MOCK=1` in your `.env` file to use mock data for testing without making real API calls.

## Project Status
- ✅ Core workflow implementation
- ✅ Natural language query parsing
- ✅ Airtable integration
- ✅ Apollo.io integration (with mock mode)
- ✅ CSV export functionality
- ✅ Email drafting (placeholder)
- ✅ Calendar integration (placeholder)
- ✅ Project creation in Airtable
- 🔄 Real Apollo API filtering (in progress)
- 🔄 Google OAuth integration (in progress)
