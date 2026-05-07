"""
AlertManager - Monitoring and alerting for the dual-model radiology validation system.

Emits structured log alerts (and optionally calls registered callbacks) when:
  - Significant model disagreements are detected (Req 2.5)
  - Consecutive model failures exceed the threshold (Req 5.5)
  - System performance degrades (processing time > threshold)
  - Audit trail issues are detected (Req 7.4)

Requirements addressed:
  - 2.5: Flag cases for manual review with detailed discrepancy reports
  - 5.5: Detailed error tracking with model-specific failure analysis
  - 14.1: Performance monitoring dashboards
  - 14.2: Alerting for critical failures and discrepancies
"""

import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Any, Callable, Deque, Dict, List, Optional

logger = logging.getLogger(__name__)

# Dedicated alert logger — operators can route this to a separate sink
alert_logger = logging.getLogger("dual_radiology.alerts")


# ---------------------------------------------------------------------------
# Alert data model
# ---------------------------------------------------------------------------

@dataclass
class Alert:
    """Represents a single alert event."""
    alert_type: str          # e.g. "MODEL_DISAGREEMENT", "CONSECUTIVE_FAILURES"
    severity: str            # "WARNING" | "CRITICAL"
    case_id: Optional[str]
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_type": self.alert_type,
            "severity": self.severity,
            "case_id": self.case_id,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


# ---------------------------------------------------------------------------
# AlertManager
# ---------------------------------------------------------------------------

class AlertManager:
    """
    Centralised alerting for the dual-model radiology validation system.

    Tracks consecutive failures per model, monitors disagreement levels,
    and emits structured alerts when thresholds are breached.

    Thread-safe via a Lock.  Callbacks are called synchronously in the
    thread that triggers the alert — keep them fast.
    """

    _MAX_ALERT_HISTORY = 500

    def __init__(
        self,
        disagreement_threshold: float = 0.5,
        consecutive_failure_threshold: int = 3,
        processing_time_threshold: float = 30.0,
    ) -> None:
        """
        Args:
            disagreement_threshold:        Alert when discrepancy ratio exceeds this.
            consecutive_failure_threshold: Alert after this many consecutive failures.
            processing_time_threshold:     Alert when processing time exceeds this (s).
        """
        self._disagreement_threshold = disagreement_threshold
        self._consecutive_failure_threshold = consecutive_failure_threshold
        self._processing_time_threshold = processing_time_threshold

        self._lock = Lock()
        self._alert_history: Deque[Alert] = deque(maxlen=self._MAX_ALERT_HISTORY)
        self._consecutive_failures: Dict[str, int] = {}   # model_name → count
        self._callbacks: List[Callable[[Alert], None]] = []

        logger.info(
            "AlertManager initialised | disagreement_threshold=%.2f | "
            "consecutive_failure_threshold=%d | processing_time_threshold=%.1fs",
            disagreement_threshold,
            consecutive_failure_threshold,
            processing_time_threshold,
        )

    # ------------------------------------------------------------------
    # Callback registration
    # ------------------------------------------------------------------

    def register_callback(self, callback: Callable[[Alert], None]) -> None:
        """
        Register a function to be called whenever an alert is emitted.

        The callback receives the Alert object.  Exceptions in callbacks
        are caught and logged so they never interrupt the main flow.
        """
        with self._lock:
            self._callbacks.append(callback)

    # ------------------------------------------------------------------
    # Alert triggers
    # ------------------------------------------------------------------

    def check_disagreement(
        self,
        case_id: str,
        consensus_score: float,
        discrepancies: List[str],
    ) -> None:
        """
        Emit a MODEL_DISAGREEMENT alert if consensus_score is below threshold.

        Args:
            case_id:         Case identifier.
            consensus_score: Overall consensus score (0–1).
            discrepancies:   List of identified discrepancy descriptions.
        """
        disagreement = 1.0 - consensus_score
        if disagreement > self._disagreement_threshold:
            alert = Alert(
                alert_type="MODEL_DISAGREEMENT",
                severity="WARNING",
                case_id=case_id,
                message=(
                    f"Significant model disagreement detected: "
                    f"disagreement={disagreement:.2f} > threshold={self._disagreement_threshold:.2f}"
                ),
                details={
                    "consensus_score": consensus_score,
                    "disagreement": disagreement,
                    "threshold": self._disagreement_threshold,
                    "discrepancy_count": len(discrepancies),
                    "discrepancies": discrepancies[:5],  # cap for log size
                },
            )
            self._emit(alert)

    def check_model_failure(self, model_name: str, case_id: str, error: str) -> None:
        """
        Track consecutive failures for a model and alert when threshold is hit.

        Args:
            model_name: Name of the failing model.
            case_id:    Case identifier.
            error:      Error description.
        """
        with self._lock:
            self._consecutive_failures[model_name] = (
                self._consecutive_failures.get(model_name, 0) + 1
            )
            count = self._consecutive_failures[model_name]

        if count >= self._consecutive_failure_threshold:
            alert = Alert(
                alert_type="CONSECUTIVE_FAILURES",
                severity="CRITICAL",
                case_id=case_id,
                message=(
                    f"Model {model_name} has failed {count} consecutive times "
                    f"(threshold={self._consecutive_failure_threshold})"
                ),
                details={
                    "model_name": model_name,
                    "consecutive_failures": count,
                    "threshold": self._consecutive_failure_threshold,
                    "last_error": error,
                },
            )
            self._emit(alert)

    def reset_failure_count(self, model_name: str) -> None:
        """Reset the consecutive failure counter for a model on success."""
        with self._lock:
            self._consecutive_failures[model_name] = 0

    def check_processing_time(self, case_id: str, elapsed: float) -> None:
        """
        Emit a SLOW_PROCESSING alert if elapsed time exceeds the threshold.

        Args:
            case_id: Case identifier.
            elapsed: Total processing time in seconds.
        """
        if elapsed > self._processing_time_threshold:
            alert = Alert(
                alert_type="SLOW_PROCESSING",
                severity="WARNING",
                case_id=case_id,
                message=(
                    f"Processing time {elapsed:.1f}s exceeded threshold "
                    f"{self._processing_time_threshold:.1f}s"
                ),
                details={
                    "elapsed_seconds": elapsed,
                    "threshold_seconds": self._processing_time_threshold,
                },
            )
            self._emit(alert)

    def check_audit_trail(self, case_id: str, missing_fields: List[str]) -> None:
        """
        Emit an AUDIT_TRAIL_INCOMPLETE alert when required fields are absent.

        Args:
            case_id:        Case identifier.
            missing_fields: List of field names that are missing.
        """
        if missing_fields:
            alert = Alert(
                alert_type="AUDIT_TRAIL_INCOMPLETE",
                severity="CRITICAL",
                case_id=case_id,
                message=(
                    f"Audit trail incomplete for case {case_id}: "
                    f"missing fields: {', '.join(missing_fields)}"
                ),
                details={"missing_fields": missing_fields},
            )
            self._emit(alert)

    # ------------------------------------------------------------------
    # Dashboard / introspection
    # ------------------------------------------------------------------

    def get_recent_alerts(self, last_n: int = 20) -> List[Dict[str, Any]]:
        """Return the last N alerts as plain dicts."""
        with self._lock:
            alerts = list(self._alert_history)[-last_n:]
        return [a.to_dict() for a in alerts]

    def get_alert_summary(self) -> Dict[str, Any]:
        """Return a summary of alert counts by type and severity."""
        with self._lock:
            alerts = list(self._alert_history)
            failures = dict(self._consecutive_failures)

        by_type: Dict[str, int] = {}
        by_severity: Dict[str, int] = {}
        for a in alerts:
            by_type[a.alert_type] = by_type.get(a.alert_type, 0) + 1
            by_severity[a.severity] = by_severity.get(a.severity, 0) + 1

        return {
            "total_alerts": len(alerts),
            "by_type": by_type,
            "by_severity": by_severity,
            "consecutive_failures": failures,
            "generated_at": datetime.now().isoformat(),
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _emit(self, alert: Alert) -> None:
        """Store the alert, log it, and invoke registered callbacks."""
        with self._lock:
            self._alert_history.append(alert)

        # Log at appropriate level
        log_fn = alert_logger.critical if alert.severity == "CRITICAL" else alert_logger.warning
        log_fn(
            "ALERT | type=%s | severity=%s | case_id=%s | message=%s | details=%s",
            alert.alert_type,
            alert.severity,
            alert.case_id or "N/A",
            alert.message,
            alert.details,
        )

        # Invoke callbacks (non-blocking, errors swallowed)
        for cb in self._callbacks:
            try:
                cb(alert)
            except Exception as exc:
                logger.warning("Alert callback raised an exception: %s", exc)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

def _build_alert_manager() -> AlertManager:
    from app.utils.config_manager import dual_config
    return AlertManager(
        disagreement_threshold=dual_config.alert_on_disagreement_above,
        consecutive_failure_threshold=dual_config.alert_on_consecutive_failures,
        processing_time_threshold=dual_config.processing_timeout_seconds,
    )


#: Shared AlertManager instance.
#:
#:   from app.utils.alert_manager import alert_manager
alert_manager: AlertManager = _build_alert_manager()
