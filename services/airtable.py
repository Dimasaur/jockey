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
        self.enable_mock: bool = os.getenv("AIRTABLE_ENABLE_MOCK", "0").lower() in ("1", "true", "yes")

        self.client: Optional[Api] = None
        if self.api_key and self.base_id and not self.enable_mock:
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

        if self.enable_mock or not (self.client and self.base_id):
            # Return mock data for testing
            return self._generate_mock_investors(project_name)

        try:
            table = self.client.table(self.base_id, self.table_investors)
            # Get all records and filter in Python to handle comma-separated project tags
            records = table.all()
            print(f"DEBUG: Found {len(records)} total records in Airtable")
            # Filter records that contain the project name in their Project Tag
            filtered_records = []
            for record in records:
                project_tag = record.get("fields", {}).get("Project Tag", "")
                print(f"DEBUG: Checking record {record.get('fields', {}).get('Company Name', 'Unknown')} with project tag: '{project_tag}'")
                if project_name in project_tag:
                    filtered_records.append(record)
                    print(f"DEBUG: Found match for project '{project_name}'")
            records = filtered_records
            print(f"DEBUG: Filtered to {len(records)} records for project '{project_name}'")
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

    def _generate_mock_investors(self, project_name: str) -> List[Investor]:
        """Generate mock investor data for testing."""
        mock_investors = [
            Investor(
                id=f"mock_airtable_1_{project_name}",
                name="TechCorp Solutions",
                website="https://techcorp-solutions.com",
                linkedin_url="https://linkedin.com/company/techcorp-solutions",
                investor_type="Strategic",
                industry_focus="Technology",
                location="San Francisco, CA",
                ticket_min=1000000,
                ticket_max=5000000,
                is_warm_lead=True,
                source="airtable",
            ),
            Investor(
                id=f"mock_airtable_2_{project_name}",
                name="Innovate Capital",
                website="https://innovate-capital.com",
                linkedin_url="https://linkedin.com/company/innovate-capital",
                investor_type="Financial",
                industry_focus="Fintech",
                location="New York, NY",
                ticket_min=500000,
                ticket_max=2000000,
                is_warm_lead=True,
                source="airtable",
            ),
            Investor(
                id=f"mock_airtable_3_{project_name}",
                name="Green Energy Ventures",
                website="https://green-energy-ventures.com",
                linkedin_url="https://linkedin.com/company/green-energy-ventures",
                investor_type="Strategic",
                industry_focus="Clean Energy",
                location="Austin, TX",
                ticket_min=2000000,
                ticket_max=10000000,
                is_warm_lead=True,
                source="airtable",
            ),
        ]
        print(f"DEBUG: Generated {len(mock_investors)} mock Airtable investors for project '{project_name}'")
        return mock_investors

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
