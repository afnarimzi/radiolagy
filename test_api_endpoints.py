#!/usr/bin/env python3
"""
Test script for Multi-Agent AI API endpoints
"""
import requests
import json
import time

# API base URL
BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test health check endpoint"""
    print("🔍 Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Health check passed: {data['status']}")
        print(f"   Agents: radiology={data.get('radiology_agent')}, risk={data.get('risk_agent')}")
        return True
    else:
        print(f"❌ Health check failed: {response.status_code}")
        return False

def test_stats():
    """Test statistics endpoint"""
    print("\n📊 Testing statistics...")
    response = requests.get(f"{BASE_URL}/stats")
    if response.status_code == 200:
        data = response.json()
        print("✅ Statistics retrieved:")
        print(f"   Patients: {data['total_patients']}")
        print(f"   Cases: {data['total_cases']}")
        print(f"   Radiology Results: {data['total_radiology_results']}")
        print(f"   Risk Assessments: {data['total_risk_assessments']}")
        print(f"   Average Confidence: {data['average_confidence']}")
        return True
    else:
        print(f"❌ Statistics failed: {response.status_code}")
        return False

def test_analyze_endpoint():
    """Test radiology analysis endpoint"""
    print("\n🖼️  Testing radiology analysis...")
    
    # Test data
    test_request = {
        "image_path": "test_images/00000003_000.png",
        "patient_code": "API_TEST_001",
        "additional_info": "API endpoint test"
    }
    
    response = requests.post(f"{BASE_URL}/analyze", json=test_request)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Radiology analysis completed:")
        print(f"   Case ID: {data['case_id']}")
        print(f"   Confidence: {data['confidence']}")
        print(f"   Abnormalities: {len(data['abnormalities'])} found")
        return data['case_id']
    else:
        print(f"❌ Radiology analysis failed: {response.status_code}")
        if response.text:
            print(f"   Error: {response.text}")
        return None

def test_risk_assessment(case_id):
    """Test risk assessment endpoint"""
    print("\n🚨 Testing risk assessment...")
    
    # Test data
    test_request = {
        "case_id": case_id,
        "patient_code": "API_TEST_001",
        "additional_clinical_info": "API endpoint test for risk assessment"
    }
    
    response = requests.post(f"{BASE_URL}/assess-risk", json=test_request)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Risk assessment completed:")
        print(f"   Risk Level: {data['risk_level']}")
        print(f"   Risk Score: {data['risk_score']}")
        print(f"   Recommended Action: {data['recommended_action']}")
        print(f"   Urgency: {data['urgency_timeline']}")
        return True
    else:
        print(f"❌ Risk assessment failed: {response.status_code}")
        if response.text:
            print(f"   Error: {response.text}")
        return False

def test_complete_pipeline():
    """Test complete analysis pipeline"""
    print("\n🔄 Testing complete pipeline (analyze + assess)...")
    
    # Test data
    test_request = {
        "image_path": "test_images/00000003_007.png",
        "patient_code": "API_TEST_002",
        "additional_info": "Complete pipeline test"
    }
    
    response = requests.post(f"{BASE_URL}/analyze-and-assess", json=test_request)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Complete pipeline completed:")
        print(f"   Case ID: {data['case_id']}")
        print(f"   Radiology Confidence: {data['radiology_analysis']['confidence']}")
        print(f"   Risk Level: {data['risk_assessment']['risk_level']}")
        print(f"   Risk Score: {data['risk_assessment']['risk_score']}")
        return data['case_id']
    else:
        print(f"❌ Complete pipeline failed: {response.status_code}")
        if response.text:
            print(f"   Error: {response.text}")
        return None

def test_case_retrieval(case_id):
    """Test case retrieval endpoints"""
    print(f"\n📋 Testing case retrieval for {case_id}...")
    
    # Test case details
    response = requests.get(f"{BASE_URL}/cases/{case_id}")
    if response.status_code == 200:
        print("✅ Case details retrieved")
    else:
        print(f"❌ Case details failed: {response.status_code}")
    
    # Test risk assessment retrieval
    response = requests.get(f"{BASE_URL}/risk-assessments/{case_id}")
    if response.status_code == 200:
        print("✅ Risk assessment retrieved")
    else:
        print(f"❌ Risk assessment retrieval failed: {response.status_code}")

def main():
    """Run all API tests"""
    print("🧪 Multi-Agent AI API Endpoint Tests")
    print("=" * 50)
    
    # Test 1: Health check
    if not test_health_check():
        print("❌ API server not responding. Make sure to run: python start_api.py")
        return
    
    # Test 2: Statistics
    test_stats()
    
    # Test 3: Radiology analysis
    case_id_1 = test_analyze_endpoint()
    
    # Test 4: Risk assessment (if radiology worked)
    if case_id_1:
        test_risk_assessment(case_id_1)
        test_case_retrieval(case_id_1)
    
    # Test 5: Complete pipeline
    case_id_2 = test_complete_pipeline()
    if case_id_2:
        test_case_retrieval(case_id_2)
    
    print("\n🎉 API endpoint testing completed!")
    print("\n💡 To view results in database:")
    print("   python view_reports.py detailed")

if __name__ == "__main__":
    main()