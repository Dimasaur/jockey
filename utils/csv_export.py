"""
CSV export utility for investor data

Exports a list of Investor models to a timestamped CSV file in the exports/
directory. Used by the orchestrator to generate downloadable investor lists.
"""

import csv
import os
from datetime import datetime
from typing import List

from models.schemas import Investor


def export_investors_to_csv(investors: List[Investor], directory: str = "./exports") -> str:
    """Export investor list to a timestamped CSV file.

    Args:
        investors: List of Investor models to export
        directory: Output directory (default: "./exports")

    Returns:
        Absolute path to the created CSV file

    The CSV includes all Investor fields: id, name, website, linkedin_url,
    investor_type, industry_focus, location, ticket_min, ticket_max,
    is_warm_lead, and source.
    """
    os.makedirs(directory, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    file_path = os.path.join(directory, f"investors_{timestamp}.csv")

    fieldnames = [
        "id",
        "name",
        "website",
        "linkedin_url",
        "investor_type",
        "industry_focus",
        "location",
        "ticket_min",
        "ticket_max",
        "is_warm_lead",
        "source",
    ]

    with open(file_path, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for inv in investors:
            writer.writerow(inv.model_dump())

    return os.path.abspath(file_path)
