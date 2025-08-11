
# Investor Research Prototype
Project: Jockey AI
Author: Dima (solo-founder)
Kick-off date: 11 Aug 2025

## Overview
AI-powered investor research tool that processes natural language queries to generated targeted investor lists, create project records, and draft client communications.

## Tech Stack
| Step | Tool | Description |
|------|------|-------------|
| Data Sources | Airtable, Crunchbase, Gmail, Google Calendar | Original sources of data |
| Data extraction | Fivetran | Handles API calls, rate limiting and incremental updates |
| Data Storage | PostgreSQL | Storage for landing and aggregating data |
| ETL orchestration | Apache Airflow | Orchestrating the entire pipeline |
| API management | FastAPI | Serves data via REST endpoints |
| NLP | OpenAI GPT API | Converts natural language into queries |

## Prototype scope
1. Generate investor lists from natural language queries using Airtable + Crunchbase APIs
2. Export CSV and draft client emails with calendar availability
3. Create Airtable projects and mark warm leads from previous projects

### Example Query
> "Generate a list of Investors that invest in automotive space in Germany, I just need companies names, website and LinkedIn URL. Take investors from Project ENIGMA and add additional investors from Crunchbase that do tickets between 5-10 million and have a dry powder available. "

## Architecture

4 directories, 14 files
.
├── .cursorrules
├── .env
├── main.py
├── models
│   └── schemas.py
├── prototype_scope.md
├── README.md
├── requirements.txt
├── services
│   ├── airtable.py
│   ├── calendar.py
│   ├── crunchbase.py
│   ├── gmail.py
│   └── openai_service.py
└── utils
    └── csv_export.py

4 directories, 13 files
