"""
Evidence Models - To be implemented
"""

# TODO: Implement evidence-based research data models
"""
Pydantic models for Evidence Agent
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class EvidenceInput(BaseModel):
    case_id: str
    patient_code: str
    diagnosis: List[str]
    radiology_findings: str

class Citation(BaseModel):
    pmid: str
    title: str
    authors: List[str]
    journal: str
    year: str
    url: str

class EvidenceFindings(BaseModel):
    case_id: str
    patient_code: str
    search_keywords: str
    evidence_summary: str
    citations: List[Citation]
    total_papers_found: int
    timestamp: datetime = None

    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.utcnow()
        super().__init__(**data)