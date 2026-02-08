# Quick Start - MedLinker AI

## Run Backend (Terminal 1)

```bash
# 1. Clone and navigate
git clone https://github.com/theov06/MedLinker.git
cd MedLinker
git checkout test

# 2. Setup Python environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt

# 3. Run backend
uvicorn medlinker_ai.api:app --reload --port 8000
```

✅ Backend running at: **http://localhost:8000**

---

## Run Frontend (Terminal 2)

```bash
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Run frontend
npm run dev
```

✅ Frontend running at: **http://localhost:5173**

---

## That's it! 🎉

Open your browser to the frontend URL and start using MedLinker AI.

**API Docs:** http://localhost:8000/docs
