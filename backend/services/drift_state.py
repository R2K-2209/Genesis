"""
API Schema Drift Registry and Request Mutator for Genesis / AegisRegistry.
Maintains active drift states selected in the API Catalog and applies them
to API calls made by the Autonomous Agent and LangChain.
"""

from typing import Dict, Any, Optional, Tuple

# In-memory store of active schema drifts:
# endpoint_id -> {"drift_mode": str, "custom_params": dict, "custom_path": str}
ACTIVE_API_DRIFTS: Dict[str, Dict[str, Any]] = {}

# Map alias IDs to canonical catalog IDs so simple-books and api_books_search match
CANONICAL_ID_MAP = {
    "api_students_list": "simple-students",
    "simple-students": "simple-students",
    "api_courses_catalog": "simple-courses",
    "simple-courses": "simple-courses",
    "api_books_search": "simple-books",
    "simple-books": "simple-books",
    "api_departments_list": "simple-departments",
    "simple-departments": "simple-departments",
    "api_clubs_directory": "simple-clubs",
    "simple-clubs": "simple-clubs",
    "api_student_academic_summary": "medium-student-summary",
    "medium-student-summary": "medium-student-summary",
    "api_course_syllabus": "medium-syllabus",
    "medium-syllabus": "medium-syllabus",
    "api_student_finance_ledger": "medium-student-finance",
    "medium-student-finance": "medium-student-finance",
    "api_student_graduation_audit": "complex-graduation-audit",
    "complex-graduation-audit": "complex-graduation-audit",
    "api_student_transcript_audit": "complex-transcript",
    "complex-transcript": "complex-transcript",
    "api_course_prerequisites_dag": "complex-prerequisite-dag",
    "complex-prerequisite-dag": "complex-prerequisite-dag",
    "api_student_scholarship_match": "complex-scholarship-matcher",
    "complex-scholarship-matcher": "complex-scholarship-matcher",
    "api_dept_faculty_workload": "complex-dept-workload",
    "complex-dept-workload": "complex-dept-workload",
    "api_library_card_loans": "medium-library-loans",
    "medium-library-loans": "medium-library-loans",
}

# Parameter rename mapping for Drift 1
RENAME_RULES = {
    "status": "student_status",
    "query": "title_or_author",
    "search": "keyword",
    "student_id": "candidate_id",
    "course_id": "class_id",
    "card_id": "borrower_card_no",
    "invoice_id": "bill_id",
    "amount": "payment_value",
    "page": "drift_page",
    "limit": "drift_limit",
    "min_credits": "credits_floor",
}


def normalize_endpoint_id(ep_id: str) -> str:
    return CANONICAL_ID_MAP.get(ep_id, ep_id)


def set_api_drift(endpoint_id: str, drift_mode: str, custom_params: Dict[str, Any] = None, custom_path: str = None):
    canonical_id = normalize_endpoint_id(endpoint_id)
    if drift_mode == "healthy" or not drift_mode:
        ACTIVE_API_DRIFTS.pop(canonical_id, None)
    else:
        ACTIVE_API_DRIFTS[canonical_id] = {
            "endpoint_id": canonical_id,
            "drift_mode": drift_mode,
            "custom_params": custom_params or {},
            "custom_path": custom_path
        }


def get_api_drift(endpoint_id: str) -> Optional[Dict[str, Any]]:
    canonical_id = normalize_endpoint_id(endpoint_id)
    return ACTIVE_API_DRIFTS.get(canonical_id)


def get_all_drifts() -> Dict[str, Any]:
    return dict(ACTIVE_API_DRIFTS)


def clear_all_drifts():
    ACTIVE_API_DRIFTS.clear()


def apply_drift_to_request(
    endpoint_id: str,
    path: str,
    method: str,
    params: Dict[str, Any],
    explicit_drifts: Optional[Dict[str, Any]] = None
) -> Tuple[str, Dict[str, Any], Optional[str]]:
    """
    Mutates path and parameters if this endpoint currently has an active drift.
    Returns: (mutated_path, mutated_params, active_drift_mode)
    """
    canonical_id = normalize_endpoint_id(endpoint_id)
    drift_info = None

    # Check explicit drifts passed in the chat request first
    if explicit_drifts:
        for k, v in explicit_drifts.items():
            if normalize_endpoint_id(k) == canonical_id:
                if isinstance(v, dict):
                    drift_info = v
                elif isinstance(v, str):
                    drift_info = {"drift_mode": v}
                break

    # Fall back to server's shared in-memory drift store
    if not drift_info:
        drift_info = ACTIVE_API_DRIFTS.get(canonical_id)

    if not drift_info or drift_info.get("drift_mode") in (None, "healthy"):
        return path, params, None

    drift_mode = drift_info.get("drift_mode")
    mutated_path = path
    mutated_params = dict(params)

    # 1. Parameter Renamed
    if drift_mode == "param_renamed":
        new_params = {}
        for k, v in mutated_params.items():
            renamed = RENAME_RULES.get(k, f"drift_{k}")
            new_params[renamed] = v
        # Also check path variables (e.g. {student_id} -> {candidate_id})
        for orig, renamed in RENAME_RULES.items():
            placeholder = f"{{{orig}}}"
            if placeholder in mutated_path:
                mutated_path = mutated_path.replace(placeholder, f"{{{renamed}}}")
        mutated_params = new_params

    # 2. Data Type Mutation (Type Mismatch)
    elif drift_mode == "type_mutated":
        for k, v in list(mutated_params.items()):
            if isinstance(v, (int, float)) or k.endswith("_id") or k in ("page", "limit", "min_credits"):
                mutated_params[k] = f"UUID_ERR_TYPE_{v}_STR"

    # 3. Nested Object Required (filter[...])
    elif drift_mode == "nested_wrapped":
        new_params = {}
        for k, v in mutated_params.items():
            new_params[f"filter[{k}]"] = v
        mutated_params = new_params

    # 4. Missing Mandatory Field
    elif drift_mode == "missing_required":
        # Remove primary query/path param
        keys_to_remove = [k for k in mutated_params.keys() if k.endswith("_id") or k in ("query", "status", "search")]
        for k in keys_to_remove:
            mutated_params.pop(k, None)

    # 5. Route Migration (/api/v2 path)
    elif drift_mode == "route_deprecated":
        mutated_path = mutated_path.replace("/api/v1/", "/api/v2/")

    return mutated_path, mutated_params, drift_mode
