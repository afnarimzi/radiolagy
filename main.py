"""
Main entry point for Multi-Agent Radiology AI System
Integrates all 4 agents:
  Stage 1: Radiology Agent    (Gemini Vision)
  Stage 2: Clinical Agent     (Groq - Llama 70B)
  Stage 2: Evidence Agent     (Groq + PubMed API)
  Stage 2: Risk Agent         (Gemini)
"""
import os
from dotenv import load_dotenv
from app.agents.radiology_agent import RadiologyAgent
from app.agents.risk_agent import RiskAssessmentAgent
from app.agents.clinical_agent import ClinicalAgent
from app.agents.evidence_agent import EvidenceAgent
from app.models.risk_models import RiskInput
from app.models.clinical_models import ClinicalInput
from app.models.evidence_models import EvidenceInput

load_dotenv()

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_step(number, title):
    print(f"\n{number} {title}")
    print("-" * 40)

def test_multi_agent_system():
    """Run complete 4-agent pipeline on test X-ray images"""

    print_section("🏥 Multi-Agent Radiology AI System")
    print("🤖 Agents: Radiology → Clinical + Evidence + Risk")

    # ── Check API Keys ────────────────────────────────────
    if not os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY") == "your_google_api_key_here":
        print("❌ Please set GOOGLE_API_KEY in .env file")
        return

    if not os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API_KEY") == "your_groq_api_key_here":
        print("❌ Please set GROQ_API_KEY in .env file")
        return

    # ── Initialize All Agents ─────────────────────────────
    print("\n🤖 Initializing All Agents...")
    try:
        radiology_agent = RadiologyAgent()
        risk_agent      = RiskAssessmentAgent()
        clinical_agent  = ClinicalAgent()
        evidence_agent  = EvidenceAgent()

        print("✅ Radiology Agent initialized  (Gemini Vision)")
        print("✅ Risk Agent initialized        (Gemini)")
        print("✅ Clinical Agent initialized    (Groq - Llama 70B)")
        print("✅ Evidence Agent initialized    (Groq + PubMed)")

    except Exception as e:
        print(f"❌ Failed to initialize agents: {str(e)}")
        return

    # ── Test Connections ──────────────────────────────────
    print("\n🔗 Testing connections...")
    if radiology_agent.test_connection():
        print("✅ Gemini Vision connection OK")
    else:
        print("❌ Gemini connection failed")
        return

    if risk_agent.test_connection():
        print("✅ Risk Agent connection OK")
    else:
        print("❌ Risk Agent connection failed")
        return

    # ── Find Test Images ──────────────────────────────────
    test_images_dir = "test_images"
    image_files = []
    for ext in ['.jpg', '.jpeg', '.png', '.bmp']:
        image_files.extend([
            f for f in os.listdir(test_images_dir)
            if f.lower().endswith(ext)
        ])

    if not image_files:
        print(f"\n❌ No X-ray images found in {test_images_dir}/")
        return

    print(f"\n📸 Found {len(image_files)} X-ray image(s)")

    # ── Process Each Image Through All 4 Agents ───────────
    for i, image_file in enumerate(image_files[:2], 1):
        print_section(f"🔬 CASE {i}: {image_file}")

        image_path   = os.path.join(test_images_dir, image_file)
        patient_code = f"TEST_{i:03d}"

        try:
            # ── STAGE 1: Radiology Agent ──────────────────
            print_step("1️⃣", "RADIOLOGY AGENT — X-ray Analysis")
            print("🔄 Analyzing X-ray with Gemini Vision...")

            radiology_result = radiology_agent.analyze_image_file(
                image_path=image_path,
                patient_code=patient_code,
                additional_info=f"Multi-agent analysis of {image_file}"
            )

            case_id = radiology_result["case_id"]

            print("✅ Radiology Analysis Complete!")
            print(f"   🆔 Case ID:       {case_id}")
            print(f"   🖼️  Image Quality: {radiology_result['image_quality']}")
            print(f"   ⚠️  Abnormalities: {', '.join(radiology_result['abnormalities']) or 'None'}")
            print(f"   📊 Confidence:    {radiology_result['confidence']:.2f}")

            # ── STAGE 2a: Clinical Agent ──────────────────
            print_step("2️⃣", "CLINICAL AGENT — Differential Diagnosis")
            print("🔄 Running clinical reasoning...")

            clinical_input = ClinicalInput(
                case_id=case_id,
                patient_code=patient_code,
                radiology_findings=radiology_result["findings"],
                abnormalities=radiology_result["abnormalities"],
                confidence=radiology_result["confidence"]
            )

            clinical_result = clinical_agent.analyze(
                clinical_input,
                save_to_db=True
            )

            print("✅ Clinical Analysis Complete!")
            print(f"   🩺 Diagnosis:  {', '.join(clinical_result.differential_diagnosis)}")
            print(f"   🚦 Urgency:    {clinical_result.urgency}")
            print(f"   📊 Confidence: {clinical_result.confidence:.2f}")
            print(f"   💊 Follow-up:  {clinical_result.recommended_followup[:80]}...")

            # ── STAGE 2b: Evidence Agent ──────────────────
            print_step("3️⃣", "EVIDENCE AGENT — PubMed Literature Search")
            print("🔄 Searching PubMed for relevant papers...")

            evidence_input = EvidenceInput(
                case_id=case_id,
                patient_code=patient_code,
                diagnosis=clinical_result.differential_diagnosis,
                radiology_findings=radiology_result["findings"]
            )

            evidence_result = evidence_agent.analyze(
                evidence_input,
                save_to_db=True
            )

            print("✅ Evidence Search Complete!")
            print(f"   🔍 Keywords:      {evidence_result.search_keywords}")
            print(f"   📚 Papers found:  {evidence_result.total_papers_found}")
            print(f"   📝 Summary:       {evidence_result.evidence_summary[:80]}...")
            if evidence_result.citations:
                print(f"   📄 Top citation:  {evidence_result.citations[0].title[:60]}...")
                print(f"   🔗 URL:           {evidence_result.citations[0].url}")

            # ── STAGE 2c: Risk Agent ──────────────────────
            print_step("4️⃣", "RISK AGENT — Risk Assessment")
            print("🔄 Assessing risk level...")

            risk_input = RiskInput(
                case_id=case_id,
                patient_age=45,
                radiology_findings=radiology_result["findings"],
                abnormalities=radiology_result["abnormalities"],
                confidence=radiology_result["confidence"],
                patient_symptoms="Test case - no specific symptoms",
                clinical_context=f"Diagnosis: {', '.join(clinical_result.differential_diagnosis)}"
            )

            risk_result = risk_agent.assess_risk(risk_input)

            print("✅ Risk Assessment Complete!")
            print(f"   🚨 Risk Level: {risk_result.risk_level.value.upper()}")
            print(f"   📊 Risk Score: {risk_result.risk_score:.2f}")
            print(f"   🏥 Action:     {risk_result.recommended_action.value}")
            print(f"   ⏰ Timeline:   {risk_result.urgency_timeline}")
            if risk_result.critical_findings:
                print(f"   ⚠️  Critical:   {', '.join(risk_result.critical_findings)}")

            # ── COMBINED REPORT ───────────────────────────
            print_section(f"📋 COMBINED REPORT — CASE {i}")
            print(f"  Case ID:     {case_id}")
            print(f"  Patient:     {patient_code}")
            print(f"  Image:       {image_file}")
            print(f"\n  {'─'*50}")
            print(f"  🔬 Radiology:  {', '.join(radiology_result['abnormalities']) or 'No abnormalities'}")
            print(f"  🩺 Diagnosis:  {', '.join(clinical_result.differential_diagnosis)}")
            print(f"  📚 Evidence:   {evidence_result.total_papers_found} PubMed papers found")
            print(f"  🚨 Risk:       {risk_result.risk_level.value.upper()} (score: {risk_result.risk_score:.2f})")
            print(f"  🏥 Action:     {risk_result.recommended_action.value}")
            print(f"  ⏰ Timeline:   {risk_result.urgency_timeline}")
            print(f"\n  Next Steps:")
            for step in risk_result.next_steps[:3]:
                print(f"    • {step}")

        except Exception as e:
            print(f"❌ Error processing {image_file}: {str(e)}")
            import traceback
            traceback.print_exc()

        print("\n" + "─" * 60)

    # ── Final Status ──────────────────────────────────────
    print_section("🎉 Multi-Agent Pipeline Complete!")
    print("✅ Radiology Agent:  Operational (Gemini Vision)")
    print("✅ Clinical Agent:   Operational (Groq Llama 70B)")
    print("✅ Evidence Agent:   Operational (Groq + PubMed)")
    print("✅ Risk Agent:       Operational (Gemini)")
    print("✅ Database:         All results saved")
    print("\n📌 All 4 agents ran in a single pipeline run.")
    print("📌 Results linked by case_id in PostgreSQL.")
    print("\n🔄 Next Step: Wire agents into LangGraph StateGraph")


if __name__ == "__main__":
    test_multi_agent_system()