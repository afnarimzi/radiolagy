"""
ConfigManager - Centralised configuration management for the dual-model
radiology validation system.

Reads all dual-model settings from environment variables with sensible
defaults, validates them at startup, and exposes a single shared instance.

Requirements addressed:
  - 6.5: Environment variables for model selection and validation thresholds
  - 8.2: Intelligent load balancing configuration
  - 8.3: Graceful degradation configuration
  - 8.5: Distributed processing support
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration dataclass
# ---------------------------------------------------------------------------

@dataclass
class DualModelConfig:
    """
    All runtime configuration for the dual-model radiology validation system.

    Values are read from environment variables; defaults are applied when
    variables are absent.  Call ``validate()`` to raise on invalid config.
    """

    # --- Validation thresholds (Req 6.5) ---
    confidence_threshold: float = 0.7
    agreement_threshold: float = 0.8
    quality_threshold: str = "adequate"
    max_retries: int = 2
    require_consensus: bool = True
    enable_statistical_analysis: bool = True

    # --- Model selection (Req 6.5) ---
    use_dual_model: bool = True          # False → fall back to single Gemini
    gemini_model: str = "gemini-2.5-flash-preview-04-17"
    groq_model: str = "llama-3.3-70b-versatile"

    # --- Rate-limit / load balancing (Req 8.2, 8.3) ---
    groq_max_retries_on_rate_limit: int = 3
    groq_rate_limit_backoff_base: float = 2.0   # seconds; doubles each attempt
    gemini_max_retries_on_rate_limit: int = 3
    gemini_rate_limit_backoff_base: float = 2.0
    single_model_fallback_enabled: bool = True   # Req 8.3

    # --- Performance (Req 8.4) ---
    processing_timeout_seconds: float = 30.0

    # --- Distributed processing (Req 8.5) ---
    instance_id: str = "default"         # Unique ID per horizontal instance
    distributed_mode: bool = False       # Enable distributed coordination

    # --- Alerting thresholds (Req 2.5, 5.5) ---
    alert_on_disagreement_above: float = 0.5   # Alert when discrepancy > 50 %
    alert_on_consecutive_failures: int = 3      # Alert after N consecutive fails

    def validate(self) -> None:
        """Raise ValueError if any configuration value is out of range."""
        if not 0.0 <= self.confidence_threshold <= 1.0:
            raise ValueError(
                f"confidence_threshold must be in [0, 1], got {self.confidence_threshold}"
            )
        if not 0.0 <= self.agreement_threshold <= 1.0:
            raise ValueError(
                f"agreement_threshold must be in [0, 1], got {self.agreement_threshold}"
            )
        allowed_quality = {"excellent", "good", "adequate", "poor"}
        if self.quality_threshold not in allowed_quality:
            raise ValueError(
                f"quality_threshold must be one of {allowed_quality}, "
                f"got '{self.quality_threshold}'"
            )
        if self.max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        if self.processing_timeout_seconds <= 0:
            raise ValueError("processing_timeout_seconds must be > 0")

    def to_validation_config(self):
        """Return a ValidationConfig Pydantic model from current settings."""
        from app.models.radiology_models import ValidationConfig
        return ValidationConfig(
            confidence_threshold=self.confidence_threshold,
            agreement_threshold=self.agreement_threshold,
            quality_threshold=self.quality_threshold,
            max_retries=self.max_retries,
            require_consensus=self.require_consensus,
            enable_statistical_analysis=self.enable_statistical_analysis,
        )


# ---------------------------------------------------------------------------
# Factory — reads from environment
# ---------------------------------------------------------------------------

def _parse_bool(value: str, default: bool) -> bool:
    if not value:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _parse_float(value: str, default: float, name: str) -> float:
    if not value:
        return default
    try:
        return float(value)
    except ValueError:
        logger.warning("Invalid float for %s='%s', using default %.2f", name, value, default)
        return default


def _parse_int(value: str, default: int, name: str) -> int:
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        logger.warning("Invalid int for %s='%s', using default %d", name, value, default)
        return default


def load_config_from_env() -> DualModelConfig:
    """
    Build a DualModelConfig by reading environment variables.

    Environment variable names follow the pattern ``DUAL_<FIELD_NAME_UPPER>``.
    All variables are optional; defaults are used when absent.
    """
    cfg = DualModelConfig(
        # Validation thresholds
        confidence_threshold=_parse_float(
            os.getenv("DUAL_CONFIDENCE_THRESHOLD", ""), 0.7, "DUAL_CONFIDENCE_THRESHOLD"
        ),
        agreement_threshold=_parse_float(
            os.getenv("DUAL_AGREEMENT_THRESHOLD", ""), 0.8, "DUAL_AGREEMENT_THRESHOLD"
        ),
        quality_threshold=os.getenv("DUAL_QUALITY_THRESHOLD", "adequate").strip().lower(),
        max_retries=_parse_int(
            os.getenv("DUAL_MAX_RETRIES", ""), 2, "DUAL_MAX_RETRIES"
        ),
        require_consensus=_parse_bool(os.getenv("DUAL_REQUIRE_CONSENSUS", ""), True),
        enable_statistical_analysis=_parse_bool(
            os.getenv("DUAL_ENABLE_STATISTICAL_ANALYSIS", ""), True
        ),

        # Model selection
        use_dual_model=_parse_bool(os.getenv("DUAL_USE_DUAL_MODEL", ""), True),
        gemini_model=os.getenv("DUAL_GEMINI_MODEL", "gemini-2.5-flash-preview-04-17"),
        groq_model=os.getenv("DUAL_GROQ_MODEL", "llama-3.3-70b-versatile"),

        # Rate-limit / load balancing
        groq_max_retries_on_rate_limit=_parse_int(
            os.getenv("DUAL_GROQ_RATE_LIMIT_RETRIES", ""), 3, "DUAL_GROQ_RATE_LIMIT_RETRIES"
        ),
        groq_rate_limit_backoff_base=_parse_float(
            os.getenv("DUAL_GROQ_BACKOFF_BASE", ""), 2.0, "DUAL_GROQ_BACKOFF_BASE"
        ),
        gemini_max_retries_on_rate_limit=_parse_int(
            os.getenv("DUAL_GEMINI_RATE_LIMIT_RETRIES", ""), 3, "DUAL_GEMINI_RATE_LIMIT_RETRIES"
        ),
        gemini_rate_limit_backoff_base=_parse_float(
            os.getenv("DUAL_GEMINI_BACKOFF_BASE", ""), 2.0, "DUAL_GEMINI_BACKOFF_BASE"
        ),
        single_model_fallback_enabled=_parse_bool(
            os.getenv("DUAL_SINGLE_MODEL_FALLBACK", ""), True
        ),

        # Performance
        processing_timeout_seconds=_parse_float(
            os.getenv("DUAL_PROCESSING_TIMEOUT", ""), 30.0, "DUAL_PROCESSING_TIMEOUT"
        ),

        # Distributed processing
        instance_id=os.getenv("DUAL_INSTANCE_ID", "default"),
        distributed_mode=_parse_bool(os.getenv("DUAL_DISTRIBUTED_MODE", ""), False),

        # Alerting
        alert_on_disagreement_above=_parse_float(
            os.getenv("DUAL_ALERT_DISAGREEMENT_THRESHOLD", ""), 0.5,
            "DUAL_ALERT_DISAGREEMENT_THRESHOLD"
        ),
        alert_on_consecutive_failures=_parse_int(
            os.getenv("DUAL_ALERT_CONSECUTIVE_FAILURES", ""), 3,
            "DUAL_ALERT_CONSECUTIVE_FAILURES"
        ),
    )

    try:
        cfg.validate()
        logger.info(
            "DualModelConfig loaded | instance_id=%s | use_dual_model=%s | "
            "confidence_threshold=%.2f | agreement_threshold=%.2f | "
            "max_retries=%d | single_model_fallback=%s | distributed=%s",
            cfg.instance_id,
            cfg.use_dual_model,
            cfg.confidence_threshold,
            cfg.agreement_threshold,
            cfg.max_retries,
            cfg.single_model_fallback_enabled,
            cfg.distributed_mode,
        )
    except ValueError as exc:
        logger.error("Invalid DualModelConfig: %s — using defaults", exc)
        cfg = DualModelConfig()

    return cfg


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

#: Shared config instance — import and use directly:
#:
#:   from app.utils.config_manager import dual_config
dual_config: DualModelConfig = load_config_from_env()
