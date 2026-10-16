# 🛡️ AegisRegistry: Autonomous Zero-Downtime Agent Tool Self-Healing Gateway

> **VESIT Quest IT Hackathon — Problem Statement 01**  
> *Production-Grade Autonomous Schema Drift Repair, In-Memory MVCC Hot-Patching, and GitOps Code Remediation.*

---

## 🌟 Executive Summary

Modern AI agents (e.g. LangChain, AutoGen, CrewAI) break when backend API contracts drift (field renames, nested payloads, mandatory protocol headers). When faced with an `HTTP 422 Unprocessable Entity`, standard agents repeatedly pass error traces into the LLM context, burning runaway token budgets and crashing with unhandled exceptions.

**AegisRegistry** solves this autonomously with **zero downtime** and **zero LLM healing tokens**:
1. **Dynamic AST Compiler:** Diagnoses and repairs arbitrary Pydantic schema drift in `< 15ms` using deterministic tree alignment (**0 AI tokens**).
2. **In-Memory MVCC Hot-Patching:** Atomically upgrades the in-memory tool contract from `v1.0` to `v1.1` with **0.00s downtime**.
3. **Real Database Integration:** Backed by persistent relational SQLite tables (`genesis_real.db`) computing live weighted CGPA arithmetic and tuition balance deductions.
4. **GitOps Auto-PR Daemon:** Asynchronously generates permanent Pydantic code migrations and files GitHub PRs.

---

## 📊 Evaluation Scorecard (VESIT Quest IT Rubric)

| Metric | Standard LangChain ReAct Agent | AegisRegistry (Our Solution) | Advantage |
| :--- | :--- | :--- | :--- |
| **Mean Time to Recover (MTTR)** | ❌ **Crash / Failed** (> 6.5s) | 🟢 **0.185s** (< 200ms) | **35x Faster** |
| **Healer Token Consumption** | ❌ **4,500+ Tokens** ($0.05/call) | 🟢 **0 Tokens** (Pure AST Compiler) | **100% Cost Reduction** |
| **Runtime Availability** | ❌ **100% Service Outage** | 🟢 **0.00s Downtime** (Atomic MVCC Swap) | **Zero Downtime** |
| **Data Consistency Guard** | ❌ None (Blind Retries Corrupt DB) | 🟢 **Semantic Invariant Guard** | Catches Silent Drift |
| **Long-Term Code Fix** | ❌ Manual Developer Bug Ticket | 🟢 **Autonomous GitOps Auto-PR** | Hands-free Repo Sync |

---

## 🏗️ Architecture & Component Flow

```
[User Request] 
      │
      ▼
[Groq LPU Agent] (openai/gpt-oss-20b)
      │ Formulates Tool Call (v1.0 Schema)
      ▼
[Aegis Interceptor]
      │ Dispatches HTTP POST
      ▼
[Dynamic API Gateway] ── (Schema Drift Occurred: 422 Unprocessable Entity)
      │
      ▼
[0-Token Dynamic AST Healer] ── < 15ms Tree Alignment (0 TOKENS)
      │
      ▼
[MVCC In-Memory Registry] ──── Hot-Patches Pointer: v1.0 ➔ v1.1 (0.00s Downtime)
      │
      ▼
[Resumed Retry] ───────────── Retries with Healed Payload ➔ 200 OK!
      │
      ├──────────────────────► [Real SQLite DB] (Weighted CGPA math on genesis_real.db)
      ├──────────────────────► [Audit Ledger] (Trace ID logged for 1-Click Undo)
      └──────────────────────► [GitOps Daemon] (Autonomous Pydantic migration PR)
```

---

## 🚀 Quickstart & Live Demo

### 1. Prerequisites
- Python 3.10+
- Dependencies: `fastapi`, `uvicorn`, `httpx`, `streamlit`, `groq`, `pydantic`

```bash
pip install fastapi uvicorn httpx streamlit groq pydantic
```

### 2. Environment Configuration
Create a `.env` file in the project root (see `.env.example`):
```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
```

### 3. Launch the Platform (1-Click)
Start both the Dynamic API Server and the Interactive UI Dashboard in a single command:
```bash
python launch_all.py
```
*(On Windows, you can simply double-click `start_demo.bat`)*

Dashboard will open automatically at:  
👉 **`http://localhost:8501`**

---

## 🧪 Verification Test Suite

Run the end-to-end verification suite across all 5 drift scenarios against the live SQLite database:
```bash
python test_real_suite.py
```

### Output:
```text
  [✅ PASS] Scenario 1: Baseline Clean (v1.0)                       | MTTR=0.000s | Tokens=0
  [✅ PASS] Scenario 2: Field Rename (user_id -> account_id)        | MTTR=0.176s | Tokens=0
  [✅ PASS] Scenario 3: Deep Object Nesting (target.id: int)        | MTTR=0.188s | Tokens=0
  [✅ PASS] Scenario 4: Required Protocol Header (X-API-Version)    | MTTR=0.174s | Tokens=0
  [✅ PASS] Scenario 5: Compound Break (Nesting + Header + Cast)    | MTTR=0.162s | Tokens=0
---------------------------------------------------------------------------
  🎯 ZERO-TOUCH ADAPTATION RATE: 100.0% (5/5 Passed)
  ⚡ AVERAGE MTTR: 0.140 seconds (Target < 2.0s: PASSED)
```

---

## 📁 Repository Structure

```
Genesis/
├── aegis/
│   ├── dynamic_ast_healer.py  # Generalized 0-token AST schema alignment engine
│   ├── groq_agent.py          # Real Groq LPU AI agent (openai/gpt-oss-20b)
│   ├── interceptor.py         # HTTP 422 trap & single-flight concurrency lock
│   ├── registry.py            # In-memory MVCC zero-downtime versioned registry
│   ├── ledger.py              # Request trace ledger for transaction rollback
│   └── gitops.py              # Autonomous GitOps Pydantic migration daemon
├── db/
│   └── database.py            # Real SQLite connection & live CGPA calculations
├── baseline_agent.py          # Standard LangChain ReAct agent (failure control)
├── dynamic_api_server.py      # Real FastAPI dynamic gateway with runtime mutator
├── dashboard.py               # Sleek, zero-scroll 3-step Streamlit presentation UI
├── genesis_real.db            # Persistent relational SQLite database
├── launch_all.py              # 1-click unified launcher (Backend + Dashboard)
├── start_demo.bat             # Windows 1-click batch launcher
├── test_real_suite.py         # 100% automated test suite across all 5 drift types
├── .env.example               # Environment variables template
└── .gitignore                 # Clean repository gitignore
```

---

## 👥 Authors
Developed for **VESIT Quest IT Hackathon — Problem Statement 01**.
