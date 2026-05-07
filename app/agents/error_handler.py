"""
ErrorHandler - Graceful degradation and failure management for the dual-model
radiology validation system.

Handles:
  - Groq API failures
  - Gemini API failures
  - Partial validation when only one model succeeds
  - Detailed error tracking and logging (Requirements 1.3, 5.5)
"""
import logging
from datetime import datetime
from typing import Optional

from app.models.dual_radiology_models import (
    DualRadiologyFindings,
    ModelOutput,
    ValidationResult,
    ConsensusMetrics,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# When operating in single-model mode the confidence is penalised because we
# cannot perform cross-model consensus validation.
_SINGLE_MODEL_CONFIDENCE_PENALTY = 0.15

# Reduced consensus score used when only one model is available.
_SINGLE_MODEL_CONSENSUS_SCORE = 0.5

# Placeholder model name used to represent a failed model in the output.
_FAILED_MODEL_PLACEHOLDER = "unavailable"


# ---------------------------------------------------------------------------
# Stub ModelOutput factory
# ---------------------------------------------------------------------------

def _make_failed_model_output(failed_model: str, error_message: str) -> ModelOutput:
    """
    Build a ModelOutput that represents a model that failed to produce results.

    The output carries zero confidence and clearly marks itself as an error
    so downstream consumers can distinguish it from a real (low-confidence)
    analysis.
    """
    return ModelOutput(
        model_name=failed_model,
        findings=f"Model failed: {error_message}",
        abnormalities=[],
        anatomical_structures=[],
        confidence=0.0,
        image_quality="unknown",
        recommendations="Manual review required — model analysis unavailable.",
        processing_time=0.0,
        timestamp=datetime.now(),
        raw_response=None,
    )


# ---------------------------------------------------------------------------
# Stub ConsensusMetrics factory
# ---------------------------------------------------------------------------

def _make_single_model_consensus_metrics() -> ConsensusMetrics:
    """
    Return a ConsensusMetrics object that reflects the absence of a second
    model.  All agreement metrics are set to neutral/zero values.
    """
    return ConsensusMetrics(
        exact_match_percentage=0.0,
        semantic_similarity_score=0.0,
        clinical_significance_alignment=0.0,
        cohens_kappa=0.0,
        abnormality_overlap_ratio=0.0,
        confidence_correlation=0.0,
        quality_agreement=False,
    )


# ---------------------------------------------------------------------------
# ErrorHandler
# ---------------------------------------------------------------------------

class ErrorHandler:
    """
    Manages model failures and provides graceful degradation for the
    dual-model radiology validation system.

    When one model fails the system should not halt; instead it should:
      1. Log the failure with enough detail for monitoring (Req 5.5).
      2. Continue with the successful model's output (Req 1.3).
      3. Adjust confidence scores to reflect reduced certainty.
      4. Return a DualRadiologyFindings marked as partial validation.
    """

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def handle_model_failure(
        self,
        failed_model: str,
        successful_output: ModelOutput,
        case_id: str,
        error_message: str = "Unknown error",
        error_type: Optional[str] = None,
    ) -> DualRadiologyFindings:
        """
        Handle a single-model failure and return partial validation findings.

        Args:
            failed_model:      Name of the model that failed (e.g. "groq" or
                               "gemini").
            successful_output: The ModelOutput produced by the surviving model.
            case_id:           Case identifier for logging and output.
            error_message:     Human-readable description of the failure.
            error_type:        Optional classification of the error (e.g.
                               "APIError", "RateLimitError").

        Returns:
            DualRadiologyFindings with partial validation results and
            appropriate flags set.
        """
        self._log_model_failure(
            failed_model=failed_model,
            case_id=case_id,
            error_message=error_message,
            error_type=error_type,
        )

        # Penalise confidence because we cannot cross-validate.
        adjusted_output = self._adjust_confidence(successful_output)

        # Build stub output for the failed model.
        failed_output = _make_failed_model_output(
            failed_model=failed_model,
            error_message=error_message,
        )

        # Determine which slot (gemini / groq) each output occupies.
        gemini_output, groq_output = self._assign_outputs(
            failed_model=failed_model,
            successful_output=adjusted_output,
            failed_output=failed_output,
        )

        validation_result = self._build_partial_validation_result(
            failed_model=failed_model,
            successful_output=adjusted_output,
            error_message=error_message,
        )

        consensus_metrics = _make_single_model_consensus_metrics()

        decision_reasoning = (
            f"Partial validation: {failed_model} model failed ({error_message}). "
            f"Analysis based solely on {successful_output.model_name} output. "
            f"Confidence adjusted from {successful_output.confidence:.2f} to "
            f"{adjusted_output.confidence:.2f} due to absence of cross-model "
            f"consensus. Manual review recommended."
        )

        findings = DualRadiologyFindings(
            case_id=case_id,
            gemini_output=gemini_output,
            groq_output=groq_output,
            validation_result=validation_result,
            consensus_metrics=consensus_metrics,
            final_decision="FAIL",
            decision_reasoning=decision_reasoning,
            retry_count=0,
            timestamp=datetime.now(),
        )

        logger.info(
            "Partial validation findings created for case_id=%s "
            "(failed_model=%s, adjusted_confidence=%.2f)",
            case_id,
            failed_model,
            adjusted_output.confidence,
        )

        return findings

    async def handle_groq_failure(
        self,
        gemini_output: ModelOutput,
        case_id: str,
        error_message: str = "Groq API failure",
        error_type: Optional[str] = None,
    ) -> DualRadiologyFindings:
        """
        Convenience wrapper for Groq-specific failures.

        Delegates to handle_model_failure with failed_model="groq".
        """
        logger.warning(
            "Groq API failure detected for case_id=%s — falling back to "
            "Gemini-only analysis. Error: %s",
            case_id,
            error_message,
        )
        return await self.handle_model_failure(
            failed_model="groq",
            successful_output=gemini_output,
            case_id=case_id,
            error_message=error_message,
            error_type=error_type or "GroqAPIError",
        )

    async def handle_gemini_failure(
        self,
        groq_output: ModelOutput,
        case_id: str,
        error_message: str = "Gemini API failure",
        error_type: Optional[str] = None,
    ) -> DualRadiologyFindings:
        """
        Convenience wrapper for Gemini-specific failures.

        Delegates to handle_model_failure with failed_model="gemini".
        """
        logger.warning(
            "Gemini API failure detected for case_id=%s — falling back to "
            "Groq-only analysis. Error: %s",
            case_id,
            error_message,
        )
        return await self.handle_model_failure(
            failed_model="gemini",
            successful_output=groq_output,
            case_id=case_id,
            error_message=error_message,
            error_type=error_type or "GeminiAPIError",
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _log_model_failure(
        failed_model: str,
        case_id: str,
        error_message: str,
        error_type: Optional[str],
    ) -> None:
        """
        Emit structured log entries for the model failure.

        Logs at ERROR level so monitoring systems can detect and alert on
        model failures (Requirement 5.5).
        """
        logger.error(
            "Model failure detected | model=%s | case_id=%s | "
            "error_type=%s | error=%s",
            failed_model,
            case_id,
            error_type or "Unknown",
            error_message,
        )
        # Additional structured log for metrics/dashboards.
        logger.info(
            "METRIC | dual_radiology | model_failure | model=%s | "
            "case_id=%s | timestamp=%s",
            failed_model,
            case_id,
            datetime.now().isoformat(),
        )

    @staticmethod
    def _adjust_confidence(output: ModelOutput) -> ModelOutput:
        """
        Return a copy of *output* with confidence reduced by the single-model
        penalty.  The original ModelOutput is not mutated.
        """
        adjusted_confidence = max(
            0.0, output.confidence - _SINGLE_MODEL_CONFIDENCE_PENALTY
        )
        # Pydantic v2: model_copy(update=…); v1: copy(update=…)
        try:
            return output.model_copy(update={"confidence": adjusted_confidence})
        except AttributeError:
            return output.copy(update={"confidence": adjusted_confidence})

    @staticmethod
    def _assign_outputs(
        failed_model: str,
        successful_output: ModelOutput,
        failed_output: ModelOutput,
    ):
        """
        Return (gemini_output, groq_output) with the correct outputs in each
        slot based on which model failed.
        """
        failed_lower = failed_model.lower()
        if "groq" in failed_lower or "llama" in failed_lower:
            return successful_output, failed_output
        # Gemini failed (or unknown model name — default to gemini slot)
        return failed_output, successful_output

    @staticmethod
    def _build_partial_validation_result(
        failed_model: str,
        successful_output: ModelOutput,
        error_message: str,
    ) -> ValidationResult:
        """
        Build a ValidationResult that reflects single-model partial analysis.

        The validation status is set to FAIL because full dual-model consensus
        cannot be established.  The discrepancies list records the failure
        details for audit purposes.
        """
        discrepancies = [
            f"{failed_model} model unavailable: {error_message}",
            "Cross-model consensus validation not possible.",
            "Confidence scores adjusted for single-model operation.",
        ]

        # Confidence validation: successful_output here is already the
        # confidence-adjusted copy, so compare directly against the threshold.
        confidence_meets_threshold = successful_output.confidence >= 0.7

        return ValidationResult(
            consensus_score=_SINGLE_MODEL_CONSENSUS_SCORE,
            confidence_validation=confidence_meets_threshold,
            quality_validation=(
                successful_output.image_quality
                not in ("poor", "unknown")
            ),
            abnormality_agreement=0.0,
            critical_findings_match=False,
            discrepancies=discrepancies,
            validation_status="FAIL",
            validation_reasoning=(
                f"Partial validation only. {failed_model} model failed with: "
                f"{error_message}. Single-model analysis from "
                f"{successful_output.model_name} is available but dual-model "
                f"consensus cannot be established. Manual review is required."
            ),
        )
