"""
Risk Assessment Agent using Google Gemini AI
Analyzes radiology findings to assess patient risk levels and recommend actions
"""
import os
import json
from typing import Dict, Any
from datetime import datetime
import google.generativeai as genai

from app.models.risk_models import RiskInput, RiskAssessment, RiskLevel, ActionType
from app.database.crud import RadiologyDB
from app.database.database import get_db
from app.database.models import PatientOutput

class RiskAssessmentAgent:
    """
    AI-powered Risk Assessment Agent using Google Gemini
    Analyzes medical findings to determine risk levels and recommend actions
    """
    
    def __init__(self):
        """Initialize the Risk Assessment Agent with Gemini AI"""
        self.agent_name = "AI Risk Assessment Agent"
        self.version = "2.0.0"
        self.model_name = "gemini-2.5-flash"
        
        # Configure Gemini API with separate key for risk agent
        api_key = os.getenv("RISK_AGENT_API_KEY")
        if not api_key or api_key == "your_risk_agent_gemini_key_here":
            # Fallback to main Gemini key if risk agent key not set
            api_key = os.getenv("GOOGLE_API_KEY")
            
        if not api_key:
            raise ValueError("No Gemini API key found. Set RISK_AGENT_API_KEY or GOOGLE_API_KEY in .env file")
            
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(self.model_name)
        
        # System prompt for medical risk assessment
        self.system_prompt = """You are an expert medical AI specializing in risk assessment for radiology findings. 

Your task is to analyze radiology findings and patient information to determine:
1. Risk level (LOW, MEDIUM, HIGH, CRITICAL)
2. Recommended action (routine_followup, schedule_appointment, urgent_consultation, emergency_department, immediate_hospitalization)
3. Urgency timeline
4. Critical findings that require immediate attention
5. Detailed reasoning for the assessment

RISK LEVEL GUIDELINES:
- LOW (0.0-0.3): Normal findings, routine follow-up
- MEDIUM (0.3-0.6): Minor abnormalities, scheduled appointment needed
- HIGH (0.6-0.8): Significant findings, urgent consultation required
- CRITICAL (0.8-1.0): Life-threatening conditions, emergency care needed

CRITICAL CONDITIONS (always CRITICAL risk):
- Pneumothorax, tension pneumothorax
- Massive pleural effusion
- Aortic dissection, aneurysm rupture
- Pulmonary embolism
- Acute fractures with complications
- Foreign body aspiration
- Pneumoperitoneum (free air)

HIGH-RISK CONDITIONS:
- Pneumonia, consolidation
- Large masses or nodules
- Significant cardiomegaly
- Multiple rib fractures
- Atelectasis with symptoms

CONSIDER PATIENT FACTORS:
- Age (elderly patients have higher risk)
- Confidence level of radiology findings
- Multiple abnormalities increase risk

You must respond with valid JSON only, no additional text."""

    def _create_risk_prompt(self, risk_input: RiskInput) -> str:
        """Create the prompt for risk assessment"""
        prompt = f"""
PATIENT CASE FOR RISK ASSESSMENT:

Case ID: {risk_input.case_id}
Patient Age: {risk_input.patient_age or 'Unknown'}
Radiology Confidence: {risk_input.confidence:.2f}

RADIOLOGY FINDINGS:
{risk_input.radiology_findings}

IDENTIFIED ABNORMALITIES:
{', '.join(risk_input.abnormalities) if risk_input.abnormalities else 'None reported'}

ADDITIONAL CONTEXT:
Patient Symptoms: {risk_input.patient_symptoms or 'Not provided'}
Clinical Context: {risk_input.clinical_context or 'Not provided'}

REQUIRED JSON RESPONSE FORMAT:
{{
    "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
    "risk_score": 0.0-1.0,
    "recommended_action": "routine_followup|schedule_appointment|urgent_consultation|emergency_department|immediate_hospitalization",
    "urgency_timeline": "specific timeline (e.g., 'within 1 hour', 'within 1-2 weeks')",
    "critical_findings": ["list", "of", "critical", "findings"],
    "risk_factors": ["list", "of", "risk", "factors"],
    "next_steps": ["specific", "actionable", "steps"],
    "reasoning": "detailed explanation of risk assessment",
    "follow_up_required": true|false,
    "specialist_referral": "specialty if needed or null"
}}

Analyze this case and provide your risk assessment in the exact JSON format above.
"""
        return prompt

    def _parse_gemini_response(self, response_text: str, case_id: str) -> Dict[str, Any]:
        """Parse and validate Gemini response"""
        try:
            # Clean the response text
            response_text = response_text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            # Parse JSON
            result = json.loads(response_text.strip())
            
            # Validate required fields
            required_fields = ['risk_level', 'risk_score', 'recommended_action', 'urgency_timeline', 'reasoning']
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate enums
            if result['risk_level'] not in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
                result['risk_level'] = 'MEDIUM'  # Default fallback
                
            valid_actions = ['routine_followup', 'schedule_appointment', 'urgent_consultation', 
                           'emergency_department', 'immediate_hospitalization']
            if result['recommended_action'] not in valid_actions:
                result['recommended_action'] = 'schedule_appointment'  # Default fallback
            
            # Ensure lists exist
            result['critical_findings'] = result.get('critical_findings', [])
            result['risk_factors'] = result.get('risk_factors', [])
            result['next_steps'] = result.get('next_steps', [])
            
            # Ensure risk score is valid
            risk_score = float(result.get('risk_score', 0.5))
            result['risk_score'] = max(0.0, min(1.0, risk_score))
            
            return result
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"Error parsing Gemini response: {e}")
            print(f"Raw response: {response_text[:200]}...")
            
            # Return fallback response
            return {
                'risk_level': 'MEDIUM',
                'risk_score': 0.5,
                'recommended_action': 'schedule_appointment',
                'urgency_timeline': 'within 1-2 weeks',
                'critical_findings': [],
                'risk_factors': ['Unable to parse AI response'],
                'next_steps': ['Contact healthcare provider for evaluation'],
                'reasoning': f'AI response parsing failed. Manual review recommended for case {case_id}.',
                'follow_up_required': True,
                'specialist_referral': None
            }

    def _save_to_database(self, risk_assessment: RiskAssessment, processing_time: float = 0.0) -> bool:
        """Save risk assessment to database"""
        try:
            # Get database session and save
            db = next(get_db())
            try:
                radiology_db = RadiologyDB(db)
                
                # Check if case input exists, if not create it
                case_input = radiology_db.get_case_input(risk_assessment.case_id)
                if not case_input:
                    # Create a basic case input for the risk assessment
                    input_data = {
                        "source": "risk_assessment",
                        "case_type": "risk_analysis",
                        "created_by": "risk_agent"
                    }
                    case_input = radiology_db.create_case_input(
                        case_id=risk_assessment.case_id,
                        patient_code="RISK_PATIENT",  # Default patient for risk-only cases
                        input_data=input_data,
                        additional_info="Case created for risk assessment"
                    )
                
                # Prepare output data for database
                output_data = {
                    "risk_level": risk_assessment.risk_level.value,
                    "risk_score": risk_assessment.risk_score,
                    "recommended_action": risk_assessment.recommended_action.value,
                    "urgency_timeline": risk_assessment.urgency_timeline,
                    "critical_findings": risk_assessment.critical_findings,
                    "risk_factors": risk_assessment.risk_factors,
                    "next_steps": risk_assessment.next_steps,
                    "reasoning": risk_assessment.reasoning,
                    "follow_up_required": risk_assessment.follow_up_required,
                    "specialist_referral": risk_assessment.specialist_referral,
                    "agent_type": risk_assessment.agent_type,
                    "timestamp": risk_assessment.timestamp.isoformat()
                }
                
                # Save as patient output with agent_type='risk'
                output = PatientOutput(
                    case_id=risk_assessment.case_id,
                    agent_type='risk',
                    output_data=output_data,
                    confidence=risk_assessment.risk_score,  # Use risk score as confidence
                    processing_time=processing_time
                )
                db.add(output)
                db.commit()
                db.refresh(output)
                
                return True
                
            finally:
                db.close()
            
        except Exception as e:
            print(f"Error saving risk assessment to database: {str(e)}")
            return False
    def assess_risk(self, risk_input: RiskInput, save_to_db: bool = True) -> RiskAssessment:
        """
        Assess patient risk using Gemini AI
        
        Args:
            risk_input: RiskInput containing patient and radiology data
            save_to_db: Whether to save results to database (default: True)
            
        Returns:
            RiskAssessment with AI-generated risk analysis
        """
        start_time = datetime.now()
        
        try:
            # Create the prompt
            prompt = self._create_risk_prompt(risk_input)
            
            # Get AI response
            response = self.model.generate_content(prompt)
            
            if not response.text:
                raise ValueError("Empty response from Gemini AI")
            
            # Parse the response
            parsed_result = self._parse_gemini_response(response.text, risk_input.case_id)
            
            # Create RiskAssessment object
            risk_assessment = RiskAssessment(
                case_id=risk_input.case_id,
                risk_level=RiskLevel(parsed_result['risk_level'].lower()),
                risk_score=parsed_result['risk_score'],
                critical_findings=parsed_result['critical_findings'],
                risk_factors=parsed_result['risk_factors'],
                recommended_action=ActionType(parsed_result['recommended_action']),
                urgency_timeline=parsed_result['urgency_timeline'],
                next_steps=parsed_result['next_steps'],
                reasoning=parsed_result['reasoning'],
                follow_up_required=parsed_result.get('follow_up_required', True),
                specialist_referral=parsed_result.get('specialist_referral'),
                agent_type="ai_risk_assessment",
                timestamp=datetime.now()
            )
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Save to database if requested
            if save_to_db:
                saved = self._save_to_database(risk_assessment, processing_time)
                if saved:
                    print(f"✅ Risk assessment saved to database (Case: {risk_input.case_id})")
                else:
                    print(f"⚠️  Risk assessment completed but not saved to database")
            
            return risk_assessment
            
        except Exception as e:
            print(f"Error in AI risk assessment: {str(e)}")
            
            # Calculate processing time for fallback
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Return fallback assessment
            fallback_assessment = RiskAssessment(
                case_id=risk_input.case_id,
                risk_level=RiskLevel.MEDIUM,
                risk_score=0.5,
                critical_findings=[],
                risk_factors=[f"AI assessment failed: {str(e)}"],
                recommended_action=ActionType.SCHEDULE_APPOINTMENT,
                urgency_timeline="within 1-2 weeks",
                next_steps=["Contact healthcare provider for manual review"],
                reasoning=f"AI risk assessment encountered an error. Manual review recommended.",
                follow_up_required=True,
                specialist_referral=None,
                agent_type="ai_risk_assessment_fallback",
                timestamp=datetime.now()
            )
            
            # Save fallback to database if requested
            if save_to_db:
                self._save_to_database(fallback_assessment, processing_time)
            
            return fallback_assessment

    def test_connection(self) -> bool:
        """Test connection to Gemini AI"""
        try:
            test_prompt = "Say hello"
            response = self.model.generate_content(test_prompt)
            return response.text and len(response.text) > 0
        except Exception as e:
            print(f"Gemini AI connection test failed: {str(e)}")
            return False

    def get_model_info(self) -> Dict[str, str]:
        """Get information about the AI model being used"""
        return {
            "agent_name": self.agent_name,
            "version": self.version,
            "model": self.model_name,
            "type": "AI-powered (Google Gemini)",
            "capabilities": "Medical risk assessment with natural language reasoning"
        }