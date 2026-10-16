# USP Integration Map: Architectural Layers, Code Modules & Lifecycle Hooks

> **Goal**: Provide an unambiguous, module-by-module mapping showing exactly where each of the 10 USPs is implemented in the codebase, which architectural layers host it, when it executes during runtime, and which product plan it belongs to.

---

## Table of Contents
1. [Master Integration Cross-Reference Matrix](#1-master-integration-cross-reference-matrix)
2. [USP-by-USP Implementation Mapping](#2-usp-by-usp-implementation-mapping)
   - [USP 1: API Time Machine — Sandboxed Regression Replay](#usp-1-api-time-machine--sandboxed-regression-replay)
   - [USP 2: Risk-Aware Self-Healing & Policy Governor](#usp-2-risk-aware-self-healing--policy-governor)
   - [USP 3: API Drift Blast-Radius & Dependency DAG Predictor](#usp-3-api-drift-blast-radius--dependency-dag-predictor)
   - [USP 4: Versioned Immutable Patches with Instant Rollback (MVCC)](#usp-4-versioned-immutable-patches-with-instant-rollback-mvcc)
   - [USP 5: Bidirectional Semantic Invariants & Repair Proofs](#usp-5-bidirectional-semantic-invariants--repair-proofs)
   - [USP 6: Sub-15ms Tiered AST Compiler](#usp-6-sub-15ms-tiered-ast-compiler)
   - [USP 7: Drift-to-GitOps Autonomous Code Remediation](#usp-7-drift-to-gitops-autonomous-code-remediation)
   - [USP 8: Zero-Hallucination Field Provenance Gate](#usp-8-zero-hallucination-field-provenance-gate)
   - [USP 9: 1-Click Database Compensating Undo & Reconciliation Engine](#usp-9-1-click-database-compensating-undo--reconciliation-engine)
   - [USP 10: Single-Flight Mutex Concurrency Guard](#usp-10-single-flight-mutex-concurrency-guard)
3. [Runtime Lifecycle Execution Sequence](#3-runtime-lifecycle-execution-sequence)

---

## 1. Master Integration Cross-Reference Matrix

The table below provides a single-pane-of-glass overview mapping every USP to its physical file location, architectural layer, execution hook point, and product tier:

| USP # | USP Name | Exact Source Code File | Architectural Layer | Lifecycle Execution Hook | Product Plan Tier |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **USP 1** | **API Time Machine** | `aegis_core/time_machine.py` | Layer 7: Validation Replay | Pre-Commit Validation | Team / Pro & Enterprise |
| **USP 2** | **Policy Governor** | `aegis_core/governor.py` | Layer 5: Safety & Governance | Pre-Patch Gatekeeper | Enterprise Only |
| **USP 3** | **DAG Predictor** | `aegis_core/dag_predictor.py` | Layer 5: Safety & Governance | Post-Commit Propagation | Enterprise Only |
| **USP 4** | **MVCC Registry** | `aegis_core/mvcc_registry.py` | Layer 6: Memory & Registry | In-Memory Patch Commit | Team / Pro & Enterprise |
| **USP 5** | **Semantic Invariants** | `aegis_core/invariants.py` | Layer 7: Validation Replay | Post-Dispatch Invariant Gate | Enterprise Only |
| **USP 6** | **Sub-15ms AST Compiler**| `aegis_core/ast_compiler.py` | Layer 4: Dual-Path Diagnosis | Immediate Post-422 Intercept | **All Tiers (Community, Pro, Ent)** |
| **USP 7** | **GitOps Auto-PR** | `devops/gitops_daemon.py` | Layer 9: DevOps Code Fix | Asynchronous Background Daemon | Team / Pro & Enterprise |
| **USP 8** | **Provenance Gate** | `aegis_core/provenance_gate.py`| Layer 5: Safety & Governance | Diagnosis-to-Patch Validation | Enterprise Only |
| **USP 9** | **1-Click DB Undo** | `persistence/undo_engine.py` | Layer 8: Persistence & Healing | Post-Dispatch Write Logging & UI | Enterprise Only |
| **USP 10**| **Single-Flight Mutex** | `aegis_core/interceptor.py` | Layer 3: Interceptor Guard | Pre-Dispatch & Post-422 Catch | **All Tiers (Community, Pro, Ent)** |

---

## 2. USP-by-USP Implementation Mapping

---

### USP 1: API Time Machine — Sandboxed Regression Replay
* **Where It Lives**:
  - File: [`aegis_core/time_machine.py`](file:///d:/Work%20Folder/Arya's%20Projects/AntiGravity/Genesis%202026/aegis_core/time_machine.py)
  - Class: `APITimeMachine`
* **Architectural Layer**: **Layer 7: Validation & Sandbox Replay Layer**
* **Integration Points**:
  - Invoked directly by `MVCCRegistry.commit_patch()` before accepting candidate patches into RAM.
  - Interacts with `mock_api/fixtures/` to load historical golden payloads.
* **Plan Tier**: **Team/Pro** (read-only fixtures) & **Enterprise** (full multi-service state sandbox).

---

### USP 2: Risk-Aware Self-Healing & Policy Governor
* **Where It Lives**:
  - File: [`aegis_core/governor.py`](file:///d:/Work%20Folder/Arya's%20Projects/AntiGravity/Genesis%202026/aegis_core/governor.py)
  - Class: `PolicyGovernor`
* **Architectural Layer**: **Layer 5: Safety, Provenance & Policy Governance Layer**
* **Integration Points**:
  - Hooks into `aegis_core/interceptor.py` immediately after diagnosis finishes.
  - If calculated risk $\mathcal{R} \ge 70$, intercepts execution and pushes an alert to `dashboard/app.py` for human sign-off.
* **Plan Tier**: **Enterprise Edition Only**.

---

### USP 3: API Drift Blast-Radius & Dependency DAG Predictor
* **Where It Lives**:
  - File: [`aegis_core/dag_predictor.py`](file:///d:/Work%20Folder/Arya's%20Projects/AntiGravity/Genesis%202026/aegis_core/dag_predictor.py)
  - Class: `DependencyDAGPredictor`
* **Architectural Layer**: **Layer 5: Safety, Provenance & Policy Governance Layer**
* **Integration Points**:
  - Subscribes to schema version updates from `MVCCRegistry`.
  - Traverses tool dependencies and calls `ast_compiler.compile_speculative_patch()` for child tools.
* **Plan Tier**: **Enterprise Edition Only**.

---

### USP 4: Versioned Immutable Patches with Instant Rollback (MVCC)
* **Where It Lives**:
  - File: [`aegis_core/mvcc_registry.py`](file:///d:/Work%20Folder/Arya's%20Projects/AntiGravity/Genesis%202026/aegis_core/mvcc_registry.py)
  - Class: `MVCCRegistry`
* **Architectural Layer**: **Layer 6: In-Memory Hot-Patching & Registry Layer**
* **Integration Points**:
  - Referenced by `agent/baseline_agent.py` and LangChain tool dispatchers to fetch the current active tool definition.
  - Linked to `aegis_core/lambda_cache.py` to store high-speed 0.1ms transformation callables.
* **Plan Tier**: **Team/Pro & Enterprise Edition**.

---

### USP 5: Bidirectional Semantic Invariants & Repair Proofs
* **Where It Lives**:
  - File: [`aegis_core/invariants.py`](file:///d:/Work%20Folder/Arya's%20Projects/AntiGravity/Genesis%202026/aegis_core/invariants.py)
  - Class: `SemanticInvariantChecker`, `RepairProofGenerator`
* **Architectural Layer**: **Layer 7: Validation & Sandbox Replay Layer**
* **Integration Points**:
  - Inspects all HTTP 200 responses returning from the downstream API.
  - Emits cryptographically signed JSON proofs into `persistence/ledger.py`.
* **Plan Tier**: **Enterprise Edition Only**.

---

### USP 6: Sub-15ms Tiered AST Compiler
* **Where It Lives**:
  - File: [`aegis_core/ast_compiler.py`](file:///d:/Work%20Folder/Arya's%20Projects/AntiGravity/Genesis%202026/aegis_core/ast_compiler.py)
  - Class: `DeterministicASTCompiler`
* **Architectural Layer**: **Layer 4: Dual-Path Diagnosis & Inference Layer**
* **Integration Points**:
  - Primary diagnostic engine called by `aegis_core/interceptor.py` when HTTP 422 is caught.
  - Passes its output (`SchemaDiff`) into `MVCCRegistry` and `ProvenanceGate`.
* **Plan Tier**: **All Tiers (Open-Source Community, Pro, Enterprise)**.

---

### USP 7: Drift-to-GitOps Autonomous Code Remediation
* **Where It Lives**:
  - File: [`devops/gitops_daemon.py`](file:///d:/Work%20Folder/Arya's%20Projects/AntiGravity/Genesis%202026/devops/gitops_daemon.py)
  - Class: `GitOpsDaemon`
* **Architectural Layer**: **Layer 9: DevOps Autonomous Code Remediation Layer**
* **Integration Points**:
  - Triggered as a non-blocking asynchronous task (`asyncio.create_task`) upon patch activation.
  - Interacts with GitHub REST API via PyGithub to commit files and open PRs.
* **Plan Tier**: **Team/Pro & Enterprise Edition**.

---

### USP 8: Zero-Hallucination Field Provenance Gate
* **Where It Lives**:
  - File: [`aegis_core/provenance_gate.py`](file:///d:/Work%20Folder/Arya's%20Projects/AntiGravity/Genesis%202026/aegis_core/provenance_gate.py)
  - Class: `ProvenanceGate`
* **Architectural Layer**: **Layer 5: Safety, Provenance & Policy Governance Layer**
* **Integration Points**:
  - Sits directly between the AST Compiler (`Layer 4`) and the MVCC Registry (`Layer 6`).
  - Intercepts missing parameter arrays and validates origins against user prompt context.
* **Plan Tier**: **Enterprise Edition Only**.

---

### USP 9: 1-Click Database Compensating Undo & Reconciliation Engine
* **Where It Lives**:
  - File: [`persistence/undo_engine.py`](file:///d:/Work%20Folder/Arya's%20Projects/AntiGravity/Genesis%202026/persistence/undo_engine.py)
  - Class: `DatabaseCompensatingUndoEngine`
  - UI Modal: [`dashboard/app.py`](file:///d:/Work%20Folder/Arya's%20Projects/AntiGravity/Genesis%202026/dashboard/app.py)
* **Architectural Layer**: **Layer 8: Persistence & Enterprise Data Healing Layer**
* **Integration Points**:
  - Reads before/after diffs from `persistence/ledger.py`.
  - Exposes `execute_undo(patch_id)` called when the developer clicks "Approve & Execute Undo" on the Streamlit dashboard.
* **Plan Tier**: **Enterprise Edition Only**.

---

### USP 10: Single-Flight Mutex Concurrency Guard
* **Where It Lives**:
  - File: [`aegis_core/interceptor.py`](file:///d:/Work%20Folder/Arya's%20Projects/AntiGravity/Genesis%202026/aegis_core/interceptor.py)
  - Class: `SingleFlightGroup`
* **Architectural Layer**: **Layer 3: Interception & Concurrency Guard Layer**
* **Integration Points**:
  - Sits at the entrance of the tool calling pipeline.
  - Manages `asyncio.Future` promises keyed by `tool_name` to synchronize concurrent requests.
* **Plan Tier**: **All Tiers (Open-Source Community, Pro, Enterprise)**.

---

## 3. Runtime Lifecycle Execution Sequence

The diagram below highlights the precise point in time when each USP fires during the execution lifecycle:

```
[Agent Initiates Tool Call]
          │
          ▼
    ┌───────────┐
    │  USP 10   │  (Single-Flight Mutex: Acquire tool lock or wait on promise)
    └─────┬─────┘
          ▼
[Execute Downstream API Call]
          │
          ├─────────────────────────────────────────────────┐
          │ (HTTP 200 OK)                                   │ (HTTP 422 Error)
          ▼                                                 ▼
    ┌───────────┐                                     ┌───────────┐
    │   USP 5   │ (Semantic Invariant Check)          │   USP 6   │ (Sub-15ms AST Compiler parses error)
    └─────┬─────┘                                     └─────┬─────┘
          │                                                 ▼
          │ (If Invariant Fails)                      ┌───────────┐
          └──────────────────────────────────────────►│   USP 8   │ (Provenance Gate blocks fake data)
                                                      └─────┬─────┘
                                                            ▼
                                                      ┌───────────┐
                                                      │   USP 2   │ (Policy Governor scores blast radius)
                                                      └─────┬─────┘
                                                            ▼
                                                      ┌───────────┐
                                                      │   USP 1   │ (API Time Machine rechecks fixtures)
                                                      └─────┬─────┘
                                                            ▼
                                                      ┌───────────┐
                                                      │   USP 4   │ (MVCC Registry swaps pointer in RAM)
                                                      └─────┬─────┘
                                                            ▼
                                            [Resume Request with Transformed Payload]
                                                            │
                                                            ▼
                                                      ┌───────────┐
                                                      │   USP 3   │ (DAG Predictor pre-patches child tools)
                                                      └─────┬─────┘
                                                            │
                                  ┌─────────────────────────┴─────────────────────────┐
                                  ▼                                                   ▼
                            ┌───────────┐                                       ┌───────────┐
                            │   USP 9   │ (Log to Request Ledger & Gen SQL)     │   USP 7   │ (GitOps Auto-PR Bot)
                            └───────────┘                                       └───────────┘
```
