# System Architecture & Layered Engineering Specification

> **Goal**: Provide an exhaustive technical breakdown of the architectural tiers, system layers, component boundaries, and inter-layer communication protocols of AegisRegistry.

---

## Table of Contents
1. [Architectural Overview & High-Level System Topology](#1-architectural-overview--high-level-system-topology)
2. [The 9 Architectural Layers of AegisRegistry](#2-the-9-architectural-layers-of-aegisregistry)
   - [Layer 1: Presentation & Telemetry Layer](#layer-1-presentation--telemetry-layer)
   - [Layer 2: Agent Runtime & Dispatch Layer](#layer-2-agent-runtime--dispatch-layer)
   - [Layer 3: Interception & Concurrency Guard Layer](#layer-3-interception--concurrency-guard-layer)
   - [Layer 4: Dual-Path Diagnosis & Inference Layer](#layer-4-dual-path-diagnosis--inference-layer)
   - [Layer 5: Safety, Provenance & Policy Governance Layer](#layer-5-safety-provenance--policy-governance-layer)
   - [Layer 6: In-Memory Hot-Patching & MVCC Registry Layer](#layer-6-in-memory-hot-patching--mvcc-registry-layer)
   - [Layer 7: Validation & Sandbox Replay Layer (API Time Machine)](#layer-7-validation--sandbox-replay-layer-api-time-machine)
   - [Layer 8: Persistence & Enterprise Data Healing Layer](#layer-8-persistence--enterprise-data-healing-layer)
   - [Layer 9: DevOps Autonomous Code Remediation Layer](#layer-9-devops-autonomous-code-remediation-layer)
3. [Component Interaction & Information Flow](#3-component-interaction--information-flow)
4. [Data Contracts & Interface Definitions](#4-data-contracts--interface-definitions)
5. [Concurrency, Thread-Safety & State Isolation](#5-concurrency-thread-safety--state-isolation)

---

## 1. Architectural Overview & High-Level System Topology

AegisRegistry operates as an **autonomous self-healing proxy and control plane** positioned directly between an AI Agent's runtime execution environment and downstream microservices.

Rather than treating tool calling as an unmonitored point-to-point network call, AegisRegistry encapsulates every tool execution within a **closed-loop feedback system**:

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                           AEGISREGISTRY SYSTEM TOPOLOGY                           │
│                                                                                   │
│   [User / Client Application]                                                     │
│               │                                                                   │
│               ▼                                                                   │
│   ┌───────────────────────────────────────────────────────────────────────────┐   │
│   │ Layer 1: Presentation & Telemetry (Streamlit Live Split-Screen UI)       │   │
│   └─────────────────────────────────────┬─────────────────────────────────────┘   │
│                                         ▼                                         │
│   ┌───────────────────────────────────────────────────────────────────────────┐   │
│   │ Layer 2: Agent Runtime & Dispatch (Gemini 1.5 Flash + LangChain Core)    │   │
│   └─────────────────────────────────────┬─────────────────────────────────────┘   │
│                                         ▼                                         │
│   ┌───────────────────────────────────────────────────────────────────────────┐   │
│   │ Layer 3: Interception & Concurrency Guard (Single-Flight Mutex Shield)    │   │
│   └─────────────────┬─────────────────────────────────────────────────────────┘   │
│                     │                                                             │
│                     ├───────────────────────────────────────────┐                 │
│                     ▼ (Normal Path)                             ▼ (Error Caught)  │
│          ┌───────────────────────┐             ┌──────────────────────────────┐   │
│          │ Downstream Rest API   │             │ Layer 4: Dual-Path Diagnosis │   │
│          │ (FastAPI Microservice)│             │ (AST Compiler / Micro-LLM)   │   │
│          └───────────────────────┘             └──────────────┬───────────────┘   │
│                                                               │                   │
│                                                               ▼                   │
│                                                ┌──────────────────────────────┐   │
│                                                │ Layer 5: Safety & Governance │   │
│                                                │ (Provenance Gate / HITL)     │   │
│                                                └──────────────┬───────────────┘   │
│                                                               │                   │
│                                                               ▼                   │
│                                                ┌──────────────────────────────┐   │
│                                                │ Layer 6: In-Memory Hot-Patch │   │
│                                                │ (MVCC Registry & Lambdas)    │   │
│                                                └──────────────┬───────────────┘   │
│                                                               │                   │
│                                                               ▼                   │
│                                                ┌──────────────────────────────┐   │
│                                                │ Layer 7: Validation Replay   │   │
│                                                │ (API Time Machine Sandbox)   │   │
│                                                └──────────────┬───────────────┘   │
│                                                               │                   │
│                     ┌─────────────────────────────────────────┴─────────────┐     │
│                     ▼                                                       ▼     │
│   ┌─────────────────────────────────────┐         ┌───────────────────────────┐   │
│   │ Layer 8: Persistence & Data Healing │         │ Layer 9: DevOps GitOps PR │   │
│   │ (Request Ledger & 1-Click Undo)     │         │ (PyGithub + PyTest Gen)   │   │
│   └─────────────────────────────────────┘         └───────────────────────────┘   │
└───────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. The 9 Architectural Layers of AegisRegistry

### Layer 1: Presentation & Telemetry Layer
* **Component**: `dashboard/app.py`
* **Technologies**: Streamlit, Rich, WebSocket telemetry streaming.
* **Responsibilities**:
  - Renders a live **Split-Screen Dashboard**:
    - **Left Screen**: Baseline Agent executing without Aegis, showing HTTP 422 error loops, token burn metrics (4,500+ tokens), and crashing state.
    - **Right Screen**: AegisRegistry executing with active interception, displaying sub-second stopwatch counters (0.05s $\to$ 0.12s $\to$ 0.52s) and successful outputs.
  - Hosts the **Scenario Switchboard**: Buttons to inject synthetic mutations (`Field Rename`, `Type Cast`, `Deep Nesting`, `Required Header`, `Compound Mutation`).
  - Displays the **Enterprise Wow Elements**:
    - Filterable **Request Ledger Table**.
    - **1-Click Undo Modal** with LLM-verified compensating SQL scripts.
    - Direct hyperlink to auto-generated GitHub Pull Requests.

---

### Layer 2: Agent Runtime & Dispatch Layer
* **Components**: `agent/baseline_agent.py`, `agent/tools.py`
* **Technologies**: Python 3.11, Google Gemini 1.5 Flash (`google-genai` SDK), LangChain Core (`AgentExecutor`, `BaseTool`).
* **Responsibilities**:
  - Ingests natural language goals from users.
  - Formulates structured tool-call arguments based on active Pydantic tool models.
  - Dispatches calls to tools via the registered interceptor.
  - Receives healed responses seamlessly without requiring conversational context reset or LLM re-prompting.

---

### Layer 3: Interception & Concurrency Guard Layer
* **Component**: `aegis_core/interceptor.py`
* **Technologies**: Python `asyncio.Lock`, `asyncio.Future`, `httpx` Middleware.
* **Responsibilities**:
  - Wraps the underlying HTTP client (`httpx.AsyncClient`).
  - Catches `400 Bad Request`, `422 Unprocessable Entity`, and `404 Not Found`.
  - **Single-Flight Mutex**:
    - When 50 concurrent requests fail simultaneously due to a schema drift, the first request acquires the tool-level mutex.
    - Concurrent requests subscribe to an in-memory `asyncio.Future` (Schema Promise) and pause execution for 0.2s.
    - Eliminates duplicate diagnostic cycles, prevents server crashes, and cuts token spend by 50x.

---

### Layer 4: Dual-Path Diagnosis & Inference Layer
* **Components**: `aegis_core/ast_compiler.py`, `aegis_core/speculative_llm.py`
* **Technologies**: Python `ast`, Pydantic Error Tree Compiler, Gemini 1.5 Flash (Strict JSON Schema Mode).
* **Responsibilities**:
  - Deduces the structural transformation required to convert the agent's outdated payload into the server's new schema.
  - **Tier 1: Fast-Path AST Compiler (< 15ms, 0 Tokens)**:
    - Analyzes structured RFC-7807/Pydantic validation errors (`loc`, `msg`, `type`).
    - Maps flat keys to nested paths (`user_id` $\to$ `target.id`).
    - Compiles type conversions (`str` $\to$ `int`).
    - Injects missing required headers (`X-API-Version`).
  - **Tier 2: Speculative Micro-LLM Fallback (< 1.2s)**:
    - Triggered strictly when backend errors are opaque text, HTML error pages, or non-standard error structures.
    - Generates a strict `SchemaDiff` JSON object.

---

### Layer 5: Safety, Provenance & Policy Governance Layer
* **Components**: `aegis_core/provenance_gate.py`, `aegis_core/governor.py`
* **Technologies**: Python Sets, Rule Engine, Human-in-the-Loop (HITL) prompt synthesizer.
* **Responsibilities**:
  - **Provenance Classifier**: Categorizes missing schema parameters:
    1. *Derivable Parameters*: Found in user prompt, auth session, or headers. Auto-mapped.
    2. *Unsupplied Business Parameters*: Personal or domain data never supplied.
  - **Zero-Hallucination Gate**: Blocks LLMs from generating dummy data (e.g., `"status": "dummy"`).
  - **Policy Governor**: Evaluates blast-radius score. Low-risk structural renames proceed automatically; high-risk financial endpoints trip circuit breakers and require explicit human sign-off.

---

### Layer 6: In-Memory Hot-Patching & MVCC Registry Layer
* **Components**: `aegis_core/mvcc_registry.py`, `aegis_core/lambda_cache.py`
* **Technologies**: Python Frozen Dataclasses, Atomic Memory Pointers, Dynamic Lambda Compilation.
* **Responsibilities**:
  - Maintains versioned snapshots of tool schemas (`v1.0`, `v1.1`, `v1.2`).
  - Performs **Atomic Pointer Swapping** to guarantee thread safety across concurrent requests.
  - Compiles candidate diffs into native Python lambdas:
    $$\text{transform} = \lambda(p, h): (\text{payload}_{\text{healed}}, \text{headers}_{\text{healed}})$$
  - Stores lambdas in RAM; subsequent requests execute transformations in **0.0001 seconds (0.1ms)** without re-running AST diffing.

---

### Layer 7: Validation & Sandbox Replay Layer (API Time Machine)
* **Components**: `aegis_core/time_machine.py`, `aegis_core/circuit_breaker.py`
* **Technologies**: In-Memory Ring Buffer, Fixture Harness, Response Invariant Asserter.
* **Responsibilities**:
  - Replays historical test fixtures against candidate patches before promoting them to production memory.
  - **Idempotency Guard**: Strictly isolates non-idempotent operations (`POST`, `DELETE`) to mock fixtures.
  - **Semantic Invariant Guard**: Verifies that the server returns valid entity data (e.g., matching student ID) rather than an empty HTTP 200 payload.
  - Enforces a strict **1-retry bound** via a Circuit Breaker to prevent infinite retry loops.

---

### Layer 8: Persistence & Enterprise Data Healing Layer
* **Components**: `persistence/ledger.py`, `persistence/undo_engine.py`
* **Technologies**: SQLite, DuckDB, SQLAlchemy ORM, SQL AST Synthesizer.
* **Responsibilities**:
  - **Request Ledger**: Logs every healed transaction with `timestamp`, `patch_id`, `request_trace_id`, pre-transform payload, and post-transform payload.
  - **1-Click Compensating SQL Synthesizer**: Generates parameterized inverse SQL transactions to reverse database state changes caused by transformed write operations.
  - **Safety Validator**: Uses an AST/LLM safety guard to reject unqualified `DELETE` or `DROP TABLE` statements before presenting the undo script to developers.

---

### Layer 9: DevOps Autonomous Code Remediation Layer
* **Component**: `devops/gitops_daemon.py`
* **Technologies**: PyGithub, Git CLI Subprocess, AST Code Formatter, PyTest.
* **Responsibilities**:
  - Bridges runtime in-memory healing to engineering permanence.
  - Asynchronously generates updated Pydantic schema files and PyTest regression test suites.
  - Commits code to a dedicated Git branch (`aegis/hotfix-<tool>-v1.1`) and opens a formal **GitHub Pull Request**.

---

## 3. Component Interaction & Information Flow

```
[Agent Runtime]
      │ (1. Call Tool with Payload)
      ▼
[Aegis Interceptor] ───► [Single-Flight Mutex] ───► [Target Microservice API]
                                                           │
                                                           ├─► (HTTP 200 OK) ──► [Semantic Invariant Guard] ──► [User]
                                                           │
                                                           └─► (HTTP 422 Error)
                                                                       │
                                                                       ▼
                                                       [Tier 1 AST Compiler]
                                                       (Fast-Path: < 15ms, 0 tokens)
                                                                       │
                                                                       ├─► (Unstructured) ──► [Tier 2 Micro-LLM]
                                                                       │
                                                                       ▼
                                                       [Provenance Gate (Anti-Hallucination)]
                                                                       │
                                                                       ▼
                                                       [MVCC In-Memory Registry]
                                                       (Atomic Pointer Swap to v1.1)
                                                                       │
                                                                       ▼
                                                       [API Time Machine Sandboxed Replay]
                                                                       │
                                                                       ▼
                                                       [Resumed Dispatch with Healed Payload]
                                                                       │
                                                                       ▼
                                                       [Target Microservice API]
                                                                       │
                                                                       ▼ (HTTP 200 OK)
                                                       [Return Output to User]
                                                                       │
                                      ┌────────────────────────────────┴────────────────────────────────┐
                                      ▼ (Async Background)                                              ▼ (Async Background)
                        [Request Ledger & 1-Click Undo]                                    [GitOps Auto-PR Daemon]
```

---

## 4. Data Contracts & Interface Definitions

Below are the exact core Python data models governing communication across the 9 layers:

```python
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

@dataclass(frozen=True)
class SchemaDiff:
    """Output contract from Layer 4 (Diagnosis Layer)."""
    field_renames: Dict[str, str]           # e.g., {"user_id": "target.id"}
    type_casts: Dict[str, str]              # e.g., {"target.id": "int"}
    injected_headers: Dict[str, str]        # e.g., {"X-API-Version": "2026-10"}
    missing_unsupplied: List[str]           # e.g., ["department_code"]
    is_structured: bool = True
    diagnostic_latency_ms: float = 0.0

@dataclass(frozen=True)
class SchemaSnapshot:
    """Immutable state model for Layer 6 (MVCC Registry Layer)."""
    version: str                            # e.g., "v1.1"
    tool_name: str                          # e.g., "get_student_info"
    json_schema: Dict[str, Any]             # JSON Schema model definition
    transform_lambda: Optional[Callable]    # Precompiled Python callable
    parent_version: Optional[str]           # e.g., "v1.0"
    created_at: datetime = field(default_factory=datetime.utcnow)
    fingerprint: str = ""                   # Cryptographic hash

@dataclass
class LedgerRecord:
    """Storage contract for Layer 8 (Persistence Layer)."""
    patch_id: str
    request_trace_id: str
    tool_name: str
    input_payload_pre: Dict[str, Any]
    input_payload_post: Dict[str, Any]
    response_status: int
    compensating_sql: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
```

---

## 5. Concurrency, Thread-Safety & State Isolation

AegisRegistry enforces strict state isolation across concurrent requests using three mechanisms:

1. **Single-Flight Promise Sharing**:
   - Implemented via a dictionary of active `asyncio.Future` instances keyed by `tool_name`.
   - If coroutine $C_1$ encounters a drift error on `get_student_info`, it locks the key.
   - Coroutines $C_2 \dots C_N$ hitting the same tool await $C_1$'s future.
   - When $C_1$ finishes hot-patching, it resolves the future with the updated `SchemaSnapshot`. All waiting coroutines immediately unblock and resume execution.

2. **Atomic Pointer Swapping (MVCC)**:
   - Tool definitions in Python are never mutated in place.
   - The registry creates a new `SchemaSnapshot` instance and swaps the memory reference (`self._active_snapshot = new_snapshot`).
   - Any coroutine that started before the swap finishes safely on its old snapshot; all new coroutines immediately see the new snapshot. No locks are held during read execution.

3. **Database Transaction Idempotency**:
   - Write operations assign a unique `request_trace_id` (UUIDv4) passed via the `Idempotency-Key` HTTP header.
   - Compensating undo scripts are strictly bounded to this `request_trace_id`, preventing accidental modifications of unrelated records during rollback.
