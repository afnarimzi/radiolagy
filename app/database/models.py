"""
Database models for Radiology Agent - Enhanced for Dual-Model System
"""
from sqlalchemy import Column, String, Text, Float, DateTime, JSON, ForeignKey, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.database.database import Base

class Patient(Base):
    """Patient information table"""
    __tablename__ = "patients"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_code = Column(String(50), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class PatientInput(Base):
    """Patient input data table - stores what we analyze"""
    __tablename__ = "patient_inputs"
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(String(50), unique=True, nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey('patients.id'), nullable=False)
    input_data = Column(JSON, nullable=False)
    image_path = Column(String(500))
    additional_info = Column(Text)
    thread_id = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class PatientOutput(Base):
    """Patient output data table - stores analysis results from all agents"""
    __tablename__ = "patient_outputs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(String(50), ForeignKey('patient_inputs.case_id'), nullable=False, index=True)
    agent_type = Column(String(50), default='radiology', nullable=False)
    output_data = Column(JSON, nullable=False)
    confidence = Column(Float, nullable=False)
    processing_time = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class AgentThread(Base):
    """Agent conversation thread table - tracks multi-agent interactions"""
    __tablename__ = "agent_threads"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(String(50), nullable=False, index=True)
    thread_id = Column(String(50), nullable=False, index=True)
    agent_type = Column(String(50), default='radiology', nullable=False)
    status = Column(String(20), default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MedicalReport(Base):
    """Medical report table - stores formatted reports"""
    __tablename__ = "medical_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(String(50), nullable=False, index=True)
    report_type = Column(String(50), default='radiology', nullable=False)
    report_content = Column(Text, nullable=False)
    findings_summary = Column(Text)
    recommendations = Column(Text)
    generated_by = Column(String(50), default='radiology_agent')
    report_status = Column(String(20), default='draft')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# New tables for dual-model system

class DualRadiologyAnalysis(Base):
    """Dual radiology analysis table - stores dual-model analysis results"""
    __tablename__ = "dual_radiology_analyses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(String(50), ForeignKey('patient_inputs.case_id'), nullable=False, index=True)
    gemini_output = Column(JSON, nullable=False, comment="Gemini model analysis output")
    groq_output = Column(JSON, nullable=False, comment="Groq model analysis output")
    validation_result = Column(JSON, nullable=False, comment="Validation analysis results")
    consensus_metrics = Column(JSON, nullable=False, comment="Statistical consensus metrics")
    final_decision = Column(String(10), nullable=False, index=True, comment="PASS or FAIL")
    decision_reasoning = Column(Text, comment="Detailed reasoning for final decision")
    retry_count = Column(Integer, default=0, comment="Number of retry attempts")
    processing_time_total = Column(Float, comment="Total processing time in seconds")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class ValidationMetrics(Base):
    """Validation metrics table - stores detailed consensus metrics"""
    __tablename__ = "validation_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(String(50), ForeignKey('patient_inputs.case_id'), nullable=False, index=True)
    consensus_score = Column(Float, nullable=False, index=True, comment="Overall consensus score")
    confidence_correlation = Column(Float, comment="Correlation between model confidence scores")
    semantic_similarity = Column(Float, comment="Semantic similarity between findings")
    cohens_kappa = Column(Float, comment="Cohen's Kappa inter-rater agreement")
    abnormality_overlap_ratio = Column(Float, comment="Ratio of overlapping abnormalities")
    quality_agreement = Column(Boolean, comment="Whether models agree on image quality")
    validation_timestamp = Column(DateTime, default=datetime.utcnow, index=True)

class ModelPerformanceLog(Base):
    """Model performance logs table - tracks individual model performance"""
    __tablename__ = "model_performance_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(String(50), ForeignKey('patient_inputs.case_id'), nullable=False, index=True)
    model_name = Column(String(50), nullable=False, index=True, comment="Model identifier (gemini/groq)")
    processing_time = Column(Float, nullable=False, comment="Processing time in seconds")
    confidence_score = Column(Float, nullable=False, comment="Model confidence score")
    success = Column(Boolean, nullable=False, index=True, comment="Whether analysis succeeded")
    error_message = Column(Text, comment="Error message if analysis failed")
    resource_usage = Column(JSON, comment="Resource usage metrics")
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)