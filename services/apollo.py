"""
Apollo service wrapper for general company and person search

Responsibilities:
- Search for companies/organizations via Apollo's API with flexible criteria
- Search for people/contacts within companies
- Map Apollo response fields to our Company and Person models
- Support a deterministic mock mode for offline/dev testing

Authentication:
- Uses `X-Api-Key: <APOLLO_API_KEY>` header

Configuration (env):
- APOLLO_API_KEY               : API key
- APOLLO_ENABLE_MOCK          : "1"/"true" to return generated mock data
- APOLLO_BASE_URL             : default "https://api.apollo.io/v1"
- APOLLO_ORG_SEARCH_URL       : override organizations search endpoint
- APOLLO_PEOPLE_SEARCH_URL    : override people search endpoint
"""

import os
from typing import List, Optional

import requests
from dotenv import load_dotenv

from models.schemas import Company, Person, CompanySearchQuery, PersonSearchQuery

import logging
logger = logging.getLogger(__name__)

load_dotenv()


class ApolloService:
    """General-purpose Apollo client for company and person search."""

    def __init__(self) -> None:
        self.api_key: Optional[str] = os.getenv("APOLLO_API_KEY")
        self.base_url: str = os.getenv("APOLLO_BASE_URL", "https://api.apollo.io/v1")
        self.enable_mock: bool = os.getenv("APOLLO_ENABLE_MOCK", "0") in {"1", "true", "True"}

    def search_companies(self, query: CompanySearchQuery, max_results: int = 50) -> List[Company]:
        """Search Apollo for companies based on flexible criteria.

        Supports searching by:
        - Keywords (general company search)
        - Industry/industries
        - Location (city, state, country)
        - Employee count ranges
        - Revenue ranges
        - Founded year ranges
        - Technologies
        - Funding stage
        """
        # Mock mode for testing
        if self.enable_mock or not self.api_key:
            return self._generate_mock_companies(query, max_results)

        # Real Apollo API call
        org_search_url = os.getenv("APOLLO_ORG_SEARCH_URL", f"{self.base_url}/organizations/search")
        try:
            headers = {
                "X-Api-Key": self.api_key,
                "Content-Type": "application/json",
            }

            # Build search payload with all available criteria
            payload = {
                "page": 1,
                "per_page": max(1, min(max_results, 25)),
            }

            # Add keywords if provided
            if query.keywords:
                payload["q_organization_keywords"] = query.keywords

            # Add industry filters
            if query.industries:
                payload["industries"] = query.industries
            elif query.industry:
                payload["industries"] = [query.industry]

            # Add location filters
            if query.country:
                payload["locations"] = [query.country]
            elif query.state:
                payload["locations"] = [query.state]
            elif query.city:
                payload["locations"] = [query.city]
            elif query.location:
                payload["locations"] = [query.location]

            # Add employee count filters (if supported by Apollo)
            if query.employee_count_min or query.employee_count_max:
                employee_filters = []
                if query.employee_count_min:
                    employee_filters.append(f"min:{query.employee_count_min}")
                if query.employee_count_max:
                    employee_filters.append(f"max:{query.employee_count_max}")
                if employee_filters:
                    payload["employee_ranges"] = employee_filters

            # Add revenue filters (if supported by Apollo)
            if query.revenue_min or query.revenue_max:
                revenue_filters = []
                if query.revenue_min:
                    revenue_filters.append(f"min:{query.revenue_min}")
                if query.revenue_max:
                    revenue_filters.append(f"max:{query.revenue_max}")
                if revenue_filters:
                    payload["revenue_ranges"] = revenue_filters

            # Add founded year filters (if supported by Apollo)
            if query.founded_year_min or query.founded_year_max:
                year_filters = []
                if query.founded_year_min:
                    year_filters.append(f"min:{query.founded_year_min}")
                if query.founded_year_max:
                    year_filters.append(f"max:{query.founded_year_max}")
                if year_filters:
                    payload["founded_years"] = year_filters

            # Add technology filters (if supported by Apollo)
            if query.technologies:
                payload["technologies"] = query.technologies

            # Add funding stage filter (if supported by Apollo)
            if query.funding_stage:
                payload["funding_stages"] = [query.funding_stage]

            logger.info(f"Apollo company search payload: {payload}")
            print(f"DEBUG: Apollo payload being sent: {payload}")
            resp = requests.post(org_search_url, headers=headers, json=payload, timeout=30)

            if resp.status_code != 200:
                logger.error(f"Apollo API error: {resp.status_code} - {resp.text}")
                return []

            data = resp.json()
            orgs = data.get("organizations") or data.get("companies") or []
            logger.info(f"Apollo API response: {len(orgs)} companies found")

            # Log sample results for debugging
            for i, org in enumerate(orgs[:3]):
                name = org.get("name", "Unknown")
                industries = org.get("industries", [])
                if isinstance(org.get("industry"), str):
                    industries = [org.get("industry")]
                logger.info(f"Sample company {i+1}: {name} - Industries: {industries}")

            # Convert to Company objects
            results: List[Company] = []
            for org in orgs:
                name = org.get("name") or org.get("organization_name") or ""
                if not name:
                    continue

                # Extract basic info
                website = (
                    org.get("website_url")
                    or org.get("website")
                    or (f"https://{org.get('primary_domain')}" if org.get("primary_domain") else None)
                )
                linkedin = org.get("linkedin_url") or org.get("linkedin")
                description = org.get("description") or org.get("snippet")

                # Extract industry info
                industries = []
                if isinstance(org.get("industries"), list):
                    industries = org.get("industries", [])
                elif isinstance(org.get("industry"), str):
                    industries = [org.get("industry")]

                industry = ", ".join(industries) if industries else None

                # Extract location info
                location = org.get("primary_location") or org.get("location")
                city = org.get("city")
                state = org.get("state")
                country = org.get("country")

                # Extract company details
                employee_count = org.get("estimated_num_employees")
                employee_range = org.get("employee_range")
                revenue = org.get("organization_revenue")
                revenue_range = org.get("revenue_range")
                founded_year = org.get("founded_year")

                # Extract technologies and keywords
                technologies = org.get("technologies", [])
                keywords = org.get("keywords", [])

                # Extract funding stage
                funding_stage = org.get("funding_stage")

                results.append(
                    Company(
                        id=str(org.get("id") or org.get("_id") or org.get("uuid") or name),
                        name=name,
                        website=website,
                        linkedin_url=linkedin,
                        description=description,
                        industry=industry,
                        industries=industries,
                        location=location,
                        city=city,
                        state=state,
                        country=country,
                        employee_count=employee_count,
                        employee_range=employee_range,
                        revenue=revenue,
                        revenue_range=revenue_range,
                        founded_year=founded_year,
                        technologies=technologies,
                        funding_stage=funding_stage,
                        keywords=keywords,
                        source="apollo",
                    )
                )

            logger.info(f"Apollo company search: {len(orgs)} total companies, {len(results)} processed")
            return results

        except Exception as e:
            logger.error(f"Apollo API error: {e}")
            return []

    def search_people(self, query: PersonSearchQuery, max_results: int = 50) -> List[Person]:
        """Search Apollo for people/contacts based on criteria.

        Supports searching by:
        - Job title
        - Seniority level
        - Department
        - Company name
        - Location
        """
        # Mock mode for testing
        if self.enable_mock or not self.api_key:
            return self._generate_mock_people(query, max_results)

        # Real Apollo API call
        people_search_url = os.getenv("APOLLO_PEOPLE_SEARCH_URL", f"{self.base_url}/people/search")
        try:
            headers = {
                "X-Api-Key": self.api_key,
                "Content-Type": "application/json",
            }

            # Build search payload
            payload = {
                "page": 1,
                "per_page": max(1, min(max_results, 25)),
            }

            # Add job title filter
            if query.job_title:
                payload["q_titles"] = [query.job_title]

            # Add seniority level filter
            if query.seniority_level:
                payload["seniority_levels"] = [query.seniority_level]

            # Add department filter
            if query.department:
                payload["departments"] = [query.department]

            # Add company name filter
            if query.company_name:
                payload["q_organization_keywords"] = query.company_name

            # Add location filter
            if query.location:
                payload["locations"] = [query.location]

            logger.info(f"Apollo people search payload: {payload}")
            resp = requests.post(people_search_url, headers=headers, json=payload, timeout=30)

            if resp.status_code != 200:
                logger.error(f"Apollo API error: {resp.status_code} - {resp.text}")
                return []

            data = resp.json()
            people = data.get("people") or []
            logger.info(f"Apollo API response: {len(people)} people found")

            # Convert to Person objects
            results: List[Person] = []
            for person in people:
                name = person.get("name") or ""
                if not name:
                    continue

                results.append(
                    Person(
                        id=str(person.get("id") or person.get("_id") or person.get("uuid") or name),
                        name=name,
                        title=person.get("title"),
                        seniority_level=person.get("seniority_level"),
                        department=person.get("department"),
                        company_id=str(person.get("organization_id")) if person.get("organization_id") else None,
                        company_name=person.get("organization_name"),
                        email=person.get("email"),
                        linkedin_url=person.get("linkedin_url"),
                        location=person.get("location"),
                        source="apollo",
                    )
                )

            logger.info(f"Apollo people search: {len(people)} total people, {len(results)} processed")
            return results

        except Exception as e:
            logger.error(f"Apollo API error: {e}")
            return []

    def _generate_mock_companies(self, query: CompanySearchQuery, max_results: int) -> List[Company]:
        """Generate mock company data for testing."""
        count = max(1, min(max_results, 10))
        industry = (query.industry or "Technology").title()
        location = (query.location or query.city or query.state or query.country or "Global").title()

        mock_companies: List[Company] = []
        for i in range(1, count + 1):
            company_type = "Tech" if "tech" in industry.lower() else "Corp"
            name = f"{industry} {company_type} {location} #{i}"
            slug = f"{industry.lower()}-{company_type.lower()}-{location.lower()}-{i}".replace(" ", "-")

            mock_companies.append(
                Company(
                    id=f"mock-apollo-{slug}",
                    name=name,
                    website=f"https://{slug}.com",
                    linkedin_url=f"https://www.linkedin.com/company/{slug}",
                    description=f"A leading {industry.lower()} company based in {location}",
                    industry=industry,
                    industries=[industry],
                    location=location,
                    city=query.city or location,
                    state=query.state,
                    country=query.country or "United States",
                    employee_count=100 + (i * 50),
                    employee_range=f"{100 + (i * 50)}-{200 + (i * 50)}",
                    revenue=1000000 + (i * 500000),
                    revenue_range=f"${1 + i}M-${2 + i}M",
                    founded_year=2010 + i,
                    technologies=query.technologies or ["Python", "JavaScript", "Cloud"],
                    funding_stage=query.funding_stage or "Series A",
                    keywords=[query.keywords] if query.keywords else [industry.lower(), "innovation", "growth"],
                    source="apollo",
                )
            )
        return mock_companies

    def _generate_mock_people(self, query: PersonSearchQuery, max_results: int) -> List[Person]:
        """Generate mock person data for testing."""
        count = max(1, min(max_results, 10))
        title = query.job_title or "Manager"
        department = query.department or "Engineering"
        company = query.company_name or "Tech Corp"

        mock_people: List[Person] = []
        for i in range(1, count + 1):
            name = f"John Doe {i}"
            slug = f"john-doe-{i}"

            mock_people.append(
                Person(
                    id=f"mock-apollo-person-{slug}",
                    name=name,
                    title=title,
                    seniority_level=query.seniority_level or "Manager",
                    department=department,
                    company_id=f"mock-company-{i}",
                    company_name=company,
                    email=f"{slug}@{company.lower().replace(' ', '')}.com",
                    linkedin_url=f"https://www.linkedin.com/in/{slug}",
                    location=query.location or "San Francisco, CA",
                    source="apollo",
                )
            )
        return mock_people

    # Legacy method for backward compatibility
    def search_investors(self, query, max_results: int = 50):
        """Legacy method - redirects to search_companies for backward compatibility."""
        logger.warning("search_investors is deprecated, use search_companies instead")
        # Convert ParsedQuery to CompanySearchQuery
        company_query = CompanySearchQuery(
            keywords=query.industry,
            industry=query.industry,
            location=query.location,
        )
        return self.search_companies(company_query, max_results)
