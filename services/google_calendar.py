from datetime import datetime, timedelta
from typing import List

from models.schemas import AvailabilitySlot


class GoogleCalendarService:
    def get_availability(self) -> List[AvailabilitySlot]:
        # Placeholder: suggest three slots starting tomorrow
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
