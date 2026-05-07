"""
Radiology Agent - Analyzes X-ray images using Google Gemini Vision
"""
import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, Union, Optional
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app.models.radiology_models import XrayInput, RadiologyFindings, RadiologyError, ModelOutput, DualRadiologyInput
from app.database.database import get_db
from app.utils.simple_timer import simple_timer

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class RadiologyAgent:
    """
    AI Agent specialized in radiology analysis using Google Gemini Vision
    Analyzes actual X-ray images and provides medical findings
    """
    
    def __init__(self):
        """Initialize the Radiology Agent"""
        # Configure Gemini
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key or api_key == "your_google_api_key_here":
            raise ValueError("Please set GOOGLE_API_KEY in your .env file")
        
        genai.configure(api_key=api_key)
        
        # Use Gemini 2.5 Flash (supports vision and is available)
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        self.agent_type = "radiology"
        
    def _create_analysis_prompt(self, additional_info: str = None) -> str:
        """Create a structured prompt for X-ray image analysis"""
        base_prompt = """
You are an expert radiologist analyzing this X-ray image. Provide a comprehensive, professional radiology report.

Analyze the X-ray image systematically and provide:

1. **TECHNIQUE & QUALITY**: Comment on image quality, positioning, and technique
2. **FINDINGS**: Detailed description of all anatomical structures and any abnormalities
3. **IMPRESSION**: Summary of key findings and clinical significance
4. **RECOMMENDATIONS**: Clinical recommendations and follow-up suggestions

Write your response as a detailed medical report, NOT in JSON format. Use professional medical terminology as a radiologist would write in a hospital report.

Structure your response like this:
TECHNIQUE: [Image quality and positioning]
FINDINGS: [Detailed systematic analysis of all structures - heart, lungs, bones, soft tissues]
IMPRESSION: [Summary of key findings]
RECOMMENDATIONS: [Clinical recommendations]

Be thorough, specific, and use proper medical terminology. If you see abnormalities, describe them in detail including location, size, characteristics, and potential differential diagnoses.
"""
        
        if additional_info:
            base_prompt += f"\nCLINICAL INFORMATION: {additional_info}\n"
        
        return base_prompt
    
    def _load_image(self, xray_input: XrayInput) -> Image.Image:
        """Load image from various input sources"""
        try:
            if xray_input.image_path:
                # Load from file path
                return Image.open(xray_input.image_path)
            elif xray_input.image_data:
                # Load from bytes data
                from io import BytesIO
                return Image.open(BytesIO(xray_input.image_data))
            elif xray_input.image_url:
                # Load from URL
                import requests
                response = requests.get(xray_input.image_url)
                from io import BytesIO
                return Image.open(BytesIO(response.content))
            else:
                raise ValueError("No image source provided")
        except Exception as e:
            raise ValueError(f"Failed to load image: {str(e)}")
    
    @simple_timer.time_agent("Radiology Agent")
    async def analyze(self, xray_input: XrayInput, save_to_db: bool = True) -> RadiologyFindings:
        """
        Analyze X-ray image and return structured findings
        
        Args:
            xray_input: XrayInput model with image and metadata
            save_to_db: Whether to save the report to database (default: True)
            
        Returns:
            RadiologyFindings: Structured analysis results
        """
        try:
            start_time = time.time()
            
            # Load the image
            image = self._load_image(xray_input)
            
            # Create analysis prompt
            prompt = self._create_analysis_prompt(xray_input.additional_info)
            
            # Generate response with Gemini Vision
            response = self.model.generate_content(
                [prompt, image],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=4096,
                    candidate_count=1
                )
            )
            
            # Get response text
            analysis_text = response.text
            
            # Parse the medical report (no longer expecting JSON)
            # Extract key information from the professional report
            findings_text = analysis_text.replace("**", "")
            
            # Try to extract structured information from the report
            abnormalities = []
            confidence = 0.8  # Default confidence for detailed reports
            recommendations = "Clinical correlation recommended"
            image_quality = "adequate"
            anatomical_structures = ["chest", "lungs", "heart", "mediastinum", "bones"]
            
            # Simple keyword extraction for abnormalities - improved logic
            lower_text = analysis_text.lower()
            
            # Look for actual abnormalities, not just mentions
            # Check context around keywords to avoid false positives
            if "pneumonia" in lower_text or "consolidation" in lower_text:
                # Check if it's mentioned as present (not "no pneumonia")
                context_words = ["no", "without", "clear", "negative"]
                pneumonia_context = ""
                for word in ["pneumonia", "consolidation"]:
                    if word in lower_text:
                        idx = lower_text.find(word)
                        pneumonia_context = lower_text[max(0, idx-30):idx+30]
                        break
                if not any(neg in pneumonia_context for neg in context_words):
                    abnormalities.append("pneumonia/consolidation")
            
            if "effusion" in lower_text:
                idx = lower_text.find("effusion")
                effusion_context = lower_text[max(0, idx-30):idx+30]
                if not any(neg in effusion_context for neg in ["no", "without", "clear"]):
                    abnormalities.append("pleural effusion")
            
            if "fracture" in lower_text:
                idx = lower_text.find("fracture")
                fracture_context = lower_text[max(0, idx-30):idx+30]
                if not any(neg in fracture_context for neg in ["no", "without", "prior", "old"]):
                    abnormalities.append("acute fracture")
            
            # Check for masses/nodules
            for word in ["mass", "nodule", "lesion"]:
                if word in lower_text:
                    idx = lower_text.find(word)
                    context = lower_text[max(0, idx-30):idx+30]
                    if not any(neg in context for neg in ["no", "without", "clear"]):
                        abnormalities.append("mass/nodule")
                        break
            
            # Check for other findings
            if "cardiomegaly" in lower_text or "enlarged heart" in lower_text:
                abnormalities.append("cardiomegaly")
            
            if "atelectasis" in lower_text:
                idx = lower_text.find("atelectasis")
                context = lower_text[max(0, idx-30):idx+30]
                if not any(neg in context for neg in ["no", "without"]):
                    abnormalities.append("atelectasis")
            
            if "pneumothorax" in lower_text:
                idx = lower_text.find("pneumothorax")
                context = lower_text[max(0, idx-30):idx+30]
                if not any(neg in context for neg in ["no", "without"]):
                    abnormalities.append("pneumothorax")
            
            # Check for pulmonary edema
            for word in ["edema", "congestion"]:
                if word in lower_text:
                    idx = lower_text.find(word)
                    context = lower_text[max(0, idx-30):idx+30]
                    if not any(neg in context for neg in ["no", "without"]):
                        abnormalities.append("pulmonary edema")
                        break
            
            # Extract image quality if mentioned
            if "excellent" in lower_text:
                image_quality = "excellent"
            elif "good" in lower_text:
                image_quality = "good"
            elif "poor" in lower_text or "limited" in lower_text:
                image_quality = "poor"
            elif "adequate" in lower_text or "satisfactory" in lower_text:
                image_quality = "adequate"
            
            # Extract recommendations if present
            lines = analysis_text.split('\n')
            for line in lines:
                if "recommend" in line.lower() and len(line.strip()) > 10:
                    recommendations = line.strip()
                    break
            
            # If no abnormalities found, check for "normal" indicators
            if not abnormalities:
                if any(word in lower_text for word in ["normal", "unremarkable", "clear", "no acute"]):
                    abnormalities = []  # Keep empty for normal findings
                else:
                    # If unclear, mark as requiring review
                    abnormalities = ["findings require clinical correlation"]
            
            # Create structured findings
            findings = RadiologyFindings(
                case_id=xray_input.case_id,
                findings=findings_text,
                abnormalities=abnormalities,
                anatomical_structures=anatomical_structures,
                confidence=confidence,
                recommendations=recommendations,
                image_quality=image_quality
            )
            
            processing_time = time.time() - start_time
            print(f"✅ Gemini vision analysis completed in {processing_time:.2f}s")
            
            # Save to database if requested
            if save_to_db:
                try:
                    db = next(get_db())
                    from app.database.crud import RadiologyDB
                    
                    radiology_db = RadiologyDB(db)
                    
                    # Create case input
                    input_data = {
                        "xray_description": xray_input.additional_info or "X-ray analysis",
                        "image_quality": image_quality,
                        "analysis_timestamp": findings.timestamp.isoformat()
                    }
                    
                    if xray_input.thread_id:
                        case_input = radiology_db.create_case_input_with_thread(
                            case_id=findings.case_id,
                            patient_code=xray_input.patient_code or "UNKNOWN",
                            input_data=input_data,
                            thread_id=xray_input.thread_id,
                            image_path=xray_input.image_path,
                            additional_info=xray_input.additional_info
                        )
                    else:
                        case_input = radiology_db.create_case_input(
                            case_id=findings.case_id,
                            patient_code=xray_input.patient_code or "UNKNOWN",
                            input_data=input_data,
                            image_path=xray_input.image_path,
                            additional_info=xray_input.additional_info
                        )
                    
                    # Save analysis output
                    output_data = {
                        "findings": findings.findings,
                        "abnormalities": findings.abnormalities,
                        "anatomical_structures": findings.anatomical_structures,
                        "recommendations": findings.recommendations,
                        "image_quality": findings.image_quality,
                        "agent_type": findings.agent_type
                    }
                    
                    case_output = radiology_db.save_analysis_output(
                        case_id=findings.case_id,
                        output_data=output_data,
                        confidence=findings.confidence,
                        processing_time=processing_time
                    )
                    
                    # Create agent thread
                    thread = radiology_db.create_agent_thread(
                        case_id=findings.case_id
                    )
                    
                    # Create medical report
                    report_content = f"""RADIOLOGY REPORT
                    
Case ID: {findings.case_id}
Patient: {xray_input.patient_code or 'UNKNOWN'}
Date: {findings.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Image Quality: {findings.image_quality}

FINDINGS:
{findings.findings}

ABNORMALITIES DETECTED:
{', '.join(findings.abnormalities) if findings.abnormalities else 'None'}

RECOMMENDATIONS:
{findings.recommendations}

Confidence Score: {findings.confidence:.2f}
Processing Time: {processing_time:.2f}s
Generated by: Radiology AI Agent"""
                    
                    medical_report = radiology_db.create_medical_report(
                        case_id=findings.case_id,
                        report_content=report_content,
                        findings_summary=', '.join(findings.abnormalities) if findings.abnormalities else 'Normal study',
                        recommendations=findings.recommendations
                    )
                    
                    # Update thread status
                    radiology_db.update_thread_status(thread.thread_id, 'completed')
                    
                    print(f"💾 Report saved to database (Case ID: {findings.case_id})")
                    
                except Exception as db_error:
                    print(f"⚠️  Database save failed: {str(db_error)}")
                    import traceback
                    traceback.print_exc()
                    # Continue without failing the analysis
            
            return findings
            
        except Exception as e:
            print(f"❌ Error in Gemini vision analysis: {str(e)}")
            # Return error as RadiologyFindings with low confidence
            return RadiologyFindings(
                case_id=xray_input.case_id,
                findings=f"Analysis failed: {str(e)}",
                abnormalities=[],
                anatomical_structures=[],
                confidence=0.0,
                recommendations="Manual review required due to analysis error",
                image_quality="unknown"
            )
    
    async def analyze_image_file(self, image_path: str, patient_code: str = None, additional_info: str = None, save_to_db: bool = True) -> Dict[str, Any]:
        """
        Simple method to analyze an image file
        
        Args:
            image_path: Path to X-ray image file
            patient_code: Optional patient identifier
            additional_info: Optional additional clinical information
            save_to_db: Whether to save the report to database (default: True)
            
        Returns:
            Dict with analysis results
        """
        xray_input = XrayInput(
            image_path=image_path,
            patient_code=patient_code,
            additional_info=additional_info
        )
        findings = await self.analyze(xray_input, save_to_db=save_to_db)
        
        return {
            "case_id": findings.case_id,
            "findings": findings.findings,
            "abnormalities": findings.abnormalities,
            "anatomical_structures": findings.anatomical_structures,
            "confidence": findings.confidence,
            "recommendations": findings.recommendations,
            "image_quality": findings.image_quality,
            "agent_type": findings.agent_type,
            "timestamp": findings.timestamp.isoformat()
        }
    
    # ------------------------------------------------------------------
    # Dual-model workflow methods (new — backward-compatible additions)
    # ------------------------------------------------------------------

    def _create_description_prompt(self, additional_info: Optional[str] = None) -> str:
        """
        Create a prompt that asks Gemini to produce a rich, structured textual
        description of the X-ray image.  This description is passed to the Groq
        agent so it can perform independent text-based medical reasoning.
        """
        prompt = """
You are an expert radiologist.  Your task is to produce a detailed, structured
textual description of this X-ray image so that another physician who cannot see
the image can perform an independent analysis.

Describe the image systematically, covering:

1. IMAGE CHARACTERISTICS: Modality, projection (PA/AP/lateral), patient positioning,
   exposure quality, contrast, and any technical artefacts.
2. ANATOMICAL SURVEY: Describe every visible structure in detail —
   - Lungs: fields, vascularity, parenchyma, costophrenic angles, hila
   - Heart: size, contour, cardiothoracic ratio
   - Mediastinum: width, contour, tracheal position
   - Bones: ribs, clavicles, scapulae, spine, visible shoulder joints
   - Soft tissues: visible soft-tissue abnormalities
   - Diaphragm: position, contour, subdiaphragmatic space
3. ABNORMAL FINDINGS: Describe any opacity, lucency, mass, effusion, consolidation,
   atelectasis, pneumothorax, fracture, or other abnormality with precise location,
   size, shape, density, and borders.
4. OVERALL IMPRESSION: Summarise the key findings in 2–3 sentences.

Be exhaustive and precise.  Use standard radiological terminology.
Do NOT provide a diagnosis or recommendations — only describe what you observe.
"""
        if additional_info:
            prompt += f"\nCLINICAL CONTEXT (for reference only): {additional_info}\n"
        return prompt

    async def get_image_description(self, input_data: DualRadiologyInput) -> str:
        """
        Generate a detailed textual description of the X-ray image using Gemini
        Vision.  This description is intended to be passed to the GroqRadiologyAgent
        so it can perform independent text-based medical reasoning.

        Args:
            input_data: DualRadiologyInput containing the image source and metadata.

        Returns:
            str: A rich, structured textual description of the X-ray image.

        Raises:
            ValueError: If the image cannot be loaded.
        """
        # Re-use the existing image loader by adapting DualRadiologyInput → XrayInput
        xray_input = XrayInput(
            image_path=input_data.image_path,
            image_data=input_data.image_data,
            image_url=input_data.image_url,
            patient_code=input_data.patient_code,
            case_id=input_data.case_id,
            additional_info=input_data.additional_info,
            thread_id=input_data.thread_id,
        )
        image = self._load_image(xray_input)
        prompt = self._create_description_prompt(input_data.additional_info)

        logger.info("Generating image description for Groq (case_id=%s)", input_data.case_id)

        response = self.model.generate_content(
            [prompt, image],
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,   # Low temperature for factual description
                max_output_tokens=2048,
                candidate_count=1,
            ),
        )
        description = response.text.strip()
        logger.info(
            "Image description generated (case_id=%s, length=%d chars)",
            input_data.case_id,
            len(description),
        )
        return description

    async def analyze_image(self, input_data: DualRadiologyInput) -> ModelOutput:
        """
        Analyze an X-ray image using Gemini Vision and return a ModelOutput
        compatible with the dual-model validation workflow.

        This method is the dual-model counterpart of the existing ``analyze()``
        method.  It performs the same Gemini Vision analysis but returns a
        ``ModelOutput`` (the shared dual-model interface) instead of
        ``RadiologyFindings``, and collects enhanced metadata required for
        consensus analysis.

        The existing ``analyze()`` method is NOT modified — backward compatibility
        is fully preserved.

        Args:
            input_data: DualRadiologyInput containing the image source, metadata,
                        and optional validation configuration.

        Returns:
            ModelOutput: Structured analysis results from Gemini 2.5 Flash.
        """
        start_time = time.time()
        raw_response: Optional[str] = None

        try:
            # Adapt DualRadiologyInput → XrayInput for the shared image loader
            xray_input = XrayInput(
                image_path=input_data.image_path,
                image_data=input_data.image_data,
                image_url=input_data.image_url,
                patient_code=input_data.patient_code,
                case_id=input_data.case_id,
                additional_info=input_data.additional_info,
                thread_id=input_data.thread_id,
            )
            image = self._load_image(xray_input)
            prompt = self._create_analysis_prompt(input_data.additional_info)

            logger.info(
                "Starting Gemini Vision analysis for dual-model workflow (case_id=%s)",
                input_data.case_id,
            )

            response = self.model.generate_content(
                [prompt, image],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=4096,
                    candidate_count=1,
                ),
            )

            raw_response = response.text
            processing_time = time.time() - start_time

            # ---- Parse the free-text report into structured fields ----
            findings_text = raw_response.replace("**", "")
            lower_text = raw_response.lower()

            # Abnormality extraction (mirrors existing analyze() logic)
            abnormalities = []
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
                    if kw in lower_text and not _has_negation(lower_text, kw):
                        abnormalities.append(label)
                        break

            # Image quality extraction
            image_quality = "adequate"
            if "excellent" in lower_text:
                image_quality = "excellent"
            elif "good" in lower_text:
                image_quality = "good"
            elif "poor" in lower_text or "limited" in lower_text:
                image_quality = "poor"
            elif "adequate" in lower_text or "satisfactory" in lower_text:
                image_quality = "adequate"

            # Recommendations extraction
            recommendations = "Clinical correlation recommended."
            for line in raw_response.split("\n"):
                if "recommend" in line.lower() and len(line.strip()) > 10:
                    recommendations = line.strip()
                    break

            # Confidence: use 0.85 for a successful detailed Gemini Vision analysis
            confidence = 0.85

            output = ModelOutput(
                model_name="gemini-2.5-flash",
                findings=findings_text,
                abnormalities=abnormalities,
                anatomical_structures=["chest", "lungs", "heart", "mediastinum", "bones"],
                confidence=confidence,
                image_quality=image_quality,
                recommendations=recommendations,
                processing_time=processing_time,
                timestamp=datetime.now(),
                raw_response=raw_response,
            )

            logger.info(
                "✅ Gemini dual-model analysis completed in %.2fs (case_id=%s, confidence=%.2f)",
                processing_time,
                input_data.case_id,
                confidence,
            )
            return output

        except Exception as exc:
            processing_time = time.time() - start_time
            logger.error(
                "❌ Gemini dual-model analysis failed (case_id=%s): %s",
                input_data.case_id,
                exc,
                exc_info=True,
            )
            return ModelOutput(
                model_name="gemini-2.5-flash",
                findings=f"Analysis failed: {exc}",
                abnormalities=[],
                anatomical_structures=[],
                confidence=0.0,
                image_quality="unknown",
                recommendations="Manual review required due to analysis error.",
                processing_time=processing_time,
                timestamp=datetime.now(),
                raw_response=raw_response,
            )

    def test_connection(self) -> bool:
        """Test if Gemini API connection is working"""
        try:
            response = self.model.generate_content("Hello, this is a test.")
            return True
        except Exception as e:
            print(f"❌ Gemini connection test failed: {str(e)}")
            return False