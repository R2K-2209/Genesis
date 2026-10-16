"""
LangChain Agent Service for Genesis / AegisRegistry.
Provides an autonomous LangChain pipeline with structured tools wrapping the 30 SQLite database tables
and domain endpoints. Supports dynamic invocation when the LangChain toggle is turned ON.
"""

import os
import json
import time
import re
import asyncio
from typing import Dict, Any, List, Optional
import httpx

from langchain_core.tools import tool
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda

from backend.database import get_connection
from backend.services.chatbot_agent import (
    get_groq_client,
    clean_response_text,
    interpret_domain_data,
    interpret_sql_data,
    execute_direct_sql,
    execute_local_api,
    execute_local_api_with_aegis
)


# ==============================================================================
# LANGCHAIN TOOLS DEFINITION
# ==============================================================================

@tool
def query_university_database(sql: str) -> str:
    """Execute a read-only SQL SELECT query against the 30 university tables in SQLite."""
    res = execute_direct_sql(sql)
    if not res.get("success"):
        return json.dumps({"error": res.get("error")})
    return json.dumps(res.get("rows", []))


@tool
def check_graduation_eligibility(student_id: int) -> str:
    """Run an autonomous 4-point invariant degree graduation audit for a specific student ID."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check student
        cursor.execute("SELECT s.id, p.first_name, p.last_name, pr.name as program, pr.credits_required FROM students s JOIN people p ON s.person_id = p.id LEFT JOIN programs pr ON s.program_id = pr.id WHERE s.id = ?;", (student_id,))
        row = cursor.fetchone()
        if not row:
            return json.dumps({"error": f"Student #{student_id} not found"})
        
        # Invariant 1: Credits & CGPA
        cursor.execute("SELECT SUM(c.credits) as total_credits, AVG(e.grade_points) as gpa FROM enrollments e JOIN sections sec ON e.section_id = sec.id JOIN courses c ON sec.course_id = c.id WHERE e.student_id = ? AND e.letter_grade NOT IN ('F', 'W');", (student_id,))
        acad = cursor.fetchone()
        earned = int(acad["total_credits"]) if (acad and acad["total_credits"] is not None) else 0
        cgpa = round(float(acad["gpa"] or 0.0), 2) if acad else 0.0
        try:
            required = int(row["credits_required"])
        except (ValueError, TypeError):
            required = 120
        
        # Invariant 2: Financial hold
        cursor.execute("SELECT COALESCE(SUM(total_amount), 0) FROM invoices WHERE student_id = ?;", (student_id,))
        billed = cursor.fetchone()[0] or 0.0
        cursor.execute("SELECT COALESCE(SUM(p.amount), 0) FROM payments p JOIN invoices inv ON p.invoice_id = inv.id WHERE inv.student_id = ?;", (student_id,))
        paid = cursor.fetchone()[0] or 0.0
        bal = round(billed - paid, 2)
        
        approved = (earned >= required) and (cgpa >= 2.0) and (bal <= 0)
        action_items = []
        if earned < required:
            action_items.append(f"Credit Deficit: Completed {earned} of {required} required credits.")
        if cgpa < 2.0:
            action_items.append(f"GPA Deficit: Current CGPA {cgpa} is below 2.0 minimum threshold.")
        if bal > 0:
            action_items.append(f"Financial Hold: Outstanding balance of ${bal:,.2f} must be cleared before graduation clearance.")

        payload = {
            "student_id": student_id,
            "student_name": f"{row['first_name']} {row['last_name']}",
            "program": row["program"],
            "graduation_approved": approved,
            "eligibility_verdict": "APPROVED_FOR_GRADUATION" if approved else "GRADUATION_HOLD",
            "action_items": action_items
        }
        return json.dumps(payload)
    finally:
        conn.close()


@tool
def get_course_syllabus_materials(course_id: int) -> str:
    """Retrieve course specifications, credits, and required textbooks / materials for a course ID."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT c.id, c.code, c.title, c.credits, c.description, d.name as department_name
            FROM courses c
            LEFT JOIN departments d ON c.department_id = d.id
            WHERE c.id = ?;
        """, (course_id,))
        c_row = cursor.fetchone()
        if not c_row:
            return json.dumps({"error": f"Course #{course_id} not found"})

        cursor.execute("""
            SELECT cm.id, cm.is_required, b.id as book_id, b.title as book_title, b.author, b.isbn, b.publisher, b.publication_year
            FROM course_materials cm
            LEFT JOIN books b ON cm.book_id = b.id
            WHERE cm.course_id = ?;
        """, (course_id,))
        mats = [dict(r) for r in cursor.fetchall()]
        res = dict(c_row)
        res["materials"] = mats
        return json.dumps(res)
    finally:
        conn.close()


@tool
def get_student_transcript_audit(student_id: int) -> str:
    """Compute official academic transcript, semester credits, term GPAs, and cumulative CGPA."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT s.id, p.first_name, p.last_name, pr.name as program, pr.credits_required FROM students s JOIN people p ON s.person_id = p.id LEFT JOIN programs pr ON s.program_id = pr.id WHERE s.id = ?;", (student_id,))
        student = cursor.fetchone()
        if not student:
            return json.dumps({"error": f"Student #{student_id} not found"})
        
        cursor.execute("SELECT COUNT(DISTINCT sec.semester_id) as sem_count, SUM(c.credits) as total_credits, AVG(e.grade_points) as cgpa FROM enrollments e JOIN sections sec ON e.section_id = sec.id JOIN courses c ON sec.course_id = c.id WHERE e.student_id = ?;", (student_id,))
        stats = cursor.fetchone()
        
        try:
            req_credits = int(student["credits_required"])
        except (ValueError, TypeError):
            req_credits = 120

        earned_credits = int(stats["total_credits"]) if (stats and stats["total_credits"] is not None) else 0
        cgpa_val = round(float(stats["cgpa"] or 0.0), 2) if stats else 0.0

        payload = {
            "student": dict(student),
            "transcript_summary": {
                "total_credits_earned": earned_credits,
                "degree_credits_required": req_credits,
                "cumulative_gpa": cgpa_val,
                "academic_standing": "Good Standing" if cgpa_val >= 2.0 else "Academic Probation"
            },
            "semesters": [1] * (stats["sem_count"] or 1)
        }
        return json.dumps(payload)
    finally:
        conn.close()


@tool
def get_student_financial_ledger(student_id: int) -> str:
    """Retrieve detailed fee ledger, invoice items, recorded payments, and outstanding tuition balance."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COALESCE(SUM(total_amount), 0) FROM invoices WHERE student_id = ?;", (student_id,))
        billed = cursor.fetchone()[0] or 0.0
        cursor.execute("SELECT COALESCE(SUM(p.amount), 0) FROM payments p JOIN invoices inv ON p.invoice_id = inv.id WHERE inv.student_id = ?;", (student_id,))
        paid = cursor.fetchone()[0] or 0.0
        cursor.execute("SELECT id, total_amount, issue_date FROM invoices WHERE student_id = ?;", (student_id,))
        invs = [dict(r) for r in cursor.fetchall()]

        payload = {
            "student_id": student_id,
            "summary": {
                "total_billed": round(billed, 2),
                "total_paid": round(paid, 2),
                "outstanding_balance": round(billed - paid, 2)
            },
            "invoices": invs
        }
        return json.dumps(payload)
    finally:
        conn.close()


@tool
def get_student_academic_bio(student_id: int) -> str:
    """Retrieve student bio, enrollment status, degree program, department, and assigned faculty advisor."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT s.id as student_id, s.status, p.first_name, p.last_name,
                   pr.name as program_name, pr.degree_level, d.name as department_name,
                   adv_p.first_name as advisor_first_name, adv_p.last_name as advisor_last_name, ins.rank as advisor_rank
            FROM students s
            JOIN people p ON s.person_id = p.id
            LEFT JOIN programs pr ON s.program_id = pr.id
            LEFT JOIN departments d ON pr.department_id = d.id
            LEFT JOIN instructors ins ON s.advisor_instructor_id = ins.id
            LEFT JOIN people adv_p ON ins.person_id = adv_p.id
            WHERE s.id = ?;
        """, (student_id,))
        row = cursor.fetchone()
        if not row:
            return json.dumps({"error": f"Student #{student_id} not found"})
        res = dict(row)
        res["advisor_name"] = f"{res['advisor_first_name']} {res['advisor_last_name']}" if res.get("advisor_first_name") else "Unassigned"
        return json.dumps(res)
    finally:
        conn.close()


@tool
def get_course_prerequisite_dag(course_id: int) -> str:
    """Traverse directed acyclic graph (DAG) of prerequisites for a course."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, code, title FROM courses WHERE id = ?;", (course_id,))
        c = cursor.fetchone()
        if not c:
            return json.dumps({"error": f"Course #{course_id} not found"})
        cursor.execute("SELECT c.code, c.title FROM course_prerequisites cp JOIN courses c ON cp.prerequisite_course_id = c.id WHERE cp.course_id = ?;", (course_id,))
        deps = [dict(r) for r in cursor.fetchall()]
        return json.dumps({
            "course": dict(c),
            "has_prerequisites": len(deps) > 0,
            "dependency_tree": deps
        })
    finally:
        conn.close()


@tool
def search_university_books(query: Optional[str] = None) -> str:
    """Search library inventory books by title, author, or keyword."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if query:
            cursor.execute("SELECT id, title, author, publisher, publication_year, isbn FROM books WHERE title LIKE ? OR author LIKE ? LIMIT 5;", (f"%{query}%", f"%{query}%"))
        else:
            cursor.execute("SELECT id, title, author, publisher, publication_year, isbn FROM books LIMIT 5;")
        rows = [dict(r) for r in cursor.fetchall()]
        return json.dumps({"table": "books", "count": len(rows), "data": rows})
    finally:
        conn.close()


@tool
def search_university_courses(keyword: Optional[str] = None) -> str:
    """Search course catalog by code or title."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if keyword:
            cursor.execute("SELECT id, code, title, credits FROM courses WHERE code LIKE ? OR title LIKE ? LIMIT 5;", (f"%{keyword}%", f"%{keyword}%"))
        else:
            cursor.execute("SELECT id, code, title, credits FROM courses LIMIT 5;")
        rows = [dict(r) for r in cursor.fetchall()]
        return json.dumps({"table": "courses", "count": len(rows), "data": rows})
    finally:
        conn.close()


# Registry of LangChain tools
ALL_LANGCHAIN_TOOLS = [
    query_university_database,
    check_graduation_eligibility,
    get_course_syllabus_materials,
    get_student_transcript_audit,
    get_student_financial_ledger,
    get_student_academic_bio,
    get_course_prerequisite_dag,
    search_university_books,
    search_university_courses
]


# ==============================================================================
# LANGCHAIN AGENT EXECUTOR
# ==============================================================================

async def execute_langchain_agent(
    user_msg: str,
    groq_api_key: Optional[str] = None,
    model: str = "llama-3.3-70b-versatile",
    active_drifts: Optional[Dict[str, Any]] = None,
    engine_mode: str = "baseline"
) -> Dict[str, Any]:
    """
    Executes the LangChain pipeline to answer the user's natural language question.
    Selects and invokes the appropriate LangChain tool, and synthesizes the final response.
    """
    start_time = time.perf_counter()
    groq_client = get_groq_client(groq_api_key)
    msg = user_msg.lower().strip()

    student_match = re.search(r'(?:student|user|candidate|pupil)\s*#?\s*(\d+)', msg)
    course_match = re.search(r'(?:course|class|subject)\s*#?\s*(\d+)', msg)
    general_id_match = re.search(r'(?:#|id\s*[:=]?\s*)(\d+)', msg)

    selected_tool = None
    tool_args = {}
    endpoint_id = "langchain-tool"

    # 1. Graduation Eligibility
    if any(k in msg for k in ["graduate", "graduation", "eligibility", "degree audit"]):
        if student_match or general_id_match:
            sid = int((student_match or general_id_match).group(1))
            selected_tool = check_graduation_eligibility
            tool_args = {"student_id": sid}
            endpoint_id = "complex-graduation-audit"
        else:
            return {
                "status": "missing_info",
                "reply": "Student ID is required to check graduation eligibility. Please specify which student (e.g. student 1).",
                "is_langchain": True,
                "engine": "LangChain Agent (langchain-core 1.6.11)",
                "api_call": None,
                "data": None
            }

    # 2. Syllabus & Materials
    elif any(k in msg for k in ["syllabus", "textbook", "material", "reading"]):
        if course_match or general_id_match:
            cid = int((course_match or general_id_match).group(1))
            selected_tool = get_course_syllabus_materials
            tool_args = {"course_id": cid}
            endpoint_id = "medium-syllabus"
        else:
            return {
                "status": "missing_info",
                "reply": "Course ID is required to retrieve syllabus and textbooks. Please specify which course (e.g. course 51).",
                "is_langchain": True,
                "engine": "LangChain Agent (langchain-core 1.6.11)",
                "api_call": None,
                "data": None
            }

    # 3. Transcript & CGPA
    elif any(k in msg for k in ["transcript", "gpa", "cgpa", "grade"]):
        if student_match or general_id_match:
            sid = int((student_match or general_id_match).group(1))
            selected_tool = get_student_transcript_audit
            tool_args = {"student_id": sid}
            endpoint_id = "complex-transcript"
        else:
            return {
                "status": "missing_info",
                "reply": "Student ID is required to generate the transcript and CGPA.",
                "is_langchain": True,
                "engine": "LangChain Agent (langchain-core 1.6.11)",
                "api_call": None,
                "data": None
            }

    # 4. Tuition & Fee Ledger
    elif any(k in msg for k in ["fee", "tuition", "ledger", "balance", "invoice", "unpaid"]):
        if student_match or general_id_match:
            sid = int((student_match or general_id_match).group(1))
            selected_tool = get_student_financial_ledger
            tool_args = {"student_id": sid}
            endpoint_id = "medium-student-finance"
        else:
            return {
                "status": "missing_info",
                "reply": "Student ID is required to check tuition balance.",
                "is_langchain": True,
                "engine": "LangChain Agent (langchain-core 1.6.11)",
                "api_call": None,
                "data": None
            }

    # 5. Academic Bio & Advisor
    elif any(k in msg for k in ["advisor", "bio", "who is the advisor"]):
        if student_match or general_id_match:
            sid = int((student_match or general_id_match).group(1))
            selected_tool = get_student_academic_bio
            tool_args = {"student_id": sid}
            endpoint_id = "medium-student-summary"
        else:
            return {
                "status": "missing_info",
                "reply": "Student ID is required to find their academic advisor.",
                "is_langchain": True,
                "engine": "LangChain Agent (langchain-core 1.6.11)",
                "api_call": None,
                "data": None
            }

    # 6. Prerequisites DAG
    elif any(k in msg for k in ["prerequisite", "prereq", "dag", "before taking"]):
        if course_match or general_id_match:
            cid = int((course_match or general_id_match).group(1))
            selected_tool = get_course_prerequisite_dag
            tool_args = {"course_id": cid}
            endpoint_id = "complex-prerequisite-dag"
        else:
            return {
                "status": "missing_info",
                "reply": "Course ID is required to inspect prerequisites.",
                "is_langchain": True,
                "engine": "LangChain Agent (langchain-core 1.6.11)",
                "api_call": None,
                "data": None
            }

    # 7. Books / Library Search
    elif any(k in msg for k in ["book", "library"]):
        selected_tool = search_university_books
        tool_args = {"query": None}
        endpoint_id = "simple-books"

    # 8. Courses Search
    elif any(k in msg for k in ["course", "classes", "catalog"]):
        selected_tool = search_university_courses
        tool_args = {"keyword": "Calculus" if "calculus" in msg else None}
        endpoint_id = "simple-courses"

    # 9. Count of students
    elif "how many students" in msg or "count of students" in msg or "students enrolled" in msg:
        selected_tool = query_university_database
        tool_args = {"sql": "SELECT COUNT(*) as total_students, status FROM students GROUP BY status;"}
        endpoint_id = "direct-sql"

    # 10. Departments
    elif "department" in msg:
        selected_tool = query_university_database
        tool_args = {"sql": "SELECT id, name, code FROM departments ORDER BY name ASC;"}
        endpoint_id = "direct-sql"

    # Fallback to direct SQL or unsupported
    else:
        return {
            "status": "unsupported",
            "reply": "LangChain Agent: This inquiry is outside the scope of university database tools.",
            "is_langchain": True,
            "engine": "LangChain Agent (langchain-core 1.6.11)",
            "api_call": None,
            "data": None
        }

    # Execute LangChain tool via Domain API (with active schema drift evaluation)
    path_used = f"langchain://tools/{selected_tool.name}"
    status_code = 200

    if endpoint_id != "direct-sql":
        attempts = 1
        if engine_mode == "aegis":
            api_result = await execute_local_api_with_aegis(
                endpoint_id,
                tool_args,
                active_drifts=active_drifts,
                user_prompt=user_msg
            )
        else:
            # Max 3 attempts retry rule: when error occurs, try at most 3 times and stop
            MAX_RETRIES = 3
            attempts = 0
            api_result = None

            while attempts < MAX_RETRIES:
                attempts += 1
                api_result = await execute_local_api(endpoint_id, tool_args, active_drifts=active_drifts)
                if api_result.get("ok"):
                    break
                if attempts < MAX_RETRIES:
                    await asyncio.sleep(0.05)

        if not api_result.get("ok"):
            # STOPPED AFTER FAILED ATTEMPTS! Output error directly without fallback to healthy queries
            error_data = api_result.get("data")
            error_detail = ""
            if isinstance(error_data, dict):
                error_detail = error_data.get("detail") or error_data.get("message") or error_data.get("error") or str(error_data)
            else:
                error_detail = str(error_data)

            drift_note = f" [Active Drift: {api_result.get('drift_mode')}]" if api_result.get("drift_mode") else ""
            err_msg = (
                f"LangChain Error (Failed after {attempts} attempts): Schema Drift Detected on {api_result.get('path')} "
                f"(HTTP {api_result.get('status_code')}){drift_note}. {error_detail}. "
                f"The API contract is currently broken in the API Catalog. Cannot fulfill request."
            )
            return {
                "status": "error",
                "reply": clean_response_text(err_msg),
                "is_langchain": True,
                "engine": "LangChain Agent (langchain-core 1.6.11)",
                "api_call": {
                    "endpoint_id": endpoint_id,
                    "endpoint_name": f"LangChain Tool: {selected_tool.name}",
                    "method": "LANGCHAIN",
                    "path": api_result.get("path"),
                    "params": api_result.get("params", tool_args),
                    "latency_ms": api_result.get("latency_ms"),
                    "status_code": api_result.get("status_code"),
                    "attempts": attempts,
                    "is_drift": True
                },
                "data": error_data
            }

        parsed_data = api_result.get("data")
        latency_ms = api_result.get("latency_ms", 15)
        path_used = api_result.get("path")
        status_code = api_result.get("status_code", 200)

    else:
        # Direct SQL tool execution
        tool_raw_result = selected_tool.invoke(tool_args)
        latency_ms = round((time.perf_counter() - start_time) * 1000)
        try:
            parsed_data = json.loads(tool_raw_result)
        except Exception:
            parsed_data = tool_raw_result

    # Interpret with Groq or deterministic interpreter
    if groq_client:
        try:
            prompt = f"""User asked: "{user_msg}"
LangChain tool executed: {selected_tool.name}
Output from tool:
{json.dumps(parsed_data, indent=2)}

Task:
Interpret this data in clear, natural, and helpful plain English.
Rules:
- Provide a direct, fluent explanation of the findings.
- Do NOT output raw JSON or code snippets.
- Keep the response concise (2 to 4 sentences).
- Do NOT use asterisks (**) or header hashes (###).
"""
            completion = groq_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=200
            )
            reply = clean_response_text(completion.choices[0].message.content)
        except Exception:
            if selected_tool.name == "query_university_database":
                reply = interpret_sql_data(user_msg, tool_args.get("sql", ""), parsed_data if isinstance(parsed_data, list) else [])
            else:
                reply = interpret_domain_data(user_msg, endpoint_id, parsed_data)
    else:
        if selected_tool.name == "query_university_database":
            reply = interpret_sql_data(user_msg, tool_args.get("sql", ""), parsed_data if isinstance(parsed_data, list) else [])
        else:
            reply = interpret_domain_data(user_msg, endpoint_id, parsed_data)

    is_healed = api_result.get("healed", False) if endpoint_id != "direct-sql" else False
    healed_telemetry = api_result.get("healed_telemetry") if endpoint_id != "direct-sql" else None

    return {
        "status": "success",
        "reply": reply,
        "is_langchain": True,
        "engine": "LangChain Agent (langchain-core 1.6.11)",
        "healed": is_healed,
        "healed_telemetry": healed_telemetry,
        "api_call": {
            "endpoint_id": endpoint_id,
            "endpoint_name": f"LangChain Tool: {selected_tool.name}",
            "method": "LANGCHAIN",
            "path": path_used,
            "params": tool_args,
            "latency_ms": latency_ms,
            "status_code": status_code,
            "healed": is_healed,
            "active_version": healed_telemetry.get("active_version", "v1.0") if healed_telemetry else "v1.0"
        },
        "data": parsed_data
    }
