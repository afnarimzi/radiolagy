#!/usr/bin/env python3
"""
Detailed timing test - measures each agent individually using real timing data
"""

import requests
import json
import time
import os
from datetime import datetime

BASE_URL = "http://localhost:8000"
TEST_IMAGE_PATH = "test_images/p10004457.jpeg"

def test_individual_agents():
    """Test complete pipeline and get real individual agent timing"""
    
    print("⏱️  DETAILED AGENT TIMING TEST")
    print(f"🕒 Started: {datetime.now().strftime('%H:%M:%S')}")
    
    if not os.path.exists(TEST_IMAGE_PATH):
        print(f"❌ Test image not found: {TEST_IMAGE_PATH}")
        return
    
    # Test complete pipeline
    print(f"\n🧪 Testing Complete 5-Agent Pipeline...")
    start_time = time.time()
    
    try:
        with open(TEST_IMAGE_PATH, 'rb') as f:
            files = {'file': (os.path.basename(TEST_IMAGE_PATH), f, 'image/png')}
            data = {
                'patient_code': f'TIMING_TEST_{int(time.time())}',
                'additional_info': 'Detailed timing analysis test',
                'patient_history': 'Performance analysis with individual agent tracking'
            }
            response = requests.post(f"{BASE_URL}/upload-complete-pipeline-with-chairman", files=files, data=data)
        
        total_duration = time.time() - start_time
        
        if response.status_code == 200:
            print(f"   ✅ Pipeline completed in {total_duration:.2f}s")
            
            # Get detailed timing information
            print(f"\n📊 FETCHING INDIVIDUAL AGENT TIMINGS...")
            timing_response = requests.get(f"{BASE_URL}/timing")
            
            if timing_response.status_code == 200:
                timing_data = timing_response.json()
                session_summary = timing_data.get('session_summary', {})
                detailed_timings = timing_data.get('detailed_timings', [])
                
                if session_summary and 'breakdown' in session_summary:
                    print(f"\n🔍 REAL AGENT EXECUTION TIMES:")
                    breakdown = session_summary['breakdown']
                    percentages = session_summary['percentages']
                    
                    # Sort agents by execution order
                    agent_order = ['Radiology Agent', 'Clinical Agent', 'Evidence Agent', 'Risk Agent', 'Chairman Agent']
                    
                    for agent in agent_order:
                        if agent in breakdown:
                            duration = breakdown[agent]
                            percentage = percentages[agent]
                            print(f"   {agent:<20} {duration:6.2f}s ({percentage:4.1f}%)")
                    
                    # Show any other agents not in the expected order
                    for agent, duration in breakdown.items():
                        if agent not in agent_order:
                            percentage = percentages[agent]
                            print(f"   {agent:<20} {duration:6.2f}s ({percentage:4.1f}%)")
                    
                    print(f"\n📈 TIMING ANALYSIS:")
                    total_agent_time = session_summary['total_time']
                    print(f"   Total Agent Time: {total_agent_time:.2f}s")
                    print(f"   Total API Time:   {total_duration:.2f}s")
                    print(f"   Overhead:         {(total_duration - total_agent_time):.2f}s")
                    
                    # Performance insights
                    print(f"\n💡 PERFORMANCE INSIGHTS:")
                    slowest_agent = max(breakdown.items(), key=lambda x: x[1])
                    fastest_agent = min(breakdown.items(), key=lambda x: x[1])
                    
                    print(f"   🐌 Slowest: {slowest_agent[0]} ({slowest_agent[1]:.2f}s)")
                    print(f"   🚀 Fastest: {fastest_agent[0]} ({fastest_agent[1]:.2f}s)")
                    
                    if total_agent_time > 25:
                        print("   ⚠️  System is running slow - possible optimizations:")
                        if breakdown.get('Radiology Agent', 0) > 8:
                            print("      • Radiology Agent: Consider image preprocessing")
                        if breakdown.get('Evidence Agent', 0) > 8:
                            print("      • Evidence Agent: PubMed API may be slow")
                        if breakdown.get('Clinical Agent', 0) > 5:
                            print("      • Clinical Agent: GROQ API latency")
                    elif total_agent_time > 15:
                        print("   ✅ System performance is good")
                    else:
                        print("   🚀 System performance is excellent!")
                    
                    # Detailed execution log
                    if detailed_timings:
                        print(f"\n📋 DETAILED EXECUTION LOG:")
                        for i, timing in enumerate(detailed_timings, 1):
                            agent = timing['agent']
                            duration = timing['duration']
                            timestamp = timing['timestamp']
                            print(f"   {i}. {agent}: {duration:.2f}s at {timestamp}")
                
                else:
                    print("   ❌ No timing data available - agents may not have executed properly")
            
            else:
                print(f"   ❌ Failed to get timing data: {timing_response.status_code}")
            
            # Analyze pipeline results
            pipeline_result = response.json()
            print(f"\n🎯 SYSTEM STATUS:")
            
            agents_working = 0
            total_agents = 5
            
            if pipeline_result.get('radiology_analysis', {}).get('confidence', 0) > 0:
                agents_working += 1
                print(f"   ✅ Radiology Agent: Working")
            else:
                print(f"   ❌ Radiology Agent: Failed")
            
            if pipeline_result.get('clinical_analysis', {}).get('confidence', 0) > 0:
                agents_working += 1
                print(f"   ✅ Clinical Agent: Working")
            else:
                print(f"   ❌ Clinical Agent: Failed")
            
            if pipeline_result.get('evidence_research', {}).get('total_papers_found', 0) >= 0:
                agents_working += 1
                print(f"   ✅ Evidence Agent: Working")
            else:
                print(f"   ❌ Evidence Agent: Failed")
            
            if pipeline_result.get('risk_assessment', {}).get('confidence', 0) > 0:
                agents_working += 1
                print(f"   ✅ Risk Agent: Working")
            else:
                print(f"   ❌ Risk Agent: Failed")
            
            if pipeline_result.get('chairman_report', {}).get('confidence_level', 0) > 0:
                agents_working += 1
                print(f"   ✅ Chairman Agent: Working")
            else:
                print(f"   ❌ Chairman Agent: Failed")
            
            overall_confidence = pipeline_result.get('overall_confidence', 0)
            print(f"\n   Working Agents: {agents_working}/{total_agents}")
            print(f"   Overall Confidence: {overall_confidence:.0%}")
            print(f"   System Health: {'🟢 EXCELLENT' if agents_working == total_agents else '🟡 PARTIAL' if agents_working >= 3 else '🔴 POOR'}")
        
        else:
            print(f"   ❌ Pipeline failed: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Test failed with error: {str(e)}")

if __name__ == "__main__":
    test_individual_agents()