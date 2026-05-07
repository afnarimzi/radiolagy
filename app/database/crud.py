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
        """Get complete case information with all multi-agent outputs"""
        case_input = self.get_case_input(case_id)
        if not case_input:
            return None
            
        # Get all agent outputs for this case
        outputs = self.db.query(PatientOutput).filter(PatientOutput.case_id == case_id).all()
        
        # Aggregate outputs by agent type
        agent_outputs = {output.agent_type: output.output_data for output in outputs}
        
        # Get medical report
        report = self.get_medical_report(case_id)
        
        patient = self.db.query(Patient).filter(Patient.id == case_input.patient_id).first()
        
        # Map to the structure expected by the frontend
        # The frontend expects radiology_analysis, clinical_analysis, evidence_research, etc.
        return {
            'case_id': case_id,
            'patient_code': patient.patient_code if patient else None,
            'input_data': case_input.input_data,
            'image_path': case_input.image_path,
            'additional_info': case_input.additional_info,
            'patient_history': case_input.input_data.get('patient_history', ''),
            
            # Formatted agent results
            'radiology_analysis': agent_outputs.get('radiology'),
            'clinical_analysis': agent_outputs.get('clinical'),
            'evidence_research': agent_outputs.get('evidence'),
            'risk_assessment': agent_outputs.get('risk'),
            'chairman_report': agent_outputs.get('chairman'),
            
            # Legacy/Overall fields
            'confidence': agent_outputs.get('chairman', {}).get('confidence') or agent_outputs.get('radiology', {}).get('confidence'),
            'processing_time': sum(o.processing_time for o in outputs if o.processing_time) if outputs else None,
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


class DualRadiologyDB:
    """
    CRUD operations for dual-model radiology analysis data.

    Extends the existing RadiologyDB with methods for saving and retrieving
    dual-model analyses, validation metrics, and model performance logs.
    Provides full audit trail support for regulatory compliance.

    Requirements: 5.4 (performance dashboards), 7.4 (audit trails), 6.3 (schema extension)
    """

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # dual_radiology_analyses
    # ------------------------------------------------------------------

    def save_dual_analysis(
        self,
        findings,  # DualRadiologyFindings
        processing_time_total: float = None,
    ):
        """
        Persist a completed DualRadiologyFindings to dual_radiology_analyses.

        Stores the full gemini_output, groq_output, validation_result, and
        consensus_metrics as JSONB so every decision factor is preserved for
        audit purposes (Requirement 7.4).

        Args:
            findings: DualRadiologyFindings instance from DualRadiologyAgent.
            processing_time_total: Optional total wall-clock time for the run.

        Returns:
            The created DualRadiologyAnalysis ORM object.
        """
        from app.database.models import DualRadiologyAnalysis
        import json

        def _json_safe(obj):
            """Recursively convert non-JSON-serializable types (e.g. datetime) to strings."""
            if isinstance(obj, dict):
                return {k: _json_safe(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_json_safe(v) for v in obj]
            if hasattr(obj, "isoformat"):  # datetime / date
                return obj.isoformat()
            if hasattr(obj, "__float__"):  # numpy floats etc.
                return float(obj)
            return obj

        record = DualRadiologyAnalysis(
            case_id=findings.case_id,
            gemini_output=_json_safe(findings.gemini_output.model_dump()),
            groq_output=_json_safe(findings.groq_output.model_dump()),
            validation_result=_json_safe(findings.validation_result.model_dump()),
            consensus_metrics=_json_safe(findings.consensus_metrics.model_dump()),
            final_decision=findings.final_decision,
            decision_reasoning=findings.decision_reasoning,
            retry_count=findings.retry_count,
            processing_time_total=processing_time_total,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_dual_analysis(self, case_id: str):
        """
        Retrieve the most recent dual-model analysis record for a given case_id.

        Args:
            case_id: Unique case identifier.

        Returns:
            DualRadiologyAnalysis ORM object or None.
        """
        from app.database.models import DualRadiologyAnalysis

        return (
            self.db.query(DualRadiologyAnalysis)
            .filter(DualRadiologyAnalysis.case_id == case_id)
            .order_by(desc(DualRadiologyAnalysis.created_at))
            .first()
        )

    def get_all_dual_analyses_for_case(self, case_id: str) -> List:
        """
        Retrieve all dual-model analysis records for a case (including retries).

        Useful for audit trails where every attempt must be traceable
        (Requirement 7.4).

        Args:
            case_id: Unique case identifier.

        Returns:
            List of DualRadiologyAnalysis ORM objects ordered oldest-first.
        """
        from app.database.models import DualRadiologyAnalysis

        return (
            self.db.query(DualRadiologyAnalysis)
            .filter(DualRadiologyAnalysis.case_id == case_id)
            .order_by(DualRadiologyAnalysis.created_at)
            .all()
        )

    def get_recent_dual_analyses(self, limit: int = 20) -> List:
        """
        Retrieve the most recent dual-model analysis records across all cases.

        Used for performance dashboard data (Requirement 5.4).

        Args:
            limit: Maximum number of records to return.

        Returns:
            List of DualRadiologyAnalysis ORM objects ordered newest-first.
        """
        from app.database.models import DualRadiologyAnalysis

        return (
            self.db.query(DualRadiologyAnalysis)
            .order_by(desc(DualRadiologyAnalysis.created_at))
            .limit(limit)
            .all()
        )

    # ------------------------------------------------------------------
    # validation_metrics
    # ------------------------------------------------------------------

    def save_validation_metrics(self, case_id: str, consensus_metrics, validation_result):
        """
        Persist consensus and validation metrics to validation_metrics table.

        Args:
            case_id:           Unique case identifier.
            consensus_metrics: ConsensusMetrics from ValidatorAgent.
            validation_result: ValidationResult from ValidatorAgent.

        Returns:
            The created ValidationMetrics ORM object.
        """
        from app.database.models import ValidationMetrics

        record = ValidationMetrics(
            case_id=case_id,
            consensus_score=validation_result.consensus_score,
            confidence_correlation=consensus_metrics.confidence_correlation,
            semantic_similarity=consensus_metrics.semantic_similarity_score,
            cohens_kappa=consensus_metrics.cohens_kappa,
            abnormality_overlap_ratio=consensus_metrics.abnormality_overlap_ratio,
            quality_agreement=consensus_metrics.quality_agreement,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_validation_metrics(self, case_id: str):
        """
        Retrieve the most recent validation metrics record for a case.

        Args:
            case_id: Unique case identifier.

        Returns:
            ValidationMetrics ORM object or None.
        """
        from app.database.models import ValidationMetrics

        return (
            self.db.query(ValidationMetrics)
            .filter(ValidationMetrics.case_id == case_id)
            .order_by(desc(ValidationMetrics.validation_timestamp))
            .first()
        )

    def get_all_validation_metrics_for_case(self, case_id: str) -> List:
        """
        Retrieve all validation metrics records for a case (including retries).

        Args:
            case_id: Unique case identifier.

        Returns:
            List of ValidationMetrics ORM objects ordered oldest-first.
        """
        from app.database.models import ValidationMetrics

        return (
            self.db.query(ValidationMetrics)
            .filter(ValidationMetrics.case_id == case_id)
            .order_by(ValidationMetrics.validation_timestamp)
            .all()
        )

    # ------------------------------------------------------------------
    # model_performance_logs
    # ------------------------------------------------------------------

    def log_model_performance(
        self,
        case_id: str,
        model_output,
        success: bool = None,
        error_message: str = None,
        resource_usage: Dict[str, Any] = None,
    ):
        """
        Persist per-model performance data to model_performance_logs.

        The ``success`` flag is determined by whether the model produced a
        non-empty findings string and a positive confidence score.  Callers
        may override this by passing ``success`` explicitly (e.g. when a
        model raised an exception and a fallback output was synthesised).

        Args:
            case_id:        Unique case identifier.
            model_output:   ModelOutput from Gemini or Groq.
            success:        Explicit success flag; inferred from output if None.
            error_message:  Optional error detail to store alongside the log.
            resource_usage: Optional dict of resource metrics (tokens, memory…).

        Returns:
            The created ModelPerformanceLog ORM object.
        """
        from app.database.models import ModelPerformanceLog

        # Infer success from output quality when not explicitly provided
        if success is None:
            success = (
                model_output.confidence > 0.0
                and bool(model_output.findings)
                and model_output.findings.lower() not in ("", "error", "failed")
            )

        record = ModelPerformanceLog(
            case_id=case_id,
            model_name=model_output.model_name,
            processing_time=model_output.processing_time,
            confidence_score=model_output.confidence,
            success=success,
            error_message=error_message,
            resource_usage=resource_usage,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_model_performance_logs(self, case_id: str) -> List:
        """
        Retrieve all model performance log entries for a case.

        Args:
            case_id: Unique case identifier.

        Returns:
            List of ModelPerformanceLog ORM objects ordered by timestamp.
        """
        from app.database.models import ModelPerformanceLog

        return (
            self.db.query(ModelPerformanceLog)
            .filter(ModelPerformanceLog.case_id == case_id)
            .order_by(ModelPerformanceLog.timestamp)
            .all()
        )

    def get_model_performance_logs_by_model(self, model_name: str, limit: int = 100) -> List:
        """
        Retrieve recent performance logs for a specific model.

        Useful for per-model reliability tracking on the performance dashboard
        (Requirement 5.4).

        Args:
            model_name: Model identifier, e.g. "gemini" or "groq".
            limit:      Maximum number of records to return.

        Returns:
            List of ModelPerformanceLog ORM objects ordered newest-first.
        """
        from app.database.models import ModelPerformanceLog

        return (
            self.db.query(ModelPerformanceLog)
            .filter(ModelPerformanceLog.model_name == model_name)
            .order_by(desc(ModelPerformanceLog.timestamp))
            .limit(limit)
            .all()
        )

    # ------------------------------------------------------------------
    # Audit trail (Requirement 7.4)
    # ------------------------------------------------------------------

    def get_audit_trail(self, case_id: str) -> Dict[str, Any]:
        """
        Build a complete, chronologically ordered audit trail for a case.

        Satisfies Requirement 7.4: "maintain audit trails of all validation
        decisions for regulatory compliance."

        The returned dict contains every decision factor, threshold comparison,
        retry attempt, and model performance entry so that a compliance officer
        can reconstruct exactly what happened and why.

        Args:
            case_id: Unique case identifier.

        Returns:
            Dict with keys:
              - case_id
              - analyses:          list of all DualRadiologyAnalysis records (as dicts)
              - validation_metrics: list of all ValidationMetrics records (as dicts)
              - model_performance:  list of all ModelPerformanceLog records (as dicts)
              - summary:            high-level summary of the final outcome
        """
        analyses = self.get_all_dual_analyses_for_case(case_id)
        metrics = self.get_all_validation_metrics_for_case(case_id)
        perf_logs = self.get_model_performance_logs(case_id)

        def _analysis_to_dict(a) -> Dict[str, Any]:
            return {
                "id": str(a.id),
                "case_id": a.case_id,
                "final_decision": a.final_decision,
                "decision_reasoning": a.decision_reasoning,
                "retry_count": a.retry_count,
                "processing_time_total": a.processing_time_total,
                "gemini_output": a.gemini_output,
                "groq_output": a.groq_output,
                "validation_result": a.validation_result,
                "consensus_metrics": a.consensus_metrics,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }

        def _metrics_to_dict(m) -> Dict[str, Any]:
            return {
                "id": str(m.id),
                "case_id": m.case_id,
                "consensus_score": m.consensus_score,
                "confidence_correlation": m.confidence_correlation,
                "semantic_similarity": m.semantic_similarity,
                "cohens_kappa": m.cohens_kappa,
                "abnormality_overlap_ratio": m.abnormality_overlap_ratio,
                "quality_agreement": m.quality_agreement,
                "validation_timestamp": m.validation_timestamp.isoformat() if m.validation_timestamp else None,
            }

        def _perf_to_dict(p) -> Dict[str, Any]:
            return {
                "id": str(p.id),
                "case_id": p.case_id,
                "model_name": p.model_name,
                "processing_time": p.processing_time,
                "confidence_score": p.confidence_score,
                "success": p.success,
                "error_message": p.error_message,
                "resource_usage": p.resource_usage,
                "timestamp": p.timestamp.isoformat() if p.timestamp else None,
            }

        # Determine final outcome from the most recent analysis
        final_analysis = analyses[-1] if analyses else None
        summary = {
            "total_attempts": len(analyses),
            "final_decision": final_analysis.final_decision if final_analysis else None,
            "final_decision_reasoning": final_analysis.decision_reasoning if final_analysis else None,
            "retry_count": final_analysis.retry_count if final_analysis else 0,
            "models_logged": list({p.model_name for p in perf_logs}),
            "all_decisions": [a.final_decision for a in analyses],
        }

        return {
            "case_id": case_id,
            "analyses": [_analysis_to_dict(a) for a in analyses],
            "validation_metrics": [_metrics_to_dict(m) for m in metrics],
            "model_performance": [_perf_to_dict(p) for p in perf_logs],
            "summary": summary,
        }

    # ------------------------------------------------------------------
    # Performance dashboard data (Requirement 5.4)
    # ------------------------------------------------------------------

    def get_performance_dashboard_data(self, limit: int = 100) -> Dict[str, Any]:
        """
        Aggregate statistics for the performance dashboard.

        Satisfies Requirement 5.4: "maintain performance dashboards showing
        consensus rates, model reliability, and system throughput."

        Args:
            limit: Number of recent analyses to include in the aggregation.

        Returns:
            Dict with keys:
              - total_cases_analysed
              - pass_rate:            fraction of cases that received PASS
              - fail_rate:            fraction of cases that received FAIL
              - avg_consensus_score
              - avg_processing_time_total
              - model_reliability:    per-model success rate dict
              - avg_confidence_by_model: per-model average confidence dict
              - recent_decisions:     list of (case_id, decision, created_at) tuples
        """
        from app.database.models import DualRadiologyAnalysis, ModelPerformanceLog
        from sqlalchemy import func

        recent = (
            self.db.query(DualRadiologyAnalysis)
            .order_by(desc(DualRadiologyAnalysis.created_at))
            .limit(limit)
            .all()
        )

        total = len(recent)
        if total == 0:
            return {
                "total_cases_analysed": 0,
                "pass_rate": 0.0,
                "fail_rate": 0.0,
                "avg_consensus_score": None,
                "avg_processing_time_total": None,
                "model_reliability": {},
                "avg_confidence_by_model": {},
                "recent_decisions": [],
            }

        pass_count = sum(1 for a in recent if a.final_decision == "PASS")
        fail_count = total - pass_count

        # Average processing time (exclude None values)
        times = [a.processing_time_total for a in recent if a.processing_time_total is not None]
        avg_time = sum(times) / len(times) if times else None

        # Average consensus score from validation_result JSONB
        consensus_scores = []
        for a in recent:
            vr = a.validation_result or {}
            score = vr.get("consensus_score")
            if score is not None:
                consensus_scores.append(float(score))
        avg_consensus = sum(consensus_scores) / len(consensus_scores) if consensus_scores else None

        # Per-model reliability and average confidence from performance logs
        perf_rows = (
            self.db.query(ModelPerformanceLog)
            .order_by(desc(ModelPerformanceLog.timestamp))
            .limit(limit * 2)  # two models per case
            .all()
        )

        model_stats: Dict[str, Dict[str, Any]] = {}
        for row in perf_rows:
            name = row.model_name
            if name not in model_stats:
                model_stats[name] = {"total": 0, "success": 0, "confidence_sum": 0.0}
            model_stats[name]["total"] += 1
            if row.success:
                model_stats[name]["success"] += 1
            model_stats[name]["confidence_sum"] += row.confidence_score

        model_reliability = {
            name: (
                round(stats["success"] / stats["total"], 4)
                if stats["total"] > 0 else 0.0
            )
            for name, stats in model_stats.items()
        }
        avg_confidence_by_model = {
            name: (
                round(stats["confidence_sum"] / stats["total"], 4)
                if stats["total"] > 0 else 0.0
            )
            for name, stats in model_stats.items()
        }

        recent_decisions = [
            {
                "case_id": a.case_id,
                "decision": a.final_decision,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in recent[:10]
        ]

        return {
            "total_cases_analysed": total,
            "pass_rate": round(pass_count / total, 4),
            "fail_rate": round(fail_count / total, 4),
            "avg_consensus_score": round(avg_consensus, 4) if avg_consensus is not None else None,
            "avg_processing_time_total": round(avg_time, 4) if avg_time is not None else None,
            "model_reliability": model_reliability,
            "avg_confidence_by_model": avg_confidence_by_model,
            "recent_decisions": recent_decisions,
        }

    # ------------------------------------------------------------------
    # Convenience: persist everything from one DualRadiologyFindings
    # ------------------------------------------------------------------

    def save_findings_to_db(self, findings, processing_time_total: float = None):
        """
        Persist all dual-model data from a single DualRadiologyFindings object.

        Saves the analysis record, validation metrics, and per-model performance
        logs in a single call.  This is the primary entry point used by the
        LangGraph pipeline node.

        Args:
            findings:              Completed DualRadiologyFindings.
            processing_time_total: Optional total wall-clock time.
        """
        self.save_dual_analysis(findings, processing_time_total)
        self.save_validation_metrics(
            case_id=findings.case_id,
            consensus_metrics=findings.consensus_metrics,
            validation_result=findings.validation_result,
        )
        self.log_model_performance(findings.case_id, findings.gemini_output)
        self.log_model_performance(findings.case_id, findings.groq_output)
