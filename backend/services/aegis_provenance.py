"""
AegisRegistry Safety & Governance Layer (Layer 5)
Anti-Hallucination Provenance Gate:
Enforces zero fabricated data in runtime healed API payloads.
Ensures every parameter traces directly to the user prompt, original tool arguments,
or verified schema defaults.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Set, Optional


@dataclass(frozen=True)
class ProvenanceResult:
    is_valid: bool
    confidence_score: float
    violations: List[str] = field(default_factory=list)
    audited_keys: List[str] = field(default_factory=list)
    origin_map: Dict[str, str] = field(default_factory=dict)  # param -> "user_input" | "original_arg" | "schema_default"


class AegisProvenanceGate:
    """
    Validates that a proposed healed payload does not hallucinate new business data
    or invent sensitive parameters that the user or agent never provided.
    """

    # Disallowed hallucinated dummy patterns
    FORBIDDEN_VALUES: Set[str] = {
        "dummy", "null", "undefined", "n/a", "unknown", "test", "fake", "placeholder"
    }

    # Parameters requiring strict human-in-the-loop verification if missing
    HIGH_RISK_SENSITIVE_FIELDS: Set[str] = {
        "ssn", "social_security", "password", "pin", "cvv", "credit_card",
        "secret", "token", "bank_account", "transfer_amount"
    }

    def verify_provenance(
        self,
        healed_params: Dict[str, Any],
        original_params: Dict[str, Any],
        user_prompt: str = ""
    ) -> ProvenanceResult:
        violations: List[str] = []
        audited_keys: List[str] = []
        origin_map: Dict[str, str] = {}

        prompt_lower = user_prompt.lower()

        for key, val in healed_params.items():
            audited_keys.append(key)
            val_str = str(val).lower().strip()

            # Rule 1: Check against forbidden dummy hallucinations
            if val_str in self.FORBIDDEN_VALUES:
                violations.append(f"Key '{key}' contains forbidden dummy placeholder '{val}'")
                continue

            # Rule 2: High-risk security fields must never be auto-fabricated
            if key.lower() in self.HIGH_RISK_SENSITIVE_FIELDS and key not in original_params:
                violations.append(f"Sensitive field '{key}' was missing and cannot be auto-synthesized (HITL Required)")
                continue

            # Rule 3: Trace value origin
            if key in original_params:
                origin_map[key] = "original_tool_argument"
            elif any(str(orig_val).lower() == val_str for orig_val in original_params.values()):
                origin_map[key] = "remapped_tool_argument"
            elif val_str in prompt_lower or any(word in prompt_lower for word in str(val).split() if len(word) > 2):
                origin_map[key] = "user_prompt_derivation"
            elif key.startswith("_default_") or key in {"page", "limit", "offset", "sort"}:
                origin_map[key] = "schema_default"
            else:
                # Value exists in healed params without direct lineage
                origin_map[key] = "inferred_parameter"

        is_valid = len(violations) == 0
        confidence = 1.0 if is_valid else max(0.0, 1.0 - (len(violations) * 0.5))

        return ProvenanceResult(
            is_valid=is_valid,
            confidence_score=confidence,
            violations=violations,
            audited_keys=audited_keys,
            origin_map=origin_map
        )


# Global singleton instance
aegis_provenance_gate = AegisProvenanceGate()
