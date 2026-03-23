
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_db():
    db = SessionLocal()
    with open("c:\\MM_internship\\radilolagy\\MM-DUK-Interns\\check_db_output.txt", "w") as f:
        try:
            from app.database.models import PatientOutput, PatientInput, Patient
            
            f.write("--- Recent Patient Inputs ---\n")
            inputs = db.query(PatientInput).order_by(PatientInput.created_at.desc()).limit(10).all()
            for i in inputs:
                patient = db.query(Patient).filter(Patient.id == i.patient_id).first()
                p_code = patient.patient_code if patient else "N/A"
                f.write(f"CASE_ID: {i.case_id} | PATIENT: {p_code} | CREATED: {i.created_at}\n")
                
            f.write("\n--- Recent Patient Outputs ---\n")
            outputs = db.query(PatientOutput).order_by(PatientOutput.created_at.desc()).limit(30).all()
            for o in outputs:
                data_str = str(o.output_data)[:200]
                f.write(f"CASE_ID: {o.case_id} | AGENT: {o.agent_type} | DATA: {data_str}...\n")
                
        except Exception as e:
            f.write(f"ERROR: {e}\n")
        finally:
            db.close()
    print("Done writing to check_db_output.txt")

if __name__ == "__main__":
    check_db()
