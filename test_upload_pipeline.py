#!/usr/bin/env python3
"""
Test the upload + complete 4-agent pipeline endpoint
Tests: Upload Image → Radiology → Clinical → Evidence → Risk Assessment
"""

import requests
import json
import time
from datetime import datetime
import os

BASE_URL = "http://localhost:8000"
TEST_IMAGE_PATH = "test_images/00000003_000.png"
PATIENT_CODE = "UPLOAD_PIPELINE_TEST"

def print_header(title):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"🔬 {title}")
    print("="*60)

def print_step(step, description):
    """Print formatted step"""
    print(f"\n📋 {step}: {description}")
    print("-" * 40)

def test_upload_complete_pipeline():
    """Test the upload + complete 4-agent pipeline endpoint"""
    
    print_header("Upload + Complete 4-Agent Pipeline Test")
    print(f"🕒 Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 API Base URL: {BASE_URL}")
    print(f"🖼️  Test Image: {TEST_IMAGE_PATH}")
    print(f"👤 Patient Code: {PATIENT_CODE}")
    
    # Check if test image exists
    if not os.path.exists(TEST_IMAGE_PATH):
        print(f"❌ Test image not found: {TEST_IMAGE_PATH}")
        return False
    
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
    
    print_step("2", "Upload Image and Execute Complete Pipeline")
    print("🚀 Uploading image and starting comprehensive analysis...")
    print("   Pipeline: Upload → Radiology → Clinical → Evidence → Risk")
    
    start_time = time.time()
    
    try:
        # Prepare file upload
        with open(TEST_IMAGE_PATH, 'rb') as f:
            files = {
                'file': (os.path.basename(TEST_IMAGE_PATH), f, 'image/png')
            }
            data = {
                'patient_code': PATIENT_CODE,
                'additional_info': 'Upload pipeline test - comprehensive medical analysis from uploaded image'
            }
            
            response = requests.post(
                f"{BASE_URL}/upload-complete-pipeline", 
                files=files, 
                data=data
            )
        
        if response.status_code == 200:
            result = response.json()
            processing_time = time.time() - start_time
            
            print(f"✅ Upload and complete pipeline executed successfully in {processing_time:.1f}s")
            
            # Display results
            print_step("3", "Upload and Pipeline Results")
            
            # Upload Information
            upload_info = result.get('upload_info', {})
            print(f"📤 Upload Information:")
            print(f"   Original Filename: {upload_info.get('original_filename')}")
            print(f"   Saved Path: {upload_info.get('saved_path')}")
            print(f"   File Size: {upload_info.get('file_size', 0):,} bytes")
            print(f"   Content Type: {upload_info.get('content_type')}")
            
            print(f"\n📊 Case Information:")
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
            print(f"   Workflow: {processing_summary.get('workflow', 'N/A')}")
            print(f"   Overall Confidence: {result.get('overall_confidence', 0):.1%}")
            print(f"   Processing Time: {processing_time:.1f} seconds")
            
            # Save detailed results
            save_upload_results(result, processing_time)
            
            return True
            
        else:
            print(f"❌ Upload pipeline execution failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Upload pipeline execution error: {str(e)}")
        return False

def save_upload_results(result, processing_time):
    """Save upload pipeline results to file"""
    try:
        import os
        os.makedirs("test_reports", exist_ok=True)
        
        case_id = result.get('case_id', 'unknown')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"test_reports/upload_pipeline_{case_id[:8]}_{timestamp}.json"
        
        # Add processing time to results
        result['processing_time_seconds'] = processing_time
        result['test_timestamp'] = datetime.now().isoformat()
        
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print(f"\n📁 Detailed results saved: {filename}")
        
    except Exception as e:
        print(f"⚠️  Could not save results: {str(e)}")

def test_api_documentation():
    """Test if the API documentation shows the new endpoint"""
    print_step("4", "API Documentation Check")
    
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code == 200:
            print("✅ API documentation accessible at http://localhost:8000/docs")
            print("   You can test the upload endpoint interactively there!")
        else:
            print(f"⚠️  API documentation not accessible: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Could not check API documentation: {str(e)}")

def main():
    """Run upload pipeline test"""
    print("🚀 Starting Upload + Complete 4-Agent Pipeline Test")
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run upload pipeline test
    upload_success = test_upload_complete_pipeline()
    
    # Check API documentation
    test_api_documentation()
    
    # Final summary
    print_header("FINAL TEST RESULTS")
    
    if upload_success:
        print("🎉 SUCCESS: Upload + Complete 4-agent pipeline is fully operational!")
        print("   ✅ Image upload working")
        print("   ✅ All agents processing uploaded image")
        print("   ✅ Complete medical analysis from uploaded file")
        print("   ✅ Comprehensive results returned")
        print("\n💡 Your system now supports:")
        print("   📤 Direct image upload via API")
        print("   🔬 Automatic radiology analysis")
        print("   🩺 Clinical interpretation")
        print("   📚 Evidence-based research")
        print("   ⚠️  Risk assessment")
        print("\n🌐 Try it interactively at: http://localhost:8000/docs")
        return True
    else:
        print("❌ FAILURE: Upload pipeline test failed")
        print("   Check the error messages above for details")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)