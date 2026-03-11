"""
Pydantic models for Radiology Agent
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Union
from datetime import datetime
import uuid

class XrayInput(BaseModel):
    """Input model for X-ray analysis"""
    image_path: Optional[str] = Field(None, description="Path to X-ray image file")
    image_data: Optional[bytes] = Field(None, description="Raw image data")
    image_url: Optional[str] = Field(None, description="URL to X-ray image")
    patient_code: Optional[str] = Field(None, description="Patient identifier")
    case_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique case identifier")
    additional_info: Optional[str] = Field(None, description="Additional clinical information")

class RadiologyFindings(BaseModel):
    """Output model for radiology analysis"""
    case_id: str = Field(..., description="Unique case identifier")
    findings: str = Field(..., description="Primary radiological findings")
    abnormalities: List[str] = Field(default=[], description="List of detected abnormalities")
    anatomical_structures: List[str] = Field(default=[], description="Anatomical structures analyzed")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    recommendations: str = Field(..., description="Clinical recommendations")
    image_quality: str = Field(default="adequate", description="Image quality assessment")
    agent_type: str = Field(default="radiology", description="Agent type identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")

class RadiologyError(BaseModel):
    """Error model for radiology analysis"""
    case_id: str
    error_type: str
    error_message: str
    timestamp: datetime = Field(default_factory=datetime.now)