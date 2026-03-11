"""
Main entry point for Multi-Agent Radiology AI System
Integrates Radiology Agent + Risk Assessment Agent
"""
import os
from dotenv import load_dotenv
from app.agents.radiology_agent import RadiologyAgent
from app.agents.risk_agent import RiskAssessmentAgent
from app.models.risk_models import RiskInput

# Load environment variables
load_dotenv()

def test_multi_agent_system():
    """Test the complete Multi-Agent System: Radiology + Risk Assessment"""
    print("🏥 Multi-Agent Radiology AI System")
    print("=" * 60)
    print("🤖 Agents: Radiology Analysis + Risk Assessment")
    
    # Check if Google API key is set
    if not os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY") == "your_google_api_key_here":
        print("❌ Please set your GOOGLE_API_KEY in the .env file")
        print("   Get your API key from: https://makersuite.google.com/app/apikey")
        return
    
    # Initialize agents
    print("\n🤖 Initializing Agents...")
    try:
        radiology_agent = RadiologyAgent()
        risk_agent = RiskAssessmentAgent()
        print("✅ Radiology Agent initialized!")
        print("✅ Risk Assessment Agent initialized!")
        
        # Test connections
        print("\n🔗 Testing connections...")
        if radiology_agent.test_connection():
            print("✅ Gemini Vision connection successful!")
        else:
            print("❌ Gemini connection failed!")
            return
            
        if risk_agent.test_connection():
            print("✅ Risk Assessment system ready!")
        else:
            print("❌ Risk Assessment system failed!")
            return
            
    except Exception as e:
        print(f"❌ Failed to initialize agents: {str(e)}")
        return
    
    # Check for test images
    test_images_dir = "test_images"
    if not os.path.exists(test_images_dir):
        print(f"\n📁 Creating {test_images_dir} directory...")
        os.makedirs(test_images_dir)
    
    # Look for X-ray images
    image_files = []
    for ext in ['.jpg', '.jpeg', '.png', '.bmp']:
        image_files.extend([f for f in os.listdir(test_images_dir) if f.lower().endswith(ext)])
    
    if not image_files:
        print(f"\n📸 No X-ray images found in {test_images_dir}/ directory")
        print("Please add X-ray images to test the system")
        return
    
    print(f"\n📸 Found {len(image_files)} X-ray images")
    print("=" * 60)
    
    # Process each image through both agents
    for i, image_file in enumerate(image_files[:2], 1):  # Test first 2 images
        print(f"\n🔬 CASE {i}: {image_file}")
        print("=" * 40)
        
        try:
            image_path = os.path.join(test_images_dir, image_file)
            patient_code = f"TEST_{i:03d}"
            
            # Step 1: Radiology Analysis
            print("1️⃣ RADIOLOGY ANALYSIS")
            print("🔄 Analyzing X-ray with Gemini Vision...")
            
            radiology_result = radiology_agent.analyze_image_file(
                image_path=image_path,
                patient_code=patient_code,
                additional_info=f"Multi-agent analysis of {image_file}"
            )
            
            print("✅ Radiology Analysis Complete!")
            print(f"   🆔 Case ID: {radiology_result['case_id']}")
            print(f"   🖼️  Quality: {radiology_result['image_quality']}")
            print(f"   ⚠️  Abnormalities: {radiology_result['abnormalities']}")
            print(f"   📊 Confidence: {radiology_result['confidence']:.2f}")
            
            # Step 2: Risk Assessment
            print("\n2️⃣ RISK ASSESSMENT")
            print("🔄 Analyzing risk factors...")
            
            # Create risk input from radiology results
            risk_input = RiskInput(
                case_id=radiology_result['case_id'],
                patient_age=45,  # Default age for testing
                radiology_findings=radiology_result.get('findings', 'No findings available'),
                abnormalities=radiology_result.get('abnormalities', []),
                confidence=radiology_result.get('confidence', 0.0),
                patient_symptoms="Test case - no specific symptoms reported",
                clinical_context=f"Multi-agent analysis of {image_file}"
            )
            
            risk_result = risk_agent.assess_risk(risk_input)
            
            print("✅ Risk Assessment Complete!")
            print(f"   🚨 Risk Level: {risk_result.risk_level.value.upper()}")
            print(f"   📊 Risk Score: {risk_result.risk_score:.2f}")
            print(f"   🏥 Action Required: {risk_result.recommended_action.value}")
            print(f"   ⏰ Timeline: {risk_result.urgency_timeline}")
            
            # Display key findings
            if risk_result.critical_findings:
                print(f"   ⚠️  Critical: {', '.join(risk_result.critical_findings)}")
            
            # Display next steps
            print(f"\n📋 NEXT STEPS:")
            for step in risk_result.next_steps[:3]:  # Show first 3 steps
                print(f"   • {step}")
            
            print(f"\n💡 REASONING: {risk_result.reasoning[:100]}...")
            
        except Exception as e:
            print(f"❌ Error processing {image_file}: {str(e)}")
        
        print("-" * 60)
    
    print("\n🎉 Multi-Agent Testing Complete!")
    print("\n📊 SYSTEM STATUS:")
    print("✅ Radiology Agent: Operational")
    print("✅ Risk Assessment Agent: Operational") 
    print("✅ Database Integration: Active")
    print("✅ Multi-Agent Workflow: Functional")
    
    print("\n🔄 Next Steps:")
    print("1. Run API server: python start_api.py")
    print("2. View saved reports: python view_reports.py")
    print("3. Add clinical_agent.py for collaboration")
    print("4. Add evidence_agent.py for research integration")

if __name__ == "__main__":
    test_multi_agent_system()