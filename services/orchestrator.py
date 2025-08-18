import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from models.schemas import (
    AvailabilitySlot,
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
from jockey_utils.csv_export import export_investors_to_csv


def _now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


class Orchestrator:
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
        return os.path.join(self.runs_dir, f"{run_id}.json")

    def _save_run(self, run: OrchestrateRun) -> None:
        with open(self._run_path(run.run_id), "w", encoding="utf-8") as f:
            json.dump(run.model_dump(), f, indent=2)

    def _load_run(self, run_id: str) -> Optional[OrchestrateRun]:
        path = self._run_path(run_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return OrchestrateRun(**data)

    # -------------------- Core orchestration --------------------
    def _new_run(self) -> OrchestrateRun:
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
        run.steps[step] = status
        run.updated_at_iso = _now_iso()
        self._save_run(run)

    def _to_parsed_query(self, parsed_raw: dict) -> ParsedQuery:
        # Map OpenAI extraction schema to ParsedQuery model
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

            # Step: fetch_apollo
            self._mark_step(run, "fetch_apollo", RunStatus.running)
            apollo_investors = self.apollo_service.search_investors(parsed, max_results=request.options.max_results)
            for inv in apollo_investors:
                inv.source = inv.source or "apollo"
            self._mark_step(run, "fetch_apollo", RunStatus.succeeded)

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
        return self._load_run(run_id)
