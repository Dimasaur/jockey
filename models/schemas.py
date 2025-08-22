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


class CompanySearchQuery(BaseModel):
    """Structured representation of a general company search query."""
    keywords: Optional[str] = None
    industry: Optional[str] = None
    industries: Optional[List[str]] = None
    location: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    employee_count_min: Optional[int] = None
    employee_count_max: Optional[int] = None
    revenue_min: Optional[float] = None
    revenue_max: Optional[float] = None
    founded_year_min: Optional[int] = None
    founded_year_max: Optional[int] = None
    technologies: Optional[List[str]] = None
    funding_stage: Optional[str] = None
    max_results: Optional[int] = 50
    _metadata: Optional[Dict[str, Any]] = None


class PersonSearchQuery(BaseModel):
    """Structured representation of a person/contact search query."""
    job_title: Optional[str] = None
    seniority_level: Optional[str] = None
    department: Optional[str] = None
    company_name: Optional[str] = None
    location: Optional[str] = None
    max_results: Optional[int] = 50
    _metadata: Optional[Dict[str, Any]] = None


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


class Company(BaseModel):
    """General company record from Apollo or other sources."""
    id: Optional[str] = None
    name: str
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    industries: Optional[List[str]] = None
    location: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    employee_count: Optional[int] = None
    employee_range: Optional[str] = None
    revenue: Optional[float] = None
    revenue_range: Optional[str] = None
    founded_year: Optional[int] = None
    technologies: Optional[List[str]] = None
    funding_stage: Optional[str] = None
    keywords: Optional[List[str]] = None
    source: Optional[str] = None


class Person(BaseModel):
    """Person/contact record from Apollo."""
    id: Optional[str] = None
    name: str
    title: Optional[str] = None
    seniority_level: Optional[str] = None
    department: Optional[str] = None
    company_id: Optional[str] = None
    company_name: Optional[str] = None
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    location: Optional[str] = None
    source: Optional[str] = None


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
