# 🏥 Multi-Agent Radiology AI System

> An end-to-end multi-agent AI pipeline for automated chest X-ray analysis, clinical reasoning, evidence retrieval, risk assessment, and final report synthesis.

---

## 📌 Overview

This system uses **5 specialized AI agents** orchestrated by **LangGraph** to analyze chest X-ray images and produce comprehensive medical reports. Each agent operates independently and communicates through a shared state, with results persisted to a PostgreSQL database.

```
Upload X-ray
     │
     ▼
┌─────────────────────┐
│   Radiology Agent   │  ← Stage 1: Image analysis (Gemini Vision)
└─────────────────────┘
     │
     ▼ (parallel fan-out)
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Clinical │  │ Evidence │  │  Risk    │  ← Stage 2: Parallel analysis
│  Agent   │  │  Agent   │  │  Agent   │
└──────────┘  └──────────┘  └──────────┘
     │              │              │
     └──────────────┴──────────────┘
                    │
                    ▼
          ┌──────────────────┐
          │  Chairman Agent  │  ← Stage 3: Synthesis & final report
          └──────────────────┘
                    │
                    ▼
           Final Medical Report
              + PostgreSQL DB
```

---

## 🤖 Agents

| Agent | Model | Role | Status |
|-------|-------|------|--------|
| **Radiology Agent** | Gemini Vision (→ MedRAX) | X-ray image analysis, abnormality detection | ✅ |
| **Clinical Agent** | Groq Llama 3.3 70B (→ MedGemma 27B) | Differential diagnosis, urgency assessment | ✅ |
| **Evidence Agent** | Groq + PubMed API (→ RAGFlow) | Literature search, evidence-based synthesis | ✅ |
| **Risk Agent** | Gemini (→ DeepSeek-R1) | Risk scoring, specialist referral | ✅ |
| **Chairman Agent** | Gemini (→ GPT-4o / Claude) | Multi-agent synthesis, final report | ✅ |

> 🔬 Current models are prototype substitutes. Production models (MedRAX, MedGemma 27B, DeepSeek-R1) will replace them when GPU infrastructure is available.

---

## 🏗️ Project Structure

```
radiolagy/
├── app/
│   ├── agents/
│   │   ├── radiology_agent.py      # Gemini Vision X-ray analysis
│   │   ├── clinical_agent.py       # Groq clinical reasoning
│   │   ├── evidence_agent.py       # Groq + PubMed evidence retrieval
│   │   ├── risk_agent.py           # Gemini risk assessment
│   │   └── chairman_agent.py       # Final synthesis agent
│   ├── models/
│   │   ├── radiology_models.py
│   │   ├── clinical_models.py
│   │   ├── evidence_models.py
│   │   ├── risk_models.py
│   │   └── chairman_models.py
│   ├── pipeline/
│   │   └── langgraph_pipeline.py   # LangGraph orchestration
│   ├── api/
│   │   ├── main.py                 # FastAPI server
│   │   └── models.py               # API request/response models
│   ├── database/
│   │   ├── models.py               # SQLAlchemy schema
│   │   ├── crud.py                 # Database operations
│   │   ├── database.py             # DB connection
│   │   └── init_db.py
│   └── utils/
│       └── simple_timer.py         # Performance timing decorator
├── test_images/                    # Sample X-ray images
├── main.py                         # Single-run pipeline entry point
├── start_api.py                    # FastAPI server launcher
├── test_langgraph.py               # LangGraph pipeline test
├── test_detailed_timing.py         # Performance benchmarking
├── view_reports.py                 # CLI database viewer
├── setup_database.py               # Database initialization
├── requirements.txt
└── .env                            # API keys and config
```

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/afnarimzi/radiolagy.git
cd radiolagy
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
pip install langgraph langchain langchain-core
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory:
```env
# Gemini API (Radiology + Risk + Chairman agents)
GOOGLE_API_KEY=your_google_api_key_here
RISK_AGENT_API_KEY=your_risk_gemini_key_here

# Groq API (Clinical + Evidence agents)
GROQ_API_KEY=your_groq_api_key_here

# PostgreSQL Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=radiology_db
DB_USER=postgres
DB_PASSWORD=your_password_here

# App Config
APP_NAME=Multi-Agent AI Medical System
DEBUG=True
```

> Get free API keys: [Google AI Studio](https://aistudio.google.com/app/apikey) | [Groq Console](https://console.groq.com)

### 5. Initialize Database
```bash
python setup_database.py
```

### 6. Add Test Images
Place chest X-ray images (`.jpg`, `.jpeg`, `.png`) in the `test_images/` folder.

---

## ▶️ Running the System

### Option 1 — Single Run (All 5 Agents)
```bash
python main.py
```
Processes all images in `test_images/`, runs all agents, prints combined report.

### Option 2 — API Server (Swagger UI)
```bash
python start_api.py
```
Then open: **http://127.0.0.1:8000/docs**

### Option 3 — LangGraph Pipeline Test
```bash
python test_langgraph.py
```

### Option 4 — View Database Reports
```bash
python view_reports.py
python view_reports.py detailed
python view_reports.py stats
```

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload-complete-pipeline-with-chairman` | **Upload image → run all 5 agents** |
| `POST` | `/upload-analyze` | Upload and run radiology analysis only |
| `POST` | `/analyze-complete-pipeline` | Run full pipeline on existing case |
| `POST` | `/assess-risk` | Risk assessment only |
| `POST` | `/clinical-agent` | Clinical analysis only |
| `POST` | `/evidence-agent` | Evidence search only |
| `GET`  | `/reports` | List all recent reports |
| `GET`  | `/reports/{case_id}` | Get full report by case ID |
| `GET`  | `/cases` | List all cases |
| `GET`  | `/cases/{case_id}` | Get specific case details |
| `GET`  | `/health` | System health check |

---

## ⚙️ LangGraph Orchestration

The pipeline uses **LangGraph StateGraph** for orchestration with two key optimizations:

**Level 1 — True Parallel Execution**
```
Stage 2 agents run simultaneously via asyncio.gather():
  Clinical (1-2s) ─┐
  Evidence (3-5s) ──┤ → total = max(all) not sum(all)
  Risk     (10s)  ─┘
```

**Level 2 — Retry with Exponential Backoff**
```
Rate limit (429) → wait 30s → retry (up to 3 times)
Timeout          → wait 2s  → retry (up to 3 times)
```

---

## 🗄️ Database Schema

| Table | Description |
|-------|-------------|
| `patients` | Patient information |
| `patient_inputs` | Input data (image path, clinical context) |
| `patient_outputs` | Agent results (linked by `case_id`) |
| `agent_threads` | Multi-agent conversation tracking |
| `medical_reports` | Formatted final reports |

All agent results are linked by a shared `case_id` (UUID), enabling full traceability across the pipeline.

---

## 📊 Performance (Prototype)

| Stage | Agent | Avg Time |
|-------|-------|----------|
| Stage 1 | Radiology (Gemini Vision) | ~13-17s |
| Stage 2 | Clinical + Evidence + Risk (parallel) | ~17s |
| Stage 3 | Chairman | ~2s |
| **Total** | **End-to-end pipeline** | **~33s** |



## 🗺️ Roadmap

- [x] 5-agent pipeline implementation
- [x] FastAPI REST endpoints
- [x] LangGraph orchestration with parallel execution
- [x] Retry logic and timeout handling
- [x] PostgreSQL database integration
- [ ] LangGraph HITL (Human-in-the-Loop) checkpoint
- [ ] Redis caching for repeated analyses
- [ ] SSE streaming for real-time progress
- [ ] MedRAX integration (GPU required)
- [ ] MedGemma 27B integration (GPU required)
- [ ] DeepSeek-R1 70B integration (GPU required)
- [ ] React frontend dashboard
- [ ] Docker containerization



## 📋 Requirements

```
fastapi
uvicorn
sqlalchemy
psycopg2-binary
python-dotenv
pydantic
groq
requests
python-multipart
pillow
google-generativeai
langgraph
langchain
langchain-core
```

---

## ⚠️ Disclaimer

This system is a **research prototype** and is **not intended for clinical use**. All outputs must be reviewed by a qualified medical professional before any clinical decision is made. The system does not replace radiologist judgment.

---

## 📄 License

This project is developed as part of an AI/ML internship research program.

---

<div align="center">
  <strong>Built with LangGraph · FastAPI · Gemini · Groq · PostgreSQL</strong>
</div>