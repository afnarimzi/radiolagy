#!/usr/bin/env python3
"""
Simple script to view saved radiology reports from database
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Load environment variables
load_dotenv()

def get_database_session():
    """Get database session"""
    database_url = os.getenv("DATABASE_URL", "sqlite:///./radiology_ai.db")
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def view_all_agent_reports(limit: int = 5):
    """View reports from ALL agents (radiology, risk, clinical, evidence)"""
    try:
        from app.database.models import PatientOutput, PatientInput, Patient
        from sqlalchemy import desc
        
        db = get_database_session()
        
        # Get all patient outputs (from all agents) with patient info
        outputs = db.query(PatientOutput, PatientInput, Patient).join(
            PatientInput, PatientOutput.case_id == PatientInput.case_id
        ).join(
            Patient, PatientInput.patient_id == Patient.id
        ).order_by(desc(PatientOutput.created_at)).limit(limit).all()
        
        if not outputs:
            print("📭 No agent reports found in database")
            return
        
        print(f"📊 Recent {len(outputs)} Agent Reports (All Types)")
        print("=" * 80)
        
        for i, (output, input_data, patient) in enumerate(outputs, 1):
            print(f"\n--- Report {i} ---")
            print(f"🆔 Case ID: {output.case_id}")
            print(f"👤 Patient: {patient.patient_code}")
            print(f"📅 Date: {output.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"🤖 Agent Type: {output.agent_type.upper()}")
            print(f"📊 Confidence: {output.confidence:.2f}")
            
            if input_data.image_path:
                print(f"🖼️  Image: {input_data.image_path}")
            
            # Display agent-specific information
            if output.agent_type == 'radiology':
                display_radiology_report(output)
            elif output.agent_type == 'risk':
                display_risk_assessment(output)
            else:
                print(f"🔍 Output Data: {str(output.output_data)[:200]}...")
            
            print("-" * 80)
        
        db.close()
            
    except Exception as e:
        print(f"❌ Error viewing agent reports: {str(e)}")
        import traceback
        traceback.print_exc()

def display_radiology_report(output):
    """Display radiology-specific report details"""
    if output.output_data:
        data = output.output_data
        
        if 'abnormalities' in data:
            abnormalities = data['abnormalities']
            if abnormalities:
                print(f"⚠️  Abnormalities: {len(abnormalities)} found")
                for abnormality in abnormalities:
                    print(f"   - {abnormality}")
        
        if 'findings' in data:
            findings = data['findings']
            print(f"🔍 Findings (first 300 chars): {findings[:300]}...")
        
        if 'recommendations' in data:
            print(f"💡 Recommendations: {data['recommendations']}")

def view_detailed_agent_reports(limit: int = 5):
    """View DETAILED reports from ALL agents with complete analysis"""
    try:
        from app.database.models import PatientOutput, PatientInput, Patient, MedicalReport
        from sqlalchemy import desc
        
        db = get_database_session()
        
        # Get all patient outputs with full details
        outputs = db.query(PatientOutput, PatientInput, Patient).join(
            PatientInput, PatientOutput.case_id == PatientInput.case_id
        ).join(
            Patient, PatientInput.patient_id == Patient.id
        ).order_by(desc(PatientOutput.created_at)).limit(limit).all()
        
        if not outputs:
            print("📭 No agent reports found in database")
            return
        
        print(f"📊 DETAILED Agent Reports ({len(outputs)} reports)")
        print("=" * 100)
        
        for i, (output, input_data, patient) in enumerate(outputs, 1):
            print(f"\n{'='*20} DETAILED REPORT {i} {'='*20}")
            print(f"🆔 Case ID: {output.case_id}")
            print(f"👤 Patient: {patient.patient_code}")
            print(f"📅 Date: {output.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"🤖 Agent Type: {output.agent_type.upper()}")
            print(f"📊 Confidence: {output.confidence:.2f}")
            print(f"⏱️  Processing Time: {output.processing_time:.2f}s" if output.processing_time else "")
            
            if input_data.image_path:
                print(f"🖼️  Image: {input_data.image_path}")
            
            if input_data.additional_info:
                print(f"ℹ️  Additional Info: {input_data.additional_info}")
            
            # Display FULL agent-specific information
            if output.agent_type == 'radiology':
                display_detailed_radiology_report(output)
            elif output.agent_type == 'risk':
                display_detailed_risk_assessment(output)
            else:
                print(f"🔍 Full Output Data:")
                print(f"   {output.output_data}")
            
            # Check for medical reports
            medical_report = db.query(MedicalReport).filter(
                MedicalReport.case_id == output.case_id
            ).first()
            
            if medical_report:
                print(f"\n📄 FORMATTED MEDICAL REPORT (Status: {medical_report.report_status}):")
                print("=" * 80)
                print(medical_report.report_content)
                print("=" * 80)
            
            print(f"\n{'='*60}")
        
        db.close()
            
    except Exception as e:
        print(f"❌ Error viewing detailed reports: {str(e)}")
        import traceback
        traceback.print_exc()

def display_detailed_radiology_report(output):
    """Display COMPLETE radiology report details"""
    if output.output_data:
        data = output.output_data
        
        print(f"\n🔍 COMPLETE RADIOLOGY ANALYSIS:")
        print("-" * 80)
        
        if 'image_quality' in data:
            print(f"🖼️  Image Quality: {data['image_quality']}")
        
        if 'anatomical_structures' in data:
            print(f"🫁 Anatomical Structures: {data['anatomical_structures']}")
        
        if 'abnormalities' in data:
            abnormalities = data['abnormalities']
            print(f"\n⚠️  ABNORMALITIES ({len(abnormalities)} found):")
            if abnormalities:
                for abnormality in abnormalities:
                    print(f"   • {abnormality}")
            else:
                print("   • No abnormalities detected")
        
        if 'findings' in data:
            findings = data['findings']
            print(f"\n📋 COMPLETE FINDINGS:")
            print(findings)
        
        if 'recommendations' in data:
            print(f"\n💡 RECOMMENDATIONS:")
            print(data['recommendations'])
        
        print("-" * 80)

def display_detailed_risk_assessment(output):
    """Display COMPLETE risk assessment details"""
    if output.output_data:
        data = output.output_data
        
        print(f"\n🚨 COMPLETE RISK ASSESSMENT:")
        print("-" * 80)
        
        print(f"🚨 Risk Level: {data.get('risk_level', 'Unknown').upper()}")
        print(f"📈 Risk Score: {data.get('risk_score', 0):.2f} / 1.0")
        print(f"🏥 Recommended Action: {data.get('recommended_action', 'Unknown').replace('_', ' ').title()}")
        print(f"⏰ Urgency Timeline: {data.get('urgency_timeline', 'Unknown')}")
        print(f"🔄 Follow-up Required: {'Yes' if data.get('follow_up_required', True) else 'No'}")
        
        if data.get('specialist_referral'):
            print(f"👨‍⚕️ Specialist Referral: {data['specialist_referral']}")
        
        if data.get('critical_findings'):
            print(f"\n⚠️  CRITICAL FINDINGS:")
            for finding in data['critical_findings']:
                print(f"   • {finding}")
        
        if data.get('risk_factors'):
            print(f"\n📊 RISK FACTORS:")
            for factor in data['risk_factors']:
                print(f"   • {factor}")
        
        if data.get('next_steps'):
            print(f"\n📋 RECOMMENDED NEXT STEPS:")
            for i, step in enumerate(data['next_steps'], 1):
                print(f"   {i}. {step}")
        
        reasoning = data.get('reasoning', '')
        if reasoning:
            print(f"\n🤔 AI MEDICAL REASONING:")
            print(f"   {reasoning}")
        
        if data.get('timestamp'):
            print(f"\n📅 Assessment Timestamp: {data['timestamp']}")
        
        print("-" * 80)

def view_recent_reports(limit: int = 10):
    """View recent radiology reports"""
    try:
        from app.database.crud import RadiologyDB
        
        db = get_database_session()
        radiology_db = RadiologyDB(db)
        
        cases = radiology_db.get_recent_cases(limit=limit)
        
        if not cases:
            print("📭 No reports found in database")
            print("\n💡 To generate reports:")
            print("   1. Run: python3 main.py")
            print("   2. This will analyze the test images and save to database")
            return
        
        print(f"📊 Recent {len(cases)} Radiology Reports")
        print("=" * 80)
        
        for i, case in enumerate(cases, 1):
            print(f"\n--- Report {i} ---")
            print(f"🆔 Case ID: {case['case_id']}")
            print(f"👤 Patient: {case['patient_code']}")
            print(f"📅 Date: {case['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Image info
            if case['image_path']:
                print(f"🖼️  Image: {case['image_path']}")
            
            # Analysis results
            if case['output_data']:
                output = case['output_data']
                print(f"📊 Confidence: {case['confidence']:.2f}")
                
                if 'abnormalities' in output:
                    abnormalities = output['abnormalities']
                    print(f"⚠️  Abnormalities: {len(abnormalities)} found")
                    if abnormalities:
                        print(f"   - {', '.join(abnormalities)}")
                
                if 'findings' in output:
                    findings = output['findings']
                    print(f"🔍 Findings (first 300 chars): {findings[:300]}{'...' if len(findings) > 300 else ''}")
                
                if 'recommendations' in output:
                    print(f"💡 Recommendations: {output['recommendations']}")
            
            # Report content
            if case['report_content']:
                print(f"📄 Report Status: {case['report_status']}")
                print(f"📝 Full Medical Report:")
                print("=" * 60)
                print(case['report_content'])
                print("=" * 60)
            
            print("-" * 80)
        
        db.close()
            
    except Exception as e:
        print(f"❌ Error viewing reports: {str(e)}")
        import traceback
        traceback.print_exc()

def view_patient_reports(patient_code: str):
    """View all reports for a specific patient"""
    try:
        from app.database.crud import RadiologyDB
        
        db = get_database_session()
        radiology_db = RadiologyDB(db)
        
        cases = radiology_db.get_patient_cases(patient_code)
        
        if not cases:
            print(f"📭 No reports found for patient: {patient_code}")
            return
        
        print(f"📊 Full Reports for Patient: {patient_code}")
        print("=" * 80)
        
        for i, case in enumerate(cases, 1):
            print(f"\n{'='*15} REPORT {i} ({case['created_at'].strftime('%Y-%m-%d')}) {'='*15}")
            print(f"🆔 Case ID: {case['case_id']}")
            
            if case['image_path']:
                print(f"🖼️  Image: {case['image_path']}")
            
            if case['output_data']:
                output = case['output_data']
                print(f"📊 Confidence: {case['confidence']:.2f}")
                
                if 'abnormalities' in output:
                    abnormalities = output['abnormalities']
                    print(f"⚠️  Abnormalities: {len(abnormalities)} found")
                    if abnormalities:
                        for abnormality in abnormalities:
                            print(f"   - {abnormality}")
                
                print(f"\n🔍 COMPLETE RADIOLOGY ANALYSIS:")
                print("-" * 70)
                if 'findings' in output:
                    print(output['findings'])
                print("-" * 70)
                
                if 'recommendations' in output:
                    print(f"\n💡 Recommendations: {output['recommendations']}")
            
            if case['report_content']:
                print(f"\n📄 FORMATTED MEDICAL REPORT (Status: {case['report_status']}):")
                print("=" * 70)
                print(case['report_content'])
                print("=" * 70)
            
            print(f"\n{'='*60}")
        
        db.close()
            
    except Exception as e:
        print(f"❌ Error viewing patient reports: {str(e)}")

def view_database_stats():
    """View database statistics"""
    try:
        from app.database.models import Patient, PatientInput, PatientOutput, MedicalReport
        
        db = get_database_session()
        
        # Count records
        total_patients = db.query(Patient).count()
        total_inputs = db.query(PatientInput).count()
        total_outputs = db.query(PatientOutput).count()
        total_reports = db.query(MedicalReport).count()
        
        print("📈 Database Statistics")
        print("=" * 30)
        print(f"👥 Total Patients: {total_patients}")
        print(f"📥 Total Cases (Inputs): {total_inputs}")
        print(f"📤 Total Analysis Results: {total_outputs}")
        print(f"📄 Total Reports: {total_reports}")
        
        if total_outputs > 0:
            # Get confidence stats
            outputs = db.query(PatientOutput).all()
            confidences = [o.confidence for o in outputs]
            avg_confidence = sum(confidences) / len(confidences)
            
            print(f"📊 Average Confidence: {avg_confidence:.2f}")
            
            # Count abnormalities
            total_abnormalities = 0
            for output in outputs:
                if output.output_data and 'abnormalities' in output.output_data:
                    total_abnormalities += len(output.output_data['abnormalities'])
            
            print(f"⚠️  Total Abnormalities Found: {total_abnormalities}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error viewing database stats: {str(e)}")

def view_specific_case(case_id: str):
    """View details of a specific case"""
    try:
        from app.database.crud import RadiologyDB
        
        db = get_database_session()
        radiology_db = RadiologyDB(db)
        
        case = radiology_db.get_complete_case(case_id)
        
        if not case:
            print(f"📭 No case found with ID: {case_id}")
            return
        
        print(f"📊 Case Details: {case_id}")
        print("=" * 60)
        
        print(f"👤 Patient: {case['patient_code']}")
        print(f"📅 Created: {case['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        if case['image_path']:
            print(f"🖼️  Image: {case['image_path']}")
        
        print(f"\n📥 Input Data:")
        if case['input_data']:
            for key, value in case['input_data'].items():
                print(f"   {key}: {value}")
        
        if case['additional_info']:
            print(f"   Additional Info: {case['additional_info']}")
        
        print(f"\n📤 Analysis Results:")
        if case['output_data']:
            print(f"   Confidence: {case['confidence']:.2f}")
            if case['processing_time']:
                print(f"   Processing Time: {case['processing_time']:.2f}s")
            
            output = case['output_data']
            for key, value in output.items():
                if key == 'abnormalities' and isinstance(value, list):
                    print(f"   {key}: {', '.join(value) if value else 'None'}")
                else:
                    print(f"   {key}: {value}")
        
        if case['report_content']:
            print(f"\n📄 Medical Report ({case['report_status']}):")
            print(f"   {case['report_content']}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error viewing case: {str(e)}")

def main():
    """Main function"""
    print("🏥 Multi-Agent AI - Database Viewer")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "stats":
            view_database_stats()
        elif command == "patient" and len(sys.argv) > 2:
            patient_code = sys.argv[2]
            view_patient_reports(patient_code)
        elif command == "recent":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            view_recent_reports(limit)
        elif command == "case" and len(sys.argv) > 2:
            case_id = sys.argv[2]
            view_specific_case(case_id)
        elif command == "full":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            view_full_reports(limit)
        elif command == "agents" or command == "all":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            view_all_agent_reports(limit)
        elif command == "detailed" or command == "detail":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            view_detailed_agent_reports(limit)
        else:
            print("Usage:")
            print("  python3 view_reports.py                   - View ALL agent reports (summary)")
            print("  python3 view_reports.py detailed [limit]  - View DETAILED agent reports (full analysis)")
            print("  python3 view_reports.py agents [limit]    - View ALL agent reports (summary)")
            print("  python3 view_reports.py recent [limit]    - View recent radiology reports only")
            print("  python3 view_reports.py patient <code>    - View patient reports")
            print("  python3 view_reports.py case <case_id>    - View specific case")
            print("  python3 view_reports.py stats             - View database stats")
            print("  python3 view_reports.py full              - View full detailed radiology reports")
    else:
        # Default: show ALL agent reports (radiology + risk + others)
        view_all_agent_reports()

if __name__ == "__main__":
    main()