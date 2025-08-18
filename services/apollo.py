import os
from typing import List, Optional

import requests
from dotenv import load_dotenv

from models.schemas import Investor, ParsedQuery


load_dotenv()


class ApolloService:
    def __init__(self) -> None:
        self.api_key: Optional[str] = os.getenv("APOLLO_API_KEY")
        self.base_url: str = os.getenv("APOLLO_BASE_URL", "https://api.apollo.io/v1")

    def search_investors(self, query: ParsedQuery, max_results: int = 50) -> List[Investor]:
        if not self.api_key:
            # Fallback mock: return empty list when not configured
            return []

        # NOTE: Apollo.io investor search specifics are omitted; this is a placeholder.
        # If you have a specific endpoint, replace this with the correct API call.
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            # Placeholder: ping health or some lightweight endpoint
            health_url = f"{self.base_url}/auth/health"
            resp = requests.get(health_url, headers=headers, timeout=15)
            resp.raise_for_status()

            # Without a real endpoint, return an empty list for now
            return []
        except Exception:
            return []
