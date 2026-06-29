"""
manager.py

Central Incident Management Engine.

Responsibilities
----------------
1. Receive anomaly detection results.
2. Calculate incident severity.
3. Prevent duplicate incidents.
4. Create new incidents.
5. Update existing incidents.
6. Resolve incidents automatically.
7. Provide a clean interface to future
   RCA / Forecast / Agentic AI modules.

This module intentionally contains NO ML.

ML belongs to:

server.analytics.*

Incident lifecycle belongs here.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from server.incident.severity import SeverityCalculator
from server.incident.deduplicator import IncidentDeduplicator

logger = logging.getLogger(__name__)


class IncidentManager:

    """
    Coordinates the entire incident lifecycle.

    Future AI modules will never directly
    touch the database.

    They only talk to IncidentManager.
    """

    def __init__(self, db):

        self.db = db

        self.severity = SeverityCalculator()

        self.deduplicator = IncidentDeduplicator()

    # ======================================================
    # PUBLIC API
    # ======================================================

    def process_anomaly(
        self,
        computer_id: int,
        snapshot: dict,
        anomaly_result: dict,
    ) -> Optional[int]:
        """
        Main entry point.

        Called immediately after anomaly detection.

        Returns
        -------
        incident_id

        or

        None
        """

        if not anomaly_result.get("is_anomaly", False):

            self.resolve_open_incidents(
                computer_id
            )

            return None

        severity = self.severity.calculate(
            snapshot,
            anomaly_result["score"],
        )

        return self._handle_incident(
            computer_id=computer_id,
            snapshot=snapshot,
            anomaly_result=anomaly_result,
            severity=severity,
        )

    # ======================================================

    def resolve_open_incidents(
        self,
        computer_id: int,
    ) -> None:
        """
        Automatically closes all open incidents
        when the machine returns to a healthy state.
        """

        open_incidents = self.db.get_open_incidents(
            computer_id
        )

        if not open_incidents:
            return

        for incident in open_incidents:

            self.db.resolve_incident(
                incident["id"]
            )

            logger.info(
                "Resolved incident %s",
                incident["id"],
            )

    # ======================================================

    def get_open_incidents(
        self,
        computer_id: int,
    ):

        return self.db.get_open_incidents(
            computer_id
        )

    # ======================================================

    def get_latest_incident(
        self,
        computer_id: int,
    ):

        return self.db.get_latest_incident(
            computer_id
        )

    # ======================================================
    # PRIVATE
    # ======================================================

    def _handle_incident(
        self,
        computer_id: int,
        snapshot: dict,
        anomaly_result: dict,
        severity,
    ):

        latest = self.db.get_latest_incident(
            computer_id
        )

        if self.deduplicator.is_duplicate(
            latest,
            "RESOURCE_ANOMALY",
        ):

            return self._update_existing_incident(
                latest,
                snapshot,
                anomaly_result,
                severity,
            )

        return self._create_new_incident(
            computer_id,
            snapshot,
            anomaly_result,
            severity,
        )

    # ======================================================
    # CREATE
    # ======================================================

    def _create_new_incident(
        self,
        computer_id: int,
        snapshot: dict,
        anomaly_result: dict,
        severity,
    ) -> int:
        """
        Creates a brand-new incident.

        Returns
        -------
        incident_id
        """

        description = self._build_description(
            snapshot,
            anomaly_result,
        )

        incident = {
            "computer_id": computer_id,
            "incident_type": "RESOURCE_ANOMALY",
            "severity": severity.severity,
            "confidence": float(anomaly_result["score"]),
            "anomaly_score": float(anomaly_result["score"]),
            "description": description,
            "status": "OPEN",
            "created_at": datetime.now(),
        }

        incident_id = self.db.create_incident(
            incident
        )

        logger.info(
            "Created incident %s (%s)",
            incident_id,
            severity.severity,
        )

        return incident_id

    # ======================================================
    # UPDATE
    # ======================================================

    def _update_existing_incident(
        self,
        incident: dict,
        snapshot: dict,
        anomaly_result: dict,
        severity,
    ) -> int:
        """
        Existing incident.

        Update instead of creating another row.
        """

        description = self._build_description(
            snapshot,
            anomaly_result,
        )

        updated = {

            "severity": severity.severity,

            "confidence": float(
                anomaly_result["score"]
            ),

            "anomaly_score": float(
                anomaly_result["score"]
            ),

            "description": description,

            "last_updated": datetime.now(),

        }

        self.db.update_incident(

            incident["id"],

            updated,

        )

        logger.info(
            "Updated incident %s",
            incident["id"],
        )

        return incident["id"]

    # ======================================================
    # DESCRIPTION
    # ======================================================

    def _build_description(
        self,
        snapshot: dict,
        anomaly_result: dict,
    ) -> str:
        """
        Human-readable incident description.

        Future:
        ------
        This function will later be replaced
        by the RCA Agent.
        """

        cpu = snapshot.get("cpu_usage", 0)

        ram = snapshot.get("ram_usage", 0)

        disk = snapshot.get("disk_usage", 0)

        proc = snapshot.get(
            "top_process_name",
            "Unknown",
        )

        proc_cpu = snapshot.get(
            "top_process_cpu",
            0,
        )

        proc_mem = snapshot.get(
            "top_process_memory",
            0,
        )

        confidence = round(
            anomaly_result["score"],
            3,
        )

        description = f"""
            Resource anomaly detected.

            Confidence : {confidence}

            CPU Usage : {cpu:.2f} %

            RAM Usage : {ram:.2f} %

            Disk Usage : {disk:.2f} %

            Top Process : {proc}

            Top Process CPU : {proc_cpu:.2f} %

            Top Process Memory : {proc_mem:.2f} %
        """

        return description.strip()

        # ======================================================
    # INCIDENT LIFECYCLE
    # ======================================================

    def acknowledge_incident(
        self,
        incident_id: int,
    ) -> None:
        """
        Marks an incident as acknowledged.

        Used when an administrator starts
        investigating an issue.
        """

        self.db.set_incident_status(
            incident_id,
            "ACKNOWLEDGED",
        )

        logger.info(
            "Incident %s acknowledged.",
            incident_id,
        )

    # ======================================================

    def resolve_incident(
        self,
        incident_id: int,
    ) -> None:
        """
        Resolve a single incident.
        """

        self.db.resolve_incident(
            incident_id
        )

        logger.info(
            "Incident %s resolved.",
            incident_id,
        )

    # ======================================================

    def close_expired_incidents(
        self,
        timeout_minutes: int = 30,
    ) -> int:
        """
        Optional housekeeping.

        Incidents left OPEN for a long time
        but with no recent updates can be
        automatically resolved.

        Returns
        -------
        Number of incidents resolved.
        """

        incidents = self.db.get_expired_incidents(
            timeout_minutes
        )

        count = 0

        for incident in incidents:

            self.db.resolve_incident(
                incident["id"]
            )

            logger.info(
                "Auto-resolved incident %s",
                incident["id"],
            )

            count += 1

        return count

    # ======================================================
    # FUTURE AI HOOKS
    # ======================================================

    def attach_root_cause(
        self,
        incident_id: int,
        root_cause: str,
    ) -> None:
        """
        Placeholder.

        Future RCA Agent will populate this.
        """

        self.db.attach_root_cause(
            incident_id,
            root_cause,
        )

    # ======================================================

    def attach_forecast(
        self,
        incident_id: int,
        forecast: dict,
    ) -> None:
        """
        Placeholder.

        Future Forecasting Engine
        will store predictions here.
        """

        self.db.attach_forecast(
            incident_id,
            forecast,
        )

    # ======================================================

    def attach_agent_decision(
        self,
        incident_id: int,
        decision: str,
    ) -> None:
        """
        Placeholder.

        Supervisor Agent /
        Planner Agent /
        Decision Agent

        will write here.
        """

        self.db.attach_agent_decision(
            incident_id,
            decision,
        )

    # ======================================================

    def attach_remediation(
        self,
        incident_id: int,
        remediation: str,
    ) -> None:
        """
        Placeholder.

        Future Remediation Agent.
        """

        self.db.attach_remediation(
            incident_id,
            remediation,
        )

    # ======================================================

    def get_incident_summary(
        self,
        incident_id: int,
    ) -> dict:
        """
        Central read API.

        Every future component should use this
        instead of reading the database directly.
        """

        return self.db.get_incident(
            incident_id
        )
