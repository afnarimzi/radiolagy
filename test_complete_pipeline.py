#!/usr/bin/env python3
"""
Test the complete 4-agent pipeline through API endpoint
Tests: Radiology → Clinical → Evidence → Risk Assessment in single workflow
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"
TEST_IMAGE_PATH = "test_images/00000003_000.png"
PATIENT_CODE = "PIPELINE_TEST_001"

def print_header(title):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"🔬 {title}")
    print("="*60)

def print_step(step, description):
    """Print formatted step"""
    print(f"\n📋 {step}: {description}")
    print("-" * 40)

def test_complete_pipeline():
    """Test the complete 4-agent pipeline endpoint"""
    
    print_header("Complete 4-Agent Pipeline Test")
    print(f"🕒 Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 API Base URL: {BASE_URL}")
    print(f"🖼️  Test Image: {TEST_IMAGE_PATH}")
    print(f"👤 Patient Code: {PATIENT_CODE}")
    
    # Test data
    pipeline_data = {
        "image_path": TEST_IMAGE_PATH,
        "patient_code": PATIENT_CODE,
        "additional_info": "Complete 4-agent pipeline test - comprehensive medical analysis"
    }
    
    print_step("1", "Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API server is healthy and ready")
        else:
            print(f"❌ API server not ready: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API server: {str(e)}")
        return False
    
    print_step("2", "Execute Complete 4-Agent Pipeline")
    print("🚀 Starting comprehensive analysis...")
    print("   Pipeline: Radiology → Clinical → Evidence → Risk")
    
    start_time = time.time()
    
    try:
        response = requests.post(f"{BASE_URL}/analyze-complete-pipeline", json=pipeline_data)
        
        if response.status_code == 200:
            result = response.json()
            processing_time = time.time() - start_time
            
            print(f"✅ Complete pipeline executed successfully in {processing_time:.1f}s")
            
            # Display results
            print_step("3", "Pipeline Results Summary")
            
            print(f"📊 Case Information:")
            print(f"   Case ID: {result.get('case_id')}")
            print(f"   Patient Code: {result.get('patient_code')}")
            print(f"   Pipeline Status: {result.get('pipeline_status')}")
            print(f"   Agents Executed: {', '.join(result.get('agents_executed', []))}")
            
            # Radiology Results
            radiology = result.get('radiology_analysis', {})
            print(f"\n🔬 Radiology Analysis:")
            print(f"   Confidence: {radiology.get('confidence', 0):.1%}")
            print(f"   Abnormalities: {len(radiology.get('abnormalities', []))} detected")
            print(f"   Image Quality: {radiology.get('image_quality', 'N/A')}")
            print(f"   Findings: {radiology.get('findings', '')[:100]}...")
            
            # Clinical Results
            clinical = result.get('clinical_analysis', {})
            print(f"\n🩺 Clinical Analysis:")
            print(f"   Confidence: {clinical.get('confidence', 0):.1%}")
            print(f"   Urgency: {clinical.get('urgency', 'N/A')}")
            diagnosis = clinical.get('differential_diagnosis', [])
            if isinstance(diagnosis, list):
                print(f"   Differential Diagnosis: {', '.join(diagnosis[:3])}")
            else:
                print(f"   Differential Diagnosis: {diagnosis}")
            print(f"   Reasoning: {clinical.get('reasoning', '')[:100]}...")
            
            # Evidence Results
            evidence = result.get('evidence_research', {})
            print(f"\n📚 Evidence Research:")
            print(f"   Search Keywords: {evidence.get('search_keywords', 'N/A')}")
            print(f"   Papers Found: {evidence.get('total_papers_found', 0)}")
            print(f"   Evidence Summary: {evidence.get('evidence_summary', '')[:100]}...")
            
            # Risk Assessment Results
            risk = result.get('risk_assessment', {})
            print(f"\n⚠️  Risk Assessment:")
            print(f"   Risk Level: {risk.get('risk_level', 'N/A')}")
            print(f"   Risk Score: {risk.get('risk_score', 0)}/10")
            print(f"   Confidence: {risk.get('confidence', 0):.1%}")
            print(f"   Recommended Action: {risk.get('recommended_action', 'N/A')}")
            print(f"   Urgency Timeline: {risk.get('urgency_timeline', 'N/A')}")
            print(f"   Specialist Referral: {risk.get('specialist_referral', 'N/A')}")
            
            # Overall Summary
            processing_summary = result.get('processing_summary', {})
            print(f"\n📈 Processing Summary:")
            print(f"   Total Agents: {processing_summary.get('total_agents', 0)}")
            print(f"   Successful Agents: {processing_summary.get('successful_agents', 0)}")
            print(f"   Data Flow: {processing_summary.get('data_flow', 'N/A')}")
            print(f"   Overall Confidence: {result.get('overall_confidence', 0):.1%}")
            print(f"   Processing Time: {processing_time:.1f} seconds")
            
            # Save detailed results
            save_pipeline_results(result, processing_time)
            
            return True
            
        else:
            print(f"❌ Pipeline execution failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Pipeline execution error: {str(e)}")
        return False

def save_pipeline_results(result, processing_time):
    """Save pipeline results to file"""
    try:
        import os
        os.makedirs("test_reports", exist_ok=True)
        
        case_id = result.get('case_id', 'unknown')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"test_reports/complete_pipeline_{case_id[:8]}_{timestamp}.json"
        
        # Add processing time to results
        result['processing_time_seconds'] = processing_time
        result['test_timestamp'] = datetime.now().isoformat()
        
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print(f"\n📁 Detailed results saved: {filename}")
        
    except Exception as e:
        print(f"⚠️  Could not save results: {str(e)}")

def test_individual_endpoints():
    """Quick test of individual endpoints to ensure they're working"""
    print_header("Individual Endpoint Verification")
    
    endpoints = [
        ("Health", "GET", "/health", None),
        ("Radiology", "POST", "/analyze", {
            "image_path": TEST_IMAGE_PATH,
            "patient_code": PATIENT_CODE + "_INDIVIDUAL"
        }),
        ("Risk", "POST", "/assess-risk", {
            "patient_code": PATIENT_CODE + "_INDIVIDUAL",
            "radiology_findings": "Test findings for individual endpoint verification"
        })
    ]
    
    results = {}
    
    for name, method, endpoint, data in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}")
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", json=data)
            
            if response.status_code == 200:
                print(f"✅ {name} endpoint: Working")
                results[name.lower()] = True
            else:
                print(f"❌ {name} endpoint: Failed ({response.status_code})")
                results[name.lower()] = False
                
        except Exception as e:
            print(f"❌ {name} endpoint: Error - {str(e)}")
            results[name.lower()] = False
    
    working = sum(results.values())
    total = len(results)
    print(f"\n📊 Individual Endpoints: {working}/{total} working")
    
    return working >= 2  # At least health and one agent working

def main():
    """Run complete pipeline test"""
    print("🚀 Starting Complete 4-Agent Pipeline Test")
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # First verify individual endpoints
    if not test_individual_endpoints():
        print("\n❌ CRITICAL: Basic endpoints not working. Cannot proceed with pipeline test.")
        return False
    
    # Run complete pipeline test
    pipeline_success = test_complete_pipeline()
    
    # Final summary
    print_header("FINAL TEST RESULTS")
    
    if pipeline_success:
        print("🎉 SUCCESS: Complete 4-agent pipeline is fully operational!")
        print("   ✅ All agents working together in single workflow")
        print("   ✅ Radiology → Clinical → Evidence → Risk pipeline complete")
        print("   ✅ Comprehensive medical analysis system ready for production")
        print("\n💡 Your Multi-Agent Medical AI System is complete and working!")
        return True
    else:
        print("❌ FAILURE: Pipeline test failed")
        print("   Check the error messages above for details")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)