"""
Gmail service (drafting only)

Generates a plain-text email draft summarizing the investor results and
proposing available meeting slots. This does not send email; it returns an
EmailDraft object for display or further editing.
"""

from typing import List, Optional

from jinja2 import Template

from models.schemas import AvailabilitySlot, EmailDraft, Investor, ParsedQuery


class GmailService:
    """Create email drafts summarizing results and availability."""

    def draft_email(self, investors: List[Investor], availability: Optional[List[AvailabilitySlot]], parsed: Optional[ParsedQuery]) -> EmailDraft:
        """Build a simple text email draft.

        Args:
            investors: Final investor list (top 5 previewed in the body).
            availability: Optional list of time slots to propose.
            parsed: Parsed query context to personalize industry/location.

        Returns:
            EmailDraft: subject and body_text populated (no HTML send).
        """
        subject = "Investor list and next steps"
        slots_text = ""
        if availability:
            slots_text = "\n".join([f"- {s.start_iso} to {s.end_iso} {('(' + s.timezone + ')' if s.timezone else '')}" for s in availability])

        first_five = investors[:5]
        investors_lines = "\n".join([f"- {i.name} ({i.website or 'n/a'})" for i in first_five])

        context = {
            "industry": parsed.industry if parsed else None,
            "location": parsed.location if parsed else None,
            "count": len(investors),
            "investors_lines": investors_lines,
            "slots_text": slots_text,
        }

        text_template = Template(
            (
                "Hi,\n\n"
                "I prepared an investor list{{ ' for ' + industry if industry else '' }}{{ ' in ' + location if location else '' }}.\n"
                "There are {{ count }} investors in total. Here are a few:\n"
                "{{ investors_lines }}\n\n"
                "Availability for a quick call:\n{{ slots_text if slots_text else 'Let me know your preferred times.'}}\n\n"
                "Best,\nJockey AI"
            )
        )

        body_text = text_template.render(**context)
        return EmailDraft(subject=subject, body_text=body_text)
