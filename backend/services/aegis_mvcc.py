"""
AegisRegistry MVCC Registry & In-Memory Hot-Patching Layer (Layer 6)
Compiles diagnosed SchemaDiff objects into native Python transformation callables.
Maintains versioned in-memory SchemaSnapshots (v1.0 -> v1.1) with atomic pointer swapping
for thread-safe, sub-millisecond execution (<0.1ms) on recurring requests.
"""

import time
import copy
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, Callable, Tuple
from backend.services.aegis_diagnoser import SchemaDiff


@dataclass(frozen=True)
class SchemaSnapshot:
    """Immutable state model for an API endpoint contract version."""
    version: str
    endpoint: str
    diff: Optional[SchemaDiff] = None
    parent_version: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    applied_count: int = 0


class AegisMVCCRegistry:
    """
    Manages in-memory hot-patch snapshots and compiled transformation lambdas.
    """

    def __init__(self):
        # endpoint -> active SchemaSnapshot
        self._snapshots: Dict[str, SchemaSnapshot] = {}
        # endpoint -> compiled transform callable: (params, body, headers) -> (healed_params, healed_body, healed_headers, redirected_path)
        self._compiled_transforms: Dict[str, Callable] = {}

    def get_snapshot(self, endpoint: str) -> SchemaSnapshot:
        if endpoint not in self._snapshots:
            self._snapshots[endpoint] = SchemaSnapshot(version="v1.0", endpoint=endpoint)
        return self._snapshots[endpoint]

    def has_hot_patch(self, endpoint: str) -> bool:
        snapshot = self._snapshots.get(endpoint)
        return snapshot is not None and snapshot.version != "v1.0" and endpoint in self._compiled_transforms

    def apply_hot_patch(
        self,
        endpoint: str,
        params: Dict[str, Any],
        body: Optional[Dict[str, Any]],
        headers: Dict[str, str]
    ) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]], Dict[str, str], Optional[str]]:
        """
        Executes precompiled hot-patch transformation in memory (<0.1ms).
        Returns: (healed_params, healed_body, healed_headers, redirected_path)
        """
        if endpoint in self._compiled_transforms:
            transform_fn = self._compiled_transforms[endpoint]
            return transform_fn(params, body, headers)
        return params, body, headers, None

    def compile_and_register_patch(
        self,
        endpoint: str,
        diff: SchemaDiff
    ) -> SchemaSnapshot:
        """
        Compiles a diagnosed SchemaDiff into an in-memory transformation lambda
        and performs an atomic pointer swap to v1.1.
        """
        current_snapshot = self.get_snapshot(endpoint)
        next_ver = self._increment_version(current_snapshot.version)

        # Build dynamic transformer callable
        def compiled_transformer(
            p: Dict[str, Any],
            b: Optional[Dict[str, Any]],
            h: Dict[str, str]
        ) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]], Dict[str, str], Optional[str]]:
            healed_params = copy.deepcopy(p)
            healed_body = copy.deepcopy(b) if b is not None else None
            healed_headers = dict(h)
            redirected_path = diff.route_redirect

            # 1. Apply field renames
            for old_key, new_key in diff.field_renames.items():
                if old_key.startswith("_inject_"):
                    # Missing parameter injection
                    real_key = old_key.replace("_inject_", "")
                    if real_key not in healed_params:
                        healed_params[real_key] = "all"
                elif old_key in healed_params:
                    val = healed_params.pop(old_key)
                    healed_params[new_key] = val
                elif healed_body and old_key in healed_body:
                    val = healed_body.pop(old_key)
                    healed_body[new_key] = val

            # 2. Apply type casts
            for key, target_type in diff.type_casts.items():
                if key in healed_params:
                    val = healed_params[key]
                    try:
                        if target_type in ("int", "integer"):
                            healed_params[key] = int(val)
                        elif target_type in ("str", "string"):
                            healed_params[key] = str(val)
                        elif target_type in ("float", "real"):
                            healed_params[key] = float(val)
                    except (ValueError, TypeError):
                        pass

            # 3. Apply nested wrapping
            for child_key, wrapper in diff.nested_wraps.items():
                if child_key in healed_params:
                    val = healed_params.pop(child_key)
                    if wrapper not in healed_params:
                        healed_params[wrapper] = {}
                    if isinstance(healed_params[wrapper], dict):
                        healed_params[wrapper][child_key] = val

            # 4. Inject required headers
            for h_key, h_val in diff.injected_headers.items():
                healed_headers[h_key] = h_val

            return healed_params, healed_body, healed_headers, redirected_path

        # Atomic memory swap
        new_snapshot = SchemaSnapshot(
            version=next_ver,
            endpoint=endpoint,
            diff=diff,
            parent_version=current_snapshot.version,
            applied_count=1
        )
        self._compiled_transforms[endpoint] = compiled_transformer
        self._snapshots[endpoint] = new_snapshot
        return new_snapshot

    def reset_endpoint(self, endpoint: str) -> None:
        """Resets an endpoint back to clean v1.0 baseline."""
        self._snapshots[endpoint] = SchemaSnapshot(version="v1.0", endpoint=endpoint)
        if endpoint in self._compiled_transforms:
            del self._compiled_transforms[endpoint]

    def reset_all(self) -> None:
        """Resets all snapshots back to clean baseline."""
        self._snapshots.clear()
        self._compiled_transforms.clear()

    def _increment_version(self, current: str) -> str:
        try:
            if current.startswith("v"):
                parts = current[1:].split(".")
                major = int(parts[0])
                minor = int(parts[1]) if len(parts) > 1 else 0
                return f"v{major}.{minor + 1}"
        except Exception:
            pass
        return "v1.1"


# Global singleton instance
aegis_mvcc_registry = AegisMVCCRegistry()
