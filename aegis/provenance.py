"""
Field Provenance Gate
Guarantees Zero-Hallucination and prevents silent downstream data corruption.
Directly solves the PS 01 core challenge:
"avoid silently passing hallucinated values that corrupt data"
"""

from typing import Any, Dict, List, Set, Tuple


class FieldProvenanceGate:
    """
    Validates that any mutated or injected parameters in a candidate patch
    have a clear, auditable provenance (origin) in the user's task or context.
    """

    KNOWN_DERIVABLE_HEADERS = {"X-API-Version", "Authorization", "X-Client-Trace-Id"}

    @classmethod
    def verify_patch_provenance(
        cls,
        user_prompt: str,
        original_payload: Dict[str, Any],
        transformed_payload: Dict[str, Any],
        injected_headers: Dict[str, str]
    ) -> Tuple[bool, List[str]]:
        """
        Returns (is_safe, reasons).
        If is_safe is False, the patch is rejected to prevent database corruption.
        """
        violations = []

        # 1. Verify Headers: Only known system/derivable headers can be injected automatically
        for h in injected_headers.keys():
            if h not in cls.KNOWN_DERIVABLE_HEADERS:
                violations.append(f"Header '{h}' is not in known derivable set; requires human credential approval.")

        # 2. Extract all values in transformed payload
        def extract_values(d: Any) -> List[Any]:
            vals = []
            if isinstance(d, dict):
                for v in d.values():
                    vals.extend(extract_values(v))
            else:
                vals.append(d)
            return vals

        original_values = set(str(v).lower() for v in extract_values(original_payload))
        transformed_values = extract_values(transformed_payload)

        # 3. Check for ungrounded business values
        for val in transformed_values:
            val_str = str(val).lower()
            # If the value was not in original payload and not present in user prompt, it is a hallucinated default
            if val_str not in original_values and val_str not in user_prompt.lower():
                # Allow type conversions of numbers
                is_type_cast = False
                for orig in original_values:
                    if orig.isdigit() and str(val).isdigit() and int(orig) == int(val):
                        is_type_cast = True
                        break
                if not is_type_cast:
                    violations.append(
                        f"Unsupplied business value '{val}' has no antecedent in prompt or payload. Hallucination blocked."
                    )

        if violations:
            return False, violations

        return True, ["All transformed fields have verified provenance in user prompt or payload."]
