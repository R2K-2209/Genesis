# Basic Workflow & Real-World Scenarios Explained

> **Goal**: Explain the exact working of the system in simple, layman terms without using metaphors or analogies.  
> **Approach**: Direct explanations and concrete real-world software scenarios.

---

## Table of Contents
1. [Core Concepts in Simple Terms](#1-core-concepts-in-simple-terms)
   - [What is an AI Agent?](#what-is-an-ai-agent)
   - [What is an API and a Schema?](#what-is-an-api-and-a-schema)
   - [What is API Schema Drift?](#what-is-api-schema-drift)
2. [Why Normal AI Agents Break in Production](#2-why-normal-ai-agents-break-in-production)
3. [Real-World Scenario 1: University Student Records API](#3-real-world-scenario-1-university-student-records-api)
   - [The Setup](#the-setup)
   - [The Backend Code Update (The Drift)](#the-backend-code-update-the-drift)
   - [Case A: What Happens Without AegisRegistry (The Failure)](#case-a-what-happens-without-aegisregistry-the-failure)
   - [Case B: What Happens With AegisRegistry (The Fix)](#case-b-what-happens-with-aegisregistry-the-fix)
4. [Real-World Scenario 2: E-Commerce Order Management API](#4-real-world-scenario-2-e-commerce-order-management-api)
5. [The Step-by-Step Workflow of AegisRegistry](#5-the-step-by-step-workflow-of-aegisregistry)
6. [Summary of What Makes This Work](#6-summary-of-what-makes-this-work)

---

## 1. Core Concepts in Simple Terms

### What is an AI Agent?
An **AI Agent** is a program powered by a Large Language Model (such as Google Gemini or OpenAI GPT). 
Unlike a simple chatbot that only writes text answers, an agent can perform actions. It does this by calling external software functions called **Tools**.
* *Example*: If you ask the agent: *"Find the grades for student 123"*, the agent calls a tool that sends a request to the university database server.

### What is an API and a Schema?
* An **API (Application Programming Interface)** is the communication channel between two computer programs. The agent runs on one server; the university database runs on another.
* A **Schema** is the strict rulebook of how the data must be formatted when calling that API.
  * For example, the server's schema might say:
    > "You must send a JSON object with one key named `user_id`, and its value must be text (a string)."
    ```json
    {
      "user_id": "123"
    }
    ```

### What is API Schema Drift?
**Schema Drift** happens when backend software engineers change how their API works, but the AI agent is still using the old instructions.
This happens all the time in real companies:
* A developer renames a field from `user_id` to `student_id`.
* A developer changes the type from text (`"123"`) to a number (`123`).
* A developer moves the field inside another object: `{"target": {"id": 123}}`.
* A developer requires a new security header: `X-API-Version: 2026-10`.

When the backend changes, the old tool definition in the agent becomes invalid.

---

## 2. Why Normal AI Agents Break in Production

When backend engineers deploy a new API version, the AI agent has no idea the API changed. It still sends the old payload.
1. The backend server rejects the request with an error: **HTTP 422 Unprocessable Entity** (or **HTTP 400 Bad Request**).
2. Existing frameworks (like LangChain or AutoGen) receive this error text and dump it into the AI's chat prompt.
3. The LLM gets confused. It does not know how to update the tool's code. It tries sending the same payload again.
4. It loops 3 to 5 times, spends thousands of tokens, runs for 10 to 15 seconds, and finally **crashes with a fatal error**.
5. The end-user sees an error screen, and software engineers must be paged to manually rewrite the code.

Industry reports show that **over 40% of outages in long-running AI agents are caused by this exact issue**.

---

## 3. Real-World Scenario 1: University Student Records API

Let us walk through the exact benchmark scenario from the project specification.

### The Setup
A university uses an AI assistant to help professors look up student information.
* **Tool Name**: `get_student_info`
* **Agent's Stored Tool Schema (v1.0)**:
  ```json
  {
    "user_id": "string"
  }
  ```
* A professor types: *"Fetch the academic transcript for student 123."*
* The agent generates the API payload:
  ```json
  {
    "user_id": "123"
  }
  ```

---

### The Backend Code Update (The Drift)
Over the weekend, the university backend engineering team deploys a major database update.
The backend API (`POST /api/v1/students/records`) now enforces three new rules:
1. **Field Renamed and Nested**: The key `user_id` must now be inside a `target` object as `id` (`target.id`).
2. **Data Type Changed**: `id` must be an integer (`123`), not a string (`"123"`).
3. **Required Header Added**: Every call must include an HTTP header: `X-API-Version: 2026-10`.

Expected payload by the new backend:
```json
// Headers:
// X-API-Version: 2026-10

// Body:
{
  "target": {
    "id": 123
  }
}
```

---

### Case A: What Happens Without AegisRegistry (The Failure)
1. The agent sends: `{"user_id": "123"}` without the new header.
2. The server rejects it and returns **HTTP 422 Unprocessable Entity**:
   ```json
   {
     "detail": [
       {"loc": ["body", "target", "id"], "msg": "Field required", "type": "missing"},
       {"loc": ["header", "x-api-version"], "msg": "Header required", "type": "missing"}
     ]
   }
   ```
3. LangChain catches the 422 error and hands the raw error text back to the LLM.
4. The LLM reasons: *"The call failed. Let me retry."* It generates the same JSON again: `{"user_id": "123"}`.
5. The server rejects it again with HTTP 422.
6. The agent retries a third time.
7. **Result**:
   - Time elapsed: **12.4 seconds**.
   - Tokens burned: **4,620 tokens**.
   - Output: `MaxIterationsExceededError: Agent stopped due to iteration limit`.
   - The professor sees a red error box.

---

### Case B: What Happens With AegisRegistry (The Fix)
1. The agent sends: `{"user_id": "123"}`.
2. The server responds with **HTTP 422 Unprocessable Entity**.
3. **Aegis Intercepts**: Before LangChain or the LLM sees the error, AegisRegistry catches the 422 response.
4. **Deterministic AST Diagnosis**: 
   - Aegis does not call an LLM to read the error (which would take 4 to 8 seconds).
   - Instead, its internal Abstract Syntax Tree (AST) parser reads the structured `loc` paths in **12 milliseconds**:
     - It sees `target.id` is missing and maps the old `user_id` into it.
     - It sees the type must be an integer, so it converts `"123"` into `123`.
     - It sees `x-api-version` header is required, so it adds `X-API-Version: 2026-10`.
   - **Tokens used: 0. Latency: 12ms.**
5. **Anti-Hallucination Check**: Aegis verifies that all values came from the original request. Nothing was fabricated.
6. **In-Memory Hot-Patch**: Aegis compiles a lightweight transformation rule and updates the tool definition in computer memory (RAM).
7. **Seamless Retry**: Aegis resends the transformed request:
   ```json
   // Headers: X-API-Version: 2026-10
   {
     "target": {
       "id": 123
     }
   }
   ```
8. The server responds with **HTTP 200 OK**:
   ```json
   {
     "student_id": 123,
     "name": "Arya Stark",
     "gpa": 3.92,
     "major": "Computer Science"
   }
   ```
9. **Result**:
   - The professor gets the student's transcript on screen immediately.
   - **Total time taken: 0.52 seconds**.
   - The user never saw an error banner.
10. **Permanent Code Fix (Background)**:
    - Aegis logs the change in an SQLite database (the Request Ledger).
    - An automated background worker connects to GitHub and opens a Pull Request with updated code and unit tests.

---

## 4. Real-World Scenario 2: E-Commerce Order Management API

Consider an enterprise customer support agent handling order cancellations for an e-commerce platform.

### The Initial Setup
* **Tool**: `cancel_order`
* **Agent sends**:
  ```json
  POST /api/v2/orders/cancel
  Payload: { "order_id": "ORD-991" }
  ```

### The Drift
The e-commerce payment infrastructure migrates to a microservice that enforces:
1. Field rename: `order_id` $\to$ `cancellation_target.order_number`.
2. Type conversion: numeric order ID (`991`).
3. Mandatory parameter: `refund_reason`.

### How AegisRegistry Handles It:
1. Server returns HTTP 422.
2. Aegis AST compiler parses the error:
   - Maps `order_id` $\to$ `cancellation_target.order_number: 991`.
3. **The Provenance Gate Activates**:
   - Aegis notices that `refund_reason` is required.
   - It checks: *Was `refund_reason` provided in the conversation?*
   - If the user said: *"Cancel order ORD-991 because it arrived damaged"*, Aegis extracts `"arrived damaged"` and injects it.
   - If the user never stated a reason, Aegis **refuses to invent fake data** (like `"reason": "test"`). Instead, it pauses and prompts the user:
     > *"The updated system requires a reason for cancellation. Why would you like to cancel order ORD-991?"*
4. Once the reason is supplied, the call executes, and an inverse SQL script is stored in the **Request Ledger** in case the customer changes their mind and requests an undo.

---

## 5. The Step-by-Step Workflow of AegisRegistry

Here is the exact sequence of events that occurs when an API call is made:

```
[1. User asks question]
         │
         ▼
[2. AI Agent creates tool payload]
         │
         ▼
[3. Request enters Aegis Interceptor]
         │
         ├─► [Check Concurrency Mutex] (If another request is already healing this tool, wait 0.2s)
         │
         ▼
[4. Dispatch to External Server]
         │
         ├─────────────────────────────────────────┐
         ▼                                         ▼
   [HTTP 200 OK]                             [HTTP 400 or 422 Error]
         │                                         │
   [Check Semantic Invariant]                      ▼
   (Is body empty []?)              [5. AST Fast-Path Diagnosis (<15ms, 0 tokens)]
         │                                         │
         │                                         ├─► If unstructured error: Speculative LLM (<1.2s)
         │                                         ▼
         │                          [6. Anti-Hallucination Provenance Gate]
         │                                         │
         │                                         ├─► If missing business data: Ask user directly
         │                                         ▼
         │                          [7. In-Memory Hot-Patch (MVCC Swap in RAM)]
         │                                         │
         │                          [8. Sandboxed Test Replay (Verify fix is safe)]
         │                                         │
         │                          [9. Resend Original Request with Transformed Payload]
         │                                         │
         │                                         ▼
         └─────────────────────────────────► [HTTP 200 OK Returned]
                                                   │
                                                   ▼
                                     [10. Display Result to User (Total MTTR: 0.52s)]
                                                   │
                         ┌─────────────────────────┴─────────────────────────┐
                         ▼                                                   ▼
         [11. Save Trace in Request Ledger]               [12. Auto-open GitHub PR with Unit Tests]
         [Generate 1-Click Database Undo SQL]
```

---

## 6. Summary of What Makes This Work

1. **Catches Errors Before the Agent Dies**: Aegis sits between the agent and the server. The agent never sees the HTTP 422 error.
2. **Speed Over Slow LLMs**: By reading structured error dictionaries with an AST compiler in 12ms (0 tokens), Aegis completes the entire repair in **0.52 seconds**.
3. **No Downtime**: Fixes are applied directly in computer memory (RAM) using version pointers. No server restarts are needed.
4. **Data Safety**: It never hallucinates fake data to satisfy new fields.
5. **Permanent Fixes**: It automatically writes permanent code updates and unit tests to GitHub.
