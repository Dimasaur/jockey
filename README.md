
# Investor Research Prototype
Project: Jockey AI
Author: Dima (solo-founder)
Kick-off date: 11 Aug 2025

## Overview
AI-powered investor research tool that processes natural language queries to generated targeted investor lists, create project records, and draft client communications.

## Tech Stack
| Step | Tool | Description |
|------|------|-------------|
| Data Sources | Airtable, Apollo.io, Gmail, Google Calendar | Original sources of data |
| Data extraction | Fivetran | Handles API calls, rate limiting and incremental updates |
| Data Storage | PostgreSQL | Storage for landing and aggregating data |
| ETL orchestration | Apache Airflow | Orchestrating the entire pipeline |
| API management | FastAPI | Serves data via REST endpoints |
| NLP | OpenAI GPT API | Converts natural language into queries |

## Prototype scope
1. Generate investor lists from natural language queries using Airtable + Apollo.io APIs
2. Export CSV and draft client emails with calendar availability
3. Create Airtable projects and mark warm leads from previous projects

### Example Query
> "Generate a list of Investors that invest in automotive space in Germany, I just need companies names, website and LinkedIn URL. Take investors from Project ENIGMA and add additional investors from Apollo.io that do tickets between 5-10 million and have a dry powder available. "

## Architecture
.
├── .cursorrules
├── .env
├── .gitignore
├── API_SETUP.md
├── env_template.txt
├── google_credentials.json
├── main.py
├── models
│   └── schemas.py
├── readme.md
├── requirements.txt
├── services
│   ├── airtable.py
│   ├── apollo.py
│   ├── calendar.py
│   ├── gmail.py
│   └── openai_service.py
├── setup_google_oauth.py
├── test_apis.py
├── token.pickle
└── utils
    └── csv_export.py

4 directories, 19 files

# Schema

## High-Level Workflow

Natural Language Query → AI Parser → Data Retrieval → Processing → Output Generation

## Detailed Flow Diagram

1. USER INPUT
   ↓
   "Generate automotive investors in Germany with 5-10M tickets from Project ENIGMA, create Project NEXUS"

2. OPENAI PARSING
   ↓
   {
     "industry": "automotive",
     "location": "Germany",
     "ticket_size": {"min": 5000000, "max": 10000000},
     "source_project": "ENIGMA",
     "new_project": "NEXUS",
     "requirements": ["dry powder available"]
   }

3. DATA RETRIEVAL (Parallel)
   ↓
   ┌─ Airtable Query ────────────┐    ┌─ Apollo.io Search ──────────┐
   │ • Search Project ENIGMA     │    │ • Industry: automotive       │
   │ • Filter by criteria        │    │ • Location: Germany          │
   │ • Mark as "warm leads"      │    │ • Ticket size: 5-10M         │
   │ • Get investor details      │    │ • Active investors only      │
   └─────────────────────────────┘    └──────────────────────────────┘

4. DATA PROCESSING
   ↓
   • Merge Airtable + Apollo results
   • Remove duplicates
   • Apply filters (ticket size, requirements)
   • Mark warm vs cold leads
   • Format for output

5. OUTPUT GENERATION (Parallel)
   ↓
   ┌─ CSV Export ────────────────┐    ┌─ Email Draft ───────────────┐    ┌─ Airtable Project ─────────┐
   │ • Company names             │    │ • Professional summary      │    │ • Create "Project NEXUS"    │
   │ • Websites                  │    │ • Calendar availability     │    │ • Add investor list         │
   │ • Investment focus          │    │ • Call scheduling           │    │ • Mark warm lead status     │
   │ • Ticket sizes              │    │ • Attachment reference      │    │ • Link to source data       │
   └─────────────────────────────┘    └──────────────────────────────┘    └─────────────────────────────┘


## Technical Architecture

### Core Components

┌─────────────────────────────────────────────────────────────┐
│                        FastAPI Server                       │
├─────────────────────────────────────────────────────────────┤
│  POST /api/generate-investors                               │
│  └─ Input: { "query": "natural language string" }          │
│  └─ Output: { "investors": [], "csv_path": "", "email": ""} │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                            │
├─────────────────────────────────────────────────────────────┤
│  OpenAIService     │  AirtableService  │  ApolloService     │
│  • parse_query()   │  • get_projects() │  • search_investors│
│  • generate_email()│  • create_project │  • filter_results  │
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
