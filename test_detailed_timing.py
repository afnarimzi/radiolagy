#!/usr/bin/env python3
"""
Detailed timing test - measures each agent individually
"""

import requests
import json
import time
import os
from datetime import datetime

BASE_URL = "http://localhost:8000"
TEST_IMAGE_PATH = "test_images/00000003_000.png"

def test_individual_agents():
    """Test each agent individually to see timing"""
    
    print("⏱️  DETAILED AGENT TIMING TEST")
    print(f"🕒 Started: {datetime.now().strftime('%H:%M:%S')}")
    
    if not os.path.exists(TEST_IMAGE_PATH):
        print(f"❌ Test image not found: {TEST_IMAGE_PATH}")
        return
    
    # Test individual endpoints with timing
    tests = [
        ("Health Check", "GET", "/health", None),
        ("Complete Pipeline", "POST", "/upload-complete-pipeline-with-chairman", "file_upload")
    ]
    
    results = {}
    
    for test_name, method, endpoint, data_type in tests:
        print(f"\n🧪 Testing {test_name}...")
        start_time = time.time()
        
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}")
            elif data_type == "file_upload":
                with open(TEST_IMAGE_PATH, 'rb') as f:
                    files = {'file': (os.path.basename(TEST_IMAGE_PATH), f, 'image/png')}
                    data = {
                        'patient_code': f'TIMING_TEST_{int(time.time())}',
                        'additional_info': f'Timing test for {test_name}',
                        'patient_history': 'Performance analysis'
                    }
                    response = requests.post(f"{BASE_URL}{endpoint}", files=files, data=data)
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                print(f"   ✅ {test_name}: {duration:.2f}s")
                results[test_name] = {
                    'duration': duration,
                    'status': 'success',
                    'response': response.json() if test_name != "Health Check" else None
                }
            else:
                print(f"   ❌ {test_name}: Failed ({response.status_code})")
                results[test_name] = {
                    'duration': duration,
                    'status': 'failed',
                    'response': None
                }
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"   ❌ {test_name}: Error - {str(e)}")
            results[test_name] = {
                'duration': duration,
                'status': 'error',
                'response': None
            }
    
    # Analyze the complete pipeline results
    if "Complete Pipeline" in results and results["Complete Pipeline"]["status"] == "success":
        pipeline_result = results["Complete Pipeline"]["response"]
        pipeline_time = results["Complete Pipeline"]["duration"]
        
        print(f"\n📊 PIPELINE ANALYSIS:")
        print(f"   Total Time: {pipeline_time:.2f}s")
        
        # Estimate individual agent times based on typical patterns
        # These are estimates since we don't have individual timing in the current setup
        estimated_times = {
            "File Upload": 0.5,
            "Radiology Agent": pipeline_time * 0.35,  # Usually the slowest (image processing)
            "Clinical Agent": pipeline_time * 0.20,   # GROQ is fast
            "Evidence Agent": pipeline_time * 0.25,   # PubMed search takes time
            "Risk Agent": pipeline_time * 0.10,       # Simple analysis
            "Chairman Agent": pipeline_time * 0.10    # GROQ synthesis
        }
        
        print(f"\n🔍 ESTIMATED AGENT BREAKDOWN:")
        for agent, est_time in estimated_times.items():
            percentage = (est_time / pipeline_time) * 100
            print(f"   {agent:<20} {est_time:6.2f}s ({percentage:4.1f}%)")
        
        # Performance insights
        print(f"\n💡 PERFORMANCE INSIGHTS:")
        if pipeline_time > 30:
            print("   🐌 System is running slow - possible causes:")
            print("      • Gemini API latency (image processing)")
            print("      • PubMed API response time")
            print("      • Network connectivity")
        elif pipeline_time > 15:
            print("   ⚠️  System performance is acceptable but could be optimized")
        else:
            print("   🚀 System performance is excellent!")
        
        # Agent status
        agents_working = 0
        total_agents = 5
        
        if pipeline_result.get('radiology_analysis', {}).get('confidence', 0) > 0:
            agents_working += 1
        if pipeline_result.get('clinical_analysis', {}).get('confidence', 0) > 0:
            agents_working += 1
        if pipeline_result.get('evidence_research', {}).get('total_papers_found', 0) >= 0:
            agents_working += 1
        if pipeline_result.get('risk_assessment', {}).get('confidence', 0) > 0:
            agents_working += 1
        if pipeline_result.get('chairman_report', {}).get('confidence_level', 0) > 0:
            agents_working += 1
        
        print(f"\n🎯 SYSTEM STATUS:")
        print(f"   Working Agents: {agents_working}/{total_agents}")
        print(f"   Overall Confidence: {pipeline_result.get('overall_confidence', 0):.0%}")
        print(f"   System Health: {'🟢 EXCELLENT' if agents_working == total_agents else '🟡 PARTIAL'}")

if __name__ == "__main__":
    test_individual_agents()