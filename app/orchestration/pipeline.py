"""
LangGraph Medical AI Pipeline
Orchestrates all 5 agents: Radiology → Clinical + Evidence + Risk → Chairman
"""
import asyncio
import time
import uuid
from typing import Dict, List, Optional, TypedDict, Annotated
import operator

from langgraph.graph import StateGraph, END
from app.agents.radiology_agent import RadiologyAgent
from app.agents.clinical_agent import ClinicalAgent
from app.agents.evidence_agent import EvidenceAgent
from app.agents.risk_agent import RiskAssessmentAgent
from app.agents.chairman_agent import ChairmanAgent
from app.models.radiology_models import XrayInput
from app.models.clinical_models import ClinicalInput
from app.models.evidence_models import EvidenceInput
from app.models.risk_models import RiskInput
from app.models.chairman_models import ChairmanInput


class MedicalPipelineState(TypedDict):
    """State shared between all agents in the medical pipeline"""
    # Input
    image_path: str
    patient_code: str
    case_id: Optional[str]
    additional_info: Optional[str]
    patient_history: Optional[str]
    
    # Radiology Results
    radiology_findings: Optional[str]
    abnormalities: Optional[List[str]]
    anatomical_structures: Optional[List[str]]
    confidence: Optional[float]
    image_quality: Optional[str]
    radiology_recommendations: Optional[List[str]]
    radiology_complete: Optional[bool]
    
    # Clinical Results
    differential_diagnosis: Optional[List[str]]
    clinical_reasoning: Optional[str]
    clinical_urgency: Optional[str]
    clinical_followup: Optional[str]
    clinical_confidence: Optional[float]
    clinical_complete: Optional[bool]
    
    # Evidence Results
    evidence_summary: Optional[str]
    search_keywords: Optional[str]
    citations: Optional[List[dict]]
    total_papers: Optional[int]
    evidence_complete: Optional[bool]
    
    # Risk Results
    risk_level: Optional[str]
    risk_score: Optional[float]
    risk_action: Optional[str]
    risk_timeline: Optional[str]
    risk_factors: Optional[List[str]]
    critical_findings: Optional[List[str]]
    next_steps: Optional[List[str]]
    risk_complete: Optional[bool]
    
    # Chairman Results
    chairman_report: Optional[dict]
    executive_summary: Optional[str]
    primary_diagnosis: Optional[str]
    immediate_actions: Optional[List[str]]
    specialist_referrals: Optional[List[str]]
    chairman_confidence: Optional[float]
    chairman_complete: Optional[bool]
    
    # Pipeline Management
    stage_timings: Optional[dict]
    errors: Annotated[List[str], operator.add]
    pipeline_complete: Optional[bool]


class MedicalPipeline:
    """LangGraph-based medical AI pipeline orchestrator"""
    
    def __init__(self):
        self.radiology_agent = RadiologyAgent()
        self.clinical_agent = ClinicalAgent()
        self.evidence_agent = EvidenceAgent()
        self.risk_agent = RiskAssessmentAgent()
        self.chairman_agent = ChairmanAgent()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph StateGraph for medical pipeline"""
        graph = StateGraph(MedicalPipelineState)
        
        # Add nodes
        graph.add_node("radiology", self._radiology_node)
        graph.add_node("parallel_analysis", self._parallel_analysis_node)
        graph.add_node("chairman", self._chairman_node)
        
        # Define flow
        graph.set_entry_point("radiology")
        graph.add_conditional_edges(
            "radiology",
            self._check_radiology_success,
            {"continue": "parallel_analysis", "end": END}
        )
        graph.add_edge("parallel_analysis", "chairman")
        graph.add_edge("chairman", END)
        
        return graph.compile()
    
    async def _radiology_node(self, state: MedicalPipelineState) -> Dict:
        """Execute radiology analysis"""
        print("🔬 Stage 1: Radiology Analysis...")
        start_time = time.time()
        
        try:
            # Create input
            xray_input = XrayInput(
                image_path=state["image_path"],
                patient_code=state["patient_code"],
                case_id=state.get("case_id") or str(uuid.uuid4()),
                additional_info=state.get("additional_info", "")
            )
            
            # Run radiology analysis
            result = await self.radiology_agent.analyze(xray_input, save_to_db=False)
            elapsed = time.time() - start_time
            
            print(f"   ✅ Radiology completed in {elapsed:.2f}s")
            
            return {
                "case_id": xray_input.case_id,
                "radiology_findings": result.findings,
                "abnormalities": result.abnormalities,
                "anatomical_structures": result.anatomical_structures,
                "confidence": result.confidence,
                "image_quality": result.image_quality,
                "radiology_recommendations": result.recommendations,
                "radiology_complete": True,
                "stage_timings": {"radiology": round(elapsed, 2)},
                "errors": []
            }
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"   ❌ Radiology failed in {elapsed:.2f}s: {str(e)}")
            return {
                "radiology_complete": False,
                "stage_timings": {"radiology": round(elapsed, 2)},
                "errors": [f"Radiology error: {str(e)}"]
            }
    
    async def _parallel_analysis_node(self, state: MedicalPipelineState) -> Dict:
        """Execute Clinical, Evidence, and Risk analysis in parallel"""
        print("🔀 Stage 2: Parallel Analysis (Clinical + Evidence + Risk)...")
        start_time = time.time()
        
        # Prepare inputs
        clinical_input = ClinicalInput(
            case_id=state["case_id"],
            patient_code=state["patient_code"],
            radiology_findings=state["radiology_findings"],
            abnormalities=state["abnormalities"],
            confidence=state["confidence"],
            additional_info=state.get("additional_info", "")
        )
        
        evidence_input = EvidenceInput(
            case_id=state["case_id"],
            patient_code=state["patient_code"],
            diagnosis=state.get("abnormalities", ["chest abnormality"]),
            radiology_findings=state["radiology_findings"]
        )
        
        risk_input = RiskInput(
            case_id=state["case_id"],
            radiology_findings=state["radiology_findings"],
            confidence=state["confidence"],
            clinical_context=f"Radiology findings: {state['radiology_findings']}"
        )
        
        # Run all three agents in parallel
        try:
            clinical_task = self.clinical_agent.analyze(clinical_input, save_to_db=False)
            evidence_task = self.evidence_agent.analyze(evidence_input, save_to_db=False)
            risk_task = self.risk_agent.assess_risk(risk_input, save_to_db=False)
            
            clinical_result, evidence_result, risk_result = await asyncio.gather(
                clinical_task, evidence_task, risk_task, return_exceptions=True
            )
            
            elapsed = time.time() - start_time
            print(f"   ✅ Parallel analysis completed in {elapsed:.2f}s")
            
            # Process results
            output = {
                "stage_timings": {"parallel_analysis": round(elapsed, 2)},
                "errors": []
            }
            
            # Clinical results
            if isinstance(clinical_result, Exception):
                output["errors"].append(f"Clinical error: {str(clinical_result)}")
                output["clinical_complete"] = False
            else:
                output.update({
                    "differential_diagnosis": clinical_result.differential_diagnosis,
                    "clinical_reasoning": clinical_result.reasoning,
                    "clinical_urgency": clinical_result.urgency,
                    "clinical_followup": clinical_result.recommended_followup,
                    "clinical_confidence": clinical_result.confidence,
                    "clinical_complete": True
                })
            
            # Evidence results
            if isinstance(evidence_result, Exception):
                output["errors"].append(f"Evidence error: {str(evidence_result)}")
                output["evidence_complete"] = False
            else:
                output.update({
                    "evidence_summary": evidence_result.evidence_summary,
                    "search_keywords": evidence_result.search_keywords,
                    "citations": [c.dict() for c in evidence_result.citations],
                    "total_papers": evidence_result.total_papers_found,
                    "evidence_complete": True
                })
            
            # Risk results
            if isinstance(risk_result, Exception):
                output["errors"].append(f"Risk error: {str(risk_result)}")
                output["risk_complete"] = False
            else:
                output.update({
                    "risk_level": risk_result.risk_level.value,
                    "risk_score": risk_result.risk_score,
                    "risk_action": risk_result.recommended_action.value,
                    "risk_timeline": risk_result.urgency_timeline,
                    "risk_factors": risk_result.risk_factors,
                    "critical_findings": risk_result.critical_findings,
                    "next_steps": risk_result.next_steps,
                    "risk_complete": True
                })
            
            return output
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"   ❌ Parallel analysis failed in {elapsed:.2f}s: {str(e)}")
            return {
                "clinical_complete": False,
                "evidence_complete": False,
                "risk_complete": False,
                "stage_timings": {"parallel_analysis": round(elapsed, 2)},
                "errors": [f"Parallel analysis error: {str(e)}"]
            }
    
    async def _chairman_node(self, state: MedicalPipelineState) -> Dict:
        """Execute chairman analysis"""
        print("👔 Stage 3: Chairman Analysis...")
        start_time = time.time()
        
        try:
            # Prepare chairman input
            chairman_input = ChairmanInput(
                case_id=state["case_id"],
                patient_code=state["patient_code"],
                radiology_findings={
                    "findings": state["radiology_findings"],
                    "abnormalities": state["abnormalities"],
                    "anatomical_structures": state["anatomical_structures"],
                    "confidence": state["confidence"],
                    "recommendations": state["radiology_recommendations"],
                    "image_quality": state["image_quality"]
                },
                clinical_findings={
                    "differential_diagnosis": state["differential_diagnosis"],
                    "reasoning": state["clinical_reasoning"],
                    "urgency": state["clinical_urgency"],
                    "recommended_followup": state["clinical_followup"],
                    "confidence": state["clinical_confidence"]
                },
                evidence_findings={
                    "search_keywords": state["search_keywords"],
                    "evidence_summary": state["evidence_summary"],
                    "total_papers_found": state["total_papers"],
                    "citations": state["citations"]
                },
                risk_findings={
                    "risk_level": state["risk_level"],
                    "risk_score": state["risk_score"],
                    "recommended_action": state["risk_action"],
                    "urgency_timeline": state["risk_timeline"],
                    "risk_factors": state["risk_factors"],
                    "critical_findings": state["critical_findings"],
                    "next_steps": state["next_steps"]
                },
                patient_history=state.get("patient_history"),
                additional_notes=state.get("additional_info")
            )
            
            # Run chairman analysis
            result = await self.chairman_agent.analyze(chairman_input, save_to_db=True)
            elapsed = time.time() - start_time
            
            print(f"   ✅ Chairman analysis completed in {elapsed:.2f}s")
            
            return {
                "chairman_report": {
                    "executive_summary": result.executive_summary,
                    "primary_diagnosis": result.primary_diagnosis,
                    "differential_diagnoses": result.differential_diagnoses,
                    "immediate_actions": result.immediate_actions,
                    "follow_up_plan": result.follow_up_plan,
                    "specialist_referrals": result.specialist_referrals,
                    "confidence_level": result.confidence_level,
                    "consensus_score": result.consensus_score,
                    "urgency_level": result.urgency_level,
                    "chairman_reasoning": result.chairman_reasoning,
                    "quality_flags": result.quality_flags,
                    "report_generated_at": result.report_generated_at
                },
                "executive_summary": result.executive_summary,
                "primary_diagnosis": result.primary_diagnosis,
                "immediate_actions": result.immediate_actions,
                "specialist_referrals": result.specialist_referrals,
                "chairman_confidence": result.confidence_level,
                "chairman_complete": True,
                "pipeline_complete": True,
                "stage_timings": {"chairman": round(elapsed, 2)},
                "errors": []
            }
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"   ❌ Chairman analysis failed in {elapsed:.2f}s: {str(e)}")
            return {
                "chairman_complete": False,
                "pipeline_complete": False,
                "stage_timings": {"chairman": round(elapsed, 2)},
                "errors": [f"Chairman error: {str(e)}"]
            }
    
    def _check_radiology_success(self, state: MedicalPipelineState) -> str:
        """Check if radiology analysis was successful"""
        return "continue" if state.get("radiology_complete", False) else "end"
    
    async def run_pipeline(
        self, 
        image_path: str, 
        patient_code: str = "UNKNOWN",
        additional_info: Optional[str] = None,
        patient_history: Optional[str] = None
    ) -> Dict:
        """Run the complete medical AI pipeline"""
        print("\n" + "="*60)
        print("  🏥 Medical AI Pipeline - LangGraph Orchestration")
        print("  🔬 Radiology → 🔀 [Clinical + Evidence + Risk] → 👔 Chairman")
        print("="*60)
        
        pipeline_start = time.time()
        
        # Initial state
        initial_state = MedicalPipelineState(
            image_path=image_path,
            patient_code=patient_code,
            case_id=str(uuid.uuid4()),
            additional_info=additional_info,
            patient_history=patient_history,
            radiology_findings=None,
            abnormalities=None,
            anatomical_structures=None,
            confidence=None,
            image_quality=None,
            radiology_recommendations=None,
            radiology_complete=None,
            differential_diagnosis=None,
            clinical_reasoning=None,
            clinical_urgency=None,
            clinical_followup=None,
            clinical_confidence=None,
            clinical_complete=None,
            evidence_summary=None,
            search_keywords=None,
            citations=None,
            total_papers=None,
            evidence_complete=None,
            risk_level=None,
            risk_score=None,
            risk_action=None,
            risk_timeline=None,
            risk_factors=None,
            critical_findings=None,
            next_steps=None,
            risk_complete=None,
            chairman_report=None,
            executive_summary=None,
            primary_diagnosis=None,
            immediate_actions=None,
            specialist_referrals=None,
            chairman_confidence=None,
            chairman_complete=None,
            stage_timings={},
            errors=[],
            pipeline_complete=None
        )
        
        # Execute pipeline
        final_state = await self.graph.ainvoke(initial_state)
        total_time = time.time() - pipeline_start
        
        # Add total time to timings
        final_state["stage_timings"]["total_pipeline"] = round(total_time, 2)
        
        # Print summary
        print("\n" + "="*60)
        print("  📋 PIPELINE COMPLETE")
        print("="*60)
        print(f"  Case ID: {final_state.get('case_id')}")
        print(f"  Patient: {patient_code}")
        print(f"  Total Time: {total_time:.2f}s")
        
        stages = [
            ("Radiology", final_state.get("radiology_complete")),
            ("Clinical", final_state.get("clinical_complete")),
            ("Evidence", final_state.get("evidence_complete")),
            ("Risk", final_state.get("risk_complete")),
            ("Chairman", final_state.get("chairman_complete"))
        ]
        
        print(f"\n  Agent Status:")
        for stage, status in stages:
            icon = "✅" if status else "❌"
            print(f"    {icon} {stage}")
        
        if final_state.get("errors"):
            print(f"\n  ⚠️  Errors:")
            for error in final_state["errors"]:
                print(f"    - {error}")
        
        return final_state


# Global pipeline instance
medical_pipeline = MedicalPipeline()