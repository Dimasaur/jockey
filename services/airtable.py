import os
from typing import List, Optional

from dotenv import load_dotenv
from pyairtable import Api

from models.schemas import Investor


load_dotenv()


class AirtableService:
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
        if not project_name:
            return []

        if not (self.client and self.base_id):
            # Fallback: no credentials, return empty list
            return []

        try:
            table = self.client.table(self.base_id, self.table_investors)
            # Basic filter example; adapt to actual schema as needed
            formula = f"{{Project}} = '{project_name}'"
            records = table.all(formula=formula)
            investors: List[Investor] = []
            for r in records:
                fields = r.get("fields", {})
                investors.append(
                    Investor(
                        id=r.get("id"),
                        name=fields.get("Name") or fields.get("Company") or "",
                        website=fields.get("Website"),
                        linkedin_url=fields.get("LinkedIn"),
                        investor_type=fields.get("Type"),
                        industry_focus=fields.get("Industry"),
                        location=fields.get("Location"),
                        ticket_min=fields.get("TicketMin"),
                        ticket_max=fields.get("TicketMax"),
                        is_warm_lead=bool(fields.get("WarmLead", False)),
                        source="airtable",
                    )
                )
            return investors
        except Exception:
            return []

    def create_project(self, project_name: str, investors: List[Investor]) -> Optional[str]:
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
