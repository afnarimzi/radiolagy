# 🏥 Multi-Agent Medical AI System

A comprehensive medical AI system that orchestrates 5 specialized AI agents using **LangGraph** to provide complete medical analysis from X-ray images.




### 🤖 AI Agents

1. **🔬 Radiology Agent** - X-ray image analysis using Google Gemini Vision
2. **🩺 Clinical Agent** - Differential diagnosis using GROQ Llama 3.1
3. **📚 Evidence Agent** - PubMed literature research using GROQ + PubMed API
4. **⚠️ Risk Agent** - Risk assessment using Google Gemini
5. **👔 Chairman Agent** - Final report synthesis using GROQ Llama 3.1


## 📁 Project Structure

```
llmCouncil/
├── app/
│   ├── agents/           # 5 AI agents
│   │   ├── radiology_agent.py    # Gemini Vision for X-ray analysis
│   │   ├── clinical_agent.py     # GROQ for clinical reasoning
│   │   ├── evidence_agent.py     # GROQ + PubMed for research
│   │   ├── risk_agent.py         # Gemini for risk assessment
│   │   └── chairman_agent.py     # GROQ for final synthesis
│   ├── api/              # FastAPI web interface
│   │   └── main.py       # REST API endpoints
│   ├── database/         # PostgreSQL operations
│   │   ├── models.py     # Database schemas
│   │   ├── crud.py       # Database operations
│   │   └── database.py   # Connection management
│   ├── models/           # Pydantic data models
│   │   ├── radiology_models.py
│   │   ├── clinical_models.py
│   │   ├── evidence_models.py
│   │   ├── risk_models.py
│   │   └── chairman_models.py
│   ├── orchestration/    # LangGraph pipeline orchestration ✨
│   │   └── pipeline.py   # StateGraph coordination
│   └── utils/            # Utilities
│       └── simple_timer.py # Performance tracking
├── test_detailed_timing.py   # Performance testing
├── start_api.py             # API server launcher
├── requirements.txt         # Dependencies
└── .env                    # API keys configuration
```

## 🛠️ Installation & Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd llmCouncil
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API Keys
Create `.env` file with your API keys:
```env
# Google Gemini API (for Radiology & Risk agents)
GOOGLE_API_KEY=your_google_api_key_here

# GROQ API (for Clinical, Evidence & Chairman agents)
GROQ_API_KEY=your_groq_api_key_here

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/medical_ai
```

### 5. Setup Database
```bash
# Install PostgreSQL and create database
createdb medical_ai

# Initialize database tables
python -c "from app.database.init_db import init_database; init_database()"
```

## 🚀 Usage

### Start the API Server
```bash
python3 start_api.py
```

The server will start at `http://localhost:8000`

#
