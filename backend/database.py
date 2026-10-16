"""
Database Management Module for University Sample Database.
Loads and initializes SQLite 3 from university-sample-database-v1-university-sample-database.json.
Provides full CRUD capabilities (read, write, delete, edit) for any table.
"""

import os
import json
import sqlite3
from typing import Dict, Any, List, Optional, Tuple

DB_PATH = os.path.join(os.path.dirname(__file__), "university.db")
DEFAULT_JSON_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "university-sample-database-v1-university-sample-database.json")
)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def infer_sqlite_type(value: Any) -> str:
    if value is None:
        return "TEXT"
    if isinstance(value, bool):
        return "INTEGER"
    if isinstance(value, int):
        return "INTEGER"
    if isinstance(value, float):
        return "REAL"
    return "TEXT"


def init_database_from_json(json_path: str = DEFAULT_JSON_PATH, force: bool = False) -> Dict[str, int]:
    """
    Parses the JSON file and initializes the SQLite database with all tables and rows.
    Returns a dictionary of {table_name: row_count}.
    """
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"JSON database file not found at: {json_path}")

    # If DB already exists and force is False, just return current stats
    if os.path.exists(DB_PATH) and not force:
        counts = get_table_counts()
        if counts and sum(counts.values()) > 0:
            return counts

    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except Exception:
            pass

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    conn = get_connection()
    cursor = conn.cursor()
    table_counts = {}

    try:
        cursor.execute("PRAGMA foreign_keys = OFF;")

        for table_name, rows in data.items():
            if not isinstance(rows, list):
                continue

            if not rows:
                cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY);")
                table_counts[table_name] = 0
                continue

            # Analyze schema from all rows to find all distinct column keys and best type
            column_types: Dict[str, str] = {}
            for row in rows:
                if isinstance(row, dict):
                    for k, v in row.items():
                        if k not in column_types:
                            column_types[k] = infer_sqlite_type(v)
                        elif column_types[k] == "TEXT":
                            pass
                        elif v is not None:
                            curr_type = infer_sqlite_type(v)
                            if curr_type == "TEXT":
                                column_types[k] = "TEXT"
                            elif curr_type == "REAL" and column_types[k] == "INTEGER":
                                column_types[k] = "REAL"

            # Create Table statement
            col_defs = []
            has_id = "id" in column_types
            for col, col_type in column_types.items():
                if col == "id":
                    col_defs.append("id INTEGER PRIMARY KEY")
                else:
                    col_defs.append(f'"{col}" {col_type}')

            create_sql = f'CREATE TABLE "{table_name}" ({", ".join(col_defs)});'
            cursor.execute(create_sql)

            # Insert all rows
            cols = list(column_types.keys())
            placeholders = ", ".join(["?"] * len(cols))
            col_names_sql = ", ".join([f'"{c}"' for c in cols])
            insert_sql = f'INSERT INTO "{table_name}" ({col_names_sql}) VALUES ({placeholders})'

            values_to_insert = []
            for row in rows:
                row_vals = []
                for c in cols:
                    val = row.get(c)
                    if isinstance(val, (dict, list)):
                        val = json.dumps(val)
                    elif isinstance(val, bool):
                        val = 1 if val else 0
                    row_vals.append(val)
                values_to_insert.append(row_vals)

            cursor.executemany(insert_sql, values_to_insert)
            table_counts[table_name] = len(values_to_insert)

            # Create index on foreign key columns like student_id, person_id, course_id, etc.
            for col in cols:
                if col.endswith("_id") and col != "id":
                    idx_name = f"idx_{table_name}_{col}"
                    try:
                        cursor.execute(f'CREATE INDEX IF NOT EXISTS "{idx_name}" ON "{table_name}" ("{col}");')
                    except Exception:
                        pass

        cursor.execute("PRAGMA foreign_keys = ON;")
        conn.commit()
    finally:
        conn.close()

    return table_counts


def get_table_counts() -> Dict[str, int]:
    """Returns row counts for all tables."""
    if not os.path.exists(DB_PATH):
        return {}
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
        tables = [row[0] for row in cursor.fetchall()]
        counts = {}
        for t in tables:
            cursor.execute(f'SELECT COUNT(*) FROM "{t}";')
            counts[t] = cursor.fetchone()[0]
        return counts
    finally:
        conn.close()


def get_tables_metadata() -> List[Dict[str, Any]]:
    """Returns full metadata for all tables including columns and row count."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
        tables = [row[0] for row in cursor.fetchall()]
        result = []
        for t in tables:
            cursor.execute(f'SELECT COUNT(*) FROM "{t}";')
            count = cursor.fetchone()[0]

            cursor.execute(f'PRAGMA table_info("{t}");')
            cols = []
            for col in cursor.fetchall():
                cols.append({
                    "cid": col[0],
                    "name": col[1],
                    "type": col[2],
                    "notnull": bool(col[3]),
                    "default_value": col[4],
                    "pk": bool(col[5])
                })
            result.append({
                "table_name": t,
                "row_count": count,
                "columns": cols
            })
        return result
    finally:
        conn.close()


def get_table_rows(
    table_name: str,
    page: int = 1,
    limit: int = 25,
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "ASC"
) -> Dict[str, Any]:
    """Paginated retrieval of rows from any table with optional search."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
        if not cursor.fetchone():
            raise ValueError(f"Table '{table_name}' does not exist.")

        cursor.execute(f'PRAGMA table_info("{table_name}");')
        columns = [col[1] for col in cursor.fetchall()]

        where_clause = ""
        params: List[Any] = []
        if search and search.strip():
            terms = [f'CAST("{c}" AS TEXT) LIKE ?' for c in columns]
            where_clause = f" WHERE ({' OR '.join(terms)})"
            params = [f"%{search.strip()}%"] * len(columns)

        # Count total
        count_sql = f'SELECT COUNT(*) FROM "{table_name}"{where_clause}'
        cursor.execute(count_sql, params)
        total_rows = cursor.fetchone()[0]

        # Sorting
        order_clause = ""
        if sort_by and sort_by in columns:
            direction = "DESC" if sort_order.upper() == "DESC" else "ASC"
            order_clause = f' ORDER BY "{sort_by}" {direction}'
        elif "id" in columns:
            order_clause = ' ORDER BY "id" ASC'

        # Pagination
        offset = max(0, (page - 1) * limit)
        data_sql = f'SELECT * FROM "{table_name}"{where_clause}{order_clause} LIMIT ? OFFSET ?'
        cursor.execute(data_sql, params + [limit, offset])

        rows = [dict(row) for row in cursor.fetchall()]

        return {
            "table_name": table_name,
            "columns": columns,
            "rows": rows,
            "total_rows": total_rows,
            "page": page,
            "limit": limit,
            "total_pages": (total_rows + limit - 1) // limit if limit > 0 else 1
        }
    finally:
        conn.close()


def get_record(table_name: str, record_id: int) -> Optional[Dict[str, Any]]:
    """Get single record by primary key id."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f'SELECT * FROM "{table_name}" WHERE id = ?;', (record_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def insert_record(table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Insert a new record into table."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cols = list(data.keys())
        placeholders = ", ".join(["?"] * len(cols))
        col_names = ", ".join([f'"{c}"' for c in cols])
        vals = [data[c] for c in cols]

        sql = f'INSERT INTO "{table_name}" ({col_names}) VALUES ({placeholders})'
        cursor.execute(sql, vals)
        new_id = cursor.lastrowid
        conn.commit()

        # Fetch and return inserted record
        if "id" in data:
            return get_record(table_name, data["id"]) or data
        return get_record(table_name, new_id) or data
    finally:
        conn.close()


def update_record(table_name: str, record_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update an existing record by id."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        set_parts = []
        vals = []
        for k, v in data.items():
            if k == "id":
                continue
            set_parts.append(f'"{k}" = ?')
            vals.append(v)

        if not set_parts:
            return get_record(table_name, record_id)

        vals.append(record_id)
        sql = f'UPDATE "{table_name}" SET {", ".join(set_parts)} WHERE id = ?'
        cursor.execute(sql, vals)
        conn.commit()

        return get_record(table_name, record_id)
    finally:
        conn.close()


def delete_record(table_name: str, record_id: int) -> bool:
    """Delete a record by id."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f'DELETE FROM "{table_name}" WHERE id = ?;', (record_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        return deleted
    finally:
        conn.close()


def get_student_full_profile(student_id: int) -> Optional[Dict[str, Any]]:
    """
    Rich domain query: fetches student details, personal info,
    enrollments with courses, calculated GPA, invoices, and payments.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT s.id as student_id, s.status, s.enrollment_date,
                   p.first_name, p.last_name, p.email, p.phone, p.gender, p.date_of_birth,
                   pr.name as program_name, pr.degree_level as degree_type,
                   d.name as department_name
            FROM students s
            LEFT JOIN people p ON s.person_id = p.id
            LEFT JOIN programs pr ON s.program_id = pr.id
            LEFT JOIN departments d ON pr.department_id = d.id
            WHERE s.id = ?;
        """, (student_id,))
        base = cursor.fetchone()
        if not base:
            return None

        result = dict(base)

        # Enrollments & Grades
        cursor.execute("""
            SELECT e.id as enrollment_id, e.letter_grade, e.grade_points,
                   c.code as course_code, c.title as course_title, c.credits
            FROM enrollments e
            LEFT JOIN sections sec ON e.section_id = sec.id
            LEFT JOIN courses c ON sec.course_id = c.id
            WHERE e.student_id = ?;
        """, (student_id,))
        enrollments = [dict(r) for r in cursor.fetchall()]
        result["enrollments"] = enrollments

        # Calculate live CGPA
        total_credits = sum(e["credits"] or 0 for e in enrollments if e.get("grade_points") is not None)
        weighted_points = sum((e["credits"] or 0) * (e["grade_points"] or 0) for e in enrollments if e.get("grade_points") is not None)
        result["cgpa"] = round(weighted_points / total_credits, 2) if total_credits > 0 else 0.0
        result["total_credits_earned"] = total_credits

        # Invoices and Payments
        cursor.execute("""
            SELECT i.id as invoice_id, i.total_amount, i.issue_date, i.due_date,
                   COALESCE(SUM(p.amount), 0.0) as total_paid
            FROM invoices i
            LEFT JOIN payments p ON p.invoice_id = i.id
            WHERE i.student_id = ?
            GROUP BY i.id;
        """, (student_id,))
        invoices = []
        total_tuition = 0.0
        total_paid = 0.0
        for inv in cursor.fetchall():
            inv_dict = dict(inv)
            inv_dict["balance_due"] = round(inv_dict["total_amount"] - inv_dict["total_paid"], 2)
            total_tuition += inv_dict["total_amount"]
            total_paid += inv_dict["total_paid"]
            invoices.append(inv_dict)

        result["invoices"] = invoices
        result["total_tuition_billed"] = round(total_tuition, 2)
        result["total_tuition_paid"] = round(total_paid, 2)
        result["outstanding_balance"] = round(total_tuition - total_paid, 2)

        return result
    finally:
        conn.close()


if __name__ == "__main__":
    print(f"Initializing SQLite database at: {DB_PATH}")
    stats = init_database_from_json(force=True)
    print(f"Successfully initialized {len(stats)} tables!")
    for tbl, count in sorted(stats.items()):
        print(f"  • {tbl}: {count} records")
