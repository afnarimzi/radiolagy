"""
Pydantic models for Radiology Agent - Enhanced for Dual-Model System
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Union, Tuple
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
    thread_id: Optional[str] = None

class DualRadiologyInput(BaseModel):
    """Enhanced input model for dual-model X-ray analysis"""
    image_path: Optional[str] = Field(None, description="Path to X-ray image file")
    image_data: Optional[bytes] = Field(None, description="Raw image data")
    image_url: Optional[str] = Field(None, description="URL to X-ray image")
    patient_code: Optional[str] = Field(None, description="Patient identifier")
    case_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique case identifier")
    additional_info: Optional[str] = Field(None, description="Additional clinical information")
    thread_id: Optional[str] = None
    validation_config: Optional['ValidationConfig'] = Field(None, description="Validation configuration for dual-model analysis")

class ValidationConfig(BaseModel):
    """Configuration for dual-model validation"""
    confidence_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Minimum confidence threshold for both models")
    agreement_threshold: float = Field(0.8, ge=0.0, le=1.0, description="Minimum agreement threshold for consensus")
    quality_threshold: str = Field("adequate", description="Minimum image quality requirement")
    max_retries: int = Field(2, ge=0, le=5, description="Maximum number of retry attempts")
    require_consensus: bool = Field(True, description="Whether consensus is required for validation")
    enable_statistical_analysis: bool = Field(True, description="Enable advanced statistical consensus analysis")

class ModelOutput(BaseModel):
    """Output model for individual model analysis"""
    model_name: str = Field(..., description="Name of the AI model (gemini/groq)")
    findings: str = Field(..., description="Primary radiological findings")
    abnormalities: List[str] = Field(default=[], description="List of detected abnormalities")
    anatomical_structures: List[str] = Field(default=[], description="Anatomical structures analyzed")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    image_quality: str = Field(default="adequate", description="Image quality assessment")
    recommendations: str = Field(..., description="Clinical recommendations")
    processing_time: float = Field(..., ge=0.0, description="Processing time in seconds")
    timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
    raw_response: Optional[str] = Field(None, description="Raw model response for debugging")

class ConsensusMetrics(BaseModel):
    """Metrics for consensus analysis between models"""
    exact_match_percentage: float = Field(..., ge=0.0, le=100.0, description="Percentage of exact matches")
    semantic_similarity_score: float = Field(..., ge=0.0, le=1.0, description="Semantic similarity score")
    clinical_significance_alignment: float = Field(..., ge=0.0, le=1.0, description="Clinical significance alignment score")
    cohens_kappa: float = Field(..., ge=-1.0, le=1.0, description="Cohen's Kappa for inter-rater agreement")
    abnormality_overlap_ratio: float = Field(..., ge=0.0, le=1.0, description="Ratio of overlapping abnormalities")
    confidence_correlation: float = Field(..., ge=-1.0, le=1.0, description="Correlation between confidence scores")
    quality_agreement: bool = Field(..., description="Whether models agree on image quality")

class ValidationResult(BaseModel):
    """Result of validation analysis"""
    consensus_score: float = Field(..., ge=0.0, le=1.0, description="Overall consensus score")
    confidence_validation: bool = Field(..., description="Whether confidence thresholds are met")
    quality_validation: bool = Field(..., description="Whether quality requirements are met")
    abnormality_agreement: float = Field(..., ge=0.0, le=1.0, description="Agreement on abnormalities")
    critical_findings_match: bool = Field(..., description="Whether critical findings match")
    discrepancies: List[str] = Field(default=[], description="List of identified discrepancies")
    validation_status: str = Field(..., description="PASS, FAIL, or RETRY")
    validation_reasoning: str = Field(..., description="Detailed reasoning for validation decision")

class DualRadiologyFindings(BaseModel):
    """Comprehensive output model for dual-model radiology analysis"""
    case_id: str = Field(..., description="Unique case identifier")
    gemini_output: ModelOutput = Field(..., description="Gemini model analysis results")
    groq_output: ModelOutput = Field(..., description="Groq model analysis results")
    validation_result: ValidationResult = Field(..., description="Validation analysis results")
    consensus_metrics: ConsensusMetrics = Field(..., description="Statistical consensus metrics")
    final_decision: str = Field(..., description="Final decision: PASS or FAIL")
    decision_reasoning: str = Field(..., description="Detailed reasoning for final decision")
    retry_count: int = Field(0, ge=0, description="Number of retry attempts made")
    timestamp: datetime = Field(default_factory=datetime.now, description="Analysis completion timestamp")

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

# Update forward references
DualRadiologyInput.model_rebuild()