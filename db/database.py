"""
Real Relational SQLite Database for Genesis Enterprise
Handles real data persistence, real queries, dynamic CGPA weighted calculations,
tuition payment arithmetic, transactions, and dynamic API definitions.
"""

import sqlite3
import json
import time
from typing import Any, Dict, List, Optional, Tuple

DB_PATH = "genesis_real.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Initializes SQLite tables and seeds realistic enterprise academic records.
    """
    conn = get_connection()
    cur = conn.cursor()

    # 1. Students Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        department TEXT NOT NULL,
        semester INTEGER NOT NULL,
        tuition_balance REAL NOT NULL,
        status TEXT NOT NULL
    );
    """)

    # 2. Courses Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY,
        code TEXT NOT NULL,
        title TEXT NOT NULL,
        credits INTEGER NOT NULL,
        department TEXT NOT NULL
    );
    """)

    # 3. Enrollments Table (with real letter grades and numerical grade points)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS enrollments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        course_id INTEGER NOT NULL,
        grade_points REAL NOT NULL,
        term TEXT NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students(id),
        FOREIGN KEY (course_id) REFERENCES courses(id)
    );
    """)

    # 4. Financial Transactions Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        type TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        trace_id TEXT NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students(id)
    );
    """)

    # 5. Dynamic API Definitions Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS dynamic_apis (
        endpoint TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        method TEXT NOT NULL,
        description TEXT NOT NULL,
        active_schema TEXT NOT NULL,
        mutation_state TEXT NOT NULL
    );
    """)

    # 6. Audit & Rollback Ledger
    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit_ledger (
        trace_id TEXT PRIMARY KEY,
        timestamp TEXT NOT NULL,
        patch_id TEXT NOT NULL,
        tool_name TEXT NOT NULL,
        original_payload TEXT NOT NULL,
        transformed_payload TEXT NOT NULL,
        reverted INTEGER DEFAULT 0
    );
    """)

    # Seed initial students if empty
    cur.execute("SELECT COUNT(*) FROM students;")
    if cur.fetchone()[0] == 0:
        students_seed = [
            (123, "Ranjit Kadam", "ranjit.kadam@vesit.edu", "Computer Science", 6, 45000.0, "Enrolled"),
            (456, "Arya Bagul", "arya.bagul@vesit.edu", "Artificial Intelligence", 6, 28000.0, "Enrolled"),
            (789, "Saumya Bhide", "saumya.bhide@vesit.edu", "Information Technology", 6, 12000.0, "Enrolled"),
            (101, "Shreeya Mandavkar", "shreeya.m@vesit.edu", "Computer Science", 6, 0.0, "Enrolled")
        ]
        cur.executemany("INSERT INTO students VALUES (?, ?, ?, ?, ?, ?, ?)", students_seed)

        courses_seed = [
            (1, "CS601", "Distributed Systems & Cloud Computing", 4, "Computer Science"),
            (2, "CS602", "Neural Networks & Deep Learning", 4, "Computer Science"),
            (3, "CS603", "Advanced Database Management", 3, "Computer Science"),
            (4, "CS604", "Software Engineering & DevOps", 3, "Computer Science"),
            (5, "CS605", "Cybersecurity & Cryptography", 3, "Computer Science")
        ]
        cur.executemany("INSERT INTO courses VALUES (?, ?, ?, ?, ?)", courses_seed)

        # Seed enrollments for student 123
        enrollments_seed = [
            (123, 1, 9.5, "Spring 2026"),
            (123, 2, 9.8, "Spring 2026"),
            (123, 3, 9.0, "Spring 2026"),
            (123, 4, 9.2, "Spring 2026"),
            (123, 5, 9.6, "Spring 2026"),
            # Seed enrollments for student 456
            (456, 1, 9.2, "Spring 2026"),
            (456, 2, 9.4, "Spring 2026"),
            (456, 3, 9.1, "Spring 2026")
        ]
        cur.executemany("INSERT INTO enrollments (student_id, course_id, grade_points, term) VALUES (?, ?, ?, ?)", enrollments_seed)

    conn.commit()
    conn.close()


def calculate_student_cgpa(student_id: int) -> Optional[Dict[str, Any]]:
    """
    Real Database Calculation:
    Queries live course credits and grade points from SQLite, computes weighted CGPA.
    Formula: CGPA = Sum(credits * grade_points) / Sum(credits)
    """
    conn = get_connection()
    cur = conn.cursor()

    # Fetch student metadata
    cur.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    student = cur.fetchone()
    if not student:
        conn.close()
        return None

    # Fetch courses and grades
    query = """
    SELECT c.code, c.title, c.credits, e.grade_points, e.term
    FROM enrollments e
    JOIN courses c ON e.course_id = c.id
    WHERE e.student_id = ?
    """
    cur.execute(query, (student_id,))
    rows = cur.fetchall()
    conn.close()

    total_credits = 0
    weighted_points = 0.0
    course_breakdown = []

    for r in rows:
        cr = r["credits"]
        gp = r["grade_points"]
        total_credits += cr
        weighted_points += (cr * gp)
        course_breakdown.append({
            "course_code": r["code"],
            "title": r["title"],
            "credits": cr,
            "grade_points": gp,
            "effective_score": round(cr * gp, 2)
        })

    computed_cgpa = round(weighted_points / total_credits, 2) if total_credits > 0 else 0.0

    # Real business logic rules
    standing = "Dean's High Honors" if computed_cgpa >= 9.5 else ("Honors" if computed_cgpa >= 9.0 else "Good Standing")

    return {
        "id": student["id"],
        "student_id": student["id"],
        "name": student["name"],
        "department": student["department"],
        "semester": student["semester"],
        "status": student["status"],
        "tuition_balance": student["tuition_balance"],
        "calculated_cgpa": computed_cgpa,
        "academic_standing": standing,
        "total_credits_earned": total_credits,
        "courses_evaluated_count": len(course_breakdown),
        "course_breakdown": course_breakdown,
        "calculation_source": "Live SQLite Weighted Aggregation Engine"
    }


def execute_tuition_payment(student_id: int, payment_amount: float, trace_id: str) -> Dict[str, Any]:
    """
    Real Database Write Operation:
    Deducts payment from balance, records transaction ledger in SQLite with atomic commit.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT tuition_balance, name FROM students WHERE id = ?", (student_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Student ID {student_id} not found.")

    current_balance = row["tuition_balance"]
    student_name = row["name"]
    new_balance = max(0.0, current_balance - payment_amount)

    # 1. Update Student Balance
    cur.execute("UPDATE students SET tuition_balance = ? WHERE id = ?", (new_balance, student_id))

    # 2. Insert Transaction Record
    cur.execute(
        "INSERT INTO transactions (student_id, amount, type, timestamp, trace_id) VALUES (?, ?, ?, ?, ?)",
        (student_id, payment_amount, "Tuition Payment", time.strftime("%Y-%m-%d %H:%M:%S"), trace_id)
    )

    conn.commit()
    conn.close()

    return {
        "student_id": student_id,
        "student_name": student_name,
        "previous_balance": current_balance,
        "amount_paid": payment_amount,
        "new_balance": new_balance,
        "trace_id": trace_id,
        "status": "SETTLED"
    }


def rollback_payment_by_trace(trace_id: str) -> bool:
    """
    1-Click Real Database Reversal:
    Finds transaction by trace_id and reverts the student balance.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT student_id, amount FROM transactions WHERE trace_id = ?", (trace_id,))
    tx = cur.fetchone()
    if not tx:
        conn.close()
        return False

    student_id = tx["student_id"]
    amount = tx["amount"]

    # Revert balance
    cur.execute("UPDATE students SET tuition_balance = tuition_balance + ? WHERE id = ?", (amount, student_id))
    cur.execute("DELETE FROM transactions WHERE trace_id = ?", (trace_id,))

    conn.commit()
    conn.close()
    return True


def get_table_records(table_name: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table_name}")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# Initialize on module import
init_db()
