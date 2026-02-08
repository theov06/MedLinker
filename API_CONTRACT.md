# MedLinker AI - API Contract for Frontend

## Base URL
```
http://localhost:8000
```

## Endpoints

### 1. GET /
Get API information
```bash
curl http://localhost:8000/
```
**Response:**
```json
{
  "name": "MedLinker AI",
  "version": "1.0.0",
  "description": "Healthcare facility capability extraction and medical desert detection API",
  "endpoints": {
    "facilities": "/facilities",
    "regions": "/regions",
    "ask": "/ask",
    "trace": "/trace/{trace_id}"
  }
}
```

### 2. GET /health
Health check
```bash
curl http://localhost:8000/health
```
**Response:**
```json
{
  "status": "healthy"
}
```

### 3. GET /facilities
Get all facility analysis outputs
```bash
curl http://localhost:8000/facilities
```
**Response:** Array of facilities
```json
[
  {
    "facility_id": "GH-ACC-001",
    "extracted_capabilities": {
      "services": ["Surgery", "Emergency", "Maternity"],
      "equipment": ["Ultrasound", "X-Ray"],
      "staffing": ["Doctors", "Nurses"],
      "hours": "24/7",
      "referral_capacity": "ADVANCED",
      "emergency_capability": "YES"
    },
    "status": "VERIFIED",
    "reasons": [],
    "confidence": "HIGH",
    "citations": [
      {
        "source_id": "web_scrape_001",
        "source_url": "https://example.com",
        "snippet": "Emergency services available 24/7",
        "field": "services",
        "start_char": 100,
        "end_char": 135
      }
    ],
    "trace_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }
]
```

**Status values:**
- `VERIFIED` - Complete and consistent
- `INCOMPLETE` - Missing essential information
- `SUSPICIOUS` - Contradictions detected

**Confidence values:**
- `HIGH` - Reliable data
- `MEDIUM` - Some concerns
- `LOW` - Significant issues

### 4. GET /regions
Get regional summaries with medical desert scores
```bash
curl http://localhost:8000/regions
```
**Response:** Array of regions
```json
[
  {
    "country": "GH",
    "region": "ACC",
    "total_facilities": 15,
    "facilities_analyzed": 15,
    "status_counts": {
      "VERIFIED": 10,
      "INCOMPLETE": 3,
      "SUSPICIOUS": 2
    },
    "coverage": {
      "services": {
        "emergency": 12,
        "surgery": 10,
        "c-section": 8
      },
      "equipment": {
        "ultrasound": 9,
        "x-ray": 7
      },
      "staffing": {
        "doctor": 14,
        "midwife": 6
      }
    },
    "missing_critical": ["service:laboratory"],
    "desert_score": 20,
    "supporting_facility_ids": ["GH-ACC-001", "GH-ACC-002"],
    "trace_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901"
  }
]
```

**Desert Score:**
- `0-30` - Low desert (good coverage)
- `31-60` - Moderate desert (some gaps)
- `61-100` - High desert (severe gaps)

### 5. POST /ask
Ask questions about facilities and regions
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Which regions lack C-section capability?"}'
```
**Request:**
```json
{
  "question": "Which regions lack C-section capability?"
}
```

**Response:**
```json
{
  "answer": "Found 2 high-desert regions (score ≥50):\n1. GH-ASH: Desert score 100\n   Missing: service:c-section, service:ultrasound, service:x-ray",
  "citations": [
    {
      "source_id": "regions_aggregate",
      "source_url": null,
      "snippet": "Region: GH-ASH; desert_score: 100; missing_critical: ['service:c-section', 'service:ultrasound']",
      "field": "region_summary",
      "start_char": null,
      "end_char": null
    }
  ],
  "trace_id": "c3d4e5f6-a7b8-9012-cdef-123456789012"
}
```

**Example Questions:**
- "Which regions are medical deserts?"
- "Show facilities with suspicious claims"
- "Where can I find ultrasound capability?"
- "Which regions lack C-section?"

### 6. GET /trace/{trace_id}
Get trace details for debugging
```bash
curl http://localhost:8000/trace/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```
**Response:**
```json
{
  "trace_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "spans": [
    {
      "step_name": "extract",
      "inputs_summary": {
        "facility_id": "GH-ACC-001",
        "source_id": "web_scrape_001"
      },
      "outputs_summary": {
        "services_count": 10,
        "equipment_count": 5,
        "staffing_count": 3
      },
      "evidence_refs": 20,
      "timestamp": "2026-02-07T10:30:45.123456"
    },
    {
      "step_name": "verify",
      "inputs_summary": {
        "facility_id": "GH-ACC-001"
      },
      "outputs_summary": {
        "status": "VERIFIED",
        "reasons_count": 0,
        "confidence": "HIGH"
      },
      "evidence_refs": 20,
      "timestamp": "2026-02-07T10:30:46.234567"
    }
  ]
}
```

## Error Responses

### 404 - Not Found
```json
{
  "detail": "Facilities data not found. Run 'python -m medlinker_ai.cli run_dataset' first."
}
```

### 400 - Bad Request
```json
{
  "detail": "Question cannot be empty"
}
```

### 500 - Server Error
```json
{
  "detail": "Error loading facilities: [error message]"
}
```

## CORS
CORS is enabled for all origins in development mode. Frontend can make requests from any domain.

## Interactive Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Example Frontend Integration

### JavaScript/React
```javascript
// Get all facilities
const facilities = await fetch('http://localhost:8000/facilities')
  .then(res => res.json());

// Get regions
const regions = await fetch('http://localhost:8000/regions')
  .then(res => res.json());

// Ask question
const result = await fetch('http://localhost:8000/ask', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    question: 'Which regions are medical deserts?' 
  })
}).then(res => res.json());

console.log(result.answer);
console.log(result.citations);
```

### Python
```python
import requests

# Get facilities
response = requests.get('http://localhost:8000/facilities')
facilities = response.json()

# Ask question
response = requests.post(
    'http://localhost:8000/ask',
    json={'question': 'Show suspicious facilities'}
)
result = response.json()
print(result['answer'])
```

## Starting the API

```bash
# Install dependencies
pip install -r requirements.txt

# Process data (required before API works)
PYTHONPATH=. LLM_PROVIDER=none python -m medlinker_ai.cli run_dataset "data.csv" --limit 30
PYTHONPATH=. LLM_PROVIDER=none python -m medlinker_ai.cli aggregate ./outputs/facilities.jsonl

# Start API
uvicorn medlinker_ai.api:app --reload
```

## Notes
- API must process data before endpoints return results
- All factual claims include citations
- Trace IDs enable debugging of AI decisions
- Desert scores range from 0-100 (higher = worse)
