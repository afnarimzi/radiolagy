"""
Simplified Database models for Radiology Agent - Essential tables only
"""
from sqlalchemy import Column, String, Text, Float, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.database.database import Base
venv) afna-rimzi@afna-rimzi-BOHK-WAX9X:~/MindsMap/llmCouncil$ source venv/bin/activate && python3 view_reports.py
🏥 Radiology AI - Database Viewer
========================================
📊 Recent 3 Radiology Reports
================================================================================

--- Report 1 ---
🆔 Case ID: 514d126a-cc0e-4bac-a4e4-b50f99af7b40
👤 Patient: TEST_002
📅 Date: 2026-03-10 12:27:44
🖼️  Image: test_images/00000003_000.png
📊 Confidence: 0.80
⚠️  Abnormalities: 2 found
   - pleural effusion, mass/nodule
🔍 Findings: **RADIOLOGY REPORT**

**PATIENT NAME:** [Not provided]
**DOB:** [Not provided]
**EXAM DATE:** [Not provided]
**EXAM TYPE:** Chest X-ray, PA view
**CLINICAL INFORMATION:** Test analysis of 00000003_000...
💡 Recommendations: **RECOMMENDATIONS:**
📄 Report Status: draft
📝 Report: RADIOLOGY REPORT
                    
Case ID: 514d126a-cc0e-4bac-a4e4-b50f99af7b40
Patient: TEST_002
Date: 2026-03-10 17:57:44
Image Quality: good

F...
--------------------------------------------------------------------------------

--- Report 2 ---
🆔 Case ID: 781cfa8e-4f17-4e92-9986-f06813aa2e83
👤 Patient: TEST_001
📅 Date: 2026-03-10 12:27:31
🖼️  Image: test_images/00000003_007.png
📊 Confidence: 0.80
⚠️  Abnormalities: 2 found
   - acute fracture, mass/nodule
🔍 Findings: **RADIOLOGY REPORT**

**PATIENT NAME:** [Not provided]
**DOB:** [Not provided]
**EXAM DATE:** [Not provided]
**EXAM TYPE:** Chest X-ray, AP view
**CLINICAL INFORMATION:** Test analysis of 00000003_007...
💡 Recommendations: Clinical correlation recommended
📄 Report Status: draft
📝 Report: RADIOLOGY REPORT
                    
Case ID: 781cfa8e-4f17-4e92-9986-f06813aa2e83
Patient: TEST_001
Date: 2026-03-10 17:57:31
Image Quality: adequat...
--------------------------------------------------------------------------------

--- Report 3 ---
🆔 Case ID: TEST_CASE_001
👤 Patient: TEST_001
📅 Date: 2026-03-10 12:27:05
🖼️  Image: /test/path.jpg
📊 Confidence: 0.85
🔍 Findings: test findings
📄 Report Status: draft
📝 Report: Test radiology report content
----------------------------------------------------
class Patient(Base):
    """Patient ID storage - minimal patient information"""
    __tablename__ = "patients"
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_code = Column(String(50), unique=True, nullable=False, index=True)  # P001, P002, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

class PatientInput(Base):
    """Patient input storage - X-ray data and clinical info"""
    __tablename__ = "patient_inputs"
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(String(50), unique=True, nullable=False, index=True)  # CASE_001, CASE_002, etc.
    patient_id = Column(UUID(as_uuid=True), ForeignKey('patients.id'), nullable=False)
    
    # Input data
    input_data = Column(JSON, nullable=False)  # X-ray description, symptoms, image path, etc.
    image_path = Column(String(500))  # Path to X-ray image
    additional_info = Column(Text)  # Any additional clinical information
    
    created_at = Column(DateTime, default=datetime.utcnow)

class PatientOutput(Base):
    """Patient output storage - Radiology analysis results"""
    __tablename__ = "patient_outputs"
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(String(50), ForeignKey('patient_inputs.case_id'), nullable=False, index=True)
    agent_type = Column(String(50), default='radiology', nullable=False)
    
    # Output data
    output_data = Column(JSON, nullable=False)  # Findings, abnormalities, confidence, etc.
    confidence = Column(Float, nullable=False)  # Analysis confidence score
    processing_time = Column(Float)  # Time taken for analysis
    
    created_at = Column(DateTime, default=datetime.utcnow)

class AgentThread(Base):
    """Thread storage - Agent report tracking"""
    __tablename__ = "agent_threads"
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(String(50), nullable=False, index=True)
    thread_id = Column(String(50), nullable=False, index=True)  # Groups related agent activities
    agent_type = Column(String(50), default='radiology', nullable=False)
    status = Column(String(20), default='active')  # active, completed, failed
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MedicalReport(Base):
    """Medical report storage - Final radiology reports"""
    __tablename__ = "medical_reports"
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(String(50), nullable=False, index=True)
    report_type = Column(String(50), default='radiology', nullable=False)
    
    # Report content
    report_content = Column(Text, nullable=False)  # Formatted medical report
    findings_summary = Column(Text)  # Key findings summary
    recommendations = Column(Text)  # Clinical recommendations
    
    # Metadata
    generated_by = Column(String(50), default='radiology_agent')
    report_status = Column(String(20), default='draft')  # draft, final, reviewed
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)