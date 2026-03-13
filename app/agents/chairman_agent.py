"""
Chairman Agent - Senior Medical Officer for Final Report Synthesis
Uses GROQ API for comprehensive medical reasoning and report generation
"""
import os
import json
from typing import Optional
from datetime import datetime
from groq import Groq
from app.models.chairman_models import ChairmanInput, ChairmanOutput
from app.database.crud import RadiologyDB
from app.database.database import get_db
from app.utils.simple_timer import simple_timer

class ChairmanAgent:
    """
    Chairman Agent - Senior Medical Officer
    Synthesizes all specialist reports into comprehensive final medical assessment
    """
    
    def __init__(self):
        self.client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        self.model = "llama-3.1-8b-instant"  # Stable GROQ model
        
    @simple_timer.time_agent("Chairman Agent")
    async def analyze(self, input_data: ChairmanInput, save_to_db: bool = True) -> ChairmanOutput:
        """
        Generate comprehensive final medical report by synthesizing all specialist findings
        """
        try:
            # Create comprehensive prompt for medical synthesis
            prompt = self._create_synthesis_prompt(input_data)
            
            # Get analysis from GROQ
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Senior Medical Officer (Chairman) with 20+ years of experience. You review specialist medical reports and provide comprehensive final medical assessments. Always prioritize patient safety and provide clear, actionable recommendations."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=4000,
                temperature=0.1  # Low temperature for consistent medical reasoning
            )
            
            # Parse the response
            analysis_text = response.choices[0].message.content
            
            # Extract structured data from response
            chairman_output = self._parse_chairman_response(analysis_text, input_data)
            
            # Save to database if requested
            if save_to_db:
                self._save_to_database(chairman_output)
            
            return chairman_output
            
        except Exception as e:
            # Return error response
            return ChairmanOutput(
                case_id=input_data.case_id,
                patient_code=input_data.patient_code,
                executive_summary=f"Chairman analysis failed: {str(e)}",
                primary_diagnosis="Analysis error - manual review required",
                differential_diagnoses=["Technical issue", "System error"],
                radiology_synthesis="Analysis failed",
                clinical_synthesis="Analysis failed", 
                evidence_synthesis="Analysis failed",
                risk_synthesis="Analysis failed",
                immediate_actions=["Manual review by senior physician required"],
                follow_up_plan=["Retry analysis with working system"],
                specialist_referrals=[],
                confidence_level=0.0,
                consensus_score=0.0,
                urgency_level="routine",
                chairman_reasoning=f"Chairman analysis encountered an error: {str(e)}",
                quality_flags=["Analysis failure", "Manual review required"]
            )
    
    def _create_synthesis_prompt(self, input_data: ChairmanInput) -> str:
        """Create comprehensive prompt for medical synthesis"""
        
        return f"""You are a Senior Medical Officer (Chairman) reviewing a comprehensive medical case. Your role is to synthesize findings from 4 specialist medical AI agents and provide a definitive final medical report.

CASE INFORMATION:
- Case ID: {input_data.case_id}
- Patient Code: {input_data.patient_code}
- Patient History: {input_data.patient_history or "Not provided"}
- Additional Notes: {input_data.additional_notes or "None"}

SPECIALIST REPORTS TO SYNTHESIZE:

1. RADIOLOGY ANALYSIS:
{json.dumps(input_data.radiology_findings, indent=2)}

2. CLINICAL ANALYSIS:
{json.dumps(input_data.clinical_findings, indent=2)}

3. EVIDENCE RESEARCH:
{json.dumps(input_data.evidence_findings, indent=2)}

4. RISK ASSESSMENT:
{json.dumps(input_data.risk_findings, indent=2)}

As the Chairman, provide a comprehensive final medical report in the following JSON format:

{{
    "executive_summary": "2-3 sentence high-level summary of the case and key findings",
    "primary_diagnosis": "Most likely primary diagnosis based on all evidence",
    "differential_diagnoses": ["Alternative diagnosis 1", "Alternative diagnosis 2", "Alternative diagnosis 3"],
    "radiology_synthesis": "Key radiology findings and their clinical significance",
    "clinical_synthesis": "Clinical interpretation and reasoning synthesis",
    "evidence_synthesis": "Evidence-based medicine findings and their relevance",
    "risk_synthesis": "Risk assessment summary and implications",
    "immediate_actions": ["Action 1", "Action 2", "Action 3"],
    "follow_up_plan": ["Follow-up 1", "Follow-up 2", "Follow-up 3"],
    "specialist_referrals": ["Referral 1 if needed", "Referral 2 if needed"],
    "confidence_level": 0.85,
    "consensus_score": 0.90,
    "urgency_level": "urgent",
    "chairman_reasoning": "Detailed explanation of your clinical reasoning process and how you synthesized the specialist reports",
    "quality_flags": ["Any quality concerns or flags"]
}}

INSTRUCTIONS:
1. Act as a senior physician with 20+ years of experience
2. Synthesize ALL specialist findings into a coherent assessment
3. Identify any conflicts between specialist reports and resolve them
4. Provide clear, actionable recommendations
5. Assign appropriate urgency level: "critical", "urgent", or "routine"
6. Calculate confidence based on agreement between specialists and quality of evidence
7. Flag any quality concerns or inconsistencies
8. Ensure medical accuracy and professional language
9. Consider patient safety as the top priority

Provide ONLY the JSON response, no additional text."""

    def _parse_chairman_response(self, response_text: str, input_data: ChairmanInput) -> ChairmanOutput:
        """Parse Claude's response into structured ChairmanOutput"""
        try:
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            json_str = response_text[json_start:json_end]
            
            parsed_data = json.loads(json_str)
            
            return ChairmanOutput(
                case_id=input_data.case_id,
                patient_code=input_data.patient_code,
                executive_summary=parsed_data.get('executive_summary', ''),
                primary_diagnosis=parsed_data.get('primary_diagnosis', ''),
                differential_diagnoses=parsed_data.get('differential_diagnoses', []),
                radiology_synthesis=parsed_data.get('radiology_synthesis', ''),
                clinical_synthesis=parsed_data.get('clinical_synthesis', ''),
                evidence_synthesis=parsed_data.get('evidence_synthesis', ''),
                risk_synthesis=parsed_data.get('risk_synthesis', ''),
                immediate_actions=parsed_data.get('immediate_actions', []),
                follow_up_plan=parsed_data.get('follow_up_plan', []),
                specialist_referrals=parsed_data.get('specialist_referrals', []),
                confidence_level=float(parsed_data.get('confidence_level', 0.5)),
                consensus_score=float(parsed_data.get('consensus_score', 0.5)),
                urgency_level=parsed_data.get('urgency_level', 'routine'),
                chairman_reasoning=parsed_data.get('chairman_reasoning', ''),
                quality_flags=parsed_data.get('quality_flags', [])
            )
            
        except Exception as e:
            # Fallback parsing if JSON parsing fails
            return ChairmanOutput(
                case_id=input_data.case_id,
                patient_code=input_data.patient_code,
                executive_summary="Chairman analysis completed with parsing issues",
                primary_diagnosis="Manual review recommended due to parsing error",
                differential_diagnoses=["Parsing error", "Manual review needed"],
                radiology_synthesis="Response parsing failed",
                clinical_synthesis="Response parsing failed",
                evidence_synthesis="Response parsing failed", 
                risk_synthesis="Response parsing failed",
                immediate_actions=["Manual review of chairman analysis"],
                follow_up_plan=["Retry with improved parsing"],
                specialist_referrals=[],
                confidence_level=0.3,
                consensus_score=0.3,
                urgency_level="routine",
                chairman_reasoning=f"Chairman analysis completed but response parsing failed: {str(e)}",
                quality_flags=["Parsing error", "Manual review recommended"]
            )
    
    def _save_to_database(self, output: ChairmanOutput):
        """Save chairman analysis to database"""
        try:
            output_data = {
                "executive_summary": output.executive_summary,
                "primary_diagnosis": output.primary_diagnosis,
                "differential_diagnoses": output.differential_diagnoses,
                "radiology_synthesis": output.radiology_synthesis,
                "clinical_synthesis": output.clinical_synthesis,
                "evidence_synthesis": output.evidence_synthesis,
                "risk_synthesis": output.risk_synthesis,
                "immediate_actions": output.immediate_actions,
                "follow_up_plan": output.follow_up_plan,
                "specialist_referrals": output.specialist_referrals,
                "confidence_level": output.confidence_level,
                "consensus_score": output.consensus_score,
                "urgency_level": output.urgency_level,
                "chairman_reasoning": output.chairman_reasoning,
                "quality_flags": output.quality_flags,
                "report_generated_at": output.report_generated_at.isoformat()
            }
            
            # Use RadiologyDB to save chairman output
            db = next(get_db())
            try:
                radiology_db = RadiologyDB(db)
                radiology_db.save_agent_output(
                    case_id=output.case_id,
                    agent_type="chairman",
                    output_data=output_data,
                    confidence=output.confidence_level
                )
            finally:
                db.close()
            
        except Exception as e:
            print(f"Failed to save chairman analysis to database: {str(e)}")

# Global instance
chairman_agent = ChairmanAgent()