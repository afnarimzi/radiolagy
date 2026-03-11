# Multi-Agent AI Medical Analysis System

A collaborative multi-agent system for medical image analysis and risk assessment using AI models.

## 🏗️ Project Structure

```
├── app/
│   ├── agents/           # AI Agent implementations
│   │   ├── radiology_agent.py    # ✅ Radiology analysis (Gemini Vision)
│   │   ├── risk_agent.py         # ✅ Risk assessment (Gemini)
│   │   ├── clinical_agent.py     # 🚧 Placeholder for clinical analysis
│   │   └── evidence_agent.py     # 🚧 Placeholder for evidence synthesis
│   ├── models/           # Data models for each agent
│   │   ├── radiology_models.py   # ✅ Radiology data structures
│   │   ├── risk_models.py        # ✅ Risk assessment models
│   │   ├── clinical_models.py    # 🚧 Placeholder for clinical models
│   │   └── evidence_models.py    # 🚧 Placeholder for evidence models
│   ├── database/         # Database layer
│   │   ├── models.py            # Database schema
│   │   ├── crud.py              # Database operations
│   │   ├── database.py          # Database connection
│   │   └── init_db.py           # Database initialization
│   └── api/              # FastAPI REST endpoints
│       ├── main.py              # API server
│       └── models.py            # API request/response models
├── test_images/          # Sample medical images for testing
├── main.py              # Main application entry point
├── start_api.py         # API server launcher
├── setup_database.py    # Database setup script
├── view_reports.py      # Database viewer utility
├── requirements.txt     # Python dependencies
└── .env                 # Environment variables (API keys)
```

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone <repository-url>
cd <project-name>
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment
Create/update `.env` file with your API keys:
```env
# Radiology Agent (Gemini Vision)
GOOGLE_API_KEY=your_radiology_gemini_key_here

# Risk Agent (Gemini)
RISK_AGENT_API_KEY=your_risk_gemini_key_here

# Database
DATABASE_URL=sqlite:///./radiology_ai.db

# Add your agent API keys here:
# CLINICAL_AGENT_API_KEY=your_clinical_key_here
# EVIDENCE_AGENT_API_KEY=your_evidence_key_here
```

### 3. Initialize Database
```bash
python setup_database.py
```

### 4. Run Analysis
```bash
# Analyze test images with existing agents
python main.py

# Start API server
python start_api.py

# View results
python view_reports.py detailed
```

## 🤖 Implemented Agents

### ✅ Radiology Agent
- **File**: `app/agents/radiology_agent.py`
- **Model**: Google Gemini Vision Pro
- **Function**: Analyzes medical images (X-rays, CT scans)
- **Output**: Abnormalities, findings, recommendations

### ✅ Risk Agent
- **File**: `app/agents/risk_agent.py`
- **Model**: Google Gemini Pro
- **Function**: Assesses medical risk from radiology findings
- **Output**: Risk level, urgency, next steps, specialist referrals

## 🚧 Placeholder Agents (Ready for Implementation)

### Clinical Agent
- **File**: `app/agents/clinical_agent.py` (placeholder)
- **Models**: `app/models/clinical_models.py` (placeholder)
- **Purpose**: Clinical decision support and treatment recommendations

### Evidence Agent
- **File**: `app/agents/evidence_agent.py` (placeholder)
- **Models**: `app/models/evidence_models.py` (placeholder)
- **Purpose**: Evidence-based medicine synthesis and literature review

## 📊 Database Schema

The system uses a unified database with these tables:
- `patients` - Patient information
- `patient_inputs` - Input data (images, clinical info)
- `patient_outputs` - Agent analysis results
- `agent_threads` - Multi-agent conversation tracking
- `medical_reports` - Formatted medical reports

Each agent saves results with `agent_type` field for identification.

## 🔧 Adding New Agents

### 1. Implement Agent Class
Create your agent in `app/agents/your_agent.py`:
```python
from app.models.your_models import YourRequest, YourResponse
from app.database.models import PatientOutput
import uuid
from datetime import datetime

class YourAgent:
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def analyze(self, request: YourRequest) -> YourResponse:
        # Your AI model implementation
        pass
    
    def save_to_database(self, db, case_id: str, response: YourResponse):
        # Save results to database
        output = PatientOutput(
            case_id=case_id,
            agent_type="your_agent",  # Unique identifier
            output_data=response.dict(),
            confidence=response.confidence,
            processing_time=response.processing_time,
            created_at=datetime.utcnow()
        )
        db.add(output)
        db.commit()
```

### 2. Define Data Models
Create models in `app/models/your_models.py`:
```python
from pydantic import BaseModel
from typing import List, Optional

class YourRequest(BaseModel):
    # Input data structure
    pass

class YourResponse(BaseModel):
    # Output data structure
    confidence: float
    processing_time: Optional[float] = None
```

### 3. Update Main Pipeline
Add your agent to `main.py`:
```python
from app.agents.your_agent import YourAgent

# Initialize your agent
your_agent = YourAgent(api_key=os.getenv("YOUR_AGENT_API_KEY"))

# Add to analysis pipeline
your_result = your_agent.analyze(your_request)
your_agent.save_to_database(db, case_id, your_result)
```

### 4. Update Report Viewer
Add display logic in `view_reports.py`:
```python
elif output.agent_type == 'your_agent':
    display_your_agent_report(output)
```

## 🔍 Viewing Results

```bash
# View all agent reports (summary)
python view_reports.py

# View detailed reports with full analysis
python view_reports.py detailed

# View specific patient reports
python view_reports.py patient PATIENT_001

# View database statistics
python view_reports.py stats
```

## 🌐 API Endpoints

Start the API server: `python start_api.py`

### General Endpoints
- `GET /` - API information and status
- `GET /health` - Health check for all agents
- `GET /stats` - Database statistics

### Patient Management
- `POST /patients` - Create new patient
- `GET /patients/{patient_code}` - Get patient info
- `GET /patients/{patient_code}/cases` - Get patient cases

### Radiology Analysis
- `POST /analyze` - Analyze X-ray image
- `POST /upload-analyze` - Upload and analyze image
- `GET /radiology-results/{case_id}` - Get radiology results

### Risk Assessment
- `POST /assess-risk` - Assess medical risk from findings
- `POST /analyze-and-assess` - Complete pipeline (radiology + risk)
- `GET /risk-assessments/{case_id}` - Get risk assessment results
- `GET /pending-risk-cases` - Cases needing risk assessment

### Case Management
- `GET /cases` - List all cases
- `GET /cases/{case_id}` - Get specific case details
- `GET /pending-clinical-cases` - Cases needing clinical analysis

### Reports
- `GET /reports/{case_id}` - Get formatted medical report
- `GET /reports` - List recent reports

## 🤝 Collaboration Notes

- Each agent operates independently and saves to the same database
- Use unique `agent_type` identifiers for your agents
- Follow the existing pattern for database integration
- Add your API keys to `.env` file
- Test with sample data before processing real medical images

## 📝 Current Status

- ✅ Database schema and CRUD operations
- ✅ Radiology agent with Gemini Vision
- ✅ Risk assessment agent with Gemini
- ✅ FastAPI server with endpoints
- ✅ Multi-agent report viewer
- 🚧 Clinical agent (placeholder ready)
- 🚧 Evidence agent (placeholder ready)

Ready for collaborative development! 🚀