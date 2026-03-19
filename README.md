#  Radiology Assistant

AI-powered radiology assistant for comprehensive medical analysis from X-ray images.

##  Project Structure

```
llmCouncil/
├── app/                  # Backend API
├── frontend/             # React web interface
├── start_api.py         # API server launcher
├── requirements.txt     # Python dependencies
└── .env                # API keys configuration
```

##  Installation & Setup

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

### Start Backend Server
```bash
python3 start_api.py
```

### Start Frontend
```bash
cd frontend
npm install
npm start
```

Access the application at `http://localhost:3000`
