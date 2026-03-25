# 🏥 Multi-Agent Medical AI System

A  AI-powered medical analysis platform that leverages multiple specialized agents to provide comprehensive X-ray analysis, clinical diagnosis, evidence-based research, risk assessment, and final medical reporting.

## 🌟 Features

- **🔬 Radiology Agent**: Advanced X-ray image analysis 
- **🩺 Clinical Agent**: Differential diagnosis generation and clinical reasoning
- **📚 Evidence Agent**: Medical literature search and evidence-based recommendations
- **⚠️ Risk Agent**: Comprehensive risk assessment and urgency evaluation
- **👔 Chairman Agent**: Senior medical officer synthesis and final reporting

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend API   │    │   Database      │
│   (React)       │◄──►│   (FastAPI)      │◄──►│  (PostgreSQL)   │
│   Port: 3000    │    │   Port: 8000     │    │   Port: 5433    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                       ┌────────┴────────┐
                       │   AI Agents     │
                       │   Pipeline      │
                       └─────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
   ┌────▼────┐         ┌────────▼────────┐         ┌────▼────┐
   │Radiology│         │   Parallel      │         │Chairman │
   │ Agent   │────────►│   Processing    │────────►│ Agent   │
   │         │         │                 │         │         │
   └─────────┘         │ ┌─────────────┐ │         └─────────┘
                       │ │Clinical     │ │
                       │ │Agent        │ │
                       │ └─────────────┘ │
                       │ ┌─────────────┐ │
                       │ │Evidence     │ │
                       │ │Agent        │ │
                       │ └─────────────┘ │
                       │ ┌─────────────┐ │
                       │ │Risk         │ │
                       │ │Agent        │ │
                       │ └─────────────┘ │
                       └─────────────────┘
```

## 🚀 Quick Start (Docker - Recommended)

### Prerequisites
- Docker and Docker Compose
- API Keys (Google Gemini, GROQ)

### 1. Clone Repository
```bash
git clone <repository-url>
cd llmCouncil
```

### 2. Configure Environment
```bash
cp .env.template .env
# Edit .env with your API keys
```

### 3. Start Services
```bash
docker-compose up -d
```

### 4. Access Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🛠️ Manual Installation

### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL 13+
- Redis (optional)

### Backend Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.template .env
# Edit .env with your configuration

# Initialize database
python -c "from app.database.init_db import init_database; init_database()"

# Start backend
python start_api.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following configuration:

```env
# Google Gemini API Configuration
GOOGLE_API_KEY=your_radiology_gemini_api_key_here
RISK_AGENT_API_KEY=your_risk_gemini_api_key_here

# GROQ API Configuration (for Clinical, Evidence, Chairman agents)
GROQ_API_KEY=your_groq_api_key_here

# Database Configuration
DATABASE_URL=postgresql://radiology_user:radiology_pass@localhost:5433/radiology_ai

# Application Configuration
APP_NAME=Radiology AI System
DEBUG=False
```

### API Keys Required

1. **Google Gemini API**: For Radiology and Risk agents
   - Get from: https://makersuite.google.com/app/apikey
   - Used for: Image analysis and risk assessment

2. **GROQ API**: For Clinical, Evidence, and Chairman agents
   - Get from: https://console.groq.com/keys
   - Used for: Text-based medical reasoning



## 🏗️ Project Structure

```
llmCouncil/
├── app/                          # Backend application
│   ├── agents/                   # AI agent implementations
│   │   ├── radiology_agent.py    # X-ray analysis agent
│   │   ├── clinical_agent.py     # Clinical diagnosis agent
│   │   ├── evidence_agent.py     # Medical literature agent
│   │   ├── risk_agent.py         # Risk assessment agent
│   │   └── chairman_agent.py     # Senior synthesis agent
│   ├── api/                      # FastAPI endpoints
│   ├── database/                 # Database models and operations
│   ├── models/                   # Pydantic data models
│   ├── orchestration/            # LangGraph pipeline orchestration
│   └── utils/                    # Utility functions
├── frontend/                     # React web application
│   ├── src/
│   │   ├── components/           # Reusable UI components
│   │   ├── pages/               # Application pages
│   │   └── contexts/            # React context providers
│   ├── public/                  # Static assets
│   └── Dockerfile               # Frontend container config
├── test_images/                 # Sample X-ray images
├── uploads/                     # User uploaded files
├── docker-compose.yml           # Multi-container orchestration
├── Dockerfile                   # Backend container config
├── requirements.txt             # Python dependencies
└── start_api.py                # API server entry point
```

## 🔧 API Endpoints

### Core Endpoints
- `POST /analyze-complete-pipeline` - Full 5-agent analysis pipeline
- `GET /cases` - Retrieve analysis history
- `GET /cases/{case_id}` - Get specific case details
- `GET /stats` - System statistics
- `GET /health` - Health check

### Individual Agent Endpoints
- `POST /analyze` - Radiology analysis only
- `POST /assess-risk` - Risk assessment only
- `POST /clinical-analysis` - Clinical diagnosis only

## 🐳 Docker Services

| Service | Container | Port | Description |
|---------|-----------|------|-------------|
| Frontend | `radiology_frontend` | 3000 | React web interface |
| Backend | `radiology_backend` | 8000 | FastAPI application |
| Database | `radiology_db` | 5433 | PostgreSQL database |
| Redis | `radiology_redis` | 6379 | Caching layer |


## 🧪 Testing

```bash
# Backend tests
python -m pytest

# Frontend tests
cd frontend
npm test
```


