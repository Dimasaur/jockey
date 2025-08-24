"""
Orchestrator service

Coordinates the end-to-end investor research workflow:
1) Parse natural language query (OpenAI)
2) Fetch existing investors (Airtable)
3) Fetch external investors (Apollo)
4) Merge, de-duplicate, and filter results
5) Export CSV
6) Draft email with calendar availability
7) Optionally create Airtable project (non-dry-run)

Runs are persisted as JSON files in ./runs so they can be polled via API.
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from models.schemas import (
    AvailabilitySlot,
    Company,
    EmailDraft,
    Investor,
    OrchestrateRequest,
    OrchestrateResponse,
    OrchestrateResult,
    OrchestrateRun,
    ParsedQuery,
    RunStatus,
    TicketSize,
)
from services.airtable import AirtableService
from services.apollo import ApolloService
from services.gmail import GmailService
from services.google_calendar import GoogleCalendarService
from services.openai_service import OpenAIService
from utils.csv_export import export_investors_to_csv


def _now_iso() -> str:
    """Return current UTC time in ISO 8601 format with trailing Z."""
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


class Orchestrator:
    """High-level coordinator for the investor workflow.

    Responsible for step sequencing, basic error handling, and simple run
    persistence on disk. Individual API specifics live in their services.
    """
    def __init__(self) -> None:
        self.openai_service = OpenAIService()
        self.airtable_service = AirtableService()
        self.apollo_service = ApolloService()
        self.gmail_service = GmailService()
        self.calendar_service = GoogleCalendarService()

        self.runs_dir = os.path.abspath(os.path.join(os.getcwd(), "runs"))
        os.makedirs(self.runs_dir, exist_ok=True)

    # -------------------- Run store helpers --------------------
    def _run_path(self, run_id: str) -> str:
        """Build absolute path for a run's JSON record."""
        return os.path.join(self.runs_dir, f"{run_id}.json")

    def _save_run(self, run: OrchestrateRun) -> None:
        """Persist run state atomically to disk.
        Either the entire save operation succeeds or it fails completely
        No partial / corrupted saves. Prevents data corruption"""
        with open(self._run_path(run.run_id), "w", encoding="utf-8") as f:
            json.dump(run.model_dump(), f, indent=2)

    def _load_run(self, run_id: str) -> Optional[OrchestrateRun]:
        """Load a run by id if present; return None when missing."""
        path = self._run_path(run_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return OrchestrateRun(**data)

    # -------------------- Core orchestration --------------------
    def _new_run(self) -> OrchestrateRun:
        """Create a new run with pending status and persist it."""
        run = OrchestrateRun(
            run_id=str(uuid.uuid4()),
            status=RunStatus.pending,
            steps={},
            created_at_iso=_now_iso(),
            updated_at_iso=_now_iso(),
        )
        self._save_run(run)
        return run

    def _mark_step(self, run: OrchestrateRun, step: str, status: RunStatus) -> None:
        """Update a specific step's status and persist the run."""
        run.steps[step] = status
        run.updated_at_iso = _now_iso()
        self._save_run(run)

    def _to_parsed_query(self, parsed_raw: dict) -> ParsedQuery:
        """Map OpenAI extraction payload to the internal ParsedQuery model."""
        # Normalize ticket size to our schema shape
        ticket_raw = parsed_raw.get("ticket_size") or {}
        ticket = None
        if isinstance(ticket_raw, dict):
            # Normalize keys: min/max → minimum/maximum
            ticket = TicketSize(
                minimum=ticket_raw.get("min") or ticket_raw.get("minimum"),
                maximum=ticket_raw.get("max") or ticket_raw.get("maximum"),
            )

        pq = ParsedQuery(
            industry=parsed_raw.get("industry"),
            location=parsed_raw.get("location"),
            ticket_size=ticket,
            company_stage=parsed_raw.get("company_stage"),
            source_project=parsed_raw.get("source_project"),
            new_project=parsed_raw.get("new_project"),
            investor_type=parsed_raw.get("investor_type"),
            requirements=parsed_raw.get("requirements"),
            timeframe=parsed_raw.get("timeframe"),
            portfolio_focus=parsed_raw.get("portfolio_focus"),
            exit_strategy=parsed_raw.get("exit_strategy"),
            _metadata=parsed_raw.get("_metadata"),
        )
        return pq

    def _merge_and_dedupe(self, airtable_investors: List[Investor], apollo_investors: List[Investor]) -> List[Investor]:
        """Merge and remove duplicates using a stable key (website/LinkedIn/name)."""
        merged: List[Investor] = []
        seen: Dict[str, str] = {}

        def key(inv: Investor) -> str:
            k = (inv.website or inv.linkedin_url or inv.name or "").strip().lower()
            return k

        for inv in airtable_investors + apollo_investors:
            k = key(inv)
            if k and k in seen:
                continue
            if k:
                seen[k] = inv.id or inv.name
            merged.append(inv)
        return merged

    def orchestrate(self, request: OrchestrateRequest) -> OrchestrateResponse:
        """Execute the full workflow and return an API-friendly response.

        This method is intentionally linear for clarity; concurrency and retries
        can be added around the independent steps if/when needed.
        """
        run = self._new_run()
        run.status = RunStatus.running
        self._save_run(run)

        result = OrchestrateResult()

        try:
            # Step: parse_query
            self._mark_step(run, "parse_query", RunStatus.running)
            parsed_raw = self.openai_service.parse_investor_query(request.query)
            if isinstance(parsed_raw, dict) and parsed_raw.get("error"):
                raise ValueError(f"Parse error: {parsed_raw.get('error')}")
            parsed = self._to_parsed_query(parsed_raw if isinstance(parsed_raw, dict) else {})
            result.parsed_query = parsed
            self._mark_step(run, "parse_query", RunStatus.succeeded)

            # Step: fetch_airtable
            self._mark_step(run, "fetch_airtable", RunStatus.running)
            airtable_investors = self.airtable_service.get_investors_from_project(parsed.source_project)
            # Mark warm leads
            for inv in airtable_investors:
                inv.is_warm_lead = True
                inv.source = inv.source or "airtable"
            self._mark_step(run, "fetch_airtable", RunStatus.succeeded)

            # Step: fetch_apollo (only if we have search criteria beyond source project)
            apollo_investors = []
            if parsed.industry or parsed.location or parsed.investor_type:
                self._mark_step(run, "fetch_apollo", RunStatus.running)
                # Convert ParsedQuery to CompanySearchQuery for the new Apollo service
                from models.schemas import CompanySearchQuery
                company_query = CompanySearchQuery(
                    keywords=parsed.industry,
                    industry=parsed.industry,
                    location=parsed.location,
                )
                apollo_companies = self.apollo_service.search_companies(company_query, max_results=request.options.max_results)
                # Convert Company objects to Investor objects for backward compatibility
                for company in apollo_companies:
                    investor = Investor(
                        id=company.id,
                        name=company.name,
                        website=company.website,
                        linkedin_url=company.linkedin_url,
                        investor_type="Unknown",  # Default since we're not filtering by investor type
                        industry_focus=company.industry,
                        location=company.location,
                        ticket_min=None,  # Not available in general company search
                        ticket_max=None,  # Not available in general company search
                        is_warm_lead=False,
                        source=company.source or "apollo",
                    )
                    apollo_investors.append(investor)
                self._mark_step(run, "fetch_apollo", RunStatus.succeeded)
            else:
                self._mark_step(run, "fetch_apollo", RunStatus.succeeded)  # Skip Apollo if only source project

            # Step: merge_filter
            self._mark_step(run, "merge_filter", RunStatus.running)
            merged = self._merge_and_dedupe(airtable_investors, apollo_investors)
            # Apply ticket size filter if present
            ts = parsed.ticket_size
            if ts and (ts.minimum or ts.maximum):
                filtered: List[Investor] = []
                for i in merged:
                    if ts.minimum is not None and i.ticket_max is not None and i.ticket_max < ts.minimum:
                        continue
                    if ts.maximum is not None and i.ticket_min is not None and i.ticket_min > ts.maximum:
                        continue
                    filtered.append(i)
                merged = filtered
            result.investors = merged
            self._mark_step(run, "merge_filter", RunStatus.succeeded)

            # Step: export_csv
            self._mark_step(run, "export_csv", RunStatus.running)
            csv_path = export_investors_to_csv(result.investors)
            result.csv_path = csv_path
            self._mark_step(run, "export_csv", RunStatus.succeeded)

            # Step: calendar
            availability: Optional[List[AvailabilitySlot]] = None
            if request.options.include_calendar:
                self._mark_step(run, "calendar", RunStatus.running)
                availability = self.calendar_service.get_availability()
                result.availability = availability
                self._mark_step(run, "calendar", RunStatus.succeeded)

            # Step: email_draft
            if request.options.include_email_draft:
                self._mark_step(run, "email_draft", RunStatus.running)
                email = self.gmail_service.draft_email(result.investors, availability, parsed)
                result.email_draft = email
                self._mark_step(run, "email_draft", RunStatus.succeeded)

            # Step: create_project
            if request.options.create_project and not request.options.dry_run and parsed.new_project:
                self._mark_step(run, "create_project", RunStatus.running)
                project_id = self.airtable_service.create_project(parsed.new_project, result.investors)
                result.project_id = project_id
                self._mark_step(run, "create_project", RunStatus.succeeded)

            run.status = RunStatus.succeeded
            run.result = result
            run.updated_at_iso = _now_iso()
            self._save_run(run)
            return OrchestrateResponse(run_id=run.run_id, status=run.status, result=result)

        except Exception as e:
            run.status = RunStatus.failed
            run.error_message = str(e)
            run.updated_at_iso = _now_iso()
            self._save_run(run)
            return OrchestrateResponse(run_id=run.run_id, status=run.status, error_message=str(e))

    # -------------------- Public helpers --------------------
    def get_run(self, run_id: str) -> Optional[OrchestrateRun]:
        """Public helper to load a persisted run by id."""
        return self._load_run(run_id)
