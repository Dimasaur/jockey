"""
FastAPI entrypoint for Jockey AI

Endpoints:
- GET /health: readiness probe
- POST /orchestrate: run the end-to-end investor workflow
- GET /runs/{run_id}: fetch status/result of a previous run
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models.schemas import OrchestrateRequest, OrchestrateResponse
from services.orchestrator import Orchestrator


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

# Singleton orchestrator instance used by all requests.
orchestrator = Orchestrator()


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
