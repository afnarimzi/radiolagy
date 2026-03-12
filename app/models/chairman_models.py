"""
Chairman Agent Models - Final Medical Report Synthesis
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ChairmanInput(BaseModel):
    """Input for Chairman Agent - All specialist reports"""
    case_id: str = Field(..., description="Unique case identifier")
    patient_code: str = Field(..., description="Patient identifier")
    
    # All specialist findings
    radiology_findings: Dict[str, Any] = Field(..., description="Complete radiology analysis")
    clinical_findings: Dict[str, Any] = Field(..., description="Complete clinical analysis")
    evidence_findings: Dict[str, Any] = Field(..., description="Complete evidence research")
    risk_findings: Dict[str, Any] = Field(..., description="Complete risk assessment")
    
    # Additional context
    patient_history: Optional[str] = Field(None, description="Patient medical history if available")
    additional_notes: Optional[str] = Field(None, description="Additional clinical notes")

class ChairmanOutput(BaseModel):
    """Output from Chairman Agent - Comprehensive Final Report"""
    case_id: str = Field(..., description="Case identifier")
    patient_code: str = Field(..., description="Patient identifier")
    
    # Executive Summary
    executive_summary: str = Field(..., description="High-level summary of all findings")
    primary_diagnosis: str = Field(..., description="Most likely primary diagnosis")
    differential_diagnoses: List[str] = Field(..., description="Alternative diagnoses ranked by likelihood")
    
    # Synthesis of Specialist Reports
    radiology_synthesis: str = Field(..., description="Key radiology findings synthesis")
    clinical_synthesis: str = Field(..., description="Clinical interpretation synthesis")
    evidence_synthesis: str = Field(..., description="Evidence-based medicine synthesis")
    risk_synthesis: str = Field(..., description="Risk assessment synthesis")
    
    # Final Recommendations
    immediate_actions: List[str] = Field(..., description="Immediate actions required")
    follow_up_plan: List[str] = Field(..., description="Follow-up care plan")
    specialist_referrals: List[str] = Field(..., description="Required specialist referrals")
    
    # Quality Metrics
    confidence_level: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in assessment")
    consensus_score: float = Field(..., ge=0.0, le=1.0, description="Agreement between specialist agents")
    urgency_level: str = Field(..., description="Overall urgency: critical, urgent, routine")
    
    # Report Metadata
    report_generated_at: datetime = Field(default_factory=datetime.utcnow)
    chairman_reasoning: str = Field(..., description="Chairman's clinical reasoning process")
    quality_flags: List[str] = Field(default=[], description="Quality concerns or flags")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }