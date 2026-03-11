"""
Clinical Models - To be implemented
"""

# TODO: Implement clinical data models
"""
Pydantic models for Clinical Agent
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ClinicalInput(BaseModel):
    case_id: str
    patient_code: str
    radiology_findings: str
    abnormalities: List[str] = []
    confidence: float = 0.0
    additional_info: Optional[str] = None

class ClinicalFindings(BaseModel):
    case_id: str
    patient_code: str
    differential_diagnosis: List[str]
    reasoning: str
    confidence: float
    urgency: str        # routine / urgent / emergency
    recommended_followup: str
    timestamp: datetime = None

    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.utcnow()
        super().__init__(**data)