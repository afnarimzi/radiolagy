"""
CRUD operations for simplified Radiology Agent database
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from app.database.models import Patient, PatientInput, PatientOutput, AgentThread, MedicalReport

class RadiologyDB:
    """Database operations for Radiology Agent"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Patient operations
    def create_patient(self, patient_code: str) -> Patient:
        """Create a new patient"""
        patient = Patient(patient_code=patient_code)
        self.db.add(patient)
        self.db.commit()
        self.db.refresh(patient)
        return patient
    
    def get_patient_by_code(self, patient_code: str) -> Optional[Patient]:
        """Get patient by patient code"""
        return self.db.query(Patient).filter(Patient.patient_code == patient_code).first()
    
    def get_or_create_patient(self, patient_code: str) -> Patient:
        """Get existing patient or create new one"""
        patient = self.get_patient_by_code(patient_code)
        if not patient:
            patient = self.create_patient(patient_code)
        return patient
    
    # Case input operations
    def create_case_input(self, case_id: str, patient_code: str, input_data: Dict[str, Any], 
                         image_path: str = None, additional_info: str = None) -> PatientInput:
        """Create a new case with input data"""
        patient = self.get_or_create_patient(patient_code)
        
        case_input = PatientInput(
            case_id=case_id,
            patient_id=patient.id,
            input_data=input_data,
            image_path=image_path,
            additional_info=additional_info
        )
        self.db.add(case_input)
        self.db.commit()
        self.db.refresh(case_input)
        return case_input
    
    def create_case_input_with_thread(self, case_id: str, patient_code: str, input_data: Dict[str, Any], 
                                    thread_id: str = None, image_path: str = None, additional_info: str = None) -> PatientInput:
        """Create a new case with input data and thread ID"""
        patient = self.get_or_create_patient(patient_code)
        
        case_input = PatientInput(
            case_id=case_id,
            patient_id=patient.id,
            input_data=input_data,
            thread_id=thread_id,
            image_path=image_path,
            additional_info=additional_info
        )
        self.db.add(case_input)
        self.db.commit()
        self.db.refresh(case_input)
        return case_input
    
    def get_case_input(self, case_id: str) -> Optional[PatientInput]:
        """Get case input by case ID"""
        return self.db.query(PatientInput).filter(PatientInput.case_id == case_id).first()
    
    # Case output operations
    def save_analysis_output(self, case_id: str, output_data: Dict[str, Any], 
                           confidence: float, processing_time: float = None, agent_type: str = 'radiology') -> PatientOutput:
        """Save radiology analysis output"""
        output = PatientOutput(
            case_id=case_id,
            agent_type='radiology',
            output_data=output_data,
            confidence=confidence,
            processing_time=processing_time
        )
        self.db.add(output)
        self.db.commit()
        self.db.refresh(output)
        return output

    def save_agent_output(self, case_id: str, agent_type: str, output_data: Dict[str, Any],
                      confidence: float, processing_time: float = None) -> PatientOutput:
        """Save any agent output - clinical, evidence, risk etc."""
        output = PatientOutput(
            case_id=case_id,
            agent_type=agent_type,
            output_data=output_data,
            confidence=confidence,
            processing_time=processing_time
        )
        self.db.add(output)
        self.db.commit()
        self.db.refresh(output)
        return output
    
    def get_case_output(self, case_id: str) -> Optional[PatientOutput]:
        """Get case output by case ID"""
        return self.db.query(PatientOutput).filter(PatientOutput.case_id == case_id).first()
    
    # Thread operations
    def create_agent_thread(self, case_id: str, thread_id: str = None) -> AgentThread:
        """Create a new agent thread"""
        if not thread_id:
            thread_id = f"thread_{uuid.uuid4().hex[:8]}"
        
        thread = AgentThread(
            case_id=case_id,
            thread_id=thread_id,
            agent_type='radiology',
            status='active'
        )
        self.db.add(thread)
        self.db.commit()
        self.db.refresh(thread)
        return thread
    
    def update_thread_status(self, thread_id: str, status: str) -> bool:
        """Update thread status"""
        thread = self.db.query(AgentThread).filter(AgentThread.thread_id == thread_id).first()
        if thread:
            thread.status = status
            thread.updated_at = datetime.utcnow()
            self.db.commit()
            return True
        return False
    
    def get_thread(self, thread_id: str) -> Optional[AgentThread]:
        """Get thread by thread ID"""
        return self.db.query(AgentThread).filter(AgentThread.thread_id == thread_id).first()

    def get_thread_history(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get all cases linked to this thread_id with agent outputs"""
        try:
            cases = self.db.query(PatientInput).filter(PatientInput.thread_id == thread_id).order_by(PatientInput.created_at).all()
            
            result = []
            for case in cases:
                outputs = self.db.query(PatientOutput).filter(PatientOutput.case_id == case.case_id).all()
                agents_run = [o.agent_type for o in outputs]
                
                result.append({
                    "case_id": case.case_id,
                    "thread_id": case.thread_id,
                    "date": case.created_at.isoformat(),
                    "agents_run": agents_run,
                    "results": {o.agent_type: o.output_data for o in outputs}
                })
            return result
        except Exception as e:
            print(f"Error fetching thread history: {e}")
            return []
    
    # Medical report operations
    def create_medical_report(self, case_id: str, report_content: str, 
                            findings_summary: str = None, recommendations: str = None) -> MedicalReport:
        """Create a medical report"""
        report = MedicalReport(
            case_id=case_id,
            report_type='radiology',
            report_content=report_content,
            findings_summary=findings_summary,
            recommendations=recommendations,
            generated_by='radiology_agent',
            report_status='draft'
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report
    
    def get_medical_report(self, case_id: str) -> Optional[MedicalReport]:
        """Get medical report by case ID"""
        return self.db.query(MedicalReport).filter(MedicalReport.case_id == case_id).first()
    
    def update_report_status(self, case_id: str, status: str) -> bool:
        """Update report status"""
        report = self.get_medical_report(case_id)
        if report:
            report.report_status = status
            report.updated_at = datetime.utcnow()
            self.db.commit()
            return True
        return False
    
    # Complete case operations
    def get_complete_case(self, case_id: str) -> Dict[str, Any]:
        """Get complete case information"""
        case_input = self.get_case_input(case_id)
        case_output = self.get_case_output(case_id)
        report = self.get_medical_report(case_id)
        
        if not case_input:
            return None
        
        patient = self.db.query(Patient).filter(Patient.id == case_input.patient_id).first()
        
        return {
            'case_id': case_id,
            'patient_code': patient.patient_code if patient else None,
            'input_data': case_input.input_data,
            'image_path': case_input.image_path,
            'additional_info': case_input.additional_info,
            'output_data': case_output.output_data if case_output else None,
            'confidence': case_output.confidence if case_output else None,
            'processing_time': case_output.processing_time if case_output else None,
            'report_content': report.report_content if report else None,
            'report_status': report.report_status if report else None,
            'created_at': case_input.created_at
        }
    
    def get_patient_cases(self, patient_code: str) -> List[Dict[str, Any]]:
        """Get all cases for a patient"""
        patient = self.get_patient_by_code(patient_code)
        if not patient:
            return []
        
        cases = self.db.query(PatientInput).filter(PatientInput.patient_id == patient.id).order_by(desc(PatientInput.created_at)).all()
        
        result = []
        for case in cases:
            complete_case = self.get_complete_case(case.case_id)
            if complete_case:
                result.append(complete_case)
        
        return result
    
    def get_recent_cases(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent cases"""
        recent_inputs = self.db.query(PatientInput).order_by(desc(PatientInput.created_at)).limit(limit).all()
        
        result = []
        for case_input in recent_inputs:
            complete_case = self.get_complete_case(case_input.case_id)
            if complete_case:
                result.append(complete_case)
        
        return result

    def get_patient_history_context(self, patient_code: str, limit: int = 3) -> str:
        """Fetch last N cases and format for LLM context"""
        try:
            patient = self.get_patient_by_code(patient_code)
            if not patient:
                return "No previous visits found."
            
            cases = self.db.query(PatientInput).filter(
                PatientInput.patient_id == patient.id
            ).order_by(desc(PatientInput.created_at)).limit(limit).all()
            
            if not cases:
                return "No previous visits found."
            
            history_parts = []
            # Reverse to show in chronological order (oldest to newest)
            for i, case in enumerate(reversed(cases)):
                # Get radiology and chairman outputs
                outputs = self.db.query(PatientOutput).filter(
                    PatientOutput.case_id == case.case_id,
                    PatientOutput.agent_type.in_(['radiology', 'chairman'])
                ).all()
                
                rad_out = next((o for o in outputs if o.agent_type == 'radiology'), None)
                chair_out = next((o for o in outputs if o.agent_type == 'chairman'), None)
                
                if not rad_out and not chair_out:
                    continue
                
                date_str = case.created_at.strftime("%Y-%m-%d")
                part = f"Visit {i+1} ({date_str}):\n"
                
                if rad_out:
                    abnormalities = rad_out.output_data.get('abnormalities', [])
                    part += f"- Abnormalities: {', '.join(abnormalities) if abnormalities else 'None'}\n"
                
                if chair_out:
                    diag = chair_out.output_data.get('primary_diagnosis', 'Unknown')
                    urgency = chair_out.output_data.get('urgency_level', 'Unknown')
                    summary = chair_out.output_data.get('executive_summary', '')[:300]
                    part += f"- Diagnosis: {diag}\n"
                    part += f"- Urgency: {urgency}\n"
                    part += f"- Summary: {summary}...\n"
                
                history_parts.append(part)
            
            return "\n".join(history_parts) if history_parts else "No previous visits found."
            
        except Exception as e:
            print(f"Error in get_patient_history_context: {e}")
            return "No previous visits found."


# Legacy CRUD classes for backward compatibility (simplified)
class RadiologyReportCRUD:
    """Legacy CRUD for radiology reports - maps to new structure"""
    
    @staticmethod
    def create_report(db: Session, findings, xray_input, processing_time: float = None):
        """Create report using new structure"""
        radiology_db = RadiologyDB(db)
        
        # Create case input
        input_data = {
            'findings': findings.findings,
            'abnormalities': findings.abnormalities,
            'anatomical_structures': findings.anatomical_structures,
            'image_quality': findings.image_quality
        }
        
        case_input = radiology_db.create_case_input(
            case_id=findings.case_id,
            patient_code=xray_input.patient_code or "UNKNOWN",
            input_data=input_data,
            image_path=xray_input.image_path,
            additional_info=xray_input.additional_info
        )
        
        # Create case output
        output_data = {
            'findings': findings.findings,
            'abnormalities': findings.abnormalities,
            'anatomical_structures': findings.anatomical_structures,
            'recommendations': findings.recommendations,
            'image_quality': findings.image_quality
        }
        
        case_output = radiology_db.save_analysis_output(
            case_id=findings.case_id,
            output_data=output_data,
            confidence=findings.confidence,
            processing_time=processing_time
        )
        
        return case_output
    
    @staticmethod
    def get_report_by_case_id(db: Session, case_id: str):
        """Get report by case ID"""
        radiology_db = RadiologyDB(db)
        return radiology_db.get_case_output(case_id)
    
    @staticmethod
    def get_recent_reports(db: Session, limit: int = 10):
        """Get recent reports"""
        radiology_db = RadiologyDB(db)
        return radiology_db.get_recent_cases(limit)

class PatientCRUD:
    """Legacy CRUD for patients"""
    
    @staticmethod
    def get_or_create_patient(db: Session, patient_code: str, **kwargs):
        """Get or create patient"""
        radiology_db = RadiologyDB(db)
        return radiology_db.get_or_create_patient(patient_code)