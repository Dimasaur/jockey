"""
Data models for the Jockey AI investor research workflow

Core models:
- RunStatus: status of an orchestration run or individual step
- TicketSize: investment ticket size range in USD
- ParsedQuery: structured representation of natural language input
- Investor: unified investor record from any source
- EmailDraft: generated email content for client communication
- AvailabilitySlot: calendar time slot for meeting scheduling
- OrchestrateOptions: configuration options for the orchestration workflow
- OrchestrateRequest/Response: API contract for the main workflow
- OrchestrateRun: persisted run state with step tracking
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RunStatus(str, Enum):
    """Status of an orchestration run or individual step."""
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class TicketSize(BaseModel):
    """Investment ticket size range in USD."""
    minimum: Optional[float] = Field(None, description="Minimum ticket size in USD")
    maximum: Optional[float] = Field(None, description="Maximum ticket size in USD")


class ParsedQuery(BaseModel):
    """Structured representation of a natural language investor query.

    Fields are populated based on what the OpenAI parser detects in the input.
    """
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
    """Unified investor record from Airtable, Apollo, or other sources."""
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
    """Generated email content for client communication."""
    subject: str
    body_text: str
    body_html: Optional[str] = None


class AvailabilitySlot(BaseModel):
    """Calendar time slot for meeting scheduling."""
    start_iso: str
    end_iso: str
    timezone: Optional[str] = None


class OrchestrateOptions(BaseModel):
    """Configuration options for the orchestration workflow."""
    dry_run: bool = True
    max_results: int = 50
    include_email_draft: bool = True
    include_calendar: bool = True
    create_project: bool = True


class OrchestrateRequest(BaseModel):
    """API request to start an investor research workflow."""
    query: str
    options: OrchestrateOptions = Field(default_factory=OrchestrateOptions)


class OrchestrateResult(BaseModel):
    """Complete output artifacts from a successful orchestration run."""
    parsed_query: Optional[ParsedQuery] = None
    investors: List[Investor] = Field(default_factory=list)
    csv_path: Optional[str] = None
    email_draft: Optional[EmailDraft] = None
    availability: Optional[List[AvailabilitySlot]] = None
    project_id: Optional[str] = None


class OrchestrateRun(BaseModel):
    """Persisted run state with step-by-step tracking and final results."""
    run_id: str
    status: RunStatus
    error_message: Optional[str] = None
    steps: Dict[str, RunStatus] = Field(default_factory=dict)
    result: Optional[OrchestrateResult] = None
    created_at_iso: str
    updated_at_iso: str


class OrchestrateResponse(BaseModel):
    """API response containing run status and optional results."""
    run_id: str
    status: RunStatus
    result: Optional[OrchestrateResult] = None
    error_message: Optional[str] = None
