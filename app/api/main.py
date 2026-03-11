"""
FastAPI application for Radiology AI Multi-Agent System
"""
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
from datetime import datetime

from app.database.database import get_db
from app.database.crud import RadiologyDB
from app.agents.radiology_agent import RadiologyAgent
from app.agents.risk_agent import RiskAgent
from app.models.radiology_models import XrayInput, RadiologyFindings
from app.models.risk_models import RiskAssessmentInput, RiskAssessmentOutput
from app.api.models import (
    PatientCreate, PatientResponse, 
    CaseResponse, AnalysisRequest, AnalysisResponse,
    RiskAssessmentRequest, RiskAssessmentResponse,
    ReportResponse, DatabaseStats
)

# Initialize FastAPI app
app = FastAPI(
    title="Multi-Agent AI Medical Analysis API",
    description="API for Multi-Agent AI Medical Analysis System (Radiology + Risk Assessment)",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents
radiology_agent = RadiologyAgent()
risk_agent = RiskAgent(api_key=os.getenv("RISK_AGENT_API_KEY"))

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Multi-Agent AI Medical Analysis System API",
        "version": "1.0.0",
        "status": "active",
        "agents": ["radiology", "risk"]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected",
        "radiology_agent": "ready",
        "risk_agent": "ready"
    }

# Patient endpoints
@app.post("/patients", response_model=PatientResponse)
async def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    """Create a new patient"""
    radiology_db = RadiologyDB(db)
    
    # Check if patient already exists
    existing_patient = radiology_db.get_patient_by_code(patient.patient_code)
    if existing_patient:
        raise HTTPException(status_code=400, detail="Patient already exists")
    
    new_patient = radiology_db.create_patient(patient.patient_code)
    return PatientResponse(
        id=str(new_patient.id),
        patient_code=new_patient.patient_code,
        created_at=new_patient.created_at
    )

@app.get("/patients/{patient_code}", response_model=PatientResponse)
async def get_patient(patient_code: str, db: Session = Depends(get_db)):
    """Get patient by patient code"""
    radiology_db = RadiologyDB(db)
    patient = radiology_db.get_patient_by_code(patient_code)
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    return PatientResponse(
        id=str(patient.id),
        patient_code=patient.patient_code,
        created_at=patient.created_at
    )

@app.get("/patients/{patient_code}/cases", response_model=List[CaseResponse])
async def get_patient_cases(patient_code: str, db: Session = Depends(get_db)):
    """Get all cases for a patient"""
    radiology_db = RadiologyDB(db)
    cases = radiology_db.get_patient_cases(patient_code)
    
    return [
        CaseResponse(
            case_id=case['case_id'],
            patient_code=case['patient_code'],
            image_path=case['image_path'],
            confidence=case['confidence'],
            report_status=case['report_status'],
            created_at=case['created_at']
        )
        for case in cases
    ]

# Analysis endpoints
@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_xray(request: AnalysisRequest, db: Session = Depends(get_db)):
    """Analyze X-ray image"""
    try:
        # Create XrayInput
        xray_input = XrayInput(
            image_path=request.image_path,
            patient_code=request.patient_code,
            case_id=request.case_id or str(uuid.uuid4()),
            additional_info=request.additional_info
        )
        
        # Analyze with radiology agent
        findings = radiology_agent.analyze(xray_input, save_to_db=True)
        
        return AnalysisResponse(
            case_id=findings.case_id,
            patient_code=request.patient_code,
            findings=findings.findings,
            abnormalities=findings.abnormalities,
            anatomical_structures=findings.anatomical_structures,
            confidence=findings.confidence,
            recommendations=findings.recommendations,
            image_quality=findings.image_quality,
            timestamp=findings.timestamp
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/upload-analyze")
async def upload_and_analyze(
    file: UploadFile = File(...),
    patient_code: str = "UNKNOWN",
    additional_info: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Upload X-ray image and analyze"""
    try:
        # Save uploaded file
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, f"{uuid.uuid4()}_{file.filename}")
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Analyze the uploaded image
        result = radiology_agent.analyze_image_file(
            image_path=file_path,
            patient_code=patient_code,
            additional_info=additional_info,
            save_to_db=True
        )
        
        return {
            "message": "Image uploaded and analyzed successfully",
            "file_path": file_path,
            "analysis": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload and analysis failed: {str(e)}")

# Risk Assessment endpoints
@app.post("/assess-risk", response_model=RiskAssessmentResponse)
async def assess_risk(request: RiskAssessmentRequest, db: Session = Depends(get_db)):
    """Assess medical risk based on radiology findings"""
    try:
        # If case_id provided, get radiology findings from database
        if request.case_id:
            from app.database.models import PatientOutput
            radiology_output = db.query(PatientOutput).filter(
                PatientOutput.case_id == request.case_id,
                PatientOutput.agent_type == 'radiology'
            ).first()
            
            if not radiology_output:
                raise HTTPException(status_code=404, detail="Radiology findings not found for this case")
            
            radiology_findings = radiology_output.output_data.get('findings', '')
        else:
            if not request.radiology_findings:
                raise HTTPException(status_code=400, detail="Either case_id or radiology_findings must be provided")
            radiology_findings = request.radiology_findings
        
        # Create risk assessment input
        risk_input = RiskAssessmentInput(
            case_id=request.case_id or str(uuid.uuid4()),
            patient_code=request.patient_code,
            radiology_findings=radiology_findings,
            additional_clinical_info=request.additional_clinical_info
        )
        
        # Assess risk with risk agent
        risk_assessment = risk_agent.assess_risk(risk_input, save_to_db=True)
        
        return RiskAssessmentResponse(
            case_id=risk_assessment.case_id,
            patient_code=request.patient_code,
            risk_level=risk_assessment.risk_level,
            risk_score=risk_assessment.risk_score,
            recommended_action=risk_assessment.recommended_action,
            urgency_timeline=risk_assessment.urgency_timeline,
            specialist_referral=risk_assessment.specialist_referral,
            critical_findings=risk_assessment.critical_findings,
            risk_factors=risk_assessment.risk_factors,
            next_steps=risk_assessment.next_steps,
            reasoning=risk_assessment.reasoning,
            confidence=risk_assessment.confidence,
            timestamp=risk_assessment.timestamp
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk assessment failed: {str(e)}")

@app.post("/analyze-and-assess", response_model=dict)
async def analyze_and_assess_risk(request: AnalysisRequest, db: Session = Depends(get_db)):
    """Complete pipeline: Analyze X-ray and assess risk"""
    try:
        # Step 1: Radiology analysis
        xray_input = XrayInput(
            image_path=request.image_path,
            patient_code=request.patient_code,
            case_id=request.case_id or str(uuid.uuid4()),
            additional_info=request.additional_info
        )
        
        radiology_findings = radiology_agent.analyze(xray_input, save_to_db=True)
        
        # Step 2: Risk assessment
        risk_input = RiskAssessmentInput(
            case_id=radiology_findings.case_id,
            patient_code=request.patient_code,
            radiology_findings=radiology_findings.findings,
            additional_clinical_info=request.additional_info
        )
        
        risk_assessment = risk_agent.assess_risk(risk_input, save_to_db=True)
        
        return {
            "case_id": radiology_findings.case_id,
            "patient_code": request.patient_code,
            "radiology_analysis": {
                "findings": radiology_findings.findings,
                "abnormalities": radiology_findings.abnormalities,
                "confidence": radiology_findings.confidence,
                "recommendations": radiology_findings.recommendations
            },
            "risk_assessment": {
                "risk_level": risk_assessment.risk_level,
                "risk_score": risk_assessment.risk_score,
                "recommended_action": risk_assessment.recommended_action,
                "urgency_timeline": risk_assessment.urgency_timeline,
                "specialist_referral": risk_assessment.specialist_referral,
                "critical_findings": risk_assessment.critical_findings,
                "next_steps": risk_assessment.next_steps,
                "confidence": risk_assessment.confidence
            },
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Complete analysis failed: {str(e)}")

@app.get("/risk-assessments/{case_id}")
async def get_risk_assessment(case_id: str, db: Session = Depends(get_db)):
    """Get risk assessment results for a case"""
    from app.database.models import PatientOutput
    
    risk_output = db.query(PatientOutput).filter(
        PatientOutput.case_id == case_id,
        PatientOutput.agent_type == 'risk'
    ).first()
    
    if not risk_output:
        raise HTTPException(status_code=404, detail="Risk assessment not found")
    
    return {
        "case_id": risk_output.case_id,
        "agent_type": risk_output.agent_type,
        "output_data": risk_output.output_data,
        "confidence": risk_output.confidence,
        "processing_time": risk_output.processing_time,
        "created_at": risk_output.created_at
    }

@app.get("/pending-risk-cases")
async def get_pending_risk_cases(limit: int = 10, db: Session = Depends(get_db)):
    """Get cases that have radiology results but need risk assessment"""
    from app.database.models import PatientOutput
    
    # Get cases with radiology results but no risk assessment
    radiology_cases = db.query(PatientOutput.case_id).filter(
        PatientOutput.agent_type == 'radiology'
    ).all()
    
    risk_cases = db.query(PatientOutput.case_id).filter(
        PatientOutput.agent_type == 'risk'
    ).all()
    
    radiology_case_ids = {case.case_id for case in radiology_cases}
    risk_case_ids = {case.case_id for case in risk_cases}
    
    pending_case_ids = radiology_case_ids - risk_case_ids
    
    radiology_db = RadiologyDB(db)
    pending_cases = []
    
    for case_id in list(pending_case_ids)[:limit]:
        case = radiology_db.get_complete_case(case_id)
        if case:
            pending_cases.append(case)
    
    return {
        "pending_cases": pending_cases,
        "total_pending": len(pending_case_ids)
    }

# Case endpoints
@app.get("/cases/{case_id}", response_model=dict)
async def get_case(case_id: str, db: Session = Depends(get_db)):
    """Get complete case information"""
    radiology_db = RadiologyDB(db)
    case = radiology_db.get_complete_case(case_id)
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    return case

@app.get("/cases", response_model=List[dict])
async def get_recent_cases(limit: int = 10, db: Session = Depends(get_db)):
    """Get recent cases"""
    radiology_db = RadiologyDB(db)
    cases = radiology_db.get_recent_cases(limit=limit)
    return cases

# Report endpoints
@app.get("/reports/{case_id}", response_model=ReportResponse)
async def get_report(case_id: str, db: Session = Depends(get_db)):
    """Get medical report for a case"""
    radiology_db = RadiologyDB(db)
    report = radiology_db.get_medical_report(case_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return ReportResponse(
        case_id=report.case_id,
        report_type=report.report_type,
        report_content=report.report_content,
        findings_summary=report.findings_summary,
        recommendations=report.recommendations,
        generated_by=report.generated_by,
        report_status=report.report_status,
        created_at=report.created_at
    )

@app.get("/reports", response_model=List[ReportResponse])
async def get_recent_reports(limit: int = 10, db: Session = Depends(get_db)):
    """Get recent medical reports"""
    radiology_db = RadiologyDB(db)
    cases = radiology_db.get_recent_cases(limit=limit)
    
    reports = []
    for case in cases:
        if case['report_content']:
            reports.append(ReportResponse(
                case_id=case['case_id'],
                report_type='radiology',
                report_content=case['report_content'],
                findings_summary=case.get('findings_summary'),
                recommendations=case.get('recommendations'),
                generated_by='radiology_agent',
                report_status=case['report_status'],
                created_at=case['created_at']
            ))
    
    return reports

# Agent-specific endpoints for clinical agent integration
@app.get("/radiology-results/{case_id}")
async def get_radiology_results(case_id: str, db: Session = Depends(get_db)):
    """Get radiology analysis results for clinical agent"""
    radiology_db = RadiologyDB(db)
    
    case_output = radiology_db.get_case_output(case_id)
    if not case_output:
        raise HTTPException(status_code=404, detail="Radiology results not found")
    
    return {
        "case_id": case_output.case_id,
        "agent_type": case_output.agent_type,
        "output_data": case_output.output_data,
        "confidence": case_output.confidence,
        "processing_time": case_output.processing_time,
        "created_at": case_output.created_at
    }

@app.get("/pending-clinical-cases")
async def get_pending_clinical_cases(limit: int = 10, db: Session = Depends(get_db)):
    """Get cases that have radiology results but need clinical analysis"""
    from app.database.models import PatientOutput
    
    # Get cases with radiology results but no clinical results
    radiology_cases = db.query(PatientOutput.case_id).filter(
        PatientOutput.agent_type == 'radiology'
    ).all()
    
    clinical_cases = db.query(PatientOutput.case_id).filter(
        PatientOutput.agent_type == 'clinical'
    ).all()
    
    radiology_case_ids = {case.case_id for case in radiology_cases}
    clinical_case_ids = {case.case_id for case in clinical_cases}
    
    pending_case_ids = radiology_case_ids - clinical_case_ids
    
    radiology_db = RadiologyDB(db)
    pending_cases = []
    
    for case_id in list(pending_case_ids)[:limit]:
        case = radiology_db.get_complete_case(case_id)
        if case:
            pending_cases.append(case)
    
    return {
        "pending_cases": pending_cases,
        "total_pending": len(pending_case_ids)
    }

# Statistics endpoint
@app.get("/stats", response_model=DatabaseStats)
async def get_database_stats(db: Session = Depends(get_db)):
    """Get database statistics"""
    from app.database.models import Patient, PatientInput, PatientOutput, MedicalReport
    
    total_patients = db.query(Patient).count()
    total_cases = db.query(PatientInput).count()
    total_radiology_results = db.query(PatientOutput).filter(
        PatientOutput.agent_type == 'radiology'
    ).count()
    total_risk_assessments = db.query(PatientOutput).filter(
        PatientOutput.agent_type == 'risk'
    ).count()
    total_clinical_results = db.query(PatientOutput).filter(
        PatientOutput.agent_type == 'clinical'
    ).count()
    total_reports = db.query(MedicalReport).count()
    
    # Calculate average confidence
    outputs = db.query(PatientOutput).all()
    avg_confidence = sum(o.confidence for o in outputs) / len(outputs) if outputs else 0
    
    return DatabaseStats(
        total_patients=total_patients,
        total_cases=total_cases,
        total_radiology_results=total_radiology_results,
        total_risk_assessments=total_risk_assessments,
        total_clinical_results=total_clinical_results,
        total_reports=total_reports,
        average_confidence=round(avg_confidence, 2)
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)