"""
FastAPI entrypoint for Jockey AI

Endpoints:
- GET /health: readiness probe
- POST /orchestrate: run the end-to-end investor workflow
- GET /runs/{run_id}: fetch status/result of a previous run
- POST /search/companies: search for companies using Apollo
- POST /search/people: search for people using Apollo
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models.schemas import (
    CompanySearchQuery,
    PersonSearchQuery,
    OrchestrateRequest,
    OrchestrateResponse,
)
from services.orchestrator import Orchestrator
from services.apollo import ApolloService


app = FastAPI(title="Jockey AI - Investor Research API")

# Permissive CORS for local testing and simple client integrations.
# Tighten in production to specific origins and headers.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton instances used by all requests.
orchestrator = Orchestrator()
apollo_service = ApolloService()


@app.get("/health")
def health() -> dict:
    """Lightweight readiness probe for the API server."""
    return {"status": "ok"}


@app.post("/orchestrate", response_model=OrchestrateResponse)
def orchestrate(req: OrchestrateRequest) -> OrchestrateResponse:
    """Execute the investor research workflow.

    Input: OrchestrateRequest with natural-language query and options.
    Output: OrchestrateResponse containing run_id, status, and artifacts
    (parsed query, investors, CSV path, email draft, availability, project id).
    """
    return orchestrator.orchestrate(req)


@app.get("/runs/{run_id}")
def get_run(run_id: str):
    """Fetch a previously created run by its run_id."""
    run = orchestrator.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@app.post("/search/companies")
def search_companies(query: CompanySearchQuery):
    """Search for companies using Apollo's API.

    Supports flexible search criteria including:
    - Keywords, industry, location
    - Employee count, revenue, founded year ranges
    - Technologies, funding stage
    """
    # Use max_results from query, default to 50
    max_results = query.max_results or 50
    companies = apollo_service.search_companies(query, max_results)
    return {
        "query": query,
        "max_results": max_results,
        "total_found": len(companies),
        "companies": companies
    }


@app.post("/search/people")
def search_people(query: PersonSearchQuery):
    """Search for people/contacts using Apollo's API.

    Supports search by:
    - Job title, seniority level, department
    - Company name, location
    """
    # Use max_results from query, default to 50
    max_results = query.max_results or 50
    people = apollo_service.search_people(query, max_results)
    return {
        "query": query,
        "max_results": max_results,
        "total_found": len(people),
        "people": people
    }
