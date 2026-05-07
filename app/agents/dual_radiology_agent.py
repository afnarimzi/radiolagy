"""
DualRadiologyAgent - Orchestrates parallel dual-model radiology analysis with
consensus validation and decision gateway logic.

Workflow:
  1. Execute Gemini analyze_image() to get ModelOutput + image description
  2. Execute Groq analyze_from_description() in parallel (using Gemini's description)
  3. Run ValidatorAgent.validate() on both outputs
  4. Run DecisionGateway.decide() on the validation result
  5. If RETRY, use RetryManager to retry up to 2 times
  6. If either model fails, use ErrorHandler for graceful degradation
  7. Return DualRadiologyFindings

Requirements addressed:
  - 1.1: Process through both Gemini and Groq models simultaneously
  - 2.1: Validator_Agent SHALL perform consensus analysis
  - 3.1: Decision_Gateway SHALL make PASS/FAIL decisions
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Optional, Tuple

from app.agents.decision_gateway import DecisionGateway
from app.agents.error_handler import ErrorHandler
from app.agents.groq_radiology_agent import GroqRadiologyAgent
from app.agents.radiology_agent import RadiologyAgent
from app.agents.retry_manager import RetryManager
from app.agents.validator_agent import ValidatorAgent
from app.models.radiology_models import (
    ConsensusMetrics,
    DualRadiologyFindings,
    DualRadiologyInput,
    ModelOutput,
    ValidationConfig,
    ValidationResult,
)
from app.utils.metrics_collector import metrics_collector
from app.utils.alert_manager import alert_manager

logger = logging.getLogger(__name__)

# Alias for clarity — RadiologyAgent IS the GeminiRadiologyAgent
GeminiRadiologyAgent = RadiologyAgent


class DualRadiologyAgent:
    """
    Orchestrates parallel execution of both Gemini and Groq radiology agents,
    integrates the ValidatorAgent for consensus analysis, and uses the
    DecisionGateway to make final PASS/FAIL decisions.

    Supports:
    - Parallel model execution (Req 1.1, 8.1)
    - Consensus validation (Req 2.1)
    - PASS/FAIL decision logic (Req 3.1)
    - Retry mechanism for borderline cases (Req 3.4)
    - Graceful degradation on single-model failure (Req 1.3)
    - Comprehensive logging and metrics (Req 5.1, 5.2, 5.3)
    """

    def __init__(self):
        """Initialise all sub-agents and supporting components."""
        from app.utils.config_manager import dual_config
        self.gemini_agent = GeminiRadiologyAgent()
        self.groq_agent = GroqRadiologyAgent()
        self.validator = ValidatorAgent()
        self.decision_gateway = DecisionGateway()
        self.error_handler = ErrorHandler()
        self.retry_manager = RetryManager()
        self._config = dual_config
        logger.info(
            "DualRadiologyAgent initialised | instance_id=%s | "
            "confidence_threshold=%.2f | agreement_threshold=%.2f | "
            "max_retries=%d | single_model_fallback=%s",
            dual_config.instance_id,
            dual_config.confidence_threshold,
            dual_config.agreement_threshold,
            dual_config.max_retries,
            dual_config.single_model_fallback_enabled,
        )

    # ------------------------------------------------------------------
    # Primary public interface
    # ------------------------------------------------------------------

    async def analyze(self, input_data: DualRadiologyInput) -> DualRadiologyFindings:
        """
        Perform dual-model radiology analysis with consensus validation.

        Steps:
          1. Run Gemini image analysis and image description generation in parallel.
          2. Feed Gemini's image description to Groq for independent text-based
             medical reasoning (also in parallel with step 1 where possible).
          3. Validate both outputs through ValidatorAgent.
          4. Make a final decision through DecisionGateway.
          5. Retry up to 2 times if the decision is RETRY.
          6. Return comprehensive DualRadiologyFindings.

        Args:
            input_data: DualRadiologyInput containing the image source, patient
                        metadata, and optional validation configuration.

        Returns:
            DualRadiologyFindings with both model outputs, validation results,
            consensus metrics, and the final PASS/FAIL decision.
        """
        start_time = time.time()
        case_id = input_data.case_id
        config = input_data.validation_config or self._config.to_validation_config()

        logger.info(
            "DualRadiologyAgent.analyze started | case_id=%s | "
            "confidence_threshold=%.2f | agreement_threshold=%.2f",
            case_id,
            config.confidence_threshold,
            config.agreement_threshold,
        )

        # ------------------------------------------------------------------
        # Step 1 & 2: Run both models (Gemini first for image description,
        #             then Groq in parallel with Gemini's full analysis)
        # ------------------------------------------------------------------
        gemini_output, groq_output = await self._run_parallel_analysis(
            input_data, case_id
        )

        # ------------------------------------------------------------------
        # Check for total failure (both models failed)
        # ------------------------------------------------------------------
        if gemini_output.confidence == 0.0 and groq_output.confidence == 0.0:
            logger.error(
                "Both models failed for case_id=%s — returning hard FAIL.", case_id
            )
            return self._build_total_failure_findings(
                case_id=case_id,
                gemini_output=gemini_output,
                groq_output=groq_output,
                config=config,
            )

        # ------------------------------------------------------------------
        # Check for single-model failure → graceful degradation
        # ------------------------------------------------------------------
        if gemini_output.confidence == 0.0:
            logger.warning(
                "Gemini failed for case_id=%s — delegating to ErrorHandler.", case_id
            )
            return await self.error_handler.handle_gemini_failure(
                groq_output=groq_output,
                case_id=case_id,
                error_message=gemini_output.findings,
            )

        if groq_output.confidence == 0.0:
            logger.warning(
                "Groq failed for case_id=%s — delegating to ErrorHandler.", case_id
            )
            return await self.error_handler.handle_groq_failure(
                gemini_output=gemini_output,
                case_id=case_id,
                error_message=groq_output.findings,
            )

        # ------------------------------------------------------------------
        # Step 3 & 4: Validate and decide (with retry loop)
        # ------------------------------------------------------------------
        findings = await self._validate_and_decide(
            input_data=input_data,
            gemini_output=gemini_output,
            groq_output=groq_output,
            config=config,
            case_id=case_id,
        )

        total_time = time.time() - start_time
        logger.info(
            "DualRadiologyAgent.analyze completed | case_id=%s | "
            "decision=%s | retry_count=%d | total_time=%.2fs",
            case_id,
            findings.final_decision,
            findings.retry_count,
            total_time,
        )

        # Req 5.1–5.2: record per-model and consensus metrics for dashboards
        # Note: decision metrics are recorded in _log_decision during the
        # validation loop to capture per-attempt threshold details (Req 5.3).
        try:
            metrics_collector.record_model_metrics(
                case_id=findings.case_id,
                model_output=findings.gemini_output,
                success=findings.gemini_output.confidence > 0.0,
            )
            metrics_collector.record_model_metrics(
                case_id=findings.case_id,
                model_output=findings.groq_output,
                success=findings.groq_output.confidence > 0.0,
            )
            metrics_collector.record_consensus_metrics(
                case_id=findings.case_id,
                validation_result=findings.validation_result,
                consensus_metrics=findings.consensus_metrics,
            )
        except Exception as metrics_exc:
            logger.warning(
                "MetricsCollector recording failed (non-fatal) | "
                "case_id=%s | error=%s",
                case_id,
                metrics_exc,
            )

        # Req 2.5, 5.5, 14.2: check alerts
        try:
            alert_manager.check_disagreement(
                case_id=case_id,
                consensus_score=findings.validation_result.consensus_score,
                discrepancies=findings.validation_result.discrepancies,
            )
            alert_manager.check_processing_time(case_id=case_id, elapsed=total_time)
            # Reset failure counters on success
            if findings.gemini_output.confidence > 0.0:
                alert_manager.reset_failure_count("gemini")
            else:
                alert_manager.check_model_failure(
                    "gemini", case_id, findings.gemini_output.findings
                )
            if findings.groq_output.confidence > 0.0:
                alert_manager.reset_failure_count("groq")
            else:
                alert_manager.check_model_failure(
                    "groq", case_id, findings.groq_output.findings
                )
        except Exception as alert_exc:
            logger.warning(
                "AlertManager check failed (non-fatal) | case_id=%s | error=%s",
                case_id,
                alert_exc,
            )

        return findings

    # ------------------------------------------------------------------
    # Parallel model execution
    # ------------------------------------------------------------------

    async def _run_parallel_analysis(
        self,
        input_data: DualRadiologyInput,
        case_id: str,
    ) -> Tuple[ModelOutput, ModelOutput]:
        """
        Execute Gemini and Groq image analysis truly in parallel.
        Both models now analyze the X-ray image independently.
        """
        logger.info("Starting parallel image analysis for case_id=%s", case_id)

        gemini_task = asyncio.create_task(self._safe_gemini_analyze(input_data, case_id))
        groq_task = asyncio.create_task(self._safe_groq_analyze_image(input_data, case_id))

        gemini_output, groq_output = await asyncio.gather(
            gemini_task, groq_task, return_exceptions=False
        )

        logger.info(
            "Parallel analysis complete | case_id=%s | gemini=%.2f | groq=%.2f",
            case_id, gemini_output.confidence, groq_output.confidence,
        )
        return gemini_output, groq_output

    async def _safe_gemini_analyze(
        self,
        input_data: DualRadiologyInput,
        case_id: str,
    ) -> ModelOutput:
        """
        Run Gemini image analysis with exception handling.

        Returns a zero-confidence ModelOutput on failure so the caller can
        detect the failure without raising.
        """
        try:
            logger.debug("Gemini analyze_image started | case_id=%s", case_id)
            output = await self.gemini_agent.analyze_image(input_data)
            logger.info(
                "Gemini analyze_image completed | case_id=%s | "
                "confidence=%.2f | processing_time=%.2fs",
                case_id,
                output.confidence,
                output.processing_time,
            )
            return output
        except Exception as exc:
            logger.error(
                "Gemini analyze_image failed | case_id=%s | error=%s",
                case_id,
                exc,
                exc_info=True,
            )
            # Record model-specific error for failure analysis (Req 5.5)
            try:
                error_type = type(exc).__name__
                metrics_collector.record_error(
                    case_id=case_id,
                    model_name="gemini-2.5-flash",
                    error_type=error_type,
                    error_message=str(exc),
                    is_recoverable=True,
                    fallback_used=False,  # fallback decision made by caller
                )
            except Exception:
                pass
            return ModelOutput(
                model_name="gemini-2.5-flash",
                findings=f"Analysis failed: {exc}",
                abnormalities=[],
                anatomical_structures=[],
                confidence=0.0,
                image_quality="unknown",
                recommendations="Manual review required due to analysis error.",
                processing_time=0.0,
                timestamp=datetime.now(),
                raw_response=None,
            )

    async def _safe_groq_analyze_image(
        self,
        input_data: DualRadiologyInput,
        case_id: str,
    ) -> ModelOutput:
        """Run Groq direct image analysis with exception handling."""
        try:
            logger.debug("Groq vision analyze_image started | case_id=%s", case_id)
            output = await self.groq_agent.analyze_image(input_data)
            logger.info(
                "Groq vision completed | case_id=%s | confidence=%.2f | time=%.2fs",
                case_id, output.confidence, output.processing_time,
            )
            return output
        except Exception as exc:
            logger.error("Groq vision failed | case_id=%s | error=%s", case_id, exc, exc_info=True)
            try:
                metrics_collector.record_error(
                    case_id=case_id, model_name="llama-4-scout",
                    error_type=type(exc).__name__, error_message=str(exc),
                    is_recoverable=True, fallback_used=False,
                )
            except Exception:
                pass
            return ModelOutput(
                model_name="meta-llama/llama-4-scout-17b-16e-instruct",
                findings=f"Analysis failed: {exc}",
                abnormalities=[], anatomical_structures=[],
                confidence=0.0, image_quality="unknown",
                recommendations="Manual review required due to analysis error.",
                processing_time=0.0, timestamp=datetime.now(), raw_response=None,
            )

    # ------------------------------------------------------------------
    # Validation, decision, and retry loop
    # ------------------------------------------------------------------

    async def _validate_and_decide(
        self,
        input_data: DualRadiologyInput,
        gemini_output: ModelOutput,
        groq_output: ModelOutput,
        config: ValidationConfig,
        case_id: str,
    ) -> DualRadiologyFindings:
        """
        Run the validation → decision → retry loop.

        Retries up to config.max_retries times when the decision is RETRY.
        After exhausting retries, triggers manual review and returns a FAIL.

        Returns:
            DualRadiologyFindings with the final decision.
        """
        retry_count = 0
        current_gemini = gemini_output
        current_groq = groq_output
        current_input = input_data

        while True:
            # ------------------------------------------------------------------
            # Validate both outputs
            # ------------------------------------------------------------------
            logger.info(
                "Running ValidatorAgent | case_id=%s | attempt=%d",
                case_id,
                retry_count + 1,
            )
            validation_result, consensus_metrics = await self.validator.validate(
                gemini_output=current_gemini,
                groq_output=current_groq,
                config=config,
            )

            self._log_validation_metrics(
                case_id=case_id,
                validation_result=validation_result,
                consensus_metrics=consensus_metrics,
                retry_count=retry_count,
            )

            # ------------------------------------------------------------------
            # Make decision
            # ------------------------------------------------------------------
            logger.info(
                "Running DecisionGateway | case_id=%s | validation_status=%s",
                case_id,
                validation_result.validation_status,
            )
            decision_report = self.decision_gateway.decide(
                validation_result=validation_result,
                config=config,
                case_id=case_id,
            )

            self._log_decision(
                case_id=case_id,
                decision_report=decision_report,
                retry_count=retry_count,
            )

            # ------------------------------------------------------------------
            # If PASS or hard FAIL — return immediately
            # ------------------------------------------------------------------
            if decision_report.decision in ("PASS", "FAIL"):
                return DualRadiologyFindings(
                    case_id=case_id,
                    gemini_output=current_gemini,
                    groq_output=current_groq,
                    validation_result=validation_result,
                    consensus_metrics=consensus_metrics,
                    final_decision=decision_report.decision,
                    decision_reasoning=decision_report.reasoning,
                    retry_count=retry_count,
                    timestamp=datetime.now(),
                )
            # ------------------------------------------------------------------
            # RETRY path — check if we can retry
            # ------------------------------------------------------------------
            should_retry = await self.retry_manager.should_retry(
                validation_result=validation_result,
                retry_count=retry_count,
            )

            if not should_retry:
                # Exhausted retries — trigger manual review and return FAIL
                review_request = self.retry_manager.trigger_manual_review(
                    case_id=case_id,
                    validation_result=validation_result,
                    retry_count=retry_count,
                )
                logger.warning(
                    "Manual review triggered | case_id=%s | priority=%s | "
                    "retry_count=%d",
                    case_id,
                    review_request.get("priority", "UNKNOWN"),
                    retry_count,
                )
                return DualRadiologyFindings(
                    case_id=case_id,
                    gemini_output=current_gemini,
                    groq_output=current_groq,
                    validation_result=validation_result,
                    consensus_metrics=consensus_metrics,
                    final_decision="FAIL",
                    decision_reasoning=(
                        f"Manual review required after {retry_count} retry attempt(s). "
                        f"{decision_report.reasoning}"
                    ),
                    retry_count=retry_count,
                    timestamp=datetime.now(),
                )

            # ------------------------------------------------------------------
            # Execute retry — re-run both models with adjusted thresholds
            # ------------------------------------------------------------------
            logger.info(
                "Executing retry attempt %d for case_id=%s",
                retry_count + 1,
                case_id,
            )

            retry_findings = await self.retry_manager.execute_retry(
                input_data=current_input,
                retry_count=retry_count,
                analysis_fn=self._analyze_for_retry,
            )

            if retry_findings is None:
                # Should not happen in normal flow, but guard defensively
                logger.error(
                    "Retry returned None for case_id=%s — returning FAIL.", case_id
                )
                return DualRadiologyFindings(
                    case_id=case_id,
                    gemini_output=current_gemini,
                    groq_output=current_groq,
                    validation_result=validation_result,
                    consensus_metrics=consensus_metrics,
                    final_decision="FAIL",
                    decision_reasoning="Retry execution returned no results.",
                    retry_count=retry_count,
                    timestamp=datetime.now(),
                )

            # Update state for next loop iteration
            retry_count += 1
            current_gemini = retry_findings.gemini_output
            current_groq = retry_findings.groq_output
            # Use the adjusted input from the retry (thresholds may have been relaxed)
            current_input = self.retry_manager._adjust_thresholds_for_retry(
                input_data, retry_count - 1
            )
            config = current_input.validation_config or config

    async def _analyze_for_retry(
        self, input_data: DualRadiologyInput
    ) -> DualRadiologyFindings:
        """
        Lightweight re-analysis used by RetryManager.execute_retry().

        Runs both models again and returns a DualRadiologyFindings with the
        raw outputs (validation/decision will be re-run in the main loop).
        """
        case_id = input_data.case_id
        gemini_output, groq_output = await self._run_parallel_analysis(
            input_data, case_id
        )

        # Build a minimal findings object — the retry loop will re-validate
        # and re-decide on the next iteration.
        placeholder_validation = ValidationResult(
            consensus_score=0.0,
            confidence_validation=False,
            quality_validation=False,
            abnormality_agreement=0.0,
            critical_findings_match=False,
            discrepancies=["Retry in progress — validation pending."],
            validation_status="RETRY",
            validation_reasoning="Retry analysis completed — awaiting re-validation.",
        )
        placeholder_metrics = ConsensusMetrics(
            exact_match_percentage=0.0,
            semantic_similarity_score=0.0,
            clinical_significance_alignment=0.0,
            cohens_kappa=0.0,
            abnormality_overlap_ratio=0.0,
            confidence_correlation=0.0,
            quality_agreement=False,
        )

        return DualRadiologyFindings(
            case_id=case_id,
            gemini_output=gemini_output,
            groq_output=groq_output,
            validation_result=placeholder_validation,
            consensus_metrics=placeholder_metrics,
            final_decision="RETRY",
            decision_reasoning="Retry analysis — pending re-validation.",
            retry_count=0,
            timestamp=datetime.now(),
        )

    # ------------------------------------------------------------------
    # Failure helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_total_failure_findings(
        case_id: str,
        gemini_output: ModelOutput,
        groq_output: ModelOutput,
        config: ValidationConfig,
    ) -> DualRadiologyFindings:
        """
        Build a DualRadiologyFindings representing total failure of both models.
        """
        validation_result = ValidationResult(
            consensus_score=0.0,
            confidence_validation=False,
            quality_validation=False,
            abnormality_agreement=0.0,
            critical_findings_match=False,
            discrepancies=[
                "Gemini model failed.",
                "Groq model failed.",
                "No analysis available — manual review required.",
            ],
            validation_status="FAIL",
            validation_reasoning=(
                "Both Gemini and Groq models failed to produce analysis results. "
                "Manual review is required."
            ),
        )
        consensus_metrics = ConsensusMetrics(
            exact_match_percentage=0.0,
            semantic_similarity_score=0.0,
            clinical_significance_alignment=0.0,
            cohens_kappa=0.0,
            abnormality_overlap_ratio=0.0,
            confidence_correlation=0.0,
            quality_agreement=False,
        )
        return DualRadiologyFindings(
            case_id=case_id,
            gemini_output=gemini_output,
            groq_output=groq_output,
            validation_result=validation_result,
            consensus_metrics=consensus_metrics,
            final_decision="FAIL",
            decision_reasoning=(
                "Both models failed to produce analysis results. "
                "Manual review is required."
            ),
            retry_count=0,
            timestamp=datetime.now(),
        )

    # ------------------------------------------------------------------
    # Logging helpers (Req 5.1, 5.2, 5.3)
    # ------------------------------------------------------------------

    @staticmethod
    def _log_validation_metrics(
        case_id: str,
        validation_result: ValidationResult,
        consensus_metrics: ConsensusMetrics,
        retry_count: int,
    ) -> None:
        """Log detailed validation metrics for monitoring and audit purposes."""
        logger.info(
            "METRIC | validation | case_id=%s | attempt=%d | "
            "status=%s | consensus_score=%.3f | "
            "cohens_kappa=%.3f | semantic_similarity=%.3f | "
            "abnormality_agreement=%.3f | confidence_validation=%s | "
            "quality_validation=%s | critical_findings_match=%s",
            case_id,
            retry_count + 1,
            validation_result.validation_status,
            validation_result.consensus_score,
            consensus_metrics.cohens_kappa,
            consensus_metrics.semantic_similarity_score,
            validation_result.abnormality_agreement,
            validation_result.confidence_validation,
            validation_result.quality_validation,
            validation_result.critical_findings_match,
        )
        if validation_result.discrepancies:
            logger.info(
                "METRIC | discrepancies | case_id=%s | count=%d | details=%s",
                case_id,
                len(validation_result.discrepancies),
                "; ".join(validation_result.discrepancies),
            )

    @staticmethod
    def _log_decision(
        case_id: str,
        decision_report,
        retry_count: int,
    ) -> None:
        """Log decision rationale and threshold comparisons (Req 5.3)."""
        logger.info(
            "METRIC | decision | case_id=%s | attempt=%d | "
            "decision=%s | confidence_passed=%s | "
            "critical_consensus_passed=%s | overall_consensus_passed=%s | "
            "quality_passed=%s | retry_recommended=%s | "
            "manual_review_required=%s",
            case_id,
            retry_count + 1,
            decision_report.decision,
            decision_report.confidence_passed,
            decision_report.critical_consensus_passed,
            decision_report.overall_consensus_passed,
            decision_report.quality_passed,
            decision_report.retry_recommended,
            decision_report.manual_review_required,
        )
        logger.info(
            "METRIC | decision_reasoning | case_id=%s | reasoning=%s",
            case_id,
            decision_report.reasoning,
        )
        # Log threshold comparison details for full transparency (Req 5.3)
        if decision_report.threshold_details:
            logger.info(
                "METRIC | threshold_comparisons | case_id=%s | details=%s",
                case_id,
                decision_report.threshold_details,
            )
        # Record to MetricsCollector with full threshold details (Req 5.3)
        try:
            metrics_collector.record_decision(
                case_id=case_id,
                decision=decision_report.decision,
                reasoning=decision_report.reasoning,
                retry_count=retry_count,
                confidence_passed=decision_report.confidence_passed,
                critical_consensus_passed=decision_report.critical_consensus_passed,
                overall_consensus_passed=decision_report.overall_consensus_passed,
                quality_passed=decision_report.quality_passed,
                retry_recommended=decision_report.retry_recommended,
                manual_review_required=decision_report.manual_review_required,
                threshold_details=decision_report.threshold_details,
            )
        except Exception as exc:
            logger.warning(
                "MetricsCollector.record_decision failed (non-fatal) | "
                "case_id=%s | error=%s",
                case_id,
                exc,
            )
