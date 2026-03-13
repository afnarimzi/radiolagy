"""
Optimized LangGraph Multi-Agent Pipeline
Level 1: True async/await + asyncio.gather() for real parallel execution
Level 2: Retry logic with exponential backoff + timeout per agent
"""
import operator
import asyncio
import time
from typing import TypedDict, Annotated, List, Optional
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

load_dotenv()

# ── Import All Agents ─────────────────────────────────────
from app.agents.radiology_agent import RadiologyAgent
from app.agents.clinical_agent import ClinicalAgent
from app.agents.evidence_agent import EvidenceAgent
from app.agents.risk_agent import RiskAssessmentAgent
from app.agents.chairman_agent import chairman_agent
from app.models.clinical_models import ClinicalInput
from app.models.evidence_models import EvidenceInput
from app.models.risk_models import RiskInput
from app.models.chairman_models import ChairmanInput

# ── Initialize Agents ─────────────────────────────────────
radiology_agent = RadiologyAgent()
clinical_agent  = ClinicalAgent()
evidence_agent  = EvidenceAgent()
risk_agent      = RiskAssessmentAgent()


# ── Pipeline State ────────────────────────────────────────
class PipelineState(TypedDict):
    image_path:        str
    patient_code:      str
    case_id:           Optional[str]

    radiology_findings:   Optional[str]
    abnormalities:        Optional[List[str]]
    confidence:           Optional[float]
    image_quality:        Optional[str]
    radiology_complete:   Optional[bool]

    differential_diagnosis:  Optional[List[str]]
    clinical_urgency:        Optional[str]
    clinical_reasoning:      Optional[str]
    clinical_complete:       Optional[bool]

    evidence_summary:        Optional[str]
    citations:               Optional[List[dict]]
    search_keywords:         Optional[str]
    evidence_complete:       Optional[bool]

    risk_level:              Optional[str]
    risk_score:              Optional[float]
    risk_action:             Optional[str]
    risk_complete:           Optional[bool]

    chairman_report:         Optional[dict]
    pipeline_complete:       Optional[bool]
    stage_timings:           Optional[dict]

    errors: Annotated[List[str], operator.add]


# ── Level 2: Retry with Exponential Backoff ───────────────
async def with_retry(coro_func, max_retries: int = 3, timeout: float = 60.0, agent_name: str = ""):
    """Retry an async coroutine with exponential backoff and timeout."""
    last_error = None
    for attempt in range(max_retries):
        try:
            result = await asyncio.wait_for(coro_func(), timeout=timeout)
            if attempt > 0:
                print(f"   ✅ {agent_name} succeeded on attempt {attempt + 1}")
            return result
        except asyncio.TimeoutError:
            last_error = f"Timeout after {timeout}s"
            wait_time = 2 ** attempt
            print(f"   ⏳ {agent_name} timed out (attempt {attempt+1}/{max_retries}), retrying in {wait_time}s...")
            await asyncio.sleep(wait_time)
        except Exception as e:
            last_error = str(e)
            if "429" in str(e) or "quota" in str(e).lower():
                wait_time = 30 * (attempt + 1)  # 30s, 60s, 90s
                print(f"   ⏳ {agent_name} rate limited (attempt {attempt+1}/{max_retries}), retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            elif attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"   ⚠️  {agent_name} failed (attempt {attempt+1}/{max_retries}): {e}, retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                raise
    raise Exception(f"{agent_name} failed after {max_retries} attempts. Last error: {last_error}")


# ── Stage 1: Radiology (async) ────────────────────────────
async def run_radiology(state: PipelineState) -> dict:
    print("\n🔬 Stage 1: Radiology Agent running...")
    start = time.time()
    try:
        result = await with_retry(
            lambda: radiology_agent.analyze_image_file(
                image_path=state["image_path"],
                patient_code=state["patient_code"],
                additional_info="LangGraph optimized pipeline",
                save_to_db=True
            ),
            max_retries=3, timeout=120.0, agent_name="Radiology"
        )
        elapsed = time.time() - start
        print(f"   ✅ Radiology complete in {elapsed:.2f}s")
        print(f"   ⚠️  Abnormalities: {result['abnormalities']}")
        return {
            "success": True,
            "case_id":            result["case_id"],
            "radiology_findings": result["findings"],
            "abnormalities":      result["abnormalities"],
            "confidence":         result["confidence"],
            "image_quality":      result["image_quality"],
            "elapsed":            elapsed
        }
    except Exception as e:
        elapsed = time.time() - start
        print(f"   ❌ Radiology failed: {e}")
        return {"success": False, "error": str(e), "elapsed": elapsed}


# ── Stage 2: Clinical (async) ─────────────────────────────
async def run_clinical(state: PipelineState) -> dict:
    print("🧠 Stage 2a: Clinical Agent running...")
    start = time.time()
    try:
        clinical_input = ClinicalInput(
            case_id=state["case_id"],
            patient_code=state["patient_code"],
            radiology_findings=state["radiology_findings"],
            abnormalities=state["abnormalities"] or [],
            confidence=state["confidence"] or 0.8
        )
        result = await with_retry(
            lambda: clinical_agent.analyze(clinical_input, save_to_db=True),
            max_retries=3, timeout=60.0, agent_name="Clinical"
        )
        elapsed = time.time() - start
        print(f"   ✅ Clinical complete in {elapsed:.2f}s — {', '.join(result.differential_diagnosis)}")
        return {
            "success": True,
            "differential_diagnosis": result.differential_diagnosis,
            "clinical_urgency":       result.urgency,
            "clinical_reasoning":     result.reasoning,
            "elapsed":                elapsed
        }
    except Exception as e:
        elapsed = time.time() - start
        print(f"   ❌ Clinical failed: {e}")
        return {"success": False, "error": str(e), "elapsed": elapsed}


# ── Stage 2: Evidence (async) ─────────────────────────────
async def run_evidence(state: PipelineState) -> dict:
    print("📚 Stage 2b: Evidence Agent running...")
    start = time.time()
    try:
        evidence_input = EvidenceInput(
            case_id=state["case_id"],
            patient_code=state["patient_code"],
            diagnosis=state["differential_diagnosis"] or [],
            radiology_findings=state["radiology_findings"]
        )
        result = await with_retry(
            lambda: evidence_agent.analyze(evidence_input, save_to_db=True),
            max_retries=3, timeout=60.0, agent_name="Evidence"
        )
        elapsed = time.time() - start
        print(f"   ✅ Evidence complete in {elapsed:.2f}s — {result.total_papers_found} papers")
        return {
            "success":          True,
            "evidence_summary": result.evidence_summary,
            "citations":        [c.dict() for c in result.citations],
            "search_keywords":  result.search_keywords,
            "elapsed":          elapsed
        }
    except Exception as e:
        elapsed = time.time() - start
        print(f"   ❌ Evidence failed: {e}")
        return {"success": False, "error": str(e), "elapsed": elapsed}


# ── Stage 2: Risk (async) ─────────────────────────────────
async def run_risk(state: PipelineState) -> dict:
    print("⚠️  Stage 2c: Risk Agent running...")
    start = time.time()
    try:
        risk_input = RiskInput(
            case_id=state["case_id"],
            radiology_findings=state["radiology_findings"],
            abnormalities=state["abnormalities"] or [],
            confidence=state["confidence"] or 0.8,
            clinical_context=f"Diagnosis: {', '.join(state.get('differential_diagnosis') or [])}"
        )
        result = await with_retry(
            lambda: risk_agent.assess_risk(risk_input, save_to_db=True),
            max_retries=3, timeout=60.0, agent_name="Risk"
        )
        elapsed = time.time() - start
        print(f"   ✅ Risk complete in {elapsed:.2f}s — {result.risk_level.value.upper()}")
        return {
            "success":    True,
            "risk_level": result.risk_level.value,
            "risk_score": result.risk_score,
            "risk_action": result.recommended_action.value,
            "elapsed":    elapsed
        }
    except Exception as e:
        elapsed = time.time() - start
        print(f"   ❌ Risk failed: {e}")
        return {"success": False, "error": str(e), "elapsed": elapsed}


# ── LangGraph Node: Radiology ─────────────────────────────
def radiology_node(state: PipelineState) -> dict:
    result = asyncio.run(run_radiology(state))
    if result["success"]:
        return {
            "case_id":            result["case_id"],
            "radiology_findings": result["radiology_findings"],
            "abnormalities":      result["abnormalities"],
            "confidence":         result["confidence"],
            "image_quality":      result["image_quality"],
            "radiology_complete": True,
            "stage_timings":      {"radiology": round(result["elapsed"], 2)},
            "errors":             []
        }
    return {
        "radiology_complete": False,
        "stage_timings":      {"radiology": round(result["elapsed"], 2)},
        "errors": [f"Radiology error: {result['error']}"]
    }


# ── LangGraph Node: Stage 2 Parallel ─────────────────────
def parallel_stage2_node(state: PipelineState) -> dict:
    """
    Level 1: Run Clinical + Evidence + Risk truly in parallel
    using asyncio.gather() — all 3 run simultaneously
    """
    print("\n🔀 Stage 2: Running Clinical + Evidence + Risk in PARALLEL...")
    start = time.time()

    async def run_all():
        # All 3 agents run at the same time
        results = await asyncio.gather(
            run_clinical(state),
            run_evidence(state),
            run_risk(state),
            return_exceptions=True  # one failure won't cancel others
        )
        return results

    clinical_r, evidence_r, risk_r = asyncio.run(run_all())
    elapsed = time.time() - start
    print(f"\n   ⏱️  Stage 2 parallel total: {elapsed:.2f}s")

    output = {"errors": [], "stage_timings": {"stage2_parallel": round(elapsed, 2)}}

    # Unpack clinical
    if isinstance(clinical_r, dict) and clinical_r.get("success"):
        output.update({
            "differential_diagnosis": clinical_r["differential_diagnosis"],
            "clinical_urgency":       clinical_r["clinical_urgency"],
            "clinical_reasoning":     clinical_r["clinical_reasoning"],
            "clinical_complete":      True
        })
    else:
        err = str(clinical_r) if isinstance(clinical_r, Exception) else clinical_r.get("error", "Unknown")
        output["errors"] = output["errors"] + [f"Clinical error: {err}"]
        output["clinical_complete"] = False

    # Unpack evidence
    if isinstance(evidence_r, dict) and evidence_r.get("success"):
        output.update({
            "evidence_summary":  evidence_r["evidence_summary"],
            "citations":         evidence_r["citations"],
            "search_keywords":   evidence_r["search_keywords"],
            "evidence_complete": True
        })
    else:
        err = str(evidence_r) if isinstance(evidence_r, Exception) else evidence_r.get("error", "Unknown")
        output["errors"] = output["errors"] + [f"Evidence error: {err}"]
        output["evidence_complete"] = False

    # Unpack risk
    if isinstance(risk_r, dict) and risk_r.get("success"):
        output.update({
            "risk_level":    risk_r["risk_level"],
            "risk_score":    risk_r["risk_score"],
            "risk_action":   risk_r["risk_action"],
            "risk_complete": True
        })
    else:
        err = str(risk_r) if isinstance(risk_r, Exception) else risk_r.get("error", "Unknown")
        output["errors"] = output["errors"] + [f"Risk error: {err}"]
        output["risk_complete"] = False

    return output


# ── LangGraph Node: Chairman ──────────────────────────────
def chairman_node(state: PipelineState) -> dict:
    print("\n👔 Stage 3: Chairman Agent running...")
    start = time.time()
    try:
        chairman_input = ChairmanInput(
            case_id=state["case_id"],
            patient_code=state["patient_code"],
            radiology_findings={
                "findings":      state["radiology_findings"],
                "abnormalities": state["abnormalities"] or [],
                "confidence":    state["confidence"] or 0.8,
                "image_quality": state["image_quality"] or "unknown"
            },
            clinical_findings={
                "differential_diagnosis": state["differential_diagnosis"] or [],
                "urgency":                state["clinical_urgency"] or "routine",
                "reasoning":              state["clinical_reasoning"] or ""
            },
            evidence_findings={
                "evidence_summary":   state["evidence_summary"] or "",
                "citations":          state["citations"] or [],
                "search_keywords":    state["search_keywords"] or "",
                "total_papers_found": len(state["citations"] or [])
            },
            risk_findings={
                "risk_level":  state["risk_level"] or "low",
                "risk_score":  state["risk_score"] or 0.0,
                "risk_action": state["risk_action"] or ""
            }
        )

        report = asyncio.run(with_retry(
            lambda: chairman_agent.analyze(chairman_input, save_to_db=True),
            max_retries=3, timeout=60.0, agent_name="Chairman"
        ))

        elapsed = time.time() - start
        print(f"   ✅ Chairman complete in {elapsed:.2f}s")
        print(f"   📋 Primary diagnosis: {report.primary_diagnosis}")
        print(f"   🚨 Urgency: {report.urgency_level}")

        return {
            "chairman_report":   report.dict(),
            "pipeline_complete": True,
            "stage_timings":     {"chairman": round(elapsed, 2)},
            "errors":            []
        }
    except Exception as e:
        elapsed = time.time() - start
        print(f"   ❌ Chairman failed: {e}")
        return {
            "pipeline_complete": False,
            "stage_timings":     {"chairman": round(elapsed, 2)},
            "errors": [f"Chairman error: {str(e)}"]
        }


# ── Conditional Edge ──────────────────────────────────────
def check_radiology(state: PipelineState) -> str:
    return "proceed" if state.get("radiology_complete") else "end"


# ── Build Graph ───────────────────────────────────────────
def build_pipeline() -> StateGraph:
    graph = StateGraph(PipelineState)

    graph.add_node("radiology", radiology_node)
    graph.add_node("stage2",    parallel_stage2_node)
    graph.add_node("chairman",  chairman_node)

    graph.set_entry_point("radiology")

    graph.add_conditional_edges(
        "radiology",
        check_radiology,
        {"proceed": "stage2", "end": END}
    )
    graph.add_edge("stage2",   "chairman")
    graph.add_edge("chairman", END)

    return graph.compile()


# ── Run Pipeline ──────────────────────────────────────────
def run_pipeline(image_path: str, patient_code: str = "UNKNOWN") -> dict:
    print("\n" + "="*60)
    print("  🏥 Optimized LangGraph Pipeline")
    print("  ⚡ Level 1: True async parallel execution")
    print("  🔄 Level 2: Retry + timeout per agent")
    print("="*60)

    pipeline_start = time.time()
    pipeline = build_pipeline()

    initial_state = PipelineState(
        image_path=image_path,
        patient_code=patient_code,
        case_id=None,
        radiology_findings=None,
        abnormalities=None,
        confidence=None,
        image_quality=None,
        radiology_complete=None,
        differential_diagnosis=None,
        clinical_urgency=None,
        clinical_reasoning=None,
        clinical_complete=None,
        evidence_summary=None,
        citations=None,
        search_keywords=None,
        evidence_complete=None,
        risk_level=None,
        risk_score=None,
        risk_action=None,
        risk_complete=None,
        chairman_report=None,
        pipeline_complete=None,
        stage_timings={},
        errors=[]
    )

    final_state = pipeline.invoke(initial_state)
    total_time = time.time() - pipeline_start

    # ── Final Report ──────────────────────────────────────
    print("\n" + "="*60)
    print("  📋 PIPELINE COMPLETE — FINAL REPORT")
    print("="*60)
    print(f"  Case ID:    {final_state.get('case_id')}")
    print(f"  Patient:    {patient_code}")
    print(f"  Diagnosis:  {', '.join(final_state.get('differential_diagnosis') or [])}")
    print(f"  Risk Level: {str(final_state.get('risk_level', 'N/A')).upper()}")
    print(f"  Urgency:    {final_state.get('clinical_urgency', 'N/A')}")
    print(f"  Papers:     {len(final_state.get('citations') or [])} PubMed citations")

    timings = final_state.get("stage_timings") or {}
    print(f"\n  ⏱️  Performance Summary:")
    print(f"    Stage 1 - Radiology:          {timings.get('radiology', 'N/A')}s")
    print(f"    Stage 2 - Parallel (3 agents): {timings.get('stage2_parallel', 'N/A')}s")
    print(f"    Stage 3 - Chairman:           {timings.get('chairman', 'N/A')}s")
    print(f"    Total Pipeline:               {total_time:.2f}s")

    stages = {
        "Radiology": final_state.get("radiology_complete"),
        "Clinical":  final_state.get("clinical_complete"),
        "Evidence":  final_state.get("evidence_complete"),
        "Risk":      final_state.get("risk_complete"),
        "Chairman":  final_state.get("pipeline_complete")
    }
    print(f"\n  Pipeline Stages:")
    for stage, status in stages.items():
        icon = "✅" if status else "❌"
        print(f"    {icon} {stage}")

    if final_state.get("errors"):
        print(f"\n  ⚠️  Errors:")
        for err in final_state["errors"]:
            print(f"     - {err}")

    return final_state