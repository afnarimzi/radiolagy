"""
Clinical Agent - To be implemented
"""

# TODO: Implement Clinical Agent for clinical decision support
"""
Clinical Reasoning Agent - Differential diagnosis from radiology findings
"""
import os
import json
from groq import Groq
from datetime import datetime
from dotenv import load_dotenv

from app.database.database import get_db
from app.database.crud import RadiologyDB
from app.models.clinical_models import ClinicalInput, ClinicalFindings

load_dotenv()

class ClinicalAgent:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"

    def analyze(self, clinical_input: ClinicalInput, save_to_db: bool = True) -> ClinicalFindings:
        """Run clinical reasoning on radiology findings"""

        # build prompt
        abnormalities_text = ", ".join(clinical_input.abnormalities) if clinical_input.abnormalities else "none specified"

        prompt = f"""You are an expert clinical physician reviewing radiology findings.

Radiology Findings: {clinical_input.radiology_findings}
Detected Abnormalities: {abnormalities_text}
Radiology Confidence: {clinical_input.confidence}
Additional Info: {clinical_input.additional_info or 'None'}

Provide a clinical reasoning analysis. Respond ONLY in this exact JSON format:
{{
  "differential_diagnosis": ["diagnosis1", "diagnosis2", "diagnosis3"],
  "reasoning": "detailed clinical reasoning here",
  "confidence": 0.85,
  "urgency": "routine",
  "recommended_followup": "next clinical steps"
}}

urgency must be one of: routine / urgent / emergency"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        raw = response.choices[0].message.content
        start = raw.find("{")
        end = raw.rfind("}") + 1
        result = json.loads(raw[start:end])

        findings = ClinicalFindings(
            case_id=clinical_input.case_id,
            patient_code=clinical_input.patient_code,
            differential_diagnosis=result["differential_diagnosis"],
            reasoning=result["reasoning"],
            confidence=result["confidence"],
            urgency=result["urgency"],
            recommended_followup=result["recommended_followup"]
        )

        # save to DB
        if save_to_db:
            self._save_to_db(clinical_input, findings)

        return findings

    def _save_to_db(self, clinical_input: ClinicalInput, findings: ClinicalFindings):
        """Save clinical results to patient_outputs table"""
        import time
        start_time = time.time()

        db = next(get_db())
        try:
            radiology_db = RadiologyDB(db)
            radiology_db.save_agent_output(
                case_id=clinical_input.case_id,
                agent_type="clinical",
                output_data={
                    "differential_diagnosis": findings.differential_diagnosis,
                    "reasoning": findings.reasoning,
                    "urgency": findings.urgency,
                    "recommended_followup": findings.recommended_followup
                },
                confidence=findings.confidence,
                processing_time=round(time.time() - start_time, 2)
            )
        finally:
            db.close()