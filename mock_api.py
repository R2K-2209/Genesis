"""
Mock API Server for AegisRegistry Demo
Simulates downstream enterprise microservices under runtime schema drift.
Features a live switchboard (/admin/mutate) to trigger synthetic breaking mutations on stage.
"""

from typing import Any, Dict, Optional
from fastapi import FastAPI, Header, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

app = FastAPI(
    title="Genesis Enterprise Student Records API",
    description="Mock Microservice demonstrating Runtime API Schema Drift (VESIT PS 01)",
    version="2.0.0"
)

# Simulated in-memory database
STUDENTS_DB = {
    123: {
        "id": 123,
        "name": "Ranjit Kadam",
        "department": "Computer Science & Engineering",
        "semester": 6,
        "cgpa": 9.42,
        "status": "Enrolled",
        "last_updated": "2026-10-15T09:30:00Z"
    },
    456: {
        "id": 456,
        "name": "Arya Bagul",
        "department": "Artificial Intelligence & Data Science",
        "semester": 6,
        "cgpa": 9.58,
        "status": "Enrolled",
        "last_updated": "2026-10-15T09:30:00Z"
    },
    789: {
        "id": 789,
        "name": "Saumya Bhide",
        "department": "Information Technology",
        "semester": 6,
        "cgpa": 9.35,
        "status": "Enrolled",
        "last_updated": "2026-10-15T09:30:00Z"
    }
}

# Mutation State Matrix
class MutationState:
    BASELINE = "baseline"            # Expects {"user_id": str}
    RENAME = "rename"                # Expects {"account_id": str}
    TYPE_CAST = "type_cast"          # Expects {"user_id": int}
    NESTING = "nesting"              # Expects {"target": {"id": int}}
    HEADER = "header"                # Requires "X-API-Version: 2026-10"
    COMPOUND = "compound"            # Expects {"target": {"id": int}} + Header "X-API-Version" (The Hackathon Stage Break)

current_mutation = MutationState.BASELINE

# Audit history of mutations triggered
mutation_history = [
    {"timestamp": "INITIAL", "scenario": MutationState.BASELINE, "note": "Initial v1.0 contract active"}
]

# Database mutation ledger (for 1-click rollback testing)
applied_compensations = []


@app.get("/")
def root():
    return {
        "service": "Genesis Student Records Microservice",
        "status": "ONLINE",
        "active_mutation": current_mutation,
        "docs_url": "/docs"
    }


@app.get("/admin/status")
def get_admin_status():
    """Returns the current mutation scenario and system telemetry."""
    return {
        "active_mutation": current_mutation,
        "available_scenarios": [
            MutationState.BASELINE,
            MutationState.RENAME,
            MutationState.TYPE_CAST,
            MutationState.NESTING,
            MutationState.HEADER,
            MutationState.COMPOUND
        ],
        "history": mutation_history,
        "active_records_count": len(STUDENTS_DB)
    }


@app.post("/admin/mutate")
def set_mutation(scenario: str):
    """
    Live on-stage switchboard to toggle breaking schema mutations.
    """
    global current_mutation
    valid_scenarios = [
        MutationState.BASELINE,
        MutationState.RENAME,
        MutationState.TYPE_CAST,
        MutationState.NESTING,
        MutationState.HEADER,
        MutationState.COMPOUND
    ]
    if scenario not in valid_scenarios:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scenario '{scenario}'. Choose from {valid_scenarios}"
        )
    
    current_mutation = scenario
    mutation_history.append({"scenario": scenario, "active": True})
    return {
        "success": True,
        "message": f"Mutation state switched to: '{scenario}'",
        "active_mutation": current_mutation
    }


@app.post("/api/students")
async def fetch_student_record(
    request: Request,
    x_api_version: Optional[str] = Header(None, alias="X-API-Version")
):
    """
    Primary endpoint that mutates under runtime schema drift.
    Returns 422 with structured Pydantic-compliant error trees when the contract is violated.
    """
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": [{"loc": ["body"], "msg": "Invalid JSON payload", "type": "value_error.json"}]}
        )

    errors = []

    # 1. Header Enforcement Check (Active in HEADER and COMPOUND modes)
    if current_mutation in (MutationState.HEADER, MutationState.COMPOUND):
        if not x_api_version:
            errors.append({
                "loc": ["header", "X-API-Version"],
                "msg": "Mandatory security header 'X-API-Version' is missing",
                "type": "value_error.missing_header"
            })
        elif x_api_version != "2026-10":
            errors.append({
                "loc": ["header", "X-API-Version"],
                "msg": f"Unsupported API version '{x_api_version}'. Required: '2026-10'",
                "type": "value_error.invalid_header_version"
            })

    # 2. Payload Schema Validation based on active mutation
    extracted_id = None

    if current_mutation in (MutationState.BASELINE, MutationState.HEADER):
        # Expects: {"user_id": str}
        if "user_id" not in payload:
            errors.append({
                "loc": ["body", "user_id"],
                "msg": "field required",
                "type": "value_error.missing"
            })
        else:
            val = payload["user_id"]
            if not isinstance(val, str):
                errors.append({
                    "loc": ["body", "user_id"],
                    "msg": "value is not a valid string",
                    "type": "type_error.str"
                })
            else:
                try:
                    extracted_id = int(val)
                except ValueError:
                    extracted_id = val

    elif current_mutation == MutationState.RENAME:
        # Expects: {"account_id": str}
        if "account_id" not in payload:
            errors.append({
                "loc": ["body", "account_id"],
                "msg": "field required. Legacy 'user_id' has been deprecated and renamed to 'account_id'",
                "type": "value_error.missing"
            })
        else:
            try:
                extracted_id = int(payload["account_id"])
            except ValueError:
                extracted_id = payload["account_id"]

    elif current_mutation == MutationState.TYPE_CAST:
        # Expects: {"user_id": int}
        if "user_id" not in payload:
            errors.append({
                "loc": ["body", "user_id"],
                "msg": "field required",
                "type": "value_error.missing"
            })
        elif not isinstance(payload["user_id"], int) or isinstance(payload["user_id"], bool):
            errors.append({
                "loc": ["body", "user_id"],
                "msg": f"value is not a valid integer; got '{type(payload['user_id']).__name__}'",
                "type": "type_error.integer"
            })
        else:
            extracted_id = payload["user_id"]

    elif current_mutation in (MutationState.NESTING, MutationState.COMPOUND):
        # Expects: {"target": {"id": int}}
        if "target" not in payload:
            errors.append({
                "loc": ["body", "target"],
                "msg": "field required: payload topology has shifted to nested object 'target'",
                "type": "value_error.missing"
            })
        elif not isinstance(payload["target"], dict):
            errors.append({
                "loc": ["body", "target"],
                "msg": "value must be an object containing 'id'",
                "type": "type_error.dict"
            })
        elif "id" not in payload["target"]:
            errors.append({
                "loc": ["body", "target", "id"],
                "msg": "field required inside 'target' object",
                "type": "value_error.missing"
            })
        elif not isinstance(payload["target"]["id"], int) or isinstance(payload["target"]["id"], bool):
            errors.append({
                "loc": ["body", "target", "id"],
                "msg": f"value is not a valid integer; got '{type(payload['target']['id']).__name__}'",
                "type": "type_error.integer"
            })
        else:
            extracted_id = payload["target"]["id"]

    # 3. If errors occurred, emit standard HTTP 422 RFC-7807 Problem Tree
    if errors:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Unprocessable Entity",
                "status_code": 422,
                "mutation_context": current_mutation,
                "detail": errors
            }
        )

    # 4. Success path: return student record
    record = STUDENTS_DB.get(extracted_id)
    if not record:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "Not Found", "message": f"Student ID {extracted_id} not found in database."}
        )

    return {
        "status": "success",
        "status_code": 200,
        "mutation_served": current_mutation,
        "data": record
    }


@app.get("/api/students/{student_id}")
def get_student_read_only(student_id: int):
    """
    Read-only endpoint used by the API Time Machine for safe regression replay tests.
    """
    record = STUDENTS_DB.get(student_id)
    if not record:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"status": "success", "data": record}


@app.post("/api/admin/undo_sql")
def execute_undo_sql(compensating_query: Dict[str, Any]):
    """
    Endpoint for 1-Click Database Compensating Undo execution.
    """
    applied_compensations.append(compensating_query)
    return {
        "success": True,
        "message": "Compensating SQL transaction executed successfully. Database state restored.",
        "query_executed": compensating_query
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
