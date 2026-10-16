# AegisRegistry 🛡️
> **Autonomous Self-Healing Tool Interface Under API Schema Drift**

AegisRegistry is an end-to-end framework and live testbed that demonstrates autonomous AI tool resilience when third-party APIs undergo breaking schema changes (Schema Drift). It features a full university relational database, a 15-endpoint API Catalog, an interactive API Explorer with live schema drift mutation injection, and a dual-agent natural language interface supporting both standard Groq LLM tool-calling and LangChain Agent execution.

---

## Key Highlights

- **Relational University Schema**: 30 SQLite tables, 6,962 rows of courses, students, faculty, transcripts, prerequisites, departments, and financial ledgers.
- **15-Endpoint REST API Catalog**: Categorized into Simple (1 table), Medium (2–4 tables), and Complex (5–6 tables) endpoints.
- **Interactive API Explorer & Postman Runner**: Test any endpoint in real time with parameters, headers, response timing, and formatted JSON output.
- **Live Schema Drift Engine**: Dynamically break API contracts on the fly with 5 enterprise drift scenarios:
  - ⚡ *Drift 1: Parameter Renamed* (e.g. `query` ➔ `title_or_author`)
  - ⚡ *Drift 2: Data Type Mutated* (e.g. `student_id` `int` ➔ `string`)
  - ⚡ *Drift 3: Nested Object Wrapped* (e.g. flat arguments wrapped in `{ "filter": { ... } }`)
  - ⚡ *Drift 4: Missing Required Field* (omits mandatory pagination/filter fields)
  - ⚡ *Drift 5: Route Deprecated / Path Altered* (e.g. endpoint relocated)
- **Autonomous Aegis & LangChain Agents**: Natural language query engine with live database tool access.
- **Strict 3-Attempt Retry Limit**: When an API fails due to schema drift, the agent attempts at most 3 times and halts immediately with detailed contract diagnostics, refusing to hallucinate or bypass broken endpoints.
- **Postman-Themed Design System**: Clean white theme with signature Postman Orange (`#FF6C37`) accents and micro-interactions.

---

## Architecture Overview

```
               ┌────────────────────────────────────────────────────────┐
               │          React 18 + Tailwind CSS Frontend              │
               │   • Postman UI / Catalog / API Explorer / Drift Picker  │
               │   • Live Chatbot Interface (Aegis / LangChain Switch)  │
               │   • Database State Inspector (30 Tables / 6,962 Rows)   │
               └──────────────────────────┬─────────────────────────────┘
                                          │ HTTP / JSON
                                          ▼
               ┌────────────────────────────────────────────────────────┐
               │               FastAPI Backend (Port 8000)              │
               │   • Schema Drift Middleware & Interceptor              │
               │   • 15 Relational REST Endpoints                       │
               │   • Active Drift State Registry (/api/v1/drift-state)  │
               │   • Aegis Agent & LangChain Agent Endpoints            │
               └──────────────┬───────────────────────────┬─────────────┘
                              │                           │
                              ▼                           ▼
               ┌──────────────────────────┐    ┌─────────────────────────┐
               │    Groq / LLM Service    │    │    SQLite 3 Database    │
               │   (Llama-3.3-70b-Versatile)│  │   (university.db)       │
               └──────────────────────────┘    └─────────────────────────┘
```

---

## Quickstart Guide

### Prerequisites
- Python 3.10+
- Node.js 18+ & npm
- (Optional) Groq API Key (falls back to local intelligent query planner if absent)

### 1. Launch Everything with One Command
Run the unified launcher script:
```bash
python launch.py
```
This automatically boots:
- **FastAPI Backend**: `http://127.0.0.1:8000` (Swagger docs at `/docs`)
- **React Frontend**: `http://127.0.0.1:5173`

---

## Manual Execution

### Backend Setup
```bash
cd backend
python -m pip install fastapi uvicorn groq langchain langchain-core pydantic
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## Project Structure

```
Genesis/
├── 01_BASIC_WORKFLOW_AND_SCENARIOS.md  # Core conceptual guide & drift breakdown
├── 02_ARCHITECTURE_AND_LAYERS.md       # Layer-by-layer technical specification
├── launch.py                           # Unified process orchestrator
├── university-sample-database-...json  # Complete 30-table raw seed dataset
├── backend/
│   ├── main.py                         # FastAPI app, CORS, & schema drift middleware
│   ├── database.py                     # SQLite engine, CRUD handlers, & schema generator
│   ├── routes/
│   │   └── api_catalog.py              # 15 university catalog endpoints
│   └── services/
│       ├── drift_state.py              # Central drift state registry & request interceptor
│       ├── chatbot_agent.py            # Aegis agent with 3-attempt hard stop
│       └── langchain_agent.py          # LangChain agent with drifted tool binding
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── ApiExplorerModal.jsx    # Postman-style API runner with drift injection
    │   │   ├── ChatbotPanel.jsx        # Dual-engine chatbot with LangChain toggle
    │   │   └── DatabaseModal.jsx       # 30-table live database inspector
    │   ├── services/
    │   │   └── api.js                  # Frontend API client & drift state sync
    │   ├── App.jsx                     # Main Aegis dashboard layout
    │   └── index.css                   # Custom Postman design tokens
    └── package.json
```

---

## License
MIT License. Built for autonomous AI tool research and resilient microservice architectures.
