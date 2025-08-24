"""
Airtable service wrapper

Responsibilities:
- Connect to Airtable base/tables using environment config
- Read investors for a given project
- Create a new project record (optional step in workflow)

Environment variables:
- AIRTABLE_API_KEY
- AIRTABLE_BASE_ID
- AIRTABLE_TABLE_INVESTORS (default: "Investors")
- AIRTABLE_TABLE_PROJECTS (default: "Projects")
"""

import os
from typing import List, Optional

from dotenv import load_dotenv
from pyairtable import Api

from models.schemas import Investor


load_dotenv()


class AirtableService:
    """Thin wrapper around pyairtable for project/investor operations."""
    def __init__(self) -> None:
        self.api_key: Optional[str] = os.getenv("AIRTABLE_API_KEY")
        self.base_id: Optional[str] = os.getenv("AIRTABLE_BASE_ID")
        self.table_investors: str = os.getenv("AIRTABLE_TABLE_INVESTORS", "Investors")
        self.table_projects: str = os.getenv("AIRTABLE_TABLE_PROJECTS", "Projects")

        self.client: Optional[Api] = None
        if self.api_key and self.base_id:
            try:
                self.client = Api(self.api_key)
            except Exception:
                self.client = None

    def get_investors_from_project(self, project_name: Optional[str]) -> List[Investor]:
        """Return investors linked to a given project name.

        Expects an "Investors" table with fields roughly matching:
        Name, Website, LinkedIn, Type, Industry, Location, TicketMin, TicketMax,
        WarmLead (checkbox), Project (text/link).
        """
        if not project_name:
            return []

        if not (self.client and self.base_id):
            # Fallback: no credentials, return empty list
            return []

        try:
            table = self.client.table(self.base_id, self.table_investors)
            # Basic filter example; adapt to your Airtable schema as needed
            # Updated to use "Project Tag" field which matches the actual Airtable schema
            formula = f"{{Project Tag}} = '{project_name}'"
            records = table.all(formula=formula)
            investors: List[Investor] = []
            for r in records:
                fields = r.get("fields", {})
                investors.append(
                    Investor(
                        id=r.get("id"),
                        name=fields.get("Company Name") or fields.get("Name") or "",
                        website=fields.get("URL"),
                        linkedin_url=fields.get("LN"),
                        investor_type=fields.get("Strategic/Financial"),
                        industry_focus=fields.get("Industry/ Sector Focus"),
                        location=fields.get("HQ"),
                        ticket_min=None,  # Not available in current schema
                        ticket_max=None,  # Not available in current schema
                        is_warm_lead=True,  # All Airtable companies are warm leads
                        source="airtable",
                    )
                )
            return investors
        except Exception:
            return []

    def create_project(self, project_name: str, investors: List[Investor]) -> Optional[str]:
        """Create a new project row and return its Airtable record id."""
        if not (self.client and self.base_id):
            return None
        try:
            table = self.client.table(self.base_id, self.table_projects)
            record = table.create({
                "Name": project_name,
                "InvestorCount": len(investors),
            })
            return record.get("id")
        except Exception:
            return None
