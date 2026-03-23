"""
Database initialization and setup with automatic migrations
"""
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

from app.database.database import Base, get_db
from app.database.models import Patient, PatientInput, PatientOutput, AgentThread, MedicalReport

# Load environment variables
load_dotenv()

def check_and_migrate_database(engine):
    """Check database schema and apply migrations if needed"""
    print("🔍 Checking database schema...")
    
    try:
        inspector = inspect(engine)
        
        # Check if patient_inputs table exists
        if 'patient_inputs' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('patient_inputs')]
            
            # Check if thread_id column exists
            if 'thread_id' not in columns:
                print("🔧 Adding missing thread_id column to patient_inputs table...")
                with engine.connect() as conn:
                    # Add thread_id column
                    conn.execute(text("""
                        ALTER TABLE patient_inputs 
                        ADD COLUMN thread_id VARCHAR(100) NULL
                    """))
                    
                    # Create index on thread_id (PostgreSQL syntax)
                    if 'postgresql' in str(engine.url):
                        conn.execute(text("""
                            CREATE INDEX IF NOT EXISTS idx_patient_inputs_thread_id 
                            ON patient_inputs(thread_id)
                        """))
                    
                    conn.commit()
                    print("✅ thread_id column added successfully!")
            else:
                print("✅ Database schema is up to date!")
        else:
            print("📋 Creating new database tables...")
            
    except Exception as e:
        print(f"⚠️  Migration check failed: {str(e)}")
        print("🔄 Proceeding with table creation...")

def init_database():
    """Initialize the database with all tables and migrations"""
    
    # Get database URL from environment or use SQLite default
    database_url = os.getenv("DATABASE_URL", "sqlite:///./radiology_ai.db")
    print(f"🔗 Connecting to database: {database_url}")
    
    # Create engine
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
    )
    
    # Check and apply migrations first
    check_and_migrate_database(engine)
    
    # Create all tables (this is safe - won't overwrite existing tables)
    print("📋 Creating/updating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")
    
    # Create session for testing
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return engine, SessionLocal

def test_database_connection():
    """Test database connection and basic operations"""
    try:
        engine, SessionLocal = init_database()
        
        # Test basic operations
        db = SessionLocal()
        
        # Test creating a patient
        from app.database.crud import RadiologyDB
        radiology_db = RadiologyDB(db)
        
        # Create test patient
        test_patient = radiology_db.get_or_create_patient("TEST_001")
        print(f"✅ Test patient created: {test_patient.patient_code}")
        
        # Create test case with thread_id
        test_case = radiology_db.create_case_input_with_thread(
            case_id="TEST_CASE_001",
            patient_code="TEST_001",
            input_data={"test": "data"},
            thread_id="TEST_THREAD_001",
            image_path="/test/path.jpg"
        )
        print(f"✅ Test case created: {test_case.case_id} with thread: {test_case.thread_id}")
        
        # Save test output
        test_output = radiology_db.save_analysis_output(
            case_id="TEST_CASE_001",
            output_data={"findings": "test findings"},
            confidence=0.85
        )
        print(f"✅ Test output saved with confidence: {test_output.confidence}")
        
        # Create test report
        test_report = radiology_db.create_medical_report(
            case_id="TEST_CASE_001",
            report_content="Test radiology report content"
        )
        print(f"✅ Test report created: {test_report.report_type}")
        
        # Get complete case
        complete_case = radiology_db.get_complete_case("TEST_CASE_001")
        print(f"✅ Complete case retrieved: {complete_case['case_id']}")
        
        db.close()
        print("✅ Database connection test successful!")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Initializing Radiology AI Database...")
    
    # Initialize database
    engine, SessionLocal = init_database()
    
    # Test connection
    print("\n🧪 Testing database connection...")
    success = test_database_connection()
    
    if success:
        print("\n✅ Database setup completed successfully!")
        print("\nDatabase tables created:")
        print("- patients (Patient ID storage)")
        print("- patient_inputs (Patient input data)")
        print("- patient_outputs (Radiology analysis results)")
        print("- agent_threads (Agent report tracking)")
        print("- medical_reports (Final medical reports)")
    else:
        print("\n❌ Database setup failed!")
        exit(1)