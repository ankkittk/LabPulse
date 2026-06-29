"""
deduplicator.py

Avoids generating duplicate incidents
for the same machine.

Without this:

Every 5 seconds

↓

new incident

Instead:

One incident

↓

update existing
"""

from __future__ import annotations

from datetime import datetime, timedelta


class IncidentDeduplicator:

    DUPLICATE_WINDOW = timedelta(minutes=5)

    @staticmethod
    def is_duplicate(
        latest_incident: dict | None,
        new_type: str,
    ) -> bool:

        if latest_incident is None:
            return False

        if latest_incident["incident_type"] != new_type:
            return False

        created = latest_incident["created_at"]

        if isinstance(created, str):
            created = datetime.fromisoformat(created)

        if datetime.now() - created <= IncidentDeduplicator.DUPLICATE_WINDOW:
            return True

        return False
