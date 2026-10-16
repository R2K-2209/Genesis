"""
AegisRegistry Persistence & Data Healing Layer (Layer 8)
Request Ledger:
Maintains an immutable audit trail of all runtime self-healed API transactions,
schema diffs, provenance verifications, and execution timings.
"""

import os
import json
import sqlite3
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from backend.database import DB_PATH


class AegisRequestLedger:
    """
    Persists self-healing audit logs to SQLite for enterprise governance,
    telemetry visualization, and compliance auditing.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._ensure_table_exists()

    def _ensure_table_exists(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS aegis_request_ledger (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    drift_type TEXT NOT NULL,
                    original_payload TEXT NOT NULL,
                    healed_payload TEXT NOT NULL,
                    status_code_before INTEGER NOT NULL,
                    status_code_after INTEGER NOT NULL,
                    diagnosis_latency_ms REAL NOT NULL,
                    total_latency_ms REAL NOT NULL,
                    provenance_verified INTEGER NOT NULL,
                    explanation TEXT,
                    compensating_sql TEXT
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[AegisLedger] Warning during table init: {e}")

    def record_healing(
        self,
        endpoint: str,
        drift_type: str,
        original_payload: Dict[str, Any],
        healed_payload: Dict[str, Any],
        status_code_before: int,
        status_code_after: int,
        diagnosis_latency_ms: float,
        total_latency_ms: float,
        provenance_verified: bool,
        explanation: str = "",
        compensating_sql: Optional[str] = None
    ) -> str:
        record_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO aegis_request_ledger (
                    id, timestamp, endpoint, drift_type, original_payload,
                    healed_payload, status_code_before, status_code_after,
                    diagnosis_latency_ms, total_latency_ms, provenance_verified,
                    explanation, compensating_sql
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record_id,
                timestamp,
                endpoint,
                drift_type,
                json.dumps(original_payload),
                json.dumps(healed_payload),
                status_code_before,
                status_code_after,
                diagnosis_latency_ms,
                total_latency_ms,
                1 if provenance_verified else 0,
                explanation,
                compensating_sql
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[AegisLedger] Error saving ledger record: {e}")

        return record_id

    def get_recent_records(self, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM aegis_request_ledger
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            conn.close()

            results = []
            for r in rows:
                item = dict(r)
                try:
                    item["original_payload"] = json.loads(item["original_payload"])
                except Exception:
                    pass
                try:
                    item["healed_payload"] = json.loads(item["healed_payload"])
                except Exception:
                    pass
                results.append(item)
            return results
        except Exception as e:
            print(f"[AegisLedger] Error fetching ledger: {e}")
            return []

    def clear_ledger(self) -> None:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM aegis_request_ledger")
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[AegisLedger] Error clearing ledger: {e}")


# Global singleton instance
aegis_request_ledger = AegisRequestLedger()
