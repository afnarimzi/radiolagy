"""
Pydantic models for API requests and responses
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Request models
class PatientCreate(BaseModel):
    patient_code: str = Field(..., description="Patient identifier code")

class AnalysisRequest(BaseModel):
    image_path: str = Field(..., description="Path to X-ray image")
    patient_code: str = Field(..., description="Patient identifier")
    case_id: Optional[str] = Field(None, description="Case identifier (auto-generated if not provided)")
    additional_info: Optional[str] = Field(None, description="Additional clinical information")

# Response models
class PatientResponse(BaseModel):
    id: str
    patient_code: str
    created_at: datetime

class CaseResponse(BaseModel):
    case_id: str
    patient_code: str
    image_path: Optional[str]
    confidence: Optional[float]
    report_status: Optional[str]
    created_at: datetime

class AnalysisResponse(BaseModel):
    case_id: str
    patient_code: str
    findings: str
    abnormalities: List[str]
    anatomical_structures: List[str]
    confidence: float
    recommendations: str
    image_quality: str
    timestamp: datetime

class ReportResponse(BaseModel):
    case_id: str
    report_type: str
    report_content: str
    findings_summary: Optional[str]
    recommendations: Optional[str]
    generated_by: Optional[str]
    report_status: str
    created_at: datetime

# Risk Assessment models
class RiskAssessmentRequest(BaseModel):
    case_id: Optional[str] = Field(None, description="Case ID to assess (if None, uses radiology findings)")
    radiology_findings: Optional[str] = Field(None, description="Radiology findings text")
    patient_code: str = Field(..., description="Patient identifier")
    additional_clinical_info: Optional[str] = Field(None, description="Additional clinical context")

class RiskAssessmentResponse(BaseModel):
    case_id: str
    patient_code: str
    risk_level: str
    risk_score: float
    recommended_action: str
    urgency_timeline: str
    specialist_referral: Optional[str]
    critical_findings: List[str]
    risk_factors: List[str]
    next_steps: List[str]
    reasoning: str
    confidence: float
    timestamp: datetime

class DatabaseStats(BaseModel):
    total_patients: int
    total_cases: int
    total_radiology_results: int
    total_risk_assessments: int
    total_clinical_results: int
    total_reports: int
    average_confidence: float
    
# Clinical Agent models
class ClinicalRequest(BaseModel):
    case_id: str
    patient_code: str
    radiology_findings: str
    abnormalities: List[str] = []
    confidence: float = 0.0
    additional_info: Optional[str] = None

class ClinicalResponse(BaseModel):
    case_id: str
    patient_code: str
    differential_diagnosis: List[str]
    reasoning: str
    confidence: float
    urgency: str
    recommended_followup: str
    timestamp: datetime

# Evidence Agent models
class EvidenceRequest(BaseModel):
    case_id: str
    patient_code: str
    diagnosis: List[str]
    radiology_findings: str

class EvidenceResponse(BaseModel):
    case_id: str
    patient_code: str
    search_keywords: str
    evidence_summary: str
    citations: List[dict]
    total_papers_found: int
    timestamp: datetime