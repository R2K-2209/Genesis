"""
AegisRegistry Policy Governor Layer (Layer 2 — USP 2)
Blast-Radius & Policy Governance Scoring Engine.

Implements the Policy Governor which assigns a Blast-Radius Risk Score (R)
to every candidate schema patch BEFORE allowing autonomous healing.

    R = Σ(w_i * S_i) = w1*S_struct + w2*S_sens + w3*S_fin + w4*S_type

Decision Boundary:
    R < 35        → AUTO_HEAL_PROCEED       (Green)
    35 ≤ R < 70   → AUTO_HEAL_AUDIT_LOG     (Amber)
    R ≥ 70        → TRIP_CIRCUIT_BREAKER_HITL (Red — Human-in-the-Loop)

All scoring dimensions S_i ∈ [0, 100].
"""

import time
import re
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple


# ─────────────────────────────────────────────────────
# Sensitive key dictionaries for S_sens scoring
# ─────────────────────────────────────────────────────
CRITICAL_KEYS = {
    "password", "passwd", "secret", "ssn", "social_security",
    "auth_token", "access_token", "refresh_token", "api_key",
    "private_key", "credit_card", "card_number", "cvv", "pin"
}
HIGH_SENSITIVITY_KEYS = {
    "email", "phone", "phone_number", "address", "date_of_birth",
    "dob", "national_id", "passport", "driver_license", "ip_address",
    "bank_account", "routing_number", "iban", "swift"
}
MODERATE_SENSITIVITY_KEYS = {
    "name", "first_name", "last_name", "full_name", "username",
    "user_id", "account_id", "employee_id"
}
# Neutral keys score 0 — anything not in the above sets

# ─────────────────────────────────────────────────────
# Financial / mutating HTTP method patterns for S_fin
# ─────────────────────────────────────────────────────
FINANCIAL_KEYWORDS = {
    "payment", "transfer", "ledger", "invoice", "balance",
    "charge", "refund", "withdraw", "deposit", "transaction",
    "billing", "subscription", "fee", "tuition"
}
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# ─────────────────────────────────────────────────────
# Type coercion risk lookup for S_type
# ─────────────────────────────────────────────────────
TYPE_COERCION_RISKS = {
    ("str", "int"):   10,   # Safe parse: "123" → 123
    ("str", "float"): 15,   # Safe parse: "12.5" → 12.5
    ("int", "str"):   5,    # Lossless: 123 → "123"
    ("float", "int"): 80,   # LOSSY truncation: 12.99 → 12
    ("int", "float"): 5,    # Lossless: 12 → 12.0
    ("str", "bool"):  40,   # Ambiguous: "true", "1", "yes"
    ("bool", "int"):  20,   # Narrow: True → 1
    ("int", "bool"):  35,   # Lossy: 42 → True?
    ("list", "str"):  60,   # Structural loss
    ("dict", "str"):  70,   # Structural loss
    ("str", "list"):  50,   # Structural expand
    ("str", "dict"):  55,   # Structural expand
}


@dataclass
class BlastRadiusScore:
    """Complete Policy Governor scoring result."""
    # Weights
    w1: float = 0.15   # Structural Complexity Weight
    w2: float = 0.30   # Data Sensitivity Weight
    w3: float = 0.40   # Financial & Transaction Impact Weight
    w4: float = 0.15   # Type Coercion Risk Weight

    # Raw dimension scores
    s_struct: float = 0.0
    s_sens: float = 0.0
    s_fin: float = 0.0
    s_type: float = 0.0

    # Dimension computation details
    struct_breakdown: Dict[str, Any] = field(default_factory=dict)
    sens_breakdown: Dict[str, Any] = field(default_factory=dict)
    fin_breakdown: Dict[str, Any] = field(default_factory=dict)
    type_breakdown: Dict[str, Any] = field(default_factory=dict)

    # Weighted contributions
    weighted_struct: float = 0.0
    weighted_sens: float = 0.0
    weighted_fin: float = 0.0
    weighted_type: float = 0.0

    # Final composite score
    risk_score: float = 0.0

    # Decision
    action: str = "AUTO_HEAL_PROCEED"
    action_label: str = "Auto-Heal Proceed"
    action_color: str = "green"

    # Computation latency
    computation_time_ms: float = 0.0

    # Real database table context
    target_table: Optional[str] = None
    real_table_verified: bool = False
    table_columns: List[Dict[str, str]] = field(default_factory=list)
    total_records: int = 0
    sample_record: Optional[Dict[str, Any]] = None



class AegisPolicyGovernor:
    """
    Evaluates every candidate schema patch against a multi-dimensional risk model
    before allowing autonomous self-healing.

    The Policy Governor MUST run BEFORE the MVCC pointer swap (Layer 6),
    acting as a pre-commit gate between Diagnosis (Layer 4) and Commit.
    """

    def __init__(self):
        self.evaluation_count = 0
        self.auto_healed_count = 0
        self.audit_logged_count = 0
        self.circuit_tripped_count = 0

    def evaluate(
        self,
        endpoint: str,
        http_method: str = "GET",
        target_table: Optional[str] = None,
        field_renames: Optional[Dict[str, str]] = None,
        type_casts: Optional[Dict[str, str]] = None,
        nested_wraps: Optional[Dict[str, Any]] = None,
        injected_headers: Optional[Dict[str, str]] = None,
        modified_keys: Optional[List[str]] = None,
    ) -> BlastRadiusScore:
        """
        Compute the Blast-Radius Risk Score R for a candidate schema patch.

        R = w1*S_struct + w2*S_sens + w3*S_fin + w4*S_type
        """
        start = time.perf_counter()

        field_renames = field_renames or {}
        type_casts = type_casts or {}
        nested_wraps = nested_wraps or {}
        injected_headers = injected_headers or {}

        # Collect all modified keys from all sources
        all_keys = set()
        all_keys.update(field_renames.keys())
        all_keys.update(field_renames.values())
        all_keys.update(type_casts.keys())
        all_keys.update(nested_wraps.keys())
        if modified_keys:
            all_keys.update(modified_keys)

        score = BlastRadiusScore()

        # Query live database table schema if target_table is specified
        db_cols = {}
        if target_table:
            score.target_table = target_table
            try:
                from backend.database import get_connection
                conn = get_connection()
                cur = conn.cursor()
                cur.execute(f'PRAGMA table_info("{target_table}");')
                cols_info = cur.fetchall()
                if cols_info:
                    score.real_table_verified = True
                    for col in cols_info:
                        c_name = col[1]
                        c_type = col[2].upper()
                        db_cols[c_name] = c_type
                        score.table_columns.append({"name": c_name, "type": c_type})

                    cur.execute(f'SELECT COUNT(*) FROM "{target_table}";')
                    score.total_records = cur.fetchone()[0]

                    cur.execute(f'SELECT * FROM "{target_table}" LIMIT 1;')
                    sample = cur.fetchone()
                    if sample:
                        score.sample_record = dict(sample)
                conn.close()
            except Exception as e:
                pass

        # ───── Dimension 1: Structural Complexity (S_struct) ─────
        n_renames = len(field_renames)
        n_nesting = len(nested_wraps)
        # Count nesting depth if nested wraps have dict values
        max_nesting_depth = 0
        for v in nested_wraps.values():
            if isinstance(v, dict):
                max_nesting_depth = max(max_nesting_depth, self._dict_depth(v))
            else:
                max_nesting_depth = max(max_nesting_depth, 1)
        n_nesting_levels = max(n_nesting, max_nesting_depth)
        n_headers = len(injected_headers)

        raw_struct = 20 * n_renames + 40 * n_nesting_levels + 15 * n_headers
        score.s_struct = min(100.0, raw_struct)
        score.struct_breakdown = {
            "n_renames": n_renames,
            "n_nesting_levels": n_nesting_levels,
            "n_headers": n_headers,
            "formula": f"min(100, 20×{n_renames} + 40×{n_nesting_levels} + 15×{n_headers})",
            "raw_value": raw_struct,
            "capped_value": score.s_struct
        }

        # ───── Dimension 2: Data Sensitivity (S_sens) ─────
        max_sensitivity = 0
        sensitive_hits = []
        for key in all_keys:
            key_lower = key.lower().strip()
            if key_lower in CRITICAL_KEYS:
                max_sensitivity = max(max_sensitivity, 100)
                sensitive_hits.append({"key": key, "level": "CRITICAL", "score": 100})
            elif key_lower in HIGH_SENSITIVITY_KEYS:
                max_sensitivity = max(max_sensitivity, 85)
                sensitive_hits.append({"key": key, "level": "HIGH", "score": 85})
            elif key_lower in MODERATE_SENSITIVITY_KEYS:
                max_sensitivity = max(max_sensitivity, 40)
                sensitive_hits.append({"key": key, "level": "MODERATE", "score": 40})
            else:
                sensitive_hits.append({"key": key, "level": "NEUTRAL", "score": 0})

        score.s_sens = float(max_sensitivity)
        score.sens_breakdown = {
            "scanned_keys": list(all_keys),
            "sensitive_hits": sensitive_hits,
            "max_sensitivity": max_sensitivity,
            "dictionaries_checked": ["CRITICAL (SSN, Passwords, Tokens)",
                                      "HIGH (Email, Phone, Address)",
                                      "MODERATE (Name, UserID)",
                                      "NEUTRAL (page_number, limit)"]
        }

        # ───── Dimension 3: Financial Impact (S_fin) ─────
        is_write = http_method.upper() in WRITE_METHODS
        endpoint_lower = endpoint.lower()
        table_lower = (target_table or "").lower()
        has_financial_keyword = any(kw in endpoint_lower or kw in table_lower for kw in FINANCIAL_KEYWORDS)

        if is_write and has_financial_keyword:
            score.s_fin = 100.0
            fin_reason = f"Write method ({http_method}) on financial endpoint ({endpoint})"
        elif is_write:
            score.s_fin = 50.0
            fin_reason = f"Write method ({http_method}) on non-financial endpoint"
        elif has_financial_keyword:
            score.s_fin = 25.0
            fin_reason = f"Read method on financial endpoint ({endpoint})"
        else:
            score.s_fin = 0.0
            fin_reason = f"Read-only query on non-financial endpoint ({endpoint})"

        score.fin_breakdown = {
            "http_method": http_method.upper(),
            "endpoint": endpoint,
            "is_write_operation": is_write,
            "has_financial_keyword": has_financial_keyword,
            "financial_keywords_matched": [kw for kw in FINANCIAL_KEYWORDS if kw in endpoint_lower],
            "reason": fin_reason,
            "score": score.s_fin
        }

        # ───── Dimension 4: Type Coercion Risk (S_type) ─────
        max_type_risk = 0
        type_details = []
        for field_name, target_type in type_casts.items():
            # Infer source type directly from live database table schema if present
            source_type = "str"  # default assumption
            db_type_match = None
            if field_name in db_cols:
                db_t = db_cols[field_name].upper()
                db_type_match = db_t
                if "REAL" in db_t or "FLOAT" in db_t or "DOUBLE" in db_t or "NUMERIC" in db_t:
                    source_type = "float"
                elif "INT" in db_t:
                    source_type = "int"
                elif "BOOL" in db_t:
                    source_type = "bool"
                else:
                    source_type = "str"
            elif field_name.endswith("_id") or field_name == "id":
                source_type = "str"  # agent sends strings, server wants int
            elif field_name in ("amount", "balance", "gpa", "price"):
                source_type = "float"
            elif field_name in ("active", "verified", "is_enrolled"):
                source_type = "bool"

            risk = TYPE_COERCION_RISKS.get((source_type, target_type), 15)
            max_type_risk = max(max_type_risk, risk)
            type_details.append({
                "field": field_name,
                "source_type": source_type,
                "target_type": target_type,
                "coercion": f"{source_type} → {target_type}",
                "risk_score": risk,
                "risk_level": "HIGH" if risk >= 60 else "MEDIUM" if risk >= 30 else "LOW",
                "real_db_column": field_name in db_cols,
                "sqlite_column_type": db_type_match
            })

        if not type_casts:
            type_details.append({
                "field": "—",
                "coercion": "No type casts in patch",
                "risk_score": 0,
                "risk_level": "NONE"
            })

        score.s_type = float(max_type_risk)
        score.type_breakdown = {
            "type_casts_evaluated": len(type_casts),
            "details": type_details,
            "max_risk": max_type_risk
        }

        # ───── Weighted Composite Score ─────
        score.weighted_struct = round(score.w1 * score.s_struct, 2)
        score.weighted_sens = round(score.w2 * score.s_sens, 2)
        score.weighted_fin = round(score.w3 * score.s_fin, 2)
        score.weighted_type = round(score.w4 * score.s_type, 2)

        score.risk_score = round(
            score.weighted_struct + score.weighted_sens +
            score.weighted_fin + score.weighted_type, 2
        )

        # ───── Decision Boundary ─────
        if score.risk_score < 35:
            score.action = "AUTO_HEAL_PROCEED"
            score.action_label = "Auto-Heal Proceed"
            score.action_color = "green"
            self.auto_healed_count += 1
        elif score.risk_score < 70:
            score.action = "AUTO_HEAL_AUDIT_LOG"
            score.action_label = "Auto-Heal + Audit Log"
            score.action_color = "amber"
            self.audit_logged_count += 1
        else:
            score.action = "TRIP_CIRCUIT_BREAKER_HITL"
            score.action_label = "Circuit Breaker Tripped — Human-in-the-Loop Required"
            score.action_color = "red"
            self.circuit_tripped_count += 1

        self.evaluation_count += 1
        score.computation_time_ms = round((time.perf_counter() - start) * 1000, 3)
        return score

    def _dict_depth(self, d: Any, current: int = 0) -> int:
        """Compute nesting depth of a dictionary."""
        if isinstance(d, dict) and d:
            return max(self._dict_depth(v, current + 1) for v in d.values())
        return current

    def get_stats(self) -> Dict[str, int]:
        return {
            "total_evaluations": self.evaluation_count,
            "auto_healed": self.auto_healed_count,
            "audit_logged": self.audit_logged_count,
            "circuit_tripped": self.circuit_tripped_count
        }


# Module-level singleton
aegis_policy_governor = AegisPolicyGovernor()
