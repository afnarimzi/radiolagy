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
        self.model = "llama-3.3-70b-versatile"  # Higher TPM limits
        
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
                        "content": "You are a Senior Medical Officer (Chairman) with 20+ years of experience. You review specialist medical reports and provide comprehensive final medical assessments. Always prioritize patient safety and provide clear, actionable recommendations. IMPORTANT: Always complete your JSON response fully - do not truncate any fields."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=2000,  # Keep prompt small to avoid TPM limits
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
        def _trim(obj, max_chars=400):
            s = json.dumps(obj) if not isinstance(obj, str) else obj
            return s[:max_chars] + "..." if len(s) > max_chars else s

        return f"""You are a Senior Medical Officer synthesizing specialist reports. Respond ONLY with valid JSON.

CASE: {input_data.patient_code} | History: {(input_data.patient_history or 'None')[:100]}

RADIOLOGY: {_trim(input_data.radiology_findings)}
CLINICAL: {_trim(input_data.clinical_findings)}
EVIDENCE: {_trim(input_data.evidence_findings)}
RISK: {_trim(input_data.risk_findings)}

Return this JSON (no extra text):
{{
    "executive_summary": "2-3 sentence summary",
    "primary_diagnosis": "most likely diagnosis",
    "differential_diagnoses": ["alt 1", "alt 2"],
    "radiology_synthesis": "key radiology findings",
    "clinical_synthesis": "clinical interpretation",
    "evidence_synthesis": "evidence relevance",
    "risk_synthesis": "risk summary",
    "immediate_actions": ["action 1", "action 2"],
    "follow_up_plan": ["follow-up 1"],
    "specialist_referrals": ["referral if needed"],
    "confidence_level": 0.85,
    "consensus_score": 0.90,
    "urgency_level": "urgent",
    "chairman_reasoning": "brief clinical reasoning",
    "quality_flags": []
}}"""

    def _parse_chairman_response(self, response_text: str, input_data: ChairmanInput) -> ChairmanOutput:
        """Parse Claude's response into structured ChairmanOutput"""
        try:
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response_text[json_start:json_end]
            
            # Check if JSON is complete (basic validation)
            if json_str.count('{') != json_str.count('}'):
                print(f"⚠️  Warning: Incomplete JSON detected in chairman response")
                print(f"📝 Raw response length: {len(response_text)} characters")
                print(f"🔍 JSON portion: {json_str[:200]}...")
                
                # Try to fix incomplete JSON by adding missing closing braces
                open_braces = json_str.count('{') - json_str.count('}')
                if open_braces > 0:
                    json_str += '}' * open_braces
                    print(f"🔧 Attempted to fix JSON by adding {open_braces} closing braces")
            
            parsed_data = json.loads(json_str)
            
            # Ensure all required fields have values, with fallbacks for incomplete responses
            return ChairmanOutput(
                case_id=input_data.case_id,
                patient_code=input_data.patient_code,
                executive_summary=parsed_data.get('executive_summary', 'Executive summary not fully generated - manual review recommended'),
                primary_diagnosis=parsed_data.get('primary_diagnosis', 'Primary diagnosis pending - requires manual review'),
                differential_diagnoses=parsed_data.get('differential_diagnoses', ['Manual review required']),
                radiology_synthesis=parsed_data.get('radiology_synthesis', 'Radiology synthesis incomplete'),
                clinical_synthesis=parsed_data.get('clinical_synthesis', 'Clinical synthesis incomplete'),
                evidence_synthesis=parsed_data.get('evidence_synthesis', 'Evidence synthesis incomplete'),
                risk_synthesis=parsed_data.get('risk_synthesis', 'Risk synthesis incomplete'),
                immediate_actions=parsed_data.get('immediate_actions', ['Complete manual review of all findings', 'Consult with senior physician']),
                follow_up_plan=parsed_data.get('follow_up_plan', ['Schedule follow-up appointment', 'Monitor patient condition']),
                specialist_referrals=parsed_data.get('specialist_referrals', []),
                confidence_level=float(parsed_data.get('confidence_level', 0.5)),
                consensus_score=float(parsed_data.get('consensus_score', 0.5)),
                urgency_level=parsed_data.get('urgency_level', 'routine'),
                chairman_reasoning=parsed_data.get('chairman_reasoning', 'Chairman reasoning incomplete - manual review required'),
                quality_flags=parsed_data.get('quality_flags', ['Incomplete AI response', 'Manual review recommended'])
            )
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error in chairman response: {str(e)}")
            print(f"📝 Raw response: {response_text[:500]}...")
            
            # Fallback parsing if JSON parsing fails
            return ChairmanOutput(
                case_id=input_data.case_id,
                patient_code=input_data.patient_code,
                executive_summary="Chairman analysis completed with JSON parsing issues - manual review recommended",
                primary_diagnosis="Manual review recommended due to parsing error",
                differential_diagnoses=["JSON parsing error", "Manual review needed"],
                radiology_synthesis="Response parsing failed - see raw AI output",
                clinical_synthesis="Response parsing failed - see raw AI output",
                evidence_synthesis="Response parsing failed - see raw AI output", 
                risk_synthesis="Response parsing failed - see raw AI output",
                immediate_actions=["Manual review of chairman analysis", "Check raw AI response for complete findings"],
                follow_up_plan=["Retry analysis with improved parsing", "Manual physician review"],
                specialist_referrals=[],
                confidence_level=0.3,
                consensus_score=0.3,
                urgency_level="routine",
                chairman_reasoning=f"Chairman analysis completed but JSON parsing failed: {str(e)}. Raw response available for manual review.",
                quality_flags=["JSON parsing error", "Manual review recommended", "Raw AI response available"]
            )
        except Exception as e:
            print(f"❌ Unexpected error in chairman response parsing: {str(e)}")
            
            # General fallback
            return ChairmanOutput(
                case_id=input_data.case_id,
                patient_code=input_data.patient_code,
                executive_summary="Chairman analysis encountered unexpected error - manual review required",
                primary_diagnosis="Manual review recommended due to system error",
                differential_diagnoses=["System error", "Manual review needed"],
                radiology_synthesis="Analysis failed due to system error",
                clinical_synthesis="Analysis failed due to system error",
                evidence_synthesis="Analysis failed due to system error", 
                risk_synthesis="Analysis failed due to system error",
                immediate_actions=["Manual review by senior physician required", "System troubleshooting needed"],
                follow_up_plan=["Retry analysis with working system", "Manual physician assessment"],
                specialist_referrals=[],
                confidence_level=0.1,
                consensus_score=0.1,
                urgency_level="routine",
                chairman_reasoning=f"Chairman analysis encountered an unexpected error: {str(e)}",
                quality_flags=["System error", "Manual review required", "Technical issue"]
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