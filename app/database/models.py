"""
Simplified Database models for Radiology Agent - Essential tables only
"""
from sqlalchemy import Column, String, Text, Float, DateTime, JSON, ForeignKey
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