"""
Pydantic models for Risk Assessment Agent
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class RiskLevel(str, Enum):
    """Risk level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ActionType(str, Enum):
    """Recommended action types"""
    ROUTINE_FOLLOWUP = "routine_followup"
    SCHEDULE_APPOINTMENT = "schedule_appointment"
    URGENT_CONSULTATION = "urgent_consultation"
    EMERGENCY_DEPARTMENT = "emergency_department"
    IMMEDIATE_HOSPITALIZATION = "immediate_hospitalization"

class RiskInput(BaseModel):
    """Input for risk assessment"""
    case_id: str = Field(..., description="Case identifier")
    radiology_findings: str = Field(..., description="Radiology findings text")
    abnormalities: List[str] = Field(default=[], description="List of abnormalities")
    confidence: float = Field(..., description="Radiology confidence score")
    patient_age: Optional[int] = Field(None, description="Patient age")
    patient_symptoms: Optional[str] = Field(None, description="Patient symptoms")
    clinical_context: Optional[str] = Field(None, description="Additional clinical context")

class RiskAssessment(BaseModel):
    """Risk assessment output"""
    case_id: str = Field(..., description="Case identifier")
    risk_level: RiskLevel = Field(..., description="Overall risk level")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Risk score (0-1)")
    
    # Risk factors
    critical_findings: List[str] = Field(default=[], description="Critical findings identified")
    risk_factors: List[str] = Field(default=[], description="Risk factors contributing to assessment")
    
    # Recommendations
    recommended_action: ActionType = Field(..., description="Primary recommended action")
    urgency_timeline: str = Field(..., description="Timeline for action (e.g., 'within 1 hour')")
    next_steps: List[str] = Field(default=[], description="Specific next steps")
    
    # Additional info
    reasoning: str = Field(..., description="Explanation of risk assessment")
    follow_up_required: bool = Field(default=True, description="Whether follow-up is needed")
    specialist_referral: Optional[str] = Field(None, description="Specialist referral if needed")
    
    # Metadata
    agent_type: str = Field(default="risk_assessment", description="Agent type")
    timestamp: datetime = Field(default_factory=datetime.now, description="Assessment timestamp")

class RiskError(BaseModel):
    """Error model for risk assessment"""
    case_id: str
    error_type: str
    error_message: str
    timestamp: datetime = Field(default_factory=datetime.now)