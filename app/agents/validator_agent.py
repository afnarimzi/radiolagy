"""
Validator Agent - Consensus analysis and validation for dual-model radiology system.

Implements:
- ConsensusAnalyzer: Cohen's Kappa, semantic similarity, clinical significance alignment
- QualityAssessor: Image quality validation across models
- ConfidenceCalibrator: Confidence score normalization
- ValidatorAgent: Orchestrates all validation components
"""

import logging
import math
from typing import List, Optional, Tuple

from app.models.radiology_models import (
    ConsensusMetrics,
    ModelOutput,
    ValidationConfig,
    ValidationResult,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional sentence-transformers import with graceful fallback
# ---------------------------------------------------------------------------
try:
    from sentence_transformers import SentenceTransformer, util as st_util

    _SENTENCE_TRANSFORMERS_AVAILABLE = True
    logger.info("sentence-transformers available — using neural semantic similarity")
except ImportError:
    _SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning(
        "sentence-transformers not installed — falling back to word-overlap similarity"
    )

# Clinical severity weights used for significance alignment
_CRITICAL_KEYWORDS = {
    "pneumothorax", "tension pneumothorax", "hemothorax", "aortic dissection",
    "pulmonary embolism", "cardiac tamponade", "massive pleural effusion",
    "respiratory failure", "acute respiratory distress", "ards",
}
_HIGH_KEYWORDS = {
    "pneumonia", "consolidation", "pleural effusion", "cardiomegaly",
    "pulmonary edema", "atelectasis", "mass", "nodule", "fracture",
    "infiltrate", "opacity",
}
_MODERATE_KEYWORDS = {
    "hyperinflation", "emphysema", "fibrosis", "scarring", "calcification",
    "mild cardiomegaly", "mild pleural effusion", "mild atelectasis",
}


def _severity_weight(term: str) -> float:
    """Return a clinical severity weight for an abnormality term."""
    t = term.lower()
    if any(k in t for k in _CRITICAL_KEYWORDS):
        return 3.0
    if any(k in t for k in _HIGH_KEYWORDS):
        return 2.0
    if any(k in t for k in _MODERATE_KEYWORDS):
        return 1.5
    return 1.0


# ---------------------------------------------------------------------------
# ConsensusAnalyzer
# ---------------------------------------------------------------------------

class ConsensusAnalyzer:
    """
    Calculates statistical consensus metrics between two model outputs.

    Implements:
    - Cohen's Kappa for inter-rater agreement on abnormalities (Req 4.1)
    - Semantic similarity for findings text (Req 4.3)
    - Clinical significance alignment weighted by severity (Req 4.3)
    - Exact match percentage and abnormality overlap ratio (Req 4.3)
    """

    def __init__(self):
        self._sentence_model: Optional[object] = None
        if _SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self._sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("SentenceTransformer model loaded: all-MiniLM-L6-v2")
            except Exception as exc:
                logger.warning("Failed to load SentenceTransformer model: %s", exc)
                self._sentence_model = None

    # ------------------------------------------------------------------
    # Cohen's Kappa
    # ------------------------------------------------------------------

    def calculate_cohens_kappa(
        self,
        gemini_abnormalities: List[str],
        groq_abnormalities: List[str],
    ) -> float:
        """
        Calculate Cohen's Kappa for inter-rater agreement on abnormalities.

        The universe of items is the union of both abnormality lists.
        Each model is treated as a rater that either "detected" or "did not detect"
        each item in the universe.

        Returns a float in [-1, 1]:
          1.0  = perfect agreement
          0.0  = agreement equal to chance
         -1.0  = perfect disagreement
        """
        # Normalise to lowercase for comparison
        gemini_set = {a.lower().strip() for a in gemini_abnormalities}
        groq_set = {a.lower().strip() for a in groq_abnormalities}
        universe = gemini_set | groq_set

        if not universe:
            # Both models found nothing — perfect agreement
            return 1.0

        n = len(universe)

        # Build binary rating vectors
        gemini_ratings = [1 if item in gemini_set else 0 for item in universe]
        groq_ratings = [1 if item in groq_set else 0 for item in universe]

        # Observed agreement (proportion of items rated the same)
        agreements = sum(g == r for g, r in zip(gemini_ratings, groq_ratings))
        p_o = agreements / n

        # Expected agreement by chance
        p_gemini_pos = sum(gemini_ratings) / n
        p_groq_pos = sum(groq_ratings) / n
        p_gemini_neg = 1.0 - p_gemini_pos
        p_groq_neg = 1.0 - p_groq_pos

        p_e = (p_gemini_pos * p_groq_pos) + (p_gemini_neg * p_groq_neg)

        if p_e == 1.0:
            # Both raters always agree by chance (all same label) — kappa undefined
            return 1.0 if p_o == 1.0 else 0.0

        kappa = (p_o - p_e) / (1.0 - p_e)
        # Clamp to [-1, 1] to guard against floating-point edge cases
        return max(-1.0, min(1.0, kappa))

    # ------------------------------------------------------------------
    # Semantic similarity
    # ------------------------------------------------------------------

    def calculate_semantic_similarity(
        self,
        gemini_findings: str,
        groq_findings: str,
    ) -> float:
        """
        Calculate semantic similarity between two findings strings.

        Uses sentence-transformers (all-MiniLM-L6-v2) when available,
        otherwise falls back to Jaccard word-overlap similarity.

        Returns a float in [0, 1].
        """
        if not gemini_findings or not groq_findings:
            return 0.0

        if self._sentence_model is not None:
            return self._neural_similarity(gemini_findings, groq_findings)
        return self._word_overlap_similarity(gemini_findings, groq_findings)

    def _neural_similarity(self, text_a: str, text_b: str) -> float:
        """Cosine similarity via sentence-transformers embeddings."""
        try:
            embeddings = self._sentence_model.encode(
                [text_a, text_b], convert_to_tensor=True
            )
            score = float(st_util.cos_sim(embeddings[0], embeddings[1]))
            # Cosine similarity can be slightly outside [0,1] due to fp precision
            return max(0.0, min(1.0, score))
        except Exception as exc:
            logger.warning("Neural similarity failed, falling back: %s", exc)
            return self._word_overlap_similarity(text_a, text_b)

    @staticmethod
    def _word_overlap_similarity(text_a: str, text_b: str) -> float:
        """
        Jaccard similarity on word sets (case-insensitive, punctuation stripped).
        """
        import re

        def tokenise(text: str) -> set:
            return set(re.sub(r"[^\w\s]", "", text.lower()).split())

        words_a = tokenise(text_a)
        words_b = tokenise(text_b)

        if not words_a and not words_b:
            return 1.0
        if not words_a or not words_b:
            return 0.0

        intersection = words_a & words_b
        union = words_a | words_b
        return len(intersection) / len(union)

    # ------------------------------------------------------------------
    # Clinical significance alignment
    # ------------------------------------------------------------------

    def calculate_clinical_significance_alignment(
        self,
        gemini_output: ModelOutput,
        groq_output: ModelOutput,
    ) -> float:
        """
        Weighted agreement score that prioritises clinically critical findings.

        For each abnormality in the union of both lists, the agreement
        contribution is weighted by clinical severity. Items agreed upon
        by both models contribute their weight; items found by only one
        model reduce the score proportionally.

        Returns a float in [0, 1].
        """
        gemini_set = {a.lower().strip() for a in gemini_output.abnormalities}
        groq_set = {a.lower().strip() for a in groq_output.abnormalities}
        universe = gemini_set | groq_set

        if not universe:
            return 1.0  # Both models found nothing — full alignment

        total_weight = 0.0
        agreed_weight = 0.0

        for item in universe:
            weight = _severity_weight(item)
            total_weight += weight
            if item in gemini_set and item in groq_set:
                agreed_weight += weight

        return agreed_weight / total_weight if total_weight > 0 else 1.0

    # ------------------------------------------------------------------
    # Exact match percentage
    # ------------------------------------------------------------------

    @staticmethod
    def calculate_exact_match_percentage(
        gemini_abnormalities: List[str],
        groq_abnormalities: List[str],
    ) -> float:
        """
        Percentage of abnormalities that appear in both lists (Jaccard * 100).

        Returns a float in [0, 100].
        """
        gemini_set = {a.lower().strip() for a in gemini_abnormalities}
        groq_set = {a.lower().strip() for a in groq_abnormalities}
        union = gemini_set | groq_set

        if not union:
            return 100.0

        intersection = gemini_set & groq_set
        return (len(intersection) / len(union)) * 100.0

    # ------------------------------------------------------------------
    # Abnormality overlap ratio
    # ------------------------------------------------------------------

    @staticmethod
    def calculate_abnormality_overlap_ratio(
        gemini_abnormalities: List[str],
        groq_abnormalities: List[str],
    ) -> float:
        """
        Jaccard overlap ratio for abnormality lists.

        Returns a float in [0, 1].
        """
        gemini_set = {a.lower().strip() for a in gemini_abnormalities}
        groq_set = {a.lower().strip() for a in groq_abnormalities}
        union = gemini_set | groq_set

        if not union:
            return 1.0

        intersection = gemini_set & groq_set
        return len(intersection) / len(union)

    # ------------------------------------------------------------------
    # Confidence correlation
    # ------------------------------------------------------------------

    @staticmethod
    def calculate_confidence_correlation(
        gemini_confidence: float,
        groq_confidence: float,
    ) -> float:
        """
        Simple normalised difference-based correlation between two scalar
        confidence scores.

        Returns a float in [-1, 1] where 1.0 means identical scores.
        """
        diff = abs(gemini_confidence - groq_confidence)
        # Map [0, 1] difference to [1, -1] correlation
        return 1.0 - 2.0 * diff

    # ------------------------------------------------------------------
    # Quality agreement
    # ------------------------------------------------------------------

    @staticmethod
    def check_quality_agreement(
        gemini_quality: str,
        groq_quality: str,
    ) -> bool:
        """
        Return True if both models agree on image quality category.

        Quality strings are normalised to lowercase before comparison.
        """
        return gemini_quality.lower().strip() == groq_quality.lower().strip()

    # ------------------------------------------------------------------
    # Full consensus metrics
    # ------------------------------------------------------------------

    def compute_consensus_metrics(
        self,
        gemini_output: ModelOutput,
        groq_output: ModelOutput,
    ) -> ConsensusMetrics:
        """
        Compute all ConsensusMetrics from two ModelOutput objects.
        """
        exact_match = self.calculate_exact_match_percentage(
            gemini_output.abnormalities, groq_output.abnormalities
        )
        semantic_sim = self.calculate_semantic_similarity(
            gemini_output.findings, groq_output.findings
        )
        clinical_align = self.calculate_clinical_significance_alignment(
            gemini_output, groq_output
        )
        kappa = self.calculate_cohens_kappa(
            gemini_output.abnormalities, groq_output.abnormalities
        )
        overlap_ratio = self.calculate_abnormality_overlap_ratio(
            gemini_output.abnormalities, groq_output.abnormalities
        )
        conf_corr = self.calculate_confidence_correlation(
            gemini_output.confidence, groq_output.confidence
        )
        quality_agree = self.check_quality_agreement(
            gemini_output.image_quality, groq_output.image_quality
        )

        return ConsensusMetrics(
            exact_match_percentage=exact_match,
            semantic_similarity_score=semantic_sim,
            clinical_significance_alignment=clinical_align,
            cohens_kappa=kappa,
            abnormality_overlap_ratio=overlap_ratio,
            confidence_correlation=conf_corr,
            quality_agreement=quality_agree,
        )


# ---------------------------------------------------------------------------
# QualityAssessor
# ---------------------------------------------------------------------------

class QualityAssessor:
    """
    Validates image quality assessments from both models.

    Applies conservative quality standards when models disagree (Req 7.2).
    """

    # Ordered quality tiers from worst to best
    _QUALITY_TIERS = ["poor", "inadequate", "suboptimal", "adequate", "good", "excellent"]

    def _tier_index(self, quality: str) -> int:
        q = quality.lower().strip()
        for i, tier in enumerate(self._QUALITY_TIERS):
            if tier in q:
                return i
        # Unknown quality — treat as adequate (middle ground)
        return self._QUALITY_TIERS.index("adequate")

    def validate_quality(
        self,
        gemini_quality: str,
        groq_quality: str,
        threshold: str = "adequate",
    ) -> Tuple[bool, List[str]]:
        """
        Validate that image quality meets the threshold.

        When models disagree, the *lower* (more conservative) quality is used.

        Returns:
            (passes: bool, discrepancies: List[str])
        """
        discrepancies: List[str] = []
        threshold_idx = self._tier_index(threshold)

        gemini_idx = self._tier_index(gemini_quality)
        groq_idx = self._tier_index(groq_quality)

        if gemini_idx != groq_idx:
            discrepancies.append(
                f"Quality disagreement: Gemini='{gemini_quality}', Groq='{groq_quality}'. "
                "Applying conservative (lower) standard."
            )

        # Conservative: use the lower quality rating
        effective_idx = min(gemini_idx, groq_idx)
        passes = effective_idx >= threshold_idx

        if not passes:
            effective_quality = self._QUALITY_TIERS[effective_idx]
            discrepancies.append(
                f"Image quality '{effective_quality}' does not meet threshold '{threshold}'."
            )

        return passes, discrepancies


# ---------------------------------------------------------------------------
# ConfidenceCalibrator
# ---------------------------------------------------------------------------

class ConfidenceCalibrator:
    """
    Normalises and calibrates confidence scores from different model architectures.

    Different models may have systematic biases in their confidence outputs.
    Calibration ensures fair comparison (Req 4.2).
    """

    # Empirical bias corrections per model (can be tuned from production data)
    _BIAS: dict = {
        "gemini": 0.0,
        "groq": 0.0,
    }

    def calibrate_confidence_scores(
        self,
        gemini_confidence: float,
        groq_confidence: float,
    ) -> Tuple[float, float]:
        """
        Apply per-model bias correction and clamp to [0, 1].
        """
        def _calibrate(score: float, model_key: str) -> float:
            bias = self._BIAS.get(model_key, 0.0)
            return max(0.0, min(1.0, score + bias))

        return (
            _calibrate(gemini_confidence, "gemini"),
            _calibrate(groq_confidence, "groq"),
        )

    def calculate_confidence_correlation(
        self,
        gemini_confidence: float,
        groq_confidence: float,
    ) -> float:
        """
        Normalised correlation between two calibrated confidence scores.

        Returns a float in [-1, 1].
        """
        cal_gemini, cal_groq = self.calibrate_confidence_scores(
            gemini_confidence, groq_confidence
        )
        return ConsensusAnalyzer.calculate_confidence_correlation(
            cal_gemini, cal_groq
        )


# ---------------------------------------------------------------------------
# ValidatorAgent
# ---------------------------------------------------------------------------

class ValidatorAgent:
    """
    Orchestrates consensus analysis, quality assessment, and confidence
    calibration to produce a ValidationResult.

    Requirements addressed:
    - 2.1: Consensus analysis comparing findings between models
    - 2.4: Agreement on critical findings with percentage calculation
    - 4.1: Cohen's Kappa for inter-rater agreement
    - 4.3: Multiple metrics including exact match, semantic similarity,
           and clinical significance alignment
    """

    def __init__(self):
        self.consensus_analyzer = ConsensusAnalyzer()
        self.quality_assessor = QualityAssessor()
        self.confidence_calibrator = ConfidenceCalibrator()

    async def validate(
        self,
        gemini_output: ModelOutput,
        groq_output: ModelOutput,
        config: ValidationConfig,
    ) -> Tuple[ValidationResult, ConsensusMetrics]:
        """
        Perform comprehensive validation of two model outputs.

        Steps:
        1. Calibrate confidence scores
        2. Validate confidence thresholds
        3. Validate image quality
        4. Compute all consensus metrics
        5. Determine validation status (PASS / FAIL / RETRY)

        Returns:
            (ValidationResult, ConsensusMetrics)
        """
        discrepancies: List[str] = []

        # ------------------------------------------------------------------
        # 1. Confidence calibration
        # ------------------------------------------------------------------
        cal_gemini_conf, cal_groq_conf = (
            self.confidence_calibrator.calibrate_confidence_scores(
                gemini_output.confidence, groq_output.confidence
            )
        )

        # ------------------------------------------------------------------
        # 2. Confidence threshold validation (Req 2.2)
        # ------------------------------------------------------------------
        confidence_validation = (
            cal_gemini_conf >= config.confidence_threshold
            and cal_groq_conf >= config.confidence_threshold
        )
        if not confidence_validation:
            if cal_gemini_conf < config.confidence_threshold:
                discrepancies.append(
                    f"Gemini confidence {cal_gemini_conf:.2f} below threshold "
                    f"{config.confidence_threshold:.2f}."
                )
            if cal_groq_conf < config.confidence_threshold:
                discrepancies.append(
                    f"Groq confidence {cal_groq_conf:.2f} below threshold "
                    f"{config.confidence_threshold:.2f}."
                )

        # ------------------------------------------------------------------
        # 3. Quality validation (Req 7.1, 7.2)
        # ------------------------------------------------------------------
        quality_validation, quality_discrepancies = self.quality_assessor.validate_quality(
            gemini_output.image_quality,
            groq_output.image_quality,
            threshold=config.quality_threshold,
        )
        discrepancies.extend(quality_discrepancies)

        # ------------------------------------------------------------------
        # 4. Consensus metrics (Req 2.1, 4.1, 4.3)
        # ------------------------------------------------------------------
        consensus_metrics = self.consensus_analyzer.compute_consensus_metrics(
            gemini_output, groq_output
        )

        # ------------------------------------------------------------------
        # 5. Abnormality agreement (Req 2.4)
        # ------------------------------------------------------------------
        abnormality_agreement = consensus_metrics.abnormality_overlap_ratio

        # ------------------------------------------------------------------
        # 6. Critical findings match (Req 7.3 — >90% agreement required)
        # ------------------------------------------------------------------
        critical_findings_match = self._check_critical_findings_match(
            gemini_output.abnormalities,
            groq_output.abnormalities,
        )
        if not critical_findings_match:
            discrepancies.append(
                "Critical findings do not match between models — manual review recommended."
            )

        # ------------------------------------------------------------------
        # 7. Overall consensus score
        # ------------------------------------------------------------------
        consensus_score = self._compute_consensus_score(consensus_metrics)

        # ------------------------------------------------------------------
        # 8. Detect significant disagreements
        # ------------------------------------------------------------------
        if consensus_metrics.semantic_similarity_score < 0.5:
            discrepancies.append(
                f"Low semantic similarity ({consensus_metrics.semantic_similarity_score:.2f}) "
                "between model findings."
            )
        if consensus_metrics.cohens_kappa < 0.4:
            discrepancies.append(
                f"Low inter-rater agreement (κ={consensus_metrics.cohens_kappa:.2f}) "
                "on abnormality detection."
            )

        # ------------------------------------------------------------------
        # 9. Determine validation status
        # ------------------------------------------------------------------
        validation_status, validation_reasoning = self._determine_status(
            consensus_score=consensus_score,
            confidence_validation=confidence_validation,
            quality_validation=quality_validation,
            abnormality_agreement=abnormality_agreement,
            critical_findings_match=critical_findings_match,
            config=config,
            discrepancies=discrepancies,
        )

        validation_result = ValidationResult(
            consensus_score=consensus_score,
            confidence_validation=confidence_validation,
            quality_validation=quality_validation,
            abnormality_agreement=abnormality_agreement,
            critical_findings_match=critical_findings_match,
            discrepancies=discrepancies,
            validation_status=validation_status,
            validation_reasoning=validation_reasoning,
        )

        logger.info(
            "Validation complete — status=%s, consensus=%.2f, κ=%.2f",
            validation_status,
            consensus_score,
            consensus_metrics.cohens_kappa,
        )

        return validation_result, consensus_metrics

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _check_critical_findings_match(
        gemini_abnormalities: List[str],
        groq_abnormalities: List[str],
    ) -> bool:
        """
        Return True if both models agree on all critical-severity findings.

        A critical finding detected by one model but not the other is a mismatch.
        If neither model detects any critical findings, they agree (True).
        """
        gemini_critical = {
            a.lower().strip()
            for a in gemini_abnormalities
            if _severity_weight(a) >= 3.0
        }
        groq_critical = {
            a.lower().strip()
            for a in groq_abnormalities
            if _severity_weight(a) >= 3.0
        }

        if not gemini_critical and not groq_critical:
            return True

        # Both sets must be identical for a match
        return gemini_critical == groq_critical

    @staticmethod
    def _compute_consensus_score(metrics: ConsensusMetrics) -> float:
        """
        Weighted composite consensus score in [0, 1].

        Weights reflect clinical importance of each metric:
        - Semantic similarity:          30%
        - Clinical significance align:  25%
        - Abnormality overlap ratio:    20%
        - Cohen's Kappa (normalised):   15%
        - Exact match (normalised):     10%
        """
        kappa_normalised = (metrics.cohens_kappa + 1.0) / 2.0  # [-1,1] → [0,1]
        exact_normalised = metrics.exact_match_percentage / 100.0

        score = (
            0.30 * metrics.semantic_similarity_score
            + 0.25 * metrics.clinical_significance_alignment
            + 0.20 * metrics.abnormality_overlap_ratio
            + 0.15 * kappa_normalised
            + 0.10 * exact_normalised
        )
        return max(0.0, min(1.0, score))

    @staticmethod
    def _determine_status(
        consensus_score: float,
        confidence_validation: bool,
        quality_validation: bool,
        abnormality_agreement: float,
        critical_findings_match: bool,
        config: ValidationConfig,
        discrepancies: List[str],
    ) -> Tuple[str, str]:
        """
        Determine PASS / FAIL / RETRY status and produce reasoning text.

        Decision rules (in priority order):
        1. FAIL  — quality validation fails
        2. FAIL  — critical findings do not match
        3. FAIL  — confidence validation fails AND consensus is low
        4. RETRY — consensus is borderline (0.6–0.8) or confidence fails alone
        5. PASS  — all checks pass
        """
        reasons: List[str] = []

        if not quality_validation:
            reasons.append("Image quality does not meet the required threshold.")
            return "FAIL", " ".join(reasons) + " " + "; ".join(discrepancies)

        if not critical_findings_match:
            reasons.append(
                "Critical findings do not match between models — high-risk disagreement."
            )
            return "FAIL", " ".join(reasons) + " " + "; ".join(discrepancies)

        if not confidence_validation and consensus_score < config.agreement_threshold:
            reasons.append(
                "Both confidence thresholds and consensus agreement are insufficient."
            )
            return "FAIL", " ".join(reasons) + " " + "; ".join(discrepancies)

        if not confidence_validation or (
            0.6 <= consensus_score < config.agreement_threshold
        ):
            reasons.append(
                "Borderline case: confidence or consensus is below the required threshold. "
                "Retry recommended."
            )
            return "RETRY", " ".join(reasons) + " " + "; ".join(discrepancies)

        if consensus_score >= config.agreement_threshold and confidence_validation:
            reasons.append(
                f"Consensus score {consensus_score:.2f} meets agreement threshold "
                f"{config.agreement_threshold:.2f}. Both models meet confidence requirements."
            )
            return "PASS", " ".join(reasons)

        # Fallback
        reasons.append(
            f"Consensus score {consensus_score:.2f} is below agreement threshold "
            f"{config.agreement_threshold:.2f}."
        )
        return "FAIL", " ".join(reasons) + " " + "; ".join(discrepancies)
