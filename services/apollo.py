"""
Apollo service wrapper

Responsibilities:
- Search for organizations (investor firms) via Apollo's API
- Map Apollo response fields to our Investor model
- Support a deterministic mock mode for offline/dev testing

Authentication:
- Prefers `X-Api-Key: <APOLLO_API_KEY>`; also sends `Authorization: Bearer <APOLLO_API_KEY>`

Configuration (env):
- APOLLO_API_KEY               : API key
- APOLLO_ENABLE_MOCK          : "1"/"true" to return generated mock data
- APOLLO_BASE_URL             : default "https://api.apollo.io/v1"
- APOLLO_ORG_SEARCH_URL       : override organizations search endpoint
"""

import os
from typing import List, Optional

import requests
from dotenv import load_dotenv

from models.schemas import Investor, ParsedQuery


load_dotenv()


class ApolloService:
    """Client for Apollo organizations search (investor firms)."""
    def __init__(self) -> None:
        self.api_key: Optional[str] = os.getenv("APOLLO_API_KEY")
        self.base_url: str = os.getenv("APOLLO_BASE_URL", "https://api.apollo.io/v1")
        self.enable_mock: bool = os.getenv("APOLLO_ENABLE_MOCK", "0") in {"1", "true", "True"}

    def search_investors(self, query: ParsedQuery, max_results: int = 50) -> List[Investor]:
        """Search Apollo for likely investor organizations based on a parsed query.

        - Uses keyword bias (capital/ventures/vc/partners) to target firms
        - Applies industry/location if provided
        - Returns a list of Investor models (subset of fields)
        - In mock mode (or missing API key), generates deterministic sample firms
        """
        # Mock mode to enable end-to-end testing without a real Apollo integration
        if self.enable_mock or not self.api_key:
            count = max(1, min(max_results, 10))
            industry = (query.industry or "General").title()
            location = (query.location or "Global").title()
            prefix = f"{industry} Capital {location}"
            ticket_min = query.ticket_size.minimum if query.ticket_size else None
            ticket_max = query.ticket_size.maximum if query.ticket_size else None

            mocked: List[Investor] = []
            for i in range(1, count + 1):
                slug = f"{industry}-{location}-vc-{i}".lower().replace(" ", "-")
                mocked.append(
                    Investor(
                        id=f"mock-apollo-{slug}",
                        name=f"{prefix} #{i}",
                        website=f"https://{slug}.com",
                        linkedin_url=f"https://www.linkedin.com/company/{slug}",
                        investor_type="VC",
                        industry_focus=query.industry,
                        location=query.location,
                        ticket_min=ticket_min,
                        ticket_max=ticket_max,
                        is_warm_lead=False,
                        source="apollo",
                    )
                )
            return mocked

        # Real call: Apollo Organizations Search API (subject to plan/permissions)
        # Endpoint is overrideable via APOLLO_ORG_SEARCH_URL
        org_search_url = os.getenv("APOLLO_ORG_SEARCH_URL", f"{self.base_url}/organizations/search")
        try:
            # Prefer X-Api-Key (works per Apollo examples); keep Bearer for compatibility
            headers = {
                "X-Api-Key": self.api_key,
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            industries: Optional[List[str]] = [query.industry] if query.industry else None
            locations: Optional[List[str]] = [query.location] if query.location else None

            # Build a permissive keyword search to bias towards investors (VC firms)
            keyword_tokens: List[str] = [
                "capital",
                "ventures",
                "partners",
                "vc",
                "investment",
                "investments",
                "equity",
            ]
            if query.industry:
                keyword_tokens.append(query.industry)
            if query.investor_type:
                keyword_tokens.append(query.investor_type)
            q_keywords = " ".join(keyword_tokens)

            payload = {
                "page": 1,
                "per_page": max(1, min(max_results, 25)),
                # Many Apollo endpoints accept flexible fields; unknown ones are ignored
                # Include common filters if supported by your plan
                "q_organization_keywords": q_keywords,
            }
            if industries:
                payload["industries"] = industries
            if locations:
                payload["locations"] = locations

            resp = requests.post(org_search_url, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            # Response may contain 'organizations' or 'companies'
            orgs = data.get("organizations") or data.get("companies") or []
            results: List[Investor] = []
            for org in orgs:
                name = org.get("name") or org.get("organization_name") or ""
                if not name:
                    continue
                website = (
                    org.get("website_url")
                    or org.get("website")
                    or (f"https://{org.get('primary_domain')}" if org.get("primary_domain") else None)
                )
                linkedin = org.get("linkedin_url") or org.get("linkedin")
                ind = None
                if isinstance(org.get("industries"), list) and org.get("industries"):
                    ind = ", ".join(org.get("industries"))
                elif isinstance(org.get("industry"), str):
                    ind = org.get("industry")
                loc = org.get("primary_location") or org.get("location")

                results.append(
                    Investor(
                        id=str(org.get("id") or org.get("_id") or org.get("uuid") or name),
                        name=name,
                        website=website,
                        linkedin_url=linkedin,
                        investor_type="VC",
                        industry_focus=ind or query.industry,
                        location=loc or query.location,
                        ticket_min=query.ticket_size.minimum if query.ticket_size else None,
                        ticket_max=query.ticket_size.maximum if query.ticket_size else None,
                        is_warm_lead=False,
                        source="apollo",
                    )
                )

            return results
        except Exception:
            # On any error, return empty to avoid breaking the overall flow
            return []
