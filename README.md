# MedLinker AI

Healthcare facility capability extraction and medical desert detection system with AI-powered analysis.

## Overview

MedLinker AI is a complete agentic pipeline that extracts, verifies, and aggregates healthcare facility data to identify medical deserts and capability gaps. The system combines backend AI processing with a modern web interface for data exploration and analysis.

## Features

### Backend Pipeline
- Facility capability extraction from unstructured data
- Verification and inconsistency detection
- Regional aggregation and medical desert scoring
- Q&A system with grounded citations
- RAG retrieval with FAISS (optional)
- LangGraph orchestration (optional)
- MLflow experiment tracking (optional)
- Distributed tracing for debugging

### Frontend Application
- Dashboard with real-time facility statistics
- Interactive map view with GPS coordinates
- Facility finder with filtering and search
- AI-powered chatbot for data queries
- Conversation save/export functionality
- User profile management
- Clean, clinical sky blue theme

## Technology Stack

### Backend
- Python 3.11+
- FastAPI for REST API
- Pydantic v2 for data validation
- FAISS for vector search (optional)
- LangGraph for orchestration (optional)
- MLflow for experiment tracking (optional)

### Frontend
- React 18
- Vite for build tooling
- TailwindCSS for styling
- React Router for navigation
- Leaflet for map visualization

## Installation

### Prerequisites
- Python 3.11 or higher
- Node.js 18 or higher
- pip or uv package manager

### Backend Setup

1. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Process facility data:
```bash
PYTHONPATH=. LLM_PROVIDER=none python -m medlinker_ai.cli run_dataset "Virtue Foundation Ghana v0.3 - Sheet1.csv" --limit 30
```

4. Aggregate regional data:
```bash
PYTHONPATH=. LLM_PROVIDER=none python -m medlinker_ai.cli aggregate ./outputs/facilities.jsonl
```

5. Build RAG indexes (optional):
```bash
PYTHONPATH=. python -m medlinker_ai.cli build_rag_index
```

6. Start the API server:
```bash
PYTHONPATH=. RAG_ENABLED=1 ORCHESTRATOR=langgraph uvicorn medlinker_ai.api:app --reload
```

The API will be available at http://localhost:8000

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start development server:
```bash
npm run dev
```

The application will be available at http://localhost:5173

## Usage

### API Endpoints

**GET /facilities**
- Returns all processed facility data
- Response includes capabilities, status, and verification details

**GET /regions**
- Returns regional aggregation summaries
- Includes desert scores and missing critical services

**POST /ask**
- Natural language Q&A interface
- Request body: `{"question": "your question here"}`
- Returns answer with grounded citations

**GET /trace/{trace_id}**
- Retrieve execution trace for debugging
- Shows pipeline steps and intermediate outputs

### Web Interface

**Home Dashboard**
- View total facilities and critical regions
- See top verified facilities
- Identify facilities needing attention
- Monitor critical medical desert regions

**Finder**
- Browse all facilities on interactive map
- Filter by services, equipment, and status
- Switch between map and list views
- View detailed facility information

**Chatbot**
- Ask questions about facilities and regions
- Get answers with supporting citations
- Save and export conversation history
- Example queries:
  - "Show me all facilities"
  - "Which regions have the highest desert score?"
  - "What facilities offer surgery?"

**Profile**
- Manage personal information
- Configure notification preferences
- Update security settings
- Changes persist across sessions

## Data Pipeline

### Phase 1: Extract
Extracts structured capabilities from unstructured facility data:
- Services (e.g., surgery, emergency care)
- Equipment (e.g., ultrasound, X-ray)
- Staffing (e.g., doctors, nurses)
- Operating hours and referral capacity

### Phase 2: Verify
Applies verification rules to detect inconsistencies:
- Incomplete information (missing hours, staffing)
- Suspicious claims (surgery without anesthesia)
- Confidence scoring based on evidence

### Phase 3: Aggregate
Aggregates facility data by region:
- Coverage analysis for critical services
- Medical desert scoring (0-100 scale)
- Identification of missing capabilities

### Phase 4: Answer
Q&A system with grounded responses:
- Intent detection (desert, capability, status queries)
- Context retrieval with RAG or keyword matching
- Citation-backed answers with traceability

## Configuration

### Environment Variables

Create a `.env` file in the project root (never commit this file):

```bash
OPENAI_API_KEY=your_api_key_here
LLM_PROVIDER=openai
RAG_ENABLED=1
ORCHESTRATOR=langgraph
```

**LLM_PROVIDER**
- Options: `none`, `openai`, `gemini`
- Default: `none` (uses deterministic fallback)

**RAG_ENABLED**
- Options: `0`, `1`
- Enables FAISS-based retrieval

**ORCHESTRATOR**
- Options: `none`, `langgraph`
- Enables LangGraph orchestration

**MLFLOW_TRACKING_URI**
- MLflow server URL for experiment tracking

**Security Note:** Never commit API keys to version control. Use `.env` files (already in .gitignore) or environment variables.

## Testing

Run all tests:
```bash
PYTHONPATH=. LLM_PROVIDER=none pytest tests/ -v
```

Run specific test suite:
```bash
PYTHONPATH=. LLM_PROVIDER=none pytest tests/test_api_smoke.py -v
```

All tests pass offline without requiring LLM API keys.

## Project Structure

```
medlinker_ai/
├── __init__.py
├── api.py              # FastAPI application
├── cli.py              # Command-line interface
├── models.py           # Pydantic data models
├── dataset.py          # Data loading utilities
├── extract.py          # Capability extraction
├── verify.py           # Verification logic
├── aggregate.py        # Regional aggregation
├── qa.py               # Q&A system
├── llm/                # LLM client implementations
├── rag/                # RAG retrieval system
└── orchestrator/       # LangGraph orchestration

frontend/
├── src/
│   ├── components/     # Reusable UI components
│   ├── sections/       # Page components
│   ├── services/       # API client
│   ├── utils/          # Helper functions
│   └── styles/         # Global styles
└── public/             # Static assets

tests/                  # Test suite
outputs/                # Generated data files
examples/               # Sample input/output files
```

## Data Format

### Facility Input
CSV file with columns:
- name: Facility name
- location: Address or region
- specialties: Medical specialties offered
- equipment: Available medical equipment
- capability: Service capabilities
- procedure: Procedures performed

### Facility Output
JSON with structured fields:
- facility_id: Unique identifier
- facility_name: Display name
- location: Geographic location
- region: Administrative region
- country: Country code
- latitude/longitude: GPS coordinates
- extracted_capabilities: Structured data
- status: VERIFIED, INCOMPLETE, or SUSPICIOUS
- confidence: HIGH, MEDIUM, or LOW
- citations: Supporting evidence

### Region Summary
JSON with aggregated metrics:
- country: Country name
- region: Region name
- total_facilities: Count of facilities
- desert_score: 0-100 scale (higher = worse)
- missing_critical: List of unavailable services
- coverage: Service/equipment availability counts

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests to ensure everything passes
5. Submit a pull request

## License

See LICENSE file for details.

## Support

For issues and questions, please open an issue on GitHub.
