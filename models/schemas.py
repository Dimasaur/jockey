from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RunStatus(str, Enum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class TicketSize(BaseModel):
    minimum: Optional[float] = Field(None, description="Minimum ticket size in USD")
    maximum: Optional[float] = Field(None, description="Maximum ticket size in USD")


class ParsedQuery(BaseModel):
    industry: Optional[str] = None
    location: Optional[str] = None
    ticket_size: Optional[TicketSize] = None
    company_stage: Optional[str] = None
    source_project: Optional[str] = None
    new_project: Optional[str] = None
    investor_type: Optional[str] = None
    requirements: Optional[List[str]] = None
    timeframe: Optional[str] = None
    portfolio_focus: Optional[str] = None
    exit_strategy: Optional[str] = None
    _metadata: Optional[Dict[str, Any]] = None


class Investor(BaseModel):
    id: Optional[str] = None
    name: str
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    investor_type: Optional[str] = None
    industry_focus: Optional[str] = None
    location: Optional[str] = None
    ticket_min: Optional[float] = None
    ticket_max: Optional[float] = None
    is_warm_lead: bool = False
    source: Optional[str] = None


class EmailDraft(BaseModel):
    subject: str
    body_text: str
    body_html: Optional[str] = None


class AvailabilitySlot(BaseModel):
    start_iso: str
    end_iso: str
    timezone: Optional[str] = None


class OrchestrateOptions(BaseModel):
    dry_run: bool = True
    max_results: int = 50
    include_email_draft: bool = True
    include_calendar: bool = True
    create_project: bool = True


class OrchestrateRequest(BaseModel):
    query: str
    options: OrchestrateOptions = Field(default_factory=OrchestrateOptions)


class OrchestrateResult(BaseModel):
    parsed_query: Optional[ParsedQuery] = None
    investors: List[Investor] = Field(default_factory=list)
    csv_path: Optional[str] = None
    email_draft: Optional[EmailDraft] = None
    availability: Optional[List[AvailabilitySlot]] = None
    project_id: Optional[str] = None


class OrchestrateRun(BaseModel):
    run_id: str
    status: RunStatus
    error_message: Optional[str] = None
    steps: Dict[str, RunStatus] = Field(default_factory=dict)
    result: Optional[OrchestrateResult] = None
    created_at_iso: str
    updated_at_iso: str


class OrchestrateResponse(BaseModel):
    run_id: str
    status: RunStatus
    result: Optional[OrchestrateResult] = None
    error_message: Optional[str] = None
