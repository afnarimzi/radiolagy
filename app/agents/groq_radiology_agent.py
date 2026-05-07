"""
Groq Radiology Agent - Direct image analysis using Llama 4 Scout (vision model).

Both Gemini and Groq now analyze the X-ray image independently.
The validator agent then compares two genuinely independent outputs.
"""
import os
import time
import json
import base64
import asyncio
import logging
from datetime import datetime
from typing import List, Optional

from groq import Groq, RateLimitError as GroqRateLimitError
from dotenv import load_dotenv

from app.models.dual_radiology_models import DualRadiologyInput, ModelOutput

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are an expert radiologist with decades of clinical experience.
Analyze the X-ray image provided and produce a structured radiology report.

You MUST respond with a single valid JSON object matching this exact schema:
{
  "findings": "<detailed radiological findings as a professional narrative>",
  "abnormalities": ["<abnormality 1>", "<abnormality 2>"],
  "anatomical_structures": ["<structure 1>", "<structure 2>"],
  "confidence": <float between 0.0 and 1.0>,
  "image_quality": "<one of: excellent | good | adequate | poor | unknown>",
  "recommendations": "<clinical recommendations>"
}

Rules:
- "findings" must be a thorough professional narrative using medical terminology.
- "abnormalities" must be an array of strings; use [] if none found.
- "anatomical_structures" must list every structure evaluated.
- "confidence" must reflect your certainty (0.0–1.0).
- "image_quality" must be one of the five allowed values.
- "recommendations" must include actionable clinical guidance.
- Do NOT include any text outside the JSON object.
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _get_image_media_type(image_path: str) -> str:
    ext = image_path.lower().split(".")[-1]
    return {
        "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "png": "image/png", "bmp": "image/bmp",
        "tiff": "image/tiff", "tif": "image/tiff",
        "webp": "image/webp",
    }.get(ext, "image/jpeg")


def _extract_abnormalities_from_text(findings_text: str) -> List[str]:
    abnormalities: List[str] = []
    lower = findings_text.lower()
    negation_words = ["no", "without", "clear", "negative", "prior", "old"]

    def _has_negation(text: str, keyword: str) -> bool:
        idx = text.find(keyword)
        if idx == -1:
            return False
        context = text[max(0, idx - 30): idx + 30]
        return any(neg in context for neg in negation_words)

    checks = [
        (["pneumonia", "consolidation"], "pneumonia/consolidation"),
        (["effusion"], "pleural effusion"),
        (["fracture"], "acute fracture"),
        (["mass", "nodule", "lesion"], "mass/nodule"),
        (["cardiomegaly", "enlarged heart"], "cardiomegaly"),
        (["atelectasis"], "atelectasis"),
        (["pneumothorax"], "pneumothorax"),
        (["edema", "congestion"], "pulmonary edema"),
    ]
    for keywords, label in checks:
        for kw in keywords:
            if kw in lower and not _has_negation(lower, kw):
                abnormalities.append(label)
                break
    return abnormalities


def _parse_groq_response(raw_text: str) -> dict:
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return json.loads(text)


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class GroqRadiologyAgent:
    """
    Radiology agent that sends the X-ray image directly to Groq's
    Llama 4 Scout vision model for independent analysis.
    """

    MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key.startswith("your_"):
            raise ValueError("Please set GROQ_API_KEY in your .env file.")
        self.client = Groq(api_key=api_key)
        self.model = self.MODEL_NAME
        self.agent_type = "groq_radiology"
        logger.info("GroqRadiologyAgent initialised with vision model %s", self.model)

    # ------------------------------------------------------------------
    # Public interface — called by DualRadiologyAgent
    # ------------------------------------------------------------------

    async def analyze_image(
        self,
        input_data: DualRadiologyInput,
    ) -> ModelOutput:
        """
        Analyze the X-ray image directly using Llama 4 Scout vision.

        Args:
            input_data: DualRadiologyInput with image_path and metadata.

        Returns:
            ModelOutput with independent Groq analysis.
        """
        from app.utils.config_manager import dual_config

        max_retries = dual_config.groq_max_retries_on_rate_limit
        backoff_base = dual_config.groq_rate_limit_backoff_base
        start_time = time.time()
        raw_response: Optional[str] = None

        for attempt in range(max_retries + 1):
            try:
                # Encode image
                image_b64 = _encode_image_to_base64(input_data.image_path)
                media_type = _get_image_media_type(input_data.image_path)

                user_content = [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{image_b64}"
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "Analyze this X-ray image and provide your independent "
                            "radiological assessment as a JSON object.\n"
                            + (f"Clinical context: {input_data.additional_info}" if input_data.additional_info else "")
                        ),
                    },
                ]

                logger.info(
                    "Sending image to Groq vision (case_id=%s, attempt=%d)",
                    input_data.case_id, attempt + 1,
                )

                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user", "content": user_content},
                    ],
                    temperature=0.2,
                    max_tokens=2048,
                )

                raw_response = completion.choices[0].message.content
                processing_time = time.time() - start_time

                parsed = _parse_groq_response(raw_response)
                output = self._build_model_output(parsed, raw_response, processing_time)

                logger.info(
                    "✅ Groq vision analysis done in %.2fs (case_id=%s, confidence=%.2f)",
                    processing_time, input_data.case_id, output.confidence,
                )
                return output

            except GroqRateLimitError as exc:
                processing_time = time.time() - start_time
                if attempt < max_retries:
                    wait = backoff_base ** attempt
                    logger.warning("Groq rate limit, backing off %.1fs", wait)
                    await asyncio.sleep(wait)
                    continue
                logger.error("Groq rate limit exhausted: %s", exc)
                return self._build_error_output(processing_time, f"Rate limit: {exc}")

            except json.JSONDecodeError as exc:
                processing_time = time.time() - start_time
                logger.warning("Groq JSON parse error: %s", exc)
                return self._build_fallback_output(raw_response or "", processing_time, str(exc))

            except Exception as exc:
                processing_time = time.time() - start_time
                logger.error("Groq vision failed: %s", exc, exc_info=True)
                return self._build_error_output(processing_time, str(exc))

        return self._build_error_output(time.time() - start_time, "Retry loop exhausted")

    # Keep backward-compat method name used by DualRadiologyAgent
    async def analyze_from_description(
        self,
        image_description: str,
        input_data: DualRadiologyInput,
    ) -> ModelOutput:
        """
        Backward-compatible wrapper — now ignores the text description
        and analyzes the image directly instead.
        """
        return await self.analyze_image(input_data)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_model_output(self, parsed: dict, raw_response: str, processing_time: float) -> ModelOutput:
        findings = parsed.get("findings", "No findings provided.")
        abnormalities = parsed.get("abnormalities", [])
        anatomical_structures = parsed.get("anatomical_structures", ["chest", "lungs", "heart", "mediastinum"])
        confidence = self._clamp_confidence(parsed.get("confidence", 0.75))
        image_quality = self._validate_image_quality(parsed.get("image_quality", "adequate"))
        recommendations = parsed.get("recommendations", "Clinical correlation recommended.")

        if not abnormalities:
            abnormalities = _extract_abnormalities_from_text(findings)

        return ModelOutput(
            model_name=self.model,
            findings=findings,
            abnormalities=abnormalities,
            anatomical_structures=anatomical_structures,
            confidence=confidence,
            image_quality=image_quality,
            recommendations=recommendations,
            processing_time=processing_time,
            timestamp=datetime.now(),
            raw_response=raw_response,
        )

    def _build_fallback_output(self, raw_response: str, processing_time: float, error_note: str) -> ModelOutput:
        return ModelOutput(
            model_name=self.model,
            findings=raw_response or "Unable to parse structured findings.",
            abnormalities=_extract_abnormalities_from_text(raw_response),
            anatomical_structures=["chest", "lungs", "heart", "mediastinum"],
            confidence=0.5,
            image_quality=self._extract_image_quality(raw_response),
            recommendations=f"Clinical correlation required. Parse issue: {error_note}",
            processing_time=processing_time,
            timestamp=datetime.now(),
            raw_response=raw_response,
        )

    def _build_error_output(self, processing_time: float, error_message: str) -> ModelOutput:
        return ModelOutput(
            model_name=self.model,
            findings=f"Analysis failed: {error_message}",
            abnormalities=[],
            anatomical_structures=[],
            confidence=0.0,
            image_quality="unknown",
            recommendations="Manual review required due to analysis error.",
            processing_time=processing_time,
            timestamp=datetime.now(),
            raw_response=None,
        )

    @staticmethod
    def _clamp_confidence(value: float) -> float:
        try:
            return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            return 0.5

    @staticmethod
    def _validate_image_quality(quality: str) -> str:
        allowed = {"excellent", "good", "adequate", "poor", "unknown"}
        n = quality.lower().strip() if quality else "unknown"
        return n if n in allowed else "adequate"

    @staticmethod
    def _extract_image_quality(text: str) -> str:
        lower = text.lower()
        for q in ["excellent", "good", "poor", "adequate"]:
            if q in lower:
                return q
        return "unknown"

    def test_connection(self) -> bool:
        try:
            self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5,
            )
            return True
        except Exception as exc:
            logger.error("Groq connection test failed: %s", exc)
            return False
