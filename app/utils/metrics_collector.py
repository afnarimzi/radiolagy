"""
MetricsCollector - Dedicated metrics collection and logging utility for the
dual-model radiology validation system.

Addresses Requirements:
  - 5.1: Log detailed metrics for each model (processing times, confidence scores,
          resource usage)
  - 5.2: Log agreement percentages, discrepancy types, and validation outcomes
  - 5.3: Log decision rationale, threshold comparisons, and retry attempts
  - 5.4: Maintain performance dashboards showing consensus rates, model reliability,
          and system throughput
  - 5.5: Detailed error tracking with model-specific failure analysis
"""

import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Any, Deque, Dict, List, Optional, Tuple

from app.models.radiology_models import (
    ConsensusMetrics,
    DualRadiologyFindings,
    ModelOutput,
    ValidationResult,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Discrepancy category constants (Req 5.2)
# ---------------------------------------------------------------------------

DISCREPANCY_CONFIDENCE = "confidence_threshold"
DISCREPANCY_QUALITY = "image_quality"
DISCREPANCY_CRITICAL_FINDINGS = "critical_findings"
DISCREPANCY_SEMANTIC = "semantic_similarity"
DISCREPANCY_KAPPA = "inter_rater_agreement"
DISCREPANCY_OTHER = "other"


def _categorise_discrepancy(discrepancy: str) -> str:
    """
    Map a free-text discrepancy description to a structured category.

    Returns one of the DISCREPANCY_* constants.
    """
    d = discrepancy.lower()
    if "confidence" in d:
        return DISCREPANCY_CONFIDENCE
    if "quality" in d:
        return DISCREPANCY_QUALITY
    if "critical" in d:
        return DISCREPANCY_CRITICAL_FINDINGS
    if "semantic" in d or "similarity" in d:
        return DISCREPANCY_SEMANTIC
    if "kappa" in d or "inter-rater" in d or "agreement" in d:
        return DISCREPANCY_KAPPA
    return DISCREPANCY_OTHER


# ---------------------------------------------------------------------------
# Internal data containers
# ---------------------------------------------------------------------------

@dataclass
class ModelMetricRecord:
    """Single record of per-model metrics for one analysis run (Req 5.1)."""
    case_id: str
    model_name: str
    processing_time: float
    confidence_score: float
    success: bool
    error_message: Optional[str]
    # Resource usage fields (Req 5.1 — resource usage logging)
    tokens_used: Optional[int] = None
    api_latency_ms: Optional[float] = None
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ConsensusMetricRecord:
    """Single record of consensus / validation metrics (Req 5.2)."""
    case_id: str
    consensus_score: float
    abnormality_agreement: float
    cohens_kappa: float
    semantic_similarity: float
    exact_match_percentage: float
    clinical_significance_alignment: float
    quality_agreement: bool
    discrepancy_count: int
    discrepancy_types: List[str]
    # Structured discrepancy category breakdown (Req 5.2)
    discrepancy_categories: Dict[str, int] = field(default_factory=dict)
    validation_status: str = "UNKNOWN"
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DecisionMetricRecord:
    """Single record of decision-gateway metrics (Req 5.3)."""
    case_id: str
    decision: str
    confidence_passed: bool
    critical_consensus_passed: bool
    overall_consensus_passed: bool
    quality_passed: bool
    retry_recommended: bool
    manual_review_required: bool
    retry_count: int
    reasoning: str
    # Threshold comparison details (Req 5.3)
    threshold_details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ErrorMetricRecord:
    """Single record of a model-specific error event (Req 5.5)."""
    case_id: str
    model_name: str
    error_type: str
    error_message: str
    is_recoverable: bool
    fallback_used: bool
    timestamp: datetime = field(default_factory=datetime.now)


# ---------------------------------------------------------------------------
# MetricsCollector
# ---------------------------------------------------------------------------

class MetricsCollector:
    """
    Centralised metrics collection and structured logging for the dual-model
    radiology validation system.

    Responsibilities
    ----------------
    1. Collect and log per-model metrics (processing time, confidence, resource usage).
    2. Collect and log consensus / validation metrics (agreement, discrepancy types).
    3. Collect and log decision-gateway metrics (rationale, threshold comparisons, retries).
    4. Maintain rolling in-memory statistics for performance dashboards.
    5. Track model-specific errors with failure analysis (Req 5.5).

    Thread Safety
    -------------
    All mutations to shared state are protected by a ``threading.Lock`` so the
    collector is safe to use from multiple async tasks running in the same
    process (asyncio runs in a single thread, but the lock adds no overhead and
    makes the class safe if used from a thread pool as well).

    Usage
    -----
    Instantiate once and share across the application (or use the module-level
    ``metrics_collector`` singleton)::

        from app.utils.metrics_collector import metrics_collector

        # After a completed analysis:
        metrics_collector.record_findings(findings)

        # For dashboard data:
        stats = metrics_collector.get_dashboard_stats()
    """

    # Maximum number of records kept in each rolling window
    _MAX_WINDOW: int = 1000

    def __init__(self) -> None:
        self._lock = Lock()

        # Rolling windows (deque with maxlen caps memory usage)
        self._model_records: Deque[ModelMetricRecord] = deque(
            maxlen=self._MAX_WINDOW
        )
        self._consensus_records: Deque[ConsensusMetricRecord] = deque(
            maxlen=self._MAX_WINDOW
        )
        self._decision_records: Deque[DecisionMetricRecord] = deque(
            maxlen=self._MAX_WINDOW
        )
        # Error records for model-specific failure analysis (Req 5.5)
        self._error_records: Deque[ErrorMetricRecord] = deque(
            maxlen=self._MAX_WINDOW
        )

        # Aggregate counters (never reset — represent lifetime totals)
        self._total_analyses: int = 0
        self._total_pass: int = 0
        self._total_fail: int = 0
        self._total_retries: int = 0
        self._model_success_counts: Dict[str, int] = defaultdict(int)
        self._model_failure_counts: Dict[str, int] = defaultdict(int)
        # Discrepancy category totals for dashboard (Req 5.2)
        self._discrepancy_category_totals: Dict[str, int] = defaultdict(int)

        # Throughput tracking
        self._analysis_start_times: Deque[float] = deque(maxlen=self._MAX_WINDOW)

        logger.info("MetricsCollector initialised.")

    # ------------------------------------------------------------------
    # High-level convenience method
    # ------------------------------------------------------------------

    def record_findings(self, findings: DualRadiologyFindings) -> None:
        """
        Extract and record all metrics from a completed DualRadiologyFindings
        object.  This is a convenience entry point for post-analysis logging.

        Internally calls:
        - ``record_model_metrics`` for both Gemini and Groq outputs
        - ``record_consensus_metrics`` for the validation result
        - ``record_decision`` for the final decision

        Note: When using DualRadiologyAgent directly, per-attempt decision
        metrics are recorded in ``_log_decision`` during the validation loop.
        This method is provided for callers that only have the final findings.

        Args:
            findings: Completed DualRadiologyFindings from DualRadiologyAgent.
        """
        self.record_model_metrics(
            case_id=findings.case_id,
            model_output=findings.gemini_output,
            success=findings.gemini_output.confidence > 0.0,
        )
        self.record_model_metrics(
            case_id=findings.case_id,
            model_output=findings.groq_output,
            success=findings.groq_output.confidence > 0.0,
        )
        self.record_consensus_metrics(
            case_id=findings.case_id,
            validation_result=findings.validation_result,
            consensus_metrics=findings.consensus_metrics,
        )
        self.record_decision(
            case_id=findings.case_id,
            decision=findings.final_decision,
            reasoning=findings.decision_reasoning,
            retry_count=findings.retry_count,
            validation_result=findings.validation_result,
        )

    # ------------------------------------------------------------------
    # Requirement 5.1 — per-model metrics
    # ------------------------------------------------------------------

    def record_model_metrics(
        self,
        case_id: str,
        model_output: ModelOutput,
        error_message: Optional[str] = None,
        success: Optional[bool] = None,
        resource_usage: Optional[Dict[str, Any]] = None,
        tokens_used: Optional[int] = None,
        api_latency_ms: Optional[float] = None,
    ) -> None:
        """
        Log and store detailed metrics for a single model output (Req 5.1).

        Logs: model name, processing time, confidence score, success/failure,
        resource usage (tokens, API latency, memory), and optional error message.

        Args:
            case_id:        Unique case identifier.
            model_output:   ModelOutput from Gemini or Groq.
            error_message:  Optional error description if the model failed.
            success:        Explicit success flag. When None, inferred from
                            confidence > 0.0 (backward-compatible default).
            resource_usage: Optional dict of resource usage metrics (e.g.
                            {"memory_mb": 128, "cpu_percent": 12.5}).
            tokens_used:    Optional token count consumed by the model call.
            api_latency_ms: Optional raw API round-trip latency in milliseconds.
        """
        # Determine success: explicit flag takes priority; fall back to confidence heuristic
        is_success = success if success is not None else (model_output.confidence > 0.0)

        # Build resource_usage dict, merging any extra fields provided
        usage: Dict[str, Any] = {}
        if resource_usage:
            usage.update(resource_usage)
        if tokens_used is not None:
            usage["tokens_used"] = tokens_used
        if api_latency_ms is not None:
            usage["api_latency_ms"] = api_latency_ms
        # Always record processing_time in resource_usage for completeness
        usage.setdefault("processing_time_s", model_output.processing_time)

        record = ModelMetricRecord(
            case_id=case_id,
            model_name=model_output.model_name,
            processing_time=model_output.processing_time,
            confidence_score=model_output.confidence,
            success=is_success,
            error_message=error_message,
            tokens_used=tokens_used,
            api_latency_ms=api_latency_ms,
            resource_usage=usage,
        )

        with self._lock:
            self._model_records.append(record)
            if is_success:
                self._model_success_counts[model_output.model_name] += 1
            else:
                self._model_failure_counts[model_output.model_name] += 1

        logger.info(
            "METRICS | model | case_id=%s | model=%s | "
            "processing_time=%.3fs | confidence=%.3f | "
            "success=%s | tokens=%s | api_latency_ms=%s | error=%s",
            case_id,
            model_output.model_name,
            model_output.processing_time,
            model_output.confidence,
            is_success,
            tokens_used if tokens_used is not None else "n/a",
            f"{api_latency_ms:.1f}" if api_latency_ms is not None else "n/a",
            error_message or "none",
        )
        if usage:
            logger.debug(
                "METRICS | model_resource_usage | case_id=%s | model=%s | usage=%s",
                case_id,
                model_output.model_name,
                usage,
            )

    # ------------------------------------------------------------------
    # Requirement 5.2 — consensus / validation metrics
    # ------------------------------------------------------------------

    def record_consensus_metrics(
        self,
        case_id: str,
        validation_result: ValidationResult,
        consensus_metrics: ConsensusMetrics,
    ) -> None:
        """
        Log and store consensus analysis metrics (Req 5.2).

        Logs: agreement percentages, discrepancy types (categorised), validation
        outcome, Cohen's Kappa, semantic similarity, and quality agreement.

        Discrepancies are categorised into structured types for dashboard
        aggregation:
          - ``confidence_threshold``: confidence score failures
          - ``image_quality``:        quality assessment disagreements
          - ``critical_findings``:    critical finding mismatches
          - ``semantic_similarity``:  low semantic similarity
          - ``inter_rater_agreement``: low Cohen's Kappa
          - ``other``:                uncategorised discrepancies

        Args:
            case_id:           Unique case identifier.
            validation_result: ValidationResult from ValidatorAgent.
            consensus_metrics: ConsensusMetrics from ValidatorAgent.
        """
        # Categorise each discrepancy for structured tracking (Req 5.2)
        discrepancy_categories: Dict[str, int] = defaultdict(int)
        for d in validation_result.discrepancies:
            cat = _categorise_discrepancy(d)
            discrepancy_categories[cat] += 1

        record = ConsensusMetricRecord(
            case_id=case_id,
            consensus_score=validation_result.consensus_score,
            abnormality_agreement=validation_result.abnormality_agreement,
            cohens_kappa=consensus_metrics.cohens_kappa,
            semantic_similarity=consensus_metrics.semantic_similarity_score,
            exact_match_percentage=consensus_metrics.exact_match_percentage,
            clinical_significance_alignment=consensus_metrics.clinical_significance_alignment,
            quality_agreement=consensus_metrics.quality_agreement,
            discrepancy_count=len(validation_result.discrepancies),
            discrepancy_types=list(validation_result.discrepancies),
            discrepancy_categories=dict(discrepancy_categories),
            validation_status=validation_result.validation_status,
        )

        with self._lock:
            self._consensus_records.append(record)
            # Accumulate discrepancy category totals for dashboard (Req 5.2)
            for cat, count in discrepancy_categories.items():
                self._discrepancy_category_totals[cat] += count

        logger.info(
            "METRICS | consensus | case_id=%s | status=%s | "
            "consensus_score=%.3f | abnormality_agreement=%.3f | "
            "cohens_kappa=%.3f | semantic_similarity=%.3f | "
            "exact_match_pct=%.1f | clinical_alignment=%.3f | "
            "quality_agreement=%s | discrepancy_count=%d",
            case_id,
            validation_result.validation_status,
            validation_result.consensus_score,
            validation_result.abnormality_agreement,
            consensus_metrics.cohens_kappa,
            consensus_metrics.semantic_similarity_score,
            consensus_metrics.exact_match_percentage,
            consensus_metrics.clinical_significance_alignment,
            consensus_metrics.quality_agreement,
            len(validation_result.discrepancies),
        )

        if validation_result.discrepancies:
            logger.info(
                "METRICS | discrepancies | case_id=%s | categories=%s | details=%s",
                case_id,
                dict(discrepancy_categories),
                " | ".join(validation_result.discrepancies),
            )

    # ------------------------------------------------------------------
    # Requirement 5.3 — decision rationale and retry tracking
    # ------------------------------------------------------------------

    def record_decision(
        self,
        case_id: str,
        decision: str,
        reasoning: str,
        retry_count: int,
        validation_result: Optional[ValidationResult] = None,
        confidence_passed: bool = False,
        critical_consensus_passed: bool = False,
        overall_consensus_passed: bool = False,
        quality_passed: bool = False,
        retry_recommended: bool = False,
        manual_review_required: bool = False,
        threshold_details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log and store decision-gateway metrics (Req 5.3).

        Logs: final decision, threshold comparison results (with actual vs.
        required values), retry count, manual review flag, and full decision
        reasoning.

        Args:
            case_id:                   Unique case identifier.
            decision:                  "PASS", "FAIL", or "RETRY".
            reasoning:                 Human-readable decision rationale.
            retry_count:               Number of retries already attempted.
            validation_result:         Optional ValidationResult for deriving
                                       threshold flags when not supplied directly.
            confidence_passed:         Whether confidence threshold was met.
            critical_consensus_passed: Whether critical consensus threshold met.
            overall_consensus_passed:  Whether overall consensus threshold met.
            quality_passed:            Whether quality threshold was met.
            retry_recommended:         Whether a retry was recommended.
            manual_review_required:    Whether manual review was triggered.
            threshold_details:         Optional dict mapping threshold names to
                                       their actual vs. required values (from
                                       DecisionReport.threshold_details). When
                                       provided, this is stored verbatim and
                                       logged for full transparency (Req 5.3).
        """
        # Derive threshold flags from validation_result when not provided
        if validation_result is not None:
            confidence_passed = validation_result.confidence_validation
            quality_passed = validation_result.quality_validation
            critical_consensus_passed = validation_result.critical_findings_match
            overall_consensus_passed = (
                validation_result.validation_status == "PASS"
            )
            retry_recommended = validation_result.validation_status == "RETRY"
            manual_review_required = (
                decision == "FAIL" and retry_count > 0
            )

        record = DecisionMetricRecord(
            case_id=case_id,
            decision=decision,
            confidence_passed=confidence_passed,
            critical_consensus_passed=critical_consensus_passed,
            overall_consensus_passed=overall_consensus_passed,
            quality_passed=quality_passed,
            retry_recommended=retry_recommended,
            manual_review_required=manual_review_required,
            retry_count=retry_count,
            reasoning=reasoning,
            threshold_details=threshold_details or {},
        )

        with self._lock:
            self._decision_records.append(record)
            self._total_analyses += 1
            if decision == "PASS":
                self._total_pass += 1
            elif decision == "FAIL":
                self._total_fail += 1
            self._total_retries += retry_count
            self._analysis_start_times.append(time.time())

        logger.info(
            "METRICS | decision | case_id=%s | decision=%s | "
            "confidence_passed=%s | critical_consensus_passed=%s | "
            "overall_consensus_passed=%s | quality_passed=%s | "
            "retry_recommended=%s | manual_review_required=%s | "
            "retry_count=%d",
            case_id,
            decision,
            confidence_passed,
            critical_consensus_passed,
            overall_consensus_passed,
            quality_passed,
            retry_recommended,
            manual_review_required,
            retry_count,
        )
        logger.info(
            "METRICS | decision_reasoning | case_id=%s | reasoning=%s",
            case_id,
            reasoning,
        )
        # Log threshold comparison details when available (Req 5.3)
        if threshold_details:
            logger.info(
                "METRICS | threshold_comparisons | case_id=%s | details=%s",
                case_id,
                threshold_details,
            )

    # ------------------------------------------------------------------
    # Requirement 5.4 — performance dashboard data
    # ------------------------------------------------------------------

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        Return aggregated performance statistics suitable for a dashboard
        (Req 5.4).

        Returns a dictionary with the following top-level keys:

        ``summary``
            Lifetime totals: total analyses, pass/fail counts, pass rate,
            total retries, and average retry rate.

        ``model_reliability``
            Per-model success rates and average confidence/processing-time
            computed from the rolling window.

        ``consensus_rates``
            Rolling-window averages for consensus score, Cohen's Kappa,
            semantic similarity, abnormality agreement, and quality agreement
            rate.  Also includes a discrepancy category breakdown.

        ``throughput``
            Estimated analyses per minute based on the rolling window of
            recorded timestamps.

        ``recent_decisions``
            Last 10 decision records as plain dicts for quick inspection.

        ``error_analysis``
            Model-specific error counts and recent error records (Req 5.5).

        Returns:
            Dict with dashboard statistics.
        """
        with self._lock:
            model_records = list(self._model_records)
            consensus_records = list(self._consensus_records)
            decision_records = list(self._decision_records)
            error_records = list(self._error_records)
            total_analyses = self._total_analyses
            total_pass = self._total_pass
            total_fail = self._total_fail
            total_retries = self._total_retries
            model_success = dict(self._model_success_counts)
            model_failure = dict(self._model_failure_counts)
            timestamps = list(self._analysis_start_times)
            discrepancy_totals = dict(self._discrepancy_category_totals)

        # --- Summary ---
        pass_rate = (total_pass / total_analyses * 100) if total_analyses else 0.0
        avg_retry_rate = (total_retries / total_analyses) if total_analyses else 0.0

        summary = {
            "total_analyses": total_analyses,
            "total_pass": total_pass,
            "total_fail": total_fail,
            "pass_rate_pct": round(pass_rate, 2),
            "total_retries": total_retries,
            "avg_retry_rate": round(avg_retry_rate, 3),
        }

        # --- Model reliability ---
        model_reliability: Dict[str, Any] = {}
        all_model_names = set(model_success.keys()) | set(model_failure.keys())
        for model_name in all_model_names:
            successes = model_success.get(model_name, 0)
            failures = model_failure.get(model_name, 0)
            total = successes + failures
            model_records_for = [
                r for r in model_records if r.model_name == model_name
            ]
            avg_confidence = (
                sum(r.confidence_score for r in model_records_for) / len(model_records_for)
                if model_records_for
                else 0.0
            )
            avg_processing_time = (
                sum(r.processing_time for r in model_records_for) / len(model_records_for)
                if model_records_for
                else 0.0
            )
            # Resource usage aggregation (Req 5.1)
            token_records = [
                r.tokens_used for r in model_records_for if r.tokens_used is not None
            ]
            latency_records = [
                r.api_latency_ms for r in model_records_for if r.api_latency_ms is not None
            ]
            model_reliability[model_name] = {
                "total_runs": total,
                "successes": successes,
                "failures": failures,
                "success_rate_pct": round(successes / total * 100, 2) if total else 0.0,
                "avg_confidence": round(avg_confidence, 3),
                "avg_processing_time_s": round(avg_processing_time, 3),
                "avg_tokens_used": (
                    round(sum(token_records) / len(token_records), 1)
                    if token_records else None
                ),
                "avg_api_latency_ms": (
                    round(sum(latency_records) / len(latency_records), 1)
                    if latency_records else None
                ),
            }

        # --- Consensus rates (rolling window) ---
        if consensus_records:
            n = len(consensus_records)
            # Aggregate discrepancy categories across rolling window (Req 5.2)
            window_discrepancy_cats: Dict[str, int] = defaultdict(int)
            for r in consensus_records:
                for cat, cnt in r.discrepancy_categories.items():
                    window_discrepancy_cats[cat] += cnt

            consensus_rates = {
                "window_size": n,
                "avg_consensus_score": round(
                    sum(r.consensus_score for r in consensus_records) / n, 3
                ),
                "avg_cohens_kappa": round(
                    sum(r.cohens_kappa for r in consensus_records) / n, 3
                ),
                "avg_semantic_similarity": round(
                    sum(r.semantic_similarity for r in consensus_records) / n, 3
                ),
                "avg_abnormality_agreement": round(
                    sum(r.abnormality_agreement for r in consensus_records) / n, 3
                ),
                "quality_agreement_rate_pct": round(
                    sum(1 for r in consensus_records if r.quality_agreement) / n * 100, 2
                ),
                "avg_discrepancy_count": round(
                    sum(r.discrepancy_count for r in consensus_records) / n, 2
                ),
                "validation_status_breakdown": _count_by(
                    consensus_records, "validation_status"
                ),
                # Structured discrepancy type breakdown (Req 5.2)
                "discrepancy_category_breakdown": dict(window_discrepancy_cats),
                "lifetime_discrepancy_totals": discrepancy_totals,
            }
        else:
            consensus_rates = {
                "window_size": 0,
                "avg_consensus_score": 0.0,
                "avg_cohens_kappa": 0.0,
                "avg_semantic_similarity": 0.0,
                "avg_abnormality_agreement": 0.0,
                "quality_agreement_rate_pct": 0.0,
                "avg_discrepancy_count": 0.0,
                "validation_status_breakdown": {},
                "discrepancy_category_breakdown": {},
                "lifetime_discrepancy_totals": discrepancy_totals,
            }

        # --- Throughput (analyses per minute over rolling window) ---
        throughput = _calculate_throughput(timestamps)

        # --- Recent decisions (last 10) ---
        recent = decision_records[-10:]
        recent_decisions = [
            {
                "case_id": r.case_id,
                "decision": r.decision,
                "retry_count": r.retry_count,
                "manual_review_required": r.manual_review_required,
                "confidence_passed": r.confidence_passed,
                "quality_passed": r.quality_passed,
                "critical_consensus_passed": r.critical_consensus_passed,
                "timestamp": r.timestamp.isoformat(),
            }
            for r in recent
        ]

        # --- Error analysis (Req 5.5) ---
        error_analysis = self._build_error_analysis(error_records)

        return {
            "summary": summary,
            "model_reliability": model_reliability,
            "consensus_rates": consensus_rates,
            "throughput": throughput,
            "recent_decisions": recent_decisions,
            "error_analysis": error_analysis,
            "generated_at": datetime.now().isoformat(),
        }

    # ------------------------------------------------------------------
    # Requirement 5.5 — error tracking with model-specific failure analysis
    # ------------------------------------------------------------------

    def record_error(
        self,
        case_id: str,
        model_name: str,
        error_type: str,
        error_message: str,
        is_recoverable: bool = True,
        fallback_used: bool = False,
    ) -> None:
        """
        Record a model-specific error event for failure analysis (Req 5.5).

        This supplements ``record_model_metrics`` with richer error context,
        enabling per-model failure pattern analysis in the dashboard.

        Args:
            case_id:        Unique case identifier.
            model_name:     Name of the failing model.
            error_type:     Short error category (e.g. "api_error", "timeout",
                            "rate_limit", "parse_error").
            error_message:  Full error description.
            is_recoverable: Whether the system can continue with fallback.
            fallback_used:  Whether single-model fallback was activated.
        """
        record = ErrorMetricRecord(
            case_id=case_id,
            model_name=model_name,
            error_type=error_type,
            error_message=error_message,
            is_recoverable=is_recoverable,
            fallback_used=fallback_used,
        )

        with self._lock:
            self._error_records.append(record)

        logger.warning(
            "METRICS | error | case_id=%s | model=%s | error_type=%s | "
            "recoverable=%s | fallback_used=%s | message=%s",
            case_id,
            model_name,
            error_type,
            is_recoverable,
            fallback_used,
            error_message,
        )

    @staticmethod
    def _build_error_analysis(error_records: List[ErrorMetricRecord]) -> Dict[str, Any]:
        """
        Build error analysis section for the dashboard (Req 5.5).

        Returns per-model error counts, error type breakdown, and recent errors.
        """
        if not error_records:
            return {
                "total_errors": 0,
                "by_model": {},
                "by_error_type": {},
                "recoverable_count": 0,
                "fallback_used_count": 0,
                "recent_errors": [],
            }

        by_model: Dict[str, int] = defaultdict(int)
        by_type: Dict[str, int] = defaultdict(int)
        recoverable = 0
        fallback_used = 0

        for r in error_records:
            by_model[r.model_name] += 1
            by_type[r.error_type] += 1
            if r.is_recoverable:
                recoverable += 1
            if r.fallback_used:
                fallback_used += 1

        recent = error_records[-5:]
        return {
            "total_errors": len(error_records),
            "by_model": dict(by_model),
            "by_error_type": dict(by_type),
            "recoverable_count": recoverable,
            "fallback_used_count": fallback_used,
            "recent_errors": [
                {
                    "case_id": r.case_id,
                    "model_name": r.model_name,
                    "error_type": r.error_type,
                    "is_recoverable": r.is_recoverable,
                    "fallback_used": r.fallback_used,
                    "timestamp": r.timestamp.isoformat(),
                }
                for r in recent
            ],
        }

    # ------------------------------------------------------------------
    # Utility / introspection
    # ------------------------------------------------------------------

    def get_model_stats(self, model_name: str) -> Dict[str, Any]:
        """
        Return rolling-window statistics for a specific model.

        Args:
            model_name: Exact model name string (e.g. "gemini-2.5-flash").

        Returns:
            Dict with success_rate, avg_confidence, avg_processing_time,
            and record count.
        """
        with self._lock:
            records = [r for r in self._model_records if r.model_name == model_name]

        if not records:
            return {"model_name": model_name, "record_count": 0}

        n = len(records)
        successes = sum(1 for r in records if r.success)
        return {
            "model_name": model_name,
            "record_count": n,
            "success_rate_pct": round(successes / n * 100, 2),
            "avg_confidence": round(sum(r.confidence_score for r in records) / n, 3),
            "avg_processing_time_s": round(
                sum(r.processing_time for r in records) / n, 3
            ),
        }

    def get_consensus_trend(self, last_n: int = 50) -> List[Dict[str, Any]]:
        """
        Return the last *n* consensus metric records as plain dicts for
        trend analysis.

        Args:
            last_n: Number of most-recent records to return (default 50).

        Returns:
            List of dicts with consensus metrics ordered oldest-first.
        """
        with self._lock:
            records = list(self._consensus_records)[-last_n:]

        return [
            {
                "case_id": r.case_id,
                "consensus_score": r.consensus_score,
                "cohens_kappa": r.cohens_kappa,
                "semantic_similarity": r.semantic_similarity,
                "abnormality_agreement": r.abnormality_agreement,
                "validation_status": r.validation_status,
                "timestamp": r.timestamp.isoformat(),
            }
            for r in records
        ]

    def reset(self) -> None:
        """
        Clear all in-memory records and reset counters.

        Intended for testing only — do not call in production.
        """
        with self._lock:
            self._model_records.clear()
            self._consensus_records.clear()
            self._decision_records.clear()
            self._error_records.clear()
            self._total_analyses = 0
            self._total_pass = 0
            self._total_fail = 0
            self._total_retries = 0
            self._model_success_counts.clear()
            self._model_failure_counts.clear()
            self._analysis_start_times.clear()
            self._discrepancy_category_totals.clear()
        logger.info("MetricsCollector reset.")


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _count_by(records: List[Any], attr: str) -> Dict[str, int]:
    """Return a frequency dict for the given attribute across records."""
    counts: Dict[str, int] = defaultdict(int)
    for r in records:
        counts[getattr(r, attr)] += 1
    return dict(counts)


def _calculate_throughput(timestamps: List[float]) -> Dict[str, Any]:
    """
    Estimate analyses-per-minute from a list of epoch timestamps.

    Uses a 60-second sliding window to compute the current rate.
    """
    if not timestamps:
        return {"analyses_per_minute": 0.0, "window_seconds": 60}

    now = time.time()
    window_start = now - 60.0
    recent = [t for t in timestamps if t >= window_start]
    return {
        "analyses_per_minute": round(len(recent), 2),
        "window_seconds": 60,
        "total_recorded": len(timestamps),
    }


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

#: Shared MetricsCollector instance — import and use directly:
#:
#:   from app.utils.metrics_collector import metrics_collector
metrics_collector = MetricsCollector()
