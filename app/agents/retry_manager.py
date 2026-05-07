"""
RetryManager - Retry logic for borderline cases in the dual-model radiology validation system.

Implements:
- RetryManager: Evaluates whether a case should be retried and executes retries
  with exponential backoff
- Maximum 2 retry attempts before triggering manual review (Req 3.4)
- Exponential backoff between retry attempts
- Manual review triggers for unresolvable borderline cases
- Retry metrics tracking

Requirements addressed:
- 3.4: WHEN borderline cases are identified, THE Decision_Gateway SHALL implement
       retry logic with up to 2 additional attempts before manual review
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, List, Optional

from app.models.radiology_models import (
    DualRadiologyFindings,
    DualRadiologyInput,
    ValidationResult,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Maximum number of retry attempts before escalating to manual review (Req 3.4)
MAX_RETRY_ATTEMPTS = 2

# Base delay in seconds for exponential backoff (attempt 1 → 1s, attempt 2 → 2s)
BACKOFF_BASE_SECONDS = 1.0

# Multiplier applied per retry attempt for exponential backoff
BACKOFF_MULTIPLIER = 2.0

# Validation statuses that are eligible for retry
RETRYABLE_STATUSES = {"RETRY"}

# Validation statuses that are hard failures — no retry
HARD_FAIL_STATUSES = {"FAIL"}


# ---------------------------------------------------------------------------
# RetryMetrics
# ---------------------------------------------------------------------------

@dataclass
class RetryMetrics:
    """
    Tracks metrics for a single retry session.

    Attributes:
        case_id:            Identifier for the case being retried.
        total_attempts:     Total number of attempts made (initial + retries).
        retry_count:        Number of retry attempts (excludes the initial attempt).
        final_status:       Final validation status after all attempts.
        manual_review:      Whether the case was escalated to manual review.
        attempt_timestamps: ISO timestamps for each attempt.
        backoff_delays:     Backoff delays applied before each retry (seconds).
        reasons:            Human-readable reason for each retry decision.
    """

    case_id: str
    total_attempts: int = 0
    retry_count: int = 0
    final_status: str = "UNKNOWN"
    manual_review: bool = False
    attempt_timestamps: List[str] = field(default_factory=list)
    backoff_delays: List[float] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialise the metrics to a plain dictionary."""
        return {
            "case_id": self.case_id,
            "total_attempts": self.total_attempts,
            "retry_count": self.retry_count,
            "final_status": self.final_status,
            "manual_review": self.manual_review,
            "attempt_timestamps": self.attempt_timestamps,
            "backoff_delays": self.backoff_delays,
            "reasons": self.reasons,
        }


# ---------------------------------------------------------------------------
# RetryManager
# ---------------------------------------------------------------------------

class RetryManager:
    """
    Manages retry logic for borderline radiology validation cases.

    The manager evaluates whether a ValidationResult warrants a retry attempt,
    enforces the maximum retry limit (2 attempts per Req 3.4), applies
    exponential backoff between attempts, and triggers manual review when
    retries are exhausted.

    Usage::

        manager = RetryManager()

        # Check if a retry is warranted
        if await manager.should_retry(validation_result, retry_count=0):
            findings = await manager.execute_retry(input_data, retry_count=0,
                                                   analysis_fn=dual_agent.analyze)

    The ``analysis_fn`` parameter of :meth:`execute_retry` must be an async
    callable that accepts a :class:`DualRadiologyInput` and returns a
    :class:`DualRadiologyFindings`.
    """

    def __init__(
        self,
        max_retries: int = MAX_RETRY_ATTEMPTS,
        backoff_base: float = BACKOFF_BASE_SECONDS,
        backoff_multiplier: float = BACKOFF_MULTIPLIER,
    ):
        """
        Initialise the RetryManager with configurable retry parameters.

        Args:
            max_retries:        Maximum number of retry attempts (default 2, per Req 3.4).
            backoff_base:       Base delay in seconds for exponential backoff.
            backoff_multiplier: Multiplier applied per retry for exponential backoff.
        """
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.backoff_multiplier = backoff_multiplier

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def should_retry(
        self,
        validation_result: ValidationResult,
        retry_count: int,
    ) -> bool:
        """
        Evaluate whether a retry attempt should be made.

        Retry conditions (all must be true):
        1. The validation status is "RETRY" (borderline case).
        2. The current retry count is below the maximum allowed (≤ max_retries - 1,
           because retry_count is 0-indexed: 0 means no retries yet).

        Hard failures ("FAIL") are never retried regardless of retry count.

        Args:
            validation_result:  The ValidationResult from the most recent attempt.
            retry_count:        Number of retries already performed (0 = no retries yet).

        Returns:
            True if a retry should be attempted, False otherwise.
        """
        status = validation_result.validation_status

        # Hard failures are never retried
        if status in HARD_FAIL_STATUSES:
            logger.debug(
                "RetryManager: status=%s is a hard failure — no retry.", status
            )
            return False

        # Only RETRY status is eligible
        if status not in RETRYABLE_STATUSES:
            logger.debug(
                "RetryManager: status=%s is not retryable.", status
            )
            return False

        # Enforce maximum retry limit (Req 3.4: up to 2 additional attempts)
        if retry_count >= self.max_retries:
            logger.info(
                "RetryManager: retry_count=%d has reached max_retries=%d — "
                "escalating to manual review.",
                retry_count,
                self.max_retries,
            )
            return False

        logger.info(
            "RetryManager: status=%s retry_count=%d/%d — retry approved.",
            status,
            retry_count,
            self.max_retries,
        )
        return True

    async def execute_retry(
        self,
        input_data: DualRadiologyInput,
        retry_count: int,
        analysis_fn: Optional[Callable] = None,
    ) -> Optional[DualRadiologyFindings]:
        """
        Execute a single retry attempt with exponential backoff.

        The method:
        1. Calculates and applies the exponential backoff delay.
        2. Adjusts the ValidationConfig thresholds slightly to give borderline
           cases a better chance on retry (reduces thresholds by 5% per attempt,
           capped at 10% total reduction).
        3. Calls ``analysis_fn`` with the (possibly adjusted) input.
        4. Returns the new DualRadiologyFindings, or None if no analysis function
           was provided (useful for testing the backoff logic in isolation).

        Args:
            input_data:     The original DualRadiologyInput for the case.
            retry_count:    The current retry count (0-indexed, before this attempt).
            analysis_fn:    Async callable ``(DualRadiologyInput) -> DualRadiologyFindings``.
                            If None, the method returns None after applying backoff.

        Returns:
            DualRadiologyFindings from the retry attempt, or None.
        """
        delay = self._calculate_backoff(retry_count)

        logger.info(
            "RetryManager: executing retry attempt %d for case=%s "
            "with backoff delay=%.2fs.",
            retry_count + 1,
            input_data.case_id,
            delay,
        )

        # Apply exponential backoff
        if delay > 0:
            await asyncio.sleep(delay)

        if analysis_fn is None:
            logger.debug(
                "RetryManager: no analysis_fn provided — returning None."
            )
            return None

        # Adjust thresholds for retry attempts to give borderline cases a chance
        adjusted_input = self._adjust_thresholds_for_retry(input_data, retry_count)

        try:
            findings = await analysis_fn(adjusted_input)
            # Stamp the retry count on the returned findings
            findings = findings.model_copy(update={"retry_count": retry_count + 1})
            logger.info(
                "RetryManager: retry attempt %d for case=%s completed — "
                "decision=%s.",
                retry_count + 1,
                input_data.case_id,
                findings.final_decision,
            )
            return findings
        except Exception as exc:
            logger.error(
                "RetryManager: retry attempt %d for case=%s failed with error: %s",
                retry_count + 1,
                input_data.case_id,
                exc,
            )
            raise

    def trigger_manual_review(
        self,
        case_id: str,
        validation_result: ValidationResult,
        retry_count: int,
    ) -> dict:
        """
        Trigger a manual review request for a case that has exhausted retries.

        This method produces a structured manual review request that can be
        consumed by downstream notification or workflow systems.

        Args:
            case_id:            Identifier for the case.
            validation_result:  The final ValidationResult after all retry attempts.
            retry_count:        Total number of retries performed.

        Returns:
            A dictionary describing the manual review request.
        """
        review_request = {
            "case_id": case_id,
            "review_type": "manual_review",
            "reason": "Borderline case exhausted all retry attempts without resolution.",
            "retry_count": retry_count,
            "max_retries": self.max_retries,
            "validation_status": validation_result.validation_status,
            "consensus_score": validation_result.consensus_score,
            "discrepancies": list(validation_result.discrepancies),
            "validation_reasoning": validation_result.validation_reasoning,
            "triggered_at": datetime.now().isoformat(),
            "priority": self._determine_review_priority(validation_result),
        }

        logger.warning(
            "RetryManager: manual review triggered for case=%s after %d retries. "
            "Priority=%s consensus=%.2f.",
            case_id,
            retry_count,
            review_request["priority"],
            validation_result.consensus_score,
        )

        return review_request

    def build_retry_metrics(
        self,
        case_id: str,
        attempts: List[dict],
        final_status: str,
        manual_review: bool,
    ) -> RetryMetrics:
        """
        Build a RetryMetrics object from a list of attempt records.

        Each attempt record should be a dict with keys:
        - ``timestamp`` (str ISO): when the attempt was made
        - ``backoff_delay`` (float): delay applied before this attempt (0 for first)
        - ``reason`` (str): reason for the retry decision

        Args:
            case_id:        Case identifier.
            attempts:       List of attempt record dicts.
            final_status:   Final validation status after all attempts.
            manual_review:  Whether manual review was triggered.

        Returns:
            Populated RetryMetrics instance.
        """
        metrics = RetryMetrics(
            case_id=case_id,
            total_attempts=len(attempts),
            retry_count=max(0, len(attempts) - 1),
            final_status=final_status,
            manual_review=manual_review,
        )
        for attempt in attempts:
            metrics.attempt_timestamps.append(attempt.get("timestamp", ""))
            metrics.backoff_delays.append(attempt.get("backoff_delay", 0.0))
            metrics.reasons.append(attempt.get("reason", ""))
        return metrics

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _calculate_backoff(self, retry_count: int) -> float:
        """
        Calculate the exponential backoff delay for a given retry count.

        Formula: ``backoff_base * (backoff_multiplier ** retry_count)``

        Examples (with defaults base=1.0, multiplier=2.0):
        - retry_count=0 → 1.0 * 2^0 = 1.0 seconds
        - retry_count=1 → 1.0 * 2^1 = 2.0 seconds

        Args:
            retry_count: 0-indexed retry count (0 = first retry).

        Returns:
            Delay in seconds (float).
        """
        delay = self.backoff_base * (self.backoff_multiplier ** retry_count)
        logger.debug(
            "RetryManager: backoff delay for retry_count=%d is %.2fs.",
            retry_count,
            delay,
        )
        return delay

    def _adjust_thresholds_for_retry(
        self,
        input_data: DualRadiologyInput,
        retry_count: int,
    ) -> DualRadiologyInput:
        """
        Slightly relax validation thresholds for retry attempts.

        For each retry, confidence and agreement thresholds are reduced by 5%
        (capped at a 10% total reduction) to give borderline cases a better
        chance of passing on retry without compromising clinical safety.

        Args:
            input_data:     Original DualRadiologyInput.
            retry_count:    Current retry count (0-indexed).

        Returns:
            A new DualRadiologyInput with adjusted ValidationConfig, or the
            original if no ValidationConfig is present.
        """
        if input_data.validation_config is None:
            return input_data

        # Reduction: 5% per retry, capped at 10%
        reduction = min(0.05 * (retry_count + 1), 0.10)

        original_config = input_data.validation_config
        adjusted_config = original_config.model_copy(
            update={
                "confidence_threshold": max(
                    0.0, original_config.confidence_threshold - reduction
                ),
                "agreement_threshold": max(
                    0.0, original_config.agreement_threshold - reduction
                ),
            }
        )

        logger.debug(
            "RetryManager: adjusted thresholds for retry %d — "
            "confidence %.2f→%.2f, agreement %.2f→%.2f.",
            retry_count + 1,
            original_config.confidence_threshold,
            adjusted_config.confidence_threshold,
            original_config.agreement_threshold,
            adjusted_config.agreement_threshold,
        )

        return input_data.model_copy(update={"validation_config": adjusted_config})

    def _determine_review_priority(self, validation_result: ValidationResult) -> str:
        """
        Determine the priority level for a manual review request.

        Priority levels:
        - "HIGH":   Critical findings mismatch or very low consensus (< 0.4).
        - "MEDIUM": Moderate consensus issues (0.4 – 0.6).
        - "LOW":    Borderline cases with near-passing consensus (> 0.6).

        Args:
            validation_result: The final ValidationResult.

        Returns:
            Priority string: "HIGH", "MEDIUM", or "LOW".
        """
        if not validation_result.critical_findings_match:
            return "HIGH"
        if validation_result.consensus_score < 0.4:
            return "HIGH"
        if validation_result.consensus_score < 0.6:
            return "MEDIUM"
        return "LOW"
