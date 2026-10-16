"""
FastAPI Backend Server for Genesis / AegisRegistry.
Exposes database management endpoints, high-level university domain APIs (Read, Write, Edit, Delete),
and dynamic mock API endpoints for self-healing agent testing.
"""

import os
import time
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, Query, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

SERVER_START_TIME = time.time()

from backend.database import (
    DB_PATH,
    DEFAULT_JSON_PATH,
    init_database_from_json,
    get_table_counts,
    get_tables_metadata,
    get_table_rows,
    get_record,
    insert_record,
    update_record,
    delete_record,
    get_student_full_profile,
    get_connection
)
from backend.routes.api_catalog import router as catalog_router
from backend.services.chatbot_agent import process_chat_message, ChatMessageRequest

app = FastAPI(
    title="Genesis / AegisRegistry API Server",
    description="High-performance backend for University Database CRUD and Self-Healing Agent API Gateway",
    version="2.0.0"
)

app.include_router(catalog_router)

@app.post("/api/chat")
async def chat_with_agent(payload: ChatMessageRequest):
    """
    Plain English Chatbot Endpoint powered by Groq AI.
    Converts plain English into correct API calls, checks for missing data,
    handles unsupported requests, and synthesizes answers.
    """
    return await process_chat_message(payload)

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "*",
    "Access-Control-Allow-Headers": "*",
}

@app.middleware("http")
async def schema_drift_middleware(request: Request, call_next):
    """Runtime Schema Drift Interceptor for hackathon testing and demo."""
    query_params = dict(request.query_params)

    # Check for parameter rename mutations
    DRIFT_RENAMES = {
        "student_state": ("status", "Parameter 'status' was renamed to 'student_state'"),
        "student_status": ("status", "Parameter 'status' was renamed to 'student_status'"),
        "candidate_id": ("student_id", "Parameter 'student_id' was renamed to 'candidate_id'"),
        "pupil_id": ("student_id", "Parameter 'student_id' was renamed to 'pupil_id'"),
        "class_id": ("course_id", "Parameter 'course_id' was renamed to 'class_id'"),
        "keyword": ("search", "Parameter 'search' was renamed to 'keyword'"),
        "search_term": ("query", "Parameter 'query' was renamed to 'search_term'"),
        "title_or_author": ("query", "Parameter 'query' was renamed to 'title_or_author'"),
        "bill_id": ("invoice_id", "Parameter 'invoice_id' was renamed to 'bill_id'"),
        "borrower_card_no": ("card_id", "Parameter 'card_id' was renamed to 'borrower_card_no'"),
        "payment_value": ("amount", "Parameter 'amount' was renamed to 'payment_value'")
    }

    for drifted_param, (original, msg) in DRIFT_RENAMES.items():
        if drifted_param in query_params:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=422,
                headers=CORS_HEADERS,
                content={
                    "status": "error",
                    "error_code": "SCHEMA_DRIFT_DETECTED",
                    "drift_type": "PARAMETER_RENAMED",
                    "detail": f"Schema Drift Detected: {msg}. The server contract expects '{original}' but received '{drifted_param}'.",
                    "expected_field": original,
                    "received_field": drifted_param,
                    "self_healing_hint": f"Aegis Registry healing adapter required to map '{drifted_param}' -> '{original}'"
                }
            )

    # Check for nested wrapper mutations in query parameters
    if any(k.startswith("filter[") or k == "filter" for k in query_params):
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=422,
            headers=CORS_HEADERS,
            content={
                "status": "error",
                "error_code": "SCHEMA_DRIFT_DETECTED",
                "drift_type": "NESTED_OBJECT_WRAP",
                "detail": "Schema Drift Detected: Parameters received inside nested 'filter' wrapper object. Current endpoint v1 only accepts top-level flat parameters.",
                "self_healing_hint": "Aegis Registry healing adapter required to unwrap nested 'filter' parameters."
            }
        )

    # Check for route migration / deprecated endpoint drift
    if request.url.path.startswith("/api/v2/"):
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=404,
            headers=CORS_HEADERS,
            content={
                "status": "error",
                "error_code": "ROUTE_VERSION_DRIFT",
                "drift_type": "ROUTE_MIGRATION",
                "detail": f"Schema Drift Detected: Route '{request.url.path}' not found. Current production contract is hosted under '/api/v1/'.",
                "self_healing_hint": "Aegis Registry healing adapter required to alias route to '/api/v1/'."
            }
        )

    response = await call_next(request)
    return response


class DriftUpdateRequest(BaseModel):
    endpoint_id: str
    drift_mode: str = "healthy"
    custom_params: Optional[Dict[str, Any]] = None
    custom_path: Optional[str] = None


@app.get("/api/v1/drift-state")
def get_drift_state_endpoint():
    from backend.services.drift_state import get_all_drifts
    return {"status": "ok", "drifts": get_all_drifts()}


@app.post("/api/v1/drift-state")
def update_drift_state_endpoint(payload: DriftUpdateRequest):
    from backend.services.drift_state import set_api_drift, get_all_drifts
    set_api_drift(payload.endpoint_id, payload.drift_mode, payload.custom_params, payload.custom_path)
    return {"status": "ok", "active_mode": payload.drift_mode, "drifts": get_all_drifts()}


@app.post("/api/v1/drift-state/reset")
def reset_drift_state_endpoint():
    from backend.services.drift_state import clear_all_drifts
    clear_all_drifts()
    return {"status": "ok", "drifts": {}}


@app.get("/api/v1/aegis/ledger")
def get_aegis_ledger_endpoint(limit: int = 50):
    from backend.services.aegis_ledger import aegis_request_ledger
    records = aegis_request_ledger.get_recent_records(limit=limit)
    return {"status": "ok", "count": len(records), "records": records}


@app.post("/api/v1/aegis/reset")
def reset_aegis_mvcc_endpoint():
    from backend.services.aegis_mvcc import aegis_mvcc_registry
    from backend.services.aegis_ledger import aegis_request_ledger
    aegis_mvcc_registry.reset_all()
    aegis_request_ledger.clear_ledger()
    return {"status": "ok", "message": "AegisRegistry MVCC snapshots and request ledger reset to clean baseline v1.0."}


# Active schema mutation state for testing API drift
MUTATION_STATE = {
    "scenario": "clean",  # options: 'clean', 'rename', 'type_cast', 'nesting', 'header', 'compound'
    "active_version": "v1.0"
}


# ==============================================================================
# DATABASE INSPECTION & GENERAL CRUD ENDPOINTS
# ==============================================================================

@app.get("/api/health")
def health_check():
    uptime = time.time() - SERVER_START_TIME
    return {
        "status": "online",
        "service": "Genesis Backend",
        "database_exists": os.path.exists(DB_PATH),
        "mutation_state": MUTATION_STATE,
        "uptime_seconds": round(uptime, 1),
        "start_time": SERVER_START_TIME
    }


@app.get("/api/database/overview")
def get_database_overview():
    """Returns database size, table count, and total record count."""
    counts = get_table_counts()
    file_size_bytes = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
    return {
        "total_tables": len(counts),
        "total_records": sum(counts.values()),
        "file_size_bytes": file_size_bytes,
        "file_size_mb": round(file_size_bytes / (1024 * 1024), 2),
        "table_summary": counts
    }


@app.get("/api/database/tables")
def list_tables_metadata():
    """Returns metadata for all 30 tables: columns, types, pk, and row count."""
    return get_tables_metadata()


@app.get("/api/database/tables/{table_name}")
def get_table_data(
    table_name: str,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(25, ge=1, le=500, description="Rows per page"),
    search: Optional[str] = Query(None, description="Search keyword across all columns"),
    sort_by: Optional[str] = Query(None, description="Column to sort by"),
    sort_order: str = Query("ASC", pattern="^(ASC|DESC|asc|desc)$", description="Sort direction")
):
    """Paginated data retrieval with search and sorting for any table."""
    try:
        data = get_table_rows(
            table_name=table_name,
            page=page,
            limit=limit,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )
        return data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/database/tables/{table_name}/{record_id}")
def get_table_record(table_name: str, record_id: int):
    """Retrieve a single row from any table by ID."""
    rec = get_record(table_name, record_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Record {record_id} not found in '{table_name}'")
    return rec


@app.post("/api/database/tables/{table_name}")
def create_table_record(table_name: str, payload: Dict[str, Any]):
    """Insert a new record into any table (Write)."""
    try:
        created = insert_record(table_name, payload)
        return {"status": "success", "message": "Record created successfully", "record": created}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to insert record: {str(e)}")


@app.put("/api/database/tables/{table_name}/{record_id}")
def update_table_record(table_name: str, record_id: int, payload: Dict[str, Any]):
    """Edit/Update an existing record by ID."""
    existing = get_record(table_name, record_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Record {record_id} not found in '{table_name}'")
    try:
        updated = update_record(table_name, record_id, payload)
        return {"status": "success", "message": "Record updated successfully", "record": updated}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update record: {str(e)}")


@app.delete("/api/database/tables/{table_name}/{record_id}")
def delete_table_record(table_name: str, record_id: int):
    """Delete a record by ID."""
    existing = get_record(table_name, record_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Record {record_id} not found in '{table_name}'")
    success = delete_record(table_name, record_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete record")
    return {"status": "success", "message": f"Record {record_id} deleted successfully from '{table_name}'"}


@app.post("/api/database/reset")
def reset_database():
    """Re-initializes the database from the original JSON file."""
    try:
        stats = init_database_from_json(force=True)
        return {
            "status": "success",
            "message": "Database reset to original JSON state successfully!",
            "tables_restored": len(stats),
            "total_records": sum(stats.values())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")


# ==============================================================================
# HIGH-LEVEL DOMAIN APIS: STUDENTS, COURSES, INVOICES, PAYMENTS
# ==============================================================================

@app.get("/api/students")
def list_students(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None)
):
    """Read students with joined personal info, program, and department."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        where = ""
        params: List[Any] = []
        if search:
            where = """
                WHERE p.first_name LIKE ? OR p.last_name LIKE ? OR p.email LIKE ?
                   OR pr.name LIKE ? OR d.name LIKE ? OR s.status LIKE ?
            """
            params = [f"%{search}%"] * 6

        count_sql = f"""
            SELECT COUNT(*)
            FROM students s
            LEFT JOIN people p ON s.person_id = p.id
            LEFT JOIN programs pr ON s.program_id = pr.id
            LEFT JOIN departments d ON pr.department_id = d.id
            {where}
        """
        cursor.execute(count_sql, params)
        total = cursor.fetchone()[0]

        offset = (page - 1) * limit
        sql = f"""
            SELECT s.id, s.status, s.enrollment_date,
                   p.first_name, p.last_name, p.email, p.phone,
                   pr.name as program_name, pr.degree_level,
                   d.name as department_name
            FROM students s
            LEFT JOIN people p ON s.person_id = p.id
            LEFT JOIN programs pr ON s.program_id = pr.id
            LEFT JOIN departments d ON pr.department_id = d.id
            {where}
            ORDER BY s.id ASC
            LIMIT ? OFFSET ?
        """
        cursor.execute(sql, params + [limit, offset])
        students = [dict(r) for r in cursor.fetchall()]

        return {
            "students": students,
            "total": total,
            "page": page,
            "limit": limit
        }
    finally:
        conn.close()


@app.get("/api/students/{student_id}")
def get_student_details(student_id: int):
    """Read complete student profile including courses, live CGPA, and billing."""
    profile = get_student_full_profile(student_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Student ID {student_id} not found.")
    return profile


class StudentCreateSchema(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = "(555) 000-0000"
    gender: Optional[str] = "other"
    date_of_birth: Optional[str] = "2000-01-01"
    program_id: Optional[int] = 1
    advisor_instructor_id: Optional[int] = 1
    status: Optional[str] = "enrolled"


@app.post("/api/students")
def create_student(payload: StudentCreateSchema):
    """Write: Create a new student (creates person + student records)."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Create person
        cursor.execute("""
            INSERT INTO people (first_name, last_name, email, phone, gender, date_of_birth)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (payload.first_name, payload.last_name, payload.email, payload.phone, payload.gender, payload.date_of_birth))
        person_id = cursor.lastrowid

        # Create student
        import datetime
        today = datetime.date.today().isoformat()
        cursor.execute("""
            INSERT INTO students (person_id, program_id, advisor_instructor_id, status, enrollment_date)
            VALUES (?, ?, ?, ?, ?);
        """, (person_id, payload.program_id, payload.advisor_instructor_id, payload.status, today))
        student_id = cursor.lastrowid
        conn.commit()

        return get_student_full_profile(student_id)
    finally:
        conn.close()


@app.put("/api/students/{student_id}")
def update_student(student_id: int, payload: Dict[str, Any]):
    """Edit: Updates student or personal fields."""
    existing = get_student_full_profile(student_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found.")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check student table fields
        student_fields = ["status", "program_id", "advisor_instructor_id"]
        stu_updates = {k: v for k, v in payload.items() if k in student_fields}
        if stu_updates:
            set_parts = [f'"{k}" = ?' for k in stu_updates.keys()]
            cursor.execute(f'UPDATE students SET {", ".join(set_parts)} WHERE id = ?', list(stu_updates.values()) + [student_id])

        # Check people fields
        cursor.execute("SELECT person_id FROM students WHERE id = ?", (student_id,))
        person_id = cursor.fetchone()[0]
        person_fields = ["first_name", "last_name", "email", "phone"]
        p_updates = {k: v for k, v in payload.items() if k in person_fields}
        if p_updates:
            set_parts = [f'"{k}" = ?' for k in p_updates.keys()]
            cursor.execute(f'UPDATE people SET {", ".join(set_parts)} WHERE id = ?', list(p_updates.values()) + [person_id])

        conn.commit()
        return get_student_full_profile(student_id)
    finally:
        conn.close()


@app.delete("/api/students/{student_id}")
def delete_student_endpoint(student_id: int):
    """Delete student record."""
    profile = get_student_full_profile(student_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found.")
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT person_id FROM students WHERE id = ?", (student_id,))
        row = cursor.fetchone()
        person_id = row[0] if row else None

        cursor.execute("DELETE FROM enrollments WHERE student_id = ?", (student_id,))
        cursor.execute("DELETE FROM invoices WHERE student_id = ?", (student_id,))
        cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
        if person_id:
            cursor.execute("DELETE FROM people WHERE id = ?", (person_id,))
        conn.commit()
        return {"status": "success", "message": f"Student {student_id} deleted successfully"}
    finally:
        conn.close()


# ==============================================================================
# DYNAMIC DRIFT TESTING APIS (FOR SELF-HEALING SHOWCASE)
# ==============================================================================

@app.post("/api/admin/mutate")
def set_mutation_scenario(scenario: str = Query("clean", pattern="^(clean|rename|type_cast|nesting|header|compound)$")):
    """
    Sets the active API drift scenario to test the self-healing agent:
      - clean: Standard v1.0 schema (expects `{"user_id": str}`)
      - rename: Field renamed (expects `{"account_id": str}`)
      - type_cast: Type cast (expects `{"user_id": int}`)
      - nesting: Deep object nesting (expects `{"target": {"id": int}}`)
      - header: Requires `X-API-Version: 2026-10`
      - compound: All breaking changes simultaneously!
    """
    MUTATION_STATE["scenario"] = scenario
    MUTATION_STATE["active_version"] = "v1.0" if scenario == "clean" else "v1.1"
    return {
        "status": "success",
        "current_scenario": MUTATION_STATE["scenario"],
        "active_version": MUTATION_STATE["active_version"],
        "description": f"Target API schema mutated to scenario: {scenario}"
    }


@app.post("/api/mock/students")
async def mock_students_endpoint(request: Request):
    """
    Simulates a microservice endpoint that experiences live schema drift.
    Validates payload based on MUTATION_STATE.
    Returns 422 Unprocessable Entity with RFC-7807/Pydantic validation errors if contract is breached.
    """
    headers = request.headers
    scenario = MUTATION_STATE["scenario"]

    # Check header drift
    if scenario in ("header", "compound"):
        api_version = headers.get("x-api-version")
        if not api_version or api_version != "2026-10":
            raise HTTPException(
                status_code=422,
                detail=[{
                    "loc": ["header", "x-api-version"],
                    "msg": "Missing or invalid protocol header. Expected 'X-API-Version: 2026-10'",
                    "type": "value_error.missing_header"
                }]
            )

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(
            status_code=422,
            detail=[{"loc": ["body"], "msg": "Invalid JSON body", "type": "value_error.json"}]
        )

    student_id = None

    if scenario == "clean":
        # v1.0 schema: {"user_id": str}
        if "user_id" not in body:
            raise HTTPException(
                status_code=422,
                detail=[{"loc": ["body", "user_id"], "msg": "Field required", "type": "missing"}]
            )
        try:
            student_id = int(body["user_id"])
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail=[{"loc": ["body", "user_id"], "msg": "Input should be a valid string representation of integer", "type": "string_type"}]
            )

    elif scenario == "rename":
        # Renamed: {"account_id": str}
        if "account_id" not in body:
            raise HTTPException(
                status_code=422,
                detail=[
                    {"loc": ["body", "account_id"], "msg": "Field 'account_id' required (formerly user_id)", "type": "missing"}
                ]
            )
        student_id = int(body["account_id"])

    elif scenario == "type_cast":
        # Type cast: {"user_id": int}
        val = body.get("user_id")
        if val is None:
            raise HTTPException(
                status_code=422,
                detail=[{"loc": ["body", "user_id"], "msg": "Field required", "type": "missing"}]
            )
        if not isinstance(val, int) or isinstance(val, bool):
            raise HTTPException(
                status_code=422,
                detail=[{"loc": ["body", "user_id"], "msg": "Input should be a valid integer, received string", "type": "int_parsing"}]
            )
        student_id = val

    elif scenario == "nesting":
        # Deep nesting: {"target": {"id": int}}
        target = body.get("target")
        if not isinstance(target, dict) or "id" not in target:
            raise HTTPException(
                status_code=422,
                detail=[
                    {"loc": ["body", "target", "id"], "msg": "Field required inside target object", "type": "missing"}
                ]
            )
        student_id = int(target["id"])

    elif scenario == "compound":
        # Compound: {"target": {"id": int}} + header
        target = body.get("target")
        errors = []
        if not isinstance(target, dict):
            errors.append({"loc": ["body", "target"], "msg": "Field 'target' object required", "type": "missing"})
        elif "id" not in target:
            errors.append({"loc": ["body", "target", "id"], "msg": "Field 'id' required inside target", "type": "missing"})
        elif not isinstance(target["id"], int) or isinstance(target["id"], bool):
            errors.append({"loc": ["body", "target", "id"], "msg": "Input should be a valid integer", "type": "int_parsing"})

        if errors:
            raise HTTPException(status_code=422, detail=errors)
        student_id = int(target["id"])

    # If valid, retrieve real data from SQLite!
    profile = get_student_full_profile(student_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Student ID {student_id} not found in database.")

    return {
        "status": "success",
        "api_version": MUTATION_STATE["active_version"],
        "scenario_matched": scenario,
        "data": profile
    }


# =========================================================================
# AEGIS ENTERPRISE GOVERNANCE & ARCHITECTURE LAYER ENDPOINTS (LAYERS 6, 7, 8, 9)
# =========================================================================

from backend.services.aegis_ledger import aegis_request_ledger
from backend.services.aegis_mvcc import aegis_mvcc_registry
from backend.services.aegis_gitops import aegis_gitops_daemon
from backend.services.aegis_time_machine import aegis_time_machine


@app.get("/api/aegis/ledger")
async def get_aegis_ledger(limit: int = 50, endpoint: Optional[str] = None, drift_type: Optional[str] = None):
    """Layer 8: Query the immutable request ledger with filter support."""
    records = aegis_request_ledger.get_recent_records(
        limit=limit,
        endpoint_filter=endpoint,
        drift_filter=drift_type
    )
    return {"status": "success", "total": len(records), "records": records}


@app.post("/api/aegis/undo/{record_id}")
async def execute_1click_undo(record_id: str):
    """Layer 8: Execute 1-Click Compensating SQL rollback bounded to request_trace_id."""
    success, message = aegis_request_ledger.execute_1click_undo(record_id)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"status": "success", "message": message, "record_id": record_id}


@app.get("/api/aegis/pull-requests")
async def get_aegis_pull_requests():
    """Layer 9: Retrieve auto-generated GitHub Pull Requests from GitOps Daemon."""
    prs = aegis_gitops_daemon.get_all_pull_requests()
    return {"status": "success", "total": len(prs), "pull_requests": [vars(p) for p in prs]}


@app.get("/api/aegis/mvcc/snapshots")
async def get_mvcc_snapshots():
    """Layer 6: View all active in-memory MVCC schema versions and fingerprints."""
    snapshots = {
        ep: {
            "version": s.version,
            "tool_name": s.tool_name,
            "fingerprint": s.fingerprint,
            "created_at": s.created_at,
            "applied_count": s.applied_count,
            "has_transform": s.transform_lambda is not None
        }
        for ep, s in aegis_mvcc_registry._active_snapshots.items()
    }
    return {"status": "success", "snapshots": snapshots}


@app.post("/api/aegis/mvcc/reset")
async def reset_mvcc_snapshots():
    """Layer 6: Reset in-memory MVCC snapshots back to clean v1.0 baseline."""
    aegis_mvcc_registry.reset_all()
    return {"status": "success", "message": "All MVCC snapshots reset to v1.0 baseline"}


@app.get("/api/aegis/time-machine/fixtures")
async def get_time_machine_fixtures(endpoint: Optional[str] = None):
    """Layer 7: Query historical sandbox fixtures stored in ring buffers."""
    if endpoint:
        fixtures = aegis_time_machine.get_fixtures(endpoint)
        return {"status": "success", "endpoint": endpoint, "fixtures": [vars(f) for f in fixtures]}
    all_fixtures = {
        ep: [vars(f) for f in buf]
        for ep, buf in aegis_time_machine._fixture_buffers.items()
    }
    return {"status": "success", "fixtures": all_fixtures}

