"""
Google Calendar service (availability stub)

Current behavior: returns 3 suggested 30-minute UTC slots for tomorrow (09:00,
13:00, 17:00). This is a lightweight placeholder to support email drafting.

To integrate real Google Calendar availability, wire this service to Google
Calendar API (using `setup_google_oauth.py` to obtain credentials) and replace
`get_availability` with free/busy queries for the desired calendar(s).
"""

from datetime import datetime, timedelta
from typing import List

from models.schemas import AvailabilitySlot


class GoogleCalendarService:
    """Suggest or fetch availability time slots."""

    def get_availability(self) -> List[AvailabilitySlot]:
        """Return three 30-minute placeholder slots starting tomorrow (UTC)."""
        # Placeholder suggestion logic: adjust to your local tz or real free/busy
        base = datetime.utcnow().replace(minute=0, second=0, microsecond=0) + timedelta(days=1)
        slots = []
        for hours in (9, 13, 17):
            start = base.replace(hour=hours)
            end = start + timedelta(minutes=30)
            slots.append(
                AvailabilitySlot(
                    start_iso=start.isoformat() + "Z",
                    end_iso=end.isoformat() + "Z",
                    timezone="UTC",
                )
            )
        return slots
