from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models.schemas import OrchestrateRequest, OrchestrateResponse
from services.orchestrator import Orchestrator


app = FastAPI(title="Jockey AI - Investor Research API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = Orchestrator()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/orchestrate", response_model=OrchestrateResponse)
def orchestrate(req: OrchestrateRequest) -> OrchestrateResponse:
    return orchestrator.orchestrate(req)


@app.get("/runs/{run_id}")
def get_run(run_id: str):
    run = orchestrator.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run
