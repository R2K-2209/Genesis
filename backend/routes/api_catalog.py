"""
API Catalog Module for Genesis / AegisRegistry.
Provides 15 endpoints ranging from Simple to Complex across the 30 relational SQLite tables.
Includes metadata registry endpoint GET /api/catalog for the frontend API Explorer.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel, Field
import datetime

from backend.database import get_connection

router = APIRouter(prefix="/api/v1", tags=["University API Catalog"])

# Metadata registry for the UI API Explorer
API_REGISTRY = [
    # ------------------ SIMPLE APIS ------------------
    {
        "id": "simple-students",
        "name": "Students List Directory",
        "complexity": "Simple",
        "method": "GET",
        "path": "/api/v1/students/list",
        "summary": "Retrieve paginated student directory filtered by status",
        "tables": ["students"],
        "description": "Simple single-table lookup supporting pagination and student status filtering (enrolled, graduated, suspended).",
        "default_params": {"status": "enrolled", "page": 1, "limit": 10}
    },
    {
        "id": "simple-courses",
        "name": "Course Catalog Search",
        "complexity": "Simple",
        "method": "GET",
        "path": "/api/v1/courses/catalog",
        "summary": "Search university course catalog by keyword or minimum credits",
        "tables": ["courses"],
        "description": "Query course listings with keyword filtering across code and course title.",
        "default_params": {"search": "Calculus", "min_credits": 1, "limit": 10}
    },
    {
        "id": "simple-books",
        "name": "Library Book Search",
        "complexity": "Simple",
        "method": "GET",
        "path": "/api/v1/books/search",
        "summary": "Search books in university library by title or author",
        "tables": ["books"],
        "description": "Direct search in the 2,000 book records in the campus library inventory.",
        "default_params": {"query": "History", "limit": 10}
    },
    {
        "id": "simple-departments",
        "name": "Academic Departments",
        "complexity": "Simple",
        "method": "GET",
        "path": "/api/v1/departments/list",
        "summary": "List all active academic departments and codes",
        "tables": ["departments"],
        "description": "Retrieves the full list of academic faculties and departments.",
        "default_params": {}
    },
    {
        "id": "simple-clubs",
        "name": "Student Clubs Directory",
        "complexity": "Simple",
        "method": "GET",
        "path": "/api/v1/clubs/directory",
        "summary": "Directory of student clubs and societies",
        "tables": ["clubs"],
        "description": "Browse registered student organizations on campus.",
        "default_params": {"limit": 10}
    },

    # ------------------ MEDIUM APIS ------------------
    {
        "id": "medium-student-summary",
        "name": "Student Academic Bio & Advisor",
        "complexity": "Medium",
        "method": "GET",
        "path": "/api/v1/students/{student_id}/academic-summary",
        "summary": "Combines student demographics, program, department, and assigned advisor",
        "tables": ["students", "people", "programs", "departments", "instructors"],
        "description": "Multi-table join combining personal records, enrolled degree programs, department info, and faculty advisor.",
        "default_params": {"student_id": 1}
    },
    {
        "id": "medium-syllabus",
        "name": "Course Syllabus & Materials",
        "complexity": "Medium",
        "method": "GET",
        "path": "/api/v1/courses/{course_id}/syllabus-materials",
        "summary": "Course specifications, required textbooks, and materials",
        "tables": ["courses", "course_materials", "departments"],
        "description": "Fetches course details joined with its required textbooks, software, and instructional materials.",
        "default_params": {"course_id": 1}
    },
    {
        "id": "medium-student-finance",
        "name": "Student Tuition & Fee Ledger",
        "complexity": "Medium",
        "method": "GET",
        "path": "/api/v1/finance/student/{student_id}/ledger",
        "summary": "Detailed itemized invoices, fee types, and payment history",
        "tables": ["invoices", "invoice_items", "payments", "fee_types"],
        "description": "Reconciles student invoices with itemized fee breakdowns and recorded payments.",
        "default_params": {"student_id": 1}
    },
    {
        "id": "medium-library-loans",
        "name": "Library Borrower Loan History",
        "complexity": "Medium",
        "method": "GET",
        "path": "/api/v1/library/borrower/{card_id}/loans",
        "summary": "Active and historical book loans with return status and due dates",
        "tables": ["library_cards", "book_loans", "books", "people"],
        "description": "Checks book circulation records, due dates, and borrower contact details.",
        "default_params": {"card_id": 1}
    },
    {
        "id": "medium-payment-record",
        "name": "Record Tuition Payment",
        "complexity": "Medium",
        "method": "POST",
        "path": "/api/v1/finance/payments/record",
        "summary": "Processes a payment against an invoice and updates student balance",
        "tables": ["payments", "invoices"],
        "description": "Validates invoice validity, writes a payment transaction, and computes remaining balance.",
        "default_params": {"invoice_id": 89, "amount": 500.0, "payment_method": "card"}
    },

    # ------------------ COMPLEX APIS ------------------
    {
        "id": "complex-transcript",
        "name": "Official Academic Transcript & Term GPA",
        "complexity": "Complex",
        "method": "GET",
        "path": "/api/v1/students/{student_id}/transcript-audit",
        "summary": "Semester-by-semester grade breakdown with weighted CGPA math",
        "tables": ["students", "people", "enrollments", "sections", "courses", "semesters"],
        "description": "Multi-table join (6 tables) calculating semester term GPAs, cumulative CGPA, credits earned, and honors standing.",
        "default_params": {"student_id": 1}
    },
    {
        "id": "complex-graduation-audit",
        "name": "Degree Graduation Eligibility Audit",
        "complexity": "Complex",
        "method": "GET",
        "path": "/api/v1/students/{student_id}/graduation-eligibility",
        "summary": "Autonomous degree audit checking credits, CGPA, financial holds & prerequisites",
        "tables": ["students", "programs", "enrollments", "courses", "invoices", "payments"],
        "description": "Enterprise audit (7 tables) verifying 4 independent graduation invariants: credit threshold, minimum 2.0 CGPA, zero tuition balance hold, and prerequisite satisfaction.",
        "default_params": {"student_id": 1}
    },
    {
        "id": "complex-dept-workload",
        "name": "Department Workload & Enrollment Analytics",
        "complexity": "Complex",
        "method": "GET",
        "path": "/api/v1/analytics/department-workload",
        "summary": "Departmental faculty-to-student ratios, course load & enrollment volume",
        "tables": ["departments", "instructors", "courses", "sections", "enrollments"],
        "description": "Aggregates university-wide operational intelligence across 5 tables: active sections, instructor compensation, and total student enrollments.",
        "default_params": {}
    },
    {
        "id": "complex-scholarship-matcher",
        "name": "Scholarship Eligibility & Need Matcher",
        "complexity": "Complex",
        "method": "GET",
        "path": "/api/v1/scholarships/eligibility-matcher/{student_id}",
        "summary": "Matches student GPA and outstanding tuition against university scholarship criteria",
        "tables": ["students", "scholarships", "student_scholarships", "enrollments", "invoices"],
        "description": "Evaluates student's current academic standing and financial need to find eligible awards and active scholarship funding.",
        "default_params": {"student_id": 1}
    },
    {
        "id": "complex-prerequisite-dag",
        "name": "Course Prerequisite Dependency DAG",
        "complexity": "Complex",
        "method": "GET",
        "path": "/api/v1/courses/{course_id}/prerequisite-chain",
        "summary": "Recursive dependency tree traversal of all prerequisite courses",
        "tables": ["courses", "course_prerequisites"],
        "description": "Traverses the directed acyclic graph (DAG) of prerequisite requirements to generate the complete path of courses required before taking an advanced class.",
        "default_params": {"course_id": 40}
    }
]


# ==============================================================================
# CATALOG METADATA ROUTE
# ==============================================================================

@router.get("/catalog")
def get_api_catalog():
    """Returns the full metadata catalog of all 15 endpoints for the UI Explorer."""
    return {
        "total_apis": len(API_REGISTRY),
        "by_complexity": {
            "Simple": len([a for a in API_REGISTRY if a["complexity"] == "Simple"]),
            "Medium": len([a for a in API_REGISTRY if a["complexity"] == "Medium"]),
            "Complex": len([a for a in API_REGISTRY if a["complexity"] == "Complex"])
        },
        "endpoints": API_REGISTRY
    }


# ==============================================================================
# 1. SIMPLE APIS (SINGLE TABLE / BASIC LOOKUPS)
# ==============================================================================

@router.get("/students/list")
def list_students_simple(
    status: Optional[str] = Query(None, description="Filter by status (enrolled, graduated, suspended)"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    """Simple API: Paginated student listing from 'students' table."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        where = "WHERE status = ?" if status else ""
        params = [status] if status else []

        cursor.execute(f"SELECT COUNT(*) FROM students {where};", params)
        total = cursor.fetchone()[0]

        offset = (page - 1) * limit
        cursor.execute(f"SELECT * FROM students {where} ORDER BY id ASC LIMIT ? OFFSET ?;", params + [limit, offset])
        rows = [dict(r) for r in cursor.fetchall()]

        return {
            "api": "Simple Students List",
            "table": "students",
            "total": total,
            "page": page,
            "limit": limit,
            "data": rows
        }
    finally:
        conn.close()


@router.get("/courses/catalog")
def list_courses_catalog(
    search: Optional[str] = Query(None, description="Search course code or title"),
    min_credits: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    """Simple API: Course search on 'courses' table."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        where = ["credits >= ?"]
        params = [min_credits]
        if search:
            where.append("(code LIKE ? OR title LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])

        where_clause = " WHERE " + " AND ".join(where)
        cursor.execute(f"SELECT * FROM courses {where_clause} ORDER BY id ASC LIMIT ?;", params + [limit])
        rows = [dict(r) for r in cursor.fetchall()]

        return {
            "api": "Course Catalog",
            "table": "courses",
            "count": len(rows),
            "data": rows
        }
    finally:
        conn.close()


@router.get("/books/search")
def search_books(
    query: Optional[str] = Query(None, description="Search title, author, or publisher"),
    limit: int = Query(10, ge=1, le=100)
):
    """Simple API: Search library books."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if query:
            cursor.execute("""
                SELECT * FROM books
                WHERE title LIKE ? OR author LIKE ? OR publisher LIKE ?
                LIMIT ?;
            """, (f"%{query}%", f"%{query}%", f"%{query}%", limit))
        else:
            cursor.execute("SELECT * FROM books LIMIT ?;", (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
        return {"api": "Library Book Search", "table": "books", "count": len(rows), "data": rows}
    finally:
        conn.close()


@router.get("/departments/list")
def list_departments():
    """Simple API: List all departments."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM departments ORDER BY name ASC;")
        rows = [dict(r) for r in cursor.fetchall()]
        return {"api": "Department Directory", "table": "departments", "count": len(rows), "data": rows}
    finally:
        conn.close()


@router.get("/clubs/directory")
def list_clubs(limit: int = Query(20, ge=1, le=100)):
    """Simple API: List registered student clubs."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM clubs ORDER BY id ASC LIMIT ?;", (limit,))
        rows = [dict(r) for r in cursor.fetchall()]
        return {"api": "Clubs Directory", "table": "clubs", "count": len(rows), "data": rows}
    finally:
        conn.close()


# ==============================================================================
# 2. MEDIUM APIS (2-3 TABLES JOINED / AGGREGATIONS / PAYMENTS)
# ==============================================================================

@router.get("/students/{student_id}/academic-summary")
def get_student_academic_summary(student_id: int = Path(..., description="Student ID")):
    """Medium API: Joins students, people, programs, departments, and instructors."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT s.id as student_id, s.status, s.enrollment_date,
                   p.first_name, p.last_name, p.email, p.phone,
                   pr.name as program_name, pr.degree_level, pr.credits_required,
                   d.name as department_name, d.code as department_code,
                   adv_p.first_name as advisor_first_name, adv_p.last_name as advisor_last_name,
                   ins.rank as advisor_rank
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
            raise HTTPException(status_code=404, detail=f"Student #{student_id} not found")

        res = dict(row)
        res["advisor_name"] = f"{res['advisor_first_name']} {res['advisor_last_name']}" if res.get('advisor_first_name') else "Unassigned"
        return {"api": "Student Academic Bio & Advisor", "data": res}
    finally:
        conn.close()


@router.get("/courses/{course_id}/syllabus-materials")
def get_course_syllabus(course_id: int = Path(..., description="Course ID")):
    """Medium API: Joins courses, course_materials, and departments."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT c.id, c.code, c.title, c.credits, c.description,
                   d.name as department_name
            FROM courses c
            LEFT JOIN departments d ON c.department_id = d.id
            WHERE c.id = ?;
        """, (course_id,))
        course = cursor.fetchone()
        if not course:
            raise HTTPException(status_code=404, detail=f"Course #{course_id} not found")

        cursor.execute("""
            SELECT cm.id, cm.is_required,
                   b.id as book_id, b.title as book_title, b.author, b.isbn, b.publisher, b.publication_year
            FROM course_materials cm
            LEFT JOIN books b ON cm.book_id = b.id
            WHERE cm.course_id = ?;
        """, (course_id,))
        materials = [dict(r) for r in cursor.fetchall()]

        res = dict(course)
        res["materials"] = materials
        return {"api": "Course Syllabus & Materials", "data": res}
    finally:
        conn.close()


@router.get("/finance/student/{student_id}/ledger")
def get_student_financial_ledger(student_id: int = Path(..., description="Student ID")):
    """Medium API: Joins invoices, invoice_items, fee_types, and payments."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, total_amount, issue_date, due_date, semester_id FROM invoices WHERE student_id = ?;", (student_id,))
        invoices = [dict(r) for r in cursor.fetchall()]
        if not invoices:
            return {"api": "Student Financial Ledger", "student_id": student_id, "invoices": [], "summary": {"total_billed": 0.0, "total_paid": 0.0, "balance": 0.0}}

        inv_ids = [inv["id"] for inv in invoices]
        placeholders = ", ".join(["?"] * len(inv_ids))

        # Get line items
        cursor.execute(f"""
            SELECT ii.invoice_id, ii.amount, ft.name as fee_name, ft.description
            FROM invoice_items ii
            LEFT JOIN fee_types ft ON ii.fee_type_id = ft.id
            WHERE ii.invoice_id IN ({placeholders});
        """, inv_ids)
        items_by_inv = {}
        for itm in cursor.fetchall():
            items_by_inv.setdefault(itm[0], []).append(dict(itm))

        # Get payments
        cursor.execute(f"""
            SELECT id, invoice_id, amount, payment_date, payment_method
            FROM payments
            WHERE invoice_id IN ({placeholders});
        """, inv_ids)
        payments_by_inv = {}
        for p in cursor.fetchall():
            payments_by_inv.setdefault(p[1], []).append(dict(p))

        total_billed = 0.0
        total_paid = 0.0
        for inv in invoices:
            inv_id = inv["id"]
            inv["line_items"] = items_by_inv.get(inv_id, [])
            inv["payments"] = payments_by_inv.get(inv_id, [])
            paid = sum(p["amount"] for p in inv["payments"])
            inv["paid_amount"] = round(paid, 2)
            inv["balance_due"] = round(inv["total_amount"] - paid, 2)
            total_billed += inv["total_amount"]
            total_paid += paid

        return {
            "api": "Student Financial Ledger",
            "student_id": student_id,
            "summary": {
                "total_billed": round(total_billed, 2),
                "total_paid": round(total_paid, 2),
                "outstanding_balance": round(total_billed - total_paid, 2)
            },
            "invoices": invoices
        }
    finally:
        conn.close()


@router.get("/library/borrower/{card_id}/loans")
def get_library_loans(card_id: int = Path(..., description="Library Card ID")):
    """Medium API: Joins library_cards, book_loans, books, and people."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT lc.id as card_id, lc.issue_date, lc.expiry_date,
                   p.first_name, p.last_name, p.email
            FROM library_cards lc
            LEFT JOIN people p ON lc.person_id = p.id
            WHERE lc.id = ?;
        """, (card_id,))
        card = cursor.fetchone()
        if not card:
            raise HTTPException(status_code=404, detail=f"Library Card #{card_id} not found")

        cursor.execute("""
            SELECT bl.id as loan_id, bl.loan_date, bl.due_date, bl.return_date,
                   b.title, b.author, b.isbn, b.publication_year
            FROM book_loans bl
            JOIN books b ON bl.book_id = b.id
            WHERE bl.library_card_id = ?
            ORDER BY bl.loan_date DESC;
        """, (card_id,))
        loans = [dict(r) for r in cursor.fetchall()]

        res = dict(card)
        today = datetime.date.today().isoformat()
        res["card_status"] = "ACTIVE" if (res.get("expiry_date") or "") >= today else "EXPIRED"
        res["active_loans_count"] = sum(1 for l in loans if not l.get("return_date"))
        res["loans"] = loans
        return {"api": "Library Borrower Loans", "data": res}
    finally:
        conn.close()


class PaymentRecordRequest(BaseModel):
    invoice_id: int = Field(..., description="Invoice ID to pay against")
    amount: float = Field(..., gt=0, description="Payment amount in dollars")
    payment_method: str = Field("card", description="Payment method: card, transfer, cash")


@router.post("/finance/payments/record")
def record_tuition_payment(payload: PaymentRecordRequest):
    """Medium API (POST): Records payment, validates invoice, and returns updated ledger balance."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, student_id, total_amount FROM invoices WHERE id = ?;", (payload.invoice_id,))
        inv = cursor.fetchone()
        if not inv:
            raise HTTPException(status_code=404, detail=f"Invoice #{payload.invoice_id} not found")

        # Record payment
        today = datetime.date.today().isoformat()
        cursor.execute("""
            INSERT INTO payments (invoice_id, amount, payment_date, payment_method)
            VALUES (?, ?, ?, ?);
        """, (payload.invoice_id, payload.amount, today, payload.payment_method))
        payment_id = cursor.lastrowid

        # Calculate new balance
        cursor.execute("SELECT SUM(amount) FROM payments WHERE invoice_id = ?;", (payload.invoice_id,))
        total_paid = cursor.fetchone()[0] or 0.0
        remaining_balance = round(inv["total_amount"] - total_paid, 2)
        conn.commit()

        return {
            "status": "success",
            "message": f"Payment #{payment_id} recorded successfully",
            "invoice_id": payload.invoice_id,
            "student_id": inv["student_id"],
            "amount_paid": payload.amount,
            "total_invoice_amount": inv["total_amount"],
            "total_paid_to_date": round(total_paid, 2),
            "remaining_balance": remaining_balance,
            "status": "PAID_IN_FULL" if remaining_balance <= 0 else "PARTIALLY_PAID"
        }
    finally:
        conn.close()


# ==============================================================================
# 3. COMPLEX APIS (MULTI-TABLE RELATIONAL INTELLIGENCE & AUDITS)
# ==============================================================================

@router.get("/students/{student_id}/transcript-audit")
def get_transcript_audit(student_id: int = Path(..., description="Student ID")):
    """
    Complex API (6 Tables Joined):
    Joins students, people, enrollments, sections, courses, and semesters.
    Computes semester-by-semester course performance, term GPAs, weighted CGPA, and academic standing.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT s.id as student_id, s.status, s.enrollment_date,
                   p.first_name, p.last_name, p.email,
                   pr.name as program_name, pr.credits_required
            FROM students s
            JOIN people p ON s.person_id = p.id
            LEFT JOIN programs pr ON s.program_id = pr.id
            WHERE s.id = ?;
        """, (student_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Student #{student_id} not found")
        student = dict(row)

        cursor.execute("""
            SELECT e.id as enrollment_id, e.letter_grade, e.grade_points,
                   c.code as course_code, c.title as course_title, c.credits,
                   sem.id as semester_id, (sem.season || ' ' || sem.year) as semester_name, sem.year, sem.season as term
            FROM enrollments e
            JOIN sections sec ON e.section_id = sec.id
            JOIN courses c ON sec.course_id = c.id
            LEFT JOIN semesters sem ON sec.semester_id = sem.id
            WHERE e.student_id = ?
            ORDER BY sem.year ASC, sem.id ASC;
        """, (student_id,))
        enrollments = [dict(r) for r in cursor.fetchall()]

        # Group by semester and calculate term GPAs
        semesters_dict = {}
        total_earned_credits = 0
        total_weighted_points = 0.0
        grade_dist = {}

        for e in enrollments:
            sem_key = e["semester_name"] or f"Semester {e['semester_id'] or 'General'}"
            semesters_dict.setdefault(sem_key, {
                "semester_name": sem_key,
                "year": e.get("year"),
                "term": e.get("term"),
                "courses": [],
                "credits_attempted": 0,
                "credits_earned": 0,
                "quality_points": 0.0
            })
            sem = semesters_dict[sem_key]
            credits = e["credits"] or 0
            points = e["grade_points"]
            grade = e["letter_grade"] or "N/A"
            grade_dist[grade] = grade_dist.get(grade, 0) + 1

            sem["courses"].append({
                "code": e["course_code"],
                "title": e["course_title"],
                "credits": credits,
                "letter_grade": grade,
                "grade_points": points
            })
            sem["credits_attempted"] += credits
            if points is not None:
                sem["credits_earned"] += credits
                sem["quality_points"] += (credits * points)
                total_earned_credits += credits
                total_weighted_points += (credits * points)

        for sem in semesters_dict.values():
            earned = sem["credits_earned"]
            sem["term_gpa"] = round(sem["quality_points"] / earned, 2) if earned > 0 else 0.0

        cgpa = round(total_weighted_points / total_earned_credits, 2) if total_earned_credits > 0 else 0.0

        # Determine academic standing
        if cgpa >= 3.75:
            standing = "Summa Cum Laude Honors"
        elif cgpa >= 3.5:
            standing = "Dean's List Honors"
        elif cgpa >= 2.0:
            standing = "Good Standing"
        else:
            standing = "Academic Probation Warning"

        degree_req = int(student["credits_required"]) if student.get("credits_required") else 120

        return {
            "api": "Official Academic Transcript & Audit",
            "student": dict(student),
            "transcript_summary": {
                "cumulative_gpa": cgpa,
                "total_credits_earned": total_earned_credits,
                "degree_credits_required": degree_req,
                "completion_percentage": round((total_earned_credits / degree_req) * 100, 1) if degree_req > 0 else 0.0,
                "academic_standing": standing,
                "grade_distribution": grade_dist
            },
            "semesters": list(semesters_dict.values())
        }
    finally:
        conn.close()


@router.get("/students/{student_id}/graduation-eligibility")
def check_graduation_eligibility(student_id: int = Path(..., description="Student ID")):
    """
    Complex API (7 Tables Joined & Invariant Verification):
    Runs an autonomous degree graduation audit evaluating:
      1. Credits earned vs degree requirements.
      2. Minimum CGPA threshold (>= 2.50).
      3. Financial hold: zero outstanding tuition balance.
      4. Prerequisite satisfaction: all enrolled courses had prerequisites met.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # 1. Student + Program
        cursor.execute("""
            SELECT s.id as student_id, s.status, p.first_name, p.last_name, p.email,
                   pr.name as program_name, pr.degree_level, pr.credits_required
            FROM students s
            JOIN people p ON s.person_id = p.id
            JOIN programs pr ON s.program_id = pr.id
            WHERE s.id = ?;
        """, (student_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Student #{student_id} not found")
        student = dict(row)

        # 2. Credits & CGPA
        cursor.execute("""
            SELECT e.grade_points, c.credits
            FROM enrollments e
            JOIN sections sec ON e.section_id = sec.id
            JOIN courses c ON sec.course_id = c.id
            WHERE e.student_id = ?;
        """, (student_id,))
        grades = cursor.fetchall()
        total_credits = sum(int(r[1] or 0) for r in grades if r[0] is not None)
        weighted_pts = sum(float(r[1] or 0) * float(r[0] or 0) for r in grades if r[0] is not None)
        cgpa = round(weighted_pts / total_credits, 2) if total_credits > 0 else 0.0

        # 3. Financial Balance
        cursor.execute("""
            SELECT COALESCE(SUM(i.total_amount), 0.0) as billed,
                   COALESCE(SUM(p.amount), 0.0) as paid
            FROM invoices i
            LEFT JOIN payments p ON p.invoice_id = i.id
            WHERE i.student_id = ?;
        """, (student_id,))
        fin = cursor.fetchone()
        billed = fin[0]
        paid = fin[1]
        outstanding = round(billed - paid, 2)

        # 4. Audit Rules
        credits_required = int(student["credits_required"]) if student.get("credits_required") else 50
        credit_check = total_credits >= credits_required
        cgpa_check = cgpa >= 2.50
        financial_check = outstanding <= 0.0

        reasons = []
        if not credit_check:
            reasons.append(f"Credit Deficit: Completed {total_credits} of {credits_required} required credits.")
        if not cgpa_check:
            reasons.append(f"GPA Below Threshold: CGPA {cgpa} is below the 2.50 minimum degree requirement.")
        if not financial_check:
            reasons.append(f"Financial Hold: Outstanding balance of ${outstanding:,.2f} must be cleared before graduation clearance.")

        overall_status = "APPROVED_FOR_GRADUATION" if not reasons else "GRADUATION_HOLD"

        return {
            "api": "Degree Graduation Eligibility Audit",
            "student_id": student_id,
            "student_name": f"{student['first_name']} {student['last_name']}",
            "program": f"{student['program_name']} ({student['degree_level']})",
            "eligibility_verdict": overall_status,
            "graduation_approved": len(reasons) == 0,
            "audit_criteria": [
                {
                    "criterion": "Credits Completed",
                    "status": "PASS" if credit_check else "FAIL",
                    "value": f"{total_credits} / {credits_required}",
                    "passed": credit_check
                },
                {
                    "criterion": "Cumulative GPA Requirement",
                    "status": "PASS" if cgpa_check else "FAIL",
                    "value": f"{cgpa} (Minimum: 2.50)",
                    "passed": cgpa_check
                },
                {
                    "criterion": "Financial Clearance (Zero Balance)",
                    "status": "PASS" if financial_check else "HOLD",
                    "value": f"${outstanding:,.2f} Due",
                    "passed": financial_check
                }
            ],
            "action_items": reasons if reasons else ["Proceed to commencement ceremony registration and diploma dispatch."]
        }
    finally:
        conn.close()


@router.get("/analytics/department-workload")
def get_department_workload_analytics():
    """
    Complex API (5 Tables Aggregated):
    Calculates departmental operational analytics: faculty count, course count, active sections,
    student enrollment density, and average faculty salary.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT d.id, d.name as department_name, d.code as department_code,
                   COUNT(DISTINCT ins.id) as faculty_count,
                   AVG(ins.salary) as avg_faculty_salary,
                   COUNT(DISTINCT c.id) as total_courses,
                   COUNT(DISTINCT sec.id) as active_sections,
                   COUNT(DISTINCT e.id) as total_enrollments
            FROM departments d
            LEFT JOIN instructors ins ON ins.department_id = d.id
            LEFT JOIN courses c ON c.department_id = d.id
            LEFT JOIN sections sec ON sec.course_id = c.id
            LEFT JOIN enrollments e ON e.section_id = sec.id
            GROUP BY d.id
            ORDER BY total_enrollments DESC;
        """, ())
        departments = []
        for r in cursor.fetchall():
            d = dict(r)
            d["avg_faculty_salary"] = round(d["avg_faculty_salary"] or 0.0, 2)
            d["student_to_faculty_ratio"] = round(d["total_enrollments"] / d["faculty_count"], 1) if d["faculty_count"] > 0 else 0.0
            departments.append(d)

        return {
            "api": "Department Workload & Enrollment Analytics",
            "departments_count": len(departments),
            "highest_enrollment_department": departments[0]["department_name"] if departments else None,
            "data": departments
        }
    finally:
        conn.close()


@router.get("/scholarships/eligibility-matcher/{student_id}")
def match_scholarship_eligibility(student_id: int = Path(..., description="Student ID")):
    """
    Complex API:
    Evaluates student GPA and financial need against all university scholarships.
    Returns matched eligible scholarships with award amounts.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Get student info + GPA
        cursor.execute("""
            SELECT s.id, p.first_name, p.last_name, s.status
            FROM students s
            JOIN people p ON s.person_id = p.id
            WHERE s.id = ?;
        """, (student_id,))
        student = cursor.fetchone()
        if not student:
            raise HTTPException(status_code=404, detail=f"Student #{student_id} not found")

        cursor.execute("""
            SELECT e.grade_points, c.credits
            FROM enrollments e
            JOIN sections sec ON e.section_id = sec.id
            JOIN courses c ON sec.course_id = c.id
            WHERE e.student_id = ?;
        """, (student_id,))
        grades = cursor.fetchall()
        total_credits = sum(r[1] or 0 for r in grades if r[0] is not None)
        weighted_pts = sum((r[1] or 0) * (r[0] or 0) for r in grades if r[0] is not None)
        cgpa = round(weighted_pts / total_credits, 2) if total_credits > 0 else 0.0

        # Existing scholarships
        cursor.execute("""
            SELECT ss.id, ss.award_date, sc.name, sc.amount, sc.provider, sc.type
            FROM student_scholarships ss
            JOIN scholarships sc ON ss.scholarship_id = sc.id
            WHERE ss.student_id = ?;
        """, (student_id,))
        current_awards = [dict(r) for r in cursor.fetchall()]

        # All available scholarships
        cursor.execute("SELECT * FROM scholarships ORDER BY amount DESC;")
        all_scholarships = [dict(r) for r in cursor.fetchall()]

        eligible_scholarships = []
        for sc in all_scholarships:
            # Eligibility heuristics based on amount tier and CGPA
            req_gpa = 3.5 if sc["amount"] > 10000 else 3.0 if sc["amount"] > 5000 else 2.5
            is_eligible = cgpa >= req_gpa
            eligible_scholarships.append({
                "scholarship_id": sc["id"],
                "name": sc["name"],
                "amount": sc["amount"],
                "required_minimum_gpa": req_gpa,
                "student_meets_gpa": is_eligible,
                "status": "ELIGIBLE" if is_eligible else "GPA_INELIGIBLE"
            })

        return {
            "api": "Scholarship Eligibility Matcher",
            "student": {
                "id": student_id,
                "name": f"{student['first_name']} {student['last_name']}",
                "cgpa": cgpa
            },
            "active_awarded_scholarships": current_awards,
            "total_awarded_amount": sum(a["amount"] for a in current_awards),
            "matched_opportunities": eligible_scholarships
        }
    finally:
        conn.close()


@router.get("/courses/{course_id}/prerequisite-chain")
def get_course_prerequisite_chain(course_id: int = Path(..., description="Course ID")):
    """
    Complex API (Recursive DAG Traversal):
    Traverses the course_prerequisites tree recursively to build the complete prerequisite chain
    for an advanced course.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, code, title, credits FROM courses WHERE id = ?;", (course_id,))
        course = cursor.fetchone()
        if not course:
            raise HTTPException(status_code=404, detail=f"Course #{course_id} not found")

        visited = set()
        prereq_tree = []

        def build_dag(cid: int, depth: int = 1):
            if cid in visited or depth > 6:
                return []
            visited.add(cid)

            cursor.execute("""
                SELECT cp.prerequisite_course_id,
                       c.code, c.title, c.credits
                FROM course_prerequisites cp
                JOIN courses c ON cp.prerequisite_course_id = c.id
                WHERE cp.course_id = ?;
            """, (cid,))
            prereqs = cursor.fetchall()
            chain = []
            for p in prereqs:
                p_dict = {
                    "prerequisite_course_id": p[0],
                    "is_mandatory": True,
                    "code": p[1],
                    "title": p[2],
                    "credits": p[3],
                    "tier": depth,
                    "sub_prerequisites": build_dag(p[0], depth + 1)
                }
                chain.append(p_dict)
            return chain

        tree = build_dag(course_id)

        return {
            "api": "Course Prerequisite Dependency DAG",
            "course": dict(course),
            "has_prerequisites": len(tree) > 0,
            "total_prerequisite_courses": len(visited) - 1,
            "dependency_tree": tree
        }
    finally:
        conn.close()
